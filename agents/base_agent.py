"""Base agent class for all UAV design agents with comprehensive conversation management."""

import asyncio
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from state import GlobalState, StoredMessage
from pydantic_models import AgentMessage
from conversation import ConversationManager
from prompts import (
    format_agent_initial_task_message,
    format_agent_final_decision_message,
    format_agent_system_context,
    format_agent_final_system_message
)
from config import COMMUNICATION_RULES


class BaseAgent:
    """Base class for all UAV design agents with comprehensive conversation management."""
    
    def __init__(self, name: str, llm: ChatOpenAI, tools: List, output_class, system_prompt: str):
        self.name = name
        self.llm_with_tools = llm.bind_tools(tools)
        self.llm_structured = llm.with_structured_output(output_class)
        self.tools = tools
        self.tool_node = ToolNode(tools)
        self.output_class = output_class
        self.system_prompt = system_prompt
        self.communication_allowed = COMMUNICATION_RULES.get(self.name, [])
        self.conversation_manager = ConversationManager()
    
    def can_communicate_with(self, other_agent: str) -> bool:
        """Check if this agent can communicate with another agent."""
        return other_agent in self.communication_allowed
    
    def get_task_for_current_iteration(self, state: GlobalState) -> Optional[str]:
        """Get task from coordinator for current iteration."""
        if state.current_iteration in state.coordinator_outputs:
            coord_output = state.coordinator_outputs[state.current_iteration]
            for task in coord_output.agent_tasks:
                if task.agent_name == self.name:
                    return task.task_description
        return None
    
    def get_messages_from_previous_iteration(self, state: GlobalState) -> List[Dict[str, str]]:
        """Get messages from previous iteration only."""
        if state.current_iteration <= 0:
            return []
        
        prev_iteration = state.current_iteration - 1
        messages = state.mailboxes[self.name].get_messages_for_iteration(prev_iteration)
        return [{"from": msg.from_agent, "content": msg.content} for msg in messages]
    
    def check_dependencies_ready(self, state: GlobalState) -> bool:
        """Check if required agent outputs exist."""
        return True  # Override in subclasses
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Get outputs from dependent agents."""
        return {}  # Override in subclasses
    
    def send_messages(self, state: GlobalState, messages: List[AgentMessage]):
        """Send messages to other agents."""
        messages_sent = []
        for msg in messages:
            if self.can_communicate_with(msg.to_agent):
                stored_msg = StoredMessage(
                    from_agent=self.name,
                    to_agent=msg.to_agent,
                    content=msg.content,
                    iteration=state.current_iteration,
                    timestamp=asyncio.get_event_loop().time()
                )
                state.mailboxes[msg.to_agent].add_message(stored_msg)
                messages_sent.append({"to": msg.to_agent, "content": msg.content})
            else:
                print(f"⚠️  Warning: {self.name} cannot send message to '{msg.to_agent}'")
        
        # Track messages sent in conversation history
        history = self.conversation_manager.get_agent_history(self.name)
        history.add_messages_sent(messages_sent)
    
    async def process(self, state: GlobalState) -> GlobalState:
        """Process the agent's task with comprehensive conversation management."""
        current_iter = state.current_iteration
        
        # Check if we have a task
        task = self.get_task_for_current_iteration(state)
        if not task:
            return state
        
        # Check dependencies
        if not self.check_dependencies_ready(state):
            return state
        
        # Check if already processed
        outputs_dict = getattr(state, f"{self.name}_outputs")
        if current_iter in outputs_dict:
            return state
        
        # Get conversation context
        messages_received = self.get_messages_from_previous_iteration(state)
        dependencies = self.get_dependency_outputs(state)
        
        # Start new conversation turn
        history = self.conversation_manager.get_agent_history(self.name)
        turn = history.start_agent_turn(current_iter, task, messages_received, dependencies)
        
        # Process the work with full conversation context
        try:
            output = await self._do_comprehensive_work(state, history)
            
            # Store output
            output.iteration = current_iter
            outputs_dict[current_iter] = output
            state.last_update_iteration[self.name] = current_iter
            
            # Set final output in conversation history
            history.set_final_output(output)
            
            # Send messages if any
            if output.messages:
                self.send_messages(state, output.messages)
            
        except Exception as e:
            print(f"Error in {self.name}: {e}")
        
        return state
    
    async def _do_comprehensive_work(self, state: GlobalState, history) -> Any:
        """Execute comprehensive work with tool calling loop and conversation tracking."""
        
        # Build system message with agent role and instructions
        system_content = format_agent_system_context(
            self.system_prompt,
            self.tools,
            ""  # Don't include conversation context in system message
        )
        system_message = SystemMessage(content=system_content)
        
        # Start conversation
        messages = [system_message]
        
        # Add task with current context as human message
        current_turn = history.turns[-1]
        
        # Get current conversation context (previous iterations + current dependencies)
        conversation_context = history.get_conversation_context()
        
        # Combine task with complete context
        task_with_context = f"""{format_agent_initial_task_message(current_turn.task)}

{conversation_context}"""
        
        messages.append(HumanMessage(content=task_with_context))
        
        # Tool calling loop
        max_tool_iterations = 5
        tool_iteration = 0
        
        while tool_iteration < max_tool_iterations:
            # Get response from LLM with tools
            response = await self.llm_with_tools.ainvoke(messages)
            messages.append(response)
            
            # Check if tools were called
            if response.tool_calls:
                print(f"🔧 {self.name}: Using tools in iteration {tool_iteration + 1}")
                
                # Execute tools
                tool_result = await self.tool_node.ainvoke({"messages": [response]})
                tool_message = tool_result["messages"][-1]
                messages.append(tool_message)
                
                # Track tool usage
                for tool_call in response.tool_calls:
                    try:
                        result = eval(tool_message.content) if tool_message.content else "No result"
                    except:
                        result = tool_message.content
                    
                    history.add_tool_call(
                        tool_call["name"], 
                        tool_call["args"],
                        result,
                        state.current_iteration
                    )
                
                tool_iteration += 1
            else:
                # No more tools needed, break the loop
                break
        
        # Get COMPLETE context for final decision including:
        # - All previous iterations with messages sent/received
        # - Current iteration messages and dependencies  
        # - Complete tool usage history
        tool_usage_summary = history.get_tool_usage_history()
        updated_conversation_context = history.get_conversation_context()  # Get updated context with tool calls
        
        final_content = format_agent_final_decision_message(
            tool_usage_summary, 
            updated_conversation_context
        )
        
        final_system_content = format_agent_final_system_message(self.system_prompt)
        
        final_response = await self.llm_structured.ainvoke([
            SystemMessage(content=final_system_content),
            HumanMessage(content=final_content)
        ])
        
        return final_response
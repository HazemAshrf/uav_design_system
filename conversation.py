"""Conversation management for tracking agent interactions and tool usage."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
import json

@dataclass
class ToolCall:
    """Represents a tool call made by an agent."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    iteration: int

@dataclass 
class ConversationTurn:
    """Represents one complete conversation turn for an agent."""
    iteration: int
    task: str
    messages_received: List[Dict[str, str]]  # Messages from other agents
    dependency_data: Dict[str, Any]  # Data from dependent agents
    tool_calls: List[ToolCall]  # Tools used in this turn
    final_output: Optional[Any]  # Final structured output
    messages_sent: List[Dict[str, str]]  # Messages sent to other agents

class AgentConversationHistory:
    """Manages conversation history for a single agent."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.turns: List[ConversationTurn] = []
        self.current_messages: List[BaseMessage] = []
    
    def start_new_turn(self, iteration: int, task: str, messages_received: List[Dict[str, str]], 
                      dependency_data: Dict[str, Any]):
        """Start a new conversation turn."""
        turn = ConversationTurn(
            iteration=iteration,
            task=task,
            messages_received=messages_received,
            dependency_data=dependency_data,
            tool_calls=[],
            final_output=None,
            messages_sent=[]
        )
        self.turns.append(turn)
        
        # Reset conversation messages for this turn
        self.current_messages = []
        return turn
    
    def add_tool_call(self, tool_name: str, parameters: Dict[str, Any], result: Any, iteration: int):
        """Add a tool call to the current turn."""
        if self.turns and self.turns[-1].iteration == iteration:
            tool_call = ToolCall(tool_name, parameters, result, iteration)
            self.turns[-1].tool_calls.append(tool_call)
    
    def set_final_output(self, output: Any):
        """Set the final output for the current turn."""
        if self.turns:
            self.turns[-1].final_output = output
    
    def add_messages_sent(self, messages: List[Dict[str, str]]):
        """Add messages sent to other agents."""
        if self.turns:
            self.turns[-1].messages_sent = messages
    
    def get_conversation_context(self) -> str:
        """Get a comprehensive conversation context for the agent."""
        if not self.turns:
            return "No previous conversation history."
        
        context_parts = []
        
        # Add summary of previous iterations
        if len(self.turns) > 1:
            context_parts.append("PREVIOUS ITERATIONS SUMMARY:")
            for turn in self.turns[:-1]:  # All but current turn
                context_parts.append(f"\nIteration {turn.iteration}:")
                context_parts.append(f"  Task: {turn.task}")
                
                if turn.messages_received:
                    context_parts.append("  Messages Received:")
                    for msg in turn.messages_received:
                        context_parts.append(f"    From {msg['from']}: {msg['content']}")
                
                if turn.tool_calls:
                    context_parts.append("  Tools Used:")
                    for tool_call in turn.tool_calls:
                        context_parts.append(f"    {tool_call.tool_name}({tool_call.parameters}) -> {tool_call.result}")
                
                if turn.final_output:
                    context_parts.append(f"  Final Output: {self._summarize_output(turn.final_output)}")
                
                if turn.messages_sent:
                    context_parts.append("  Messages Sent:")
                    for msg in turn.messages_sent:
                        context_parts.append(f"    To {msg['to']}: {msg['content']}")
        
        # Add current iteration context
        current_turn = self.turns[-1]
        context_parts.append(f"\nCURRENT ITERATION {current_turn.iteration}:")
        context_parts.append(f"Task: {current_turn.task}")
        
        if current_turn.messages_received:
            context_parts.append("Messages Received:")
            for msg in current_turn.messages_received:
                context_parts.append(f"  From {msg['from']}: {msg['content']}")
        
        if current_turn.dependency_data:
            context_parts.append("Dependency Data Available:")
            for dep_name, dep_data in current_turn.dependency_data.items():
                if dep_data:
                    context_parts.append(f"  {dep_name}: {self._summarize_output(dep_data)}")
        
        return "\n".join(context_parts)
    
    def get_tool_usage_history(self) -> str:
        """Get history of tool usage for current iteration context."""
        if not self.turns:
            return ""
        
        current_turn = self.turns[-1]
        if not current_turn.tool_calls:
            return ""
        
        tool_history = ["TOOL USAGE IN THIS ITERATION:"]
        for i, tool_call in enumerate(current_turn.tool_calls, 1):
            tool_history.append(f"{i}. Called {tool_call.tool_name}")
            tool_history.append(f"   Parameters: {tool_call.parameters}")
            tool_history.append(f"   Result: {tool_call.result}")
        
        return "\n".join(tool_history)
    
    def _summarize_output(self, output: Any) -> str:
        """Create a brief summary of an output."""
        if hasattr(output, 'dict'):
            output_dict = output.dict()
            # Create a brief summary of key parameters
            key_items = []
            for key, value in output_dict.items():
                if key in ['iteration', 'messages']:
                    continue
                key_items.append(f"{key}={value}")
            return ", ".join(key_items[:3]) + ("..." if len(key_items) > 3 else "")
        return str(output)[:100] + ("..." if len(str(output)) > 100 else "")

class ConversationManager:
    """Manages conversation histories for all agents."""
    
    def __init__(self):
        self.agent_histories: Dict[str, AgentConversationHistory] = {}
    
    def get_agent_history(self, agent_name: str) -> AgentConversationHistory:
        """Get or create conversation history for an agent."""
        if agent_name not in self.agent_histories:
            self.agent_histories[agent_name] = AgentConversationHistory(agent_name)
        return self.agent_histories[agent_name]
    
    def start_agent_turn(self, agent_name: str, iteration: int, task: str, 
                        messages_received: List[Dict[str, str]], dependency_data: Dict[str, Any]) -> ConversationTurn:
        """Start a new conversation turn for an agent."""
        history = self.get_agent_history(agent_name)
        return history.start_new_turn(iteration, task, messages_received, dependency_data)
"""Coordinator Agent for UAV design system with comprehensive prompting."""

import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from state import GlobalState, StoredMessage
from pydantic_models import CoordinatorOutput
from prompts import COORDINATOR_INITIAL_SYSTEM, COORDINATOR_EVALUATION_SYSTEM
from prompts import format_coordinator_initial_message, format_coordinator_evaluation_message


class CoordinatorAgent:
    """Coordinator Agent - manages project workflow and completion with comprehensive evaluation."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm.with_structured_output(CoordinatorOutput)
    
    def check_stability(self, state: GlobalState) -> bool:
        """Check if results are stable (no updates for stability_threshold iterations)."""
        current_iter = state.current_iteration
        
        if current_iter < state.stability_threshold:
            return False
        
        for agent_name, last_update in state.last_update_iteration.items():
            if current_iter - last_update < state.stability_threshold:
                return False
        
        return True
    
    async def process(self, state: GlobalState) -> GlobalState:
        """Coordinator decides on next steps with comprehensive evaluation."""
        current_iter = state.current_iteration
        
        if current_iter == 0:
            # Initial task assignment
            output = await self._create_initial_tasks(state)
            print(f"🎯 Coordinator created initial tasks for {len(output.agent_tasks)} agents")
        else:
            # Check stability first - if not stable, continue without LLM evaluation
            is_stable = self.check_stability(state)
            
            if not is_stable:
                # System is not stable, continue to next iteration without LLM evaluation
                print(f"🔄 System NOT STABLE - continuing to iteration {current_iter + 1}")
                output = CoordinatorOutput(
                    project_complete=False,
                    completion_reason=f"System not stable - agents still updating. Continuing to iteration {current_iter + 1}.",
                    agent_tasks=[],
                    messages=[],
                    iteration=current_iter
                )
            else:
                # System is stable, evaluate with LLM
                print(f"✅ System STABLE - evaluating completion...")
                output = await self._evaluate_and_decide(state)
                
                # If LLM decides to continue, reset stability by updating last_update_iteration
                if not output.project_complete:
                    print(f"🔄 Coordinator decided to CONTINUE: {output.completion_reason}")
                    # Reset stability by marking this iteration as an update
                    state.last_update_iteration["coordinator"] = current_iter
                else:
                    print(f"🎉 Coordinator decided to COMPLETE: {output.completion_reason}")
        
        output.iteration = current_iter
        state.coordinator_outputs[current_iter] = output
        state.project_complete = output.project_complete
        
        # Send coordinator messages - trust the LLM to use correct agent names
        for msg in output.messages:
            if msg.to_agent in state.mailboxes:
                stored_msg = StoredMessage(
                    from_agent="coordinator",
                    to_agent=msg.to_agent,
                    content=msg.content,
                    iteration=current_iter,
                    timestamp=asyncio.get_event_loop().time()
                )
                state.mailboxes[msg.to_agent].add_message(stored_msg)
            else:
                print(f"⚠️  Warning: Invalid agent name '{msg.to_agent}' in coordinator message")
        
        # Increment iteration if continuing
        if not output.project_complete:
            state.current_iteration += 1
        
        return state
    
    async def _create_initial_tasks(self, state: GlobalState) -> CoordinatorOutput:
        """Create initial tasks for all agents with detailed context."""
        human_message = format_coordinator_initial_message(state.user_requirements)
        
        response = await self.llm.ainvoke([
            SystemMessage(content=COORDINATOR_INITIAL_SYSTEM),
            HumanMessage(content=human_message)
        ])
        
        return response
    
    async def _evaluate_and_decide(self, state: GlobalState) -> CoordinatorOutput:
        """Evaluate current outputs and decide on project completion with comprehensive analysis."""
        # Get latest outputs
        latest_outputs = {}
        if state.mission_planner_outputs:
            latest_outputs["mission_planner"] = state.mission_planner_outputs[max(state.mission_planner_outputs.keys())]
        if state.aerodynamics_outputs:
            latest_outputs["aerodynamics"] = state.aerodynamics_outputs[max(state.aerodynamics_outputs.keys())]
        if state.propulsion_outputs:
            latest_outputs["propulsion"] = state.propulsion_outputs[max(state.propulsion_outputs.keys())]
        if state.structures_outputs:
            latest_outputs["structures"] = state.structures_outputs[max(state.structures_outputs.keys())]
        if state.manufacturing_outputs:
            latest_outputs["manufacturing"] = state.manufacturing_outputs[max(state.manufacturing_outputs.keys())]
        
        is_stable = self.check_stability(state)
        
        human_message = format_coordinator_evaluation_message(
            state.user_requirements,
            state.current_iteration,
            is_stable,
            latest_outputs
        )
        
        response = await self.llm.ainvoke([
            SystemMessage(content=COORDINATOR_EVALUATION_SYSTEM),
            HumanMessage(content=human_message)
        ])
        
        return response
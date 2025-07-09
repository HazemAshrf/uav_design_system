"""Workflow for the UAV design system using LangGraph."""

import asyncio
from typing import Literal

from state import GlobalState
from agents.mission_planner import MissionPlannerAgent
from agents.aerodynamics import AerodynamicsAgent
from agents.propulsion import PropulsionAgent
from agents.structures import StructuresAgent
from agents.manufacturing import ManufacturingAgent
from agents.coordinator import CoordinatorAgent
from tools import (
    MISSION_PLANNER_TOOLS,
    AERODYNAMICS_TOOLS,
    PROPULSION_TOOLS,
    STRUCTURES_TOOLS,
    MANUFACTURING_TOOLS
)
from config import get_llm
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph


async def aggregator_node(state: GlobalState) -> GlobalState:
    """Run all agents concurrently using LangGraph create_react_agent."""
    current_iter = state.current_iteration
    
    llm = get_llm()
    
    # Create agents with their specific tools
    agents = [
        MissionPlannerAgent(llm, MISSION_PLANNER_TOOLS),
        AerodynamicsAgent(llm, AERODYNAMICS_TOOLS),
        PropulsionAgent(llm, PROPULSION_TOOLS),
        StructuresAgent(llm, STRUCTURES_TOOLS),
        ManufacturingAgent(llm, MANUFACTURING_TOOLS)
    ]
    
    # Run all agents concurrently
    await asyncio.gather(*[agent.process(state) for agent in agents])
    
    # Print iteration summary
    print(f"\n📊 ITERATION {current_iter} SUMMARY:")
    agent_names = ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
    for agent_name in agent_names:
        outputs_dict = getattr(state, f"{agent_name}_outputs")
        if current_iter in outputs_dict:
            # Check if this was an update or maintain
            if state.last_update_iteration[agent_name] == current_iter:
                status = "✅ OUTPUT (UPDATED)"
            else:
                status = "✅ OUTPUT (MAINTAINED)"
        else:
            status = "❌ NO OUTPUT"
        print(f"   {agent_name}: {status}")
    
    return state


async def coordinator_node(state: GlobalState) -> GlobalState:
    """Coordinator evaluation and decision."""
    llm = get_llm()
    coordinator = CoordinatorAgent(llm)
    return await coordinator.process(state)


def should_continue(state: GlobalState) -> Literal["continue", "end"]:
    """Determine if workflow should continue."""
    if state.project_complete or state.current_iteration >= state.max_iterations:
        return "end"
    return "continue"


def create_uav_design_workflow() -> CompiledStateGraph:
    """Create the LangGraph workflow for UAV design coordination."""
    workflow = StateGraph(GlobalState)
    
    # Add nodes
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("aggregator", aggregator_node)
    
    # Set entry point
    workflow.set_entry_point("coordinator")
    
    # Define conditional flow
    workflow.add_conditional_edges(
        "coordinator",
        should_continue,
        {
            "continue": "aggregator",
            "end": END
        }
    )
    
    # Add edge back to coordinator after aggregator completes
    workflow.add_edge("aggregator", "coordinator")
    
    return workflow.compile()
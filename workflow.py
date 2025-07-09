"""Workflow for the UAV design system."""

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
    """Run all agents concurrently."""
    llm = get_llm()
    
    # Give each agent only the tools they need
    agents = [
        MissionPlannerAgent(llm, MISSION_PLANNER_TOOLS),
        AerodynamicsAgent(llm, AERODYNAMICS_TOOLS),
        PropulsionAgent(llm, PROPULSION_TOOLS),
        StructuresAgent(llm, STRUCTURES_TOOLS),
        ManufacturingAgent(llm, MANUFACTURING_TOOLS)
    ]
    
    # Run all agents concurrently
    await asyncio.gather(*[agent.process(state) for agent in agents])
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
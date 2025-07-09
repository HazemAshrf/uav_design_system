"""Structures Agent for UAV design system with comprehensive conversation management."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from state import GlobalState
from pydantic_models import StructuresOutput
from prompts import STRUCTURES_SYSTEM


class StructuresAgent(BaseAgent):
    """Structures Agent - designs structural components."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("structures", llm, tools, StructuresOutput, STRUCTURES_SYSTEM)
    
    def check_dependencies_ready(self, state: GlobalState) -> bool:
        """Needs MTOW from mission planner and wing geometry from aerodynamics."""
        return (state.current_iteration in state.mission_planner_outputs and 
                state.current_iteration in state.aerodynamics_outputs)
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Get mission planner and aerodynamics outputs."""
        return {
            "mission_plan": state.mission_planner_outputs.get(state.current_iteration),
            "aerodynamics": state.aerodynamics_outputs.get(state.current_iteration)
        }
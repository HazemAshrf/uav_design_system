"""Propulsion Agent for UAV design system with comprehensive conversation management."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from state import GlobalState
from pydantic_models import PropulsionOutput
from prompts import PROPULSION_SYSTEM


class PropulsionAgent(BaseAgent):
    """Propulsion Agent - designs the propulsion system."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("propulsion", llm, tools, PropulsionOutput, PROPULSION_SYSTEM)
    
    def check_dependencies_ready(self, state: GlobalState) -> bool:
        """Needs MTOW from mission planner."""
        return state.current_iteration in state.mission_planner_outputs
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Get mission planner output."""
        return {
            "mission_plan": state.mission_planner_outputs.get(state.current_iteration)
        }
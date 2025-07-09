"""Mission Planner Agent for UAV design system with comprehensive conversation management."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from state import GlobalState
from pydantic_models import MissionPlannerOutput
from prompts import MISSION_PLANNER_SYSTEM


class MissionPlannerAgent(BaseAgent):
    """Mission Planner Agent - defines mission requirements and MTOW."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("mission_planner", llm, tools, MissionPlannerOutput, MISSION_PLANNER_SYSTEM)
    
    def check_dependencies_ready(self, state: GlobalState) -> bool:
        """Mission planner has no dependencies."""
        return True
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Mission planner has no dependencies."""
        return {}
"""Manufacturing Agent for UAV design system with comprehensive conversation management."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from agents.base_agent import BaseAgent
from state import GlobalState
from pydantic_models import ManufacturingOutput
from prompts import MANUFACTURING_SYSTEM


class ManufacturingAgent(BaseAgent):
    """Manufacturing Agent - analyzes manufacturability and costs."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("manufacturing", llm, tools, ManufacturingOutput, MANUFACTURING_SYSTEM)
    
    def check_dependencies_ready(self, state: GlobalState) -> bool:
        """Needs output from structures agent."""
        return state.current_iteration in state.structures_outputs
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Get structures output."""
        return {
            "structures": state.structures_outputs.get(state.current_iteration)
        }
"""Manufacturing Agent for UAV design system using LangGraph create_react_agent."""

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
        return len(state.structures_outputs) > 0
    
    def get_dependency_outputs(self, state: GlobalState) -> Dict[str, Any]:
        """Get latest structures output."""
        if state.structures_outputs:
            latest_key = max(state.structures_outputs.keys())
            return {
                "structures": state.structures_outputs[latest_key]
            }
        return {}
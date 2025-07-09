"""Global state and message system for the UAV design system."""

import asyncio
from typing import Dict, List
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass

from pydantic_models import (
    MissionPlannerOutput, AerodynamicsOutput, PropulsionOutput,
    StructuresOutput, ManufacturingOutput, CoordinatorOutput
)
from config import MAX_ITERATIONS, STABILITY_THRESHOLD


@dataclass
class StoredMessage:
    """Internal message storage format."""
    from_agent: str
    to_agent: str
    content: str
    iteration: int
    timestamp: float


class AgentMailbox:
    """Mailbox for storing agent messages."""
    
    def __init__(self):
        self.messages: List[StoredMessage] = []
    
    def add_message(self, message: StoredMessage):
        """Add a message to the mailbox."""
        self.messages.append(message)
    
    def get_messages_for_iteration(self, iteration: int) -> List[StoredMessage]:
        """Get all messages for a specific iteration."""
        return [msg for msg in self.messages if msg.iteration == iteration]


class GlobalState(BaseModel):
    """Global state containing all agent outputs and communication."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Agent outputs by iteration
    mission_planner_outputs: Dict[int, MissionPlannerOutput] = Field(default_factory=dict)
    aerodynamics_outputs: Dict[int, AerodynamicsOutput] = Field(default_factory=dict)
    propulsion_outputs: Dict[int, PropulsionOutput] = Field(default_factory=dict)
    structures_outputs: Dict[int, StructuresOutput] = Field(default_factory=dict)
    manufacturing_outputs: Dict[int, ManufacturingOutput] = Field(default_factory=dict)
    coordinator_outputs: Dict[int, CoordinatorOutput] = Field(default_factory=dict)
    
    # Communication system
    mailboxes: Dict[str, AgentMailbox] = Field(default_factory=lambda: {
        "coordinator": AgentMailbox(),
        "mission_planner": AgentMailbox(),
        "aerodynamics": AgentMailbox(),
        "propulsion": AgentMailbox(),
        "structures": AgentMailbox(),
        "manufacturing": AgentMailbox()
    })
    
    # Iteration tracking
    current_iteration: int = 0
    max_iterations: int = MAX_ITERATIONS
    stability_threshold: int = STABILITY_THRESHOLD
    last_update_iteration: Dict[str, int] = Field(default_factory=lambda: {
        "mission_planner": -1,
        "aerodynamics": -1,
        "propulsion": -1,
        "structures": -1,
        "manufacturing": -1
    })
    
    # Project status
    project_complete: bool = False
    user_requirements: str = ""
"""Configuration settings for the UAV design system."""

import os
from langchain_openai import ChatOpenAI

# API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")

# Model Configuration
MODEL_NAME = "mistralai/mistral-small-3.2-24b-instruct:free"

# System Configuration
MAX_ITERATIONS = 20
STABILITY_THRESHOLD = 3

# Agent Communication Rules
COMMUNICATION_RULES = {
    "mission_planner": ["aerodynamics", "propulsion", "structures"],
    "aerodynamics": ["mission_planner", "propulsion", "structures"],
    "propulsion": ["mission_planner", "aerodynamics"],
    "structures": ["mission_planner", "aerodynamics", "manufacturing"],
    "manufacturing": ["structures"]
}

# Initialize LLM
def get_llm() -> ChatOpenAI:
    """Get configured LLM instance."""
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY
    )
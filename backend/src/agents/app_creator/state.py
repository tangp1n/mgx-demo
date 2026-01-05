"""State management for app_creator agent."""
from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State for the app_creator agent.

    Attributes:
        messages: Conversation messages
        application_id: Application ID
        user_id: User ID
        requirements: Extracted requirements
        requirements_confirmed: Whether requirements are confirmed
        clarifying_questions: List of clarifying questions to ask
        current_stage: Current conversation stage
        error: Error message if any
    """
    messages: List[BaseMessage]
    application_id: str
    user_id: str
    requirements: Optional[str]
    requirements_confirmed: bool
    clarifying_questions: Optional[List[str]]
    current_stage: str
    error: Optional[str]


# Conversation stages
class ConversationStage:
    """Conversation stage enumeration."""
    GATHERING = "gathering"  # Initial requirements gathering
    CLARIFYING = "clarifying"  # Asking clarification questions
    CONFIRMING = "confirming"  # Confirming requirements with user
    CONFIRMED = "confirmed"  # Requirements confirmed, ready for code generation
    ERROR = "error"  # Error state

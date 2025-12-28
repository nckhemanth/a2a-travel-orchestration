from __future__ import annotations  # Enable postponed evaluation of annotations (allows using types before definition)

from typing import Any  # Type hint for any type
from uuid import uuid4  # Generate unique identifiers for messages

from a2a.types import (
    AgentCapabilities,  # Defines what agent can do (streaming, push notifications, etc.)
    AgentCard,  # Agent metadata card (name, skills, capabilities) for discovery
    AgentSkill,  # Specific skill/ability an agent has (e.g., "sales analysis")
    DataPart,  # Structured data part in message (JSON/dict)
    Part,  # Base class for message parts (text, data, file, etc.)
    Message,  # Complete message object with role, parts, messageId (camelCase param, snake_case attribute)
    Role,  # Message role enum (user, agent, system)
    TextPart,  # Plain text part in message
    TransportProtocol,  # Communication protocol enum (jsonrpc, http, etc.)
)

# --- PATCH: Ensure Message model accepts snake_case input (a2a-sdk vs Pydantic 2.x compat fix) ---
try:
    if hasattr(Message, "model_config"):
        # Force Pydantic to allow populating fields by their attribute name (snake_case)
        # even if an alias (camelCase) is defined. This fixes the Streamlit validation error.
        Message.model_config["populate_by_name"] = True
        Message.model_rebuild()
except Exception:
    pass
# -------------------------------------------------------------------------------------------------


def create_agent_card(
    *,
    name: str,
    description: str,
    skill_id: str,
    skill_name: str,
    skill_description: str,
    version: str = "1.0.0",
    url: str | None = None,
) -> AgentCard:
    """Build a minimal A2A agent card for local orchestration."""
    endpoint = url or f"local://{name.lower().replace(' ', '-') }"
    return AgentCard(
        name=name,
        description=description,
        version=version,
        url=endpoint,
        preferred_transport=TransportProtocol.jsonrpc.value,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain", "application/json"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=[
            AgentSkill(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                tags=["sales", "marketing", "analytics"],
            )
        ],
        supports_authenticated_extended_card=False,
    )


def create_text_message(content: str, role: Role = Role.user) -> Message:
    """Create an A2A text message."""
    return Message(messageId=str(uuid4()), role=role, parts=[TextPart(text=content)])


def create_text_message_with_data(
    content: str,
    *,
    role: Role = Role.user,
    data: dict[str, Any] | None = None,
) -> Message:
    """Create a text message with optional structured data."""
    parts: list[TextPart | DataPart] = [TextPart(text=content)]
    if data is not None:
        parts.append(DataPart(data=data))
    return Message(messageId=str(uuid4()), role=role, parts=parts)


def create_agent_message(*, text: str, data: dict[str, Any] | None = None) -> Message:
    """Create a combined agent response with optional structured data."""
    parts: list[TextPart | DataPart] = []
    if text:
        parts.append(TextPart(text=text))
    if data is not None:
        parts.append(DataPart(data=data))
    return Message(messageId=str(uuid4()), role=Role.agent, parts=parts)


def extract_text_from_message(message: Message) -> str:
    """Extract the concatenated text parts from a message."""
    texts: list[str] = []
    for part in message.parts:
        target = part.root if isinstance(part, Part) else part
        if isinstance(target, TextPart):
            texts.append(target.text)
    return "\n".join(texts)


def get_data_part(message: Message) -> dict[str, Any] | None:
    """Return the first structured data part if present."""
    for part in message.parts:
        target = part.root if isinstance(part, Part) else part
        if isinstance(target, DataPart):
            return target.data
    return None


import os

def get_llm_config() -> dict[str, Any]:
    """
    Resolve the best available LLM configuration.
    Prioritizes EUR_API_KEY if available, falling back to OPENAI_API_KEY.
    """
    eur_key = os.getenv("EUR_API_KEY")
    if eur_key:
        # POLYFILL: Some libraries (CrewAI/LiteLLM) perform hard validation for OPENAI_API_KEY
        # We explicitly match it to the Euri key to pass these checks.
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = eur_key

        return {
            "api_key": eur_key,
            "base_url": "https://api.euron.one/api/v1/euri",
            "model_default": "gpt-4.1-nano"
        }
    
    # Fallback to standard OpenAI
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": None, # Use default OpenAI URL
        "model_default": "gpt-4o-mini"
    }

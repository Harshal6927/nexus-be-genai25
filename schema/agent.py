from datetime import datetime

from msgspec import Struct


class AgentCreate(Struct):
    agent_name: str
    agent_instructions: str | None = None


class AgentUpdate(Struct):
    agent_name: str
    agent_instructions: str | None = None


class AgentResponse(Struct):
    agent_name: str
    agent_instructions: str | None
    id: int
    updated_at: datetime
    created_at: datetime

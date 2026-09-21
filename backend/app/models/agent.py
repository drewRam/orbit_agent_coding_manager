from enum import Enum
from pydantic import BaseModel

class AgentStatus(str, Enum):
    IDLE = "idle"
    READY = "ready"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

class Agent(BaseModel):
    id: str
    name: str
    role: str
    capabilities: list[str] = []
    status: AgentStatus = AgentStatus.IDLE
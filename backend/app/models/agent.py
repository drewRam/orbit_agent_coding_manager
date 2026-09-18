from enum import Enum
from pydantic import BaseModel

class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

class Agent(BaseModel):
    id: str
    name: str
    role: str
    status: AgentStatus = AgentStatus.IDLE
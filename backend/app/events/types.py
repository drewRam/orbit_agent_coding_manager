from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class EventType(str, Enum):
    PROJECT_STARTED = "project_started"
    TASK_CREATED = "task_created"
    TASK_READY = "task_ready"
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    TASK_COMPLETED = "task_completed"
    PROJECT_COMPLETED = "project_completed"

class Event(BaseModel):
    type: EventType
    project_id: str
    task_id: str | None = None
    agent_id: str | None = None
    message: str
    timestamp: datetime
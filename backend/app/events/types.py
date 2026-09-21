from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class EventType(str, Enum):
    PROJECT_STARTED = "project_started"
    TASK_CREATED = "task_created"
    TASK_READY = "task_ready"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_REASSIGNED = "task_reassigned"
    TASK_COMPLETED = "task_completed"
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    PROJECT_COMPLETED = "project_completed"

class Event(BaseModel):
    type: EventType
    project_id: str
    task_id: str | None = None
    agent_id: str | None = None
    message: str
    timestamp: datetime
    data: dict | None = None 
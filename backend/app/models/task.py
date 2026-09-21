from enum import Enum
from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"


class Task(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING

    assigned_agent_id: str | None = None

    dependencies: list[str] = []

    retry_count: int = 0
    max_retries: int = 1

    failure_reason: str | None = None

    required_capability: str | None = None

    input_context: str | None = None
    result: str | None = None
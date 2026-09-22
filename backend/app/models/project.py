from pydantic import BaseModel
from .task import Task

class Project(BaseModel):
    id: str
    name: str
    goal: str
    tasks: list[Task] = []

    replan_count: int = 0
    max_replans: int = 2

    final_result: str | None = None
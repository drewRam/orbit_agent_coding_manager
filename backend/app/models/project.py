from pydantic import BaseModel
from .task import Task

class Project(BaseModel):
    id: str
    name: str
    goal: str
    tasks: list[Task] = []
from typing import Literal

from pydantic import BaseModel


Capability = Literal[
    "research",
    "requirements",
    "documentation",
    "coding",
    "implementation",
    "debugging",
    "backend",
    "review",
    "testing",
    "verification",
]


class PlannedTask(BaseModel):
    id: str
    title: str
    description: str
    dependencies: list[str] = []
    required_capability: Capability | None = None


class ProjectPlan(BaseModel):
    tasks: list[PlannedTask]
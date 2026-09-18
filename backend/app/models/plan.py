from pydantic import BaseModel

class PlannedTask(BaseModel):
    id: str
    title: str
    description: str
    assigned_agent_id: str
    dependencies: list[str] = []

class ProjectPlan(BaseModel):
    tasks: list[PlannedTask]
from app.agents.base import BaseAgent
from app.models.task import Task
from app.models.plan import ProjectPlan
from app.orchestration.planner import Planner

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="manager",
            name="Manager",
            role="Project orchestration",
            capabilities=[
                "planning",
                "orchestration",
                "delegation",
                "management",
            ],
        )

        self.planner = Planner()

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Manager completed: {task.title}",
        }

    def create_plan(self, goal: str) -> ProjectPlan:
        return self.planner.create_plan(goal)
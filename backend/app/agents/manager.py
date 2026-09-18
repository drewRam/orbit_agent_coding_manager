from app.agents.base import BaseAgent
from app.models.task import Task

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="manager",
            name="Manager",
            role="Project orchestration",
        )

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Manager completed: {task.title}",
        }
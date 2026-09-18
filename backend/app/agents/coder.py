from app.agents.base import BaseAgent
from app.models.task import Task

class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="coder",
            name="Coder",
            role="Software development",
        )

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Coder completed: {task.title}",
        }
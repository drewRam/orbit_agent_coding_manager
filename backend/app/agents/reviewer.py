from app.agents.base import BaseAgent
from app.models.task import Task

class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="reviewer",
            name="Reviewer",
            role="Code review and verification",
        )

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Reviewer completed: {task.title}",
        }
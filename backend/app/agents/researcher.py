from app.agents.base import BaseAgent
from app.models.task import Task

class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="researcher",
            name="Researcher",
            role="Research and information gathering",
        )

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Researcher completed: {task.title}",
        }
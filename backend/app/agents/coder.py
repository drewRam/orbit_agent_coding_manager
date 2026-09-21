import asyncio

from app.agents.base import BaseAgent
from app.models.task import Task


class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="coder",
            name="Coder",
            role="Implementation",
            capabilities=[
                "coding",
                "implementation",
                "debugging",
            ],
        )

    async def execute(self, task: Task):
        await asyncio.sleep(2)

        # Temporary failure for reassignment testing
        raise RuntimeError(
            "Coder encountered an implementation error."
        )
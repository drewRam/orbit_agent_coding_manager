import asyncio

from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider
from app.models.task import Task


class BackendCoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="backend_coder",
            name="Backend Coder",
            role="Backend implementation",
            capabilities=[
                "coding",
                "implementation",
                "debugging",
                "backend",
            ],
        )

        self.llm = LLMProvider()

    async def execute(self, task: Task):
        await asyncio.sleep(1)

        context = task.input_context or "No previous task context."

        prompt = f"""
You are the Backend Coder agent inside ORBIT.

Your job is to implement the task using the requirements and
research produced by previous agents.

TASK:
{task.title}

DESCRIPTION:
{task.description}

PREVIOUS AGENT CONTEXT:
{context}

Produce a practical implementation plan and the code needed
to accomplish this task.

Consider:
- Requirements from the previous agent
- Correctness
- Edge cases
- Maintainability
- Testing considerations

Return your implementation result in a clear format.
Include code when code is appropriate.
"""

        result = self.llm.generate(prompt)

        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Backend Coder completed: {task.title}",
            "result": result,
        }
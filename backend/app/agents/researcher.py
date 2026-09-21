import asyncio

from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider
from app.models.task import Task


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="researcher",
            name="Researcher",
            role="Research and requirements",
            capabilities=[
                "research",
                "requirements",
                "documentation",
            ],
        )

        self.llm = LLMProvider()

    async def execute(self, task: Task):
        await asyncio.sleep(1)

        prompt = f"""
You are the Researcher agent inside ORBIT.

Your job is to analyze the task and produce useful research
that another agent can directly use.

Task title:
{task.title}

Task description:
{task.description}

Provide:
1. The important requirements.
2. Key technical considerations.
3. Potential risks or edge cases.
4. Concrete recommendations for the implementation agent.

Be concise but useful.

Return ONLY the research findings.
"""

        result = self.llm.generate(prompt)

        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Researcher completed: {task.title}",
            "result": result,
        }
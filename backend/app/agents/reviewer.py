import asyncio

from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider
from app.models.task import Task


class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="reviewer",
            name="Reviewer",
            role="Review and verification",
            capabilities=[
                "review",
                "testing",
                "verification",
            ],
        )

        self.llm = LLMProvider()

    async def execute(self, task: Task):
        await asyncio.sleep(1)

        context = task.input_context or "No implementation context provided."

        prompt = f"""
You are the Reviewer agent inside ORBIT.

Your job is to review the work produced by another agent.

TASK:
{task.title}

DESCRIPTION:
{task.description}

WORK TO REVIEW:
{context}

Evaluate the work for:

1. Correctness
2. Completeness
3. Requirements coverage
4. Bugs or logical problems
5. Edge cases
6. Testing concerns
7. Maintainability

At the end, provide a clear verdict:

VERDICT: APPROVED

or

VERDICT: NEEDS_CHANGES

Then explain why and list any changes that should be made.

Return only the review.
"""

        result = self.llm.generate(prompt)

        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Reviewer completed: {task.title}",
            "result": result,
        }
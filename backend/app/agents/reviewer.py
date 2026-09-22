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

                Your job is to review work produced by another agent.

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

                Decide whether the work is acceptable.

                Return ONLY valid JSON in this exact structure:

                {{
                    "approved": true,
                    "feedback": "Explain your reasoning and any important findings.",
                    "result": "Provide a concise review of the work."
                }}

                Rules:

                - approved must be true or false.
                - Set approved to true only if the work is acceptable.
                - Set approved to false if meaningful changes are required.
                - feedback should explain why.
                - result should summarize the review.
            """

        review = self.llm.generate_json(prompt)

        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Reviewer completed: {task.title}",
            "approved": review.get("approved", False),
            "feedback": review.get("feedback", ""),
            "result": review.get("result", ""),
        }
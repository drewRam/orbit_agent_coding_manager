import asyncio

from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider
from app.models.artifact import AgentOutput
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

        context = (
            task.input_context
            or "No previous task context."
        )

        prompt = f"""
                    You are the Backend Coder agent inside ORBIT.

                    Your job is to produce the actual implementation for the task.

                    TASK:
                    {task.title}

                    DESCRIPTION:
                    {task.description}

                    PREVIOUS AGENT CONTEXT:
                    {context}

                    Create the files necessary to accomplish the task.

                    Rules:

                    - Produce complete, usable file contents.
                    - Do not use placeholders such as "TODO" unless the task
                    explicitly requires one.
                    - Use relative file paths.
                    - Never use absolute paths.
                    - Never use ".." in file paths.
                    - Include tests when appropriate.
                    - Include documentation when appropriate.
                    - Do not claim a file exists unless you provide its contents.

                    Return ONLY valid JSON in this structure:

                    {{
                        "result": "Concise summary of the implementation.",
                        "artifacts": [
                            {{
                                "path": "example.py",
                                "content": "complete file contents",
                                "description": "What this file does"
                            }}
                        ]
                    }}
                """

        raw_result = self.llm.generate_json(prompt)

        output = AgentOutput.model_validate(
            raw_result
        )

        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": (
                f"Backend Coder completed: "
                f"{task.title}"
            ),
            "result": output.result,
            "artifacts": [
                artifact.model_dump()
                for artifact in output.artifacts
            ],
        }
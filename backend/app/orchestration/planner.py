from app.llm.provider import LLMProvider
from app.models.plan import ProjectPlan


class Planner:
    def __init__(self):
        self.llm = LLMProvider()

    def create_plan(self, goal: str) -> ProjectPlan:
        prompt = f"""
You are the planning system for an AI agent orchestration platform called ORBIT.

Your job is to break a user's goal into a practical sequence of tasks.

USER GOAL:
{goal}

Create a project plan that:

1. Breaks the goal into meaningful tasks.
2. Orders tasks using dependencies.
3. Gives each task a clear title.
4. Gives each task a useful description.
5. Assigns a required capability to each task.

Available capabilities:

- research
- requirements
- documentation
- coding
- implementation
- debugging
- backend
- review
- testing
- verification

IMPORTANT:

- Do NOT assign specific agents.
- Do NOT include assigned_agent_id.
- ORBIT will decide which agent performs each task.
- Every task must have a unique id.
- Dependencies must reference existing task IDs.
- Do not create circular dependencies.
- Only create tasks that are necessary to accomplish the goal.

Return ONLY valid JSON in this exact structure:

{{
    "tasks": [
        {{
            "id": "unique_task_id",
            "title": "Task title",
            "description": "Detailed task description",
            "dependencies": [],
            "required_capability": "research"
        }}
    ]
}}
"""

        result = self.llm.generate_json(prompt)

        return ProjectPlan.model_validate(result)
from app.llm.provider import LLMProvider
from app.models.plan import PlannedTask, ProjectPlan
from app.models.project import Project

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

                    STRICT CAPABILITY RULE:

                    The required_capability field MUST contain exactly one
                    of the capabilities listed above.

                    IMPORTANT:

                    - Do NOT assign specific agents.
                    - Do NOT include assigned_agent_id.
                    - ORBIT will decide which agent performs each task.
                    - Every task must have a unique id.
                    - Dependencies must reference existing task IDs.
                    - Do not create circular dependencies.

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

    def replan(self, project: Project, reason: str) -> ProjectPlan:
        current_tasks = []

        for task in project.tasks:
            current_tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "dependencies": task.dependencies,
                    "required_capability": (
                        task.required_capability
                    ),
                    "result": task.result,
                    "review_feedback": task.review_feedback,
                    "failure_reason": task.failure_reason,
                }
            )

        prompt = f"""
                    You are the replanning system for ORBIT.

                    ORBIT is currently executing this project:

                    GOAL:
                    {project.goal}

                    CURRENT TASKS:
                    {current_tasks}

                    REASON FOR REPLANNING:
                    {reason}

                    Your job is to determine what NEW work should be added to
                    the project so ORBIT can continue toward the original goal.

                    IMPORTANT RULES:

                    - Return ONLY NEW tasks.
                    - Do NOT repeat or modify existing tasks.
                    - Every new task ID MUST be unique.
                    - New task IDs should begin with "replan_".
                    - Dependencies may reference existing task IDs.
                    - Dependencies may also reference another new task.
                    - Do not create circular dependencies.
                    - Do NOT assign specific agents.
                    - Use required_capability to describe what kind of worker is needed.

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

                    STRICT CAPABILITY RULE:

                    required_capability MUST be exactly one of the capabilities
                    listed above.

                    Only create tasks that are necessary to address the problem
                    and move the project forward.

                    Return ONLY valid JSON:

                    {{
                        "tasks": [
                            {{
                                "id": "replan_unique_id",
                                "title": "Corrective task",
                                "description": "What needs to be done",
                                "dependencies": [],
                                "required_capability": "coding"
                            }}
                        ]
                    }}
                """

        result = self.llm.generate_json(prompt)

        return ProjectPlan.model_validate(result)
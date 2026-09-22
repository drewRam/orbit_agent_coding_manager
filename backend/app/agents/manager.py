from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider
from app.models.project import Project
from app.models.task import Task
from app.models.plan import ProjectPlan
from app.models.decision import ManagerDecision
from app.orchestration.planner import Planner

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="manager",
            name="Manager",
            role="Project orchestration",
            capabilities=[
                "planning",
                "orchestration",
                "delegation",
                "management",
            ],
        )

        self.planner = Planner()
        self.llm = LLMProvider()

    async def execute(self, task: Task):
        return {
            "agent": self.id,
            "task": task.id,
            "status": "completed",
            "message": f"Manager completed: {task.title}",
        }

    def create_plan(self, goal: str) -> ProjectPlan:
        return self.planner.create_plan(goal)

    def evaluate_project(self, project: Project) -> ManagerDecision:
        task_summary = []

        for task in project.tasks:
            task_summary.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "result": task.result,
                    "review_verdict": task.review_verdict,
                    "review_feedback": task.review_feedback,
                }
            )

        prompt = f"""
                    You are the Manager agent for ORBIT.

                    You supervise an autonomous multi-agent project.

                    PROJECT GOAL:
                    {project.goal}

                    PROJECT TASKS:
                    {task_summary}

                    REPLAN COUNT:
                    {project.replan_count}

                    MAX REPLANS:
                    {project.max_replans}

                    Decide what ORBIT should do next.

                    Choose exactly one action:

                    - "continue" if the current plan should continue.
                    - "replan" if the current plan is no longer sufficient and new
                    or modified tasks are needed.
                    - "complete" if the project has successfully accomplished its goal.

                    Rules:

                    - Do not choose "replan" merely because a task failed once if the
                    existing retry/reassignment system can recover.
                    - Choose "replan" when the current plan itself needs to change.
                    - Never choose "replan" if replan_count has reached max_replans.
                    - Choose "complete" only when the project goal has been adequately
                    accomplished.
                    - Provide a concise reason.

                    Return ONLY valid JSON:

                    {{
                        "action": "continue",
                        "reason": "The current plan can continue."
                    }}
                """

        result = self.llm.generate_json(prompt)

        return ManagerDecision.model_validate(result)

    def generate_final_result(self, project: Project) -> str:
        completed_work = []

        for task in project.tasks:
            completed_work.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "result": task.result,
                    "review_verdict": task.review_verdict,
                    "review_feedback": task.review_feedback,
                }
            )

        prompt = f"""
                    You are the Manager agent for ORBIT.

                    The project has completed all of its tasks.

                    PROJECT NAME:
                    {project.name}

                    PROJECT GOAL:
                    {project.goal}

                    COMPLETED WORK:
                    {completed_work}

                    Create a final project report.

                    The report should contain:

                    1. A concise summary of what was accomplished.
                    2. The major work completed.
                    3. Important implementation or technical details.
                    4. Verification/review results.
                    5. Any limitations or remaining considerations.
                    6. A final conclusion describing the state of the project.

                    Write this as a professional project completion report.

                    Do not claim anything was completed unless it is supported by
                    the task results provided above.
                """

        return self.llm.generate(prompt)
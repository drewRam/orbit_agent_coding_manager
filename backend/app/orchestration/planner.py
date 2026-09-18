from app.models.plan import PlannedTask, ProjectPlan

class Planner:
    def create_plan(self, goal: str) -> ProjectPlan:
        tasks = [
            PlannedTask(
                id="research",
                title="Research requirements",
                description=f"Research the requirements for: {goal}",
                assigned_agent_id="researcher",
                dependencies=[],
            ),
            PlannedTask(
                id="implementation",
                title="Implement solution",
                description=f"Implement the solution for: {goal}",
                assigned_agent_id="coder",
                dependencies=["research"],
            ),
            PlannedTask(
                id="review",
                title="Review implementation",
                description="Review the implementation and verify correctness.",
                assigned_agent_id="reviewer",
                dependencies=["implementation"],
            ),
        ]

        return ProjectPlan(tasks=tasks)
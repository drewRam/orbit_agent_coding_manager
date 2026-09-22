from app.agents.manager import ManagerAgent
from app.models.project import Project
from app.models.task import Task, TaskStatus

project = Project(
    id="replan-test",
    name="Replan Test",
    goal="Build a Python ASCII donut renderer",
    tasks=[
        Task(
            id="research",
            title="Research requirements",
            description="Determine renderer requirements.",
            status=TaskStatus.COMPLETED,
            result="The renderer needs a rotating ASCII donut.",
        ),
        Task(
            id="implementation",
            title="Implement renderer",
            description="Build the renderer.",
            status=TaskStatus.FAILED,
            failure_reason="Implementation does not rotate correctly.",
        ),
    ],
)

manager = ManagerAgent()

reason = (
    "The implementation failed because the renderer "
    "does not rotate correctly."
)

plan = manager.planner.replan(
    project,
    reason,
)

for task in plan.tasks:
    print()
    print("ID:", task.id)
    print("Title:", task.title)
    print("Description:", task.description)
    print("Dependencies:", task.dependencies)
    print("Capability:", task.required_capability)
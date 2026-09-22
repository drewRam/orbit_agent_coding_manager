from app.agents.manager import ManagerAgent
from app.models.project import Project
from app.models.task import Task, TaskStatus

manager = ManagerAgent()

project = Project(
    id="test-project",
    name="Manager Test",
    goal="Build a Python ASCII donut renderer",
    tasks=[
        Task(
            id="research",
            title="Research requirements",
            description="Determine what the renderer needs.",
            status=TaskStatus.COMPLETED,
            result="The renderer should produce a continuously rotating ASCII donut.",
        ),
        Task(
            id="implementation",
            title="Implement renderer",
            description="Build the renderer.",
            status=TaskStatus.IN_PROGRESS,
        ),
    ],
)

decision = manager.evaluate_project(project)

print("ACTION:", decision.action)
print("REASON:", decision.reason)
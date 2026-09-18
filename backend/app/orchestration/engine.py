from app.models.project import Project
from app.models.task import TaskStatus
from app.orchestration.scheduler import Scheduler
from app.agents.registry import AgentRegistry

class OrchestrationEngine:

    def __init__(self):
        self.scheduler = Scheduler()
        self.agents = AgentRegistry()

    async def run(self, project: Project):
        while True:
            ready_tasks = self.scheduler.get_ready_tasks(project.tasks)

            if not ready_tasks:
                break

            for task in ready_tasks:
                await self.execute_task(task)

        return project

    async def execute_task(self, task):
        if task.assigned_agent_id is None:
            raise ValueError(
                f"Task {task.id} has no assigned agent"
            )

        agent = self.agents.get(task.assigned_agent_id)

        if agent is None:
            raise ValueError(
                f"Agent {task.assigned_agent_id} not found"
            )

        task.status = TaskStatus.IN_PROGRESS

        result = await agent.execute(task)

        task.status = TaskStatus.COMPLETED

        return result
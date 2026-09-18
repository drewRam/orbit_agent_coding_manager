from datetime import datetime
from app.models.project import Project
from app.models.task import TaskStatus
from app.orchestration.scheduler import Scheduler
from app.agents.registry import AgentRegistry
from app.events.bus import EventBus
from app.events.types import Event, EventType

class OrchestrationEngine:
    def __init__(self, event_bus: EventBus):
        self.scheduler = Scheduler()
        self.agents = AgentRegistry()
        self.event_bus = event_bus

    async def run(self, project: Project):
        await self.event_bus.publish(
            Event(
                type=EventType.PROJECT_STARTED,
                project_id=project.id,
                message=f"Project started: {project.name}",
                timestamp=datetime.now(),
            )
        )

        for task in project.tasks:
            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_CREATED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=task.assigned_agent_id,
                    message=f"Task created: {task.title}",
                    timestamp=datetime.now(),
                )
            )

        while True:
            ready_tasks = self.scheduler.get_ready_tasks(project.tasks)

            if not ready_tasks:
                break

            for task in ready_tasks:
                await self.event_bus.publish(
                    Event(
                        type=EventType.TASK_READY,
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=task.assigned_agent_id,
                        message=f"Task ready: {task.title}",
                        timestamp=datetime.now(),
                    )
                )

                await self.execute_task(task, project.id)

        await self.event_bus.publish(
            Event(
                type=EventType.PROJECT_COMPLETED,
                project_id=project.id,
                message=f"Project completed: {project.name}",
                timestamp=datetime.now(),
            )
        )

        return project

    async def execute_task(self, task, project_id: str):
        if task.assigned_agent_id is None:
            raise ValueError(
                f"Task {task.id} has no assigned agent"
            )

        agent = self.agents.get(task.assigned_agent_id)

        if agent is None:
            raise ValueError(
                f"Agent {task.assigned_agent_id} not found"
            )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_ASSIGNED,
                project_id=project_id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} assigned to {task.title}",
                timestamp=datetime.now(),
            )
        )

        task.status = TaskStatus.IN_PROGRESS

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STARTED,
                project_id=project_id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} started working",
                timestamp=datetime.now(),
            )
        )

        result = await agent.execute(task)

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_COMPLETED,
                project_id=project_id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} completed the task",
                timestamp=datetime.now(),
            )
        )

        task.status = TaskStatus.COMPLETED

        await self.event_bus.publish(
            Event(
                type=EventType.TASK_COMPLETED,
                project_id=project_id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"Task completed: {task.title}",
                timestamp=datetime.now(),
            )
        )

        return result
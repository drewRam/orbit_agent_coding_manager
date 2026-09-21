from datetime import datetime

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.events.types import EventType, Event
from app.events.bus import EventBus
from app.agents.registry import AgentRegistry
from app.orchestration.scheduler import Scheduler


class OrchestrationEngine:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.scheduler = Scheduler()
        self.agents = AgentRegistry()

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
            ready_tasks = self.scheduler.get_ready_tasks(
                project.tasks
            )

            if not ready_tasks:
                break

            for task in ready_tasks:
                await self.execute_task(
                    project,
                    task,
                )

        all_completed = all(
            task.status == TaskStatus.COMPLETED
            for task in project.tasks
        )

        if all_completed:
            await self.event_bus.publish(
                Event(
                    type=EventType.PROJECT_COMPLETED,
                    project_id=project.id,
                    message=f"Project completed: {project.name}",
                    timestamp=datetime.now(),
                )
            )

    async def execute_task(
        self,
        project: Project,
        task: Task,
    ):
        agent = self.agents.get(
            task.assigned_agent_id
        )

        if agent is None:
            raise RuntimeError(
                f"Agent not found: {task.assigned_agent_id}"
            )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_ASSIGNED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} assigned to {task.title}",
                timestamp=datetime.now(),
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STATUS_CHANGED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} is ready",
                timestamp=datetime.now(),
                data={
                    "status": "READY",
                },
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STATUS_CHANGED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} is thinking",
                timestamp=datetime.now(),
                data={
                    "status": "THINKING",
                },
            )
        )

        task.status = TaskStatus.IN_PROGRESS

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STATUS_CHANGED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} is working",
                timestamp=datetime.now(),
                data={
                    "status": "WORKING",
                },
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STARTED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} started {task.title}",
                timestamp=datetime.now(),
            )
        )

        # ---------------------------------------------------------
        # Build context from completed dependency results
        # ---------------------------------------------------------

        dependency_results = []

        for dependency_id in task.dependencies:
            for previous_task in project.tasks:
                if previous_task.id == dependency_id:
                    if previous_task.result:
                        dependency_results.append(
                            f"Task: {previous_task.title}\n"
                            f"Result: {previous_task.result}"
                        )

        if dependency_results:
            task.input_context = "\n\n".join(
                dependency_results
            )

        # ---------------------------------------------------------
        # Execute agent
        # ---------------------------------------------------------

        try:
            result = await agent.execute(task)

            if isinstance(result, dict):
                task.result = result.get("result")

        except Exception as error:
            task.status = TaskStatus.FAILED
            task.failure_reason = str(error)

            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_FAILED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=agent.id,
                    message=f"{agent.name} failed: {error}",
                    timestamp=datetime.now(),
                    data={
                        "reason": str(error),
                    },
                )
            )

            await self.event_bus.publish(
                Event(
                    type=EventType.AGENT_STATUS_CHANGED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=agent.id,
                    message=f"{agent.name} failed",
                    timestamp=datetime.now(),
                    data={
                        "status": "FAILED",
                    },
                )
            )

            # -----------------------------------------------------
            # Retry
            # -----------------------------------------------------

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING

                await self.event_bus.publish(
                    Event(
                        type=EventType.TASK_RETRYING,
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=agent.id,
                        message=(
                            f"Retrying {task.title} "
                            f"(attempt {task.retry_count})"
                        ),
                        timestamp=datetime.now(),
                        data={
                            "retry_count": task.retry_count,
                        },
                    )
                )

                return

            # -----------------------------------------------------
            # Reassignment
            # -----------------------------------------------------

            new_agent_id = self.find_replacement(
                task,
                failed_agent_id=agent.id,
            )

            if new_agent_id is None:
                raise RuntimeError(
                    f"No compatible agent available "
                    f"for task: {task.title}"
                )

            previous_agent_id = agent.id

            task.assigned_agent_id = new_agent_id
            task.retry_count = 0
            task.status = TaskStatus.PENDING
            task.failure_reason = None

            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_REASSIGNED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=new_agent_id,
                    message=(
                        f"Task {task.title} reassigned "
                        f"from {previous_agent_id} "
                        f"to {new_agent_id}"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "previous_agent": previous_agent_id,
                        "new_agent": new_agent_id,
                    },
                )
            )

            return

        # ---------------------------------------------------------
        # Successful completion
        # ---------------------------------------------------------

        task.status = TaskStatus.COMPLETED

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_COMPLETED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} completed {task.title}",
                timestamp=datetime.now(),
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STATUS_CHANGED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"{agent.name} completed",
                timestamp=datetime.now(),
                data={
                    "status": "COMPLETED",
                },
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.TASK_COMPLETED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=f"Task completed: {task.title}",
                timestamp=datetime.now(),
            )
        )

    def find_replacement(
        self,
        task: Task,
        failed_agent_id: str,
    ) -> str | None:
        capable_agents = self.agents.find_capable_agents(
            task.required_capability
        )

        for agent in capable_agents:
            if agent.id != failed_agent_id:
                return agent.id

        return None
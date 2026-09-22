from datetime import datetime

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.plan import ProjectPlan
from app.models.artifact import Artifact
from app.events.types import EventType, Event
from app.events.bus import EventBus
from app.agents.registry import AgentRegistry
from app.agents.manager import ManagerAgent
from app.orchestration.scheduler import Scheduler


class OrchestrationEngine:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.scheduler = Scheduler()
        self.agents = AgentRegistry()
        self.manager = ManagerAgent()

    async def run(self, project: Project):
        await self.event_bus.publish(
            Event(
                type=EventType.PROJECT_STARTED,
                project_id=project.id,
                message=f"Project started: {project.name}",
                timestamp=datetime.now(),
            )
        )

        # ---------------------------------------------------------
        # Publish initial tasks
        # ---------------------------------------------------------

        for task in project.tasks:
            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_CREATED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=task.assigned_agent_id,
                    message=f"Task created: {task.title}",
                    timestamp=datetime.now(),
                    data={
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "dependencies": task.dependencies,
                        "required_capability": (
                            task.required_capability
                        ),
                    },
                )
            )

        # ---------------------------------------------------------
        # Main orchestration loop
        # ---------------------------------------------------------

        while True:
            ready_tasks = self.scheduler.get_ready_tasks(
                project.tasks
            )

            # -----------------------------------------------------
            # Execute tasks that are ready
            # -----------------------------------------------------

            if ready_tasks:
                for task in ready_tasks:
                    await self.execute_task(
                        project,
                        task,
                    )

                continue

            # -----------------------------------------------------
            # Check project completion
            # -----------------------------------------------------

            all_completed = all(
                task.status == TaskStatus.COMPLETED
                for task in project.tasks
            )

            if all_completed:
                project.final_result = (
                    self.manager.generate_final_result(
                        project
                    )
                )

                await self.event_bus.publish(
                    Event(
                        type=EventType.PROJECT_COMPLETED,
                        project_id=project.id,
                        message=(
                            f"Project completed: "
                            f"{project.name}"
                        ),
                        timestamp=datetime.now(),
                        data={
                            "final_result": (
                                project.final_result
                            ),
                        },
                    )
                )

                return

            # -----------------------------------------------------
            # Ask Manager what should happen
            # -----------------------------------------------------

            decision = self.manager.evaluate_project(
                project
            )

            print(
                f"[MANAGER] {decision.action}: "
                f"{decision.reason}"
            )

            await self.event_bus.publish(
                Event(
                    type=EventType.MANAGER_DECISION,
                    project_id=project.id,
                    message=(
                        f"Manager decided to "
                        f"{decision.action}: "
                        f"{decision.reason}"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "action": decision.action,
                        "reason": decision.reason,
                    },
                )
            )

            # -----------------------------------------------------
            # Manager says complete
            # -----------------------------------------------------

            if decision.action == "complete":
                raise RuntimeError(
                    "Manager attempted to complete "
                    "an incomplete project."
                )

            # -----------------------------------------------------
            # Manager says continue
            # -----------------------------------------------------

            if decision.action == "continue":
                raise RuntimeError(
                    "Manager requested continuation, "
                    "but no tasks are ready."
                )

            # -----------------------------------------------------
            # Manager says replan
            # -----------------------------------------------------

            if decision.action == "replan":
                if (
                    project.replan_count
                    >= project.max_replans
                ):
                    raise RuntimeError(
                        "Maximum project replans reached."
                    )

                project.replan_count += 1

                print(
                    f"[MANAGER] Starting replan "
                    f"{project.replan_count}/"
                    f"{project.max_replans}"
                )

                new_plan = self.manager.planner.replan(
                    project,
                    decision.reason,
                )

                await self.add_replanned_tasks(
                    project,
                    new_plan,
                )

                continue

    async def add_replanned_tasks(
        self,
        project: Project,
        plan: ProjectPlan,
    ):
        existing_ids = {
            task.id
            for task in project.tasks
        }

        new_ids = {
            task.id
            for task in plan.tasks
        }

        # ---------------------------------------------------------
        # Validate duplicate IDs
        # ---------------------------------------------------------

        duplicate_ids = existing_ids.intersection(
            new_ids
        )

        if duplicate_ids:
            raise RuntimeError(
                "Replan produced duplicate task IDs: "
                f"{duplicate_ids}"
            )

        # ---------------------------------------------------------
        # Validate dependencies
        # ---------------------------------------------------------

        all_ids = existing_ids.union(new_ids)

        for planned_task in plan.tasks:
            for dependency_id in planned_task.dependencies:
                if dependency_id not in all_ids:
                    raise RuntimeError(
                        f"Replanned task "
                        f"{planned_task.id} depends on "
                        f"unknown task: "
                        f"{dependency_id}"
                    )

        # ---------------------------------------------------------
        # Create new tasks
        # ---------------------------------------------------------

        for planned_task in plan.tasks:
            agent = self.agents.find_agent_for_task(
                planned_task.required_capability
            )

            if agent is None:
                raise RuntimeError(
                    "No compatible agent available for "
                    f"replanned task: "
                    f"{planned_task.title}"
                )

            task = Task(
                id=planned_task.id,
                title=planned_task.title,
                description=planned_task.description,
                status=TaskStatus.PENDING,
                assigned_agent_id=agent.id,
                dependencies=planned_task.dependencies,
                required_capability=(
                    planned_task.required_capability
                ),
            )

            project.tasks.append(task)

            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_CREATED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=task.assigned_agent_id,
                    message=(
                        f"Task created: "
                        f"{task.title}"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "dependencies": task.dependencies,
                        "required_capability": (
                            task.required_capability
                        ),
                        "replanned": True,
                    },
                )
            )

            print(
                f"[REPLAN] Added task: "
                f"{task.title} → {agent.name}"
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
                f"Agent not found: "
                f"{task.assigned_agent_id}"
            )

        # ---------------------------------------------------------
        # Agent assigned
        # ---------------------------------------------------------

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_ASSIGNED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=(
                    f"{agent.name} assigned to "
                    f"{task.title}"
                ),
                timestamp=datetime.now(),
            )
        )

        # ---------------------------------------------------------
        # Agent ready
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Agent thinking
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Agent working
        # ---------------------------------------------------------

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
                message=(
                    f"{agent.name} started "
                    f"{task.title}"
                ),
                timestamp=datetime.now(),
            )
        )

        # ---------------------------------------------------------
        # Build context from dependencies
        # ---------------------------------------------------------

        dependency_results = []

        for dependency_id in task.dependencies:
            for previous_task in project.tasks:
                if previous_task.id == dependency_id:
                    if previous_task.result:
                        dependency_results.append(
                            f"Task: "
                            f"{previous_task.title}\n"
                            f"Result: "
                            f"{previous_task.result}"
                        )

        context_parts = []

        if dependency_results:
            context_parts.append(
                "\n\n".join(
                    dependency_results
                )
            )

        if task.review_feedback:
            context_parts.append(
                "REVIEWER FEEDBACK:\n"
                f"{task.review_feedback}"
            )

        if context_parts:
            task.input_context = "\n\n".join(
                context_parts
            )

        # ---------------------------------------------------------
        # Execute agent
        # ---------------------------------------------------------

        try:
            result = await agent.execute(task)

            if isinstance(result, dict):
                task.result = result.get(
                    "result"
                )

                task.artifacts = [
                    Artifact.model_validate(
                        artifact
                    )
                    for artifact in result.get(
                        "artifacts",
                        []
                    )
                ]

                if task.required_capability == "review":
                    task.review_verdict = (
                        "approved"
                        if result.get(
                            "approved"
                        ) is True
                        else "needs_changes"
                    )

                    task.review_feedback = (
                        result.get(
                            "feedback",
                            "",
                        )
                    )

        except Exception as error:
            # -----------------------------------------------------
            # Task failed
            # -----------------------------------------------------

            task.status = TaskStatus.FAILED
            task.failure_reason = str(error)

            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_FAILED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=agent.id,
                    message=(
                        f"{agent.name} failed: "
                        f"{error}"
                    ),
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
                    message=(
                        f"{agent.name} failed"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "status": "FAILED",
                    },
                )
            )

            # -----------------------------------------------------
            # Retry same agent
            # -----------------------------------------------------

            if (
                task.retry_count
                < task.max_retries
            ):
                task.retry_count += 1
                task.status = TaskStatus.PENDING

                await self.event_bus.publish(
                    Event(
                        type=EventType.TASK_RETRYING,
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=agent.id,
                        message=(
                            f"Retrying "
                            f"{task.title} "
                            f"(attempt "
                            f"{task.retry_count})"
                        ),
                        timestamp=datetime.now(),
                        data={
                            "retry_count": (
                                task.retry_count
                            ),
                        },
                    )
                )

                return

            # -----------------------------------------------------
            # Reassignment
            # -----------------------------------------------------

            new_agent_id = (
                self.find_replacement(
                    task,
                    failed_agent_id=agent.id,
                )
            )

            if new_agent_id is None:
                raise RuntimeError(
                    "No compatible agent available "
                    f"for task: {task.title}"
                )

            previous_agent_id = agent.id

            task.assigned_agent_id = (
                new_agent_id
            )
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
                        f"Task {task.title} "
                        f"reassigned from "
                        f"{previous_agent_id} "
                        f"to {new_agent_id}"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "previous_agent": (
                            previous_agent_id
                        ),
                        "new_agent": (
                            new_agent_id
                        ),
                    },
                )
            )

            return

        # ---------------------------------------------------------
        # Reviewer quality gate
        # ---------------------------------------------------------

        if (
            task.required_capability
            == "review"
            and task.review_verdict
            == "needs_changes"
        ):
            # -----------------------------------------------------
            # Rework allowed
            # -----------------------------------------------------

            if (
                task.review_cycles
                < task.max_review_cycles
            ):
                task.review_cycles += 1
                task.status = TaskStatus.PENDING

                review_feedback = (
                    task.review_feedback
                    or "Reviewer requested changes."
                )

                for dependency_id in task.dependencies:
                    for previous_task in project.tasks:
                        if (
                            previous_task.id
                            == dependency_id
                        ):
                            previous_task.status = (
                                TaskStatus.PENDING
                            )

                            previous_task.failure_reason = (
                                None
                            )

                            previous_task.review_feedback = (
                                review_feedback
                            )

                            previous_task.review_verdict = (
                                None
                            )

                await self.event_bus.publish(
                    Event(
                        type=EventType.AGENT_COMPLETED,
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=agent.id,
                        message=(
                            f"{agent.name} rejected "
                            f"{task.title}"
                        ),
                        timestamp=datetime.now(),
                    )
                )

                await self.event_bus.publish(
                    Event(
                        type=(
                            EventType.AGENT_STATUS_CHANGED
                        ),
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=agent.id,
                        message=(
                            f"{agent.name} completed "
                            f"review"
                        ),
                        timestamp=datetime.now(),
                        data={
                            "status": "COMPLETED",
                        },
                    )
                )

                await self.event_bus.publish(
                    Event(
                        type=EventType.TASK_RETRYING,
                        project_id=project.id,
                        task_id=task.id,
                        agent_id=agent.id,
                        message=(
                            f"Reviewer rejected "
                            f"{task.title}. "
                            f"Starting rework cycle "
                            f"{task.review_cycles}."
                        ),
                        timestamp=datetime.now(),
                        data={
                            "review_cycle": (
                                task.review_cycles
                            ),
                            "reason": (
                                review_feedback
                            ),
                        },
                    )
                )

                return

            # -----------------------------------------------------
            # Review limit reached
            # -----------------------------------------------------

            task.status = TaskStatus.FAILED
            task.failure_reason = (
                "Maximum review cycles reached. "
                "Work was not approved."
            )

            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_FAILED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=agent.id,
                    message=(
                        f"{task.title} failed review "
                        f"after "
                        f"{task.review_cycles} "
                        f"rework cycles."
                    ),
                    timestamp=datetime.now(),
                    data={
                        "reason": (
                            task.failure_reason
                        ),
                        "review_cycle": (
                            task.review_cycles
                        ),
                    },
                )
            )

            await self.event_bus.publish(
                Event(
                    type=EventType.AGENT_STATUS_CHANGED,
                    project_id=project.id,
                    task_id=task.id,
                    agent_id=agent.id,
                    message=(
                        f"{agent.name} review failed"
                    ),
                    timestamp=datetime.now(),
                    data={
                        "status": "FAILED",
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
                message=(
                    f"{agent.name} completed "
                    f"{task.title}"
                ),
                timestamp=datetime.now(),
            )
        )

        await self.event_bus.publish(
            Event(
                type=EventType.AGENT_STATUS_CHANGED,
                project_id=project.id,
                task_id=task.id,
                agent_id=agent.id,
                message=(
                    f"{agent.name} completed"
                ),
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
                message=(
                    f"Task completed: "
                    f"{task.title}"
                ),
                timestamp=datetime.now(),
            )
        )

    def find_replacement(
        self,
        task: Task,
        failed_agent_id: str,
    ) -> str | None:
        capable_agents = (
            self.agents.find_capable_agents(
                task.required_capability
            )
        )

        for agent in capable_agents:
            if agent.id != failed_agent_id:
                return agent.id

        return None
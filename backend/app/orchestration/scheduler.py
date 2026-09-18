from app.models.task import Task, TaskStatus

class Scheduler:
    def get_ready_tasks(self, tasks: list[Task]) -> list[Task]:
        completed_ids = {
            task.id
            for task in tasks
            if task.status == TaskStatus.COMPLETED
        }

        ready_tasks = []

        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue

            dependencies_met = all(
                dependency_id in completed_ids
                for dependency_id in task.dependencies
            )

            if dependencies_met:
                task.status = TaskStatus.READY
                ready_tasks.append(task)

        return ready_tasks
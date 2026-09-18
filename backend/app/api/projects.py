from fastapi import APIRouter, HTTPException
from app.models.project import Project
from app.models.task import Task
from app.orchestration.engine import OrchestrationEngine
from app.agents.manager import ManagerAgent

router = APIRouter(prefix="/api/projects", tags=["projects"])

projects: dict[str, Project] = {}

@router.post("", response_model=Project)
async def create_project(project: Project):
    projects[project.id] = project
    return project

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = projects.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project

@router.post("/{project_id}/run", response_model=Project)
async def run_project(project_id: str):
    project = projects.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    manager = ManagerAgent()

    if not project.tasks:
        plan = manager.create_plan(project.goal)

        project.tasks = [
            Task(
                id=task.id,
                title=task.title,
                description=task.description,
                status="pending",
                assigned_agent_id=task.assigned_agent_id,
                dependencies=task.dependencies,
            )
            for task in plan.tasks
        ]

    engine = OrchestrationEngine()

    await engine.run(project)

    return project

@router.post("/{project_id}/plan", response_model=Project)
async def plan_project(project_id: str):
    project = projects.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    manager = ManagerAgent()

    plan = manager.create_plan(project.goal)

    project.tasks = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": "pending",
            "assigned_agent_id": task.assigned_agent_id,
            "dependencies": task.dependencies,
        }
        for task in plan.tasks
    ]

    return project
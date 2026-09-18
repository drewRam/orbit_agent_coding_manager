from fastapi import APIRouter, HTTPException
from app.models.project import Project
from app.orchestration.engine import OrchestrationEngine

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

    engine = OrchestrationEngine()

    await engine.run(project)

    return project
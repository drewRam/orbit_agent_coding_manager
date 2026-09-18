from fastapi import APIRouter, HTTPException
from app.models.project import Project

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
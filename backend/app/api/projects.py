import io
import json
import re
import zipfile
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, WebSocket
from app.models.project import Project
from app.models.task import Task
from app.agents.manager import ManagerAgent
from app.agents.registry import AgentRegistry
from app.orchestration.engine import OrchestrationEngine
from app.events.connection import ConnectionManager
from app.events.bus import EventBus

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
)

projects: dict[str, Project] = {}

connection_manager = ConnectionManager()

event_bus = EventBus(connection_manager)

def safe_project_name(name: str) -> str:
    cleaned = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        name,
    )

    return cleaned.strip("_") or "orbit-project"


def build_tasks(plan):
    registry = AgentRegistry()

    tasks = []

    for planned_task in plan.tasks:
        agent = registry.find_agent_for_task(
            planned_task.required_capability
        )

        if agent is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No agent available for capability: "
                    f"{planned_task.required_capability}"
                ),
            )

        tasks.append(
            Task(
                id=planned_task.id,
                title=planned_task.title,
                description=planned_task.description,
                status="pending",
                assigned_agent_id=agent.id,
                dependencies=planned_task.dependencies,
                required_capability=(
                    planned_task.required_capability
                ),
            )
        )

    return tasks


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

    project.tasks = build_tasks(plan)

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

        project.tasks = build_tasks(plan)

    engine = OrchestrationEngine(event_bus)

    await engine.run(project)

    return project


@router.get("/{project_id}/events")
async def get_project_events(project_id: str):
    project = projects.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    events = [
        event
        for event in event_bus.get_events()
        if event.project_id == project_id
    ]

    return events


@router.websocket("/{project_id}/events/ws")
async def websocket_events(
    websocket: WebSocket,
    project_id: str,
):
    project = projects.get(project_id)

    if project is None:
        await websocket.close(code=1008)
        return

    await connection_manager.connect(
        project_id,
        websocket,
    )

    try:
        while True:
            await websocket.receive_text()

    except Exception:
        connection_manager.disconnect(
            project_id,
            websocket,
        )

@router.get("/{project_id}/download")
async def download_project(project_id: str):
    project = projects.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    artifacts = {}

    # Collect artifacts from completed tasks.
    # If two tasks produced the same path,
    # the later artifact replaces the earlier one.
    for task in project.tasks:
        if task.status != "completed":
            continue

        for artifact in task.artifacts:
            artifacts[artifact.path] = artifact

    if not artifacts:
        raise HTTPException(
            status_code=400,
            detail="Project has no generated artifacts.",
        )

    buffer = io.BytesIO()

    project_folder = (
        f"{safe_project_name(project.name)}"
        f"-{project.id}"
    )

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        # Write generated files
        for path, artifact in artifacts.items():
            archive.writestr(
                f"{project_folder}/{path}",
                artifact.content,
            )

        # Write project report
        if project.final_result:
            archive.writestr(
                f"{project_folder}/ORBIT_REPORT.md",
                project.final_result,
            )

        # Write a machine-readable manifest
        manifest = {
            "project_id": project.id,
            "project_name": project.name,
            "goal": project.goal,
            "replan_count": project.replan_count,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "assigned_agent_id": (
                        task.assigned_agent_id
                    ),
                    "artifacts": [
                        {
                            "path": artifact.path,
                            "description": (
                                artifact.description
                            ),
                        }
                        for artifact in task.artifacts
                    ],
                }
                for task in project.tasks
            ],
        }

        archive.writestr(
            f"{project_folder}/ORBIT_MANIFEST.json",
            json.dumps(
                manifest,
                indent=2,
            ),
        )

    buffer.seek(0)

    filename = (
        f"{project_folder}.zip"
    )

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )
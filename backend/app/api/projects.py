from fastapi import APIRouter, HTTPException, WebSocket
from app.models.project import Project
from app.models.task import Task
from app.orchestration.engine import OrchestrationEngine
from app.agents.manager import ManagerAgent
from app.events.bus import EventBus
from app.events.connection import ConnectionManager

router = APIRouter(prefix="/api/projects", tags=["projects"])

projects: dict[str, Project] = {}
connection_manager = ConnectionManager()
event_bus = EventBus(connection_manager)

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

    engine = OrchestrationEngine(event_bus)

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
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(
        self,
        project_id: str,
        websocket: WebSocket,
    ):
        await websocket.accept()

        if project_id not in self.connections:
            self.connections[project_id] = []

        self.connections[project_id].append(websocket)

    def disconnect(
        self,
        project_id: str,
        websocket: WebSocket,
    ):
        if project_id not in self.connections:
            return

        if websocket in self.connections[project_id]:
            self.connections[project_id].remove(websocket)

        if not self.connections[project_id]:
            del self.connections[project_id]

    async def broadcast(
        self,
        project_id: str,
        message: str,
    ):
        connections = self.connections.get(project_id, [])

        for websocket in connections:
            await websocket.send_text(message)
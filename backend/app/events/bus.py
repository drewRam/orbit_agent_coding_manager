from app.events.types import Event
from app.events.connection import ConnectionManager

import json

class EventBus:
    def __init__(self, connection_manager: ConnectionManager):
        self.events: list[Event] = []
        self.connection_manager = connection_manager

    async def publish(self, event: Event):
        self.events.append(event)

        print(
            f"[EVENT] {event.type.value}: {event.message}"
        )

        await self.connection_manager.broadcast(
            event.project_id,
            json.dumps(event.model_dump(mode="json"))
        )

    def get_events(self) -> list[Event]:
        return self.events
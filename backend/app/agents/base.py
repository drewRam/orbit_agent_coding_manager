from abc import ABC, abstractmethod
from app.models.task import Task

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, role: str, capabilities: list[str]):
        self.id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities

    def can_handle(self, capability: str | None) -> bool:
        if capability is None:
            return True

        return capability in self.capabilities

    @abstractmethod
    async def execute(self, task: Task):
        pass
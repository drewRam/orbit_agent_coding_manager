from abc import ABC, abstractmethod
from app.models.task import Task

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, role: str):
        self.id = agent_id
        self.name = name
        self.role = role

    @abstractmethod
    async def execute(self, task: Task):
        pass
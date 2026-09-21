from app.agents.manager import ManagerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.backend_coder import BackendCoderAgent


class AgentRegistry:
    def __init__(self):
        self.agents = {
            "manager": ManagerAgent(),
            "researcher": ResearcherAgent(),
            "coder": CoderAgent(),
            "backend_coder": BackendCoderAgent(),
            "reviewer": ReviewerAgent(),
        }

    def get(self, agent_id: str):
        return self.agents.get(agent_id)

    def all(self):
        return list(self.agents.values())

    def find_capable_agents(
        self,
        capability: str | None,
    ):
        return [
            agent
            for agent in self.agents.values()
            if agent.can_handle(capability)
        ]

    def find_agent_for_task(
        self,
        capability: str | None,
    ):
        capable_agents = self.find_capable_agents(
            capability
        )

        if not capable_agents:
            return None

        return capable_agents[0]
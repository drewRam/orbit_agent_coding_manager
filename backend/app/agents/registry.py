from app.agents.manager import ManagerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.coder import CoderAgent
from app.agents.reviewer import ReviewerAgent

class AgentRegistry:
    def __init__(self):
        self.agents = {
            "manager": ManagerAgent(),
            "researcher": ResearcherAgent(),
            "coder": CoderAgent(),
            "reviewer": ReviewerAgent(),
        }

    def get(self, agent_id: str):
        return self.agents.get(agent_id)

    def all(self):
        return list(self.agents.values())
from app.agents.manager import ManagerAgent

class AgentRegistry:
    def __init__(self):
        self.agents = {
            "manager": ManagerAgent(),
        }

    def get(self, agent_id: str):
        return self.agents.get(agent_id)

    def all(self):
        return list(self.agents.values())
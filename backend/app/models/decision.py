from typing import Literal
from pydantic import BaseModel

DecisionAction = Literal[
    "continue",
    "replan",
    "complete",
]

class ManagerDecision(BaseModel):
    action: DecisionAction
    reason: str
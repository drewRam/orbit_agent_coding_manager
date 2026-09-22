from pathlib import PurePosixPath
from pydantic import BaseModel, field_validator

class Artifact(BaseModel):
    path: str
    content: str
    description: str | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        value = value.replace("\\", "/")

        path = PurePosixPath(value)

        if path.is_absolute():
            raise ValueError(
                "Artifact paths must be relative."
            )

        if ".." in path.parts:
            raise ValueError(
                "Artifact paths cannot contain '..'."
            )

        return str(path)


class AgentOutput(BaseModel):
    result: str
    artifacts: list[Artifact] = []
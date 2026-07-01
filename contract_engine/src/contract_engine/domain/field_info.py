from typing import Any

from pydantic import BaseModel, ConfigDict


class FieldInfo(BaseModel):
    path: str
    type: str
    required: bool
    constraints: dict[str, Any] = {}

    model_config = ConfigDict(extra="forbid")

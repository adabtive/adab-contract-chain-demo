from pydantic import BaseModel, ConfigDict

from contract_engine.domain.types import FieldDefinition, FieldType


class Contract(BaseModel):
    name: str
    version: str

    fields: list[FieldDefinition]
    root_type: FieldType | None = None

    description: str | None = None

    model_config = ConfigDict(extra="forbid")

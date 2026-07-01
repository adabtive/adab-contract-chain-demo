from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: TC003
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Unset:
    def __deepcopy__(self, memo: object) -> _Unset:
        return self

    def __copy__(self) -> _Unset:
        return self


UNSET = _Unset()


class FieldType(BaseModel):
    pass


class PrimitiveKind(StrEnum):
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    NULL = "null"


class PrimitiveType(FieldType):
    kind: PrimitiveKind

    minimum: int | float | None = None
    maximum: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[str | int | float | bool | None] | None = None
    format: str | None = None
    minimum_date_time: datetime | None = None
    maximum_date_time: datetime | None = None
    minimum_date: date | None = None
    maximum_date: date | None = None
    minimum_duration: timedelta | None = None
    maximum_duration: timedelta | None = None
    default: Any = UNSET

    model_config = ConfigDict(extra="forbid")


class AnyType(FieldType):
    model_config = ConfigDict(extra="forbid")


class ObjectType(FieldType):
    fields: list[FieldDefinition] = Field(default_factory=list)
    additional_properties: bool | FieldType = False
    model_config = ConfigDict(extra="forbid")


class ArrayType(FieldType):
    items: FieldType = Field(default_factory=lambda: AnyType())
    prefix_items: list[FieldType] = Field(default_factory=list)
    allow_additional_items: bool = True
    min_items: int | None = None
    max_items: int | None = None

    model_config = ConfigDict(extra="forbid")


class FieldDefinition(BaseModel):
    name: str
    type: FieldType
    required: bool = True

    model_config = ConfigDict(extra="forbid")


class OneOfType(FieldType):
    options: list[FieldType]
    default: Any = UNSET

    model_config = ConfigDict(extra="forbid")


class AnyOfType(FieldType):
    options: list[FieldType]

    model_config = ConfigDict(extra="forbid")


FieldDefinition.model_rebuild()

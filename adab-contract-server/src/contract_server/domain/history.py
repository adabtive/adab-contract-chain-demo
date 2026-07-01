from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventKind(StrEnum):
    VALIDATE = "validate"
    GENERATE = "generate"
    RESPOND = "respond"


class ValidateEvent(BaseModel):
    kind: EventKind = EventKind.VALIDATE
    endpoint_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]
    valid: bool
    errors: list[dict[str, Any]]


class GenerateEvent(BaseModel):
    kind: EventKind = EventKind.GENERATE
    endpoint_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]
    status_code: int
    response_body: dict[str, Any]


class RespondEvent(BaseModel):
    kind: EventKind = EventKind.RESPOND
    endpoint_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_body: dict[str, Any]
    response_body: dict[str, Any] | None
    status_code: int
    request_valid: bool | None
    errors: list[dict[str, Any]]


HistoryEvent = ValidateEvent | GenerateEvent | RespondEvent

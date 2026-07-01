from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SessionState(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    EXPIRED = "expired"


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    endpoint_name: str
    interval_ms: int
    period: str | None = None
    jitter_ms: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    state: SessionState = SessionState.RUNNING

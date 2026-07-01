from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import UUID


class Scheduler(Protocol):
    async def schedule(
        self,
        session_id: UUID,
        callback: Callable[[], Awaitable[None]],
        interval_ms: int,
        jitter_ms: int,
        period: str | None,
        on_expire: Callable[[], Awaitable[None]] | None = None,
    ) -> None: ...

    async def cancel(self, session_id: UUID) -> None: ...

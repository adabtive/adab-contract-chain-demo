import asyncio
import contextlib
import random
from collections.abc import Awaitable, Callable
from uuid import UUID

import isodate


class AsyncioScheduler:
    def __init__(self) -> None:
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    async def schedule(
        self,
        session_id: UUID,
        callback: Callable[[], Awaitable[None]],
        interval_ms: int,
        jitter_ms: int,
        period: str | None,
        on_expire: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        deadline: float | None = None
        if period is not None:
            duration = isodate.parse_duration(period)
            seconds = duration.total_seconds()
            if seconds <= 0:
                msg = f"period '{period}' resolves to zero seconds — use time-based durations like PT1H, not month/year (P1M, P1Y)"
                raise ValueError(msg)
            deadline = asyncio.get_event_loop().time() + seconds

        async def loop() -> None:
            while True:
                if deadline is not None and asyncio.get_event_loop().time() >= deadline:
                    self._tasks.pop(session_id, None)
                    if on_expire is not None:
                        await on_expire()
                    break
                await callback()
                offset = random.randint(-jitter_ms, jitter_ms) if jitter_ms > 0 else 0  # noqa: S311
                sleep_ms = max(1, interval_ms + offset)
                await asyncio.sleep(sleep_ms / 1000)

        self._tasks[session_id] = asyncio.create_task(loop())

    async def cancel(self, session_id: UUID) -> None:
        task = self._tasks.pop(session_id, None)
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

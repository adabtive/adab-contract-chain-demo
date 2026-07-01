import asyncio
import contextlib
from collections import deque

from contract_server.domain.history import HistoryEvent


class InMemoryEventBus:
    def __init__(self, maxlen: int = 100) -> None:
        self._buffer: deque[HistoryEvent] = deque(maxlen=maxlen)
        self._subscribers: dict[asyncio.Queue[HistoryEvent], str | None] = {}

    def publish(self, event: HistoryEvent) -> None:
        self._buffer.append(event)
        for queue, endpoint_filter in self._subscribers.items():
            if endpoint_filter is None or endpoint_filter == event.endpoint_name:
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event)

    def history(self, endpoint: str | None = None) -> list[HistoryEvent]:
        if endpoint is None:
            return list(self._buffer)
        return [e for e in self._buffer if e.endpoint_name == endpoint]

    def add_subscriber(self, queue: asyncio.Queue[HistoryEvent], endpoint: str | None = None) -> None:
        self._subscribers[queue] = endpoint

    def remove_subscriber(self, queue: asyncio.Queue[HistoryEvent]) -> None:
        self._subscribers.pop(queue, None)

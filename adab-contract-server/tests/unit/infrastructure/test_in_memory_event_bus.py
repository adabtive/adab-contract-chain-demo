import asyncio

from contract_server.domain.history import EventKind, ValidateEvent
from contract_server.infrastructure.events.in_memory_event_bus import InMemoryEventBus


def _event(endpoint: str = "ep") -> ValidateEvent:
    return ValidateEvent(endpoint_name=endpoint, payload={}, valid=True, errors=[])


def test_published_event_appears_in_history():
    bus = InMemoryEventBus()
    bus.publish(_event())
    assert len(bus.history()) == 1


def test_history_filtered_by_endpoint():
    bus = InMemoryEventBus()
    bus.publish(_event("a"))
    bus.publish(_event("b"))
    assert len(bus.history("a")) == 1
    assert bus.history("a")[0].endpoint_name == "a"


def test_history_unfiltered_returns_all():
    bus = InMemoryEventBus()
    bus.publish(_event("a"))
    bus.publish(_event("b"))
    assert len(bus.history()) == 2


def test_ring_buffer_evicts_oldest():
    bus = InMemoryEventBus(maxlen=2)
    bus.publish(_event("a"))
    bus.publish(_event("b"))
    bus.publish(_event("c"))
    names = [e.endpoint_name for e in bus.history()]
    assert names == ["b", "c"]


def test_subscriber_receives_event():
    bus = InMemoryEventBus()
    queue: asyncio.Queue[ValidateEvent] = asyncio.Queue()
    bus.add_subscriber(queue)
    bus.publish(_event())
    assert queue.qsize() == 1
    assert queue.get_nowait().kind == EventKind.VALIDATE


def test_subscriber_filtered_by_endpoint():
    bus = InMemoryEventBus()
    queue: asyncio.Queue[ValidateEvent] = asyncio.Queue()
    bus.add_subscriber(queue, endpoint="a")
    bus.publish(_event("a"))
    bus.publish(_event("b"))
    assert queue.qsize() == 1


def test_unfiltered_subscriber_receives_all():
    bus = InMemoryEventBus()
    queue: asyncio.Queue[ValidateEvent] = asyncio.Queue()
    bus.add_subscriber(queue)
    bus.publish(_event("a"))
    bus.publish(_event("b"))
    assert queue.qsize() == 2


def test_remove_subscriber_stops_delivery():
    bus = InMemoryEventBus()
    queue: asyncio.Queue[ValidateEvent] = asyncio.Queue()
    bus.add_subscriber(queue)
    bus.remove_subscriber(queue)
    bus.publish(_event())
    assert queue.qsize() == 0

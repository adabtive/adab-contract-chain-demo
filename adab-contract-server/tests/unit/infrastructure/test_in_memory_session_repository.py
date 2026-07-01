from uuid import uuid4

from contract_server.domain.session import Session
from contract_server.infrastructure.sessions.in_memory_session_repository import InMemorySessionRepository


def test_save_and_get():
    repo = InMemorySessionRepository()
    session = Session(endpoint_name="gen_b", interval_ms=500)
    repo.save(session)

    assert repo.get(session.id) == session


def test_get_unknown_returns_none():
    assert InMemorySessionRepository().get(uuid4()) is None


def test_list_all():
    repo = InMemorySessionRepository()
    s1 = Session(endpoint_name="a", interval_ms=100)
    s2 = Session(endpoint_name="b", interval_ms=200)
    repo.save(s1)
    repo.save(s2)

    result = repo.list_all()
    assert {s.id for s in result} == {s1.id, s2.id}


def test_update():
    from contract_server.domain.session import SessionState

    repo = InMemorySessionRepository()
    session = Session(endpoint_name="gen_b", interval_ms=500)
    repo.save(session)
    session.state = SessionState.STOPPED
    repo.update(session)

    assert repo.get(session.id).state == SessionState.STOPPED


def test_delete_removes_only_target_session():
    repo = InMemorySessionRepository()
    target = Session(endpoint_name="gen_b", interval_ms=500)
    other = Session(endpoint_name="gen_c", interval_ms=200)
    repo.save(target)
    repo.save(other)

    repo.delete(target.id)

    assert repo.get(target.id) is None
    assert repo.get(other.id) == other


def test_delete_nonexistent_is_a_noop():
    InMemorySessionRepository().delete(uuid4())

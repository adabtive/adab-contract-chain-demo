from contract_server.domain.session import Session, SessionState


def test_session_defaults():
    s = Session(endpoint_name="gen_b", interval_ms=500)
    assert s.state == SessionState.RUNNING
    assert s.jitter_ms == 0
    assert s.period is None


def test_session_id_is_unique():
    a = Session(endpoint_name="gen_b", interval_ms=500)
    b = Session(endpoint_name="gen_b", interval_ms=500)
    assert a.id != b.id


def test_session_state_mutation():
    s = Session(endpoint_name="gen_b", interval_ms=500)
    s.state = SessionState.STOPPED
    assert s.state == SessionState.STOPPED

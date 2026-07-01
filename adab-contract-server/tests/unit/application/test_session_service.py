from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from contract_server.application.session_service import SessionService, StartSessionRequest
from contract_server.domain.errors import SessionNotFoundError
from contract_server.domain.session import Session, SessionState


async def test_start_creates_session_and_schedules():
    emission = AsyncMock()
    repo = MagicMock()
    scheduler = AsyncMock()

    request = StartSessionRequest(endpoint_name="gen_b", interval_ms=500)
    session = await SessionService(emission, repo, scheduler).start(request)

    assert session.endpoint_name == "gen_b"
    assert session.interval_ms == 500
    assert session.state == SessionState.RUNNING
    repo.save.assert_called_once_with(session)
    scheduler.schedule.assert_called_once()


async def test_start_passes_period_and_jitter():
    emission = AsyncMock()
    repo = MagicMock()
    scheduler = AsyncMock()

    request = StartSessionRequest(endpoint_name="gen_b", interval_ms=500, period="PT1H", jitter_ms=50)
    session = await SessionService(emission, repo, scheduler).start(request)

    _, kwargs = scheduler.schedule.call_args
    assert kwargs["period"] == "PT1H"
    assert kwargs["jitter_ms"] == 50
    assert session.period == "PT1H"
    assert session.jitter_ms == 50


async def test_stop_marks_session_stopped_and_cancels():
    emission = AsyncMock()
    repo = MagicMock()
    scheduler = AsyncMock()

    session = Session(endpoint_name="gen_b", interval_ms=500)
    repo.get.return_value = session

    await SessionService(emission, repo, scheduler).stop(session.id)

    assert session.state == SessionState.STOPPED
    repo.update.assert_called_once_with(session)
    scheduler.cancel.assert_called_once_with(session.id)


async def test_stop_unknown_session_raises():
    repo = MagicMock()
    repo.get.return_value = None

    with pytest.raises(SessionNotFoundError):
        await SessionService(AsyncMock(), repo, AsyncMock()).stop(UUID("00000000-0000-0000-0000-000000000000"))


def test_list_returns_all_sessions():
    repo = MagicMock()
    sessions = [Session(endpoint_name="gen_b", interval_ms=500)]
    repo.list_all.return_value = sessions

    result = SessionService(AsyncMock(), repo, AsyncMock()).list_sessions()

    assert result == sessions

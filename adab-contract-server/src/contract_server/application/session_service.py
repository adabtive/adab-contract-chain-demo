from dataclasses import dataclass, field
from uuid import UUID

from contract_server.application.emission_service import EmissionService
from contract_server.application.interfaces.scheduler import Scheduler
from contract_server.application.interfaces.session_repository import SessionRepository
from contract_server.domain.errors import SessionNotFoundError
from contract_server.domain.session import Session, SessionState


@dataclass
class StartSessionRequest:
    endpoint_name: str
    interval_ms: int
    period: str | None = None
    jitter_ms: int = field(default=0)


class SessionService:
    def __init__(
        self,
        emission_service: EmissionService,
        session_repository: SessionRepository,
        scheduler: Scheduler,
    ) -> None:
        self._emission = emission_service
        self._repo = session_repository
        self._scheduler = scheduler

    async def start(self, request: StartSessionRequest) -> Session:
        session = Session(
            endpoint_name=request.endpoint_name,
            interval_ms=request.interval_ms,
            period=request.period,
            jitter_ms=request.jitter_ms,
        )

        async def tick() -> None:
            await self._emission.emit(session.endpoint_name)

        async def expire() -> None:
            session.state = SessionState.EXPIRED
            self._repo.update(session)

        await self._scheduler.schedule(
            session_id=session.id,
            callback=tick,
            interval_ms=request.interval_ms,
            jitter_ms=request.jitter_ms,
            period=request.period,
            on_expire=expire,
        )
        self._repo.save(session)
        return session

    async def stop(self, session_id: UUID) -> None:
        session = self._repo.get(session_id)
        if session is None:
            raise SessionNotFoundError(str(session_id))
        session.state = SessionState.STOPPED
        self._repo.update(session)
        await self._scheduler.cancel(session_id)

    def list_sessions(self) -> list[Session]:
        return self._repo.list_all()

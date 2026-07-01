from typing import Any
from uuid import UUID

from contract_engine.domain.validation_result import ValidationResult

from contract_server.application.emission_service import EmissionService
from contract_server.application.interfaces.http_client import HttpResponse
from contract_server.application.respond_service import RespondResult, RespondService
from contract_server.application.session_service import SessionService, StartSessionRequest
from contract_server.application.validation_service import ValidationService
from contract_server.domain.session import Session


class ContractServer:
    def __init__(
        self,
        validation_service: ValidationService,
        emission_service: EmissionService,
        session_service: SessionService,
        respond_service: RespondService,
    ) -> None:
        self._validation = validation_service
        self._emission = emission_service
        self._sessions = session_service
        self._respond = respond_service

    def validate(self, endpoint_name: str, message: dict[str, Any]) -> ValidationResult:
        return self._validation.validate(endpoint_name, message)

    async def emit(self, endpoint_name: str) -> HttpResponse:
        return await self._emission.emit(endpoint_name)

    def respond(self, endpoint_name: str, request_body: dict[str, Any]) -> RespondResult:
        return self._respond.respond(endpoint_name, request_body)

    async def start_session(self, request: StartSessionRequest) -> Session:
        return await self._sessions.start(request)

    async def stop_session(self, session_id: UUID) -> None:
        await self._sessions.stop(session_id)

    def list_sessions(self) -> list[Session]:
        return self._sessions.list_sessions()

from contract_engine.application.contract_engine_factory import create_default_contract_engine

from contract_server.application.contract_server import ContractServer
from contract_server.application.emission_service import EmissionService
from contract_server.application.interfaces.event_bus import EventBus
from contract_server.application.interfaces.http_client import HttpClient
from contract_server.application.interfaces.scheduler import Scheduler
from contract_server.application.interfaces.session_repository import SessionRepository
from contract_server.application.respond_service import RespondService
from contract_server.application.session_service import SessionService
from contract_server.application.validation_service import ValidationService
from contract_server.domain.config import ServerConfig


class ContractServerFactory:
    @staticmethod
    def create(
        config: ServerConfig,
        http_client: HttpClient,
        session_repository: SessionRepository,
        scheduler: Scheduler,
        event_bus: EventBus,
    ) -> ContractServer:
        engine = create_default_contract_engine()
        validation_service = ValidationService(config, engine, event_bus)
        emission_service = EmissionService(config, engine, http_client, event_bus)
        respond_service = RespondService(config, engine, event_bus)
        session_service = SessionService(emission_service, session_repository, scheduler)
        return ContractServer(validation_service, emission_service, session_service, respond_service)

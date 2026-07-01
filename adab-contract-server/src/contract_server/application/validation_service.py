from pathlib import Path
from typing import Any

from contract_engine.application.contract_engine import ContractEngine
from contract_engine.domain.validation_result import ValidationResult

from contract_server.application.interfaces.event_bus import EventBus
from contract_server.domain.config import EndpointType, ServerConfig
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError
from contract_server.domain.history import ValidateEvent


class ValidationService:
    def __init__(self, config: ServerConfig, engine: ContractEngine, event_bus: EventBus) -> None:
        self._config = config
        self._engine = engine
        self._event_bus = event_bus

    def validate(self, endpoint_name: str, message: dict[str, Any]) -> ValidationResult:
        endpoint = self._config.endpoints.get(endpoint_name)
        if endpoint is None:
            raise UnknownEndpointError(endpoint_name)
        if endpoint.type != EndpointType.VALIDATE:
            raise EndpointTypeMismatchError(f"'{endpoint_name}' is not a validate endpoint")

        contracts_dir = Path(self._config.contracts_dir)
        result = self._engine.validate_instance(
            contract_source=str(contracts_dir / endpoint.contract),
            instance=message,
            refinements=endpoint.refinements,
            base_path=contracts_dir,
        )
        self._event_bus.publish(
            ValidateEvent(
                endpoint_name=endpoint_name,
                payload=message,
                valid=result.valid,
                errors=[{"location": e.location, "message": e.message} for e in result.errors],
            )
        )
        return result

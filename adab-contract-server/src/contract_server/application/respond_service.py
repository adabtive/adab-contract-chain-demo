from pathlib import Path
from typing import Any, NamedTuple

from contract_engine.application.contract_engine import ContractEngine

from contract_server.application.interfaces.event_bus import EventBus
from contract_server.domain.config import EndpointType, ServerConfig
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError
from contract_server.domain.history import RespondEvent


class RespondResult(NamedTuple):
    valid: bool
    errors: list[dict[str, Any]]
    data: dict[str, Any] | None
    status_code: int


class RespondService:
    def __init__(self, config: ServerConfig, engine: ContractEngine, event_bus: EventBus) -> None:
        self._config = config
        self._engine = engine
        self._event_bus = event_bus

    def respond(self, endpoint_name: str, request_body: dict[str, Any]) -> RespondResult:
        endpoint = self._config.endpoints.get(endpoint_name)
        if endpoint is None:
            raise UnknownEndpointError(endpoint_name)
        if endpoint.type != EndpointType.RESPOND:
            raise EndpointTypeMismatchError(f"'{endpoint_name}' is not a respond endpoint")

        contracts_dir = Path(self._config.contracts_dir)
        errors: list[dict[str, Any]] = []
        request_valid: bool | None = None

        if endpoint.request_contract:
            validation = self._engine.validate_instance(
                contract_source=str(contracts_dir / endpoint.request_contract),
                instance=request_body,
                base_path=contracts_dir,
            )
            request_valid = validation.valid
            errors = [{"location": e.location, "message": e.message} for e in validation.errors]
            if not request_valid:
                self._event_bus.publish(
                    RespondEvent(
                        endpoint_name=endpoint_name,
                        request_body=request_body,
                        response_body=None,
                        status_code=400,
                        request_valid=False,
                        errors=errors,
                    )
                )
                return RespondResult(valid=False, errors=errors, data=None, status_code=400)

        response_data: dict[str, Any] | None = None
        if endpoint.contract:
            result = self._engine.generate_instance(
                contract_source=str(contracts_dir / endpoint.contract),
                overrides=endpoint.overrides,
                refinements=endpoint.refinements,
                base_path=contracts_dir,
            )
            response_data = result.data

        self._event_bus.publish(
            RespondEvent(
                endpoint_name=endpoint_name,
                request_body=request_body,
                response_body=response_data,
                status_code=endpoint.status_code,
                request_valid=request_valid,
                errors=errors,
            )
        )
        return RespondResult(valid=True, errors=[], data=response_data, status_code=endpoint.status_code)

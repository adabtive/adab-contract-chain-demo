from pathlib import Path

from contract_engine.application.contract_engine import ContractEngine

from contract_server.application.interfaces.event_bus import EventBus
from contract_server.application.interfaces.http_client import HttpClient, HttpResponse
from contract_server.domain.config import EndpointType, ServerConfig
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError
from contract_server.domain.history import GenerateEvent


class EmissionService:
    def __init__(
        self, config: ServerConfig, engine: ContractEngine, http_client: HttpClient, event_bus: EventBus
    ) -> None:
        self._config = config
        self._engine = engine
        self._http_client = http_client
        self._event_bus = event_bus

    async def emit(self, endpoint_name: str) -> HttpResponse:
        endpoint = self._config.endpoints.get(endpoint_name)
        if endpoint is None:
            raise UnknownEndpointError(endpoint_name)
        if endpoint.type != EndpointType.GENERATE:
            raise EndpointTypeMismatchError(f"'{endpoint_name}' is not a generate endpoint")

        contracts_dir = Path(self._config.contracts_dir)
        result = self._engine.generate_instance(
            contract_source=str(contracts_dir / endpoint.contract),
            overrides=endpoint.overrides,
            refinements=endpoint.refinements,
            base_path=contracts_dir,
        )

        base = (endpoint.destination.base_url or self._config.outgoing_base_url).rstrip("/")
        url = base + endpoint.destination.path
        response = await self._http_client.request(endpoint.destination.method, url, result.data)
        self._event_bus.publish(
            GenerateEvent(
                endpoint_name=endpoint_name,
                payload=result.data,
                status_code=response.status_code,
                response_body=response.body,
            )
        )
        return response

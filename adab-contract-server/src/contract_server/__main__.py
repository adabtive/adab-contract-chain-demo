import sys

import uvicorn

from contract_server.adapters.http_api.app import create_app
from contract_server.application.contract_server_factory import ContractServerFactory
from contract_server.infrastructure.config.yaml_config_loader import YamlConfigLoader
from contract_server.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from contract_server.infrastructure.http.httpx_client import HttpxClient
from contract_server.infrastructure.scheduler.asyncio_scheduler import AsyncioScheduler
from contract_server.infrastructure.sessions.in_memory_session_repository import InMemorySessionRepository


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: contract-server <config.yaml>\n")
        sys.exit(1)

    config = YamlConfigLoader().load(sys.argv[1])
    http_client = HttpxClient()
    session_repository = InMemorySessionRepository()
    scheduler = AsyncioScheduler()
    event_bus = InMemoryEventBus()

    server = ContractServerFactory.create(config, http_client, session_repository, scheduler, event_bus)
    app = create_app(server, config, event_bus)

    uvicorn.run(
        app, host=config.host, port=config.port, ssl_certfile=config.ssl_certfile, ssl_keyfile=config.ssl_keyfile
    )


if __name__ == "__main__":
    main()

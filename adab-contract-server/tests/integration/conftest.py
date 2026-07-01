from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from contract_server.adapters.http_api.app import create_app
from contract_server.application.contract_server_factory import ContractServerFactory
from contract_server.application.interfaces.http_client import HttpResponse
from contract_server.infrastructure.sessions.in_memory_session_repository import InMemorySessionRepository


@pytest.fixture
def mock_http():
    http = AsyncMock()
    http.request.return_value = HttpResponse(status_code=200, body={})
    return http


@pytest.fixture
def mock_scheduler():
    return AsyncMock()


@pytest.fixture
def app(server_config, mock_http, mock_scheduler, event_bus):
    repo = InMemorySessionRepository()
    server = ContractServerFactory.create(server_config, mock_http, repo, mock_scheduler, event_bus)
    return create_app(server, server_config, event_bus)


@pytest.fixture
def client(app):
    return TestClient(app)

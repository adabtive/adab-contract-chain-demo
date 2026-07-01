import pytest
from fastapi.testclient import TestClient

from contract_server.adapters.http_api.app import create_app
from contract_server.application.contract_server_factory import ContractServerFactory
from contract_server.domain.config import ServerConfig
from contract_server.infrastructure.sessions.in_memory_session_repository import InMemorySessionRepository
from tests.conftest import CONTRACTS_DIR


@pytest.fixture
def respond_config():
    return ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(CONTRACTS_DIR),
        endpoints={
            "get_a": {"type": "respond", "method": "GET", "contract": "a.json", "status_code": 200},
            "create_a": {
                "type": "respond",
                "method": "POST",
                "request_contract": "a.json",
                "contract": "b.json",
                "status_code": 201,
            },
            "ping": {"type": "respond", "method": "GET", "status_code": 204},
        },
    )


@pytest.fixture
def respond_client(respond_config, mock_http, mock_scheduler, event_bus):
    repo = InMemorySessionRepository()
    server = ContractServerFactory.create(respond_config, mock_http, repo, mock_scheduler, event_bus)
    return TestClient(create_app(server, respond_config, event_bus))


def test_get_respond_returns_generated_body(respond_client):
    response = respond_client.get("/get_a")
    assert response.status_code == 200
    body = response.json()
    assert "name" in body
    assert "value" in body


def test_respond_with_valid_request_body(respond_client):
    response = respond_client.post("/create_a", json={"name": "foo", "value": 42})
    assert response.status_code == 201


def test_respond_with_invalid_request_body_returns_400(respond_client):
    response = respond_client.post("/create_a", json={"bad": "data"})
    assert response.status_code == 400
    assert response.json()["valid"] is False


def test_respond_no_contract_returns_empty(respond_client):
    response = respond_client.get("/ping")
    assert response.status_code == 204


def test_unknown_respond_endpoint_returns_404(respond_client):
    response = respond_client.get("/nonexistent")
    assert response.status_code == 404


def test_wrong_method_returns_405(respond_client):
    response = respond_client.post("/get_a")
    assert response.status_code == 405

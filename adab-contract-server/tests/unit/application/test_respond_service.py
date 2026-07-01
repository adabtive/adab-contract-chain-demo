import pytest

from contract_server.application.respond_service import RespondService
from contract_server.domain.config import ServerConfig
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError


def test_respond_generates_response(server_config, engine, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(server_config.contracts_dir),
        endpoints={"get_a": {"type": "respond", "contract": "a.json", "status_code": 200}},
    )
    result = RespondService(config, engine, event_bus).respond("get_a", {})

    assert result.valid
    assert result.status_code == 200
    assert result.data is not None
    assert "name" in result.data


def test_respond_no_contract_returns_empty(server_config, engine, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(server_config.contracts_dir),
        endpoints={"ping": {"type": "respond", "status_code": 204}},
    )
    result = RespondService(config, engine, event_bus).respond("ping", {})

    assert result.valid
    assert result.status_code == 204
    assert result.data is None


def test_respond_validates_request_body(server_config, engine, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(server_config.contracts_dir),
        endpoints={
            "create_a": {
                "type": "respond",
                "method": "POST",
                "request_contract": "a.json",
                "contract": "b.json",
                "status_code": 201,
            }
        },
    )
    result = RespondService(config, engine, event_bus).respond("create_a", {"name": "foo", "value": 42})
    assert result.valid
    assert result.status_code == 201


def test_respond_returns_400_on_invalid_request(server_config, engine, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(server_config.contracts_dir),
        endpoints={
            "create_a": {
                "type": "respond",
                "method": "POST",
                "request_contract": "a.json",
                "contract": "b.json",
                "status_code": 201,
            }
        },
    )
    result = RespondService(config, engine, event_bus).respond("create_a", {"bad": "data"})
    assert not result.valid
    assert result.status_code == 400
    assert len(result.errors) > 0


def test_respond_unknown_endpoint_raises(server_config, engine, event_bus):
    with pytest.raises(UnknownEndpointError):
        RespondService(server_config, engine, event_bus).respond("nonexistent", {})


def test_respond_wrong_type_raises(server_config, engine, event_bus):
    with pytest.raises(EndpointTypeMismatchError):
        RespondService(server_config, engine, event_bus).respond("validate_a", {})

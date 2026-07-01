import pytest
from pydantic import ValidationError

from contract_server.domain.config import EndpointConfig, EndpointType, ServerConfig


def test_validate_endpoint_needs_no_destination():
    cfg = EndpointConfig(type="validate", contract="a.json")
    assert cfg.type == EndpointType.VALIDATE
    assert cfg.destination is None


def test_generate_endpoint_requires_destination():
    with pytest.raises(ValidationError, match="destination"):
        EndpointConfig(type="generate", contract="b.json")


def test_generate_endpoint_requires_contract():
    with pytest.raises(ValidationError, match="contract"):
        EndpointConfig(type="generate", destination={"path": "/recv"})


def test_generate_endpoint_with_destination():
    cfg = EndpointConfig(type="generate", contract="b.json", destination={"path": "/recv"})
    assert cfg.destination is not None
    assert cfg.destination.path == "/recv"
    assert cfg.destination.method == "POST"


def test_destination_method_uppercased():
    cfg = EndpointConfig(type="generate", contract="b.json", destination={"path": "/recv", "method": "put"})
    assert cfg.destination is not None
    assert cfg.destination.method == "PUT"


def test_endpoint_method_uppercased():
    cfg = EndpointConfig(type="validate", contract="a.json", method="get")
    assert cfg.method == "GET"


def test_respond_endpoint_minimal():
    cfg = EndpointConfig(type="respond")
    assert cfg.type == EndpointType.RESPOND
    assert cfg.contract is None
    assert cfg.status_code == 200


def test_respond_endpoint_full():
    cfg = EndpointConfig(
        type="respond",
        method="POST",
        contract="response.json",
        request_contract="request.json",
        status_code=201,
    )
    assert cfg.request_contract == "request.json"
    assert cfg.status_code == 201


def test_server_config_defaults():
    cfg = ServerConfig(outgoing_base_url="http://localhost:8000", endpoints={})
    assert cfg.host == "0.0.0.0"  # noqa: S104
    assert cfg.port == 8877
    assert cfg.contracts_dir == "./contracts"


def test_server_config_parses_endpoints():
    cfg = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        endpoints={
            "validate_a": {"type": "validate", "contract": "a.json"},
            "gen_b": {"type": "generate", "contract": "b.json", "destination": {"path": "/recv"}},
        },
    )
    assert cfg.endpoints["validate_a"].type == EndpointType.VALIDATE
    assert cfg.endpoints["gen_b"].destination is not None
    assert cfg.endpoints["gen_b"].destination.path == "/recv"

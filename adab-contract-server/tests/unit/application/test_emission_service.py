from unittest.mock import AsyncMock

import pytest

from contract_server.application.emission_service import EmissionService
from contract_server.application.interfaces.http_client import HttpResponse
from contract_server.domain.config import ServerConfig
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError
from contract_server.domain.history import EventKind


async def test_emit_posts_generated_data_to_destination(server_config, engine, event_bus):
    http = AsyncMock()
    http.request.return_value = HttpResponse(status_code=200, body={})

    response = await EmissionService(server_config, engine, http, event_bus).emit("gen_b")

    assert response.status_code == 200
    method, url, payload = http.request.call_args.args
    assert method == "POST"
    assert url == "http://localhost:8000/recv"
    assert "id" in payload
    assert "count" in payload

    events = event_bus.history("gen_b")
    assert len(events) == 1
    assert events[0].kind == EventKind.GENERATE


async def test_emit_uses_configured_destination_method(engine, contracts_dir, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(contracts_dir),
        endpoints={
            "gen_b": {"type": "generate", "contract": "b.json", "destination": {"path": "/recv", "method": "PUT"}}
        },
    )
    http = AsyncMock()
    http.request.return_value = HttpResponse(status_code=200, body={})

    await EmissionService(config, engine, http, event_bus).emit("gen_b")

    method, _, _ = http.request.call_args.args
    assert method == "PUT"


async def test_emit_strips_trailing_slash_from_base_url(engine, contracts_dir, event_bus):
    config = ServerConfig(
        outgoing_base_url="http://localhost:8000/",
        contracts_dir=str(contracts_dir),
        endpoints={"gen_b": {"type": "generate", "contract": "b.json", "destination": {"path": "/recv"}}},
    )
    http = AsyncMock()
    http.request.return_value = HttpResponse(status_code=200, body={})

    await EmissionService(config, engine, http, event_bus).emit("gen_b")

    _, url, _ = http.request.call_args.args
    assert url == "http://localhost:8000/recv"


async def test_emit_unknown_endpoint_raises(server_config, engine, event_bus):
    with pytest.raises(UnknownEndpointError):
        await EmissionService(server_config, engine, AsyncMock(), event_bus).emit("nonexistent")


async def test_emit_validate_endpoint_raises_type_mismatch(server_config, engine, event_bus):
    with pytest.raises(EndpointTypeMismatchError):
        await EmissionService(server_config, engine, AsyncMock(), event_bus).emit("validate_a")

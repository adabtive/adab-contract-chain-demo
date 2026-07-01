import contextlib
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from contract_server.application.contract_server import ContractServer
from contract_server.domain.config import EndpointType, ServerConfig


def create_router(server: ContractServer, config: ServerConfig) -> APIRouter:
    router = APIRouter()
    for name, endpoint in config.endpoints.items():
        if endpoint.type == EndpointType.RESPOND:
            _add_route(router, server, name, endpoint.method)
    return router


def _add_route(router: APIRouter, server: ContractServer, endpoint_name: str, method: str) -> None:
    async def handle(request: Request) -> JSONResponse:
        body: dict[str, Any] = {}
        if method not in ("GET", "HEAD", "DELETE"):
            with contextlib.suppress(json.JSONDecodeError):
                body = await request.json()

        result = server.respond(endpoint_name, body)
        if not result.valid:
            return JSONResponse({"valid": False, "errors": result.errors}, status_code=400)
        return JSONResponse(result.data or {}, status_code=result.status_code)

    router.add_api_route(f"/{endpoint_name}", handle, methods=[method])

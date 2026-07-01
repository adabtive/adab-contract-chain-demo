from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from contract_server.application.contract_server import ContractServer
from contract_server.domain.config import EndpointType, ServerConfig


def create_router(server: ContractServer, config: ServerConfig) -> APIRouter:
    router = APIRouter()
    for name, endpoint in config.endpoints.items():
        if endpoint.type == EndpointType.GENERATE:
            _add_route(router, server, name, endpoint.method)
    return router


def _add_route(router: APIRouter, server: ContractServer, endpoint_name: str, method: str) -> None:
    async def handle() -> JSONResponse:
        response = await server.emit(endpoint_name)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Destination returned {response.status_code}")
        return JSONResponse({"sent": True, "destination_status": response.status_code})

    router.add_api_route(f"/{endpoint_name}", handle, methods=[method])

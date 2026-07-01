from pathlib import Path
from typing import Any
from uuid import UUID

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from contract_server.application.contract_server import ContractServer
from contract_server.application.session_service import StartSessionRequest
from contract_server.domain.errors import SessionNotFoundError

_CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent / "infrastructure" / "contracts"


def create_router(server: ContractServer) -> APIRouter:
    engine = create_default_contract_engine()
    router = APIRouter(prefix="/sessions")

    @router.post("", status_code=201)
    async def start_session(request: dict[str, Any]) -> JSONResponse:
        result = engine.validate_instance(
            contract_source=str(_CONTRACTS_DIR / "start_session.json"),
            instance=request,
            base_path=_CONTRACTS_DIR,
        )
        if not result.valid:
            raise HTTPException(
                status_code=422,
                detail=[{"location": e.location, "message": e.message} for e in result.errors],
            )
        req = StartSessionRequest(
            endpoint_name=request["endpoint"],
            interval_ms=request["interval_ms"],
            period=request.get("period"),
            jitter_ms=request.get("jitter_ms", 0),
        )
        session = await server.start_session(req)
        return JSONResponse({"session_id": str(session.id)}, status_code=201)

    @router.get("")
    def list_sessions() -> JSONResponse:
        sessions = server.list_sessions()
        return JSONResponse(
            [
                {
                    "session_id": str(s.id),
                    "endpoint_name": s.endpoint_name,
                    "interval_ms": s.interval_ms,
                    "period": s.period,
                    "jitter_ms": s.jitter_ms,
                    "started_at": s.started_at.isoformat(),
                    "state": s.state,
                }
                for s in sessions
            ]
        )

    @router.delete("/{session_id}", status_code=204)
    async def stop_session(session_id: UUID) -> None:
        try:
            await server.stop_session(session_id)
        except SessionNotFoundError as err:
            raise HTTPException(status_code=404, detail="Session not found") from err

    return router

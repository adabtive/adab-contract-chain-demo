import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from contract_server.application.contract_server import ContractServer
from contract_server.application.interfaces.event_bus import EventBus
from contract_server.application.session_service import StartSessionRequest
from contract_server.domain.config import EndpointType, ServerConfig
from contract_server.domain.errors import SessionNotFoundError
from contract_server.domain.history import HistoryEvent  # noqa: TC001

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["tojson"] = lambda obj, indent=None: json.dumps(obj, indent=indent, ensure_ascii=False, default=str)  # type: ignore[assignment]
    return env


def _format_sse(event_name: str, html: str) -> str:
    lines = "\n".join(f"data: {line}" for line in html.splitlines())
    return f"event: {event_name}\n{lines}\n\n"


async def _sse_stream(
    bus: EventBus,
    endpoint: str | None,
    env: Environment,
) -> AsyncGenerator[str]:
    queue: asyncio.Queue[HistoryEvent] = asyncio.Queue()
    bus.add_subscriber(queue, endpoint)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                html = env.get_template("partials/history_event.html").render(event=event)
                yield _format_sse("history_event", html)
            except TimeoutError:
                yield ": keepalive\n\n"
    finally:
        bus.remove_subscriber(queue)


def create_router(server: ContractServer, config: ServerConfig, event_bus: EventBus) -> APIRouter:
    router = APIRouter(prefix="/ui")
    env = _make_env()
    engine = create_default_contract_engine()
    contracts_dir = Path(config.contracts_dir)
    generate_endpoint_names = [n for n, e in config.endpoints.items() if e.type == EndpointType.GENERATE]

    def render(template: str, **ctx: Any) -> str:
        return env.get_template(template).render(config=config, **ctx)

    @router.get("/", response_class=HTMLResponse)
    def overview() -> HTMLResponse:
        events = list(reversed(event_bus.history()))
        return HTMLResponse(render("overview.html", events=events))

    @router.get("/endpoints/{name}", response_class=HTMLResponse)
    def endpoint_detail(name: str) -> HTMLResponse:
        endpoint = config.endpoints.get(name)
        if endpoint is None:
            raise HTTPException(status_code=404)
        events = list(reversed(event_bus.history(name)))
        return HTMLResponse(
            render(
                "endpoint_detail.html",
                name=name,
                endpoint=endpoint,
                events=events,
                generate_endpoint_names=generate_endpoint_names,
            )
        )

    @router.get("/sessions", response_class=HTMLResponse)
    def sessions_page() -> HTMLResponse:
        sessions = server.list_sessions()
        return HTMLResponse(
            render(
                "sessions.html",
                sessions=sessions,
                generate_endpoint_names=generate_endpoint_names,
            )
        )

    @router.get("/contracts/{name}", response_class=HTMLResponse)
    def contract_detail(name: str) -> HTMLResponse:
        contract_path = contracts_dir / name
        if not contract_path.is_file() or contract_path.suffix != ".json":
            raise HTTPException(status_code=404)
        schema = json.loads(contract_path.read_text())
        fields = engine.inspect_contract(str(contract_path), base_path=contracts_dir)
        return HTMLResponse(
            render(
                "contract_detail.html",
                name=name,
                schema_json=json.dumps(schema, indent=2),
                fields=fields,
            )
        )

    @router.get("/events/all")
    async def events_all() -> StreamingResponse:
        return StreamingResponse(
            _sse_stream(event_bus, None, env),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.get("/events/{endpoint_name}")
    async def events_endpoint(endpoint_name: str) -> StreamingResponse:
        return StreamingResponse(
            _sse_stream(event_bus, endpoint_name, env),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.post("/emit/{endpoint_name}", response_class=HTMLResponse)
    async def emit_now(endpoint_name: str) -> HTMLResponse:
        try:
            response = await server.emit(endpoint_name)
            ok = response.status_code < 400
            return HTMLResponse(
                render("partials/emit_result.html", ok=ok, status_code=response.status_code, error=None)
            )
        except Exception as e:
            return HTMLResponse(render("partials/emit_result.html", ok=False, status_code=None, error=str(e)))

    @router.post("/sessions/start")
    async def start_session_ui(
        endpoint: Annotated[str, Form()],
        interval_ms: Annotated[int, Form()],
        period: Annotated[str | None, Form()] = None,
        jitter_ms: Annotated[int, Form()] = 0,
    ) -> Response:
        try:
            await server.start_session(
                StartSessionRequest(
                    endpoint_name=endpoint,
                    interval_ms=interval_ms,
                    period=period or None,
                    jitter_ms=jitter_ms,
                )
            )
        except Exception as e:
            return HTMLResponse(render("partials/start_session_error.html", error=str(e)))
        return Response(status_code=200, headers={"HX-Redirect": "/ui/sessions"})

    @router.delete("/sessions/{session_id}")
    async def stop_session_ui(session_id: UUID) -> Response:
        with contextlib.suppress(SessionNotFoundError):
            await server.stop_session(session_id)
        return Response(status_code=200, headers={"HX-Redirect": "/ui/sessions"})

    return router

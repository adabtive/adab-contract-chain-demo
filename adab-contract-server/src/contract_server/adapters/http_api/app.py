from pathlib import Path

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.exceptions import HTTPException

from contract_server.adapters.http_api.routers import generate, respond, sessions, ui, validate
from contract_server.application.contract_server import ContractServer
from contract_server.application.interfaces.event_bus import EventBus
from contract_server.domain.config import ServerConfig

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


def create_app(server: ContractServer, config: ServerConfig, event_bus: EventBus) -> FastAPI:
    app = FastAPI(title="Contract Server")

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse | JSONResponse:
        if request.url.path.startswith("/ui"):
            html = env.get_template("404.html").render(message=exc.detail or "The page you requested does not exist.")
            return HTMLResponse(html, status_code=exc.status_code)
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.include_router(validate.create_router(server, config))
    app.include_router(generate.create_router(server, config))
    app.include_router(respond.create_router(server, config))
    app.include_router(sessions.create_router(server))
    app.include_router(ui.create_router(server, config, event_bus))
    return app

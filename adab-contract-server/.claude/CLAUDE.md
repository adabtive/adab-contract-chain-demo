# Contract Server

## Billing
eteck

Config-driven HTTP mock server wrapping `contract_engine`. Three endpoint types: validate inbound messages, generate and emit contract-valid messages to a destination, or respond to requests with contract-valid bodies.

## Stack
Python 3.13, FastAPI, uvicorn, httpx, pyyaml, isodate, pydantic v2, pytest, uv, hatchling, Nix flakes

## Sibling dependency
`contract_engine` lives at `../contract_engine`. Referenced as a local editable dependency via `[tool.uv.sources]` in pyproject.toml. Always install with `uv sync` — not pip.

## Commands
```bash
# Enter dev environment (Nix + direnv)
direnv allow    # first time only
direnv reload   # after pyproject.toml changes

# Install / sync
uv sync --group dev

# Run tests
pytest

# Run server
contract-server mock.yaml

# Run example (3 containers: producer, validator, responder)
docker compose up --build
```

## Architecture
Hexagonal / DDD, mirroring `contract_engine`. Layers:

```
domain/          Pure value objects: ServerConfig, EndpointConfig, Session, errors
application/     Services + Protocol ports (no I-prefix — just ConfigLoader, HttpClient, etc.)
infrastructure/  Concrete impls: YamlConfigLoader, HttpxClient, InMemorySessionRepository, AsyncioScheduler, InMemoryEventBus
adapters/        Inbound HTTP: FastAPI app + routers (validate, generate, respond, sessions, ui)
```

See `.claude/DESIGN.md` for full data-flow diagrams and `.claude/DECISIONS.md` for architectural choices.

## Key files
- `src/contract_server/application/contract_server_factory.py` — wires everything
- `src/contract_server/adapters/http_api/app.py` — FastAPI app factory
- `src/contract_server/adapters/http_api/routers/` — validate, generate, respond, sessions, ui routers
- `src/contract_server/adapters/http_api/templates/` — Jinja2 + HTMX UI
- `src/contract_server/infrastructure/scheduler/asyncio_scheduler.py` — interval session scheduler
- `src/contract_server/infrastructure/events/in_memory_event_bus.py` — ring buffer + SSE fan-out
- `src/contract_server/infrastructure/contracts/start_session.json` — built-in schema for POST /sessions (dogfooded)
- `tests/conftest.py` — shared fixtures: `engine`, `server_config`, `contracts_dir`, `event_bus`
- `tests/integration/conftest.py` — FastAPI TestClient with mock http + mock scheduler
- `tests/fixtures/contracts/a.json` + `b.json` — real Draft 7 schemas used in all tests
- `example/` — EnergyPod docker-compose demo (producer, validator, responder)

## Endpoints
All endpoints are dynamically mounted from YAML config at startup.

| Pattern | Type | Behaviour |
|---|---|---|
| `{method} /{name}` | validate | Validates body against contract → 200 or 400 with errors |
| `{method} /{name}` | generate | Generates instance, sends to destination → 200 or 502 |
| `{method} /{name}` | respond | Optionally validates request, returns generated response body |
| `POST /sessions` | control | Starts interval emission loop → 201 `{session_id}` |
| `GET /sessions` | control | Lists active sessions |
| `DELETE /sessions/{id}` | control | Stops session → 204 or 404 |
| `GET /ui/` | ui | HTMX browser UI with live SSE event feed |

## Gotchas
- `contract_engine` uses `Draft7Validator` internally — fixture schemas use `draft-07`, not `2020-12`
- No `types-isodate` on PyPI — do not add it to dev deps
- Protocol classes (ports) have no `I` prefix — `HttpClient` not `IHttpClient`
- `GenerationResult.data` holds the generated dict — not `.instance`
- Factory function is `create_default_contract_engine()` — not `create_default_engine()`
- Routes are added at app construction time — no hot-reload of config without restart
- `AsyncioScheduler` uses `asyncio.get_event_loop()` — must run inside an asyncio event loop (FastAPI guarantees this)
- ISO 8601 period must be time-based (`PT1H`, `PT30M`) — month/year durations (`P1M`, `P1Y`) resolve to 0 seconds via isodate and are rejected at session start
- HTMX only swaps content on 2xx responses — UI error partials must return 200
- Dockerfile build context is `..` (parent of this repo) — `contract_engine` is copied from the sibling path

## TODO

### In progress

### Backlog
- **Outgoing auth** — add auth support for outgoing HTTP requests. Static headers (API keys, Bearer tokens) first: add `headers: dict` to `Destination`, pass through in `HttpxClient`. OAuth2/token refresh as a follow-up: `TokenProvider` injected into `HttpxClient`.
- **Transport abstraction** — support message buses (Kafka, NATS, MQTT) as emit destinations. `HttpClient` becomes a general `Transport` with `send(destination, payload)`. `destination` becomes a tagged union: `{type: http, path, method}`, `{type: kafka, topic, broker}`, `{type: nats, subject}`. Look at how `contract_engine` modelled its transport layer before starting.
- **Effects model (service virtualization)** — replace the `type` field with a composable `effects` list. Design fully specified in `DECISIONS.md` (2026-06-04). Each effect is `respond`, `http`, or `messagebus`. Conditional execution via `when:` (single field/operator/value, no combinators). Branching via `when:`/`default:` blocks. Named effects for cross-referencing. `request_contract` at endpoint level for fail-fast request validation.
- **Query param awareness** — respond service currently sees only request body; query params not addressable. Requires passing full request context through the service layer.

### Blocked

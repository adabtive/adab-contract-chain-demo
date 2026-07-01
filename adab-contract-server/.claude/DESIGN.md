# Contract Server — Design

## Purpose

Config-driven HTTP server that wraps `contract_engine` to provide two runtime roles:

- **Enforcement** (inbound): validate incoming messages against a contract, return 200 or structured 400
- **Emission** (outbound): generate contract-valid instances and POST them to a target endpoint, on-demand or on an interval

Configured entirely via a single YAML file + a folder of JSON Schema contracts. No code required from the user.

---

## Architecture: Hexagonal / DDD

Mirrors `contract_engine`. Dependency rule: domain ← application ← infrastructure / adapters.

```
domain/          Pure value objects and errors. No external deps.
application/     Use-case services + port interfaces. Depends only on domain.
infrastructure/  Implements ports: YAML loader, httpx client, asyncio scheduler, in-memory sessions.
adapters/        Inbound HTTP adapter (FastAPI). Mounts dynamic routes from config.
```

---

## Layer detail

### domain/

| File | Contents |
|---|---|
| `config.py` | `ServerConfig`, `EndpointConfig`, `EndpointType` (validate \| generate) |
| `session.py` | `Session`, `SessionState` (running \| stopped \| expired) |
| `errors.py` | `UnknownEndpointError`, `EndpointTypeMismatchError`, `SessionNotFoundError` |

`EndpointConfig` holds: type, contract path, optional refinements, optional overrides, destination (generate only).

`Session` holds: id (UUID), endpoint name, interval_ms, period (optional ISO 8601), jitter_ms (optional), started_at, tick_count, state.

### application/

**Interfaces (ports)**:

| Interface | Responsibility |
|---|---|
| `IConfigLoader` | Load YAML → `ServerConfig` |
| `IHttpClient` | POST JSON to a URL, return status + body |
| `ISessionRepository` | CRUD for `Session` objects |
| `IScheduler` | Schedule/cancel recurring async callbacks |

**Services**:

| Service | Responsibility |
|---|---|
| `ValidationService` | Resolve endpoint config, call `contract_engine.validate_instance`, return `ValidationResult` |
| `EmissionService` | Resolve endpoint config, call `contract_engine.generate_instance`, POST via `IHttpClient` |
| `SessionService` | Start/stop/list sessions; delegates ticks to `EmissionService` via `IScheduler` |

**Facade**: `ContractServer` — thin wrapper over the three services, public API.

**Factory**: `ContractServerFactory` — wires all dependencies, accepts a `ServerConfig`.

### infrastructure/

| Module | Implements |
|---|---|
| `config/yaml_config_loader.py` | `IConfigLoader` — PyYAML + Pydantic validation |
| `http/httpx_client.py` | `IHttpClient` — async httpx |
| `sessions/in_memory_session_repository.py` | `ISessionRepository` — dict, sufficient for demo scope |
| `scheduler/asyncio_scheduler.py` | `IScheduler` — asyncio tasks, handles interval + jitter + period expiry |
| `contracts/` | Built-in JSON Schema files for the control API (`start_session.json`, `stop_session.json`) |

### adapters/http_api/

FastAPI app factory. Reads `ServerConfig` at startup and mounts routes dynamically:

- One `POST /{endpoint_name}` per validate endpoint
- One `POST /{endpoint_name}` per generate endpoint (fires single emission)
- `/sessions` router: `POST`, `GET`, `DELETE /{id}`

The sessions control API is itself contract-validated — `POST /sessions` body is validated against the built-in `start_session.json` schema before processing. Dogfooding.

---

## Data flows

### Validate

```
POST /{endpoint_name}  body: raw message
  → ValidationService.validate(endpoint_name, body)
      → contract_engine.validate_instance(contract, body, base_path)
          → 200 {valid: true}  |  400 {valid: false, errors: [{path, message}]}
```

### Generate (single)

```
POST /{endpoint_name}  (no body)
  → EmissionService.emit(endpoint_name)
      → contract_engine.generate_instance(contract, overrides, refinements)
      → IHttpClient.post(outgoing_base_url + destination, generated_instance)
          → 200 {sent: true, destination: "..."}
```

### Session lifecycle

```
POST /sessions  body: {endpoint, interval_ms, period?, jitter_ms?}
  → validated against start_session.json contract
  → SessionService.start(request)
      → Session created, stored in ISessionRepository
      → IScheduler.schedule(tick_fn, interval_ms, jitter_ms, period)
          → each tick: EmissionService.emit(endpoint_name)
  → 201 {session_id: "..."}

DELETE /sessions/{id}
  → SessionService.stop(id)
      → IScheduler.cancel(session_id)
      → Session.state = stopped
  → 204
```

---

## Entry point

```bash
python -m contract_server mock.yaml
```

`__main__.py` loads config via `IConfigLoader`, builds `ContractServer` via factory, passes to adapter which builds and starts the FastAPI app with uvicorn.

---

## Package structure

```
contract_server/
├── pyproject.toml
└── src/contract_server/
    ├── __init__.py
    ├── __main__.py
    ├── domain/
    │   ├── config.py
    │   ├── session.py
    │   └── errors.py
    ├── application/
    │   ├── contract_server.py
    │   ├── contract_server_factory.py
    │   ├── validation_service.py
    │   ├── emission_service.py
    │   ├── session_service.py
    │   └── interfaces/
    │       ├── http_client.py
    │       ├── config_loader.py
    │       ├── session_repository.py
    │       └── scheduler.py
    ├── infrastructure/
    │   ├── config/yaml_config_loader.py
    │   ├── http/httpx_client.py
    │   ├── sessions/in_memory_session_repository.py
    │   ├── scheduler/asyncio_scheduler.py
    │   └── contracts/
    │       ├── start_session.json
    │       └── stop_session.json
    └── adapters/
        └── http_api/
            ├── app.py
            └── routers/
                ├── validate.py
                ├── generate.py
                └── sessions.py
```

# contract-server

A config-driven HTTP mock server for contract-based testing. Point it at a YAML file and a folder of JSON Schema contracts — no code required.

Four endpoint types:

- **validate** — accepts inbound messages and validates them against a contract
- **generate** — generates a contract-valid message and sends it to a destination
- **respond** — receives a request, optionally validates the body, and responds with a generated contract-valid payload
- **sessions** — runs a generate endpoint on a repeating interval in the background

A browser UI at `/ui/` gives a live view of all endpoints, contracts, and event history.

---

## Install

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo>
cd adab-contract-server
uv sync
```

`contract_engine` is a local sibling dependency at `../contract_engine`. Clone it alongside this repo before running `uv sync`.

---

## Quickstart

**1. Write a config file**

```yaml
# mock.yaml
display_name: "my-mock"
outgoing_base_url: "http://localhost:9000"
contracts_dir: "./contracts"

endpoints:
  ingest_event:
    type: validate
    contract: event.json

  emit_event:
    type: generate
    contract: event.json
    destination:
      path: /events

  get_event:
    type: respond
    method: GET
    contract: event.json
    status_code: 200
```

**2. Add your contracts**

Place JSON Schema (Draft 7) files in the `contracts_dir` folder.

**3. Start the server**

```bash
contract-server mock.yaml
```

The server starts on `http://0.0.0.0:8877` by default. Open `http://localhost:8877/ui/` for the browser UI.

---

## Configuration reference

```yaml
host: "0.0.0.0"              # optional, default: 0.0.0.0
port: 8877                    # optional, default: 8877
display_name: "Contract Server"  # optional: shown in the UI
outgoing_base_url: "..."      # required: base URL for outgoing requests
contracts_dir: "./contracts"  # optional, default: ./contracts

endpoints:
  <name>:
    type: validate | generate | respond   # required
    method: POST                          # optional: HTTP method this endpoint listens on (default: POST)
    contract: <filename.json>             # required for validate/generate; optional for respond
    refinements: {}                       # optional: schema constraints applied before generation
    overrides: {}                         # optional: field values applied after generation
    destination:                          # required for generate
      path: /path                         # appended to outgoing_base_url
      method: POST                        # optional: outgoing HTTP method (default: POST)
    status_code: 200                      # respond only: HTTP status code to return (default: 200)
    request_contract: <filename.json>     # respond only: validate the incoming body before responding
```

**`overrides`** force specific field values on the generated output after generation. Each key is a dot-path; the value replaces whatever was generated:

```yaml
overrides:
  status: "unknown"          # set status to a fixed string
  metrics.voltage: 42.0      # nested path
```

**`refinements`** narrow the contract before generation — the engine generates within the tightened constraints. Each key is a dot-path; the value is a **constraint object**, not a bare value:

```yaml
refinements:
  status:
    const: "interrupted"     # pin to a single value
  metrics.voltage:
    minimum: 10
    maximum: 100
  session_id:
    pattern: "^test-"
```

Common constraint keys: `const`, `enum`, `minimum`, `maximum`, `min_length`, `max_length`, `pattern`, `format`. A bare string like `status: "interrupted"` is invalid — it must be wrapped as `status: {const: "interrupted"}`.

See the contract_engine README for the full constraint reference and wildcard array paths (`sensors[*].value`).

---

## Endpoint types

### validate

Accepts a request body and validates it against the contract.

```
POST /{name}        # method: configurable via 'method' field
Content-Type: application/json
```

**Success**
```json
HTTP 200
{ "valid": true }
```

**Validation failure**
```json
HTTP 400
{
  "valid": false,
  "errors": [
    { "location": "voltage", "message": "'voltage' is a required property" }
  ]
}
```

---

### generate

Generates a contract-valid instance and sends it to the configured destination.

```
POST /{name}        # method: configurable via 'method' field
```

**Success**
```json
HTTP 200
{ "sent": true, "destination_status": 200 }
```

**Destination error**
```
HTTP 502
```

---

### respond

Receives a request and responds with a generated contract-valid payload. Useful for standing in for a service your code is calling.

```
GET /{name}         # method: configurable via 'method' field
```

If `request_contract` is set, the incoming body is validated first. Invalid body returns 400 before any generation.

**Success**
```json
HTTP <status_code>
{ ...generated payload... }
```

**Invalid request body**
```json
HTTP 400
{
  "valid": false,
  "errors": [{ "location": "...", "message": "..." }]
}
```

If no `contract` is set, the response body is empty. Useful for mocking 204-style endpoints.

---

### Sessions

Sessions run a generate endpoint on a repeating interval in the background.

#### Start a session

```
POST /sessions
Content-Type: application/json
```

```json
{
  "endpoint": "emit_event",
  "interval_ms": 5000,
  "period": "PT10M",
  "jitter_ms": 200
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `endpoint` | string | yes | Name of a `generate` endpoint |
| `interval_ms` | integer | yes | Milliseconds between emissions (minimum: 1) |
| `period` | string | no | Optional label (e.g. `hourly`) |
| `jitter_ms` | integer | no | Random ±jitter per interval in ms (default: 0) |

**Success**
```json
HTTP 201
{ "session_id": "550e8400-e29b-41d4-a716-446655440000" }
```

#### List sessions

```
GET /sessions
```

#### Stop a session

```
DELETE /sessions/{session_id}
```

```
HTTP 204   — stopped
HTTP 404   — not found
```

---

## Browser UI

The UI is served at `/ui/` and requires no separate setup.

| Page | Path |
|---|---|
| Overview + live feed | `/ui/` |
| Endpoint detail | `/ui/endpoints/{name}` |
| Sessions | `/ui/sessions` |
| Contract schema + paths | `/ui/contracts/{name}` |

The live feed uses SSE. The overview shows a merged stream of all endpoints; each endpoint detail page shows its own filtered stream. History is kept in memory (last 100 events per server instance, lost on restart).

Actions available in the UI: **Send now** (generate endpoints), **Start session**, **Stop session**.

---

## Contracts

Contracts are standard [JSON Schema Draft 7](https://json-schema.org/specification-links#draft-7) files.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "sensor_id": { "type": "string" },
    "voltage":   { "type": "number", "minimum": 0 },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["sensor_id", "voltage", "timestamp"],
  "additionalProperties": false
}
```

Use `$ref` freely — the engine resolves references relative to the contract file's location.

---

## Development

```bash
uv sync --group dev   # install dev dependencies

pytest                # run tests
pytest -x             # stop on first failure

ruff check src/       # lint
mypy src/             # type check
```

---

## Architecture

Hexagonal layout: `domain` → `application` → `infrastructure` / `adapters`. The config file and contracts are the only runtime inputs. Sessions and event history live in memory and are lost on restart.

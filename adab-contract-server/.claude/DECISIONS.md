# Contract Server — Decisions

## 2026-06-02: Separate package, not part of contract_engine

`contract_engine` is a pure library with no HTTP/server dependencies. Adding a server there would couple it to FastAPI/uvicorn/httpx and break its identity as a standalone tool. `contract_server` depends on `contract_engine`; not the other way around.

## 2026-06-02: Hexagonal / DDD mirroring contract_engine

Same rationale: infrastructure is replaceable (swap httpx for aiohttp, swap in-memory sessions for Redis) without touching domain or application logic. Also makes unit testing services trivial — inject test doubles for ports.

## 2026-06-02: Dynamic route mounting from YAML config

FastAPI routes are added at app construction time from the loaded `ServerConfig`. Alternative was a single catch-all dispatcher, but named routes give better OpenAPI docs and clearer error messages (404 vs bad dispatch). Downside: no hot-reload of config without restart — acceptable for demo scope.

## 2026-06-02: No send_type in YAML; sessions are the interval mechanism

Any `generate` endpoint is callable directly (single) or periodically (via sessions API). This avoids duplicating interval config in the YAML and makes the sessions concept explicit and orthogonal. The YAML defines *what* to generate; sessions define *when*.

## 2026-06-02: Control API is itself contract-validated (dogfooding)

`POST /sessions` body is validated against `start_session.json` using the same `contract_engine` pipeline. Two reasons: it demonstrates the tool's own value, and it gives structured validation errors for free instead of writing manual Pydantic error handlers.

## 2026-06-02: In-memory session repository

Persistence across restarts is out of scope for the demo. The interface is defined so a persistent backend can be swapped in later.

## 2026-06-02: asyncio scheduler (not APScheduler or Celery)

FastAPI runs on asyncio. Using asyncio tasks directly avoids a scheduler dependency and keeps the session tick in the same event loop as outbound HTTP. Jitter is applied per-tick as a random sleep offset within `[-jitter_ms, +jitter_ms]` clamped to > 0.

## 2026-06-04: Service virtualization direction — effects model

### Context

The current type system (validate / generate / respond) treats each endpoint as having exactly one behaviour. Real services do more: validate the request, respond conditionally, forward to a message bus, emit downstream over HTTP. Modelling this requires composing behaviours, not picking one.

### Decision

Move toward a **service virtualization** framing. An endpoint declares a list of **effects** — ordered side-effects that execute when the endpoint is called. Effects replace the top-level `type` field. The endpoint-level `request_contract` handles request validation before any effects run (fail-fast, returns 400).

### Effect types

| Type | Behaviour |
|---|---|
| `respond` | Generate a response body from `contract` and return it to the caller |
| `http` | Generate a payload from `contract` and POST it to `destination` |
| `messagebus` | Publish a payload to a message bus topic (`bus_type: kafka\|nats\|mqtt`) |

Payload source is either generated fresh from `contract` (default) or forwarded from the request body (`forward: true`, uses the endpoint's `request_contract` schema).

### Conditional execution

Effects support an optional `when:` clause. Two forms:

**On request data** — one field, one operator, one value:
```yaml
when:
  path: $request.body.owner_id
  equals: 1234
```

**On a named effect's result** — referencing another effect by name:
```yaml
when:
  some_effect_name:
    path: $response.status_code
    not_equals: 200
```

Operators: `equals`, `not_equals`. No boolean combinators (`and`/`or`), no lists, no nesting. If a use case requires more complex conditions, the tool is the wrong abstraction.

### Branching

A block of effects can be guarded by a `when:` condition. A `default:` block runs when no `when:` block matched. `when:` and `default:` blocks are items in the `effects` list alongside direct effects:

```yaml
effects:
  - when:
      path: $request.body.owner_id
      equals: 1234
    effects:
      - name: error_response
        type: respond
        contract: fleet_lookup_error_response.json
      - name: error_bus
        type: messagebus
        bus_type: nats
        topic: lookup_errors
        contract: fleet_lookup_request_emit.json
  - default:
    effects:
      - name: happy_response
        type: respond
        contract: fleet_lookup_response.json
      - name: happy_bus
        type: messagebus
        bus_type: nats
        topic: lookup_success
        forward: true
```

### Effect names

Optional. Only needed when another effect references the result via `when:`. Unnamed effects cannot be referenced.

### Disambiguation rule

In a `when:` clause, a `$`-prefixed key (`$request`, `$response`) is a data path. A bare key is an effect name.

### Execution order

Fixed, regardless of YAML order: validate request → run effects top-to-bottom → return response to caller. The first `respond` effect that executes wins; subsequent respond effects in the same branch are ignored.

### Dynamic overrides and refinements

Effect payloads support `overrides` and `refinements` with dynamic values sourced from the request or a prior effect's response, using the same `$`-prefixed path syntax as `when:`:

```yaml
- name: post_bus
  type: messagebus
  bus_type: kafka
  topic: charging_sessions_emit_notice
  contract: charging_sessions_emit_notice.json
  overrides:
    id: $request.body.id
  refinements:
    some_field: $response.body.value
```

Both `overrides` and `refinements` are supported and behave as they do today — best-effort. If the referenced path doesn't exist at runtime (e.g. the field wasn't in the request), the engine proceeds with its normal generation for that field and will surface an error if the result is invalid. No silent swallowing — config errors and bugs should be visible.

**Scope boundary**: path references (`$request.*`, `$response.*`) are valid only in `overrides` and `refinements` values. All other config fields (`topic`, `bus_type`, `destination`, `contract` filename, etc.) are static and resolved at load time, not at request time.

### What this is not

Not a rules engine. Not a transformation pipeline. Not a DSL with loops or variables. The ceiling is: one service, a few branches, a handful of downstream targets. Complexity beyond that belongs in a real implementation.

## 2026-06-05: Roadmap to service virtualization

### Phases

**Phase 1 — Config model**
Replace `EndpointConfig` and its `type` field with the effects-based model. New Pydantic models, new YAML parsing. Migrate the 3 example configs. No behaviour changes — everything else stays as-is while this stabilises. Foundation for all subsequent phases.

**Phase 1.5 — Inbound auth**
Protect the server itself before it gets deployed against test/acc environments. Static API key check as FastAPI middleware, configured in YAML:
```yaml
auth:
  type: api_key
  header: X-Api-Key
  value: secret
```
No value in deferring this — once someone points this at a real environment, an open port is a real risk.

**Phase 2 — Universal effect executor**
Replace the three separate routers with a single router mounting one handler per endpoint. Build an `EffectExecutor` that runs an effects list in order. Map existing behaviour: `respond` effect = current respond type, `http` effect = current generate type. Sessions decouple from `generate` and attach to any endpoint with an `http` effect. UI updated to show effects instead of type badges.

**Phase 3 — Conditional execution and dynamic binding**
Add `when:` condition evaluator (request data path, `equals`/`not_equals`). Add `when:`/`default:` block branching in the executor. Add `$request.body.x` / `$response.x` path resolution in `overrides` and `refinements`. Purely additive — the executor already runs effects; now some effects are skipped or use runtime values.

**Phase 4 — Message bus transport**
Abstract `Transport` interface alongside the existing `HttpClient`. Concrete implementations for Kafka, NATS, MQTT. `messagebus` effect type wired into the executor. `forward: true` payload mode (emit request body as-is rather than generating). Largest new piece — connection management, auth, and serialization per bus type.

**Phase 4.5 — Outbound auth**
Auth for `http` and `messagebus` effects reaching real destinations. Static headers first (`headers: {Authorization: Bearer ...}` on `destination` or effect level). OAuth2/token refresh as follow-up: `TokenProvider` abstraction injected into the transport layer.

### Rationale for ordering

- Phase 1 before everything: config is the contract between user and tool; stabilise it first.
- Phase 1.5 early: inbound auth is a safety concern, not a feature — ship it before real deployments happen.
- Phase 2 before 3: get existing behaviour running under the new executor before adding conditional logic.
- Phase 3 before 4: conditional HTTP effects can ship and be useful before message bus exists.
- Phase 4.5 with/after 4: outbound auth grows with the transport layer naturally.

## 2026-06-02: Validate endpoints take raw body, no overrides

The design goal is zero changes to producer code — they just point at a different URL. Accepting overrides in the request body would complicate the contract (whose overrides win?) and break that goal.

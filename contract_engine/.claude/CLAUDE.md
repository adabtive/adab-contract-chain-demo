# Contract Engine

## Billing
eteck

Contract-driven test data generation and validation. Produces deterministic instances from JSON Schema using seeds, supports overrides for negative testing, publishes over MQTT or HTTP to Azure Event Grid.

## Stack
Python 3.13, Pydantic v2, jsonschema, exrex, paho-mqtt, aiohttp, pytest, hypothesis, ruff, mypy (strict)

## Commands
```bash
pip install -e ".[dev]"
pytest
ruff check src tests && ruff format src tests
mypy src
```

## Key files
- `src/contract_engine/__init__.py` — public API, `create_default_engine()`
- `src/contract_engine/application/contract_engine.py` — facade
- `src/contract_engine/application/contract_engine_factory.py` — wiring
- `src/contract_engine/domain/types.py` — FieldType hierarchy
- `src/contract_engine/domain/contract.py` — Contract domain object
- `src/contract_engine/application/override_applier.py` — dot-path override logic
- `src/contract_engine/application/contract_refinement_service.py` — constraint refinements
- `src/contract_engine/infrastructure/generators/` — REALISTIC/FUZZ strategies
- `src/contract_engine/infrastructure/transport/` — MQTT + HTTP-MQTT transports
- `src/contract_engine/robot_adapter/keywords.py` — Robot keyword adapter
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`

## Architecture layers
```
Domain        → Contract, FieldType hierarchy, GenerationResult, ValidationResult
Application   → ContractEngine facade, services, override applier
Infrastructure→ JSON Schema parser, generators, jsonschema validator, transports
Robot adapter → Robot Framework keyword wrapper
```

## Gotchas
- `FieldDefinition.model_rebuild()` at module level — recursive type ref; don't move or remove
- Array overrides fail on empty arrays; if `minItems=0`, set array with `:=` first then index
- `oneOf` selection is seed-deterministic but exclusivity is not verified — run `validate_instance` if needed
- Root-level properties alongside `oneOf` are ignored — only the selected option's schema is used
- Refinement paths must exist; raises `ValueError` for unknown paths — use overrides for new fields
- `additionalProperties` sub-schema: refinements promote a field on first access (deepcopy of schema type)
- `additionalProperties: true`: refinements require a `type` constraint (e.g. `{"type": "number", "minimum": 0}`); raises `ValueError` without it
- `additionalProperties: false` (default): refinements to unknown sub-paths raise `ValueError`
- `exrex` can be slow/fail on complex regex — keep patterns simple
- Transport is separate from ContractEngine — create via `load_transport_from_env()`, call independently
- Azure auth requires all three: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

## TODO

### Backlog

### In progress

### Blocked

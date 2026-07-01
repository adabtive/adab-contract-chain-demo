# Design

## Architecture

DDD, four layers. Dependency flows inward: Infrastructure → Application → Domain. Robot adapter is a thin wrapper over Application.

```
Domain        → Contract, FieldDefinition, FieldType hierarchy, GenerationResult, ValidationResult, Seed
Application   → ContractEngine facade, ContractLoaderService, GeneratorService, ValidationService,
                ContractIntrospectionService, ContractRefinementService, ContractValidationService, OverrideApplier
Infrastructure→ JSON Schema parser, generators (REALISTIC/FUZZ), jsonschema validator, transports
Robot adapter → keyword wrapper only, no logic
```

## Core invariant

```
generate(contract, seed) → instance   # same seed + contract = same instance always
validate(contract, instance) → valid
```

Seeds are human-readable strings (`"happyflow"`) hashed to int internally. Batch seeds: `{seed}_0`, `{seed}_1`, etc.

## Domain model

`FieldType` sealed hierarchy (Pydantic models):
- `PrimitiveType` — string/number/integer/boolean/null + constraints (min/max, enum, format, pattern)
- `ObjectType` — list of `FieldDefinition`, `additional_properties` flag
- `ArrayType` — items type + min/maxItems
- `OneOfType` — list of options, one selected deterministically per seed
- `AnyType` — unconstrained

`Contract` wraps a list of `FieldDefinition` at root. For schemas where the root itself is a `oneOf` (no wrapping object), `Contract.root_type` holds the `OneOfType` and `fields` is empty. The generator produces the selected option's fields as a flat dict in this case.

## Generation modes

- **REALISTIC** (default) — mid-range values, plausible formats
- **FUZZ** — extremes, empty arrays, edge-case strings; always contract-valid

Strategies per type live in `infrastructure/generators/strategies/`.

## Override system

`OverrideApplier` patches the generated dict post-generation via dot-path keys. Supports:
- `field.nested` — nested objects
- `arr[0].field` — indexed array element
- `arr[*].field` — wildcard (all elements)
- `:=` prefix — parse value as JSON

Overrides can create new fields (with a warning) — intentional for adversarial testing.

## Refinement system

`ContractRefinementService.refine()` deep-copies a Contract and applies constraint overrides (min, max, enum, const) before generation. Original schema is never touched.

Supported constraints: `const`, `enum`, `minimum`, `maximum`, `min_length`, `max_length`, `format`, `pattern`, `one_of_filter`.

Path traversal:
- `field.nested` — object fields
- `field[*].sub` — array items
- `field.sub` where `field` is `OneOfType` — applies to all options that have `sub`, raises if none match
- `""` (empty string) — targets `Contract.root_type` for root-level oneOf schemas

`one_of_filter` is a flat `{field: value}` dict applied to a `OneOfType` field. Prunes options where any condition doesn't match. Raises if no options survive. Options match if they are `ObjectType` and each named field's enum allows the value (or is unconstrained).

Refinements are applied in dict iteration order — caller controls sequence. Filter before path-constrain is the natural order.

## Transport layer

Two transports behind `ITransport`:
- `MqttTransport` — paho-mqtt, TLS, username/password, Azure AD
- `HttpMqttTransport` — HTTP POST to Azure Event Grid MQTT bridge, Entra ID auth

Auth resolved by `AuthHandlerFactory` from env vars (`TRANSPORT_TYPE`, `AZURE_*`, `MQTT_*`).

## Data flow

```
contract_source (str/dict/path/url)
  → ContractLoaderService (parse + resolve $ref)
  → ContractRefinementService (optional)
  → ContractValidationService
  → GeneratorService (generate per seed + mode)
  → OverrideApplier
  → GenerationResult
  → Transport.send(topic, result)
```

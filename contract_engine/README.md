
# Contract Engine

## Overview

The Contract Engine provides **contract-driven data generation and validation** based on JSON Schema.

It enables:

* Deterministic test data generation
* Validation against contracts
* Scenario creation via overrides (including negative tests)
* Contract introspection to discover available fields

Core invariant:

```
generate(contract, seed) → instance
validate(contract, instance) → valid
```

---

## Installation

```bash
pip install contract-engine
```

---

## Quick Start

```python
from contract_engine import create_default_engine

engine = create_default_engine()

schema = {
    "type": "object",
    "properties": {
        "temperature": {"type": "number", "minimum": 0, "maximum": 100}
    },
    "required": ["temperature"],
}

result = engine.generate_instance(schema, seed="happyflow")

print(result.data)
```

---

## Deterministic Seeds

You can use human-readable seeds:

```python
engine.generate_instance(schema, seed="happyflow")
```

Guarantee:

```
same seed → same data
```

Batch generation:

```python
results = engine.generate_instances(schema, count=3, seed="happyflow")
```

Produces:

```
happyflow_0
happyflow_1
happyflow_2
```

Each can be replayed individually.

---

## Modes: Realistic and Fuzz
The engine can create objects based on contracts in two different modes.
Realistic generates (semi) realistic data. It is biased towards averages of contraints for example
Fuzz mode will generate data looking for edgecases favouring extremes in contraints, empty-ish values etc.
Usage:

```python
results = engine.generate_instances(schema, count=3, seed="happyflow", mode=GenerationMode.FUZZ)
or:
results = engine.generate_instances(schema, count=3, seed="happyflow", mode=GenerationMode.REALISTIC)
```
The default is mode is `REALISTIC`

---

## Validation

```python
validation = engine.validate_instance(schema, result.data)

assert validation.valid
```

---

## Overrides (Scenario Control)

Overrides allow you to **modify generated data after generation**.

This is especially useful for:

* Edge cases
* Negative tests
* Specific scenarios

### Basic override

```python
result = engine.generate_instance(
    schema,
    overrides={
        "temperature": -999
    },
)
```

---

## Nested Overrides

```python
schema = {
    "type": "object",
    "properties": {
        "sensor": {
            "type": "object",
            "properties": {
                "value": {"type": "number"}
            },
        }
    },
}

result = engine.generate_instance(
    schema,
    overrides={
        "sensor.value": 0
    },
)
```

---

## Array Overrides

```python
result = engine.generate_instance(
    schema,
    overrides={
        "sensors[0].value": 0
    },
)
```

---

## Wildcard Overrides

Apply to all elements:

```python
result = engine.generate_instance(
    schema,
    overrides={
        "sensors[*].value": 0
    },
)
```
---

## JSON Overrides

Overrides support full JSON values using :=.

This allows replacing entire objects or arrays.
```python
result = engine.generate_instance(
    schema,
    overrides={
        "data": [{"id": "alert-1", "message": "test"}]
    },
)

```

When using string-based overrides:

```python
data:=[{"id":"alert-1","message":"test"}]
```

Use this for:

Replacing arrays completely
Injecting complex objects
Creating controlled payloads
Creating New Fields (Permissive Mode)

Overrides can create fields that do not exist in the schema.

```python
result = engine.generate_instance(
    schema,
    overrides={
        "unexpected.field": 123
    },
)

```
Result:
```python
{
  "unexpected": {
    "field": 123
  }
}
```

⚠️ A warning is logged when new fields are created.

This is intentional and useful for:

Testing additionalProperties: false
Simulating malformed input
Robustness testing
Array Behavior (Important)

Array overrides are strict:

```python
overrides = {
    "items[0]": 1
}
```

If the array is empty:
```python
{"items": []}
```

→ This will raise an error:

`OverridePathError: Index 0 out of range`
Recommended pattern

Explicitly replace the array first:

```python
overrides = {
    "items": [{}],
    "items[0].value": 1
}
```

---

## Refinements (Pre-Generation Contract Mutations)

Refinements narrow or filter a contract **before generation**. Unlike overrides, which patch the generated dict after the fact, refinements change the schema constraints the generator works from. The original contract is never modified.

Use refinements to:

* Pin a field to a specific value without breaking schema validity
* Narrow numeric or string constraints per test scenario
* Select which `oneOf` branches are eligible for generation

### String syntax

```python
# pin a value (const)
refinements = "payload.value = 42"

# full constraint dict via JSON
refinements = 'payload.value := {"minimum": 10, "maximum": 50}'

# filter oneOf branches
refinements = 'payload := {"one_of_filter": {"kind": "sensor"}}'
```

### Multiline (multiple refinements, applied in order)

```python
refinements = """
payload := {"one_of_filter": {"kind": "sensor"}}
payload.value := {"minimum": 0, "maximum": 100}
"""
```

### Dict syntax

```python
refinements = {
    "payload": {"one_of_filter": {"kind": "sensor"}},
    "payload.value": {"minimum": 0, "maximum": 100},
}
```

### Supported constraints

| Key | Applies to |
|---|---|
| `type` | primitive union (`OneOfType`) — filters to matching branch(es); single match also applies remaining constraints. Also required when `additionalProperties: true` to infer the field type |
| `const` | primitive — pins to exact value |
| `enum` | primitive — restricts to list of values |
| `minimum` / `maximum` | number / integer |
| `min_length` / `max_length` | string |
| `format` | string |
| `pattern` | string |
| `minimum_date_time` / `maximum_date_time` | `date-time` or `datetime_naive` string — constrains the generated timestamp to a range |
| `minimum_date` / `maximum_date` | `date` string — constrains the generated date to a range |
| `minimum_duration` / `maximum_duration` | `isoduration` string — constrains the generated duration to a range |
| `one_of_filter` | oneOf field — prunes non-matching branches |
| `required` | any field — `true` forces an optional field to always appear; `false` always excludes it |

### Forcing optional fields

Use `required` to guarantee an optional field is always present or always absent:

```python
# force an optional field to always be included
refinements = {"subject": {"required": True}}

# exclude an optional field entirely
refinements = {"subject": {"required": False}}
```

Can be combined with other constraints:

```python
refinements = {"subject": {"required": True, "const": "alarms"}}
```

---

### Constraining date-time fields

Use `minimum_date_time` and `maximum_date_time` to bound the generated value of a `date-time` string field. Values must be `datetime` objects (timezone-aware recommended):

```python
from datetime import UTC, datetime

result = engine.generate_instance(
    schema,
    refinements={
        "timestamp": {
            "minimum_date_time": datetime(2024, 1, 1, tzinfo=UTC),
            "maximum_date_time": datetime(2024, 12, 31, tzinfo=UTC),
        }
    },
    seed="test",
)
```

Pin to the current moment by passing the same value for both bounds:

```python
now = datetime.now(tz=UTC)
refinements = {"timestamp": {"minimum_date_time": now, "maximum_date_time": now}}
```

Raises if `maximum_date_time` is earlier than `minimum_date_time`.

---

### Constraining date fields

Use `minimum_date` and `maximum_date` to bound a `date` string field. Values must be `date` objects:

```python
from datetime import date

result = engine.generate_instance(
    schema,
    refinements={
        "day": {
            "minimum_date": date(2024, 1, 1),
            "maximum_date": date(2024, 12, 31),
        }
    },
    seed="test",
)
```

Raises if `maximum_date` is earlier than `minimum_date`.

---

### Constraining datetime_naive fields

`datetime_naive` reuses `minimum_date_time` and `maximum_date_time`. The output has no timezone suffix:

```python
from datetime import UTC, datetime

result = engine.generate_instance(
    schema,
    refinements={
        "ts": {
            "minimum_date_time": datetime(2024, 1, 1, tzinfo=UTC),
            "maximum_date_time": datetime(2024, 12, 31, tzinfo=UTC),
        }
    },
    seed="test",
)
# result.data["ts"] → "2024-06-15T10:23:00" (no +00:00)
```

---

### Constraining isoduration fields

Use `minimum_duration` and `maximum_duration` to bound an `isoduration` field. Values must be `timedelta` objects:

```python
from datetime import timedelta

result = engine.generate_instance(
    schema,
    refinements={
        "window": {
            "minimum_duration": timedelta(hours=1),
            "maximum_duration": timedelta(days=7),
        }
    },
    seed="test",
)
```

Raises if `maximum_duration` is less than `minimum_duration`.

---

### Refining additionalProperties fields

When a schema uses `additionalProperties` with a sub-schema, target a specific key by name via a dot-path refinement. The field is promoted on first access; the original contract is unchanged.

```python
schema = {
    "type": "object",
    "properties": {
        "props": {
            "type": "object",
            "additionalProperties": {"type": "number", "minimum": 0},
        }
    },
}

result = engine.generate_instance(
    schema,
    refinements={"props.Value": {"minimum": 15.0, "maximum": 35.0}},
    seed="test",
)
# result.data["props"]["Value"] is a number between 15.0 and 35.0
```

When `additionalProperties` is `true` (no sub-schema), a `type` constraint is required so the engine knows what to generate:

```python
schema = {
    "type": "object",
    "properties": {
        "props": {"type": "object", "additionalProperties": True}
    },
}

result = engine.generate_instance(
    schema,
    refinements={"props.Score": {"type": "number", "minimum": 0, "maximum": 100}},
    seed="test",
)
```

Omitting `type` when `additionalProperties` is `true` raises a `ValueError`.

---

### oneOf branch selection

When a field is a `oneOf` type, use `one_of_filter` to keep only branches where all given field/value conditions match:

```python
result = engine.generate_instance(
    schema,
    refinements={
        "event": {"one_of_filter": {"kind": "sensor"}},
    },
)
```

Branches are matched at schema level: a branch matches if it is an object type containing the named field with an enum that includes the value (or no enum constraint at all). Raises if no branches survive.

### Path refinement through oneOf

A dot-path that traverses a `oneOf` field applies the constraint to all branches that contain the field:

```python
refinements = {"event.value": {"minimum": 0}}
# → applied to every oneOf branch that has a "value" field
```

### Ordering

Refinements are applied in the order they appear. Filtering before narrowing is the natural order:

```python
refinements = {
    "event": {"one_of_filter": {"kind": "sensor"}},  # prune first
    "event.value": {"minimum": 0},                    # then constrain surviving branch
}
```

### Narrowing primitive unions by type

When a field has a JSON Schema type array (e.g. `["boolean", "string", "integer", "number"]`), it is parsed as a `OneOfType`. Use `type` to filter it down to the branch(es) you want:

```python
# narrow to number, then apply constraints
refinements = {"value": {"type": "number", "minimum": 10.0, "maximum": 20.0}}
```

When the filter leaves exactly one branch, remaining constraints (`minimum`, `maximum`, `const`, etc.) are applied to that branch directly. When multiple branches survive, the generator picks from them — combining with further primitive constraints will raise.

```python
# keep string and number branches — cannot chain minimum here
refinements = {"value": {"type": ["string", "number"]}}
```

Raises if the type string is unknown or no branches match.

---

## Negative Testing (Very Important)

Overrides allow you to intentionally break contracts.

Example:

```python
schema = {
    "type": "object",
    "properties": {
        "temperature": {"type": "number", "minimum": 0}
    },
    "required": ["temperature"],
}

result = engine.generate_instance(
    schema,
    overrides={
        "temperature": -100  # invalid
    },
)

validation = engine.validate_instance(schema, result.data)

assert not validation.valid
```

This allows you to:

* Test validation logic
* Simulate bad upstream data
* Verify system robustness

---

## Inspect Contract (Discover Paths)

You can inspect a contract to see available override paths:

```python
fields = engine.inspect_contract(schema)

for f in fields:
    print(f.path)
```

Example output:

```
temperature
sensor.value
sensors[*].value
```

---

## Contract Sources

Contracts can be provided as:

```python
# File path
engine.generate_instance("contracts/event.json")

# URL
engine.generate_instance("https://example.com/schema.json")

# Python dict
engine.generate_instance(schema_dict)

# JSON string
engine.generate_instance(json_string)
```

---

## Architecture (Short)

```
Domain        → Contract model
Application   → Services (generator, validator, loader)
Infrastructure→ JSON Schema + generation
Adapter       → Robot Framework
```

---
## MQTT Transport (Sending Generated Data)

The Contract Engine can send generated data to external systems using MQTT.

This is useful for:

* Integration testing
* Event-driven systems
* Sending test data to message brokers (e.g. Azure Event Grid)

---

### Basic Usage (Python)
```bash
from contract_engine import create_default_engine
from contract_engine.infrastructure.transport.config.transport_config_loader import load_transport_from_env

engine = create_default_engine()
transport = load_transport_from_env()

result = engine.generate_instance(schema, seed="happyflow")

transport.send(
    topic="test/topic",
    message=result,

```
)
#### Include Seed Metadata

You can optionally include the seed in the outgoing payload for traceability:

```bash
transport.send(
    destination="test/topic",
    message=result,
    include_seed=True,
)

```

This produces:
```bash
{
  "temperature": 42,
  "_meta": {
    "seed": {
      "label": "happyflow",
      "value": 123456
    }
  }
}
```

#### Transport Configuration

The Contract Engine supports multiple transport mechanisms.

The active transport is selected via:
i
```bash
TRANSPORT_TYPE=mqtt        # default
# or
TRANSPORT_TYPE=http_mqtt
```

#### MQTT Transport
Required
```bash
MQTT_HOST=localhost
```
Optional
```bash
MQTT_PORT=8883
MQTT_TLS=true
MQTT_CLIENT_ID=
```
Transport Options
```bash
MQTT_TRANSPORT=tcp        # or "websockets"
MQTT_WS_PATH=/mqtt
```

Authentication Modes
1. No Authentication (default)

No variables required.

2. Username / Password
```bash
MQTT_USERNAME=
MQTT_PASSWORD=
```
3. Azure (Microsoft Entra ID / Service Principal)
```bash
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=

```
Used for:

Azure Event Grid (MQTT via Event Grid Namespace)
#### TLS Configuration
```bash
MQTT_CA_CERT=
MQTT_CLIENT_CERT=
MQTT_CLIENT_KEY=
```

If MQTT_TLS=true, TLS is enabled automatically.

🌐 HTTP MQTT Transport (Azure Event Grid)

This transport sends messages via HTTP to an MQTT topic using Azure Event Grid.

 Recommended for Azure Event Grid integrations.

Required
```bash
TRANSPORT_TYPE=http_mqtt
MQTT_HOST=<namespace>.westeurope-1.ts.eventgrid.azure.net

AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
```

Behavior
Uses Azure AD (Entra ID) for authentication
Sends messages via:
POST /mqtt/messages?topic=<topic>
Internally publishes to MQTT topic spaces

#### Configuration Behavior

Configuration is loaded automatically from environment variables
Transport type determines which configuration is used
Authentication mode is inferred from available variables
Invalid or incomplete configurations will fail at startup


#### Supported Setups
MQTT Transport
Azure Event Grid (MQTT via Event Grid Namespace)
Secure MQTT brokers (TLS, username/password, certificates)
Local/test MQTT brokers
HTTP MQTT Transport
Azure Event Grid (Topic Spaces via HTTP bridge)


## Design Principles

* Deterministic generation
* Contract-first testing
* Clear separation of concerns
* Extensible architecture

---

## JSON Schema Support

The Contract Engine supports a **practical subset of JSON Schema**, focused on enabling reliable data generation and validation.

---

### ✅ Supported Features

#### Types

* `object`
* `array`
* `string`
* `number`
* `integer`
* `boolean`
* `null`
* type arrays like `["boolean","null"]`

---

#### Object Features

* `properties`
* `required`
* nested objects
* `additionalProperties` (schema form — target specific keys via refinements)

---

#### Array Features

* `items`
* `minItems`
* `maxItems`

---

#### Numeric Constraints

* `minimum`
* `maximum`

---

#### String Constraints

* `minLength`
* `maxLength`
* `pattern` (regex-based generation)
* `format`

---

#### Enumerations

* `enum`
* `const`

---

#### Format Support

The following formats are supported via built-in generators:

* `date-time` (RFC3339)
* `date` (ISO 8601 calendar date)
* `datetime_naive` (ISO 8601 local datetime, no timezone)
* `isoduration` (ISO 8601 duration)
* `uuid`
* `uri`
* `email`

---

#### Composition

* `$ref` (local and external)
* `allOf` (merged into a single schema)
* `oneOf` (deterministic selection during generation)

---

### ⚠️ Partially Supported

These features are supported with limitations:

#### `pattern`

* Generated using regex expansion
* May fail for complex or ambiguous regex patterns
* Generation is limited to avoid excessive computation

---

#### `allOf`

* Merged into a single schema
* Conflicts are detected (e.g. incompatible constraints)
* Complex interactions may not be fully supported

---

#### `oneOf`
* Exactly one schema is selected during generation
* Selection is deterministic based on the seed
* Does not validate exclusivity semantics (i.e. “exactly one must match” is not enforced)
* Base schema properties outside oneOf are currently not merged with selected options

---

### ❌ Not Supported (Yet)

The following JSON Schema features are currently **not implemented**:

* `anyOf`
* `not`
* `if / then / else`
* `dependentSchemas` / `dependencies`
* `patternProperties`
* `unevaluatedProperties`

---

### ⚠️ Design Philosophy

The engine intentionally supports a **focused subset** of JSON Schema:

* Prioritizes **deterministic data generation**
* Avoids ambiguous or non-deterministic constructs
* Ensures generated data is **always valid**

---

### 💡 Recommendation

For best results:

* Use **explicit constraints**
* Avoid ambiguous schema constructs
* Prefer `allOf` over complex conditional logic

---

### 🔮 Future Extensions

Planned or possible future support:

* `anyOf`
* richer format support (e.g. `ipv4`, `hostname`)
* improved regex handling
* conditional schemas

---

---
## Next Steps

* See `ROBOT_USAGE.md` for Robot Framework usage
* Use overrides to build meaningful test scenarios
* Use seeds to reproduce failures exactly

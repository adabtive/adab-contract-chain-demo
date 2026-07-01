
# Contract Engine — Robot Framework Usage

This guide explains how to use the Contract Engine in Robot Framework tests.

---

## Installation

```robot
Library    contract_engine.robot_adapter.keywords.ContractEngineKeywords
```

---
## Robot Framework Keyword Documentation

For Robot Framework users, keyword documentation is available as a resource file.

Generate HTML documentation:

libdoc robot/contract_engine_keywords.resource robot/contract_engine_keywords.html

This documentation describes:

- Available keywords
- Arguments
- Usage examples

---

## Generate Data

```robot
${result}=    Generate Contract Instance
...           contracts/device_event.json
...           seed=happyflow

Log    ${result.data}
```

---

## Access Generated Data

```robot
Log    ${result.data.temperature}
Log    ${result.seed.label}
```

---

## Generate Multiple Instances

```robot
@{results}=    Generate Contract Instances
...            contracts/device_event.json
...            count=3
...            seed=batch

FOR    ${r}    IN    @{results}
    Log    ${r.seed.label}
END
```

Output:

```
batch_0
batch_1
batch_2
```

---

## Modes: Realistic and Fuzz
The engine can create objects based on contracts in two different modes.
Realistic generates (semi) realistic data. It is biased towards averages of contraints for example
Fuzz mode will generate data looking for edgecases favouring extremes in contraints, empty-ish values etc.
Usage:

```robot
@{results}=    Generate Contract Instances
...            contracts/device_event.json
...            count=3
...            seed=batch
...            mode=fuzz


FOR    ${r}    IN    @{results}
    Log    ${r.seed.label}
END
```

The default is mode is `REALISTIC`

---

## Validate Data

```robot
${validation}=    Validate Contract Instance
...               contracts/device_event.json
...               ${result.data}

Should Be True    ${validation.valid}
```

---

## Overrides (Scenario Control)

Overrides allow you to modify generated data to create specific scenarios.

They are especially useful for:

* Edge cases
* Negative tests
* Forcing deterministic values
* Injecting custom payloads

You can provide overrides as either:

* a **dictionary** (most robust)
* a **string** (recommended for readability in Robot)

---

## String Overrides (Recommended)

### Inline format

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=temperature=-999
```

---

### Multiline format (best for multiple overrides)

⚠️ Robot does **not automatically concatenate multiline arguments**. Use this format:

```robot
${overrides}=    Catenate    SEPARATOR=\n
...    temperature=-999
...    sensors[*].value=0
...    flag=true

${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=${overrides}
```

---

## Dictionary Overrides (Fully Supported)

Recommended when:

* Using complex values (lists / dicts)
* Avoiding parsing issues

```robot
${overrides}=    Create Dictionary
...    temperature=-999
...    sensor.value=0

${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=${overrides}
```

---

## Nested Overrides

### String

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=sensor.value=0
```

### Dictionary

```robot
${overrides}=    Create Dictionary
...    sensor.value=0
```

---

## Array Overrides

### String

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=sensors[0].value=0
```

### Dictionary

```robot
${overrides}=    Create Dictionary
...    sensors[0].value=0
```

---

## Wildcard Overrides

Apply to all elements:

```robot
${overrides}=    Catenate    SEPARATOR=\n
...    sensors[*].value=0
```

---

## JSON Overrides (Advanced)

You can replace entire objects or arrays using JSON with `:=`.

### String

```robot
${overrides}=    Catenate    SEPARATOR=\n
...    data:=[{"id":"alert-1","message":"test"}]
```

### Dictionary (recommended for complex structures)

```robot
${data}=    Create Dictionary    id=alert-1    message=test
@{list}=    Create List    ${data}

${overrides}=    Create Dictionary
...    data=${list}
```

Use JSON overrides for:

* Replacing arrays completely
* Injecting structured payloads
* Creating controlled test data

---

## Refinements (Pre-Generation Contract Mutations)

Refinements narrow or filter the contract **before generation**. Unlike overrides (which patch the generated dict), refinements change what the generator is allowed to produce. The original contract is never modified.

Use refinements to:

* Pin or narrow a field's value range per test scenario
* Select which `oneOf` branch is eligible for generation

---

### String refinements (recommended for readability)

#### Inline — pin a value

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=payload.value=42
```

#### Multiline — multiple refinements applied in order

```robot
${refinements}=    Catenate    SEPARATOR=\n
...    payload := {"one_of_filter": {"kind": "sensor"}}
...    payload.value := {"minimum": 0, "maximum": 100}

${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=${refinements}
```

---

### Dictionary refinements

```robot
${filter}=      Create Dictionary    one_of_filter=&{kind_filter}
&{kind_filter}=    Create Dictionary    kind=sensor
${constraint}=  Create Dictionary    minimum=${0}    maximum=${100}

${refinements}=    Create Dictionary
...    payload=${filter}
...    payload.value=${constraint}

${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=${refinements}
```

For complex refinements, the JSON string form is usually more readable than Robot dictionaries.

---

### Forcing optional fields

Use `required` to guarantee an optional field is always present or always absent:

```robot
# Always include
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=subject := {"required": true}

# Always exclude
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=subject := {"required": false}
```

Can be combined with other constraints:

```robot
refinements=subject := {"required": true, "const": "alarms"}
```

---

### Constraining date-time fields

Use `minimum_date_time` and `maximum_date_time` to bound a `date-time` string field. In Robot, pass ISO 8601 strings — the engine parses them at the boundary:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=timestamp := {"minimum_date_time": "2024-01-01T00:00:00+00:00", "maximum_date_time": "2024-12-31T23:59:59+00:00"}
```

Raises if `maximum_date_time` is earlier than `minimum_date_time`.

---

### Constraining datetime_naive fields

`datetime_naive` reuses `minimum_date_time` and `maximum_date_time`. The output has no timezone suffix:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=ts := {"minimum_date_time": "2024-01-01T00:00:00+00:00", "maximum_date_time": "2024-12-31T23:59:59+00:00"}
```

---

### Constraining date fields

Use `minimum_date` and `maximum_date` to bound a `date` string field. Pass ISO 8601 date strings:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=day := {"minimum_date": "2024-01-01", "maximum_date": "2024-12-31"}
```

Raises if `maximum_date` is earlier than `minimum_date`.

---

### Constraining isoduration fields

Use `minimum_duration` and `maximum_duration` to bound an `isoduration` field. Pass ISO 8601 duration strings:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=window := {"minimum_duration": "PT3600S", "maximum_duration": "P7D"}
```

Raises if `maximum_duration` is less than `minimum_duration`.

---

### Refining additionalProperties fields

When a schema uses `additionalProperties` with a sub-schema, target a specific key via a dot-path refinement. The field is promoted on first access; the original contract is unchanged.

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=props.Value := {"minimum": 15.0, "maximum": 35.0}
```

When `additionalProperties` is `true` (no sub-schema), include a `type` constraint so the engine knows what to generate:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=props.Score := {"type": "number", "minimum": 0, "maximum": 100}
```

Omitting `type` when `additionalProperties` is `true` raises an error.

---

### oneOf branch selection

Select which `oneOf` branch the generator uses:

```robot
${refinements}=    Catenate    SEPARATOR=\n
...    payload := {"one_of_filter": {"kind": "sensor"}}

${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=${refinements}
```

Only branches where `kind` is `"sensor"` survive. The generator then picks from those. Raises if no branches match.

---

### Narrowing primitive unions by type

When a field has a JSON Schema type array (e.g. `["boolean", "string", "integer", "number"]`), use `type` to filter it to one or more branches:

```robot
# narrow to number and apply constraints
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=value := {"type": "number", "minimum": 10.0, "maximum": 20.0}
```

When exactly one branch survives, remaining constraints apply to it. When multiple survive, the generator picks from them — adding primitive constraints like `minimum` at that point will raise.

```robot
# keep two branches, no further constraints
refinements=value := {"type": ["string", "number"]}
```

---

### Combining refinements and overrides

Refinements run before generation; overrides run after. Both can be used together:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           refinements=payload := {"one_of_filter": {"kind": "sensor"}}
...           overrides=payload.value=999
```

---

## Creating New Fields (Permissive Behavior)

Overrides can create fields that do not exist in the schema.

```robot
${overrides}=    Create Dictionary
...    unexpected.field=123
```

Result:

```json
{
  "unexpected": {
    "field": 123
  }
}
```

⚠️ A warning is logged when new fields are created.

This is useful for:

* Testing `additionalProperties: false`
* Simulating malformed input
* Negative testing

---

## Array Behavior (Important)

Array overrides are **strict**:

```robot
${overrides}=    Create Dictionary
...    items[0]=1
```

If the array is empty:

```json
{"items": []}
```

→ This will fail:

```
OverridePathError: Index 0 out of range
```

### Recommended pattern

Explicitly initialize the array:

```robot
${overrides}=    Create Dictionary
...    items=${EMPTY}
...    items[0].value=1
```

Or use JSON:

```robot
${overrides}=    Catenate    SEPARATOR=\n
...    items:=[{"value":1}]
```

---

## Supported Value Types (String Overrides)

Values are automatically parsed:

```
true / false  → boolean
null          → None
123           → int
3.14          → float
text          → string
```

---

## Override Rules

* Format must be:

  ```
  key=value
  key:=json
  ```

* Paths support:

  ```
  a.b.c
  a[0]
  a[*]
  ```

* More specific overrides take precedence:

  ```
  sensors[*].value=0
  sensors[0].value=5
  ```

* Invalid paths or indices raise errors

---

## Limitations

### String overrides

Not supported:

```
name=hello,world   ❌ commas inside values
```

Use dictionary overrides instead.

---

## Negative Testing (Very Important)

Overrides allow you to intentionally break contracts.

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           overrides=temperature=-100

${validation}=    Validate Contract Instance
...               ${SCHEMA}
...               ${result.data}

Should Be False    ${validation.valid}
```

---

Use this to:

* Test validation logic
* Simulate invalid upstream data
* Verify system robustness

---

## Recommendation

| Use case             | Recommended approach |
| -------------------- | -------------------- |
| Simple tweaks        | String overrides     |
| Multiple overrides   | Multiline + Catenate |
| Complex structures   | Dictionary overrides |
| Full payload control | JSON (`:=`)          |

---

## Tip

Use `Inspect Contract` to discover valid override paths:

```robot
${fields}=    Inspect Contract    ${SCHEMA}
```

## Inspect Contract (Discover Paths)

If you're unsure what paths exist:

```robot
@{fields}=    Inspect Contract
...           ${SCHEMA}

FOR    ${f}    IN    @{fields}
    Log    ${f.path}
END
```

Example output:

```
temperature
sensor.value
sensors[*].value
```

---
## Transport

```robot
Send Message
...    ${result}
...    destination=test/topic
...    include_seed=${TRUE}
```

### Configuration (Environment Variables)
MQTT transport is configured via environment variables.

Required
```
MQTT_HOST=localhost
TRANSPORT_TYPE=mqtt #or http_mqtt
```
Optional
```
MQTT_PORT=1883
MQTT_TLS=false

MQTT_USERNAME=
MQTT_PASSWORD=

MQTT_CA_CERT=
MQTT_CLIENT_CERT=
MQTT_CLIENT_KEY=

MQTT_CLIENT_ID=
```
TLS / Azure Compatibility

The transport supports secure MQTT connections:

TLS (MQTT_TLS=true)
Client certificates
Username/password authentication

This makes it compatible with:

Azure Event Grid (MQTT)
Secure MQTT brokers

## Deterministic Seeds

```robot
seed=happyflow
```

Guarantees:

```
same seed → same data
```

Batch:

```
happyflow_0
happyflow_1
happyflow_2
```

---

## Replay Failed Tests

If a test fails with:

```
seed=happyflow_2
```

Replay it:

```robot
${result}=    Generate Contract Instance
...           ${SCHEMA}
...           seed=happyflow_2
```

---

## When to Use What

| Use case         | Keyword                                 |
| ---------------- | --------------------------------------- |
| Generate one     | Generate Contract Instance              |
| Generate many    | Generate Contract Instances             |
| Validate only    | Validate Contract Instance              |
| Explore contract | Inspect Contract                        |

---

## Notes

* Contracts can be:

  * File paths
  * URLs
  * JSON strings
  * Dictionaries

* Overrides currently use dictionary syntax

---

## Tips

* Use readable seeds (`happyflow`, `edgecase`, `invalid_input`)
* Use `Inspect Contract` to discover override paths
* Use overrides to create meaningful test scenarios

---

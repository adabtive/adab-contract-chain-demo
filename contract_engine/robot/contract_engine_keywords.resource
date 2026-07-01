*** Settings ***
Documentation    Contract Engine keyword reference for Robot Framework.
...              This resource documents how QA engineers can use the Contract Engine in tests.
Library          BuiltIn


*** Keywords ***
Generate Contract Instance
    [Documentation]    Generates one data instance based on a contract.
    ...
    ...    Arguments:
    ...    - ``schema``: Contract source. Can be a file path, URL, JSON string, or dictionary.
    ...    - ``seed``: Optional deterministic seed used to reproduce the same data.
    ...    - ``mode``: Optional generation mode: ``realistic`` (default) or ``fuzz``.
    ...    - ``overrides``: Optional post-generation patches as string or dictionary.
    ...    - ``refinements``: Optional pre-generation contract mutations as string or dictionary.
    ...
    ...    Refinements narrow the contract before generation. Use ``key=value`` to pin a field,
    ...    or ``key:={"constraint": ...}`` for full constraint dicts.
    ...    Use ``one_of_filter`` to select which oneOf branches are eligible.
    ...    Use ``type`` to filter a primitive union (type array) to matching branch(es):
    ...    ``value := {"type": "number", "minimum": 10}`` — filters to number branch and applies constraints.
    ...    ``value := {"type": ["string", "number"]}`` — keeps both branches; cannot chain primitive constraints.
    ...    Use ``required`` to force an optional field to always appear (``true``) or always be excluded (``false``).
    ...    Use ``minimum_date_time`` / ``maximum_date_time`` to bound a ``date-time`` or ``datetime_naive`` field (ISO 8601 strings):
    ...    ``ts := {"minimum_date_time": "2024-01-01T00:00:00+00:00", "maximum_date_time": "2024-12-31T23:59:59+00:00"}``
    ...    Use ``minimum_date`` / ``maximum_date`` to bound a ``date`` field (ISO 8601 date strings):
    ...    ``day := {"minimum_date": "2024-01-01", "maximum_date": "2024-12-31"}``
    ...    Use ``minimum_duration`` / ``maximum_duration`` to bound an ``isoduration`` field (ISO 8601 duration strings):
    ...    ``window := {"minimum_duration": "PT3600S", "maximum_duration": "P7D"}``
    ...    Use a dot-path to target a specific key in an ``additionalProperties`` sub-schema:
    ...    ``props.Value := {"minimum": 15.0}`` — promotes the field on first access; original contract unchanged.
    ...    When ``additionalProperties`` is ``true`` (no sub-schema), include a ``type`` constraint:
    ...    ``props.Score := {"type": "number", "minimum": 0}`` — required so the engine knows what to generate.
    ...
    ...    Refinements are applied in order. Filter before constraining:
    ...    | payload := {"one_of_filter": {"kind": "sensor"}} |
    ...    | payload.value := {"minimum": 0, "maximum": 100} |
    ...
    ...    Example:
    ...    | ${result}= | Generate Contract Instance | contracts/device_event.json | seed=happyflow |
    ...    | Log | ${result.data} |
    ...
    ...    With refinements:
    ...    | ${result}= | Generate Contract Instance | ${SCHEMA} | refinements=payload.value=42 |
    [Arguments]    ${schema}    ${seed}=${None}    ${mode}=realistic    ${overrides}=${None}    ${refinements}=${None}
    No Operation


Generate Contract Instances
    [Documentation]    Generates multiple data instances based on a contract.
    ...
    ...    Arguments:
    ...    - ``schema``: Contract source. Can be a file path, URL, JSON string, or dictionary.
    ...    - ``count``: Number of instances to generate.
    ...    - ``seed``: Optional deterministic seed prefix.
    ...    - ``mode``: Optional generation mode: ``realistic`` (default) or ``fuzz``.
    ...    - ``overrides``: Optional post-generation patches as string or dictionary.
    ...    - ``refinements``: Optional pre-generation contract mutations as string or dictionary.
    ...
    ...    Example:
    ...    | @{results}= | Generate Contract Instances | contracts/device_event.json | count=3 | seed=batch |
    ...    | FOR | ${r} | IN | @{results} |
    ...    | | Log | ${r.seed.label} |
    ...    | END |
    [Arguments]    ${schema}    ${count}=1    ${seed}=${None}    ${mode}=realistic    ${overrides}=${None}    ${refinements}=${None}
    No Operation


Validate Contract Instance
    [Documentation]    Validates data against a contract.
    ...
    ...    Arguments:
    ...    - ``schema``: Contract source. Can be a file path, URL, JSON string, or dictionary.
    ...    - ``data``: Data object to validate.
    ...
    ...    Example:
    ...    | ${validation}= | Validate Contract Instance | contracts/device_event.json | ${result.data} |
    ...    | Should Be True | ${validation.valid} |
    [Arguments]    ${schema}    ${data}
    No Operation

Inspect Contract
    [Documentation]    Returns available contract paths that can be used for overrides.
    ...
    ...    Example:
    ...    | @{fields}= | Inspect Contract | ${SCHEMA} |
    ...    | FOR | ${f} | IN | @{fields} |
    ...    | | Log | ${f.path} |
    ...    | END |
    ...
    ...    Example output:
    ...    | temperature |
    ...    | sensor.value |
    ...    | sensors[*].value |
    [Arguments]    ${schema}
    No Operation

Send Message
    [Documentation]    Sends a message (generated instance) over the configured transport (mqtt or http_mqtt etc)
    ...
    ...    Arguments:
    ...    - ``destination``: MQTT topic / url
    ...    - ``message``: GenerationResult object
    ...
    ...    Example:
    ...    | ${result}= | Generate Contract Instance | ${SCHEMA} |
    ...    | Send Message | test/topic | ${result} |
    [Arguments]    ${topic}    ${result}
    No Operation

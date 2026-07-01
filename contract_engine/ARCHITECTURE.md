# Architecture

```mermaid
graph TD
    %% Entry points
    Caller["Python caller / Robot Framework"]

    subgraph adapter["Robot Adapter"]
        KW["keywords.py"]
    end

    subgraph app["Application"]
        CE["ContractEngine (facade)"]
        CLS["ContractLoaderService"]
        GS["GeneratorService"]
        VS["ValidationService"]
        CIS["ContractIntrospectionService"]
        CRS["ContractRefinementService"]
        CVS["ContractValidationService"]
        OA["apply_overrides()"]
    end

    subgraph domain["Domain"]
        Contract["Contract\n(name, version, fields)"]
        FD["FieldDefinition\n(name, type, required)"]
        FT["FieldType hierarchy\n(Primitive / Object / Array / OneOf / Any)"]
        Seed["Seed\n(label, value)"]
        GR["GenerationResult\n(seed, data)"]
        VR["ValidationResult\n(valid, errors)"]
        FI["FieldInfo\n(path)"]
    end

    subgraph infra["Infrastructure"]
        JCP["JsonSchemaContractParser\n($ref, allOf, oneOf, primitives)"]
        RR["RefResolver\n(local + URL $ref)"]
        DG["DeterministicGenerator\n(random.Random seeded)"]
        PS["PrimitiveStrategy"]
        OS["ObjectStrategy"]
        AS["ArrayStrategy"]
        OOS["OneOfStrategy"]
        ANS["AnyStrategy"]
        JSB["JsonSchemaBuilder"]
        JSV["JsonSchemaValidator"]
        DCI["DefaultContractIntrospector"]
        MQTT["MqttTransport"]
        HTTP["HttpMqttTransport"]
        AuthF["AuthHandlerFactory\n(no-auth / basic / azure)"]
    end

    %% Caller flow
    Caller -->|"direct"| CE
    Caller -->|"Robot"| KW --> CE

    %% Facade orchestration
    CE --> CLS
    CE --> GS
    CE --> VS
    CE --> CIS
    CE --> CRS
    CE --> CVS

    %% Loader
    CLS -->|"parse(schema, base_path)"| JCP
    JCP --> RR
    JCP -->|"produces"| Contract
    Contract --> FD --> FT

    %% Refinement
    CRS -->|"deepcopy + mutate"| Contract

    %% Contract validation
    CVS -->|"validates"| Contract

    %% Generation
    GS -->|"normalize_seed → Seed"| Seed
    GS -->|"generate(contract, mode, seed)"| DG
    DG --> PS & OS & AS & OOS & ANS
    DG -->|"produces"| GR
    GS -->|"apply_overrides(data, overrides, seed)"| OA
    OA -->|"patches data in GR"| GR

    %% Validation
    VS --> JSB -->|"build JSON Schema from Contract"| JSV
    JSV -->|"produces"| VR

    %% Introspection
    CIS --> DCI -->|"produces"| FI

    %% Transport (independent of CE)
    Caller -->|"send(topic, result)"| MQTT & HTTP
    MQTT & HTTP --> AuthF
```

## Notes

- `ContractLoaderService` auto-detects Azure DevOps UI URLs and rewrites them to API URLs.
- `DeterministicGenerator` uses a strategy map keyed by `type(field_type)` — adding a new `FieldType` requires registering a strategy there.
- `GeneratorService` calls `apply_overrides` after generation, passing the `Seed` so override values can embed `{SEED}` as a placeholder.
- `ValidationService` rebuilds the JSON Schema from the domain `Contract` on every call via `JsonSchemaBuilder` — no caching.

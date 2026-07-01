from contract_engine.domain.contract import Contract
from contract_engine.domain.types import AnyOfType, ArrayType, FieldDefinition, ObjectType, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.validation.jsonschema_builder import JsonSchemaBuilder


def test_schema_contains_min_max():
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(kind="number", minimum=0, maximum=100),
            )
        ],
    )

    builder = JsonSchemaBuilder()
    schema = builder.build(contract)

    assert schema["type"] == "object"
    assert "temperature" in schema["properties"]
    assert schema["properties"]["temperature"]["minimum"] == 0
    assert schema["properties"]["temperature"]["maximum"] == 100


def test_array_schema_generation():
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="values",
                type=ArrayType(
                    items=PrimitiveType(kind="integer", minimum=0, maximum=10),
                    min_items=1,
                    max_items=5,
                ),
            )
        ],
    )

    builder = JsonSchemaBuilder()
    schema = builder.build(contract)

    arr = schema["properties"]["values"]
    assert arr["type"] == "array"
    assert arr["items"]["minimum"] == 0
    assert arr["minItems"] == 1
    assert arr["maxItems"] == 5


def test_nested_object_schema():
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="device",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="id",
                            type=PrimitiveType(kind="string"),
                        )
                    ]
                ),
            )
        ],
    )

    builder = JsonSchemaBuilder()
    schema = builder.build(contract)

    assert schema["properties"]["device"]["type"] == "object"
    assert "id" in schema["properties"]["device"]["properties"]


def test_jsonschema_string_length() -> None:
    builder = JsonSchemaBuilder()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="name",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    min_length=3,
                    max_length=10,
                ),
            )
        ],
    )

    schema = builder.build(contract)

    field_schema = schema["properties"]["name"]

    assert field_schema["minLength"] == 3
    assert field_schema["maxLength"] == 10


def test_anyof_serializes_as_anyof_not_oneof() -> None:
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="start",
                type=AnyOfType(
                    options=[
                        PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"),
                        PrimitiveType(kind=PrimitiveKind.NULL),
                    ]
                ),
            )
        ],
    )

    builder = JsonSchemaBuilder()
    schema = builder.build(contract)

    field_schema = schema["properties"]["start"]
    assert "anyOf" in field_schema
    assert "oneOf" not in field_schema
    assert len(field_schema["anyOf"]) == 2


def test_anyof_options_are_correctly_serialized() -> None:
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="start",
                type=AnyOfType(
                    options=[
                        PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"),
                        PrimitiveType(kind=PrimitiveKind.NULL),
                    ]
                ),
            )
        ],
    )

    builder = JsonSchemaBuilder()
    schema = builder.build(contract)

    options = schema["properties"]["start"]["anyOf"]
    types = {opt["type"] for opt in options}
    assert types == {"string", "null"}

    string_opt = next(o for o in options if o["type"] == "string")
    assert string_opt["format"] == "date-time"


def test_builder_writes_format_for_primitive() -> None:
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="time",
                required=True,
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    format="date-time",
                ),
            )
        ],
    )

    builder = JsonSchemaBuilder()

    schema = builder.build(contract)

    assert schema["properties"]["time"]["format"] == "date-time"

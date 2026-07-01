from pathlib import Path

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from contract_engine.domain.contract import Contract
from contract_engine.domain.types import ArrayType, FieldDefinition, ObjectType, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.contract_introspectors.default_contract_introspector import (
    DefaultContractIntrospector,
)

CONTRACTS_DIR = Path("src/contract_engine/infrastructure/contracts")


def test_primitive_constraints() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    minimum=-10,
                    maximum=50,
                ),
            )
        ],
    )

    fields = introspector.inspect(contract)

    assert len(fields) == 1
    field = fields[0]

    assert field.path == "temperature"
    assert field.type == "number"
    assert field.constraints["minimum"] == -10
    assert field.constraints["maximum"] == 50


def test_nested_object_paths() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="data",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="temperature",
                            type=PrimitiveType(kind=PrimitiveKind.NUMBER),
                        ),
                        FieldDefinition(
                            name="humidity",
                            type=PrimitiveType(kind=PrimitiveKind.NUMBER),
                        ),
                    ]
                ),
            )
        ],
    )

    fields = introspector.inspect(contract)

    paths = {f.path for f in fields}

    assert "data" in paths
    assert "data.temperature" in paths
    assert "data.humidity" in paths


def test_array_paths() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="measurements",
                type=ArrayType(
                    items=PrimitiveType(kind=PrimitiveKind.NUMBER),
                    min_items=1,
                    max_items=10,
                ),
            )
        ],
    )

    fields = introspector.inspect(contract)

    paths = {f.path for f in fields}

    assert "measurements" in paths
    assert "measurements[0]" in paths


def test_array_of_objects_paths() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="measurements",
                type=ArrayType(
                    items=ObjectType(
                        fields=[
                            FieldDefinition(
                                name="value",
                                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
                            ),
                            FieldDefinition(
                                name="unit",
                                type=PrimitiveType(kind=PrimitiveKind.STRING),
                            ),
                        ]
                    )
                ),
            )
        ],
    )

    fields = introspector.inspect(contract)

    paths = {f.path for f in fields}

    assert "measurements" in paths
    assert "measurements[0]" in paths
    assert "measurements[0].value" in paths
    assert "measurements[0].unit" in paths


def test_optional_field_flag() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="temperature",
                required=False,
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ],
    )

    fields = introspector.inspect(contract)

    assert fields[0].required is False


def test_string_constraints() -> None:
    introspector = DefaultContractIntrospector()

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="device_id",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    min_length=5,
                    max_length=10,
                    pattern="[A-Z0-9]+",
                ),
            )
        ],
    )

    fields = introspector.inspect(contract)

    constraints = fields[0].constraints

    assert constraints["min_length"] == 5
    assert constraints["max_length"] == 10
    assert constraints["pattern"] == "[A-Z0-9]+"


def test_inspect_anyof_contract() -> None:
    schema_paths = list(CONTRACTS_DIR.glob("**/JsonSchema_AlertEvent.json"))
    schema_path = schema_paths[0]

    engine = create_default_contract_engine()
    fields = engine.inspect_contract(str(schema_path), base_path=schema_path.parent)

    paths = [f.path for f in fields]

    assert paths != []

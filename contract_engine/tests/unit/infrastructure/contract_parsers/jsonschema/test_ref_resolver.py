from pathlib import Path

import pytest

from contract_engine.domain.types import ArrayType, ObjectType, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.contract_parsers.jsonschema.jsonschema_contract_parser import (
    JsonSchemaContractParser,
)


def test_parse_local_ref() -> None:
    schema = {
        "type": "object",
        "$defs": {
            "id": {
                "type": "string",
                "pattern": "^[A-Z]+$",
            }
        },
        "properties": {
            "event_id": {
                "$ref": "#/$defs/id",
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]

    assert field.name == "event_id"
    assert field.required is False

    primitive = field.type
    assert isinstance(primitive, PrimitiveType)
    assert primitive.kind == PrimitiveKind.STRING
    assert primitive.pattern == "^[A-Z]+$"


def test_parse_nested_local_ref() -> None:
    schema = {
        "type": "object",
        "$defs": {"id": {"type": "string"}},
        "properties": {
            "data": {
                "type": "object",
                "properties": {"id": {"$ref": "#/$defs/id"}},
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    data_field = contract.fields[0]
    obj = data_field.type

    assert isinstance(obj, ObjectType)

    inner = obj.fields[0]
    primitive = inner.type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.kind == PrimitiveKind.STRING


def test_parse_ref_chain() -> None:
    schema = {
        "type": "object",
        "$defs": {
            "A": {"$ref": "#/$defs/B"},
            "B": {"$ref": "#/$defs/C"},
            "C": {"type": "string"},
        },
        "properties": {"value": {"$ref": "#/$defs/A"}},
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    primitive = field.type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.kind == PrimitiveKind.STRING


def test_parse_missing_ref() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"$ref": "#/$defs/missing"}},
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="Unresolvable"):
        parser.parse(schema)


def test_parse_circular_ref() -> None:
    schema = {
        "type": "object",
        "$defs": {
            "A": {"$ref": "#/$defs/B"},
            "B": {"$ref": "#/$defs/A"},
        },
        "properties": {"value": {"$ref": "#/$defs/A"}},
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="Circular"):
        parser.parse(schema)


def test_parse_external_ref(tmp_path: Path) -> None:
    base = tmp_path / "base.json"

    base.write_text("""
    {
        "type": "string",
        "pattern": "^[A-Z]+$"
    }
    """)

    schema = {"type": "object", "properties": {"id": {"$ref": "base.json"}}}

    parser = JsonSchemaContractParser()

    contract = parser.parse(schema, base_path=base.parent)

    field = contract.fields[0]
    primitive = field.type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.pattern == "^[A-Z]+$"


def test_parse_array_items_ref() -> None:
    schema = {
        "type": "object",
        "$defs": {"id": {"type": "string"}},
        "properties": {
            "ids": {
                "type": "array",
                "items": {"$ref": "#/$defs/id"},
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    arr = field.type

    assert isinstance(arr, ArrayType)

    primitive = arr.items
    assert isinstance(primitive, PrimitiveType)
    assert primitive.kind == PrimitiveKind.STRING

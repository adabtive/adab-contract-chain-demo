import json
from pathlib import Path

import pytest

from contract_engine.domain.types import (
    AnyOfType,
    AnyType,
    ArrayType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)
from contract_engine.infrastructure.contract_parsers.jsonschema.jsonschema_contract_parser import (
    JsonSchemaContractParser,
)


def test_jsonschema_parser_parses_simple_schema() -> None:

    path = Path("tests/fixtures/contracts/simple_schema.json")

    with path.open() as f:
        document = json.load(f)

    parser = JsonSchemaContractParser()

    contract = parser.parse(document)

    assert contract.name == "simple_test_contract"
    assert len(contract.fields) == 4


def test_parse_const_string() -> None:

    schema = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "alert_event",
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    primitive = field.type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.enum == ["alert_event"]


def test_parse_const_via_ref() -> None:

    schema = {
        "$defs": {
            "event_type": {
                "type": "string",
                "const": "alert_event",
            }
        },
        "type": "object",
        "properties": {"type": {"$ref": "#/$defs/event_type"}},
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    primitive = contract.fields[0].type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.enum == ["alert_event"]


def test_parse_const_integer() -> None:

    schema = {
        "type": "object",
        "properties": {
            "version": {
                "type": "integer",
                "const": 1,
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    primitive = contract.fields[0].type

    assert isinstance(primitive, PrimitiveType)
    assert primitive.enum == [1]


def test_parse_const_overrides_enum() -> None:
    schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["open", "closed", "pending"],
                "const": "open",
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    primitive = field.type

    assert isinstance(primitive, PrimitiveType)

    assert primitive.enum == ["open"]


def test_parse_allof_merges_properties() -> None:

    schema = {
        "type": "object",
        "properties": {
            "user": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                    },
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    obj = field.type

    assert isinstance(obj, ObjectType)
    assert {f.name for f in obj.fields} == {"id", "name"}


def test_parse_allof_with_ref() -> None:

    schema = {
        "$defs": {
            "base": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            }
        },
        "type": "object",
        "properties": {
            "user": {
                "allOf": [
                    {"$ref": "#/$defs/base"},
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    user = contract.fields[0].type
    assert isinstance(user, ObjectType)
    assert {f.name for f in user.fields} == {"id", "name"}


def test_allof_ref_plus_inline_properties() -> None:
    schema = {
        "$defs": {
            "Base": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            }
        },
        "type": "object",
        "properties": {
            "event": {
                "allOf": [
                    {"$ref": "#/$defs/Base"},
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    event = contract.fields[0].type
    assert isinstance(event, ObjectType)

    assert {f.name for f in event.fields} == {"id", "name"}


def test_allof_ref_plus_partial_schema() -> None:
    schema = {
        "$defs": {
            "Base": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            }
        },
        "type": "object",
        "properties": {
            "event": {
                "allOf": [
                    {"$ref": "#/$defs/Base"},
                    {"properties": {"name": {"type": "string"}}},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    event = contract.fields[0].type
    assert isinstance(event, ObjectType)

    assert {f.name for f in event.fields} == {"id", "name"}


def test_allof_multiple_refs() -> None:
    schema = {
        "$defs": {
            "A": {
                "type": "object",
                "properties": {"a": {"type": "string"}},
            },
            "B": {
                "type": "object",
                "properties": {"b": {"type": "string"}},
            },
        },
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"$ref": "#/$defs/A"},
                    {"$ref": "#/$defs/B"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    value = contract.fields[0].type
    assert isinstance(value, ObjectType)

    assert {f.name for f in value.fields} == {"a", "b"}


def test_allof_merges_required() -> None:
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                        "required": ["id"],
                    },
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    user = contract.fields[0].type
    assert isinstance(user, ObjectType)

    required = {f.name for f in user.fields if f.required}
    assert required == {"id", "name"}


def test_allof_merges_numeric_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "integer", "minimum": 10},
                    {"type": "integer", "maximum": 20},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    primitive = contract.fields[0].type
    assert isinstance(primitive, PrimitiveType)

    assert primitive.minimum == 10
    assert primitive.maximum == 20


def test_allof_nested_allof() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"allOf": [{"allOf": [{"type": "string"}]}]}},
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    primitive = contract.fields[0].type
    assert isinstance(primitive, PrimitiveType)
    assert primitive.kind == PrimitiveKind.STRING


def test_allof_conflicting_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "integer", "minimum": 10},
                    {"type": "integer", "maximum": 5},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="conflicting"):
        parser.parse(schema)


def test_allof_conflicting_numeric_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "integer", "minimum": 10},
                    {"type": "integer", "maximum": 5},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="minimum > maximum"):
        parser.parse(schema)


def test_allof_conflicting_string_lengths() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "string", "minLength": 10},
                    {"type": "string", "maxLength": 5},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="minLength > maxLength"):
        parser.parse(schema)


def test_allof_conflicting_enum() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "string", "enum": ["A"]},
                    {"type": "string", "enum": ["B"]},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="empty enum"):
        parser.parse(schema)


def test_allof_conflicting_types() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "allOf": [
                    {"type": "string"},
                    {"type": "integer"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(ValueError, match="conflicting type"):
        parser.parse(schema)


def test_parser_preserves_format() -> None:
    schema = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "format": "date-time",
            }
        },
        "required": ["date"],
    }

    parser = JsonSchemaContractParser()

    contract = parser.parse(schema)

    field = contract.fields[0]

    assert isinstance(field.type, PrimitiveType)
    assert field.type.format == "date-time"


def test_type_union_is_parsed_as_oneof() -> None:
    parser = JsonSchemaContractParser()

    schema = {"type": "object", "properties": {"data": {"type": ["string", "null"]}}}

    contract = parser.parse(schema)

    field = contract.fields[0]

    assert isinstance(field.type, OneOfType)
    assert len(field.type.options) == 2

    option_types = {type(opt) for opt in field.type.options}
    assert PrimitiveType in option_types


def test_type_union_preserves_constraints() -> None:
    parser = JsonSchemaContractParser()

    schema = {"type": "object", "properties": {"data": {"type": ["string", "null"], "minLength": 5}}}

    contract = parser.parse(schema)

    field = contract.fields[0]
    oneof = field.type

    assert isinstance(oneof, OneOfType)

    string_option = next(
        opt for opt in oneof.options if isinstance(opt, PrimitiveType) and opt.kind == PrimitiveKind.STRING
    )

    assert string_option.min_length == 5


def test_allof_merges_property_constraints_deeply() -> None:
    parser = JsonSchemaContractParser()

    schema = {
        "type": "object",
        "allOf": [
            {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "pattern": "^abc$",
                    }
                },
            },
            {
                "type": "object",
                "properties": {
                    "type": {
                        "const": "abc",
                    }
                },
            },
        ],
    }

    contract = parser.parse(schema)

    field = next(f for f in contract.fields if f.name == "type")

    assert isinstance(field.type, PrimitiveType)
    assert field.type.kind == PrimitiveKind.STRING

    assert field.type.pattern == "^abc$"
    assert field.type.enum == ["abc"]


def test_parse_root_level_one_of() -> None:
    schema = {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "const": "sensor"},
                    "value": {"type": "number"},
                },
                "required": ["kind", "value"],
            },
            {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "const": "alert"},
                    "message": {"type": "string"},
                },
                "required": ["kind", "message"],
            },
        ]
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    assert contract.fields == []
    assert isinstance(contract.root_type, OneOfType)
    assert len(contract.root_type.options) == 2


def test_parse_additional_properties_sub_schema() -> None:
    schema = {
        "type": "object",
        "properties": {
            "props": {
                "type": "object",
                "additionalProperties": {"type": "number"},
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    obj = contract.fields[0].type
    assert isinstance(obj, ObjectType)
    assert isinstance(obj.additional_properties, PrimitiveType)
    assert obj.additional_properties.kind == PrimitiveKind.NUMBER


def test_parse_additional_properties_invalid_type_raises() -> None:
    schema = {
        "type": "object",
        "properties": {
            "props": {
                "type": "object",
                "additionalProperties": "yes please",
            }
        },
    }

    parser = JsonSchemaContractParser()

    with pytest.raises(TypeError, match="additionalProperties must be a bool or a schema object"):
        parser.parse(schema)


def test_parse_anyof_produces_anyoftype() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "integer"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    assert isinstance(field.type, AnyOfType)
    assert not isinstance(field.type, OneOfType)
    assert len(field.type.options) == 2


def test_parse_anyof_nullable_string() -> None:
    schema = {
        "type": "object",
        "properties": {
            "start": {
                "anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    assert isinstance(field.type, AnyOfType)

    kinds = {opt.kind for opt in field.type.options if isinstance(opt, PrimitiveType)}
    assert PrimitiveKind.STRING in kinds
    assert PrimitiveKind.NULL in kinds


def test_parse_anyof_preserves_format() -> None:
    schema = {
        "type": "object",
        "properties": {
            "start": {
                "anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    anyof = contract.fields[0].type
    assert isinstance(anyof, AnyOfType)

    string_opt = next(o for o in anyof.options if isinstance(o, PrimitiveType) and o.kind == PrimitiveKind.STRING)
    assert string_opt.format == "date-time"


def test_parse_anyof_three_options() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "integer"},
                    {"type": "null"},
                ]
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    field = contract.fields[0]
    assert isinstance(field.type, AnyOfType)
    assert len(field.type.options) == 3


def test_parse_additional_properties_bool_unaffected() -> None:
    schema = {
        "type": "object",
        "properties": {
            "props": {
                "type": "object",
                "additionalProperties": False,
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    obj = contract.fields[0].type
    assert isinstance(obj, ObjectType)
    assert obj.additional_properties is False


def test_parse_tuple_array_produces_prefix_items() -> None:
    schema = {
        "type": "object",
        "properties": {
            "coords": {
                "type": "array",
                "items": [
                    {"type": "number"},
                    {"type": "number"},
                ],
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    arr = contract.fields[0].type
    assert isinstance(arr, ArrayType)
    assert len(arr.prefix_items) == 2
    assert all(isinstance(p, PrimitiveType) for p in arr.prefix_items)


def test_parse_tuple_array_items_defaults_to_anytype() -> None:
    schema = {
        "type": "object",
        "properties": {
            "coords": {
                "type": "array",
                "items": [{"type": "number"}, {"type": "string"}],
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    arr = contract.fields[0].type
    assert isinstance(arr, ArrayType)
    assert isinstance(arr.items, AnyType)


def test_parse_tuple_array_additional_items_schema() -> None:
    schema = {
        "type": "object",
        "properties": {
            "slots": {
                "type": "array",
                "items": [{"type": "string"}, {"type": "integer"}],
                "additionalItems": {"type": "boolean"},
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    arr = contract.fields[0].type
    assert isinstance(arr, ArrayType)
    assert arr.allow_additional_items is True
    assert isinstance(arr.items, PrimitiveType)
    assert arr.items.kind == PrimitiveKind.BOOLEAN


def test_parse_tuple_array_additional_items_false() -> None:
    schema = {
        "type": "object",
        "properties": {
            "fixed": {
                "type": "array",
                "items": [{"type": "string"}, {"type": "integer"}],
                "additionalItems": False,
            }
        },
    }

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema)

    arr = contract.fields[0].type
    assert isinstance(arr, ArrayType)
    assert arr.allow_additional_items is False

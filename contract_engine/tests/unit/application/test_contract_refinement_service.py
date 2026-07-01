import re
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from contract_engine.application.contract_refinement_service import ContractRefinementService
from contract_engine.application.contract_validation_service import ContractValidationService
from contract_engine.domain.contract import Contract
from contract_engine.domain.errors import ContractValidationError
from contract_engine.domain.types import (
    AnyType,
    ArrayType,
    FieldDefinition,
    FieldType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)

if TYPE_CHECKING:
    from contract_engine.application.contract_refinement_types import Refinements


def make_contract(fields: list[FieldDefinition]) -> Contract:
    return Contract(
        name="test",
        version="1.0",
        fields=fields,
    )


def test_const_applied() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"temperature": {"const": 42}},
    )

    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)

    assert t.enum == [42]


def test_const_nested() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="sensor",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="value",
                            type=PrimitiveType(kind=PrimitiveKind.NUMBER),
                        )
                    ]
                ),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"sensor.value": {"const": 10}},
    )

    t = refined.fields[0].type
    assert isinstance(t, ObjectType)

    inner = t.fields[0].type
    assert isinstance(inner, PrimitiveType)

    assert inner.enum == [10]


def test_const_array() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="data",
                type=ArrayType(items=PrimitiveType(kind=PrimitiveKind.STRING)),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"data[*]": {"const": "A"}},
    )
    t = refined.fields[0].type
    assert isinstance(t, ArrayType)

    items = t.items
    assert isinstance(items, PrimitiveType)

    assert items.enum == ["A"]


def test_invalid_path() -> None:
    contract = make_contract([])

    service = ContractRefinementService()

    with pytest.raises(ValueError, match="unknown"):
        service.refine(contract, {"unknown": {"const": 1}})


def test_minimum_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"minimum": 10}},
    )

    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)
    assert t.minimum == 10


def test_maximum_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"maximum": 100}},
    )

    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)
    assert t.maximum == 100


def test_min_and_max_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"minimum": 10, "maximum": 20}},
    )

    t = refined.fields[0].type

    assert isinstance(t, PrimitiveType)
    assert t.minimum == 10
    assert t.maximum == 20


def test_invalid_range_after_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    minimum=0,
                    maximum=10,
                ),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"minimum": 20}},
    )
    validator = ContractValidationService()
    with pytest.raises(ContractValidationError):
        validator.validate_contract(refined)


def test_array_minimum() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="data",
                type=ArrayType(items=PrimitiveType(kind=PrimitiveKind.NUMBER)),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"data[*]": {"minimum": 5}},
    )

    t = refined.fields[0].type
    assert isinstance(t, ArrayType)

    items = t.items
    assert isinstance(items, PrimitiveType)

    assert items.minimum == 5


def test_min_length_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="name",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"name": {"min_length": 3}},
    )

    t = refined.fields[0].type

    assert isinstance(t, PrimitiveType)
    assert t.min_length == 3


def test_min_max_length_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="name",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"name": {"min_length": 2, "max_length": 5}},
    )

    t = refined.fields[0].type

    assert isinstance(t, PrimitiveType)

    assert t.min_length == 2
    assert t.max_length == 5


def test_invalid_length_range() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="name",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    min_length=1,
                    max_length=5,
                ),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"name": {"min_length": 10}},
    )
    validator = ContractValidationService()
    with pytest.raises(ContractValidationError):
        validator.validate_contract(refined)


def test_enum_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"enum": [1, 2, 3]}},
    )

    t = refined.fields[0].type

    assert isinstance(t, PrimitiveType)

    assert t.enum == [1, 2, 3]


def test_enum_refinement_overrides() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER, enum=[4, 5, 6]),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"value": {"enum": [1, 2, 3]}},
    )

    t = refined.fields[0].type

    assert isinstance(t, PrimitiveType)

    assert t.enum == [1, 2, 3]


def test_format_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="id",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"id": {"format": "uuid"}},
    )

    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)
    assert t.format == "uuid"


def test_pattern_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="code",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {"code": {"pattern": "^[A-Z]+$"}},
    )

    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)
    assert t.pattern == "^[A-Z]+$"


def test_string_refinement_all_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    }

    engine = create_default_contract_engine()

    refinements: Refinements = {
        "code": {
            "min_length": 5,
            "max_length": 5,
            "pattern": "^[A-Z]+$",
            "enum": ["HELLO"],  # strongest constraint
            "format": "uuid",  # interesting: conflicting with enum/pattern
        }
    }

    result = engine.generate_instance(
        schema,
        refinements=refinements,
        seed="test",
    )

    value = result.data["code"]

    assert isinstance(value, str)
    assert value == "HELLO"
    assert len(value) == 5
    assert re.match("^[A-Z]+$", value)


def test_string_constraints_invalid_range() -> None:
    schema = {
        "type": "object",
        "properties": {"code": {"type": "string"}},
    }

    engine = create_default_contract_engine()

    with pytest.raises(ContractValidationError):
        engine.generate_instance(
            schema,
            refinements={
                "code": {
                    "min_length": 10,
                    "max_length": 5,
                }
            },
        )


def _make_one_of_contract(options: list[FieldType]) -> Contract:
    return make_contract(
        [
            FieldDefinition(
                name="payload",
                type=OneOfType(options=options),
            )
        ]
    )


def _sensor_option() -> ObjectType:
    return ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["sensor"])),
            FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER)),
        ]
    )


def _alert_option() -> ObjectType:
    return ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["alert"])),
            FieldDefinition(name="message", type=PrimitiveType(kind=PrimitiveKind.STRING)),
        ]
    )


def test_one_of_filter_keeps_matching_option() -> None:
    contract = _make_one_of_contract([_sensor_option(), _alert_option()])
    service = ContractRefinementService()

    refined = service.refine(contract, {"payload": {"one_of_filter": {"kind": "sensor"}}})

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    assert len(payload_type.options) == 1
    option = payload_type.options[0]
    assert isinstance(option, ObjectType)
    assert any(field.name == "value" for field in option.fields)


def test_one_of_filter_no_match_raises() -> None:
    contract = _make_one_of_contract([_sensor_option(), _alert_option()])
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="matched no options"):
        service.refine(contract, {"payload": {"one_of_filter": {"kind": "unknown"}}})


def test_one_of_filter_on_non_one_of_raises() -> None:
    contract = make_contract([FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.STRING))])
    service = ContractRefinementService()

    with pytest.raises(TypeError, match="one_of_filter only supported"):
        service.refine(contract, {"value": {"one_of_filter": {"kind": "sensor"}}})


def test_one_of_path_traversal_applies_to_all_options() -> None:
    sensor = ObjectType(
        fields=[
            FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER)),
        ]
    )
    alert = ObjectType(
        fields=[
            FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER)),
        ]
    )
    contract = _make_one_of_contract([sensor, alert])
    service = ContractRefinementService()

    refined = service.refine(contract, {"payload.value": {"minimum": 99}})

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    for option in payload_type.options:
        assert isinstance(option, ObjectType)
        value_field = next(field for field in option.fields if field.name == "value")
        assert isinstance(value_field.type, PrimitiveType)
        assert value_field.type.minimum == 99


def test_one_of_path_traversal_no_match_raises() -> None:
    contract = _make_one_of_contract([_sensor_option(), _alert_option()])
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="not found in any oneOf option"):
        service.refine(contract, {"payload.nonexistent": {"minimum": 0}})


def test_one_of_path_traversal_deeper_nested() -> None:
    sensor = ObjectType(
        fields=[
            FieldDefinition(
                name="reading",
                type=ObjectType(
                    fields=[
                        FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER)),
                    ]
                ),
            )
        ]
    )
    alert = ObjectType(
        fields=[
            FieldDefinition(
                name="reading",
                type=ObjectType(
                    fields=[
                        FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER)),
                    ]
                ),
            )
        ]
    )
    contract = _make_one_of_contract([sensor, alert])
    service = ContractRefinementService()

    refined = service.refine(contract, {"payload.reading.value": {"maximum": 10}})

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    for option in payload_type.options:
        assert isinstance(option, ObjectType)
        reading = next(field for field in option.fields if field.name == "reading")
        assert isinstance(reading.type, ObjectType)
        value_field = next(field for field in reading.type.fields if field.name == "value")
        assert isinstance(value_field.type, PrimitiveType)
        assert value_field.type.maximum == 10


def test_one_of_filter_multiple_conditions_all_must_match() -> None:
    v1_sensor = ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["sensor"])),
            FieldDefinition(name="version", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["v1"])),
        ]
    )
    v2_sensor = ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["sensor"])),
            FieldDefinition(name="version", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["v2"])),
        ]
    )
    contract = _make_one_of_contract([v1_sensor, v2_sensor])
    service = ContractRefinementService()

    refined = service.refine(contract, {"payload": {"one_of_filter": {"kind": "sensor", "version": "v2"}}})

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    assert len(payload_type.options) == 1
    option = payload_type.options[0]
    assert isinstance(option, ObjectType)
    version_field = next(field for field in option.fields if field.name == "version")
    assert isinstance(version_field.type, PrimitiveType)
    assert version_field.type.enum == ["v2"]


def test_one_of_filter_multiple_branches_survive() -> None:
    sensor_a = ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["sensor"])),
            FieldDefinition(name="channel", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["a"])),
        ]
    )
    sensor_b = ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["sensor"])),
            FieldDefinition(name="channel", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["b"])),
        ]
    )
    alert = ObjectType(
        fields=[
            FieldDefinition(name="kind", type=PrimitiveType(kind=PrimitiveKind.STRING, enum=["alert"])),
        ]
    )
    contract = _make_one_of_contract([sensor_a, sensor_b, alert])
    service = ContractRefinementService()

    refined = service.refine(contract, {"payload": {"one_of_filter": {"kind": "sensor"}}})

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    assert len(payload_type.options) == 2
    for option in payload_type.options:
        assert isinstance(option, ObjectType)
        kind_field = next(field for field in option.fields if field.name == "kind")
        assert isinstance(kind_field.type, PrimitiveType)
        assert kind_field.type.enum == ["sensor"]


def test_required_true_forces_optional_field() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="subject",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
                required=False,
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(contract, {"subject": {"required": True}})

    assert refined.fields[0].required is True


def test_required_false_makes_field_optional() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="subject",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
                required=True,
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(contract, {"subject": {"required": False}})

    assert refined.fields[0].required is False


def test_required_combined_with_other_constraint() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="subject",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
                required=False,
            )
        ]
    )

    service = ContractRefinementService()

    refined = service.refine(contract, {"subject": {"required": True, "const": "fixed"}})

    assert refined.fields[0].required is True
    t = refined.fields[0].type
    assert isinstance(t, PrimitiveType)
    assert t.enum == ["fixed"]


def test_required_does_not_mutate_original() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="subject",
                type=PrimitiveType(kind=PrimitiveKind.STRING),
                required=False,
            )
        ]
    )

    service = ContractRefinementService()
    service.refine(contract, {"subject": {"required": True}})

    assert contract.fields[0].required is False


def test_required_on_root_raises() -> None:
    contract = Contract(name="test", version="1.0", fields=[], root_type=AnyType())
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="not supported at root level"):
        service.refine(contract, {"": {"required": True}})


def test_one_of_filter_then_path_refinement_ordered() -> None:
    contract = _make_one_of_contract([_sensor_option(), _alert_option()])
    service = ContractRefinementService()

    refined = service.refine(
        contract,
        {
            "payload": {"one_of_filter": {"kind": "sensor"}},
            "payload.value": {"minimum": 50},
        },
    )

    payload_type = refined.fields[0].type
    assert isinstance(payload_type, OneOfType)
    assert len(payload_type.options) == 1
    option = payload_type.options[0]
    assert isinstance(option, ObjectType)
    value_field = next(field for field in option.fields if field.name == "value")
    assert isinstance(value_field.type, PrimitiveType)
    assert value_field.type.minimum == 50


def test_additional_properties_schema_promotes_field_on_refinement() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(
                    additional_properties=PrimitiveType(kind=PrimitiveKind.NUMBER),
                ),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"props.Value": {"minimum": 15.0}})

    props = refined.fields[0].type
    assert isinstance(props, ObjectType)
    value_field = next(f for f in props.fields if f.name == "Value")
    assert isinstance(value_field.type, PrimitiveType)
    assert value_field.type.minimum == 15.0
    assert value_field.required is False


def test_additional_properties_schema_does_not_mutate_original() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(
                    additional_properties=PrimitiveType(kind=PrimitiveKind.NUMBER),
                ),
            )
        ]
    )
    service = ContractRefinementService()
    service.refine(contract, {"props.Value": {"minimum": 15.0}})

    props = contract.fields[0].type
    assert isinstance(props, ObjectType)
    assert props.fields == []


def test_additional_properties_true_missing_type_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(additional_properties=True),
            )
        ]
    )
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="type"):
        service.refine(contract, {"props.Value": {"minimum": 1.0}})


def test_additional_properties_false_unknown_path_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(additional_properties=False),
            )
        ]
    )
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="unknown"):
        service.refine(contract, {"props.Value": {"minimum": 1.0}})


def test_additional_properties_true_with_number_type_promotes_field() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(additional_properties=True),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"props.Value": {"type": "number", "minimum": 15.0, "maximum": 35.0}})

    props = refined.fields[0].type
    assert isinstance(props, ObjectType)
    value_field = next(f for f in props.fields if f.name == "Value")
    assert isinstance(value_field.type, PrimitiveType)
    assert value_field.type.kind == PrimitiveKind.NUMBER
    assert value_field.type.minimum == 15.0
    assert value_field.type.maximum == 35.0
    assert value_field.required is False


def test_additional_properties_true_with_string_type_promotes_field() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(additional_properties=True),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"props.Label": {"type": "string", "min_length": 3}})

    props = refined.fields[0].type
    assert isinstance(props, ObjectType)
    label_field = next(f for f in props.fields if f.name == "Label")
    assert isinstance(label_field.type, PrimitiveType)
    assert label_field.type.kind == PrimitiveKind.STRING
    assert label_field.type.min_length == 3
    assert label_field.required is False


def test_additional_properties_true_does_not_mutate_original() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(additional_properties=True),
            )
        ]
    )
    service = ContractRefinementService()
    service.refine(contract, {"props.Value": {"type": "number", "minimum": 1.0}})

    props = contract.fields[0].type
    assert isinstance(props, ObjectType)
    assert props.fields == []


def test_additional_properties_schema_promotes_field_with_required_and_constraint() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="props",
                type=ObjectType(
                    additional_properties=PrimitiveType(kind=PrimitiveKind.STRING),
                ),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"props.Label": {"required": True, "min_length": 5}})

    props = refined.fields[0].type
    assert isinstance(props, ObjectType)
    label_field = next(f for f in props.fields if f.name == "Label")
    assert label_field.required is True
    assert isinstance(label_field.type, PrimitiveType)
    assert label_field.type.min_length == 5


def test_additional_properties_schema_end_to_end() -> None:
    schema = {
        "type": "object",
        "properties": {
            "props": {
                "type": "object",
                "additionalProperties": {"type": "number", "minimum": 0},
            }
        },
    }
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"props.Value": {"minimum": 15.0, "maximum": 35.0}},
        seed="test",
    )

    value = result.data["props"]["Value"]
    assert isinstance(value, float | int)
    assert 15.0 <= value <= 35.0


def test_min_items_sets_array_lower_bound() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="tags",
                type=ArrayType(items=PrimitiveType(kind=PrimitiveKind.STRING)),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"tags": {"min_items": 3}})

    assert isinstance(refined.fields[0].type, ArrayType)
    assert refined.fields[0].type.min_items == 3


def test_max_items_sets_array_upper_bound() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="tags",
                type=ArrayType(items=PrimitiveType(kind=PrimitiveKind.STRING)),
            )
        ]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"tags": {"max_items": 1}})

    assert isinstance(refined.fields[0].type, ArrayType)
    assert refined.fields[0].type.max_items == 1


def test_min_max_items_does_not_mutate_original() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="tags",
                type=ArrayType(items=PrimitiveType(kind=PrimitiveKind.STRING)),
            )
        ]
    )
    service = ContractRefinementService()
    service.refine(contract, {"tags": {"min_items": 2, "max_items": 2}})

    original = contract.fields[0].type
    assert isinstance(original, ArrayType)
    assert original.min_items is None
    assert original.max_items is None


def test_min_items_on_non_array_raises() -> None:
    contract = make_contract([FieldDefinition(name="name", type=PrimitiveType(kind=PrimitiveKind.STRING))])
    service = ContractRefinementService()

    with pytest.raises(TypeError, match="min_items only supported for array types"):
        service.refine(contract, {"name": {"min_items": 1}})


def test_min_max_items_end_to_end() -> None:
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"tags": {"min_items": 2, "max_items": 2}},
        seed="test",
    )

    assert isinstance(result.data["tags"], list)
    assert len(result.data["tags"]) == 2


def test_minimum_date_time_sets_lower_bound() -> None:
    dt = datetime(2024, 1, 1, tzinfo=UTC)
    contract = make_contract(
        [FieldDefinition(name="ts", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"ts": {"minimum_date_time": dt}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.minimum_date_time == dt


def test_maximum_date_time_sets_upper_bound() -> None:
    dt = datetime(2025, 1, 1, tzinfo=UTC)
    contract = make_contract(
        [FieldDefinition(name="ts", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"ts": {"maximum_date_time": dt}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.maximum_date_time == dt


def test_date_time_bounds_end_to_end() -> None:
    schema = {
        "type": "object",
        "properties": {"timestamp": {"type": "string", "format": "date-time"}},
    }
    min_dt = datetime(2024, 6, 1, tzinfo=UTC)
    max_dt = datetime(2024, 6, 30, tzinfo=UTC)
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"timestamp": {"minimum_date_time": min_dt, "maximum_date_time": max_dt}},
        seed="test",
    )

    generated = datetime.fromisoformat(result.data["timestamp"])
    assert min_dt <= generated <= max_dt


def test_date_time_bounds_does_not_mutate_original() -> None:
    dt = datetime(2024, 1, 1, tzinfo=UTC)
    contract = make_contract(
        [FieldDefinition(name="ts", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"))]
    )
    service = ContractRefinementService()
    service.refine(contract, {"ts": {"minimum_date_time": dt, "maximum_date_time": dt}})

    original = contract.fields[0].type
    assert isinstance(original, PrimitiveType)
    assert original.minimum_date_time is None
    assert original.maximum_date_time is None


def test_date_time_upper_below_lower_raises() -> None:
    schema = {
        "type": "object",
        "properties": {"timestamp": {"type": "string", "format": "date-time"}},
    }
    min_dt = datetime(2025, 1, 1, tzinfo=UTC)
    max_dt = datetime(2024, 1, 1, tzinfo=UTC)
    engine = create_default_contract_engine()

    with pytest.raises(ValueError, match="maximum_date_time must be >= minimum_date_time"):
        engine.generate_instance(
            schema,
            refinements={"timestamp": {"minimum_date_time": min_dt, "maximum_date_time": max_dt}},
            seed="test",
        )


def test_date_time_upper_equals_lower_pins_value() -> None:
    schema = {
        "type": "object",
        "properties": {"timestamp": {"type": "string", "format": "date-time"}},
    }
    pinned = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"timestamp": {"minimum_date_time": pinned, "maximum_date_time": pinned}},
        seed="test",
    )

    assert datetime.fromisoformat(result.data["timestamp"]) == pinned


def _make_primitive_union(kinds: list[PrimitiveKind]) -> FieldDefinition:
    return FieldDefinition(
        name="value",
        type=OneOfType(options=[PrimitiveType(kind=k) for k in kinds]),
    )


def test_type_filter_single_str_filters_and_applies_constraints() -> None:
    contract = make_contract(
        [_make_primitive_union([PrimitiveKind.BOOLEAN, PrimitiveKind.STRING, PrimitiveKind.NUMBER])]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"value": {"type": "number", "minimum": 5.0}})

    field_type = refined.fields[0].type
    assert isinstance(field_type, OneOfType)
    assert len(field_type.options) == 1
    surviving = field_type.options[0]
    assert isinstance(surviving, PrimitiveType)
    assert surviving.kind == PrimitiveKind.NUMBER
    assert surviving.minimum == 5.0


def test_type_filter_list_keeps_one_of_with_survivors() -> None:
    contract = make_contract(
        [_make_primitive_union([PrimitiveKind.BOOLEAN, PrimitiveKind.STRING, PrimitiveKind.NUMBER])]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"value": {"type": ["string", "number"]}})

    field_type = refined.fields[0].type
    assert isinstance(field_type, OneOfType)
    assert len(field_type.options) == 2
    kinds = {opt.kind for opt in field_type.options if isinstance(opt, PrimitiveType)}
    assert kinds == {PrimitiveKind.STRING, PrimitiveKind.NUMBER}


def test_type_filter_no_match_raises() -> None:
    contract = make_contract([_make_primitive_union([PrimitiveKind.BOOLEAN, PrimitiveKind.STRING])])
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="matched no oneOf options"):
        service.refine(contract, {"value": {"type": "number"}})


def test_type_filter_unknown_type_raises() -> None:
    contract = make_contract([_make_primitive_union([PrimitiveKind.STRING])])
    service = ContractRefinementService()

    with pytest.raises(ValueError, match="unknown type"):
        service.refine(contract, {"value": {"type": "banana"}})


def test_type_filter_does_not_mutate_original() -> None:
    contract = make_contract(
        [_make_primitive_union([PrimitiveKind.BOOLEAN, PrimitiveKind.STRING, PrimitiveKind.NUMBER])]
    )
    service = ContractRefinementService()
    service.refine(contract, {"value": {"type": "number"}})

    original = contract.fields[0].type
    assert isinstance(original, OneOfType)
    assert len(original.options) == 3


def test_type_filter_list_with_primitive_constraint_raises() -> None:
    contract = make_contract([_make_primitive_union([PrimitiveKind.STRING, PrimitiveKind.NUMBER])])
    service = ContractRefinementService()

    with pytest.raises(TypeError, match="minimum only supported for primitive types"):
        service.refine(contract, {"value": {"type": ["string", "number"], "minimum": 5.0}})


def test_minimum_date_sets_lower_bound() -> None:
    d = date(2024, 1, 1)
    contract = make_contract(
        [FieldDefinition(name="day", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"day": {"minimum_date": d}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.minimum_date == d


def test_maximum_date_sets_upper_bound() -> None:
    d = date(2025, 1, 1)
    contract = make_contract(
        [FieldDefinition(name="day", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"day": {"maximum_date": d}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.maximum_date == d


def test_date_bounds_end_to_end() -> None:
    schema = {"type": "object", "properties": {"day": {"type": "string", "format": "date"}}}
    min_d = date(2024, 6, 1)
    max_d = date(2024, 6, 30)
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema, refinements={"day": {"minimum_date": min_d, "maximum_date": max_d}}, seed="test"
    )

    generated = date.fromisoformat(result.data["day"])
    assert min_d <= generated <= max_d


def test_date_bounds_does_not_mutate_original() -> None:
    d = date(2024, 1, 1)
    contract = make_contract(
        [FieldDefinition(name="day", type=PrimitiveType(kind=PrimitiveKind.STRING, format="date"))]
    )
    service = ContractRefinementService()
    service.refine(contract, {"day": {"minimum_date": d, "maximum_date": d}})

    original = contract.fields[0].type
    assert isinstance(original, PrimitiveType)
    assert original.minimum_date is None
    assert original.maximum_date is None


def test_minimum_duration_sets_lower_bound() -> None:
    dur = timedelta(hours=1)
    contract = make_contract(
        [FieldDefinition(name="dur", type=PrimitiveType(kind=PrimitiveKind.STRING, format="isoduration"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"dur": {"minimum_duration": dur}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.minimum_duration == dur


def test_maximum_duration_sets_upper_bound() -> None:
    dur = timedelta(hours=5)
    contract = make_contract(
        [FieldDefinition(name="dur", type=PrimitiveType(kind=PrimitiveKind.STRING, format="isoduration"))]
    )
    service = ContractRefinementService()

    refined = service.refine(contract, {"dur": {"maximum_duration": dur}})

    field = refined.fields[0].type
    assert isinstance(field, PrimitiveType)
    assert field.maximum_duration == dur


def test_duration_bounds_end_to_end() -> None:
    schema = {"type": "object", "properties": {"dur": {"type": "string", "format": "isoduration"}}}
    min_dur = timedelta(hours=1)
    max_dur = timedelta(hours=2)
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema, refinements={"dur": {"minimum_duration": min_dur, "maximum_duration": max_dur}}, seed="test"
    )

    value = result.data["dur"]
    assert isinstance(value, str)
    assert value.startswith("P")


def test_duration_bounds_does_not_mutate_original() -> None:
    dur = timedelta(hours=1)
    contract = make_contract(
        [FieldDefinition(name="dur", type=PrimitiveType(kind=PrimitiveKind.STRING, format="isoduration"))]
    )
    service = ContractRefinementService()
    service.refine(contract, {"dur": {"minimum_duration": dur, "maximum_duration": dur}})

    original = contract.fields[0].type
    assert isinstance(original, PrimitiveType)
    assert original.minimum_duration is None
    assert original.maximum_duration is None


def test_type_filter_end_to_end() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"type": ["boolean", "string", "integer", "number"]}},
    }
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"value": {"type": "number", "minimum": 10.0, "maximum": 20.0}},
        seed="test",
    )

    assert isinstance(result.data["value"], float)
    assert 10.0 <= result.data["value"] <= 20.0

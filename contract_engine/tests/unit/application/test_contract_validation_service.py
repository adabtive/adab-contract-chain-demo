import pytest

from contract_engine.application.contract_validation_service import ContractValidationService
from contract_engine.domain.contract import Contract
from contract_engine.domain.errors import ContractValidationError
from contract_engine.domain.types import ArrayType, FieldDefinition, OneOfType, PrimitiveKind, PrimitiveType


def make_contract(fields: list[FieldDefinition]) -> Contract:
    return Contract(
        name="test",
        version="1.0",
        fields=fields,
    )


def test_valid_primitive_passes() -> None:

    contract = make_contract(
        [
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    minimum=0,
                    maximum=100,
                ),
            )
        ]
    )

    validator = ContractValidationService()

    validator.validate_contract(contract)  # should not raise


def test_min_greater_than_max_raises() -> None:

    contract = make_contract(
        [
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    minimum=50,
                    maximum=40,
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError) as exc:
        validator.validate_contract(contract)

    assert "minimum" in str(exc.value)


def test_min_length_greater_than_max_length() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="name",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    min_length=10,
                    max_length=5,
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_empty_enum_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="status",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    enum=[],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_invalid_array_min_max_items() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="items",
                type=ArrayType(
                    items=PrimitiveType(kind=PrimitiveKind.NUMBER),
                    min_items=5,
                    max_items=2,
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_oneof_empty_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="field",
                type=OneOfType(options=[]),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_nested_invalid_field() -> None:
    from contract_engine.application.contract_validation_service import ContractValidationService
    from contract_engine.domain.errors import ContractValidationError
    from contract_engine.domain.types import (
        FieldDefinition,
        ObjectType,
        PrimitiveKind,
        PrimitiveType,
    )

    contract = make_contract(
        [
            FieldDefinition(
                name="sensor",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="value",
                            type=PrimitiveType(
                                kind=PrimitiveKind.NUMBER,
                                minimum=10,
                                maximum=5,
                            ),
                        )
                    ]
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError) as exc:
        validator.validate_contract(contract)

    assert "sensor.value" in str(exc.value)


def test_enum_matches_type_passes() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="status",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    enum=["A", "B"],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    validator.validate_contract(contract)


def test_enum_type_mismatch_string_in_number() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    enum=["A"],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError) as exc:
        validator.validate_contract(contract)

    assert "does not match type" in str(exc.value)


def test_enum_float_in_integer_field() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.INTEGER,
                    enum=[1.5],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_enum_bool_in_number_field() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    enum=[True],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_enum_null_type() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NULL,
                    enum=[None],
                ),
            )
        ]
    )

    validator = ContractValidationService()

    validator.validate_contract(contract)


def test_format_on_string_is_valid() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="id",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    format="uuid",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    validator.validate_contract(contract)


def test_format_on_number_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    format="uuid",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError) as exc:
        validator.validate_contract(contract)

    assert "only allowed for string" in str(exc.value)


def test_format_on_boolean_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="flag",
                type=PrimitiveType(
                    kind=PrimitiveKind.BOOLEAN,
                    format="uuid",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_format_on_null_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NULL,
                    format="uuid",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_pattern_on_string_is_valid() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="code",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    pattern="^[A-Z]{3}$",
                ),
            )
        ]
    )

    validator = ContractValidationService()
    validator.validate_contract(contract)


def test_pattern_on_number_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.NUMBER,
                    pattern=".*",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_pattern_on_boolean_raises() -> None:
    contract = make_contract(
        [
            FieldDefinition(
                name="flag",
                type=PrimitiveType(
                    kind=PrimitiveKind.BOOLEAN,
                    pattern="true|false",
                ),
            )
        ]
    )

    validator = ContractValidationService()

    with pytest.raises(ContractValidationError):
        validator.validate_contract(contract)


def test_valid_default_passes() -> None:
    contract = make_contract(
        [FieldDefinition(name="name", type=PrimitiveType(kind=PrimitiveKind.STRING, default="koekjes"))]
    )
    ContractValidationService().validate_contract(contract)


def test_default_type_mismatch_raises() -> None:
    contract = make_contract(
        [FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.STRING, default=1.0))]
    )
    with pytest.raises(ContractValidationError, match="default value"):
        ContractValidationService().validate_contract(contract)


def test_default_bool_in_number_raises() -> None:
    contract = make_contract(
        [FieldDefinition(name="value", type=PrimitiveType(kind=PrimitiveKind.NUMBER, default=True))]
    )
    with pytest.raises(ContractValidationError, match="default value"):
        ContractValidationService().validate_contract(contract)

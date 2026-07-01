from typing import Any

from contract_engine.domain.contract import Contract
from contract_engine.domain.errors import ContractValidationError
from contract_engine.domain.types import (
    UNSET,
    AnyOfType,
    ArrayType,
    FieldDefinition,
    FieldType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)


class ContractValidationService:
    def validate_contract(self, contract: Contract) -> None:
        for field in contract.fields:
            self._validate_field_definition(field, path=field.name)

    def _validate_field_definition(self, field: FieldDefinition, path: str) -> None:
        self._validate_field_type(field.type, path)

    def _validate_field_type(self, field_type: FieldType, path: str) -> None:
        if isinstance(field_type, PrimitiveType):
            self._validate_primitive(field_type, path)

        elif isinstance(field_type, ObjectType):
            for f in field_type.fields:
                self._validate_field_definition(f, f"{path}.{f.name}")

        elif isinstance(field_type, ArrayType):
            self._validate_field_type(field_type.items, f"{path}[*]")

            if (
                field_type.min_items is not None
                and field_type.max_items is not None
                and field_type.min_items > field_type.max_items
            ):
                raise ContractValidationError(
                    f"{path}: min_items ({field_type.min_items}) > max_items ({field_type.max_items})"
                )

        elif isinstance(field_type, OneOfType):
            if not field_type.options:
                raise ContractValidationError(f"{path}: oneOf has no options")

            for i, option in enumerate(field_type.options):
                self._validate_field_type(option, f"{path}.oneOf[{i}]")

        elif isinstance(field_type, AnyOfType):
            if not field_type.options:
                raise ContractValidationError(f"{path}: anyOf has no options")

            for i, option in enumerate(field_type.options):
                self._validate_field_type(option, f"{path}.anyOf[{i}]")

        else:
            # AnyType or unknown → OK
            pass

    def _validate_primitive(self, field_type: PrimitiveType, path: str) -> None:
        if (
            field_type.minimum is not None
            and field_type.maximum is not None
            and field_type.minimum > field_type.maximum
        ):
            raise ContractValidationError(f"{path}: minimum ({field_type.minimum}) > maximum ({field_type.maximum})")

        if (
            field_type.min_length is not None
            and field_type.max_length is not None
            and field_type.min_length > field_type.max_length
        ):
            raise ContractValidationError(
                f"{path}: min_length ({field_type.min_length}) > max_length ({field_type.max_length})"
            )

        if field_type.enum is not None:
            if len(field_type.enum) == 0:
                raise ContractValidationError(f"{path}: enum cannot be empty")

            for value in field_type.enum:
                if not self._value_matches_kind(value, field_type.kind):
                    raise ContractValidationError(f"{path}: enum value {value!r} does not match type {field_type.kind}")

        if field_type.default is not UNSET and not self._value_matches_kind(field_type.default, field_type.kind):
            raise ContractValidationError(
                f"{path}: default value {field_type.default!r} does not match type {field_type.kind}"
            )

        if field_type.format is not None and field_type.kind != PrimitiveKind.STRING:
            raise ContractValidationError(f"{path}: format '{field_type.format}' is only allowed for string type")

        if field_type.pattern is not None and field_type.kind != PrimitiveKind.STRING:
            raise ContractValidationError(f"{path}: pattern is only allowed for string type")

    def _value_matches_kind(self, value: Any, kind: PrimitiveKind) -> bool:
        if kind == PrimitiveKind.STRING:
            return isinstance(value, str)

        if kind == PrimitiveKind.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if kind == PrimitiveKind.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)

        if kind == PrimitiveKind.BOOLEAN:
            return isinstance(value, bool)

        if kind == PrimitiveKind.NULL:
            return value is None

        return True  # fallback, should not happen

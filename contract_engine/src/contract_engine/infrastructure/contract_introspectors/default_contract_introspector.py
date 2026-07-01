from typing import Any

from contract_engine.application.interfaces.contract_introspector import ContractIntrospector
from contract_engine.domain.contract import Contract
from contract_engine.domain.field_info import FieldInfo
from contract_engine.domain.types import (
    AnyType,
    ArrayType,
    FieldDefinition,
    ObjectType,
    OneOfType,
    PrimitiveType,
)


class DefaultContractIntrospector(ContractIntrospector):
    def inspect(self, contract: Contract) -> list[FieldInfo]:
        fields: list[FieldInfo] = []

        for field in contract.fields:
            self._walk(field, field.name, fields)

        unique = {}
        for f in fields:
            unique[f.path] = f

        return list(unique.values())

    def _walk(
        self,
        field: FieldDefinition,
        path: str,
        out: list[FieldInfo],
    ) -> None:
        field_type = field.type
        if isinstance(field_type, PrimitiveType):
            out.append(
                FieldInfo(
                    path=path,
                    type=field_type.kind.value,
                    required=field.required,
                    constraints=self._extract_constraints(field_type),
                )
            )
            return

        if isinstance(field_type, ObjectType):
            out.append(
                FieldInfo(
                    path=path,
                    type="object",
                    required=field.required,
                )
            )

            for child in field_type.fields:
                child_path = f"{path}.{child.name}"
                self._walk(child, child_path, out)

            return

        if isinstance(field_type, ArrayType):
            out.append(
                FieldInfo(
                    path=path,
                    type="array",
                    required=field.required,
                    constraints={
                        "min_items": field_type.min_items,
                        "max_items": field_type.max_items,
                    },
                )
            )

            # represent array element
            item_field = FieldDefinition(
                name="[0]",
                type=field_type.items,
                required=True,
            )

            self._walk(item_field, f"{path}[0]", out)

        if isinstance(field_type, OneOfType):
            out.append(
                FieldInfo(
                    path=path,
                    type="oneOf",
                    required=field.required,
                )
            )

            for option in field_type.options:
                option_field = FieldDefinition(
                    name=field.name,
                    type=option,
                    required=field.required,
                )
                self._walk(option_field, path, out)

            return

        if isinstance(field_type, AnyType):
            out.append(
                FieldInfo(
                    path=path,
                    type="any",
                    required=field.required,
                )
            )
            return

    def _extract_constraints(self, primitive: PrimitiveType) -> dict[str, Any]:
        constraints: dict[str, Any] = {}

        if primitive.minimum is not None:
            constraints["minimum"] = primitive.minimum

        if primitive.maximum is not None:
            constraints["maximum"] = primitive.maximum

        if primitive.min_length is not None:
            constraints["min_length"] = primitive.min_length

        if primitive.max_length is not None:
            constraints["max_length"] = primitive.max_length

        if primitive.pattern:
            constraints["pattern"] = primitive.pattern

        if primitive.enum:
            constraints["enum"] = primitive.enum

        if primitive.format:
            constraints["format"] = primitive.format

        return constraints

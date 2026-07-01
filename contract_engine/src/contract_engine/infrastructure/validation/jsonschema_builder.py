from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import AnyOfType, AnyType, ArrayType, FieldType, ObjectType, OneOfType, PrimitiveType

if TYPE_CHECKING:
    from contract_engine.domain.contract import Contract


class JsonSchemaBuilder:
    def build(self, contract: Contract) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {field.name: self._build_field_schema(field.type) for field in contract.fields},
            "required": [field.name for field in contract.fields if field.required],
            "additionalProperties": False,
        }

    def _build_field_schema(self, field_type: FieldType) -> dict[str, Any]:
        if isinstance(field_type, PrimitiveType):
            return self._build_primitive_schema(field_type)

        if isinstance(field_type, ObjectType):
            return self._build_object_schema(field_type)

        if isinstance(field_type, ArrayType):
            return self._build_array_schema(field_type)

        if isinstance(field_type, OneOfType):
            return self._build_oneof_schema(field_type)

        if isinstance(field_type, AnyOfType):
            return self._build_anyof_schema(field_type)

        if isinstance(field_type, AnyType):
            return self._build_any_schema()

        raise TypeError(f"Unsupported FieldType: {type(field_type)}")

    def _build_primitive_schema(self, field: PrimitiveType) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": field.kind,
        }

        if field.minimum is not None:
            schema["minimum"] = field.minimum

        if field.maximum is not None:
            schema["maximum"] = field.maximum

        if field.pattern is not None:
            schema["pattern"] = field.pattern

        if field.enum is not None:
            schema["enum"] = field.enum

        if field.min_length is not None:
            schema["minLength"] = field.min_length

        if field.max_length is not None:
            schema["maxLength"] = field.max_length

        if field.format is not None:
            schema["format"] = field.format

        return schema

    def _build_object_schema(self, obj: ObjectType) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {field.name: self._build_field_schema(field.type) for field in obj.fields},
            "required": [field.name for field in obj.fields if field.required],
            "additionalProperties": obj.additional_properties,
        }

    def _build_array_schema(self, arr: ArrayType) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": "array"}

        if arr.prefix_items:
            schema["items"] = [self._build_field_schema(p) for p in arr.prefix_items]
            schema["additionalItems"] = self._build_field_schema(arr.items) if arr.allow_additional_items else False
        else:
            schema["items"] = self._build_field_schema(arr.items)

        if arr.min_items is not None:
            schema["minItems"] = arr.min_items

        if arr.max_items is not None:
            schema["maxItems"] = arr.max_items

        return schema

    def _build_oneof_schema(self, field: OneOfType) -> dict[str, Any]:
        return {"oneOf": [self._build_field_schema(option) for option in field.options]}

    def _build_anyof_schema(self, field: AnyOfType) -> dict[str, Any]:
        return {"anyOf": [self._build_field_schema(option) for option in field.options]}

    def _build_any_schema(self) -> dict[str, Any]:
        return {}

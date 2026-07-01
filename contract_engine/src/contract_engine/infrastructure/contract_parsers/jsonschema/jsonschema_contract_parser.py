from collections.abc import Mapping
from pathlib import Path
from typing import Any

from contract_engine.application.interfaces.contract_parser import ContractParser
from contract_engine.domain.contract import Contract
from contract_engine.domain.types import (
    UNSET,
    AnyOfType,
    AnyType,
    ArrayType,
    FieldDefinition,
    FieldType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)
from contract_engine.infrastructure.contract_parsers.jsonschema.ref_resolver import RefResolver


class JsonSchemaContractParser(ContractParser):
    def parse(
        self,
        document: Mapping[str, Any],
        *,
        base_path: Path | None = None,
    ) -> Contract:

        self._resolver = RefResolver(document, base_path=base_path)

        while "$ref" in document:
            document = self._resolver.resolve(document)

        while "allOf" in document:
            document = self._merge_allof(document)

        if "oneOf" in document and "properties" not in document:
            root_type = self._parse_one_of(document)
            return Contract(
                name=document.get("title", "schema"),
                version="1.0",
                fields=[],
                root_type=root_type,
            )

        properties = document.get("properties", {})
        required = set(document.get("required", []))

        fields = [self._parse_field(name, schema, required=name in required) for name, schema in properties.items()]

        return Contract(
            name=document.get("title", "schema"),
            version="1.0",
            fields=fields,
        )

    def _parse_field(
        self,
        name: str,
        schema: Mapping[str, Any],
        *,
        required: bool,
    ) -> FieldDefinition:

        field_type = self._parse_type(schema)

        return FieldDefinition(
            name=name,
            type=field_type,
            required=required,
        )

    def _parse_type(self, schema: Mapping[str, Any]) -> FieldType:
        seen: set[str] = set()

        while "$ref" in schema:
            ref = schema["$ref"]

            if ref in seen:
                raise ValueError(f"Circular $ref detected: {ref}")

            seen.add(ref)
            schema = self._resolver.resolve(schema)

        while "allOf" in schema:
            schema = self._merge_allof(schema)

        type_name = schema.get("type")

        if isinstance(type_name, list):
            return self._parse_type_union(schema, type_name)

        if type_name == "object":
            return self._parse_object(schema)

        if type_name == "array":
            return self._parse_array(schema)

        if type_name is not None:
            return self._parse_primitive(schema)

        if "oneOf" in schema:
            return self._parse_one_of(schema)

        if "anyOf" in schema:
            return self._parse_any_of(schema)

        return AnyType()

    def _parse_type_union(
        self,
        schema: Mapping[str, Any],
        types: list[Any],
    ) -> FieldType:
        if not types:
            raise ValueError("type list must not be empty")

        _NULL_STRIP = frozenset(
            {
                "format",
                "pattern",
                "minLength",
                "maxLength",
                "minimum",
                "maximum",
                "exclusiveMinimum",
                "exclusiveMaximum",
                "multipleOf",
                "default",
            }
        )

        options = []

        for t in types:
            if not isinstance(t, str):
                raise TypeError("All entries in type list must be strings")

            strip = _NULL_STRIP if t == "null" else {"default"}
            option_schema = {k: v for k, v in schema.items() if k not in strip}
            option_schema["type"] = t

            options.append(self._parse_type(option_schema))

        return OneOfType(options=options, default=schema.get("default", UNSET))

    def _parse_object(self, schema: Mapping[str, Any]) -> ObjectType:

        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        fields = [
            self._parse_field(name, subschema, required=name in required) for name, subschema in properties.items()
        ]

        ap = schema.get("additionalProperties", True)

        if isinstance(ap, bool):
            additional_properties: bool | FieldType = ap
        elif isinstance(ap, dict):
            additional_properties = self._parse_type(ap)
        else:
            raise TypeError(f"additionalProperties must be a bool or a schema object, got {type(ap).__name__}")

        return ObjectType(
            fields=fields,
            additional_properties=additional_properties,
        )

    def _parse_array(self, schema: Mapping[str, Any]) -> ArrayType:
        raw_items = schema.get("items", {})
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")

        if isinstance(raw_items, list):
            prefix_items = [self._parse_type(s) for s in raw_items]

            additional = schema.get("additionalItems")
            if isinstance(additional, dict):
                items = self._parse_type(additional)
                allow_additional = True
            elif additional is False:
                items = AnyType()
                allow_additional = False
            else:
                items = AnyType()
                allow_additional = True

            return ArrayType(
                prefix_items=prefix_items,
                items=items,
                allow_additional_items=allow_additional,
                min_items=min_items,
                max_items=max_items,
            )

        return ArrayType(
            items=self._parse_type(raw_items),
            min_items=min_items,
            max_items=max_items,
        )

    def _parse_primitive(self, schema: Mapping[str, Any]) -> PrimitiveType:

        type_name = schema.get("type")

        if not isinstance(type_name, str):
            raise TypeError("Schema field 'type' must be a string or an array")

        kind_map = {
            "integer": PrimitiveKind.INTEGER,
            "number": PrimitiveKind.NUMBER,
            "string": PrimitiveKind.STRING,
            "boolean": PrimitiveKind.BOOLEAN,
            "null": PrimitiveKind.NULL,
        }

        if type_name not in kind_map:
            raise ValueError(f"Unsupported primitive type: {type_name}")

        kind = kind_map[type_name]

        enum = schema.get("enum")
        const = schema.get("const")

        if const is not None:
            enum = [const]

        return PrimitiveType(
            kind=kind,
            minimum=schema.get("minimum"),
            maximum=schema.get("maximum"),
            min_length=schema.get("minLength"),
            max_length=schema.get("maxLength"),
            pattern=schema.get("pattern"),
            enum=enum,
            format=schema.get("format"),
            default=schema.get("default", UNSET),
        )

    def _parse_one_of(self, schema: Mapping[str, Any]) -> FieldType:
        options = schema.get("oneOf")

        if not isinstance(options, list):
            raise TypeError("oneOf must be a list")

        if not options:
            raise ValueError("oneOf must contain at least one schema")

        parsed_options = [self._parse_type(option) for option in options]

        return OneOfType(options=parsed_options)

    def _parse_any_of(self, schema: Mapping[str, Any]) -> FieldType:
        options = schema.get("anyOf")

        if not isinstance(options, list):
            raise TypeError("anyOf must be a list")

        if not options:
            raise ValueError("anyOf must contain at least one schema")

        parsed_options = [self._parse_type(option) for option in options]

        return AnyOfType(options=parsed_options)

    def _merge_allof(self, schema: Mapping[str, Any]) -> Mapping[str, Any]:

        allof = schema.get("allOf")

        if not isinstance(allof, list):
            raise TypeError("allOf must be a list")

        merged: dict[str, Any] = {}

        for part in allof:
            if not isinstance(part, Mapping):
                raise TypeError("allOf elements must be objects")

            while "$ref" in part:
                part = self._resolver.resolve(part)

            merged = self._merge_schema_dicts(merged, part)

        return merged

    def _merge_schema_dicts(
        self,
        left: Mapping[str, Any],
        right: Mapping[str, Any],
    ) -> dict[str, Any]:

        merged = dict(left)

        for key, value in right.items():
            if key not in merged:
                merged[key] = value
                continue

            if key == "properties":
                merged_props = dict(merged[key])

                for prop_name, prop_value in value.items():
                    if prop_name in merged_props:
                        if isinstance(merged_props[prop_name], dict) and isinstance(prop_value, dict):
                            merged_props[prop_name] = self._merge_schema_dicts(
                                merged_props[prop_name],
                                prop_value,
                            )
                        else:
                            merged_props[prop_name] = prop_value
                    else:
                        merged_props[prop_name] = prop_value

                merged[key] = merged_props

            elif key == "required":
                merged[key] = list(set(merged[key]) | set(value))

            elif key == "enum":
                merged[key] = [v for v in merged[key] if v in value]

            elif key in {"minimum", "minLength"}:
                merged[key] = max(merged[key], value)

            elif key in {"maximum", "maxLength"}:
                merged[key] = min(merged[key], value)

            elif key == "type":
                if merged[key] != value:
                    raise ValueError("conflicting type constraints in allOf")

            else:
                merged[key] = value

        self._validate_constraints(merged)

        return merged

    def _validate_constraints(self, schema: Mapping[str, Any]) -> None:

        minimum = schema.get("minimum")
        maximum = schema.get("maximum")

        if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)) and minimum > maximum:
            raise ValueError("conflicting numeric constraints: minimum > maximum")

        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")

        if isinstance(min_length, int) and isinstance(max_length, int) and min_length > max_length:
            raise ValueError("conflicting string length constraints: minLength > maxLength")

        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")

        if isinstance(min_items, int) and isinstance(max_items, int) and min_items > max_items:
            raise ValueError("conflicting array constraints: minItems > maxItems")

        enum = schema.get("enum")

        if isinstance(enum, list) and len(enum) == 0:
            raise ValueError("conflicting enum constraints: empty enum")

        const = schema.get("const")

        if const is not None and isinstance(enum, list) and const not in enum:
            raise ValueError("const conflicts with enum")

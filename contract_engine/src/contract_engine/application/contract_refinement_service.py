from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import (
    ArrayType,
    FieldDefinition,
    FieldType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)

if TYPE_CHECKING:
    from datetime import date, datetime, timedelta

    from contract_engine.application.contract_refinement_types import Constraint, Refinements
    from contract_engine.domain.contract import Contract

SUPPORTED_CONSTRAINTS = {
    "type",
    "const",
    "minimum",
    "maximum",
    "min_length",
    "max_length",
    "enum",
    "format",
    "pattern",
    "one_of_filter",
    "required",
    "min_items",
    "max_items",
    "minimum_date_time",
    "maximum_date_time",
    "minimum_date",
    "maximum_date",
    "minimum_duration",
    "maximum_duration",
}


class ContractRefinementService:
    def refine(
        self,
        contract: Contract,
        refinements: Refinements,
    ) -> Contract:
        """
        Apply refinements to a contract and return a new refined contract.
        """
        refined = copy.deepcopy(contract)

        for path, constraint in refinements.items():
            self._apply_refinement(refined, path, constraint)

        return refined

    def _apply_refinement(
        self,
        contract: Contract,
        path: str,
        constraint: Constraint,
    ) -> None:
        if path == "":
            if contract.root_type is None:
                raise ValueError("Refinement path '' targets root type, but contract has no root type")
            if "required" in constraint:
                raise ValueError("required constraint is not supported at root level")
            self._apply_constraint(contract.root_type, constraint, path)
            return

        parts = self._parse_path(path)

        for field in contract.fields:
            if field.name == parts[0]:
                self._apply_to_field(field, parts[1:], constraint, full_path=path)
                return

        raise ValueError(f"Refinement path not found: {path}")

    def _apply_to_field(
        self,
        field: FieldDefinition,
        parts: list[str],
        constraint: Constraint,
        full_path: str,
    ) -> None:
        if not parts:
            if "required" in constraint:
                field.required = constraint["required"]
            self._apply_constraint(field.type, constraint, full_path)
            return

        head = parts[0]

        if isinstance(field.type, ObjectType):
            for sub in field.type.fields:
                if sub.name == head:
                    self._apply_to_field(sub, parts[1:], constraint, full_path)
                    return
            if isinstance(field.type.additional_properties, FieldType):
                promoted = FieldDefinition(
                    name=head,
                    type=copy.deepcopy(field.type.additional_properties),
                    required=False,
                )
                field.type.fields.append(promoted)
                self._apply_to_field(promoted, parts[1:], constraint, full_path)
                return
            if field.type.additional_properties is True:
                if "type" not in constraint:
                    raise ValueError(
                        f"{full_path}: cannot refine additional property '{head}' without a 'type' constraint"
                    )
                type_val = constraint["type"]
                if not isinstance(type_val, str):
                    raise ValueError(
                        f"{full_path}: type constraint for additional property '{head}' must be a string, not a list"
                    )
                try:
                    kind = PrimitiveKind(type_val)
                except ValueError:
                    raise ValueError(
                        f"{full_path}: unsupported type '{type_val}' for additional property '{head}'"
                    ) from None
                promoted = FieldDefinition(name=head, type=PrimitiveType(kind=kind), required=False)
                field.type.fields.append(promoted)
                self._apply_to_field(promoted, parts[1:], constraint, full_path)
                return
            raise ValueError(f"{full_path}: unknown path '{head}'")

        if isinstance(field.type, ArrayType):
            if head != "*":
                raise ValueError(f"{full_path}: expected [*] for array")

            dummy = FieldDefinition(name="*", type=field.type.items)
            self._apply_to_field(dummy, parts[1:], constraint, full_path)
            field.type.items = dummy.type
            return

        if isinstance(field.type, OneOfType):
            matched = False
            for option in field.type.options:
                if isinstance(option, ObjectType):
                    for sub in option.fields:
                        if sub.name == head:
                            self._apply_to_field(sub, parts[1:], constraint, full_path)
                            matched = True
                            break
            if not matched:
                raise ValueError(f"{full_path}: path '{head}' not found in any oneOf option")
            return

        raise ValueError(f"{full_path}: invalid path")

    def _parse_path(self, path: str) -> list[str]:
        parts: list[str] = []

        for part in path.split("."):
            if "[*]" in part:
                name = part.replace("[*]", "")
                if name:
                    parts.append(name)
                parts.append("*")
            else:
                parts.append(part)

        return parts

    def _apply_constraint(
        self,
        field_type: FieldType,
        constraint: Constraint,
        path: str,
    ) -> None:
        effective_type: FieldType = field_type

        if "type" in constraint and isinstance(field_type, OneOfType):
            effective_type = self._apply_type_filter(field_type, constraint["type"], path)

        if "one_of_filter" in constraint:
            self._apply_one_of_filter(effective_type, constraint["one_of_filter"], path)

        if "const" in constraint:
            self._apply_const(effective_type, constraint["const"], path)

        if "minimum" in constraint:
            self._apply_minimum(effective_type, constraint["minimum"], path)

        if "maximum" in constraint:
            self._apply_maximum(effective_type, constraint["maximum"], path)

        if "min_length" in constraint:
            self._apply_min_length(effective_type, constraint["min_length"], path)

        if "max_length" in constraint:
            self._apply_max_length(effective_type, constraint["max_length"], path)

        if "enum" in constraint:
            self._apply_enum(effective_type, constraint["enum"], path)

        if "format" in constraint:
            self._apply_format(effective_type, constraint["format"], path)

        if "pattern" in constraint:
            self._apply_pattern(effective_type, constraint["pattern"], path)

        if "min_items" in constraint:
            self._apply_min_items(effective_type, constraint["min_items"], path)

        if "max_items" in constraint:
            self._apply_max_items(effective_type, constraint["max_items"], path)

        if "minimum_date_time" in constraint:
            self._apply_minimum_date_time(effective_type, constraint["minimum_date_time"], path)

        if "maximum_date_time" in constraint:
            self._apply_maximum_date_time(effective_type, constraint["maximum_date_time"], path)

        if "minimum_date" in constraint:
            self._apply_minimum_date(effective_type, constraint["minimum_date"], path)

        if "maximum_date" in constraint:
            self._apply_maximum_date(effective_type, constraint["maximum_date"], path)

        if "minimum_duration" in constraint:
            self._apply_minimum_duration(effective_type, constraint["minimum_duration"], path)

        if "maximum_duration" in constraint:
            self._apply_maximum_duration(effective_type, constraint["maximum_duration"], path)

        for key in constraint:
            if key not in SUPPORTED_CONSTRAINTS:
                raise ValueError(f"{path}: unsupported constraint '{key}'")

    def _apply_one_of_filter(
        self,
        field_type: FieldType,
        filter_dict: dict[str, Any],
        path: str,
    ) -> None:
        if not isinstance(field_type, OneOfType):
            raise TypeError(f"{path}: one_of_filter only supported for oneOf types")

        surviving = [option for option in field_type.options if self._option_matches(option, filter_dict)]

        if not surviving:
            raise ValueError(f"{path}: one_of_filter matched no options for {filter_dict}")

        field_type.options = surviving

    def _apply_type_filter(self, field_type: OneOfType, type_val: str | list[str], path: str) -> FieldType:
        types = [type_val] if isinstance(type_val, str) else type_val

        kinds: list[PrimitiveKind] = []
        for t in types:
            try:
                kinds.append(PrimitiveKind(t))
            except ValueError:
                raise ValueError(f"{path}: unknown type '{t}' for type filter") from None

        surviving: list[FieldType] = [
            opt for opt in field_type.options if isinstance(opt, PrimitiveType) and opt.kind in kinds
        ]

        if not surviving:
            raise ValueError(f"{path}: type filter {type_val!r} matched no oneOf options")

        field_type.options = surviving
        return surviving[0] if len(surviving) == 1 else field_type

    def _option_matches(self, option: FieldType, filter_dict: dict[str, Any]) -> bool:
        if not isinstance(option, ObjectType):
            return False

        field_map = {field.name: field.type for field in option.fields}

        for key, value in filter_dict.items():
            if key not in field_map:
                return False
            field_type = field_map[key]
            if not isinstance(field_type, PrimitiveType):
                return False
            if field_type.enum is not None and value not in field_type.enum:
                return False

        return True

    def _apply_const(
        self,
        field_type: FieldType,
        value: Any,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: const only supported for primitive types")

        field_type.enum = [value]

    def _apply_minimum(
        self,
        field_type: FieldType,
        value: float,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: minimum only supported for primitive types")

        field_type.minimum = value

    def _apply_maximum(
        self,
        field_type: FieldType,
        value: float,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: maximum only supported for primitive types")

        field_type.maximum = value

    def _apply_min_length(
        self,
        field_type: FieldType,
        value: int,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: min_length only supported for primitive types")

        field_type.min_length = value

    def _apply_max_length(
        self,
        field_type: FieldType,
        value: int,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: max_length only supported for primitive types")

        field_type.max_length = value

    def _apply_enum(
        self,
        field_type: FieldType,
        value: list[Any],
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: enum only supported for primitive types")

        field_type.enum = value

    def _apply_format(
        self,
        field_type: FieldType,
        value: str,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: format only supported for primitive types")

        field_type.format = value

    def _apply_pattern(
        self,
        field_type: FieldType,
        value: str,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: pattern only supported for primitive types")

        field_type.pattern = value

    def _apply_min_items(
        self,
        field_type: FieldType,
        value: int,
        path: str,
    ) -> None:
        if not isinstance(field_type, ArrayType):
            raise TypeError(f"{path}: min_items only supported for array types")

        field_type.min_items = value

    def _apply_max_items(
        self,
        field_type: FieldType,
        value: int,
        path: str,
    ) -> None:
        if not isinstance(field_type, ArrayType):
            raise TypeError(f"{path}: max_items only supported for array types")

        field_type.max_items = value

    def _apply_minimum_date_time(
        self,
        field_type: FieldType,
        value: datetime,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: minimum_date_time only supported for primitive types")

        field_type.minimum_date_time = value

    def _apply_maximum_date_time(
        self,
        field_type: FieldType,
        value: datetime,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: maximum_date_time only supported for primitive types")

        field_type.maximum_date_time = value

    def _apply_minimum_date(
        self,
        field_type: FieldType,
        value: date,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: minimum_date only supported for primitive types")

        field_type.minimum_date = value

    def _apply_maximum_date(
        self,
        field_type: FieldType,
        value: date,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: maximum_date only supported for primitive types")

        field_type.maximum_date = value

    def _apply_minimum_duration(
        self,
        field_type: FieldType,
        value: timedelta,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: minimum_duration only supported for primitive types")

        field_type.minimum_duration = value

    def _apply_maximum_duration(
        self,
        field_type: FieldType,
        value: timedelta,
        path: str,
    ) -> None:
        if not isinstance(field_type, PrimitiveType):
            raise TypeError(f"{path}: maximum_duration only supported for primitive types")

        field_type.maximum_duration = value

from contract_engine.domain.types import FieldType, PrimitiveKind, PrimitiveType


def filter_ambiguous_numeric_union(options: list[FieldType]) -> list[FieldType]:
    has_integer = any(isinstance(opt, PrimitiveType) and opt.kind == PrimitiveKind.INTEGER for opt in options)
    has_number = any(isinstance(opt, PrimitiveType) and opt.kind == PrimitiveKind.NUMBER for opt in options)

    # If both exist → remove INTEGER to avoid overlap
    if has_integer and has_number:
        return [opt for opt in options if not (isinstance(opt, PrimitiveType) and opt.kind == PrimitiveKind.INTEGER)]

    return options

from contract_engine.domain.types import FieldDefinition, PrimitiveKind, PrimitiveType


def test_primitive_type_creation() -> None:
    field = FieldDefinition(
        name="temperature",
        type=PrimitiveType(kind=PrimitiveKind.NUMBER, minimum=0, maximum=100),
    )

    assert field.name == "temperature"
    assert isinstance(field.type, PrimitiveType)
    assert field.type.minimum == 0
    assert field.type.maximum == 100

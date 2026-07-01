from contract_engine.application.generator_service import GeneratorService
from contract_engine.domain.contract import Contract
from contract_engine.domain.types import ArrayType, FieldDefinition, ObjectType, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.generators.deterministic_generator import DeterministicGenerator
from contract_engine.infrastructure.generators.generation_mode import GenerationMode


def test_generator_returns_seed() -> None:
    seed = 1234
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER),
            )
        ],
    )

    generator = GeneratorService(generator=DeterministicGenerator())
    instance = generator.generate(contract, seed=seed)

    assert instance.seed.value == seed


def test_generator_respects_bounds() -> None:
    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="temperature",
                type=PrimitiveType(kind=PrimitiveKind.NUMBER, minimum=0, maximum=100),
            )
        ],
    )

    generator = GeneratorService(generator=DeterministicGenerator(), mode=GenerationMode.FUZZ)
    instance = generator.generate(contract)

    assert 0 <= instance.data["temperature"] <= 100


def test_seed_reproducibility() -> None:
    generator = GeneratorService(generator=DeterministicGenerator())

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="value",
                type=PrimitiveType(kind=PrimitiveKind.INTEGER, minimum=0, maximum=100),
            )
        ],
    )

    a = generator.generate(contract, seed=123)
    b = generator.generate(contract, seed=123)

    assert a == b


def test_nested_object_generation() -> None:
    contract = Contract(
        name="nested",
        version="1.0",
        fields=[
            FieldDefinition(
                name="device",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="temperature",
                            type=PrimitiveType(
                                kind=PrimitiveKind.NUMBER,
                                minimum=0,
                                maximum=100,
                            ),
                        ),
                        FieldDefinition(
                            name="active",
                            type=PrimitiveType(kind=PrimitiveKind.BOOLEAN),
                        ),
                    ]
                ),
            )
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=1)

    assert "device" in result.data
    assert isinstance(result.data["device"], dict)

    device = result.data["device"]

    assert 0 <= device["temperature"] <= 100
    assert isinstance(device["active"], bool)


def test_array_generation() -> None:
    contract = Contract(
        name="array",
        version="1.0",
        fields=[
            FieldDefinition(
                name="readings",
                type=ArrayType(
                    items=PrimitiveType(
                        kind=PrimitiveKind.INTEGER,
                        minimum=0,
                        maximum=10,
                    ),
                    min_items=2,
                    max_items=5,
                ),
            )
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=2)

    readings = result.data["readings"]

    assert isinstance(readings, list)
    assert 2 <= len(readings) <= 5

    for value in readings:
        assert 0 <= value <= 10


def test_enum_generation() -> None:
    contract = Contract(
        name="enum",
        version="1.0",
        fields=[
            FieldDefinition(
                name="status",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    enum=["ON", "OFF", "UNKNOWN"],
                ),
            )
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=3)

    assert result.data["status"] in {"ON", "OFF", "UNKNOWN"}


def test_optional_field_generation() -> None:
    contract = Contract(
        name="optional",
        version="1.0",
        fields=[
            FieldDefinition(
                name="mandatory",
                type=PrimitiveType(kind=PrimitiveKind.INTEGER),
                required=True,
            ),
            FieldDefinition(
                name="optional",
                type=PrimitiveType(kind=PrimitiveKind.INTEGER),
                required=False,
            ),
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=4)

    assert "mandatory" in result.data


def test_deep_nested_structure() -> None:
    contract = Contract(
        name="deep",
        version="1.0",
        fields=[
            FieldDefinition(
                name="outer",
                type=ObjectType(
                    fields=[
                        FieldDefinition(
                            name="inner",
                            type=ObjectType(
                                fields=[
                                    FieldDefinition(
                                        name="value",
                                        type=PrimitiveType(
                                            kind=PrimitiveKind.INTEGER,
                                            minimum=10,
                                            maximum=20,
                                        ),
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            )
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=5)

    assert 10 <= result.data["outer"]["inner"]["value"] <= 20


def test_string_length_bounds() -> None:
    contract = Contract(
        name="string_length",
        version="1.0",
        fields=[
            FieldDefinition(
                name="name",
                type=PrimitiveType(
                    kind=PrimitiveKind.STRING,
                    min_length=5,
                    max_length=10,
                ),
            )
        ],
    )

    generator = GeneratorService(DeterministicGenerator())

    result = generator.generate(contract, seed=1)

    value = result.data["name"]

    assert 5 <= len(value) <= 10

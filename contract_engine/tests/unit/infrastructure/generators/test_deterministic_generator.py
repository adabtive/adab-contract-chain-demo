import random

from contract_engine.domain.types import (
    AnyOfType,
    ArrayType,
    FieldDefinition,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)
from contract_engine.infrastructure.generators.deterministic_generator import MAX_DEPTH, DeterministicGenerator
from contract_engine.infrastructure.generators.generation_mode import GenerationMode


def test_edge_biased_candidates_include_boundaries() -> None:
    gen = DeterministicGenerator()

    candidates = gen.edge_biased_int_candidates(10, 20)

    assert 10 in candidates
    assert 20 in candidates
    assert 15 in candidates  # midpoint


def tes_tedge_biased_int_returns_valid_value() -> None:
    gen = DeterministicGenerator()
    rng = random.Random(1)

    value = gen.edge_biased_int(10, 20, rng)

    assert 10 <= value <= 20


def test_edge_biased_float_candidates_include_boundaries() -> None:
    gen = DeterministicGenerator()
    rng = random.Random(1)

    candidates = gen.edge_biased_float_candidates(10.0, 20.0, rng)

    assert 10.0 in candidates
    assert 20.0 in candidates
    assert 15.0 in candidates  # midpoint


def test_edge_biased_float_candidates_include_zero_when_in_range() -> None:
    gen = DeterministicGenerator()
    rng = random.Random(1)

    candidates = gen.edge_biased_float_candidates(-10.0, 20.0, rng)

    assert 0.0 in candidates


def test_edge_biased_float_candidates_exclude_zero_when_outside_range() -> None:
    gen = DeterministicGenerator()
    rng = random.Random(1)

    candidates = gen.edge_biased_float_candidates(10.0, 20.0, rng)

    assert 0.0 not in candidates


def test_edge_biased_float_returns_valid_value() -> None:
    gen = DeterministicGenerator()
    rng = random.Random(1)

    value = gen.edge_biased_float(10.0, 20.0, rng)

    assert 10.0 <= value <= 20.0


def test_depth_limit_stops_object_expansion() -> None:
    gen = DeterministicGenerator()

    value = gen.generate_field(
        ObjectType(fields=[]),
        random.Random(1),
        GenerationMode.FUZZ,
        depth=MAX_DEPTH,
    )

    assert value == {}


def test_depth_limit_stops_array_expansion() -> None:
    gen = DeterministicGenerator()

    value = gen.generate_field(
        ArrayType(items=PrimitiveType(kind=PrimitiveKind.BOOLEAN)),
        random.Random(1),
        GenerationMode.FUZZ,
        depth=MAX_DEPTH,
    )

    assert value == []


def test_oneof_returns_valid_option() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
        ]
    )

    value = gen.generate_field(
        field,
        random.Random(1),
        GenerationMode.FUZZ,
        depth=0,
    )

    assert isinstance(value, (str, int))


def test_oneof_is_deterministic_for_same_seed() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
        ]
    )

    rng1 = random.Random(42)
    rng2 = random.Random(42)

    value1 = gen.generate_field(field, rng1, GenerationMode.FUZZ, depth=0)
    value2 = gen.generate_field(field, rng2, GenerationMode.FUZZ, depth=0)

    assert value1 == value2


def test_oneof_varies_across_seeds() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
        ]
    )

    value1 = gen.generate_field(field, random.Random(1), GenerationMode.FUZZ, depth=0)
    value2 = gen.generate_field(field, random.Random(2), GenerationMode.FUZZ, depth=0)

    # Not guaranteed always different, but very likely
    assert value1 != value2 or not isinstance(value1, type(value2))


def test_oneof_with_object_option() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            ObjectType(
                fields=[
                    FieldDefinition(
                        name="x",
                        type=PrimitiveType(kind=PrimitiveKind.INTEGER),
                        required=True,
                    )
                ]
            ),
            PrimitiveType(kind=PrimitiveKind.STRING),
        ]
    )

    value = gen.generate_field(
        field,
        random.Random(1),
        GenerationMode.FUZZ,
        depth=0,
    )

    assert isinstance(value, (dict, str))

    if isinstance(value, dict):
        assert "x" in value
        assert isinstance(value["x"], int)


def test_oneof_respects_depth_limit_for_object() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            ObjectType(
                fields=[
                    FieldDefinition(
                        name="x",
                        type=PrimitiveType(kind=PrimitiveKind.INTEGER),
                        required=True,
                    )
                ]
            )
        ]
    )

    value = gen.generate_field(
        field,
        random.Random(1),
        GenerationMode.FUZZ,
        depth=MAX_DEPTH,
    )

    # Should stop expanding object
    assert value == {}


def test_type_union_generates_valid_values() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.NULL),
        ]
    )

    value = gen.generate_field(
        field,
        random.Random(1),
        GenerationMode.FUZZ,
        depth=0,
    )

    assert value is None or isinstance(value, str)


def test_type_union_is_deterministic() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.NULL),
        ]
    )

    rng1 = random.Random(123)
    rng2 = random.Random(123)

    value1 = gen.generate_field(field, rng1, GenerationMode.FUZZ, depth=0)
    value2 = gen.generate_field(field, rng2, GenerationMode.FUZZ, depth=0)

    assert value1 == value2


def test_oneof_with_all_json_types_including_null() -> None:
    gen = DeterministicGenerator()

    field = OneOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
            PrimitiveType(kind=PrimitiveKind.NUMBER),
            PrimitiveType(kind=PrimitiveKind.BOOLEAN),
            PrimitiveType(kind=PrimitiveKind.NULL),
        ]
    )

    value = gen.generate_field(
        field,
        random.Random(1),
        GenerationMode.FUZZ,
        depth=0,
    )

    assert value is None or isinstance(value, (str, int, float, bool))


def test_tuple_array_generates_prefix_items_in_order() -> None:
    gen = DeterministicGenerator()

    field = ArrayType(
        prefix_items=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
            PrimitiveType(kind=PrimitiveKind.BOOLEAN),
        ],
        min_items=3,
        max_items=3,
    )

    result = gen.generate_field(field, random.Random(1), GenerationMode.FUZZ, depth=0)

    assert len(result) == 3
    assert isinstance(result[0], str)
    assert isinstance(result[1], int)
    assert isinstance(result[2], bool)


def test_tuple_array_no_extra_items_when_not_allowed() -> None:
    gen = DeterministicGenerator()

    field = ArrayType(
        prefix_items=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.STRING),
        ],
        allow_additional_items=False,
        min_items=2,
        max_items=2,
    )

    result = gen.generate_field(field, random.Random(1), GenerationMode.FUZZ, depth=0)

    assert len(result) == 2


def test_tuple_array_appends_additional_items_when_allowed() -> None:
    gen = DeterministicGenerator()

    field = ArrayType(
        prefix_items=[
            PrimitiveType(kind=PrimitiveKind.STRING),
        ],
        items=PrimitiveType(kind=PrimitiveKind.INTEGER),
        allow_additional_items=True,
        min_items=3,
        max_items=3,
    )

    result = gen.generate_field(field, random.Random(1), GenerationMode.FUZZ, depth=0)

    assert len(result) == 3
    assert isinstance(result[0], str)
    assert isinstance(result[1], int)
    assert isinstance(result[2], int)


def test_anyof_generates_one_valid_option() -> None:
    gen = DeterministicGenerator()

    field = AnyOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
        ]
    )

    value = gen.generate_field(field, random.Random(1), GenerationMode.FUZZ, depth=0)

    assert isinstance(value, (str, int))


def test_anyof_nullable_string_generates_string_or_none() -> None:
    gen = DeterministicGenerator()

    field = AnyOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING, format="date-time"),
            PrimitiveType(kind=PrimitiveKind.NULL),
        ]
    )

    results = {type(gen.generate_field(field, random.Random(seed), GenerationMode.FUZZ, depth=0)) for seed in range(20)}

    assert str in results
    assert type(None) in results


def test_anyof_is_deterministic_for_same_seed() -> None:
    gen = DeterministicGenerator()

    field = AnyOfType(
        options=[
            PrimitiveType(kind=PrimitiveKind.STRING),
            PrimitiveType(kind=PrimitiveKind.INTEGER),
        ]
    )

    value1 = gen.generate_field(field, random.Random(42), GenerationMode.FUZZ, depth=0)
    value2 = gen.generate_field(field, random.Random(42), GenerationMode.FUZZ, depth=0)

    assert value1 == value2


def test_primitive_default_used_in_realistic_mode() -> None:
    gen = DeterministicGenerator()
    field = PrimitiveType(kind=PrimitiveKind.STRING, default="koekjes")
    value = gen.generate_primitive(field, random.Random(1), GenerationMode.REALISTIC)
    assert value == "koekjes"


def test_primitive_default_ignored_in_fuzz_mode() -> None:
    gen = DeterministicGenerator()
    field = PrimitiveType(kind=PrimitiveKind.STRING, default="koekjes")
    value = gen.generate_primitive(field, random.Random(1), GenerationMode.FUZZ)
    assert value != "koekjes"


def test_primitive_no_default_generates_normally() -> None:
    gen = DeterministicGenerator()
    field = PrimitiveType(kind=PrimitiveKind.INTEGER, minimum=5, maximum=5)
    value = gen.generate_primitive(field, random.Random(1), GenerationMode.REALISTIC)
    assert value == 5


def test_one_of_default_used_in_realistic_mode() -> None:
    gen = DeterministicGenerator()
    field = OneOfType(
        options=[PrimitiveType(kind=PrimitiveKind.STRING), PrimitiveType(kind=PrimitiveKind.NULL)],
        default="koekjes",
    )
    value = gen.generate_field(field, random.Random(1), GenerationMode.REALISTIC, depth=0)
    assert value == "koekjes"


def test_one_of_default_ignored_in_fuzz_mode() -> None:
    gen = DeterministicGenerator()
    field = OneOfType(
        options=[PrimitiveType(kind=PrimitiveKind.STRING), PrimitiveType(kind=PrimitiveKind.NULL)],
        default="koekjes",
    )
    for seed in range(10):
        value = gen.generate_field(field, random.Random(seed), GenerationMode.FUZZ, depth=0)
        assert value != "koekjes"

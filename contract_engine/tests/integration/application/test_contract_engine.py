import pytest

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from contract_engine.domain.errors import ContractValidationError
from contract_engine.infrastructure.generators.generation_mode import GenerationMode


def test_generate_instance() -> None:
    schema = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
            }
        },
        "required": ["temperature"],
    }

    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="happyflow")

    assert result.data["temperature"] >= 0
    assert result.data["temperature"] <= 100

    assert result.seed.label == "happyflow"


def test_generation_is_deterministic() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
    }

    engine = create_default_contract_engine()
    a = engine.generate_instance(schema, seed="testseed")
    b = engine.generate_instance(schema, seed="testseed")

    assert a.data == b.data


def test_generate_instances() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
    }

    engine = create_default_contract_engine()
    results = engine.generate_instances(schema, count=3, seed="batch")

    assert len(results) == 3

    assert results[0].seed.label == "batch_0"
    assert results[1].seed.label == "batch_1"
    assert results[2].seed.label == "batch_2"


def test_generate_instance_with_override() -> None:
    schema = {
        "type": "object",
        "properties": {"temperature": {"type": "number"}},
        "required": ["temperature"],
    }

    engine = create_default_contract_engine()
    result = engine.generate_instance(
        schema,
        overrides={"temperature": -999},
    )

    assert result.data["temperature"] == -999


def test_inspect_contract() -> None:
    schema = {
        "type": "object",
        "properties": {"temperature": {"type": "number"}},
    }

    engine = create_default_contract_engine()
    fields = engine.inspect_contract(schema)

    paths = [f.path for f in fields]

    assert "temperature" in paths


def test_generate_validate_roundtrip() -> None:
    schema = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
            },
            "device_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 10,
            },
        },
        "required": ["temperature", "device_id"],
    }

    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="roundtrip")

    validation = engine.validate_instance(schema, result.data)

    assert validation.valid


ROOT_ONE_OF_SCHEMA = {
    "oneOf": [
        {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "const": "sensor"},
                "value": {"type": "number"},
            },
            "required": ["kind", "value"],
        },
        {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "const": "alert"},
                "message": {"type": "string"},
            },
            "required": ["kind", "message"],
        },
    ]
}


def test_root_one_of_branch_filter() -> None:
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        ROOT_ONE_OF_SCHEMA,
        refinements={"": {"one_of_filter": {"kind": "sensor"}}},
        seed="test",
    )

    assert result.data["kind"] == "sensor"
    assert "value" in result.data
    assert "message" not in result.data


def test_root_one_of_branch_filter_with_override() -> None:
    engine = create_default_contract_engine()

    result = engine.generate_instance(
        ROOT_ONE_OF_SCHEMA,
        refinements={"": {"one_of_filter": {"kind": "sensor"}}},
        overrides={"value": 42},
    )

    assert result.data["kind"] == "sensor"
    assert result.data["value"] == 42


def test_refinement_affects_generation() -> None:
    schema = {
        "type": "object",
        "properties": {
            "temperature": {"type": "number"},
        },
    }

    engine = create_default_contract_engine()

    result = engine.generate_instance(
        schema,
        refinements={"temperature": {"const": 42}},
    )

    assert result.data["temperature"] == 42


def test_default_used_in_realistic_mode() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "default": "koekjes"}},
        "required": ["name"],
    }
    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="test", mode=GenerationMode.REALISTIC)
    assert result.data["name"] == "koekjes"


def test_default_ignored_in_fuzz_mode() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "default": "koekjes"}},
        "required": ["name"],
    }
    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="test", mode=GenerationMode.FUZZ)
    assert result.data["name"] != "koekjes"


def test_nullable_string_default_used_in_realistic_mode() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": ["string", "null"], "default": "koekjes"}},
        "required": ["name"],
    }
    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="test", mode=GenerationMode.REALISTIC)
    assert result.data["name"] == "koekjes"


def test_nullable_string_null_default_used_in_realistic_mode() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": ["string", "null"], "default": None}},
        "required": ["name"],
    }
    engine = create_default_contract_engine()
    result = engine.generate_instance(schema, seed="test", mode=GenerationMode.REALISTIC)
    assert result.data["name"] is None


def test_default_type_mismatch_raises_at_validation() -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"type": "string", "default": 1.0}},
        "required": ["value"],
    }
    engine = create_default_contract_engine()
    with pytest.raises(ContractValidationError, match="default value"):
        engine.generate_instance(schema, seed="test")

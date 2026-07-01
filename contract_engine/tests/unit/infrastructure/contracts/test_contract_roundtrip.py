import json
from pathlib import Path

import pytest

from contract_engine.application.generator_service import GeneratorService
from contract_engine.application.validation_service import ValidationService
from contract_engine.infrastructure.contract_parsers.jsonschema.jsonschema_contract_parser import (
    JsonSchemaContractParser,
)
from contract_engine.infrastructure.generators.deterministic_generator import DeterministicGenerator
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.validation.jsonschema_builder import JsonSchemaBuilder
from contract_engine.infrastructure.validation.jsonschema_validator import JsonSchemaValidator

CONTRACTS_DIR = Path("src/contract_engine/infrastructure/contracts")
SEEDS = [0, 1, 42, 1234, 20260313]


def discover_contracts() -> list[Path]:
    return sorted(CONTRACTS_DIR.glob("**/*.json"))


def test_roundtrip_generation_validation() -> None:

    path = Path("tests/fixtures/contracts/simple_schema.json")

    with path.open() as f:
        document = json.load(f)

    parser = JsonSchemaContractParser()

    contract = parser.parse(document)

    generator = GeneratorService(DeterministicGenerator())

    validator = ValidationService(
        JsonSchemaBuilder(),
        JsonSchemaValidator(),
    )

    generation_result = generator.generate(contract, seed=1)

    result = validator.validate(contract, generation_result.data)

    assert result.valid


@pytest.mark.parametrize("schema_path", discover_contracts())
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("mode", GenerationMode)
def test_contract_roundtrip(schema_path: Path, seed: int, mode: GenerationMode) -> None:

    with schema_path.open() as f:
        schema = json.load(f)

    parser = JsonSchemaContractParser()
    contract = parser.parse(schema, base_path=schema_path.parent)

    generator = GeneratorService(DeterministicGenerator(), mode=mode)

    validator = ValidationService(
        JsonSchemaBuilder(),
        JsonSchemaValidator(),
    )

    instance = generator.generate(contract, seed=seed)

    result = validator.validate(contract, instance.data)
    assert result.valid, f"Generated instance invalid for {schema_path.name} (seed={seed}) → {instance}"

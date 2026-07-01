from contract_engine.application.generator_service import GeneratorService
from contract_engine.application.validation_service import ValidationService
from contract_engine.domain.contract import Contract
from contract_engine.domain.types import FieldDefinition, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.generators.deterministic_generator import DeterministicGenerator
from contract_engine.infrastructure.validation.jsonschema_builder import JsonSchemaBuilder
from contract_engine.infrastructure.validation.jsonschema_validator import JsonSchemaValidator


def test_generated_instance_validates() -> None:
    generator = GeneratorService(DeterministicGenerator())

    validator = ValidationService(
        JsonSchemaBuilder(),
        JsonSchemaValidator(),
    )

    contract = Contract(
        name="test",
        version="1.0",
        fields=[
            FieldDefinition(
                name="value",
                type=PrimitiveType(
                    kind=PrimitiveKind.INTEGER,
                    minimum=0,
                    maximum=10,
                ),
            )
        ],
    )

    generation_result = generator.generate(contract, seed=1)
    instance = generation_result.data

    result = validator.validate(contract, instance)

    assert result.valid

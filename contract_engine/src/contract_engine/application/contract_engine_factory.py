from contract_engine.application.contract_engine import ContractEngine
from contract_engine.application.contract_introspection_service import ContractIntrospectionService
from contract_engine.application.contract_loader_service import ContractLoaderService
from contract_engine.application.contract_refinement_service import ContractRefinementService
from contract_engine.application.contract_validation_service import ContractValidationService
from contract_engine.application.generator_service import GeneratorService
from contract_engine.application.validation_service import ValidationService
from contract_engine.infrastructure.contract_introspectors.default_contract_introspector import (
    DefaultContractIntrospector,
)
from contract_engine.infrastructure.contract_parsers.jsonschema.jsonschema_contract_parser import (
    JsonSchemaContractParser,
)
from contract_engine.infrastructure.generators.deterministic_generator import DeterministicGenerator
from contract_engine.infrastructure.validation.jsonschema_builder import JsonSchemaBuilder
from contract_engine.infrastructure.validation.jsonschema_validator import JsonSchemaValidator


def create_default_contract_engine() -> ContractEngine:
    parser = JsonSchemaContractParser()

    loader = ContractLoaderService(parser)

    contract_refiner = ContractRefinementService()

    contract_validator = ContractValidationService()

    generator = GeneratorService(DeterministicGenerator())

    validator = ValidationService(JsonSchemaBuilder(), JsonSchemaValidator())

    introspector = ContractIntrospectionService(DefaultContractIntrospector())

    return ContractEngine(loader, generator, validator, introspector, contract_refiner, contract_validator)

from pathlib import Path
from typing import Any

from contract_engine.application.contract_introspection_service import (
    ContractIntrospectionService,
)
from contract_engine.application.contract_loader_service import ContractLoaderService
from contract_engine.application.contract_refinement_service import ContractRefinementService
from contract_engine.application.contract_refinement_types import Refinements
from contract_engine.application.contract_validation_service import ContractValidationService
from contract_engine.application.generator_service import GeneratorService
from contract_engine.application.validation_service import ValidationService
from contract_engine.domain.contract import Contract
from contract_engine.domain.field_info import FieldInfo
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.domain.validation_result import ValidationResult
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.seed_utils import derive_instance_seed


class ContractEngine:
    """
    Facade API for the Contract Engine.

    Provides a stable interface for external users (Python / Robot)
    while orchestrating internal application services.
    """

    def __init__(
        self,
        loader: ContractLoaderService,
        generator: GeneratorService,
        validator: ValidationService,
        introspector: ContractIntrospectionService,
        contract_refiner: ContractRefinementService,
        contract_validator: ContractValidationService,
    ) -> None:
        self._loader = loader
        self._generator = generator
        self._validator = validator
        self._introspector = introspector
        self._contract_validator = contract_validator
        self._contract_refiner = contract_refiner

    def generate_instance_from_contract(
        self,
        contract: Contract,
        seed: int | str | None = None,
        mode: GenerationMode = GenerationMode.REALISTIC,
        overrides: dict[str, Any] | None = None,
    ) -> GenerationResult:

        return self._generator.generate(
            contract=contract,
            seed=seed,
            mode=mode,
            overrides=overrides,
        )

    def generate_instance(
        self,
        contract_source: str | dict[str, Any],
        seed: int | str | None = None,
        mode: GenerationMode = GenerationMode.REALISTIC,
        overrides: dict[str, Any] | None = None,
        refinements: Refinements | None = None,
        *,
        base_path: Path | None = None,
    ) -> GenerationResult:

        contract = self._prepare_contract(contract_source, refinements=refinements, base_path=base_path)
        return self.generate_instance_from_contract(contract, seed, mode, overrides)

    def generate_instances(
        self,
        contract_source: str | dict[str, Any],
        count: int,
        seed: int | str | None = None,
        mode: GenerationMode = GenerationMode.REALISTIC,
        overrides: dict[str, Any] | None = None,
        refinements: Refinements | None = None,
        *,
        base_path: Path | None = None,
    ) -> list[GenerationResult]:

        contract = self._prepare_contract(contract_source, refinements=refinements, base_path=base_path)
        results = []

        for i in range(count):
            instance_seed = derive_instance_seed(seed, i)

            result = self.generate_instance_from_contract(
                contract,
                instance_seed,
                mode,
                overrides,
            )

            results.append(result)

        return results

    def validate_instance(
        self,
        contract_source: str | dict[str, Any],
        instance: dict[str, Any],
        refinements: Refinements | None = None,
        *,
        base_path: Path | None = None,
    ) -> ValidationResult:
        """
        Validate a generated or external instance against a contract.
        """

        contract = self._prepare_contract(contract_source, refinements=refinements, base_path=base_path)

        return self._validator.validate(contract, instance)

    def inspect_contract(
        self,
        contract_source: str | dict[str, Any],
        refinements: Refinements | None = None,
        *,
        base_path: Path | None = None,
    ) -> list[FieldInfo]:
        """
        Inspect the contract structure for override paths.
        """

        contract = self._prepare_contract(contract_source, refinements=refinements, base_path=base_path)

        return self._introspector.inspect(contract)

    def _prepare_contract(
        self,
        contract_source: str | dict[str, Any],
        *,
        base_path: Path | None = None,
        refinements: Refinements | None = None,
    ) -> Contract:
        contract = self._loader.load(contract_source, base_path=base_path)

        if refinements:
            contract = self._contract_refiner.refine(contract, refinements)

        self._contract_validator.validate_contract(contract)

        return contract

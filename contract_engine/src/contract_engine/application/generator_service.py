import logging
from typing import Any

from contract_engine.application.interfaces.generator import Generator
from contract_engine.application.override_applier import apply_overrides
from contract_engine.domain.contract import Contract
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.seed_utils import normalize_seed

logger = logging.getLogger(__name__)


class GeneratorService:
    def __init__(
        self,
        generator: Generator,
        mode: GenerationMode = GenerationMode.REALISTIC,
    ) -> None:
        self._generator = generator
        self._mode = mode

    def generate(
        self,
        contract: Contract,
        seed: int | str | None = None,
        mode: GenerationMode = GenerationMode.REALISTIC,
        overrides: dict[str, Any] | None = None,
    ) -> GenerationResult:
        seed_obj = normalize_seed(seed)

        logger.debug(
            "Generating instance contract=%s mode=%s seed=%s",
            contract.name,
            mode,
            seed_obj.label,
        )

        result = self._generator.generate(contract, mode, seed_obj)

        if overrides:
            result.data = apply_overrides(result.data, overrides, seed_obj)

        return result

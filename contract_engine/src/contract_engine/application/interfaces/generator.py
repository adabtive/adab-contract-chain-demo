from typing import Protocol

from contract_engine.domain.contract import Contract
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.domain.seed import Seed
from contract_engine.infrastructure.generators.generation_mode import GenerationMode


class Generator(Protocol):
    def generate(
        self,
        contract: Contract,
        mode: GenerationMode,
        seed: Seed,
    ) -> GenerationResult: ...

import random
from typing import TYPE_CHECKING, Any, Protocol

from contract_engine.infrastructure.generators.generation_mode import GenerationMode

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class GenerationStrategy[T](Protocol):
    def generate(
        self,
        field_type: T,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> Any: ...

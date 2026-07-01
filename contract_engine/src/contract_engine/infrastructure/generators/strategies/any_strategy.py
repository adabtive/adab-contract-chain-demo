import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import AnyType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class AnyStrategy(GenerationStrategy[AnyType]):
    def generate(
        self,
        _field_type: AnyType,
        _generator: "DeterministicGenerator",
        rng: random.Random,
        _mode: GenerationMode,
        _depth: int,
    ) -> Any:
        return rng.choice(
            [
                None,
                "",
                0,
                True,
                {},
            ]
        )

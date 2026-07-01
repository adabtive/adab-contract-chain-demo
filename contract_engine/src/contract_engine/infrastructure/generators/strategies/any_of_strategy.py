import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import AnyOfType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.filters import filter_ambiguous_numeric_union
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class AnyOfStrategy(GenerationStrategy[AnyOfType]):
    def generate(
        self,
        field_type: AnyOfType,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> Any:
        options = filter_ambiguous_numeric_union(field_type.options)
        option = rng.choice(options)
        return generator.generate_field(option, rng, mode, depth + 1)

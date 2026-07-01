import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import UNSET, OneOfType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.filters import filter_ambiguous_numeric_union
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class OneOfStrategy(GenerationStrategy[OneOfType]):
    def generate(
        self,
        field_type: OneOfType,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> Any:
        if mode == GenerationMode.REALISTIC and field_type.default is not UNSET:
            return field_type.default

        options = filter_ambiguous_numeric_union(field_type.options)
        option = rng.choice(options)
        return generator.generate_field(option, rng, mode, depth + 1)

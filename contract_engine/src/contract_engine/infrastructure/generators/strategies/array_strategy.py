import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import ArrayType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class ArrayStrategy(GenerationStrategy[ArrayType]):
    def generate(
        self,
        field_type: ArrayType,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> list[Any]:

        minimum = field_type.min_items if field_type.min_items is not None else 0
        maximum = field_type.max_items if field_type.max_items is not None else minimum + 10

        if field_type.prefix_items:
            result = [generator.generate_field(t, rng, mode, depth + 1) for t in field_type.prefix_items]

            if field_type.allow_additional_items:
                extra_min = max(0, minimum - len(result))
                extra_max = maximum - len(result)
                if extra_max > 0:
                    extra = self._pick_size(extra_min, extra_max, rng, mode, generator)
                    result.extend(
                        generator.generate_field(field_type.items, rng, mode, depth + 1) for _ in range(extra)
                    )

            return result

        size = self._pick_size(minimum, maximum, rng, mode, generator)
        return [generator.generate_field(field_type.items, rng, mode, depth + 1) for _ in range(size)]

    def _pick_size(
        self,
        minimum: int,
        maximum: int,
        rng: random.Random,
        mode: GenerationMode,
        generator: "DeterministicGenerator",
    ) -> int:
        if mode == GenerationMode.REALISTIC:
            return rng.randint(minimum, (minimum + maximum) // 2)
        return generator.edge_biased_int(minimum, maximum, rng)

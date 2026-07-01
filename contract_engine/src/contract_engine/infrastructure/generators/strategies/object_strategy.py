import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import ObjectType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class ObjectStrategy(GenerationStrategy[ObjectType]):
    def generate(
        self,
        field_type: ObjectType,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> dict[str, Any]:

        result: dict[str, Any] = {}

        for field in field_type.fields:
            if not field.required:
                presence_probability = 0.9 if mode == GenerationMode.REALISTIC else 0.5

                if rng.random() > presence_probability:
                    continue

            result[field.name] = generator.generate_field(
                field.type,
                rng,
                mode,
                depth + 1,
            )

        return result

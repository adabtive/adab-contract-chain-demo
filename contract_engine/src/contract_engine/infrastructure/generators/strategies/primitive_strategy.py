import random
from typing import TYPE_CHECKING, Any

from contract_engine.domain.types import UNSET, PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.deterministic_generator import (
        DeterministicGenerator,
    )


class PrimitiveStrategy(GenerationStrategy[PrimitiveType]):
    def generate(
        self,
        field_type: PrimitiveType,
        generator: "DeterministicGenerator",
        rng: random.Random,
        mode: GenerationMode,
        _depth: int = 0,
    ) -> Any:

        if mode == GenerationMode.REALISTIC and field_type.default is not UNSET:
            return field_type.default

        if field_type.enum:
            return rng.choice(field_type.enum)

        match field_type.kind:
            case PrimitiveKind.INTEGER:
                return generator.generate_integer(field_type, rng, mode)

            case PrimitiveKind.NUMBER:
                return generator.generate_number(field_type, rng, mode)

            case PrimitiveKind.STRING:
                return generator.generate_string(field_type, rng, mode)

            case PrimitiveKind.BOOLEAN:
                return rng.choice([True, False])

            case PrimitiveKind.NULL:
                return None

            case _:
                raise TypeError(f"Unsupported primitive kind: {field_type.kind}")

from typing import Any, Protocol

from contract_engine.domain.generation_result import GenerationResult


class Serializer(Protocol):
    def serialize(
        self,
        message: GenerationResult,
        *,
        include_seed: bool = False,
    ) -> dict[str, Any]: ...

from typing import Any

from contract_engine.application.interfaces.serializer import Serializer
from contract_engine.domain.generation_result import GenerationResult


class JsonSerializer(Serializer):
    def serialize(
        self,
        message: GenerationResult,
        *,
        include_seed: bool = False,
    ) -> dict[str, Any]:

        if not include_seed:
            return message.data

        return {
            **message.data,
            "_meta": {
                "seed": {
                    "label": message.seed.label,
                    "value": message.seed.value,
                }
            },
        }

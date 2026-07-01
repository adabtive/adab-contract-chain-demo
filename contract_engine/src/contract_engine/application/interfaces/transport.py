from typing import Protocol

from contract_engine.domain.generation_result import GenerationResult


class Transport(Protocol):
    def send(
        self,
        destination: str,
        message: GenerationResult,
        *,
        include_seed: bool = False,
    ) -> None: ...

    def send_multiple(
        self, destination: str, messages: list[GenerationResult], *, include_seed: bool = False, concurrency: int = 10
    ) -> None: ...

from typing import Any, Protocol

from contract_engine.domain.validation_result import ValidationResult


class Validator(Protocol):
    def validate(self, schema: dict[str, Any], instance: dict[str, Any]) -> ValidationResult: ...

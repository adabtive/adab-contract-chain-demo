from typing import Any

from contract_engine.application.interfaces.schema_builder import SchemaBuilder
from contract_engine.application.interfaces.validator import Validator
from contract_engine.domain.contract import Contract
from contract_engine.domain.validation_result import ValidationResult


class ValidationService:
    def __init__(self, schema_builder: SchemaBuilder, validator: Validator) -> None:
        self._schema_builder = schema_builder
        self._validator = validator

    def validate(self, contract: Contract, instance: dict[str, Any]) -> ValidationResult:
        schema = self._schema_builder.build(contract)
        return self._validator.validate(schema, instance)

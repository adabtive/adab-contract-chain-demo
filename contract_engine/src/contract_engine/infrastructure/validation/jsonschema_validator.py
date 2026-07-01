from typing import Any

from jsonschema import Draft7Validator, FormatChecker

from contract_engine.domain.validation_result import (
    ValidationErrorDetail,
    ValidationResult,
)


class JsonSchemaValidator:
    def validate(self, schema: dict[str, Any], instance: dict[str, Any]) -> ValidationResult:
        validator = Draft7Validator(schema, format_checker=FormatChecker())

        errors = sorted(
            validator.iter_errors(instance),
            key=lambda e: list(e.absolute_path),
        )

        if not errors:
            return ValidationResult(valid=True)

        details = [
            ValidationErrorDetail(
                location=".".join(map(str, error.absolute_path)) or "$",
                message=error.message,
            )
            for error in errors
        ]

        return ValidationResult(valid=False, errors=details)

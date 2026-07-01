from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorDetail(BaseModel):
    location: str
    message: str

    model_config = ConfigDict(extra="forbid")


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationErrorDetail] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

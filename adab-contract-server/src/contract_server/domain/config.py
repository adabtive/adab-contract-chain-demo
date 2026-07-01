from enum import StrEnum
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class EndpointType(StrEnum):
    VALIDATE = "validate"
    GENERATE = "generate"
    RESPOND = "respond"


_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class Destination(BaseModel):
    path: str
    method: str = "POST"
    base_url: str | None = None

    @field_validator("path")
    @classmethod
    def path_must_start_with_slash(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError(f"destination path must start with '/' — got '{v}'")
        return v

    @field_validator("method", mode="before")
    @classmethod
    def uppercase_method(cls, v: str) -> str:
        v = v.upper()
        if v not in _ALLOWED_METHODS:
            raise ValueError(f"unsupported HTTP method '{v}'")
        return v


class EndpointConfig(BaseModel):
    type: EndpointType
    contract: str | None = None
    method: str = "POST"
    refinements: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None
    destination: Destination | None = None
    status_code: int = 200
    request_contract: str | None = None

    @field_validator("method", mode="before")
    @classmethod
    def uppercase_method(cls, v: str) -> str:
        v = v.upper()
        if v not in _ALLOWED_METHODS:
            raise ValueError(f"unsupported HTTP method '{v}'")
        return v

    @model_validator(mode="after")
    def check_required_fields(self) -> "EndpointConfig":
        if self.type == EndpointType.GENERATE:
            if self.contract is None:
                raise ValueError("generate endpoints require 'contract'")
            if self.destination is None:
                raise ValueError("generate endpoints require 'destination'")
        if self.type == EndpointType.VALIDATE and self.contract is None:
            raise ValueError("validate endpoints require 'contract'")
        return self


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8877
    display_name: str = "Contract Server"
    outgoing_base_url: str
    contracts_dir: str = "./contracts"
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None
    endpoints: dict[str, EndpointConfig]

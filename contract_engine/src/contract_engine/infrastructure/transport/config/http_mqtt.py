from pydantic import BaseModel

from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth


class HttpMqttConfig(BaseModel):
    host: str
    auth: AzureClientCredentialsAuth
    api_version: str = "2025-08-01-preview"

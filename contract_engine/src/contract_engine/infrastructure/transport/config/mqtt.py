from typing import Literal

from pydantic import BaseModel, Field

from contract_engine.infrastructure.transport.config.auth import AuthConfig, NoAuth


class MqttConfig(BaseModel):
    host: str

    port: int | None = None
    tls: bool = True

    transport: Literal["tcp", "websockets"] = "tcp"
    websocket_path: str | None = None

    client_id: str | None = None

    # TLS options (for non-Azure brokers)
    ca_cert: str | None = None
    client_cert: str | None = None
    client_key: str | None = None

    # Auth
    auth: AuthConfig = Field(default_factory=NoAuth)

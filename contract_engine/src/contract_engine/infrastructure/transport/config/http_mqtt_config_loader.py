import logging
import os

from contract_engine.infrastructure.transport.config.auth import AuthConfig, AzureClientCredentialsAuth
from contract_engine.infrastructure.transport.config.http_mqtt import HttpMqttConfig

logger = logging.getLogger(__name__)


def load_http_mqtt_config_from_env() -> HttpMqttConfig:
    if not os.getenv("MQTT_HOST"):
        raise ValueError("MQTT_HOST required for http_mqtt transport")

    auth: AuthConfig

    if os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_CLIENT_SECRET"):
        logger.info("[INFO] loading azure auth config")
        auth = AzureClientCredentialsAuth(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"],
        )
    else:
        raise ValueError("HTTP MQTT requires Azure auth")

    return HttpMqttConfig(
        host=os.environ["MQTT_HOST"],
        auth=auth,
    )

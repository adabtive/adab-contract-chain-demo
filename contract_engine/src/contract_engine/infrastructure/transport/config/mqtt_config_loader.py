import logging
import os

from contract_engine.infrastructure.transport.config.auth import (
    AuthConfig,
    AzureClientCredentialsAuth,
    NoAuth,
    UsernamePasswordAuth,
)
from contract_engine.infrastructure.transport.config.mqtt import MqttConfig

logger = logging.getLogger(__name__)


def load_mqtt_config_from_env() -> MqttConfig:
    if os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_CLIENT_SECRET"):
        logger.info("[INFO] loading azure auth config")
        auth: AuthConfig = AzureClientCredentialsAuth(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"],
        )

    elif os.getenv("MQTT_USERNAME"):
        logger.info("[INFO] loading basic auth config")
        auth = UsernamePasswordAuth(
            username=os.environ["MQTT_USERNAME"],
            password=os.environ.get("MQTT_PASSWORD", ""),
        )

    else:
        auth = NoAuth()

    mqtt_transport = os.getenv("MQTT_TRANSPORT", "tcp")
    mqtt_ws_path = os.getenv("MQTT_WS_PATH")
    logger.debug("[DEBUG] loading: mqtt_transport=%s and mqtt_websocket_path=%s", mqtt_transport, mqtt_ws_path)

    port_env = os.getenv("MQTT_PORT")
    logger.debug("[DEBUG] loading: mqtt_port=%s", port_env)

    port = int(port_env) if port_env is not None else 443 if mqtt_transport == "websockets" else 8883

    return MqttConfig(
        host=os.environ["MQTT_HOST"],
        port=port,
        tls=os.getenv("MQTT_TLS", "true").lower() == "true",
        transport=mqtt_transport,  # type: ignore[arg-type]
        websocket_path=mqtt_ws_path,
        client_id=os.getenv("MQTT_CLIENT_ID"),
        ca_cert=os.getenv("MQTT_CA_CERT"),
        client_cert=os.getenv("MQTT_CLIENT_CERT"),
        client_key=os.getenv("MQTT_CLIENT_KEY"),
        auth=auth,
    )

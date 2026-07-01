import logging
import os

from contract_engine.application.interfaces.transport import Transport
from contract_engine.infrastructure.serialization.json_serializer import JsonSerializer
from contract_engine.infrastructure.transport.config.http_mqtt_config_loader import load_http_mqtt_config_from_env
from contract_engine.infrastructure.transport.config.mqtt_config_loader import load_mqtt_config_from_env
from contract_engine.infrastructure.transport.http_mqtt_transport import HttpMqttTransport
from contract_engine.infrastructure.transport.mqtt_transport import MqttTransport

logger = logging.getLogger(__name__)


def load_transport_from_env() -> Transport:
    transport_type = os.getenv("TRANSPORT_TYPE", "mqtt")
    logger.info("[INFO] transport type: %s", transport_type)
    serializer = JsonSerializer()

    if transport_type == "mqtt":
        mqtt_config = load_mqtt_config_from_env()
        return MqttTransport(mqtt_config, serializer)

    if transport_type == "http_mqtt":
        http_mqtt_config = load_http_mqtt_config_from_env()
        return HttpMqttTransport(http_mqtt_config, serializer)

    raise ValueError(f"Unknown transport type: {transport_type}")

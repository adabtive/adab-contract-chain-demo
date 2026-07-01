import json
import logging
import threading
from typing import Any

import paho.mqtt.client as mqtt

from contract_engine.application.interfaces.serializer import Serializer
from contract_engine.application.interfaces.transport import Transport
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.infrastructure.transport.auth.auth_handler_factory import build_auth_handler
from contract_engine.infrastructure.transport.config.mqtt import MqttConfig

logger = logging.getLogger(__name__)


def _on_connect(_client: mqtt.Client, _userdata: Any, _flags: dict[str, Any], rc: int, _properties: Any = None) -> None:
    if rc == 0:
        logger.info("[MQTT] Connected successfully")
    else:
        logger.error("[MQTT] Connection failed with rc=%s", rc)


def _on_disconnect(_client: mqtt.Client, _userdata: Any, rc: int, _properties: Any = None) -> None:
    if rc == 0:
        logger.info("[MQTT] Disconnected cleanly")
    else:
        logger.warning("[MQTT] Unexpected disconnect rc=%s", rc)


class MqttTransport(Transport):
    def __init__(self, config: MqttConfig, serializer: Serializer) -> None:
        self._config = config
        self._serializer = serializer
        self._connected_event = threading.Event()
        self._auth = build_auth_handler(config.auth)

        self._client = mqtt.Client(
            client_id=self._config.client_id,
            transport=self._config.transport,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
        )

        def _on_connect(
            _client: mqtt.Client,
            _userdata: Any,
            _flags: dict[str, Any],
            rc: int,
            _properties: Any = None,
        ) -> None:
            if rc == 0:
                logger.info("[MQTT] Connected successfully")
                self._connected_event.set()
            else:
                logger.error("[MQTT] Connection failed with rc=%s", rc)

        def _on_disconnect(
            _client: mqtt.Client,
            _userdata: Any,
            rc: int,
            _properties: Any = None,
        ) -> None:
            if rc == 0:
                logger.info("[MQTT] Disconnected cleanly")
            else:
                logger.warning("[MQTT] Unexpected disconnect rc=%s", rc)

        def _on_log(
            _client: mqtt.Client,
            _userdata: Any,
            _level: int,
            buf: str,
        ) -> None:
            logger.debug("[MQTT LOG] %s", buf)

        self._client.on_connect = _on_connect
        self._client.on_disconnect = _on_disconnect
        self._client.on_log = _on_log

        self._configure_connection()

        port = self._config.port

        if port is None:
            port = 443 if self._config.transport == "websockets" else 8883
        logger.info(
            "[MQTT CONFIG] host=%s port=%s transport=%s ws_path=%s tls=%s",
            self._config.host,
            port,
            self._config.transport,
            self._config.websocket_path,
            self._config.tls,
        )
        logger.info(
            "[MQTT CLIENT] transport=%s protocol=%s",
            self._config.transport,
            mqtt.MQTTv5,
        )
        if self._config.transport == "websockets":
            path = self._config.websocket_path or "/mqtt"
            logger.info("[MQTT WS] path=%s", path)

            self._client.ws_set_options(
                path=path,
                headers={
                    "Sec-WebSocket-Protocol": "mqtt",
                },
            )

        self._client.enable_logger(logger)
        self._client.connect(self._config.host, port)
        self._client.loop_start()

        if not self._connected_event.wait(timeout=5):
            raise RuntimeError("MQTT connection timeout")

    def _configure_connection(self) -> None:
        tls_configured = self._auth.configure_mqtt(self._client)

        # fallback TLS if auth didn not set it
        if self._config.tls and not tls_configured:
            self._client.tls_set()

    def send(
        self,
        topic: str,
        message: GenerationResult,
        *,
        include_seed: bool = False,
    ) -> None:
        payload = json.dumps(self._serializer.serialize(message, include_seed=include_seed))

        result = self._client.publish(topic, payload)
        result.wait_for_publish()

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {result.rc}")

        if not result.is_published():
            raise RuntimeError("MQTT message was not published successfully")

    def send_multiple(
        self,
        topic: str,
        messages: list[GenerationResult],
        *,
        include_seed: bool = False,
        # ignored for MQTT (but kept for interface consistency)
        concurrency: int = 10,  # noqa: ARG002
    ) -> None:
        results = []

        for message in messages:
            payload = json.dumps(self._serializer.serialize(message, include_seed=include_seed))

            result = self._client.publish(topic, payload)
            results.append(result)

        # wait for all publishes
        for result in results:
            result.wait_for_publish()

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"MQTT publish failed with code {result.rc}")

            if not result.is_published():
                raise RuntimeError("MQTT message was not published successfully")

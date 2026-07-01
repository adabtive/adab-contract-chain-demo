import paho.mqtt.client as mqtt

from contract_engine.infrastructure.transport.auth.auth_handler import AuthHandler
from contract_engine.infrastructure.transport.config.auth import UsernamePasswordAuth


class BasicAuthHandler(AuthHandler):
    def __init__(self, config: UsernamePasswordAuth) -> None:
        self._config = config

    def get_headers(self) -> dict[str, str]:
        # HTTP MQTT does not use this, but placeholder for future
        return {}

    def configure_mqtt(self, client: mqtt.Client) -> bool:
        client.username_pw_set(
            self._config.username,
            self._config.password,
        )
        client.tls_set()

        return True

import paho.mqtt.client as mqtt

from contract_engine.infrastructure.transport.auth.auth_handler import AuthHandler


class NoAuthHandler(AuthHandler):
    def get_headers(self) -> dict[str, str]:
        return {}

    def configure_mqtt(self, _client: mqtt.Client) -> bool:
        return False

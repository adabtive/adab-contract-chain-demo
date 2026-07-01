from typing import Protocol

import paho.mqtt.client as mqtt


class AuthHandler(Protocol):
    def get_headers(self) -> dict[str, str]: ...
    def configure_mqtt(self, client: mqtt.Client) -> bool: ...

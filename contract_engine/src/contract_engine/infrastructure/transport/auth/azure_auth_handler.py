import paho.mqtt.client as mqtt

from contract_engine.infrastructure.transport.auth.auth_handler import AuthHandler
from contract_engine.infrastructure.transport.auth.azure_token_provider import AzureTokenProvider
from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth


class AzureAuthHandler(AuthHandler):
    def __init__(self, config: AzureClientCredentialsAuth) -> None:
        self._provider = AzureTokenProvider(config)
        self._config = config

    def get_headers(self) -> dict[str, str]:
        token = self._provider.get_token()
        return {"Authorization": f"Bearer {token}"}

    def configure_mqtt(self, client: mqtt.Client) -> bool:
        token = self._provider.get_token()

        client.username_pw_set(
            self._config.client_id,
            token,
        )

        import ssl

        context = ssl.create_default_context()
        context.set_alpn_protocols(["mqtt"])
        client.tls_set_context(context)

        return True

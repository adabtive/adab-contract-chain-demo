from unittest.mock import patch

from contract_engine.infrastructure.transport.auth.azure_auth_handler import AzureAuthHandler
from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth


def test_azure_auth_handler_headers() -> None:
    handler = AzureAuthHandler(
        AzureClientCredentialsAuth(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
    )

    with patch.object(handler._provider, "get_token", return_value="token"):
        headers = handler.get_headers()

    assert headers == {"Authorization": "Bearer token"}

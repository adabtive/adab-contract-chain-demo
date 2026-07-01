from unittest.mock import patch

import pytest

from contract_engine.infrastructure.transport.auth.azure_token_provider import AzureTokenProvider
from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth


def test_get_token_success() -> None:
    provider = AzureTokenProvider(
        AzureClientCredentialsAuth(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
    )

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_post.return_value.raise_for_status.return_value = None

        token = provider.get_token()

    assert token == "token"


def test_get_token_missing_access_token() -> None:
    provider = AzureTokenProvider(
        AzureClientCredentialsAuth(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
    )

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.raise_for_status.return_value = None

        with pytest.raises(TypeError):
            provider.get_token()


def test_get_token_cached() -> None:
    provider = AzureTokenProvider(
        AzureClientCredentialsAuth(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
    )

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "access_token": "token",
            "expires_in": 3600,
        }
        mock_post.return_value.raise_for_status.return_value = None

        token1 = provider.get_token()
        token2 = provider.get_token()

    assert token1 == "token"
    assert token2 == "token"
    assert mock_post.call_count == 1

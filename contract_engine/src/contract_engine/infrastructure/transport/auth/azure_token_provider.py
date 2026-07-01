from datetime import UTC, datetime, timedelta

import requests

from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth


class AzureTokenProvider:
    def __init__(self, config: AzureClientCredentialsAuth) -> None:
        self._config = config
        self._token: str | None = None
        self._expiry: datetime | None = None

    def get_token(self) -> str:
        now = datetime.now(UTC)

        if self._token and self._expiry and now < self._expiry:
            return self._token

        url = f"https://login.microsoftonline.com/{self._config.tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": self._config.client_id,
            "scope": "https://eventgrid.azure.net/.default",
            "client_secret": self._config.client_secret,
            "grant_type": "client_credentials",
        }

        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, dict):
            raise TypeError(f"Unexpected token response: {payload}")

        access_token = payload.get("access_token")

        if not isinstance(access_token, str):
            raise TypeError(f"Invalid token response: {payload}")

        self._token = access_token
        self._expiry = now + timedelta(seconds=payload["expires_in"] - 60)

        return self._token

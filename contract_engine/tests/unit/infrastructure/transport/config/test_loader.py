from unittest.mock import patch

from contract_engine.infrastructure.transport.config.auth import (
    AzureClientCredentialsAuth,
    NoAuth,
    UsernamePasswordAuth,
)
from contract_engine.infrastructure.transport.config.mqtt_config_loader import load_mqtt_config_from_env


def test_loader_uses_azure_auth_when_env_present() -> None:
    with patch.dict(
        "os.environ",
        {
            "MQTT_HOST": "host",
            "AZURE_CLIENT_ID": "id",
            "AZURE_CLIENT_SECRET": "secret",
            "AZURE_TENANT_ID": "tenant",
        },
    ):
        config = load_mqtt_config_from_env()

    assert isinstance(config.auth, AzureClientCredentialsAuth)


def test_loader_falls_back_to_basic_auth() -> None:
    with patch.dict(
        "os.environ",
        {
            "MQTT_HOST": "host",
            "MQTT_USERNAME": "user",
            "MQTT_PASSWORD": "pass",
        },
    ):
        config = load_mqtt_config_from_env()

    assert isinstance(config.auth, UsernamePasswordAuth)


def test_loader_defaults_to_no_auth() -> None:
    with patch.dict(
        "os.environ",
        {
            "MQTT_HOST": "host",
        },
    ):
        config = load_mqtt_config_from_env()

    assert isinstance(config.auth, NoAuth)

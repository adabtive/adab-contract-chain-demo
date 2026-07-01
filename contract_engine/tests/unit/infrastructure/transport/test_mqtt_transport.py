from typing import Any
from unittest.mock import Mock, patch

from contract_engine.infrastructure.serialization.json_serializer import JsonSerializer
from contract_engine.infrastructure.transport.config.auth import AzureClientCredentialsAuth, UsernamePasswordAuth
from contract_engine.infrastructure.transport.config.mqtt import MqttConfig
from contract_engine.infrastructure.transport.mqtt_transport import MqttTransport


def test_transport_uses_auth_handler_for_mqtt_config() -> None:
    config = MqttConfig(
        host="host",
        auth=AzureClientCredentialsAuth(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        ),
    )

    fake_handler = Mock()

    with (
        patch("contract_engine.infrastructure.transport.mqtt_transport.build_auth_handler", return_value=fake_handler),
        patch("paho.mqtt.client.Client") as mock_client_cls,
    ):
        mock_client = mock_client_cls.return_value

        def trigger_connect(*_args: Any, **_kwargs: Any) -> None:
            mock_client.on_connect(mock_client, None, {}, 0)

        mock_client.connect.side_effect = trigger_connect

        _serializer = JsonSerializer()
        _transport = MqttTransport(config, _serializer)

        fake_handler.configure_mqtt.assert_called_once_with(mock_client)


def test_transport_uses_basic_auth() -> None:
    config = MqttConfig(
        host="host",
        auth=UsernamePasswordAuth(username="u", password="p"),
    )

    with patch("paho.mqtt.client.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value

        # simulate connect → immediately trigger on_connect callback
        def trigger_connect(*_args: Any, **_kwargs: Any) -> None:
            # call assigned callback with rc=0 (success)
            mock_client.on_connect(mock_client, None, {}, 0)

        mock_client.connect.side_effect = trigger_connect

        _transport = MqttTransport(config, JsonSerializer())

        mock_client.username_pw_set.assert_called_with("u", "p")

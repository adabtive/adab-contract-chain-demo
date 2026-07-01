import asyncio
import logging
import urllib.parse
from typing import Any

import aiohttp

from contract_engine.application.interfaces.serializer import Serializer
from contract_engine.application.interfaces.transport import Transport
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.infrastructure.transport.auth.auth_handler_factory import build_auth_handler
from contract_engine.infrastructure.transport.config.http_mqtt import HttpMqttConfig

logger = logging.getLogger(__name__)


class HttpMqttTransport(Transport):
    def __init__(self, config: HttpMqttConfig, serializer: Serializer) -> None:
        self._config = config
        self._host = config.host
        self._auth = build_auth_handler(config.auth)
        self._serializer = serializer

    def _preview(self, payload: dict[str, Any], max_len: int = 500) -> str:
        import json

        text = json.dumps(payload)
        if len(text) > max_len:
            return text[:max_len] + "...(truncated)"
        return text

    def _safe_headers(self, headers: dict[str, Any]) -> dict[str, Any]:
        safe = dict(headers)
        if "Authorization" in safe:
            safe["Authorization"] = "Bearer ***"
        return safe

    def send(
        self,
        destination: str,
        message: GenerationResult,
        *,
        include_seed: bool = False,
    ) -> None:
        asyncio.run(
            self._send_many_async(
                destination,
                [message],
                include_seed=include_seed,
            )
        )

    def send_multiple(
        self,
        destination: str,
        messages: list[GenerationResult],
        *,
        include_seed: bool = False,
        concurrency: int = 10,
    ) -> None:
        asyncio.run(
            self._send_many_async(
                destination,
                messages,
                include_seed=include_seed,
                concurrency=concurrency,
            )
        )

    async def _send_many_async(
        self,
        destination: str,
        messages: list[GenerationResult],
        *,
        include_seed: bool,
        concurrency: int = 10,
    ) -> None:
        url = self._build_url(destination)

        headers = self._build_headers()

        semaphore = asyncio.Semaphore(concurrency)

        logger.debug("[HTTP MQTT] Sending batch")
        logger.debug("[HTTP MQTT] URL: %s", url)
        logger.debug("[HTTP MQTT] Headers: %s", self._safe_headers(headers))
        logger.debug("[HTTP MQTT] Message count: %s", len(messages))

        async with aiohttp.ClientSession() as session:

            async def _send_one(idx: int, message: GenerationResult) -> None:
                async with semaphore:
                    payload = self._serializer.serialize(message, include_seed=include_seed)
                    logger.debug("[HTTP MQTT] [%s] Topic: %s", idx, destination)
                    logger.debug("[HTTP MQTT] [%s] Payload: %s", idx, self._preview(payload))

                    async with session.post(url, json=payload, headers=headers) as resp:
                        text = await resp.text()
                        logger.debug("[HTTP MQTT] [%s] Status: %s", idx, resp.status)
                        logger.debug("[HTTP MQTT] [%s] Response: %s", idx, text)
                        if resp.status < 200 or resp.status >= 300:
                            raise RuntimeError(f"HTTP MQTT publish failed: {resp.status} {text}")

            await asyncio.gather(*[_send_one(i, m) for i, m in enumerate(messages)])

    def _build_url(self, destination: str) -> str:
        encoded_topic = urllib.parse.quote(destination, safe="")
        return f"https://{self._host}/mqtt/messages?topic={encoded_topic}&api-version={self._config.api_version}"

    def _build_headers(self) -> dict[str, str]:
        return {
            "mqtt-qos": "1",
            "Content-Type": "application/json",
            **self._auth.get_headers(),
        }

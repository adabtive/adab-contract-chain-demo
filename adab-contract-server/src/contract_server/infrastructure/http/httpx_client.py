from typing import Any

import httpx

from contract_server.application.interfaces.http_client import HttpResponse


class HttpxClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def request(self, method: str, url: str, payload: dict[str, Any]) -> HttpResponse:
        response = await self._client.request(method, url, json=payload)
        try:
            body = response.json()
        except Exception:
            body = {}
        return HttpResponse(status_code=response.status_code, body=body)

    async def aclose(self) -> None:
        await self._client.aclose()

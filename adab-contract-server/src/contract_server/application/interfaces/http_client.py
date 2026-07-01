from typing import Any, NamedTuple, Protocol


class HttpResponse(NamedTuple):
    status_code: int
    body: dict[str, Any]


class HttpClient(Protocol):
    async def request(self, method: str, url: str, payload: dict[str, Any]) -> HttpResponse: ...

from typing import Protocol

from contract_server.domain.config import ServerConfig


class ConfigLoader(Protocol):
    def load(self, source: str) -> ServerConfig: ...

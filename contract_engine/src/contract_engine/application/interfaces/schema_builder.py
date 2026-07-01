from typing import Any, Protocol

from contract_engine.domain.contract import Contract


class SchemaBuilder(Protocol):
    def build(self, contract: Contract) -> dict[str, Any]: ...

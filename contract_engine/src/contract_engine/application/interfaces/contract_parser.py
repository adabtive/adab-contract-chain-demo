from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from contract_engine.domain.contract import Contract


class ContractParser(Protocol):
    def parse(
        self,
        document: Mapping[str, Any],
        *,
        base_path: Path | None = None,
    ) -> Contract: ...

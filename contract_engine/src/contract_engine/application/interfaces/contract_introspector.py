from typing import Protocol

from contract_engine.domain.contract import Contract
from contract_engine.domain.field_info import FieldInfo


class ContractIntrospector(Protocol):
    def inspect(self, contract: Contract) -> list[FieldInfo]: ...

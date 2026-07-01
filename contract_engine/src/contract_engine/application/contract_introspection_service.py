from contract_engine.application.interfaces.contract_introspector import ContractIntrospector
from contract_engine.domain.contract import Contract
from contract_engine.domain.field_info import FieldInfo


class ContractIntrospectionService:
    def __init__(self, inspector: ContractIntrospector) -> None:
        self._inspector = inspector

    def inspect(self, contract: Contract) -> list[FieldInfo]:
        return self._inspector.inspect(contract)

    def list_paths(self, contract: Contract) -> list[str]:
        return [f.path for f in self.inspect(contract)]

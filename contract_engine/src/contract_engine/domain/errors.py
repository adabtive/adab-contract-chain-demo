class ContractValidationError(Exception):
    def __init__(self, message: str, path: str | None = None):
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)

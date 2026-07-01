from pathlib import Path

import yaml

from contract_server.domain.config import ServerConfig


class YamlConfigLoader:
    def load(self, source: str) -> ServerConfig:
        with Path(source).open() as f:
            data = yaml.safe_load(f)
        return ServerConfig.model_validate(data)

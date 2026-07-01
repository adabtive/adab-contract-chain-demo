from typing import Any

from pydantic import BaseModel, ConfigDict

from contract_engine.domain.seed import Seed


class GenerationResult(BaseModel):
    seed: Seed
    data: dict[str, Any]

    model_config = ConfigDict(extra="forbid")

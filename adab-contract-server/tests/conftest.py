from pathlib import Path

import pytest
from contract_engine.application.contract_engine_factory import create_default_contract_engine

from contract_server.domain.config import ServerConfig
from contract_server.infrastructure.events.in_memory_event_bus import InMemoryEventBus

CONTRACTS_DIR = Path(__file__).parent / "fixtures" / "contracts"


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def contracts_dir() -> Path:
    return CONTRACTS_DIR


@pytest.fixture
def engine():
    return create_default_contract_engine()


@pytest.fixture
def server_config() -> ServerConfig:
    return ServerConfig(
        outgoing_base_url="http://localhost:8000",
        contracts_dir=str(CONTRACTS_DIR),
        endpoints={
            "validate_a": {"type": "validate", "contract": "a.json"},
            "gen_b": {"type": "generate", "contract": "b.json", "destination": {"path": "/recv"}},
        },
    )

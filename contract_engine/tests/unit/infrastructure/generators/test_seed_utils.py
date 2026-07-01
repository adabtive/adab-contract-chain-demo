from contract_engine.domain.seed import Seed
from contract_engine.infrastructure.generators.seed_utils import normalize_seed


def test_string_seed_is_deterministic() -> None:
    assert normalize_seed("happyflow") == normalize_seed("happyflow")


def test_string_seed_changes() -> None:
    assert normalize_seed("a") != normalize_seed("b")


def test_int_seed_passthrough() -> None:
    assert normalize_seed(42) == Seed(value=42, label=42)

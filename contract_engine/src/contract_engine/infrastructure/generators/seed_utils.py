import hashlib
import random

from contract_engine.domain.seed import Seed


def normalize_seed(seed: int | str | None) -> Seed:

    if seed is None:
        value = random.randrange(0, 2**32)  # noqa: S311
        return Seed(label=value, value=value)

    if isinstance(seed, int):
        return Seed(label=seed, value=seed)

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    value = int.from_bytes(digest[:4], "big")

    return Seed(label=seed, value=value)


def derive_instance_seed(
    base_seed: int | str | None,
    index: int,
) -> int | str | None:

    if base_seed is None:
        return None

    if isinstance(base_seed, int):
        return base_seed + index

    return f"{base_seed}_{index}"

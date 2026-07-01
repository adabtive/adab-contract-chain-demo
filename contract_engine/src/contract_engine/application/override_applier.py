import logging
from typing import Any, Literal

from contract_engine.domain.seed import Seed

logger = logging.getLogger(__name__)


Index = int | Literal["*"] | None


class OverridePathError(Exception):
    """Raised when an override path cannot be resolved."""


def apply_overrides(
    data: dict[str, Any],
    overrides: dict[str, Any],
    seed: Seed,
) -> dict[str, Any]:
    for path, value in overrides.items():
        resolved = _resolve_value(value, seed)
        _set_path(data, path, resolved)

    return data


def _resolve_value(value: Any, seed: Seed) -> Any:
    if isinstance(value, str):
        return value.replace("{SEED}", str(seed.label))

    if isinstance(value, dict):
        return {k: _resolve_value(v, seed) for k, v in value.items()}

    if isinstance(value, list):
        return [_resolve_value(v, seed) for v in value]

    return value


def _set_path(obj: Any, path: str, value: Any) -> None:
    parts = _parse_path(path)
    _apply(obj, parts, value, path)


def _apply(
    current: Any,
    parts: list[tuple[str, Index]],
    value: Any,
    path: str,
) -> None:
    key, index = parts[0]

    if not isinstance(current, dict):
        raise OverridePathError("Expected object while resolving %r", path)

    if key not in current:
        if len(parts) == 1:
            logger.warning("Creating new field %r in path %r", key, path)
            current[key] = value
            return

        logger.warning("Creating intermediate field %r in path %r", key, path)
        current[key] = {}

    target = current[key]

    # Case 1: object field (no array index)
    if index is None:
        if len(parts) == 1:
            current[key] = value
            return

        _apply(target, parts[1:], value, path)
        return

    # From here we must be dealing with an array
    if not isinstance(target, list):
        raise OverridePathError(f"Field '{key}' is not an array in path '{path}'")

    # Case 2: wildcard array override
    if index == "*":
        if len(parts) == 1:
            raise OverridePathError(f"Wildcard override requires subfield in '{path}'")

        for element in target:
            _apply(element, parts[1:], value, path)

        return

    # Case 3: specific array index (STRICT)
    if not isinstance(index, int):
        raise OverridePathError(f"Invalid index '{index}' in path '{path}'")

    try:
        element = target[index]
    except IndexError as exc:
        raise OverridePathError(f"Index {index} out of range in path '{path}'") from exc

    if len(parts) == 1:
        target[index] = value
        return

    _apply(element, parts[1:], value, path)


def _parse_path(path: str) -> list[tuple[str, Index]]:
    parts: list[tuple[str, Index]] = []

    for part in path.split("."):
        if "[" in part:
            name, index = part[:-1].split("[")
            if index == "*":
                parts.append((name, "*"))
            else:
                parts.append((name, int(index)))
        else:
            parts.append((part, None))

    return parts

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from contract_engine.application.contract_engine_factory import create_default_contract_engine
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.transport.config.transport_config_loader import load_transport_from_env

if TYPE_CHECKING:
    from contract_engine.application.contract_engine import ContractEngine
    from contract_engine.application.contract_refinement_types import Constraint, Refinements
    from contract_engine.application.interfaces.transport import Transport
    from contract_engine.domain.field_info import FieldInfo
    from contract_engine.domain.generation_result import GenerationResult
    from contract_engine.domain.validation_result import ValidationResult

logger = logging.getLogger(__name__)


def _parse_overrides(overrides: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if overrides is None:
        return None

    if isinstance(overrides, dict):
        return overrides

    if not isinstance(overrides, str):
        raise TypeError(f"Invalid overrides type: {type(overrides)}")

    result: dict[str, Any] = {}

    for line in overrides.splitlines():
        line = line.strip()
        if not line:
            continue

        # JSON override (:=)
        if ":=" in line:
            key, raw_value = line.split(":=", 1)
            key = key.strip()
            raw_value = raw_value.strip()

            if not key:
                raise ValueError(f"Invalid override: empty key in '{line}'")

            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in override '{line}': {exc}") from exc

        # Standard override (=)
        elif "=" in line:
            key, raw_value = line.split("=", 1)
            key = key.strip()
            raw_value = raw_value.strip()

            if not key:
                raise ValueError(f"Invalid override: empty key in '{line}'")

            value = _parse_value(raw_value)

        else:
            raise ValueError(f"Invalid override format: '{line}' (expected key=value or key:=json)")

        result[key] = value

    return result


def _parse_value(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"

    if value.lower() == "null":
        return None

    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    try:
        return float(value)
    except ValueError:
        pass

    return value


_DATETIME_CONSTRAINT_KEYS = {"minimum_date_time", "maximum_date_time"}
_DATE_CONSTRAINT_KEYS = {"minimum_date", "maximum_date"}
_DURATION_CONSTRAINT_KEYS = {"minimum_duration", "maximum_duration"}

_ISO_DURATION_RE = re.compile(r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


def _parse_isoduration(value: str) -> timedelta:
    m = _ISO_DURATION_RE.match(value)
    if not m:
        raise ValueError(f"Invalid ISO 8601 duration: {value!r}")
    years, months, weeks, days, hours, minutes, seconds = (int(x or 0) for x in m.groups())
    total_days = years * 365 + months * 30 + weeks * 7 + days
    return timedelta(days=total_days, hours=hours, minutes=minutes, seconds=seconds)


def _coerce_constraint(raw: dict[str, Any]) -> Constraint:
    for key in _DATETIME_CONSTRAINT_KEYS:
        if key in raw and isinstance(raw[key], str):
            raw[key] = datetime.fromisoformat(raw[key])
    for key in _DATE_CONSTRAINT_KEYS:
        if key in raw and isinstance(raw[key], str):
            raw[key] = date.fromisoformat(raw[key])
    for key in _DURATION_CONSTRAINT_KEYS:
        if key in raw and isinstance(raw[key], str):
            raw[key] = _parse_isoduration(raw[key])
    return cast("Constraint", raw)


def _parse_refinements(refinements: str | dict[str, Any] | None) -> Refinements | None:
    if refinements is None:
        return None

    if isinstance(refinements, dict):
        return refinements  # type: ignore[return-value]

    if not isinstance(refinements, str):
        raise TypeError(f"Invalid refinements type: {type(refinements)}")

    result: Refinements = {}

    for line in refinements.splitlines():
        line = line.strip()
        if not line:
            continue

        if ":=" in line:
            key, raw_value = line.split(":=", 1)
            key = key.strip()
            raw_value = raw_value.strip()

            if not key:
                raise ValueError(f"Invalid refinement: empty key in '{line}'")

            try:
                constraint = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in refinement '{line}': {exc}") from exc

            if not isinstance(constraint, dict):
                raise ValueError(f"Refinement constraint must be a JSON object: '{line}'")

            result[key] = _coerce_constraint(constraint)

        elif "=" in line:
            key, raw_value = line.split("=", 1)
            key = key.strip()
            raw_value = raw_value.strip()

            if not key:
                raise ValueError(f"Invalid refinement: empty key in '{line}'")

            result[key] = {"const": _parse_value(raw_value)}

        else:
            raise ValueError(f"Invalid refinement format: '{line}' (expected key=value or key:=json)")

    return result


class ContractEngineKeywords:
    """
    Robot Framework keywords for the Contract Engine.
    """

    def __init__(self, engine: ContractEngine | None = None) -> None:
        self._engine = engine or create_default_contract_engine()
        self._transport: Transport | None = None

    def _get_transport(self) -> Transport:
        if self._transport is None:
            try:
                self._transport = load_transport_from_env()
            except (KeyError, ValueError) as exc:
                raise RuntimeError(
                    "Transport is not configured correctly. "
                    "Check environment variables (e.g. TRANSPORT_TYPE, MQTT_HOST, AZURE_CLIENT_ID)."
                ) from exc
        return self._transport

    def generate_contract_instance(
        self,
        contract: str | dict[str, Any],
        seed: int | str | None = None,
        mode: str = "realistic",
        overrides: dict[str, Any] | str | None = None,
        refinements: dict[str, Any] | str | None = None,
        base_path: str | None = None,
    ) -> GenerationResult:
        parsed_overrides = _parse_overrides(overrides)
        parsed_refinements = _parse_refinements(refinements)
        try:
            generation_mode = GenerationMode(mode.lower())
        except ValueError as exc:
            raise ValueError(f"Invalid mode: {mode}") from exc

        return self._engine.generate_instance(
            contract_source=contract,
            seed=seed,
            mode=generation_mode,
            overrides=parsed_overrides,
            refinements=parsed_refinements,
            base_path=Path(base_path) if base_path else None,
        )

    def generate_contract_instances(
        self,
        contract: str | dict[str, Any],
        count: int,
        seed: int | str | None = None,
        mode: str = "realistic",
        overrides: dict[str, Any] | str | None = None,
        refinements: dict[str, Any] | str | None = None,
        base_path: str | None = None,
    ) -> list[GenerationResult]:
        parsed_overrides = _parse_overrides(overrides)
        parsed_refinements = _parse_refinements(refinements)
        try:
            generation_mode = GenerationMode(mode.lower())
        except ValueError as exc:
            raise ValueError(f"Invalid mode: {mode}") from exc
        return self._engine.generate_instances(
            contract_source=contract,
            count=count,
            seed=seed,
            mode=generation_mode,
            overrides=parsed_overrides,
            refinements=parsed_refinements,
            base_path=Path(base_path) if base_path else None,
        )

    def validate_contract_instance(
        self,
        contract: str | dict[str, Any],
        instance: dict[str, Any],
        base_path: str | None = None,
    ) -> ValidationResult:
        """
        Validate an instance against a contract.
        """
        return self._engine.validate_instance(
            contract_source=contract,
            instance=instance,
            base_path=Path(base_path) if base_path else None,
        )

    def inspect_contract(
        self,
        contract: str | dict[str, Any],
        base_path: str | None = None,
    ) -> list[FieldInfo]:
        """
        Inspect contract structure for override paths.
        """
        return self._engine.inspect_contract(contract_source=contract, base_path=Path(base_path) if base_path else None)

    def send_message(
        self,
        message: GenerationResult,
        destination: str,
        *,
        include_seed: bool = False,
    ) -> None:
        transport = self._get_transport()
        transport.send(
            destination,
            message,
            include_seed=include_seed,
        )

    def send_messages(
        self,
        messages: list[GenerationResult],
        destination: str,
        *,
        include_seed: bool = False,
    ) -> None:
        transport = self._get_transport()

        transport.send_multiple(
            destination=destination,
            messages=messages,
            include_seed=include_seed,
        )

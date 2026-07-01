from datetime import date, timedelta

import pytest

from contract_engine.robot_adapter.keywords import _parse_isoduration, _parse_overrides, _parse_refinements


def test_overrides_support_json_values() -> None:
    overrides = _parse_overrides('data:=[{"a": 1}]')

    assert overrides is not None
    assert overrides["data"] == [{"a": 1}]


def test_refinements_none_returns_none() -> None:
    assert _parse_refinements(None) is None


def test_refinements_dict_passthrough() -> None:
    refinements = {"payload": {"one_of_filter": {"kind": "sensor"}}}
    assert _parse_refinements(refinements) == refinements


def test_refinements_simple_eq_becomes_const() -> None:
    result = _parse_refinements("payload.value = 42")

    assert result is not None
    assert result["payload.value"] == {"const": 42}


def test_refinements_json_constraint() -> None:
    result = _parse_refinements('payload := {"one_of_filter": {"kind": "sensor"}}')

    assert result is not None
    assert result["payload"] == {"one_of_filter": {"kind": "sensor"}}


def test_refinements_multiline() -> None:
    result = _parse_refinements('payload := {"one_of_filter": {"kind": "sensor"}}\npayload.value = 99')

    assert result is not None
    assert result["payload"] == {"one_of_filter": {"kind": "sensor"}}
    assert result["payload.value"] == {"const": 99}


def test_refinements_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="Invalid refinement format"):
        _parse_refinements("no_equals_sign")


def test_refinements_json_must_be_object_raises() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        _parse_refinements("payload := 42")


def test_refinements_coerces_minimum_date_from_string() -> None:
    result = _parse_refinements('field := {"minimum_date": "2024-01-01"}')
    assert result is not None
    assert result["field"]["minimum_date"] == date(2024, 1, 1)


def test_refinements_coerces_maximum_date_from_string() -> None:
    result = _parse_refinements('field := {"maximum_date": "2025-12-31"}')
    assert result is not None
    assert result["field"]["maximum_date"] == date(2025, 12, 31)


def test_refinements_coerces_minimum_duration_from_string() -> None:
    result = _parse_refinements('field := {"minimum_duration": "PT3600S"}')
    assert result is not None
    assert result["field"]["minimum_duration"] == timedelta(seconds=3600)


def test_refinements_coerces_maximum_duration_from_string() -> None:
    result = _parse_refinements('field := {"maximum_duration": "P1D"}')
    assert result is not None
    assert result["field"]["maximum_duration"] == timedelta(days=1)


def test_parse_isoduration_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Invalid ISO 8601 duration"):
        _parse_isoduration("not-a-duration")

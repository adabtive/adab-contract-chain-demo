from typing import Any

import pytest

from contract_engine.application.override_applier import OverridePathError, apply_overrides
from contract_engine.domain.seed import Seed

TEST_SEED = Seed(value=42, label="test-seed")


def test_simple_override() -> None:
    data = {"temperature": 20}

    result = apply_overrides(data, {"temperature": -100}, TEST_SEED)

    assert result["temperature"] == -100


def test_nested_override() -> None:
    data = {"data": {"temperature": 20}}

    result = apply_overrides(data, {"data.temperature": -100}, TEST_SEED)

    assert result["data"]["temperature"] == -100


def test_array_override() -> None:
    data = {"measurements": [{"value": 10}]}

    result = apply_overrides(data, {"measurements[0].value": 999}, TEST_SEED)

    assert result["measurements"][0]["value"] == 999


def test_array_wildcard_override() -> None:
    data = {
        "measurements": [
            {"value": 10},
            {"value": 20},
        ]
    }

    result = apply_overrides(
        data,
        {"measurements[*].value": 999},
        TEST_SEED,
    )

    assert result["measurements"][0]["value"] == 999
    assert result["measurements"][1]["value"] == 999


def test_nested_wildcard_override() -> None:
    data = {
        "devices": [
            {
                "measurements": [
                    {"value": 1},
                    {"value": 2},
                ]
            },
            {
                "measurements": [
                    {"value": 3},
                    {"value": 4},
                ]
            },
        ]
    }

    result = apply_overrides(
        data,
        {"devices[*].measurements[*].value": 999},
        TEST_SEED,
    )

    assert result["devices"][0]["measurements"][0]["value"] == 999
    assert result["devices"][0]["measurements"][1]["value"] == 999
    assert result["devices"][1]["measurements"][0]["value"] == 999
    assert result["devices"][1]["measurements"][1]["value"] == 999


def test_outer_wildcard_override() -> None:
    data = {
        "devices": [
            {"temperature": 10},
            {"temperature": 20},
        ]
    }

    result = apply_overrides(
        data,
        {"devices[*].temperature": -100},
        TEST_SEED,
    )

    assert result["devices"][0]["temperature"] == -100
    assert result["devices"][1]["temperature"] == -100


def test_wildcard_on_non_array_raises() -> None:
    data = {"device": {"value": 1}}

    with pytest.raises(OverridePathError):
        apply_overrides(data, {"device[*].value": 999}, TEST_SEED)


def test_double_wildcard_override() -> None:
    data = {
        "devices": [
            {"sensors": [{"value": 1}, {"value": 2}]},
            {"sensors": [{"value": 3}, {"value": 4}]},
        ]
    }

    result = apply_overrides(
        data,
        {"devices[*].sensors[*].value": 999},
        TEST_SEED,
    )

    assert result["devices"][0]["sensors"][0]["value"] == 999
    assert result["devices"][0]["sensors"][1]["value"] == 999
    assert result["devices"][1]["sensors"][0]["value"] == 999
    assert result["devices"][1]["sensors"][1]["value"] == 999


def test_overrides_can_create_missing_fields() -> None:
    data: dict[str, int] = {}

    result = apply_overrides(data, {"a.b": 1}, TEST_SEED)

    assert result == {"a": {"b": 1}}


def test_overrides_do_not_expand_arrays() -> None:
    data: dict[str, list[int]] = {"items": []}

    with pytest.raises(OverridePathError):
        apply_overrides(data, {"items[0]": 1}, TEST_SEED)


def test_override_replaces_structure_with_json() -> None:
    data = {"a": {"b": 1}}

    result = apply_overrides(data, {"a": {"x": 2}}, TEST_SEED)

    assert result["a"] == {"x": 2}


def test_seed_templating_plain_value() -> None:
    data = {"id": "original"}

    result = apply_overrides(data, {"id": "test-{SEED}"}, TEST_SEED)

    assert result["id"] == f"test-{TEST_SEED.label}"


def test_seed_templating_nested_field() -> None:
    data = {"a": {"b": "original"}}

    result = apply_overrides(data, {"a.b": "value-{SEED}"}, TEST_SEED)

    assert result["a"]["b"] == f"value-{TEST_SEED.label}"


def test_seed_templating_json_override() -> None:
    data = {"a": {"b": 1}}

    result = apply_overrides(
        data,
        {"a": {"id": "test-{SEED}"}},
        TEST_SEED,
    )

    assert result["a"] == {"id": f"test-{TEST_SEED.label}"}


def test_seed_templating_inside_nested_json_structure() -> None:
    data: dict[str, Any] = {"a": {}}

    result = apply_overrides(
        data,
        {"a": {"nested": {"id": "test-{SEED}"}}},
        TEST_SEED,
    )

    assert result["a"]["nested"]["id"] == f"test-{TEST_SEED.label}"


def test_seed_templating_list_of_strings() -> None:
    data = {"items": ["a", "b"]}

    result = apply_overrides(
        data,
        {"items": ["x-{SEED}", "y-{SEED}"]},
        TEST_SEED,
    )

    assert result["items"] == [
        f"x-{TEST_SEED.label}",
        f"y-{TEST_SEED.label}",
    ]


def test_seed_templating_list_of_objects() -> None:
    data: dict[str, Any] = {"items": [{}]}

    result = apply_overrides(
        data,
        {"items[0]": {"id": "item-{SEED}"}},
        TEST_SEED,
    )

    assert result["items"][0]["id"] == f"item-{TEST_SEED.label}"


def test_seed_templating_nested_object_inside_list() -> None:
    data: dict[str, Any] = {"items": [{}]}

    result = apply_overrides(
        data,
        {"items[0]": {"nested": {"id": "deep-{SEED}"}}},
        TEST_SEED,
    )

    assert result["items"][0]["nested"]["id"] == f"deep-{TEST_SEED.label}"


def test_seed_templating_mixed_nested_structure() -> None:
    data: dict[str, Any] = {"a": {}}

    result = apply_overrides(
        data,
        {
            "a": {
                "items": [
                    {"id": "one-{SEED}"},
                    {"id": "two-{SEED}"},
                ]
            }
        },
        TEST_SEED,
    )

    assert result["a"]["items"][0]["id"] == f"one-{TEST_SEED.label}"
    assert result["a"]["items"][1]["id"] == f"two-{TEST_SEED.label}"


def test_seed_templating_multiple_occurrences() -> None:
    data = {"id": ""}

    result = apply_overrides(
        data,
        {"id": "{SEED}-{SEED}-{SEED}"},
        TEST_SEED,
    )

    expected = f"{TEST_SEED.label}-{TEST_SEED.label}-{TEST_SEED.label}"
    assert result["id"] == expected

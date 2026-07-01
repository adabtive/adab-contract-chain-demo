import random
import re
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest

from contract_engine.domain.types import PrimitiveKind, PrimitiveType
from contract_engine.infrastructure.generators.format_generators import (
    generate_date,
    generate_datetime,
    generate_datetime_naive,
    generate_isoduration,
    generate_uuid,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
_DATETIME_NAIVE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
_ISODURATION_RE = re.compile(r"^P(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?$")

_STRING_FIELD = PrimitiveType(kind=PrimitiveKind.STRING)


def test_generate_date_format() -> None:
    value = generate_date(random.Random(1), _STRING_FIELD)
    assert _DATE_RE.match(value), f"Not a valid date: {value!r}"


def test_generate_date_is_valid_calendar_date() -> None:
    value = generate_date(random.Random(42), _STRING_FIELD)
    date.fromisoformat(value)


def test_generate_date_is_deterministic() -> None:
    assert generate_date(random.Random(7), _STRING_FIELD) == generate_date(random.Random(7), _STRING_FIELD)


def test_generate_datetime_naive_format() -> None:
    value = generate_datetime_naive(random.Random(1), _STRING_FIELD)
    assert _DATETIME_NAIVE_RE.match(value), f"Not a valid naive datetime: {value!r}"


def test_generate_datetime_naive_has_no_timezone() -> None:
    value = generate_datetime_naive(random.Random(1), _STRING_FIELD)
    assert "+" not in value
    assert value[-1] != "Z"


def test_generate_datetime_naive_is_deterministic() -> None:
    assert generate_datetime_naive(random.Random(7), _STRING_FIELD) == generate_datetime_naive(
        random.Random(7), _STRING_FIELD
    )


def test_generate_isoduration_format() -> None:
    value = generate_isoduration(random.Random(1), _STRING_FIELD)
    assert _ISODURATION_RE.match(value), f"Not a valid ISO duration: {value!r}"


def test_generate_isoduration_starts_with_p() -> None:
    assert generate_isoduration(random.Random(1), _STRING_FIELD).startswith("P")


def test_generate_isoduration_is_deterministic() -> None:
    assert generate_isoduration(random.Random(7), _STRING_FIELD) == generate_isoduration(
        random.Random(7), _STRING_FIELD
    )


def test_generate_datetime_still_works_with_field() -> None:
    value = generate_datetime(random.Random(1), _STRING_FIELD)
    assert _DATETIME_RE.match(value), f"Not a valid datetime: {value!r}"


def test_generate_uuid_still_works_with_field() -> None:
    value = generate_uuid(random.Random(1), _STRING_FIELD)
    uuid.UUID(value)


# --- generate_date bounds ---


def test_generate_date_respects_minimum_date() -> None:
    min_date = date(2024, 1, 1)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_date=min_date)
    assert date.fromisoformat(generate_date(random.Random(1), field)) >= min_date


def test_generate_date_respects_maximum_date() -> None:
    max_date = date(2000, 12, 31)
    field = PrimitiveType(kind=PrimitiveKind.STRING, maximum_date=max_date)
    assert date.fromisoformat(generate_date(random.Random(1), field)) <= max_date


def test_generate_date_respects_both_bounds() -> None:
    min_date = date(2024, 6, 1)
    max_date = date(2024, 6, 30)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_date=min_date, maximum_date=max_date)
    for seed in range(20):
        d = date.fromisoformat(generate_date(random.Random(seed), field))
        assert min_date <= d <= max_date


def test_generate_date_max_below_min_raises() -> None:
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_date=date(2025, 1, 1), maximum_date=date(2024, 1, 1))
    with pytest.raises(ValueError, match="maximum_date must be >= minimum_date"):
        generate_date(random.Random(1), field)


# --- generate_datetime_naive bounds ---


def test_generate_datetime_naive_respects_minimum_date_time() -> None:
    min_dt = datetime(2024, 1, 1, tzinfo=UTC)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_date_time=min_dt)
    value = datetime.fromisoformat(generate_datetime_naive(random.Random(1), field))
    assert value >= min_dt.replace(tzinfo=None)


def test_generate_datetime_naive_respects_maximum_date_time() -> None:
    max_dt = datetime(2000, 12, 31, tzinfo=UTC)
    field = PrimitiveType(kind=PrimitiveKind.STRING, maximum_date_time=max_dt)
    value = datetime.fromisoformat(generate_datetime_naive(random.Random(1), field))
    assert value <= max_dt.replace(tzinfo=None)


def test_generate_datetime_naive_max_below_min_raises() -> None:
    field = PrimitiveType(
        kind=PrimitiveKind.STRING,
        minimum_date_time=datetime(2025, 1, 1, tzinfo=UTC),
        maximum_date_time=datetime(2024, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="maximum_date_time must be >= minimum_date_time"):
        generate_datetime_naive(random.Random(1), field)


# --- generate_isoduration bounds ---


def _isoduration_to_seconds(value: str) -> int:
    m = re.match(r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$", value)
    assert m, f"Not a valid ISO duration: {value!r}"
    y, mo, w, d, h, mi, s = (int(x or 0) for x in m.groups())
    return (y * 365 + mo * 30 + w * 7 + d) * 86400 + h * 3600 + mi * 60 + s


def test_generate_isoduration_respects_bounds() -> None:
    min_dur = timedelta(hours=1)
    max_dur = timedelta(hours=3)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_duration=min_dur, maximum_duration=max_dur)
    for seed in range(20):
        secs = _isoduration_to_seconds(generate_isoduration(random.Random(seed), field))
        assert int(min_dur.total_seconds()) <= secs <= int(max_dur.total_seconds())


def test_generate_isoduration_respects_minimum_only() -> None:
    min_dur = timedelta(days=1)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_duration=min_dur)
    for seed in range(10):
        secs = _isoduration_to_seconds(generate_isoduration(random.Random(seed), field))
        assert secs >= int(min_dur.total_seconds())


def test_generate_isoduration_respects_maximum_only() -> None:
    max_dur = timedelta(minutes=5)
    field = PrimitiveType(kind=PrimitiveKind.STRING, maximum_duration=max_dur)
    for seed in range(10):
        secs = _isoduration_to_seconds(generate_isoduration(random.Random(seed), field))
        assert secs <= int(max_dur.total_seconds())


def test_generate_isoduration_pinned_duration() -> None:
    dur = timedelta(hours=1, minutes=30)
    field = PrimitiveType(kind=PrimitiveKind.STRING, minimum_duration=dur, maximum_duration=dur)
    secs = _isoduration_to_seconds(generate_isoduration(random.Random(1), field))
    assert secs == int(dur.total_seconds())


def test_generate_isoduration_max_below_min_raises() -> None:
    field = PrimitiveType(
        kind=PrimitiveKind.STRING,
        minimum_duration=timedelta(hours=2),
        maximum_duration=timedelta(hours=1),
    )
    with pytest.raises(ValueError, match="maximum_duration must be >= minimum_duration"):
        generate_isoduration(random.Random(1), field)


def test_generate_isoduration_unbounded_unchanged() -> None:
    assert generate_isoduration(random.Random(7), _STRING_FIELD) == generate_isoduration(
        random.Random(7), _STRING_FIELD
    )

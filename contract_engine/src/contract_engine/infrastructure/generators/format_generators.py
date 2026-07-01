from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import random
    from collections.abc import Callable

    from contract_engine.domain.types import PrimitiveType

    FormatGenerator = Callable[[random.Random, PrimitiveType], str]

_DEFAULT_MIN_TIMESTAMP = 0
_DEFAULT_MAX_TIMESTAMP = 2_000_000_000
_DEFAULT_MIN_DATE_ORD = datetime.fromtimestamp(_DEFAULT_MIN_TIMESTAMP, tz=UTC).date().toordinal()
_DEFAULT_MAX_DATE_ORD = datetime.fromtimestamp(_DEFAULT_MAX_TIMESTAMP, tz=UTC).date().toordinal()
_DEFAULT_MAX_DURATION_SECS = 5 * 365 * 86400


def generate_datetime(rng: random.Random, field: PrimitiveType) -> str:
    min_ts = int(field.minimum_date_time.timestamp()) if field.minimum_date_time is not None else _DEFAULT_MIN_TIMESTAMP
    max_ts = int(field.maximum_date_time.timestamp()) if field.maximum_date_time is not None else _DEFAULT_MAX_TIMESTAMP
    if max_ts < min_ts:
        raise ValueError("maximum_date_time must be >= minimum_date_time")
    return datetime.fromtimestamp(rng.randint(min_ts, max_ts), tz=UTC).isoformat()


def generate_date(rng: random.Random, field: PrimitiveType) -> str:
    min_ord = field.minimum_date.toordinal() if field.minimum_date is not None else _DEFAULT_MIN_DATE_ORD
    max_ord = field.maximum_date.toordinal() if field.maximum_date is not None else _DEFAULT_MAX_DATE_ORD
    if max_ord < min_ord:
        raise ValueError("maximum_date must be >= minimum_date")
    return date.fromordinal(rng.randint(min_ord, max_ord)).isoformat()


def generate_datetime_naive(rng: random.Random, field: PrimitiveType) -> str:
    min_ts = int(field.minimum_date_time.timestamp()) if field.minimum_date_time is not None else _DEFAULT_MIN_TIMESTAMP
    max_ts = int(field.maximum_date_time.timestamp()) if field.maximum_date_time is not None else _DEFAULT_MAX_TIMESTAMP
    if max_ts < min_ts:
        raise ValueError("maximum_date_time must be >= minimum_date_time")
    return (
        datetime.fromtimestamp(rng.randint(min_ts, max_ts), tz=UTC).replace(tzinfo=None).isoformat(timespec="seconds")
    )


def generate_isoduration(rng: random.Random, field: PrimitiveType) -> str:
    if field.minimum_duration is not None or field.maximum_duration is not None:
        min_secs = int(field.minimum_duration.total_seconds()) if field.minimum_duration is not None else 0
        max_secs = (
            int(field.maximum_duration.total_seconds())
            if field.maximum_duration is not None
            else _DEFAULT_MAX_DURATION_SECS
        )
        if max_secs < min_secs:
            raise ValueError("maximum_duration must be >= minimum_duration")
        total_secs = rng.randint(min_secs, max_secs)
        days, remainder = divmod(total_secs, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        date_part = f"{days}D" if days else ""
        time_part = f"{hours}H" if hours else ""
        time_part += f"{minutes}M" if minutes else ""
        time_part += f"{seconds}S" if seconds else ""
        if not date_part and not time_part:
            return "PT0S"
        return f"P{date_part}" + (f"T{time_part}" if time_part else "")

    years = rng.randint(0, 5)
    months = rng.randint(0, 11)
    days = rng.randint(0, 30)
    hours = rng.randint(0, 23)
    minutes = rng.randint(0, 59)
    seconds = rng.randint(0, 59)

    date_part = f"{years}Y" if years else ""
    date_part += f"{months}M" if months else ""
    date_part += f"{days}D" if days else ""

    time_part = f"{hours}H" if hours else ""
    time_part += f"{minutes}M" if minutes else ""
    time_part += f"{seconds}S" if seconds else ""

    if not date_part and not time_part:
        return "PT0S"

    return f"P{date_part}" + (f"T{time_part}" if time_part else "")


def generate_uuid(rng: random.Random, _field: PrimitiveType) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128)))


def generate_uri(rng: random.Random, _field: PrimitiveType) -> str:
    host = f"example{rng.randint(1, 1000)}.com"
    path = f"/resource/{rng.randint(1, 1000)}"
    return f"https://{host}{path}"


def generate_email(rng: random.Random, _field: PrimitiveType) -> str:
    user = f"user{rng.randint(1, 10000)}"
    domain = f"example{rng.randint(1, 100)}.com"
    return f"{user}@{domain}"


FORMAT_GENERATORS: dict[str, FormatGenerator] = {
    "date-time": generate_datetime,
    "date": generate_date,
    "datetime_naive": generate_datetime_naive,
    "isoduration": generate_isoduration,
    "uuid": generate_uuid,
    "uri": generate_uri,
    "email": generate_email,
}

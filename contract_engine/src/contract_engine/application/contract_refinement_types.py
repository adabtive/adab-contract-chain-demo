from datetime import date, datetime, timedelta
from typing import Any, TypedDict


class Constraint(TypedDict, total=False):
    const: Any
    minimum: float
    maximum: float
    min_length: int
    max_length: int
    enum: list[str | int | float | bool | None]
    format: str
    pattern: str
    one_of_filter: dict[str, Any]
    required: bool
    type: str | list[str]
    min_items: int
    max_items: int
    minimum_date_time: datetime
    maximum_date_time: datetime
    minimum_date: date
    maximum_date: date
    minimum_duration: timedelta
    maximum_duration: timedelta


Refinements = dict[str, Constraint]

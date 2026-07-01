import logging
import os
from collections import deque
from datetime import UTC, datetime
from typing import Literal

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("alert_engine")
app = FastAPI()

ALERT_SINK_URL = os.getenv("ALERT_SINK_URL", "http://alert-sink:8893")

THRESHOLDS: dict[str, dict[str, tuple[float, float]]] = {
    "air_quality": {"co2_ppm":       (800,  1500)},
    "climate":     {"temperature_c": (30,   38)},
    "noise":       {"db_spl":        (70,   85)},
}

alerts: deque = deque(maxlen=100)


class Stats(BaseModel):
    mean: float
    std_dev: float
    min: float
    max: float


class AggregatedWindow(BaseModel):
    sensor_id: str
    measurement_type: str
    window_start: str
    window_end: str
    sample_count: int
    metric: str
    stats: Stats


class AlertEvent(BaseModel):
    sensor_id: str
    triggered_at: str
    severity: Literal["info", "warning", "critical"]
    measurement_type: str
    metric: str
    value: float
    threshold: float


@app.get("/health")
def health():
    return {"status": "ok", "service": "alert_engine"}


@app.post("/evaluate")
async def evaluate(window: AggregatedWindow):
    thresholds = THRESHOLDS.get(window.measurement_type, {})
    warning_threshold, critical_threshold = thresholds.get(window.metric, (None, None))

    if warning_threshold is None:
        return {"received": True, "status": "ok"}

    value = window.stats.mean
    if value >= critical_threshold:
        severity = "critical"
        threshold = critical_threshold
    elif value >= warning_threshold:
        severity = "warning"
        threshold = warning_threshold
    else:
        return {"received": True, "status": "ok"}

    alert = AlertEvent(
        sensor_id=window.sensor_id,
        triggered_at=datetime.now(UTC).isoformat(),
        severity=severity,
        measurement_type=window.measurement_type,
        metric=window.metric,
        value=value,
        threshold=threshold,
    )

    alerts.append(alert.model_dump())
    logger.info("Alert fired: sensor=%s metric=%s value=%.2f severity=%s", window.sensor_id, window.metric, value, severity)

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{ALERT_SINK_URL}/notify", json=alert.model_dump(), timeout=5.0)
        except httpx.ConnectError:
            logger.error("Could not reach alert sink at %s", ALERT_SINK_URL)

    return {"received": True, "status": "ok"}


@app.get("/alerts")
def get_alerts():
    return {"alerts": list(alerts)}


@app.delete("/alerts")
def clear_alerts():
    alerts.clear()
    return {"cleared": True}

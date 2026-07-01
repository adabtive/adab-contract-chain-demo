import logging
import os
import statistics
from collections import deque
from typing import Annotated, Literal, Union

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger("aggregator")

app = FastAPI()

WINDOW_SIZE = 5
ALERT_ENGINE_URL = os.getenv("ALERT_ENGINE_URL", "http://alert-engine:8893")


class AirQualityMeasurements(BaseModel):
    measurement_type: Literal["air_quality"]
    co2_ppm: int
    pm25_ugm3: float
    voc_ppb: int


class ClimateMeasurements(BaseModel):
    measurement_type: Literal["climate"]
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float


class NoiseMeasurements(BaseModel):
    measurement_type: Literal["noise"]
    db_spl: float
    peak_frequency_hz: int


Measurements = Annotated[
    Union[AirQualityMeasurements, ClimateMeasurements, NoiseMeasurements],
    Field(discriminator="measurement_type"),
]


class SensorReading(BaseModel):
    sensor_id: str
    timestamp: str
    measurements: Measurements


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


PRIMARY_METRIC: dict[str, str] = {
    "air_quality": "co2_ppm",
    "climate": "temperature_c",
    "noise": "db_spl",
}

windows: dict[str, deque] = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "aggregator"}


@app.post("/ingest")
async def ingest(reading: SensorReading):
    key = f"{reading.sensor_id}:{reading.measurements.measurement_type}"

    if key not in windows:
        windows[key] = deque(maxlen=WINDOW_SIZE)

    windows[key].append(reading)

    if len(windows[key]) == WINDOW_SIZE:
        await emit_window(reading.sensor_id, reading.measurements.measurement_type, list(windows[key]))
        windows[key].clear()

    return {"accepted": True, "window_size": len(windows[key])}


async def emit_window(sensor_id: str, measurement_type: str, readings: list[SensorReading]):
    metric = PRIMARY_METRIC[measurement_type]
    values = [float(getattr(r.measurements, metric)) for r in readings]

    window = AggregatedWindow(
        sensor_id=sensor_id,
        measurement_type=measurement_type,
        window_start=readings[0].timestamp,
        window_end=readings[-1].timestamp,
        sample_count=len(values),
        metric=metric,
        stats=Stats(
            mean=statistics.mean(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            min=min(values),
            max=max(values),
        ),
    )

    logger.info("Emitting window: sensor=%s type=%s metric=%s mean=%.2f", sensor_id, measurement_type, metric, statistics.mean(values))
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{ALERT_ENGINE_URL}/evaluate", json=window.model_dump(), timeout=5.0)
        except httpx.ConnectError:
            logger.error("Could not reach alert engine at %s", ALERT_ENGINE_URL)

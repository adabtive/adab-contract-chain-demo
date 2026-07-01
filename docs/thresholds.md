# Thresholds and generated ranges

The alert engine evaluates the mean of a window against a `(warning, critical)` threshold pair per metric. The sensor producer generates values within a refinement range. Together they determine how often alerts fire during the demo.

## Alert engine thresholds

Defined in `services/alert_engine/app/main.py`:

| Measurement type | Metric | Warning | Critical |
|---|---|---|---|
| `air_quality` | `co2_ppm` | 800 | 1500 |
| `climate` | `temperature_c` | 30 | 38 |
| `noise` | `db_spl` | 70 | 85 |

An alert fires when `mean >= warning`. Severity is `critical` if `mean >= critical`, else `warning`.

## Producer refinements

Defined in `contract-server/sensor-producer.yaml`:

| Endpoint | Metric | Min | Max |
|---|---|---|---|
| `air-quality` | `co2_ppm` | 800 | 1500 |
| `air-quality` | `pm25_ugm3` | 5 | 80 |
| `climate` | `temperature_c` | 15 | 40 |
| `climate` | `humidity_pct` | 30 | 85 |
| `noise` | `db_spl` | 55 | 95 |

Each endpoint is pinned to a single `sensor_id`:
- `air-quality` → `sensor-air-01`
- `climate` → `sensor-climate-01`
- `noise` → `sensor-noise-01`

This keeps the aggregator window filling on repeated clicks (window is keyed by `sensor_id + measurement_type`).

## What fires during the demo

Windows are 5 readings. Mean is roughly `(min + max) / 2` — Gaussian-ish around the middle.

| Endpoint | Expected mean | Fires? |
|---|---|---|
| `air-quality` | ~1150 | **Always warning.** Min value equals the warning threshold, so the mean is always above it. Critical is possible but rare. |
| `climate` | ~27 | **Sometimes warning.** Warning threshold sits inside the range, so it fires when the RNG runs hot. |
| `noise` | ~75 | **Usually warning.** Mean is slightly above the threshold. |

Reliable demo path: fire 5x `air-quality` → guaranteed alert every window.

## Tuning

To force critical alerts on `air-quality`, raise the minimum to `1500` in the producer refinement. To break the alert entirely, drop the maximum below `800`.

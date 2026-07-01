# Integration tests

Two Robot Framework suites, both aimed at the aggregator. The pair tells one story:
what testing looks like with and without a contract engine.

## Prerequisites

The aggregator must be reachable:

```bash
docker compose -f docker-compose.app.yml up -d --build aggregator
```

## Run in Docker (no local Python needed)

`--build` is important: the Robot files are baked into the image via `COPY`, so
without it you'll re-run whatever was in the image last time. Cheap to always pass.

Both suites:

```bash
docker compose -f docker-compose.tests.yml run --build --rm tests
```

Just suite 1 (manual payloads):

```bash
docker compose -f docker-compose.tests.yml run --build --rm tests \
  robot --outputdir /workspace/results integration-tests/01_manual_payloads.robot
```

Just suite 2 (contract-generated):

```bash
docker compose -f docker-compose.tests.yml run --build --rm tests \
  robot --outputdir /workspace/results integration-tests/02_contract_generated.robot
```

The container joins the `chain` network, hits `http://aggregator:8000`, and drops
`log.html` / `report.html` / `output.xml` into `./results/` on the host.

## Run locally (if you have Python)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r integration-tests/requirements.txt
robot integration-tests/
```

Or one suite at a time:

```bash
robot integration-tests/01_manual_payloads.robot
robot integration-tests/02_contract_generated.robot
```

## The two suites

### `01_manual_payloads.robot` — without the contract engine

Hand-written JSON fixtures inline in the suite. Covers valid air-quality and climate
readings, plus a few rejection cases (missing `sensor_id`, missing `co2_ppm`, unknown
`measurement_type`).

Every payload is a frozen copy of the current schema. Rename a field in
`sensor_reading.json` and the valid cases don't just fail — they may keep passing
against a stale definition until something downstream breaks. This is the pain.

### `02_contract_generated.robot` — with the contract engine

Uses `ContractEngineKeywords.Generate Contract Instances` to produce 10 valid
instances per measurement type (air-quality, climate, noise), then POSTs each to
the aggregator.

The instances come from `sensor_reading.json` directly. Change the schema and the
suite picks it up on the next run — no fixture edits, no stale data.

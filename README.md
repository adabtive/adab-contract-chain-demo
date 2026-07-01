# adab-contract-chain-demo

A small HTTP chain that ingests fake sensor readings, aggregates them into windows,
fires alerts on threshold breaches, and validates the alerts against a JSON Schema
contract at the output boundary.

Built as a demo for the `contract-engine` and `contract-server` tools.

```
sensor-producer (fake)  →  aggregator (real)  →  alert-engine (real)  →  alert-validator (fake)
```

- **fakes** run via `contract-server` on ports `8891` / `8892` / `8893`
- **real services** are FastAPI apps on `8000` / `8001`
- **contracts** live in `contracts/` — six JSON Schema files
- **integration-tests** exercise the aggregator with hand-written and generated payloads

See `docs/architecture.md` for diagrams, `docs/thresholds.md` for alert math.

## Bring the stack up

```bash
docker compose -f docker-compose.app.yml -f docker-compose.contract-server.yml up --build
```

Only the aggregator is needed for the test suites:

```bash
docker compose -f docker-compose.app.yml up -d --build aggregator
```

## Run the tests (Docker, no local Python)

```bash
docker compose -f docker-compose.tests.yml run --build --rm tests
```

The `--build` is important — Robot files are baked into the image via `COPY`, so
without it you re-run the previous image. Reports (`log.html`, `report.html`,
`output.xml`) land in `./results/`.

## Run the tests locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r integration-tests/requirements.txt
robot integration-tests/
```

## The two test suites

- `01_manual_payloads.robot` — hand-written JSON. What testing looks like without a
  contract engine. Rename a field in the schema, every fixture rots.
- `02_contract_generated.robot` — payloads generated from `sensor_reading.json` at
  runtime. Schema changes propagate; no fixture edits.

Details in `integration-tests/README.md`.

## Ports

| Service            | Port | Kind |
|---|---|---|
| sensor-producer    | 8891 | fake (contract-server) |
| alert-responder    | 8892 | fake (contract-server) |
| alert-validator    | 8893 | fake (contract-server) |
| aggregator         | 8000 | real (FastAPI) |
| alert-engine       | 8001 | real (FastAPI) |

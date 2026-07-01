FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# contract_engine is a sibling repo, copied to match the relative path ../contract_engine
COPY contract_engine/ /contract_engine/

WORKDIR /app
COPY adab-contract-server/pyproject.toml adab-contract-server/uv.lock adab-contract-server/README.md ./
COPY adab-contract-server/src/ ./src/

RUN uv sync --no-dev --frozen && \
    useradd --create-home --uid 10001 appuser && \
    chown -R appuser:appuser /app /contract_engine

USER appuser

ENTRYPOINT ["uv", "run", "contract-server"]

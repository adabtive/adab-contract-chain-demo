FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /workspace
COPY contract_engine/ contract_engine/
COPY adab-contract-server/ adab-contract-server/

WORKDIR /workspace/adab-contract-server
RUN uv sync --no-dev

EXPOSE 8891
ENTRYPOINT [".venv/bin/contract-server"]

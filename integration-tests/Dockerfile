FROM python:3.13-slim

WORKDIR /workspace

COPY contract_engine/ contract_engine/
COPY contracts/ contracts/
COPY integration-tests/ integration-tests/

RUN pip install --no-cache-dir robotframework robotframework-requests \
    && pip install --no-cache-dir -e contract_engine

CMD ["robot", "integration-tests/"]

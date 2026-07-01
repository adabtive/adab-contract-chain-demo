*** Settings ***
Documentation    Aggregator tested with payloads generated from the contract.
...              The contract engine reads sensor_reading.json and produces valid instances
...              on the fly. Change the schema and these tests still align — no fixture edits.
Resource         resources/chain.resource
Library          contract_engine.robot_adapter.keywords.ContractEngineKeywords

*** Variables ***
${SENSOR_CONTRACT}    ${CONTRACTS_DIR}/sensor_reading.json

*** Test Cases ***
Ten Generated Air-Quality Readings Are Accepted
    ${refinements}=    Create Dictionary
    ...    measurements    ${{ {"one_of_filter": {"measurement_type": "air_quality"}} }}
    ${readings}=    Generate Contract Instances
    ...    contract=${SENSOR_CONTRACT}
    ...    count=10
    ...    seed=demo-air
    ...    refinements=${refinements}
    ...    base_path=${CONTRACTS_DIR}
    FOR    ${reading}    IN    @{readings}
        POST    ${AGGREGATOR_URL}/ingest    json=${reading.data}    expected_status=200
    END

Ten Generated Climate Readings Are Accepted
    ${refinements}=    Create Dictionary
    ...    measurements    ${{ {"one_of_filter": {"measurement_type": "climate"}} }}
    ${readings}=    Generate Contract Instances
    ...    contract=${SENSOR_CONTRACT}
    ...    count=10
    ...    seed=demo-climate
    ...    refinements=${refinements}
    ...    base_path=${CONTRACTS_DIR}
    FOR    ${reading}    IN    @{readings}
        POST    ${AGGREGATOR_URL}/ingest    json=${reading.data}    expected_status=200
    END

Ten Generated Noise Readings Are Accepted
    ${refinements}=    Create Dictionary
    ...    measurements    ${{ {"one_of_filter": {"measurement_type": "noise"}} }}
    ${readings}=    Generate Contract Instances
    ...    contract=${SENSOR_CONTRACT}
    ...    count=10
    ...    seed=demo-noise
    ...    refinements=${refinements}
    ...    base_path=${CONTRACTS_DIR}
    FOR    ${reading}    IN    @{readings}
        POST    ${AGGREGATOR_URL}/ingest    json=${reading.data}    expected_status=200
    END

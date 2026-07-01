*** Settings ***
Documentation    Aggregator tested with hand-written payloads.
...              This is what tests look like without a contract engine.
...              Every fixture below is a copy of the current schema, frozen in time.
...              Rename `co2_ppm` in the contract and every valid case here silently rots.
Resource         resources/chain.resource

*** Test Cases ***
Valid Air-Quality Reading Is Accepted
    ${measurements}=    Create Dictionary
    ...    measurement_type=air_quality
    ...    co2_ppm=${900}
    ...    pm25_ugm3=${12.5}
    ...    voc_ppb=${150}
    ${payload}=    Create Dictionary
    ...    sensor_id=sensor-air-01
    ...    timestamp=2026-07-01T10:00:00Z
    ...    measurements=${measurements}
    ${response}=    POST    ${AGGREGATOR_URL}/ingest    json=${payload}    expected_status=200
    Should Be Equal    ${response.json()}[accepted]    ${TRUE}

Valid Climate Reading Is Accepted
    ${measurements}=    Create Dictionary
    ...    measurement_type=climate
    ...    temperature_c=${22.4}
    ...    humidity_pct=${55.0}
    ...    pressure_hpa=${1013.2}
    ${payload}=    Create Dictionary
    ...    sensor_id=sensor-climate-01
    ...    timestamp=2026-07-01T10:00:00Z
    ...    measurements=${measurements}
    ${response}=    POST    ${AGGREGATOR_URL}/ingest    json=${payload}    expected_status=200
    Should Be Equal    ${response.json()}[accepted]    ${TRUE}

Reading Missing Sensor Id Is Rejected
    ${measurements}=    Create Dictionary
    ...    measurement_type=air_quality
    ...    co2_ppm=${900}
    ...    pm25_ugm3=${12.5}
    ...    voc_ppb=${150}
    ${payload}=    Create Dictionary
    ...    timestamp=2026-07-01T10:00:00Z
    ...    measurements=${measurements}
    POST    ${AGGREGATOR_URL}/ingest    json=${payload}    expected_status=422

Air-Quality Reading Missing Co2 Is Rejected
    ${measurements}=    Create Dictionary
    ...    measurement_type=air_quality
    ...    pm25_ugm3=${12.5}
    ...    voc_ppb=${150}
    ${payload}=    Create Dictionary
    ...    sensor_id=sensor-air-01
    ...    timestamp=2026-07-01T10:00:00Z
    ...    measurements=${measurements}
    POST    ${AGGREGATOR_URL}/ingest    json=${payload}    expected_status=422

Unknown Measurement Type Is Rejected
    ${measurements}=    Create Dictionary
    ...    measurement_type=radiation
    ...    sievert=${0.01}
    ${payload}=    Create Dictionary
    ...    sensor_id=sensor-x-01
    ...    timestamp=2026-07-01T10:00:00Z
    ...    measurements=${measurements}
    POST    ${AGGREGATOR_URL}/ingest    json=${payload}    expected_status=422

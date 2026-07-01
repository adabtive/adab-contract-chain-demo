*** Settings ***
Library    RequestsLibrary
Library    Collections

*** Variables ***
${AGGREGATOR_URL}    %{AGGREGATOR_URL=http://localhost:8000}
${CONTRACTS_DIR}     %{CONTRACTS_DIR=${CURDIR}/../../contracts}

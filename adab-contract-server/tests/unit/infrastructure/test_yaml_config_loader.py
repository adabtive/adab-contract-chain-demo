import textwrap

import pytest

from contract_server.domain.config import EndpointType
from contract_server.infrastructure.config.yaml_config_loader import YamlConfigLoader


def test_load_full_config(tmp_path):
    yaml_content = textwrap.dedent("""
        host: "127.0.0.1"
        port: 9000
        outgoing_base_url: "http://localhost:8000"
        contracts_dir: "./contracts"
        endpoints:
          validate_a:
            type: validate
            contract: a.json
          gen_b:
            type: generate
            contract: b.json
            destination:
              path: /recv
    """)
    config_file = tmp_path / "mock.yaml"
    config_file.write_text(yaml_content)

    config = YamlConfigLoader().load(str(config_file))

    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert config.endpoints["validate_a"].type == EndpointType.VALIDATE
    assert config.endpoints["gen_b"].destination is not None
    assert config.endpoints["gen_b"].destination.path == "/recv"


def test_load_defaults(tmp_path):
    yaml_content = textwrap.dedent("""
        outgoing_base_url: "http://localhost:8000"
        endpoints: {}
    """)
    config_file = tmp_path / "mock.yaml"
    config_file.write_text(yaml_content)

    config = YamlConfigLoader().load(str(config_file))

    assert config.host == "0.0.0.0"  # noqa: S104
    assert config.port == 8877
    assert config.contracts_dir == "./contracts"


def test_generate_without_destination_fails(tmp_path):
    from pydantic import ValidationError

    yaml_content = textwrap.dedent("""
        outgoing_base_url: "http://localhost:8000"
        endpoints:
          bad:
            type: generate
            contract: b.json
    """)
    config_file = tmp_path / "mock.yaml"
    config_file.write_text(yaml_content)

    with pytest.raises(ValidationError):
        YamlConfigLoader().load(str(config_file))


def test_load_with_refinements_and_overrides(tmp_path):
    yaml_content = textwrap.dedent("""
        outgoing_base_url: "http://localhost:8000"
        endpoints:
          gen_b:
            type: generate
            contract: b.json
            destination:
              path: /recv
            overrides:
              count: 99
    """)
    config_file = tmp_path / "mock.yaml"
    config_file.write_text(yaml_content)

    config = YamlConfigLoader().load(str(config_file))

    assert config.endpoints["gen_b"].overrides == {"count": 99}


def test_load_respond_endpoint(tmp_path):
    yaml_content = textwrap.dedent("""
        outgoing_base_url: "http://localhost:8000"
        endpoints:
          get_item:
            type: respond
            method: GET
            contract: a.json
            status_code: 200
    """)
    config_file = tmp_path / "mock.yaml"
    config_file.write_text(yaml_content)

    config = YamlConfigLoader().load(str(config_file))

    ep = config.endpoints["get_item"]
    assert ep.type == EndpointType.RESPOND
    assert ep.method == "GET"
    assert ep.status_code == 200

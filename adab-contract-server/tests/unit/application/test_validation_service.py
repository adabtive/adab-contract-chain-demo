import pytest

from contract_server.application.validation_service import ValidationService
from contract_server.domain.errors import EndpointTypeMismatchError, UnknownEndpointError
from contract_server.domain.history import EventKind


def test_valid_message_returns_valid(server_config, engine, event_bus):
    result = ValidationService(server_config, engine, event_bus).validate("validate_a", {"name": "foo", "value": 42})
    assert result.valid
    assert result.errors == []


def test_validate_publishes_event(server_config, engine, event_bus):
    ValidationService(server_config, engine, event_bus).validate("validate_a", {"name": "foo", "value": 42})
    events = event_bus.history("validate_a")
    assert len(events) == 1
    assert events[0].kind == EventKind.VALIDATE
    assert events[0].valid is True


def test_invalid_message_publishes_event(server_config, engine, event_bus):
    ValidationService(server_config, engine, event_bus).validate("validate_a", {"name": "foo"})
    events = event_bus.history("validate_a")
    assert len(events) == 1
    assert events[0].valid is False


def test_invalid_message_returns_errors(server_config, engine, event_bus):
    result = ValidationService(server_config, engine, event_bus).validate("validate_a", {"name": "foo"})
    assert not result.valid
    assert any("value" in e.message or "value" in e.location for e in result.errors)


def test_extra_field_fails(server_config, engine, event_bus):
    result = ValidationService(server_config, engine, event_bus).validate(
        "validate_a", {"name": "foo", "value": 1, "extra": "x"}
    )
    assert not result.valid


def test_wrong_type_fails(server_config, engine, event_bus):
    result = ValidationService(server_config, engine, event_bus).validate(
        "validate_a", {"name": "foo", "value": "not-a-number"}
    )
    assert not result.valid


def test_unknown_endpoint_raises(server_config, engine, event_bus):
    with pytest.raises(UnknownEndpointError):
        ValidationService(server_config, engine, event_bus).validate("nonexistent", {})


def test_generate_endpoint_raises_type_mismatch(server_config, engine, event_bus):
    with pytest.raises(EndpointTypeMismatchError):
        ValidationService(server_config, engine, event_bus).validate("gen_b", {})

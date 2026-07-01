def test_valid_message_returns_200(client):
    response = client.post("/validate_a", json={"name": "foo", "value": 42})
    assert response.status_code == 200
    assert response.json() == {"valid": True}


def test_missing_required_field_returns_400(client):
    response = client.post("/validate_a", json={"name": "foo"})
    assert response.status_code == 400
    body = response.json()
    assert body["valid"] is False
    assert any("value" in e["message"] or "value" in e["location"] for e in body["errors"])


def test_wrong_type_returns_400(client):
    response = client.post("/validate_a", json={"name": "foo", "value": "not-a-number"})
    assert response.status_code == 400
    assert response.json()["valid"] is False


def test_additional_property_returns_400(client):
    response = client.post("/validate_a", json={"name": "foo", "value": 1, "extra": "x"})
    assert response.status_code == 400


def test_unknown_endpoint_returns_404(client):
    response = client.post("/nonexistent", json={})
    assert response.status_code == 404

def test_emit_returns_200_and_sent_true(client, mock_http):  # noqa: ARG001
    response = client.post("/gen_b")
    assert response.status_code == 200
    assert response.json()["sent"] is True


def test_emit_posts_contract_valid_payload_to_destination(client, mock_http):
    client.post("/gen_b")

    mock_http.request.assert_called_once()
    _method, url, payload = mock_http.request.call_args.args
    assert url == "http://localhost:8000/recv"
    assert isinstance(payload.get("id"), str)
    assert isinstance(payload.get("count"), int)
    assert payload["count"] >= 0


def test_emit_502_when_destination_fails(client, mock_http):
    from contract_server.application.interfaces.http_client import HttpResponse

    mock_http.request.return_value = HttpResponse(status_code=503, body={})

    response = client.post("/gen_b")
    assert response.status_code == 502


def test_unknown_endpoint_returns_404(client):
    response = client.post("/nonexistent_generate")
    assert response.status_code == 404

def test_start_session_returns_201_with_session_id(client):
    response = client.post("/sessions", json={"endpoint": "gen_b", "interval_ms": 500})
    assert response.status_code == 201
    assert "session_id" in response.json()


def test_start_session_missing_interval_returns_422(client):
    response = client.post("/sessions", json={"endpoint": "gen_b"})
    assert response.status_code == 422


def test_start_session_missing_endpoint_returns_422(client):
    response = client.post("/sessions", json={"interval_ms": 500})
    assert response.status_code == 422


def test_list_sessions_returns_started_session(client):
    client.post("/sessions", json={"endpoint": "gen_b", "interval_ms": 500})

    response = client.get("/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["endpoint_name"] == "gen_b"
    assert sessions[0]["interval_ms"] == 500
    assert sessions[0]["state"] == "running"


def test_stop_session_returns_204(client):
    start = client.post("/sessions", json={"endpoint": "gen_b", "interval_ms": 500})
    session_id = start.json()["session_id"]

    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 204


def test_stop_session_marks_it_stopped(client):
    start = client.post("/sessions", json={"endpoint": "gen_b", "interval_ms": 500})
    session_id = start.json()["session_id"]
    client.delete(f"/sessions/{session_id}")

    sessions = client.get("/sessions").json()
    assert sessions[0]["state"] == "stopped"


def test_stop_unknown_session_returns_404(client):
    response = client.delete("/sessions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_start_session_with_period_and_jitter(client):
    response = client.post(
        "/sessions",
        json={
            "endpoint": "gen_b",
            "interval_ms": 200,
            "period": "PT1H",
            "jitter_ms": 50,
        },
    )
    assert response.status_code == 201

    sessions = client.get("/sessions").json()
    assert sessions[0]["period"] == "PT1H"
    assert sessions[0]["jitter_ms"] == 50

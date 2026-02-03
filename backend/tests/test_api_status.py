def test_api_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert data.get("ok") is True

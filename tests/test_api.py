def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data

def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"

def test_bad_age_is_422(client, good_row):
    response = client.post("/v1/predict", json={**good_row, "Age": -1})
    assert response.status_code == 422

def test_missing_column_is_422(client, good_row):
    row = dict(good_row)
    del row["Age"]
    response = client.post("/v1/predict", json=row)
    assert response.status_code == 422

def test_extra_column_is_422(client, good_row):
    good_row["extra"] = 1
    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 422
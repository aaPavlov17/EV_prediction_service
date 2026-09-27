def test_predict_smoke(client, good_row):
    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["score"] <= 1
    assert data["will_buy"] in [True, False]
    assert "model_version" in data
    assert "request_id" in data
    assert data["latency"] >= 0

def test_repeated_predictions_agree(client, good_row):
    s1 = client.post("/v1/predict", json=good_row).json()["score"]
    s2 = client.post("/v1/predict", json=good_row).json()["score"]
    assert abs(s1 - s2) < 1e-12

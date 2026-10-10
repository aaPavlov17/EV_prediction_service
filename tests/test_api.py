import logging
from unittest.mock import Mock
from uuid import UUID

import psycopg
import pytest

from ev import db


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
    assert str(UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
    data = response.json()
    assert set(data) == {"detail"}
    error = data["detail"][0]
    assert error["loc"] == ["body", "Age"]
    assert error["type"] == "greater_than_equal"
    assert error["input"] == -1

def test_missing_column_is_422(client, good_row):
    row = dict(good_row)
    del row["Age"]
    response = client.post("/v1/predict", json=row)
    assert response.status_code == 422

def test_extra_column_is_422(client, good_row):
    good_row["extra"] = 1
    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 422


def test_validation_response_survives_database_failure(client, good_row, monkeypatch, caplog):
    save_prediction = Mock(side_effect=psycopg.OperationalError("database unavailable"))
    monkeypatch.setattr(db, "save_prediction", save_prediction)

    with caplog.at_level(logging.ERROR):
        response = client.post("/v1/predict", json={**good_row, "Age": -1})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "Age"]
    save_prediction.assert_called_once()
    assert "database unavailable" in caplog.text


@pytest.mark.parametrize(
    ("request_kwargs", "expected_features"),
    [
        ({}, None),
        ({"json": []}, []),
        (
            {"content": '{"Age": 30}', "headers": {"Content-Type": "text/plain"}},
            {"raw_body": '{"Age": 30}'},
        ),
    ],
    ids=["empty-body", "wrong-json-shape", "unsupported-content-type"],
)
def test_invalid_body_is_logged(client, monkeypatch, request_kwargs, expected_features):
    saved = []

    def capture_prediction(request_id, features, score, model_version, latency, status_code):
        saved.append(
            {
                "request_id": request_id,
                "features": features,
                "score": score,
                "model_version": model_version,
                "latency": latency,
                "status_code": status_code,
            }
        )

    monkeypatch.setattr(db, "save_prediction", capture_prediction)

    response = client.post("/v1/predict", **request_kwargs)

    assert response.status_code == 422
    assert response.json()["detail"]
    assert len(saved) == 1
    assert saved[0]["request_id"] == response.headers["X-Request-ID"]
    assert str(UUID(saved[0]["request_id"])) == saved[0]["request_id"]
    assert saved[0]["features"] == expected_features
    assert saved[0]["score"] is None
    assert saved[0]["status_code"] == 422
    assert saved[0]["latency"] >= 0
    assert saved[0]["model_version"] == client.app.state.model_version

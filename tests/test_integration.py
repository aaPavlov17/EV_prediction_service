import psycopg
import pytest

from ev.config import settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        settings.db_url is None,
        reason="DB_URL is not configured; set it in the environment or .env",
    ),
]


def test_prediction_is_logged(client, good_row):
    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 200, response.text
    body = response.json()
    assert response.headers["X-Request-ID"] == body["request_id"]

    with psycopg.connect(settings.db_url) as conn:
        row = conn.execute(
            "SELECT model_version, score, features, status_code "
            "FROM predictions WHERE request_id = %s",
            (body["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == body["model_version"]
    assert row[1] == pytest.approx(body["score"])
    assert row[2] == good_row
    assert row[3] == 200


@pytest.mark.parametrize(
    ("invalid_request", "error_type", "error_field"),
    [
        pytest.param("negative_age", "greater_than_equal", "Age", id="negative-age"),
        pytest.param("missing_age", "missing", "Age", id="missing-age"),
        pytest.param("extra_field", "extra_forbidden", "extra", id="extra-field"),
        pytest.param("malformed_json", "json_invalid", None, id="malformed-json"),
    ],
)
def test_invalid_prediction_is_logged(client, good_row, invalid_request, error_type, error_field):
    payload = dict(good_row)
    if invalid_request == "negative_age":
        payload["Age"] = -1
    elif invalid_request == "missing_age":
        del payload["Age"]
    elif invalid_request == "extra_field":
        payload["extra"] = 1

    if invalid_request == "malformed_json":
        raw_body = '{"Age": -1,'
        response = client.post(
            "/v1/predict", content=raw_body, headers={"Content-Type": "application/json"}
        )
        expected_features = {"raw_body": raw_body}
    else:
        response = client.post("/v1/predict", json=payload)
        expected_features = payload

    assert response.status_code == 422, response.text
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["type"] == error_type
    assert errors[0]["msg"]
    if error_field is not None:
        assert errors[0]["loc"] == ["body", error_field]
    else:
        assert errors[0]["loc"][0] == "body"

    request_id = response.headers["X-Request-ID"]
    with psycopg.connect(settings.db_url) as conn:
        rows = conn.execute(
            "SELECT model_version, score, features, latency, status_code "
            "FROM predictions WHERE request_id = %s",
            (request_id,),
        ).fetchall()

    assert len(rows) == 1
    model_version, score, features, latency, status_code = rows[0]
    assert model_version == client.app.state.model_version
    assert score is None
    assert features == expected_features
    assert latency >= 0
    assert status_code == 422

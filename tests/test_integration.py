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

    with psycopg.connect(settings.db_url) as conn:
        row = conn.execute(
            "SELECT model_version, score, features "
            "FROM predictions WHERE request_id = %s",
            (body["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == body["model_version"]
    assert row[1] == pytest.approx(body["score"])
    assert row[2] == good_row

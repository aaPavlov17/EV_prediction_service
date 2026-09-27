import psycopg
from psycopg.types.json import Json

from ev.config import settings

DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    request_id UUID PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT NOW(),
    model_version TEXT NOT NULL,
    features JSON NOT NULL,
    score FLOAT NOT NULL,
    latency FLOAT NOT NULL,
    status_code INT NOT NULL
)"""

def init():
    if settings.db_url is None:
        return
    with psycopg.connect(settings.db_url) as conn:
        conn.execute(DDL)

def save_prediction(request_id: str, features: dict, score: float, model_version: str, latency: float, status_code: int):
    if settings.db_url is None:
        return
    with psycopg.connect(settings.db_url) as conn:
        conn.execute(
            "INSERT INTO predictions (request_id, model_version, features, score, latency, status_code) VALUES (%s, %s, %s, %s, %s, %s)",
            (request_id, model_version, Json(features), score, latency, status_code)
        )
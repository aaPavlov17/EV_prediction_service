import logging

import psycopg
from psycopg.types.json import Json
from pydantic import JsonValue

from ev.config import settings

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    request_id UUID PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT NOW(),
    model_version TEXT NOT NULL,
    features JSON NOT NULL,
    score FLOAT,
    latency FLOAT NOT NULL,
    status_code INT NOT NULL
)"""

def init():
    if settings.db_url is None:
        return
    with psycopg.connect(settings.db_url) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(7001)")
        conn.execute(DDL)
        conn.execute("ALTER TABLE predictions ALTER COLUMN score DROP NOT NULL")

def save_prediction(
    request_id: str,
    features: JsonValue,
    score: float | None,
    model_version: str,
    latency: float,
    status_code: int,
):
    if settings.db_url is None:
        return
    with psycopg.connect(settings.db_url) as conn:
        conn.execute(
            "INSERT INTO predictions "
            "(request_id, model_version, features, score, latency, status_code) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (request_id, model_version, Json(features), score, latency, status_code)
        )


def save_rejected_prediction(
    request_id: str,
    features: JsonValue,
    model_version: str,
    latency: float,
):
    try:
        save_prediction(
            request_id,
            features,
            score=None,
            model_version=model_version,
            latency=latency,
            status_code=422,
        )
    except Exception:
        logger.exception("Failed to log rejected prediction %s", request_id)

import time
import uuid
import joblib

import pandas as pd

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from ev.config import settings
from ev import db

class Features(BaseModel):
    model_config = {"extra": "forbid"}

    Age: int = Field(ge=1, le=100)
    Annual_Income_USD: float
    Daily_Commute_km: float
    Number_of_Cars_Owned: float
    Charging_Stations_Near_Home: float
    Charging_Stations_Near_Work: float
    Environmental_Concern_Level: float
    Gender: str
    City_Type: str
    Current_Car_Type: str
    Home_Charging_Possible: str
    Subsidy_Available: str
    Range_Anxiety_Level: str
    


class Prediction(BaseModel):
    score: float
    will_buy: bool
    model_version: str
    request_id: str
    latency: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load(settings.model_path)
    print(bundle)
    app.state.pipeline = bundle["pipeline"]
    app.state.meta = bundle["metadata"]
    app.state.model_version = bundle["metadata"]["model_version"]

    db.init()
    yield
    app.state.pipeline = None

app = FastAPI(title="EV", version=1.0, lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "model_version": getattr(app.state, "model_version", "unknown")}

@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", "None") is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return {"status": "ready"}

@app.post("/v1/predict", status_code=200)
def predict(x: Features, bg: BackgroundTasks):
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())
    payload = x.model_dump()
    df = pd.DataFrame([payload]).reindex(columns=app.state.meta["features"])

    score = float(app.state.pipeline.predict_proba(df)[0, 1])
    latency = round(time.perf_counter() - t0, 2) * 1000

    bg.add_task(db.save_prediction, request_id, payload, score, app.state.model_version, latency, status_code=200)

    will_buy = score >= app.state.meta["threshold"]
    return Prediction(score=score, will_buy=will_buy, model_version=app.state.model_version, request_id=request_id, latency=latency)

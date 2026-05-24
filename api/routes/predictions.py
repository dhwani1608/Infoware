from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.common import get_predictor
from api.schemas.prediction import DailyPredictionRequest, DailyPredictionResponse, DynamicRerouteRequest, WeeklyPredictionRequest
from api.services.prediction_service import PredictionService
from database.db import get_db
from model.trainer import train_models


router = APIRouter(tags=["predictions"])


@router.post("/predict/daily", response_model=DailyPredictionResponse)
async def predict_daily(payload: DailyPredictionRequest, db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    service = PredictionService(predictor)
    try:
        return service.predict_daily(db, payload.driver_id, payload.date, payload.locations)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/predict/weekly")
async def predict_weekly(payload: WeeklyPredictionRequest, db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    service = PredictionService(predictor)
    try:
        return service.predict_weekly(db, payload.driver_id, payload.week)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/retrain")
async def retrain_models():
    metrics = train_models()
    return {"status": "success", "metrics": metrics}


@router.post("/reroute/dynamic", response_model=DailyPredictionResponse)
async def reroute_dynamic(payload: DynamicRerouteRequest, db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    service = PredictionService(predictor)
    try:
        return service.reroute_dynamic(
            db,
            payload.driver_id,
            payload.date,
            payload.current_stop,
            payload.remaining_stops,
            payload.traffic_level,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

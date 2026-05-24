from datetime import date
from pydantic import BaseModel, Field


class DailyPredictionRequest(BaseModel):
    driver_id: str = Field(..., examples=["D1"])
    date: date
    locations: list[str] = Field(..., min_length=1)


class DailyPredictionResponse(BaseModel):
    recommended_route: list[str]
    predicted_time: str
    confidence: float
    total_distance_km: float
    route_efficiency_score: float


class WeeklyPredictionRequest(BaseModel):
    driver_id: str
    week: str = Field(..., examples=["2026-W20"])


class DynamicRerouteRequest(BaseModel):
    driver_id: str
    date: date
    current_stop: str
    remaining_stops: list[str] = Field(..., min_length=1)
    traffic_level: str = Field(default="high", examples=["high", "medium", "low"])

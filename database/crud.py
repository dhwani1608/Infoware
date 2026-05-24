import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import models


def get_drivers(db: Session):
    return db.query(models.Driver).all()


def get_locations(db: Session):
    return db.query(models.Location).all()


def upsert_driver(db: Session, driver_id: str, name: str, region: str, efficiency: float) -> models.Driver:
    obj = db.get(models.Driver, driver_id)
    if not obj:
        obj = models.Driver(id=driver_id, name=name, home_region=region, efficiency_score=efficiency)
        db.add(obj)
    else:
        obj.name = name
        obj.home_region = region
        obj.efficiency_score = efficiency
    db.commit()
    db.refresh(obj)
    return obj


def upsert_location(db: Session, stop_name: str, latitude: float, longitude: float, region: str, hotspot: float):
    obj = db.query(models.Location).filter(models.Location.stop_name == stop_name).first()
    if not obj:
        obj = models.Location(
            stop_name=stop_name, latitude=latitude, longitude=longitude, region=region, hotspot_score=hotspot
        )
        db.add(obj)
    else:
        obj.latitude = latitude
        obj.longitude = longitude
        obj.region = region
        obj.hotspot_score = hotspot
    db.commit()
    db.refresh(obj)
    return obj


def create_route_prediction(
    db: Session,
    driver_id: str,
    prediction_date,
    route,
    predicted_time_hours: float,
    total_distance_km: float,
    confidence: float,
    efficiency_score: float,
):
    obj = models.RoutePrediction(
        driver_id=driver_id,
        prediction_date=prediction_date,
        recommended_route=json.dumps(route),
        predicted_time_hours=predicted_time_hours,
        total_distance_km=total_distance_km,
        confidence=confidence,
        route_efficiency_score=efficiency_score,
        created_at=datetime.utcnow(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_weekly_prediction(db: Session, driver_id: str, week: str, schedule: dict, distance: float, efficiency: float):
    obj = models.WeeklyPrediction(
        driver_id=driver_id,
        week=week,
        schedule_json=json.dumps(schedule),
        weekly_distance_km=distance,
        weekly_efficiency=efficiency,
        created_at=datetime.utcnow(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

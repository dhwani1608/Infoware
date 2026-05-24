from datetime import date
from sqlalchemy.orm import Session
from model.predictor import RoutePredictor


class PredictionService:
    def __init__(self, predictor: RoutePredictor):
        self.predictor = predictor

    def predict_daily(self, db: Session, driver_id: str, route_date: date, locations: list[str]):
        return self.predictor.predict_daily(db, driver_id, route_date, locations)

    def predict_weekly(self, db: Session, driver_id: str, week: str):
        return self.predictor.predict_weekly(db, driver_id, week)

    def route_map(self, db: Session, driver_id: str):
        return self.predictor.route_map_html(db, driver_id)

    def reroute_dynamic(
        self,
        db: Session,
        driver_id: str,
        route_date: date,
        current_stop: str,
        remaining_stops: list[str],
        traffic_level: str,
    ):
        return self.predictor.reroute_dynamic(db, driver_id, route_date, current_stop, remaining_stops, traffic_level)

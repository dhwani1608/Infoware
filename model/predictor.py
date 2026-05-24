from datetime import date
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.settings import get_settings
from database import crud
from database import models
from integrations.google_places import GooglePlacesClient
from integrations.google_maps import GoogleMapsClient
from model.feature_engineering import FEATURE_COLUMNS, build_features
from model.route_optimizer import optimize_route
from model.trainer import train_models
from scripts.generate_data import generate_synthetic_data


class RoutePredictor:
    def __init__(self):
        settings = get_settings()
        model_dir = Path(settings.model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        data_path = Path(settings.synthetic_data_path)
        if not data_path.exists():
            data_path.parent.mkdir(parents=True, exist_ok=True)
            generate_synthetic_data().to_csv(data_path, index=False)
        if not (model_dir / "xgb_travel_time.joblib").exists() or not (model_dir / "kmeans_locations.joblib").exists():
            train_models(str(data_path))
        self.regressor = joblib.load(model_dir / "xgb_travel_time.joblib")
        self.cluster_model = joblib.load(model_dir / "kmeans_locations.joblib")
        self.history = pd.read_csv(data_path)

    def predict_daily(self, db: Session, driver_id: str, route_date: date, stops: list[str]):
        all_locs = crud.get_locations(db)
        loc_map = {x.stop_name.lower(): x for x in all_locs}
        locs = []
        unresolved = []
        for stop in stops:
            hit = loc_map.get(stop.lower())
            if hit:
                locs.append(hit)
            else:
                unresolved.append(stop)

        # Resolve unknown stops dynamically via geocoding and persist for reuse.
        if unresolved:
            places = GooglePlacesClient()
            for name in unresolved:
                geo = places.geocode_place(name)
                if geo:
                    saved = crud.upsert_location(
                        db,
                        stop_name=name,
                        latitude=float(geo["latitude"]),
                        longitude=float(geo["longitude"]),
                        region=geo.get("region", "Unknown"),
                        hotspot=0.55,
                    )
                    locs.append(saved)

        if not locs:
            raise ValueError("No valid locations found for prediction. Use GET /locations to view known stops.")
        traffic = "high" if route_date.weekday() < 5 else "medium"
        stop_payload = [{"stop_name": l.stop_name, "latitude": l.latitude, "longitude": l.longitude} for l in locs]
        optimized = optimize_route(stop_payload, traffic_level=traffic)

        rows = []
        for i, stop in enumerate(optimized.sequence):
            loc = next(x for x in locs if x.stop_name == stop)
            rows.append(
                {
                    "driver_id": driver_id,
                    "date": str(route_date),
                    "stop_name": loc.stop_name,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "visit_time": f"{9 + i:02d}:00:00",
                    "visit_duration": 20 + i * 3,
                    "traffic_level": traffic,
                    "weather": "clear",
                    "distance_from_previous": optimized.total_distance_km / max(1, len(optimized.sequence)),
                    "travel_time": optimized.total_duration_min / max(1, len(optimized.sequence)),
                    "fuel_estimate": optimized.total_distance_km * 0.09,
                    "region": loc.region,
                    "day_of_week": route_date.strftime("%A"),
                    "week_number": route_date.isocalendar().week,
                }
            )
        feature_df = build_features(pd.DataFrame(rows), self.cluster_model)
        preds = self.regressor.predict(feature_df[FEATURE_COLUMNS])
        total_minutes = float(np.sum(preds))
        confidence = max(0.6, min(0.98, 1 - (np.std(preds) / (np.mean(preds) + 1e-6)) * 0.25))
        efficiency = max(50, min(100, 100 * (optimized.total_distance_km / (total_minutes / 60 + 1e-6)) / 40))
        crud.create_route_prediction(
            db,
            driver_id=driver_id,
            prediction_date=route_date,
            route=optimized.sequence,
            predicted_time_hours=round(total_minutes / 60, 2),
            total_distance_km=optimized.total_distance_km,
            confidence=float(round(confidence, 2)),
            efficiency_score=float(round(efficiency, 2)),
        )
        return {
            "recommended_route": optimized.sequence,
            "predicted_time": f"{round(total_minutes / 60, 2)} hours",
            "confidence": round(confidence, 2),
            "total_distance_km": optimized.total_distance_km,
            "route_efficiency_score": round(efficiency, 2),
        }

    def predict_weekly(self, db: Session, driver_id: str, iso_week: str):
        week_df = self.history[self.history["driver_id"] == driver_id].copy()
        if week_df.empty:
            raise ValueError("No historical records for driver")
        grouped = week_df.groupby("day_of_week")["stop_name"].agg(lambda x: list(x.value_counts().head(3).index))
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule = {day.lower(): grouped.get(day, []) for day in order}
        weekly_distance = float(week_df["distance_from_previous"].sum() / max(1, week_df["week_number"].nunique()))
        weekly_efficiency = float((week_df["distance_from_previous"].sum() / (week_df["travel_time"].sum() / 60 + 1e-6)) / 35)
        weekly_efficiency = max(0.5, min(0.98, weekly_efficiency))
        crud.create_weekly_prediction(db, driver_id, iso_week, schedule, weekly_distance, weekly_efficiency)
        payload = schedule.copy()
        payload["weekly_distance"] = f"{round(weekly_distance, 2)}km"
        payload["weekly_efficiency"] = round(weekly_efficiency, 2)
        return payload

    def route_map_html(self, db: Session, driver_id: str) -> str:
        import folium

        trips = self.history[self.history["driver_id"] == driver_id].head(25)
        if trips.empty:
            return ""
        center = [trips["latitude"].mean(), trips["longitude"].mean()]
        fmap = folium.Map(location=center, zoom_start=11)
        points = []
        for _, row in trips.iterrows():
            loc = [row["latitude"], row["longitude"]]
            points.append(loc)
            folium.Marker(loc, popup=f"{row['stop_name']} ({row['visit_time']})").add_to(fmap)
        folium.PolyLine(points, color="blue", weight=3).add_to(fmap)
        out = Path(get_settings().model_dir).parent / "route_map.html"
        fmap.save(str(out))
        return str(out)

    def reroute_dynamic(
        self,
        db: Session,
        driver_id: str,
        route_date: date,
        current_stop: str,
        remaining_stops: list[str],
        traffic_level: str = "high",
    ):
        if current_stop not in remaining_stops:
            remaining_stops = [current_stop, *remaining_stops]
        all_locs = crud.get_locations(db)
        loc_map = {x.stop_name.lower(): x for x in all_locs}
        ordered = []
        for stop in remaining_stops:
            loc = loc_map.get(stop.lower())
            if not loc:
                raise ValueError(f"Unknown stop '{stop}' for rerouting")
            ordered.append(loc)
        start_idx = next((i for i, x in enumerate(ordered) if x.stop_name.lower() == current_stop.lower()), 0)
        payload = [{"stop_name": l.stop_name, "latitude": l.latitude, "longitude": l.longitude} for l in ordered]
        optimized = optimize_route(payload, traffic_level=traffic_level, start_index=start_idx, refresh_traffic=True)
        return self.predict_daily(db, driver_id, route_date, optimized.sequence)

    def monitoring_summary(self, db: Session) -> dict:
        route_stats = db.query(
            func.count(models.RoutePrediction.id),
            func.avg(models.RoutePrediction.confidence),
            func.avg(models.RoutePrediction.route_efficiency_score),
        ).one()
        trip_stats = db.query(func.count(models.Trip.id), func.avg(models.Trip.travel_time)).one()
        maps_cache = GoogleMapsClient().cache_stats()
        places_cache = GooglePlacesClient().cache_stats()
        return {
            "total_predictions": int(route_stats[0] or 0),
            "avg_confidence": round(float(route_stats[1] or 0.0), 3),
            "avg_efficiency_score": round(float(route_stats[2] or 0.0), 3),
            "total_trips": int(trip_stats[0] or 0),
            "avg_trip_time_min": round(float(trip_stats[1] or 0.0), 2),
            "cache": {"google_maps": maps_cache, "google_places": places_cache},
        }

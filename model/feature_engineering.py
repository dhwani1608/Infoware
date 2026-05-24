import pandas as pd
import numpy as np


TRAFFIC_MAP = {"low": 1, "medium": 2, "high": 3}
WEATHER_MAP = {"clear": 1, "cloudy": 2, "rain": 3}


def build_features(df: pd.DataFrame, cluster_model=None) -> pd.DataFrame:
    data = df.copy()
    data["visit_dt"] = pd.to_datetime(data["date"].astype(str) + " " + data["visit_time"])
    data["hour"] = data["visit_dt"].dt.hour
    data["day_num"] = data["visit_dt"].dt.dayofweek
    data["is_weekend"] = (data["day_num"] >= 5).astype(int)
    data["is_rush_hour"] = data["hour"].isin([8, 9, 10, 17, 18, 19]).astype(int)
    data["traffic_num"] = data["traffic_level"].map(TRAFFIC_MAP).fillna(2).astype(int)
    data["weather_num"] = data["weather"].map(WEATHER_MAP).fillna(1).astype(int)
    data["stop_count_daily"] = data.groupby(["driver_id", "date"])["stop_name"].transform("count")
    data["total_distance_daily"] = data.groupby(["driver_id", "date"])["distance_from_previous"].transform("sum")
    data["avg_speed_kmh"] = (data["distance_from_previous"] / (data["travel_time"] / 60 + 1e-6)).clip(5, 70)
    data["driver_avg_speed"] = data.groupby("driver_id")["avg_speed_kmh"].transform("mean")
    data["driver_avg_daily_visits"] = data.groupby("driver_id")["stop_count_daily"].transform("mean")
    region_density = data.groupby("region")["stop_name"].transform("count")
    data["region_density"] = region_density / region_density.max()
    data["historical_efficiency"] = (data["avg_speed_kmh"] / (1 + data["traffic_num"])).clip(0, 100)
    if cluster_model is not None:
        data["cluster_id"] = cluster_model.predict(data[["latitude", "longitude"]])
    elif "cluster_id" not in data:
        data["cluster_id"] = 0
    region_pref = (
        data.groupby(["driver_id", "region"])["stop_name"].transform("count")
        / data.groupby("driver_id")["stop_name"].transform("count")
    )
    data["driver_region_preference"] = region_pref.fillna(0.0)
    data["hotspot_score"] = (
        (data["traffic_num"] * 0.5 + data["stop_count_daily"] / data["stop_count_daily"].max() * 0.5).clip(0, 1)
    )
    data = data.replace([np.inf, -np.inf], 0).fillna(0)
    return data


FEATURE_COLUMNS = [
    "hour",
    "day_num",
    "is_weekend",
    "is_rush_hour",
    "week_number",
    "distance_from_previous",
    "visit_duration",
    "traffic_num",
    "weather_num",
    "stop_count_daily",
    "total_distance_daily",
    "driver_avg_speed",
    "driver_avg_daily_visits",
    "region_density",
    "historical_efficiency",
    "cluster_id",
    "driver_region_preference",
    "hotspot_score",
]

import pandas as pd
from model.feature_engineering import build_features, FEATURE_COLUMNS


def test_feature_engineering_columns():
    df = pd.DataFrame(
        [
            {
                "driver_id": "D1",
                "date": "2026-05-20",
                "stop_name": "A",
                "latitude": 23.02,
                "longitude": 72.57,
                "visit_time": "10:00:00",
                "visit_duration": 20,
                "traffic_level": "medium",
                "weather": "clear",
                "distance_from_previous": 8.0,
                "travel_time": 19.0,
                "fuel_estimate": 0.8,
                "region": "North Ahmedabad",
                "day_of_week": "Tuesday",
                "week_number": 20,
            }
        ]
    )
    out = build_features(df)
    for col in FEATURE_COLUMNS:
        assert col in out.columns

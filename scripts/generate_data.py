from datetime import datetime, timedelta
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings


def generate_synthetic_data(num_records: int = 1600, num_drivers: int = 12, num_locations: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    drivers = [f"D{i+1}" for i in range(num_drivers)]
    regions = ["North Ahmedabad", "South Ahmedabad", "Gandhinagar", "Vadodara", "Surat Hub"]
    base_lat, base_lon = 23.0225, 72.5714

    locations = []
    for i in range(num_locations):
        region = regions[i % len(regions)]
        lat = base_lat + rng.normal(0, 0.16)
        lon = base_lon + rng.normal(0, 0.2)
        locations.append((f"Store_{i+1}", lat, lon, region))

    start_date = datetime(2026, 1, 1)
    rows = []
    for _ in range(num_records):
        driver = rng.choice(drivers)
        days = int(rng.integers(0, 140))
        d = start_date + timedelta(days=days)
        day = d.strftime("%A")
        is_weekend = day in ["Saturday", "Sunday"]
        stop_name, lat, lon, region = locations[int(rng.integers(0, len(locations)))]
        hour = int(rng.choice([8, 9, 10, 12, 14, 16, 17, 18, 20], p=[0.12, 0.13, 0.13, 0.1, 0.1, 0.1, 0.14, 0.1, 0.08]))
        traffic = rng.choice(["low", "medium", "high"], p=[0.15, 0.45, 0.4] if not is_weekend else [0.3, 0.5, 0.2])
        weather = rng.choice(["clear", "cloudy", "rain"], p=[0.55, 0.3, 0.15])
        dist = max(1.2, float(rng.normal(8.5, 4.2)))
        traffic_factor = {"low": 0.9, "medium": 1.2, "high": 1.6}[traffic]
        weather_factor = {"clear": 1.0, "cloudy": 1.1, "rain": 1.3}[weather]
        driver_factor = 0.9 + (int(driver[1:]) % 5) * 0.05
        travel_time = (dist / 28) * 60 * traffic_factor * weather_factor * driver_factor
        visit_duration = float(rng.normal(22, 6) + (3 if region == "Surat Hub" else 0))
        fuel = dist * rng.uniform(0.07, 0.12)
        rows.append(
            {
                "driver_id": driver,
                "date": d.date().isoformat(),
                "stop_name": stop_name,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "visit_time": f"{hour:02d}:{int(rng.choice([0, 15, 30, 45])):02d}:00",
                "visit_duration": round(max(8, visit_duration), 2),
                "traffic_level": traffic,
                "weather": weather,
                "distance_from_previous": round(dist, 2),
                "travel_time": round(max(4, travel_time), 2),
                "fuel_estimate": round(fuel, 2),
                "region": region,
                "day_of_week": day,
                "week_number": int(d.isocalendar().week),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    settings = get_settings()
    df = generate_synthetic_data()
    path = Path(settings.synthetic_data_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Generated {len(df)} rows at {path}")

import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Base, engine, SessionLocal
from database import crud
from config.settings import get_settings


def seed():
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    df = pd.read_csv(settings.synthetic_data_path)
    db = SessionLocal()
    try:
        for driver_id in sorted(df["driver_id"].unique()):
            crud.upsert_driver(db, driver_id, f"Driver {driver_id}", "Ahmedabad", 0.75)
        locs = df.groupby("stop_name").first().reset_index()
        for _, row in locs.iterrows():
            crud.upsert_location(
                db,
                stop_name=row["stop_name"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                region=row["region"],
                hotspot=0.6,
            )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Database seeded.")

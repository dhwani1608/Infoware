from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from config.settings import get_settings
from model.clustering import fit_location_clusters
from model.feature_engineering import FEATURE_COLUMNS, build_features


def train_models(data_path: str | None = None) -> dict:
    settings = get_settings()
    source_path = data_path or settings.synthetic_data_path
    df = pd.read_csv(source_path)
    cluster_model = fit_location_clusters(df)
    engineered = build_features(df, cluster_model)
    X = engineered[FEATURE_COLUMNS]
    y = engineered["travel_time"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # XGBoost scales well with feature count and handles nonlinear interactions in traffic behavior.
    reg = XGBRegressor(
        n_estimators=220, max_depth=6, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, random_state=42
    )
    reg.fit(X_train, y_train)
    pred = reg.predict(X_test)
    metrics = {"mae_minutes": float(mean_absolute_error(y_test, pred)), "r2": float(r2_score(y_test, pred))}

    model_dir = Path(settings.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(reg, model_dir / "xgb_travel_time.joblib")
    joblib.dump(cluster_model, model_dir / "kmeans_locations.joblib")
    return metrics

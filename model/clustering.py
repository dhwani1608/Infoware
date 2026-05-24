import joblib
import pandas as pd
from sklearn.cluster import KMeans
from config.settings import get_settings


def fit_location_clusters(df: pd.DataFrame, n_clusters: int | None = None) -> KMeans:
    settings = get_settings()
    n = n_clusters or settings.default_location_cluster_count
    model = KMeans(n_clusters=n, random_state=42, n_init=10)
    model.fit(df[["latitude", "longitude"]])
    return model


def save_cluster_model(model: KMeans, path: str) -> None:
    joblib.dump(model, path)


def load_cluster_model(path: str) -> KMeans:
    return joblib.load(path)

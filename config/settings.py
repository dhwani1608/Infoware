from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI Route Prediction System"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = f"sqlite:///{(BASE_DIR / 'route_prediction.db').as_posix()}"
    model_dir: str = str(BASE_DIR / "model" / "saved_models")
    synthetic_data_path: str = str(BASE_DIR / "data" / "synthetic" / "trips.csv")
    google_maps_api_key: str = ""
    google_maps_base_url: str = "https://maps.googleapis.com/maps/api"
    cache_dir: str = str(BASE_DIR / ".cache")
    cache_ttl_seconds: int = 86400
    api_rate_limit_per_second: float = 5.0
    default_location_cluster_count: int = 8
    redis_url: str = ""
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Runtime settings loaded from environment variables / .env files."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "config/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    http_timeout_s: float = 10.0
    http_retries: int = 2

    default_lat: float = 39.9526
    default_lon: float = -75.1652
    default_radius_km: float = 25.0

    max_ws_clients: int = 100
    realtime_poll_interval_s: float = 10.0
    realtime_aircraft_radius_nm: int = 250

    mapillary_api_key: str | None = None
    greynoise_api_key: str | None = None
    opensky_username: str | None = None
    opensky_password: str | None = None
    aishub_username: str | None = None
    aprs_fi_api_key: str | None = None
    nasa_firms_map_key: str | None = None
    transitland_api_key: str | None = None
    mta_api_key: str | None = None


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

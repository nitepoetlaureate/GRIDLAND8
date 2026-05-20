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

    # Cache TTLs (0 disables, callers may opt in per call)
    cache_ttl_overpass_s: float = 300.0       # 5 min
    cache_ttl_dot_s: float = 60.0             # 1 min
    cache_ttl_nws_forecast_s: float = 900.0   # 15 min
    cache_ttl_nws_alerts_s: float = 60.0      # 1 min
    cache_ttl_wikipedia_s: float = 3600.0     # 1 h
    cache_ttl_mapillary_s: float = 600.0      # 10 min
    cache_ttl_quakes_s: float = 300.0         # 5 min
    cache_ttl_firms_s: float = 600.0          # 10 min
    cache_ttl_openaq_s: float = 600.0         # 10 min
    cache_ttl_metar_s: float = 300.0          # 5 min
    cache_ttl_tle_s: float = 21600.0          # 6 h
    cache_ttl_septa_vehicles_s: float = 10.0  # 10 s (live transit)
    cache_ttl_septa_alerts_s: float = 60.0    # 1 min
    cache_ttl_septa_detours_s: float = 120.0  # 2 min
    cache_ttl_indego_s: float = 30.0          # 30 s (GBFS status)
    cache_ttl_penndot_s: float = 3600.0       # 1 h (camera inventory)
    cache_ttl_phila311_s: float = 300.0       # 5 min
    cache_ttl_opendataphilly_s: float = 300.0  # 5 min (Carto SQL)
    cache_ttl_usgs_water_s: float = 600.0     # 10 min
    cache_ttl_nyctmc_s: float = 60.0          # 1 min (image refresh fast)
    cache_ttl_cr511_s: float = 60.0           # 1 min
    cache_ttl_nps_webcams_s: float = 3600.0   # 1 h (very rarely changes)

    default_lat: float = 39.9526
    default_lon: float = -75.1652
    default_radius_km: float = 25.0

    max_ws_clients: int = 100
    realtime_poll_interval_s: float = 10.0
    realtime_aircraft_radius_nm: int = 250

    # Discovery source toggles & districts
    caltrans_districts: list[int] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    )

    # Free upstream API keys (sources skip themselves if a required key is unset)
    mapillary_api_key: str | None = None
    wsdot_api_key: str | None = None
    n511ny_api_key: str | None = None
    greynoise_api_key: str | None = None
    opensky_username: str | None = None
    opensky_password: str | None = None
    aishub_username: str | None = None
    aprs_fi_api_key: str | None = None
    nasa_firms_map_key: str | None = None
    openaq_api_key: str | None = None
    transitland_api_key: str | None = None
    mta_api_key: str | None = None
    nps_api_key: str | None = None
    cam2_client_id: str | None = None
    cam2_client_secret: str | None = None

    # Satellite catalogs exposed by /api/satellites
    tle_catalogs: list[str] = Field(
        default_factory=lambda: ["stations", "active", "weather", "geo", "starlink"]
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings_cache() -> None:
    """For tests: drop the memoized Settings so env changes take effect."""
    global _settings
    _settings = None

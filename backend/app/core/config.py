"""
Application Settings
Loaded from environment variables / .env file.
Uses pydantic-settings for type-safe, validated configuration.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unknown env vars
    )

    # ── Application ───────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # ── Database ──────────────────────────────────────────
    database_url: str | None = None
    postgres_user: str = "logistics_user"
    postgres_password: str = "changeme"
    postgres_db: str = "logistics_db"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @field_validator("database_url", mode="before")
    @classmethod
    def parse_database_url(cls, v):
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis / Celery ─────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # ── JWT Authentication ────────────────────────────────
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── CORS ──────────────────────────────────────────────
    backend_cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "*",
    ]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            if v.strip().startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── External APIs ─────────────────────────────────────
    ors_api_key: str = ""
    ors_base_url: str = "https://api.openrouteservice.org"
    weather_api_base_url: str = "https://api.open-meteo.com/v1"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "sih-logistics-dss/1.0"

    # ── Toll Model (INR per km) ───────────────────────────
    toll_rate_per_km_nh: float = 1.20
    toll_rate_per_km_sh: float = 0.75
    toll_rate_per_km_other: float = 0.00

    # ── Fuel Prices (INR) ────────────────────────────────
    diesel_price_per_liter: float = 92.50
    petrol_price_per_liter: float = 102.00
    cng_price_per_kg: float = 85.00
    co2_factor_diesel: float = 2.68
    co2_factor_petrol: float = 2.31
    co2_factor_cng: float = 1.90
    driver_cost_per_hour_inr: float = 120.00

    # ── Synthetic Data ────────────────────────────────────
    seed_random_seed: int = 42
    seed_num_vehicles: int = 50
    seed_num_drivers: int = 50
    seed_num_shipments: int = 500
    seed_num_historical_trips: int = 300
    seed_num_incidents: int = 80

    # ── Admin Bootstrap ───────────────────────────────────
    admin_email: str = "admin@logistics.in"
    admin_password: str = "Admin@123!"
    admin_full_name: str = "System Administrator"

    # ── Email (optional) ──────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@logistics.in"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Use `get_settings()` everywhere instead of `Settings()` to avoid
    re-reading the .env file on every call.
    """
    return Settings()

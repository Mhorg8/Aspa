from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ASPA API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = "postgresql+asyncpg://aspa:aspa@localhost:5432/aspa"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(min_length=32, repr=False)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    auth_rate_limit_requests: int = Field(default=20, gt=0)
    auth_rate_limit_window_seconds: int = Field(default=60, gt=0)
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=10)

    @model_validator(mode="after")
    def reject_example_secrets(self) -> Self:
        if self.jwt_secret_key in {
            "development-only-secret-change-me",
            "replace-with-at-least-32-random-characters",
        }:
            raise ValueError("Set JWT_SECRET_KEY to a randomly generated secret")
        return self


@lru_cache
def get_settings() -> Settings:
    # Required settings are supplied and validated by BaseSettings from the environment.
    return Settings()  # pyright: ignore[reportCallIssue]

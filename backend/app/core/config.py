from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field(default="http://localhost:3000")
    max_result_rows: int = Field(default=1000, ge=1, le=100_000)
    query_timeout_seconds: int = Field(default=15, ge=1, le=300)
    session_ttl_seconds: int = Field(default=3600, ge=60)
    chat_history_turns: int = Field(default=8, ge=0, le=50)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

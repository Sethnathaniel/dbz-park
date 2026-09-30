"""Settings, read once from the `.env` at the project root — shared with the front."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# app/config.py → app/ → backend/ → project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Nothing else in the code reads `os.environ`: it all goes through `get_settings()`."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "dbz_park"
    postgres_password: str = ""
    postgres_db: str = "dbz_park"

    # Signed JWTs, stored nowhere: changing this secret revokes every token at once.
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 12 * 60

    # Comma-separated. In dev the Vite proxy serves /api from the same origin.
    cors_origins: str = "http://localhost:5173"
    # Joining a queue is refused from this hour on (the SPEC closes them at 19:00).
    queue_closing_hour: int = 19
    debug: bool = False

    @property
    def database_url(self) -> URL:
        """Built by `URL.create` so a password with special characters needs no escaping."""
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

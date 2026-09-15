from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class AppSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="AF_")

    env: Literal["dev", "prod"] = "prod"
    api_prefix: str = "/api/v1"
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    expose_headers: list[str] = ["*"]



class DBSettings(BaseSettings):
    """Database settings."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "postgres"
    port: int = 5432
    user: str = "devuser"
    password: str = "devpass"
    name: str = "devdatabase"

    pool_size: int = 20
    echo: bool = False

    @computed_field
    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.name,
        )


app_settings = AppSettings()
db_settings = DBSettings()

__all__ = ["app_settings", "db_settings"]

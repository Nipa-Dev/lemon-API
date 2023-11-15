from functools import lru_cache

from loguru import logger

from decouple import config


class Settings:
    port: str = "5001"
    env_name: str = "Local"
    base_url: str = f"http://localhost:{port}"
    sqlite_url: str = "sqlite:///./shortener.db"
    postgres_url: str = f"postgresql+psycopg2://{config('DB_USER')}:{config('DB_PASSWORD')}@postgres:{config('DB_PORT')}/{config('DB_NAME')}"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    logger.debug(f"Loading settings for: {settings.env_name}")
    return settings

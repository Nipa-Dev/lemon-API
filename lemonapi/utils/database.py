import asyncpg

from .constants import Server


class Connection:
    """Connection configuration for postgresql database and redis."""

    DATABASE_URL = f"postgres://{Server.DB_USER}:{Server.DB_PASSWORD}@{Server.DB_HOST}:{Server.DB_PORT}/{Server.DB_NAME}"
    # DATABASE_URL = f"postgres://{Server.DB_USER}:{Server.DB_PASSWORD}@postgres:{Server.DB_PORT}/{Server.DB_NAME}"

    DB_POOL = asyncpg.create_pool(DATABASE_URL)

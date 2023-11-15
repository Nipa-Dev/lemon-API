import asyncpg
from decouple import config


class Connection:
    """Connection configuration for postgresql database and redis."""

    DATABASE_URL = f"postgres://{config('DB_USER')}:{config('DB_PASSWORD')}@postgres:{config('DB_PORT')}/{config('DB_NAME')}"

    DB_POOL = asyncpg.create_pool(DATABASE_URL)

import secrets
import string
from typing import Annotated

from fastapi import Depends
from loguru import logger

from .. import dependencies, schemas
from ..constants import Server


class UrlService:
    """
    Service class for URL shortening operations.
    """

    def __init__(self, pool: dependencies.PoolDep):
        """
        Initialize the UrlService with a database connection pool.

        Args:
            pool: Database connection pool dependency.
        """
        self.pool = pool

    async def get_url_by_secret_key(self, secret_key: str):
        """
        Get URL by secret key.

        Args:
            secret_key: The secret key of the URL.

        Returns:
            The URL row if found and active, None otherwise.
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE secret_key = $1 AND is_active = $2",
                secret_key,
                True,
            )
        return row

    async def get_db_url_by_key(self, url_key: str):
        """
        Get URL by URL key.

        Args:
            url_key: The URL key.

        Returns:
            The URL row if found and active, None otherwise.
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE url_key = $1 AND is_active = $2",
                url_key,
                True,
            )
        return row

    async def deactivate_db_url_by_secret_key(self, secret_key: str):
        """
        Deactivate and delete URL by secret key.

        Args:
            secret_key: The secret key of the URL to deactivate.

        Returns:
            The deleted URL row if found, None otherwise.
        """
        async with self.pool.acquire() as con:
            db_url = await self.get_url_by_secret_key(secret_key)
            if db_url:
                await con.execute(
                    "DELETE FROM urls WHERE secret_key = $1 RETURNING *",
                    secret_key,
                )
            logger.info(
                f"URL with secret key '{secret_key}' deleted from the database."
            )
        return db_url

    async def create_db_url(self, url: schemas.URLBase):
        """
        Create a new shortened URL in the database.

        Args:
            url: The URL base data containing the target URL.

        Returns:
            The created URL row with key, target URL, and secret key.
        """
        secret_key_length = Server.SECRET_KEY_LENGTH

        async with self.pool.acquire() as con:
            key = await self.create_unique_random_key()
            secret_key = (
                f"{key}_{await self.create_random_key(length=secret_key_length)}"
            )

            await con.execute(
                """INSERT INTO urls (
                    target_url,
                    url_key,
                    secret_key) VALUES ($1, $2, $3)""",
                str(url.target_url),
                key,
                secret_key,
            )
            row = await con.fetchrow(
                "SELECT url_key, target_url, secret_key FROM urls WHERE url_key = $1",
                key,
            )
            logger.info(f"URL created with key '{key}' in the database.")
        return row

    async def update_db_clicks(self, db_url: schemas.URL):
        """
        Update the click count for a URL.

        Args:
            db_url: The URL object to update clicks for.

        Returns:
            The updated URL row.
        """
        async with self.pool.acquire() as con:
            await con.execute(
                "UPDATE urls SET clicks = $1 WHERE url_key = $2",
                db_url.clicks + 1,
                db_url.url_key,
            )
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE url_key = $1", db_url.url_key
            )
            return row

    async def create_random_key(self, length: int = Server.KEY_LENGTH) -> str:
        """
        Generate a random key of given length for URL shortening.

        Args:
            length: The length of the key. Defaults to Server.KEY_LENGTH.

        Returns:
            A random string key.
        """
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    async def create_unique_random_key(self) -> str:
        """
        Create a unique random key by ensuring it doesn't exist in the database.

        Returns:
            A unique random key.
        """
        key = await self.create_random_key()
        foo = await self.get_db_url_by_key(key)
        while foo:
            key = await self.create_random_key()
            foo = await self.get_db_url_by_key(key)
        return key


UrlServiceDep = Annotated[UrlService, Depends(UrlService)]

import secrets
import string

from asyncpg import Connection

from . import crud


async def create_random_key(length: int = 5) -> str:
    """Generate random key from given length to be used in url shortener."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def create_unique_random_key(conn: Connection) -> str:
    """Requires logic check, not done yet"""
    key = await create_random_key()
    foo = await crud.get_db_url_by_key(conn, key)
    while foo:
        key = await create_random_key()
        foo = await crud.get_db_url_by_key(conn, key)
    return key

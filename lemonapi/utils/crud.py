from fastapi import status, HTTPException

# from sqlalchemy.orm import Session

from . import keygen, schemas, auth
from loguru import logger

from asyncpg import Connection
from ulid import ULID


async def get_url_by_secret_key(conn: Connection, secret_key: str):
    row = await conn.fetchrow(
        "SELECT * FROM urls WHERE secret_key = $1 AND is_active = $2", secret_key, True
    )
    return row


async def get_db_url_by_key(conn: Connection, url_key: str):
    row = await conn.fetchrow(
        "SELECT * FROM urls WHERE url_key = $1 AND is_active = $2", url_key, True
    )
    return row


async def deactivate_db_url_by_secret_key(conn: Connection, secret_key: str):
    db_url = await get_url_by_secret_key(conn, secret_key)
    if db_url:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM urls WHERE secret_key = $1 RETURNING *",
                secret_key,
            )
            logger.trace(f"Deleted data associated with {secret_key} from database")
    return db_url


async def create_db_url(conn: Connection, url: schemas.URLBase):
    key = await keygen.create_unique_random_key(conn)
    secret_key = f"{key}_{await keygen.create_random_key(length=8)}"
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO urls (target_url, url_key, secret_key) VALUES ($1, $2, $3)",
            url.target_url,
            key,
            secret_key,
        )
        row = await conn.fetchrow(
            "SELECT url_key, target_url, secret_key FROM urls WHERE url_key = $1", key
        )
    return row


async def update_db_clicks(conn: Connection, db_url: schemas.URL):
    async with conn.transaction():
        await conn.execute(
            "UPDATE urls SET clicks = $1 WHERE url_key = $2",
            db_url.clicks + 1,
            db_url.url_key,
        )
        row = await conn.fetchrow(
            "SELECT * FROM urls WHERE url_key = $1", db_url.url_key
        )
    return row


async def get_list_of_usernames(conn: Connection) -> list[str]:
    rows = await conn.fetch("SELECT username FROM users")
    return [row["username"] for row in rows]


async def get_list_of_emails(conn: Connection) -> list[str]:
    rows = await conn.fetch("SELECT email FROM users")
    return [row["email"] for row in rows]


async def add_user(conn: Connection, user: auth.NewUser):
    if user.username in await get_list_of_usernames(conn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )  # raise exception if username already exists
    elif user.email in await get_list_of_emails(conn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )
    ulid = ULID()
    user_id_str = str(ulid)
    async with conn.transaction():
        await conn.execute(
            """INSERT INTO users (
                user_id,
                username,
                hashed_password,
                fullname,
                email
                ) VALUES ($1, $2, $3, $4, $5)""",
            user_id_str,
            user.username,
            auth.get_password_hash(user.password),
            user.full_name,
            user.email,
        )
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            user.username,
        )
    return row

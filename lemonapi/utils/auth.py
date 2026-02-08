import secrets
import asyncpg

from typing import Annotated
from loguru import logger
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from asyncpg import Record
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from lemonapi.utils.constants import Server
from lemonapi.utils import dependencies
from lemonapi.utils.schemas import User, UserInDB, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2 security scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    description="OAuth security scheme",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify the password.

    Args:
        plain_password: Password in plain text.
        hashed_password: The hashed password.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash the password from given string.

    Args:
        password: The password to be hashed.

    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


async def get_user(username: str, con: asyncpg.Connection) -> UserInDB | None:
    """
    Get user by username.

    Args:
        username: Username of the user.
        con: Database connection.

    Returns:
        UserInDB object if found, None otherwise.
    """

    row = await con.fetchrow("SELECT * FROM users WHERE username = $1", username)

    if row:
        return UserInDB(**dict(row))
    return None


async def authenticate_user(
    username: str,
    password: str,
    request: Request,
    pool: dependencies.PoolDep,
):
    """
    Authenticate the user with username and password.

    Args:
        username: Username of the user.
        password: Password of the user.
        request: The incoming request object.
        pool: Database connection pool.

    Returns:
        User object if authentication succeeds, False otherwise.
    """
    user = await get_user(username, pool)
    if not user:
        logger.warning(f"Incorrect username attempt from IP: {request.client.host}")
        return False
    if not verify_password(password, user.hashed_password):
        if request:
            logger.warning(f"Incorrect password attempt from IP: {request.client.host}")
        else:
            logger.warning(f"Incorrect password request from user: {username}")
        return False

    return user


async def reset_refresh_token(
    con: asyncpg.Connection, user_id: str
) -> tuple[str, Record]:
    """
    Reset the refresh token for the user or receive it.

    Args:
        con: Database connection.
        user_id: The id of the user.

    Returns:
        Tuple containing the refresh token and the row from the database.
    """
    # Generate 22 char long string
    token_salt = secrets.token_urlsafe(16)

    expiration = datetime.now(timezone.utc) + timedelta(
        seconds=Server.REFRESH_EXPIRE_IN
    )
    row = await con.fetchrow(
        "UPDATE users SET key_salt = $1 WHERE user_id = $2 RETURNING *",
        token_salt,
        user_id,
    )
    token = jwt.encode(
        {
            "id": row["user_id"],
            "grant_type": "refresh_token",
            "expiration": expiration.timestamp(),
            "salt": token_salt,
            "scopes": row["scopes"],
        },
        Server.SECRET_KEY,
        algorithm=Server.ALGORITHM,
    )
    return token, row


async def create_access_token(
    con: asyncpg.Connection, refresh_token: str, request: Request
) -> tuple[str, str]:
    """
    Create access token to be used for authentication.
    Refresh existing refresh token if it is expired.

    Args:
        con: Database connection.
        refresh_token: Refresh token used to create access token.
        request: The incoming request object.

    Returns:
        Tuple containing the access token and refresh token.

    Raises:
        HTTPException: When the refresh token is invalid.
    """
    try:
        token_data = jwt.decode(refresh_token, Server.SECRET_KEY)
    except JWTError:
        logger.warning(f"Incorrect/Invalid token from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expire = datetime.now(timezone.utc) + timedelta(seconds=Server.ACCESS_EXPIRE_IN)

    row = await con.fetchrow(
        "SELECT user_id, key_salt, scopes FROM users WHERE user_id = $1",
        token_data["id"],
    )
    # validate salt
    if row["key_salt"] != token_data["salt"]:
        logger.warning(f"Incorrect/Invalid salt from IP: {request.client.host}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if int(token_data["expiration"]) < datetime.now(timezone.utc).timestamp():
        refresh_token, row = await reset_refresh_token(con, row["user_id"])

    token = jwt.encode(
        {
            "id": token_data["id"],
            "grant_type": "access_token",
            "expiration": expire.timestamp(),
            "salt": row["key_salt"],
            "scopes": row["scopes"],
        },
        Server.SECRET_KEY,
        algorithm=Server.ALGORITHM,
    )
    return token, refresh_token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    pool: dependencies.PoolDep,
    request: Request,
):
    """
    Get the current user.

    Args:
        token: Authorization token.
        pool: Database connection pool.
        request: The incoming request object.

    Returns:
        UserInDB object with necessary data.

    Raises:
        HTTPException: When credentials are invalid.
    """
    authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    async with pool.acquire() as con:
        try:
            payload = jwt.decode(
                token, Server.SECRET_KEY, algorithms=[Server.ALGORITHM]
            )
            u_id: str = payload.get("id")
            if u_id is None:
                raise credentials_exception
            username = await con.fetchrow(
                "SELECT username FROM users WHERE user_id = $1", u_id
            )
            token_data = TokenData(username=str(username[0]))
        except (JWTError, ValidationError):
            host = request.client.host
            logger.warning(
                f"""Incorrect/Invalid token from IP: {
                    host if host is not None else "Unavailable"
                }"""
            )
            logger.trace("JWT Error, invalid token")
            raise credentials_exception
        user = await get_user(username=token_data.username, con=con)
    if user is None:
        logger.trace("User not found but ID was in token")
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current active user. This user is authenticated.

    Args:
        current_user: Current user that is received from get_current_user.

    Returns:
        User object with necessary data.

    Raises:
        HTTPException: When the user is disabled.
    """
    if current_user.is_disabled:
        logger.info(f"Inactive user requested: {current_user} ")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

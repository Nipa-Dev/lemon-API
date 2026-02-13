from typing import Annotated

from fastapi import Depends, HTTPException, status
from loguru import logger
from ulid import ULID

from .. import auth, dependencies, schemas


class UserService:
    """
    Service class for user management operations.
    """

    def __init__(self, pool: dependencies.PoolDep):
        """
        Initialize the UserService with a database connection pool.

        Args:
            pool: Database connection pool dependency.
        """
        self.pool = pool

    async def add_user(self, user: schemas.NewUser):
        """
        Add a new user to the database.

        Args:
            user: The new user data.

        Returns:
            The created user row.

        Raises:
            HTTPException: If username or email already exists.
        """
        async with self.pool.acquire() as con:
            if await con.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username=$1)", user.username
            ):
                logger.info(f"User with username '{user.username}' already exists.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists.",
                )

            if await con.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email=$1)", user.email
            ):
                logger.info(f"Email '{user.email}' already exists.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists.",
                )

        # create user ID
        ulid = ULID()
        user_id_str = str(ulid)
        async with self.pool.acquire() as con:
            await con.execute(
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
            row = await con.fetchrow(
                "SELECT * FROM users WHERE username = $1",
                user.username,
            )
        logger.info(
            f"User '{user.username}' created successfully with ID '{user_id_str}'."
        )
        return row

    async def update_password(self, user: schemas.User, new_password: str):
        """
        Update user password.

        Args:
            user: The user object.
            new_password: The new password to set.

        Returns:
            Tuple of the updated user row and a success message.

        Raises:
            HTTPException: If user is not found.
        """
        async with self.pool.acquire() as con:
            row = await auth.get_user(user.username, con)
            if row is None:
                raise HTTPException(404, detail="User not found")
            hashed_password = auth.get_password_hash(new_password)
            await con.execute(
                "UPDATE users SET hashed_password = $1 WHERE user_id = $2",
                hashed_password,
                row.user_id,
            )
            row = await con.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                row.user_id,
            )
            logger.info(
                f"User '{user.username}' ({user.user_id}) updated password successfully"
            )
        return row, f"Password updated to '{new_password}' successfully."


UserServiceDep = Annotated[UserService, Depends(UserService)]

from fastapi import Depends, HTTPException, status
from loguru import logger

from .auth import get_current_user
from .schemas import User


class RequiredScopes:
    """Checks whether a user is authorized to access an endpoint based on scopes.

    Args:
        required_scopes (list[str]): A list of scopes required to access the endpoint.

    Returns:
        bool: True if the user has all required scopes.

    Raises:
        HTTPException: If the user does not have the required scopes.
    """

    def __init__(self, required_scopes: list[str]) -> None:
        self.required_scopes = required_scopes

    def __call__(self, user: User = Depends(get_current_user)) -> bool:
        missing_permissions = [
            permission
            for permission in self.required_scopes
            if permission not in user.scopes
        ]

        if missing_permissions:
            missing_permissions_str = ", ".join(missing_permissions)
            logger.warning(
                f"Unauthorized access attempt by {user.user_id} to protected endpoint "
                f"without required permission(s): {missing_permissions_str}"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Scopes"},
            )
        return True

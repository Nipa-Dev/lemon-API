from fastapi import HTTPException, Request


def raise_bad_request(message: str) -> None:
    """
    Raise a 400 Bad Request HTTPException.

    Args:
        message: The error message to include in the response.
    """
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request: Request) -> None:
    """
    Raise a 404 Not Found HTTPException for missing URLs.

    Args:
        request: The incoming request object, used to construct the error message.
    """
    message = f"URL '{request.url}' does not exist"
    raise HTTPException(status_code=404, detail=message)


def raise_unauthorized(detail: str = "Not authenticated") -> None:
    """
    Raise a 401 Unauthorized HTTPException.

    Args:
        detail: The error message to include in the response.
    """
    raise HTTPException(status_code=401, detail=detail)


def raise_forbidden(detail: str = "Not authorized") -> None:
    """
    Raise a 403 Forbidden HTTPException.

    Args:
        detail: The error message to include in the response.
    """
    raise HTTPException(status_code=403, detail=detail)
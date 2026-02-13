from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger

from lemonapi.utils import auth, dependencies
from lemonapi.utils.auth import get_current_active_user
from lemonapi.utils.constants import Server
from lemonapi.utils.schemas import AccessToken, NewUser, RefreshToken, User
from lemonapi.utils.services.user_service import UserServiceDep

router = APIRouter()


@router.get("/showtoken")
async def show_token(request: Request, token: Annotated[str | None, Cookie()] = None):
    """
    Retrieves the token from the request cookies and renders the "api_token.html" template with the token as a context variable.

    Args:
        request: The incoming request object.
        token: The token retrieved from the request cookies. Defaults to None.

    Returns:
        TemplateResponse: The rendered "api_token.html" template with the token as a context variable if the token is found.
        dict: A dictionary with a "detail" key set to "No token found" if the token is not found.
    """
    context = {"request": request}
    if token:
        context["token"] = token
        template_name = "api_token.html"
        return Server.TEMPLATES.TemplateResponse(template_name, context)

    else:
        return {"detail": "No token found"}


@router.post("/token")
async def login_for_refresh_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    pool: dependencies.PoolDep,
):
    """
    Endpoint to receive a refresh token. This token does not grant user permissions.

    Requires username and password.

    Args:
        request: The incoming request object.
        form_data: The OAuth2 password request form containing username and password.
        pool: The database connection pool.

    Returns:
        dict: A dictionary containing the refresh token and token type, or access token if from docs.

    Raises:
        HTTPException: When incorrect username or password is provided.
    """
    async with pool.acquire() as con:
        user = await auth.authenticate_user(
            form_data.username, form_data.password, request=request, pool=con
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = await con.fetchrow(
            "SELECT user_id FROM users WHERE username = $1", user.username
        )
        refresh_token, _ = await auth.reset_refresh_token(
            con=con,
            user_id=user_id[0],
        )
    log_user = user_id["user_id"]
    ip = request.client.host
    logger.info(f"Successful login from: user_id={log_user} | client_ip={ip}")
    redirect = RedirectResponse(url="/showtoken", status_code=303)
    redirect.set_cookie(
        key="token",
        value=refresh_token,
        httponly=True,
        max_age=Server.REFRESH_EXPIRE_IN,
        path="/showtoken",
    )
    headers = request.headers

    # If the request comes from docs, we want to give the access token upon
    # request so that we can test the API endpoint in the docs. If the
    # access_token would not be provided like this you would be unable to
    # test protected endpoints in the docs.
    if "referer" in headers and "/docs" in request.headers["referer"]:
        token = await authenticate(
            request, RefreshToken(refresh_token=refresh_token), pool=pool
        )
        return {
            "access_token": token["access_token"],
            "token_type": token["token_type"],
        }
    # Return redirect when request comes from /login endpoint
    elif "referer" in headers and "/login" in request.headers["referer"]:
        return redirect
    else:
        return {"refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/authenticate", response_model=AccessToken)
async def authenticate(
    request: Request,
    body: RefreshToken,
    pool: dependencies.PoolDep,
) -> dict:
    """
    Authenticate and get an access token.

    Users should replace their local refresh token with the one returned.

    Args:
        request: The incoming request object.
        body: The refresh token data.
        pool: The database connection pool.

    Returns:
        dict: A dictionary containing access token, token type, refresh token, and expiration time.
    """
    async with pool.acquire() as con:
        access, refresh = await auth.create_access_token(
            con=con,
            refresh_token=body.refresh_token,
            request=request,
        )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": Server.ACCESS_EXPIRE_IN,  # value in seconds
        "refresh_token": refresh,
    }


@router.post("/users/add/")
async def add_user(
    request: Request, user_service: UserServiceDep, user: NewUser = Depends()
):
    """
    Register a new user, add user to database with username and hashed password.

    Args:
        request: The incoming request object.
        user_service: The user service dependency.
        user: The new user data.

    Returns:
        The added user data.
    """
    added_user = await user_service.add_user(user)

    return added_user


@router.patch("/users/update/password")
async def update_password(
    request: Request,
    user: Annotated[User, Depends(get_current_active_user)],
    new_password: str,
    user_service: UserServiceDep,
):
    """
    Update user password.

    Args:
        request: The incoming request object.
        user: The current authenticated user.
        new_password: The new password to set.
        user_service: The user service dependency.

    Returns:
        dict: A dictionary with detail and timestamp.
    """
    row, message = await user_service.update_password(user, new_password)
    return {"detail": row, "dt": message}


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get the current authenticated user's information.

    Args:
        current_user: The current authenticated user.

    Returns:
        User: The user data.
    """
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    pool: dependencies.PoolDep,
):
    """
    Logout the current user by invalidating their refresh token.
    This will invalidate all existing refresh tokens for the user.

    Args:
        request: The incoming request object.
        current_user: The current authenticated user.
        pool: The database connection pool.

    Returns:
        dict: A dictionary with a logout confirmation message.
    """
    async with pool.acquire() as con:
        await auth.invalidate_refresh_token(con, current_user.user_id)

    response = {"detail": "Successfully logged out"}
    return response


@router.get("/login", include_in_schema=False)
async def login(request: Request):
    """
    Render the login page template.

    Args:
        request: The incoming request object.

    Returns:
        TemplateResponse: The rendered login.html template.
    """
    context = {"request": request}
    template_name = "login.html"
    return Server.TEMPLATES.TemplateResponse(template_name, context)

from typing import Annotated
from asyncpg import Connection

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Cookie
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from lemonapi.utils import auth
from lemonapi.utils import crud

from lemonapi.utils.constants import Server, get_db
from lemonapi.utils.auth import (
    User,
    get_current_active_user,
    RefreshToken,
    AccessToken,
)

router = APIRouter()


@router.post("/token")
async def login_for_refresh_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Connection, Depends(get_db)],
):
    """
    Endpoint to receive a refresh token. This token does not grant user
    permissions.

    Requires username and password.

    Returns
    -------
        refresh token and token type.

    Raises
    ------
    HTTPException
        When incorrect username or password is provided.
    """
    user = await auth.authenticate_user(form_data.username, form_data.password, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = await db.fetchrow(
        "SELECT user_id FROM users WHERE username = $1", user.username
    )
    refresh_token, _ = await auth.reset_refresh_token(
        db=db,
        user_id=user_id[0],
    )
    redirect = RedirectResponse(url="/showtoken", status_code=303)
    redirect.set_cookie(
        key="token",
        value=refresh_token,
        httponly=True,
        max_age=10,
        path="/showtoken",
    )
    headers = request.headers
    if "referer" in headers and "/login" in request.headers["referer"]:
        return redirect
    else:
        return {"refresh": refresh_token, "token_type": "bearer"}


@router.post("/authenticate", response_model=AccessToken)
async def authenticate(
    body: RefreshToken,
    db: Annotated[Connection, Depends(get_db)],
) -> dict:
    """
    Authenticate and get an access token.

    Users should replace their local refresh token with the one returned.

    Returns
    -------
    dict
        containing access token, token type, refresh token, and expiration time.
        Response model is AccessToken.
    """
    access, refresh = await auth.create_access_token(
        db=db,
        refresh_token=body.refresh_token,
    )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": Server.ACCESS_EXPIRE_IN,  # value in seconds
        "refresh_token": refresh,
    }


@router.post("/users/add/")
async def add_user(
    request: Request, user: auth.NewUser = Depends(), db: Connection = Depends(get_db)
):
    """Register a new user, add user to database with username and hashed password."""
    db_user = await crud.add_user(db, user)
    return db_user


@router.get("/showtoken")
async def show_token(request: Request, token: Annotated[str | None, Cookie()] = None):
    context = {"request": request}
    if token:
        context["token"] = token
        template_name = "api_token.html"
        return Server.TEMPLATES.TemplateResponse(template_name, context)

    else:
        return {"detail": "No token found"}


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/login", include_in_schema=False)
async def login(request: Request):
    context = {"request": request}
    template_name = "login.html"
    return Server.TEMPLATES.TemplateResponse(template_name, context)

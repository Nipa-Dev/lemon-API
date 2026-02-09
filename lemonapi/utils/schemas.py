from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class URLBase(BaseModel):
    target_url: HttpUrl


class URL(URLBase):
    is_active: bool
    clicks: int
    url_key: str


class URLInfo(URL):
    url: str
    admin_url: str


class URLInspectResponse(BaseModel):
    original_url: HttpUrl
    short_key: str
    redirects_to: HttpUrl
    created_at: datetime


class URLDeleteResponse(URLBase):
    url_key: str
    deleted: bool


class NoteCreate(BaseModel):
    title: str
    slug: str
    content: str
    tags: Optional[List[str]] = None


# Authentication-related models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    scopes: list[str] = []


class User(BaseModel):
    username: str
    user_id: str
    email: str | None = None
    full_name: str | None = None
    is_disabled: bool | None = None
    scopes: list[str] = []


class UserInDB(User):
    hashed_password: str


class NewUser(BaseModel):
    username: str
    password: str
    email: str
    full_name: str


class RefreshToken(BaseModel):
    refresh_token: str


class AccessToken(RefreshToken):
    """Used as a response for requesting a new access token."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str

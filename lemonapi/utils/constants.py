from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from fastapi import Request

from fastapi.templating import Jinja2Templates


class _Server(BaseSettings):
    """Server class to handle the server constant variables."""

    model_config = SettingsConfigDict(
        validate_default=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # the 4 constants below are used in authentication file (auth.py)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_IN: int = 3600  # value in seconds
    REFRESH_EXPIRE_IN: int = ACCESS_EXPIRE_IN * 6

    DEBUG: bool
    IMPORT_NOTE_EXTENSIONS: set[str] = {".md", ".txt"}

    IMPORT_NOTES_PATH: Path

    # Database connection
    DB_HOST: str
    DB_NAME: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_USER: str

    TEMPLATES: Jinja2Templates = Jinja2Templates(directory="lemonapi/templates")

    SCOPES: list[str] = ["users:read"]
    # key length is used for shortened urls.
    # value of default 5 generates shortened urls like:
    # http://localhost:5000/UEFIS
    KEY_LENGTH: int = 5
    SECRET_KEY_LENGTH: int = 10


Server = _Server()


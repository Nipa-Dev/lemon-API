from fastapi import status, HTTPException
from lemonapi.utils.constants import Server

from sqlalchemy.orm import Session

from . import keygen, models, schemas, auth


def get_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.is_active)
        .first()
    )


def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )


def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url


def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    key = keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    db_url = models.URL(target_url=url.target_url, key=key, secret_key=secret_key)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url


def get_list_of_usernames(db: Session) -> list[str]:
    return [user.username for user in db.query(models.User).all()]


def add_user(db: Session, user: auth.NewUser) -> models.User:
    username_taken = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Username already exists.",
    )
    if user.username in get_list_of_usernames(db):
        raise username_taken  # raise exception if username already exists
    db_user = models.User(
        username=user.username,
        hashed_password=auth.get_password_hash(user.password),
        fullname=user.full_name,
        email=user.email,
        scopes=[Server.SCOPES[0]],
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

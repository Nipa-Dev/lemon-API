import validators

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from typing import Annotated
from loguru import logger

from lemonapi.utils import schemas
from lemonapi.utils.constants import Server
from lemonapi.utils.services.url_service import UrlServiceDep
from lemonapi.utils.errors import raise_not_found

router = APIRouter()


templates = Jinja2Templates(directory="lemonapi/templates")


@router.get("/short/{url_key}", include_in_schema=False)
async def forward_to_target_url(
    request: Request, url_key: str, url_service: UrlServiceDep
):
    """
    Forwards a request to the target URL based on the provided URL key.

    Args:
        request (Request): The incoming request object.
        url_key (str): The key of the URL to be forwarded.
        url_service (UrlServiceDep): The URL service dependency.

    Returns:
        RedirectResponse: A redirect response to the target URL if the URL key exists.

    Raises:
        HTTPException: If the URL key does not exist, a 404 HTTPException is raised.
    """
    if url_key == "docs":
        return RedirectResponse("/docs/")
    row = await url_service.get_db_url_by_key(url_key=url_key)

    try:
        url_object = schemas.URL(**dict(row))
    except Exception as e:
        logger.trace(e)
    if row:
        row = await url_service.update_db_clicks(db_url=url_object)

        return RedirectResponse(row["target_url"])
    else:
        raise_not_found(request)


@router.delete("/admin/{secret_key}")
async def delete_url(request: Request, secret_key: str, url_service: UrlServiceDep):
    """
    Deletes a URL by its secret key.

    Args:
        request (Request): The incoming request object.
        secret_key (str): The secret key of the URL to be deleted.
        url_service (UrlServiceDep): The URL service dependency.

    Returns:
        dict: A dictionary containing the detail message of the deleted URL.

    Raises:
        HTTPException: If the URL with the given secret key is not found.
    """
    if row := await url_service.deactivate_db_url_by_secret_key(secret_key=secret_key):
        message = f"""
        Deleted URL for '{row["url_key"]} -> {row["target_url"]}'
        """
        # if message above fails, it is due to row being None as it's inactive and not
        # selected by database query resulting to server raising Internal Server Error
        return {"detail": message}
    else:
        raise_not_found(request)


@router.post("/url/")
async def create_url(url: schemas.URLBase, url_service: UrlServiceDep):
    """
    Create a new URL in the database.

    Parameters:
        url (schemas.URLBase): The URL object containing the target URL.
        url_service (UrlServiceDep): The URL service dependency.

    Returns:
        The created URL object.

    Raises:
        HTTPException: If the provided URL is invalid.
    """
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")
    db_url = await url_service.create_db_url(url=url)

    return db_url


@router.get("/url/inspect")
async def inspect_url(
    url_service: UrlServiceDep, url: Annotated[schemas.URLBase, Depends()]
):
    """
    Inspects a URL and returns information about it.

    Parameters:
        url_service (UrlServiceDep): The URL service dependency.
        url (Annotated[schemas.URLBase, Depends()]): The URL object containing the target URL.

    Returns:
        dict: A dictionary containing the detail message of the inspected URL. The message includes the target URL and the creation date.

    Raises:
        HTTPException: If the provided URL is invalid or the URL key length does not match the defined length.
    """
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")

    url_key = url.target_url.split("/")[-1]
    # url key length does not match the defined length, raise HTTPException
    if len(url_key) != Server.KEY_LENGTH:
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")

    url_info = await url_service.get_db_url_by_key(url_key=url_key)

    target = url_info["target_url"]  # target where 'url.target_url' redirects to
    created_at = url_info["created_at"]

    message = (
        f"URL '{url.target_url}' redirects to '{target}'. Created at: {created_at}"
    )

    return {"detail": message}

import datetime
import pathlib
import socket
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from lemonapi.endpoints import lemons, notes, search, security, shortener
from lemonapi.utils.auth import get_current_active_user
from lemonapi.utils.constants import Server
from lemonapi.utils.database import Connection

description = """Random API"""

favicon_path = pathlib.Path("./static/images/favicon.ico")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        logger.info(f"Local network: http://{local_ip}:8000")
    except Exception:
        logger.error("Failure to get local network IP address.")
        logger.trace(
            "Startup failed to receive network IP address, proceeding anyways."
        )

    logger.info(f"Server started at: {datetime.datetime.now(datetime.timezone.utc)}")

    # possible error that might happen: socket.gaierror, if it keeps persisting,
    # try adding try-except block to catch it and re-do the `await Connection.DB_POOL`
    # within the block

    # Create database connection pool
    await Connection.DB_POOL

    yield
    # closing down, anything after yield will be ran as shutdown event.
    await Connection.DB_POOL.close()
    logger.info(
        f"Server shutting down at: {datetime.datetime.now(datetime.timezone.utc)}"
    )


app = FastAPI(
    title="API",
    description=description,
    version="0.2",
    terms_of_service="http://example.com/terms/",
    license_info={
        "name": "MIT license",
        "url": "https://github.com/Nipa-Code/lemon-API/blob/main/LICENSE",
    },
    docs_url="/altdocs",  # set docs to None to use custom template
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory="lemonapi/static"),
    name="static",
)
# include coverage reports
app.mount("/coverage/", StaticFiles(directory="htmlcov", html=True), name="coverage")

# By default this value is set to False and is configured without need of user.
# This is only used for testing purposes during development.
if Server.DEBUG:
    from lemonapi.endpoints import testing

    app.include_router(testing.router, tags=["testing"])

app.include_router(security.router, tags=["security"])
app.include_router(
    lemons.router, tags=["lemons"], dependencies=[Depends(get_current_active_user)]
)
app.include_router(shortener.router, tags=["shortener"])
app.include_router(notes.router, tags=["notes"])
app.include_router(search.router, tags=["search"])


@app.exception_handler(StarletteHTTPException)
async def my_exception_handler(request: Request, exception: StarletteHTTPException):
    """Custom exception handler for 404 error."""
    if exception.status_code == 404:
        name = "error.html"
        return Server.TEMPLATES.TemplateResponse(
            request=request, name=name, status_code=404
        )

    else:
        return Response(
            content=str(exception.detail), status_code=exception.status_code
        )


@app.get("/docs/", include_in_schema=False)
async def get_docs(request: Request):
    """Generate documentation for API instead of using the default documentation."""
    name = "docs.html"
    return Server.TEMPLATES.TemplateResponse(
        request=request, name=name, status_code=200
    )


@app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
async def get_favicon():
    """This is the favicon.ico file that is returned from the server."""
    return FileResponse(favicon_path)


@app.get("/", include_in_schema=False)
async def home():
    """
    Endpoint to forward requests to documentation instead of empty home page.
    :param request:
    :return: RedirectResponse
    """
    return RedirectResponse("/docs/")


@app.get("/status/")
async def server_status(request: Request) -> Response:
    return Response(content="Server is running.", status_code=200)

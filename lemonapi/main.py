import datetime
import socket
import logging
import asyncio
import pathlib

from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, Response, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lemonapi.endpoints import shortener, lemons, security  # moderation
from lemonapi.utils.constants import Server
from lemonapi.utils.auth import get_current_active_user
from lemonapi.utils.database import Connection
from lemonapi.utils import promthutils

description = """Random API"""

favicon_path = pathlib.Path("./static/images/favicon.ico")

app = FastAPI(
    title="API",
    description=description,
    version="0.2",
    terms_of_service="http://example.com/terms/",
    license_info={
        "name": "MIT license",
        "url": "https://github.com/Nipa-Code/lemon-API/blob/main/LICENSE",
    },
    docs_url=None,  # set docs to None and use custom template
    redoc_url=None,
)
# initialize prometheus metrics
Instrumentator().instrument(app).expose(app)

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

# Add prometheus middleware
# NOTE this requires new implementation as it slows down the server
app.add_middleware(promthutils.PrometheusMiddleware, app_name="web")


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


@app.exception_handler(StarletteHTTPException)
async def my_exception_handler(request: Request, exception: StarletteHTTPException):
    """Custom exception handler for 404 error."""
    if exception.status_code == 404:
        name = "error.html"
        return Server.TEMPLATES.TemplateResponse(
            name=name, context={"request": request}, status_code=404
        )

    else:
        return Response(
            content=str(exception.detail), status_code=exception.status_code
        )


@app.on_event("startup")
async def startup() -> None:
    """Startup event for the server."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        logger.info(f"Local network: http://{local_ip}:5001")
    except Exception:
        logger.error("Failure to get local network IP address.")
        logger.trace(
            "Startup failed to receive network IP address, proceeding anyways."
        )

    logger.info(f"Server started at: {datetime.datetime.now()}")
    # Create database connection pool
    try:
        await Connection.DB_POOL
    except socket.gaierror:
        logger.trace("Failed to connect to database, retrying in 1 second.")
        await asyncio.sleep(1)
        await Connection.DB_POOL

    logger.trace("Initialized database connection pool.")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Shutdown event for the server."""
    logger.info(f"Server shutting down at: {datetime.datetime.now()}")
    # Close database connection pool
    await Connection.DB_POOL.close()
    logger.trace("Database connection pool closed")


@app.get("/docs/", include_in_schema=False)
async def get_docs(request: Request):
    """Generate documentation for API instead of using the default documentation."""
    name = "docs.html"
    return Server.TEMPLATES.TemplateResponse(name, {"request": request}, 200)


@app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
async def get_favicon(request: Request):
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
async def server_status() -> Response:
    return Response(content="Server is running.", status_code=200)

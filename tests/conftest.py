import os
import sys
from pathlib import Path

# We are running podman on rootless mode, this needs to be set true
os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"
os.environ["DOCKER_HOST"] = f"unix:///run/user/{os.getuid()}/podman/podman.sock"


import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

# Add project root to sys.path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from lemonapi.main import app
from lemonapi.utils.dependencies import get_pool

# Test database URL
TEST_DATABASE_URL = "postgres://test:test_password@localhost:5432/lemonapi_test"

# Podman/PostgreSQL config
PG_CONTAINER = "database"
PG_USER = "test"
PG_DB = "lemonapi_test"

INIT_SQL = Path(__file__).resolve().parent.parent / "postgres" / "init.sql"


'''
@pytest.fixture()
async def test_pool():
    """Create a connection pool to the test database."""
    pool = await asyncpg.create_pool(TEST_DATABASE_URL)
    yield pool
    await pool.close()
'''


@pytest.fixture
async def test_pool():
    """Start container, create pool, and initialize schema."""
    # Start PostgreSQL container
    with PostgresContainer(
        "postgres:16", dbname="lemonapi_test", username="test", password="test_password"
    ) as container:
        conn_url = container.get_connection_url()
        conn_url = conn_url.replace("+psycopg2", "")

        pool = await asyncpg.create_pool(conn_url)

        # Initialize schema + seed data
        async with pool.acquire() as conn:
            await conn.execute(INIT_SQL.read_text())

        yield pool
        await pool.close()


@pytest.fixture
async def client(test_pool):
    """
    AsyncClient fixture for testing.
    If `auth=True` is passed, automatically authenticates and attaches Bearer token.
    """

    async def override_get_pool():
        return test_pool

    app.dependency_overrides[get_pool] = override_get_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:

        async def _client(auth: bool = False):
            if auth:
                login_data = {"username": "admin", "password": "weakadmin"}
                headers = {"Content-Type": "application/x-www-form-urlencoded"}

                token_resp = await ac.post("/token", data=login_data, headers=headers)
                token_json = token_resp.json()

                # Use refresh token if access_token is not returned
                refresh_token = token_json["refresh_token"]

                res = await ac.post(
                    "/authenticate", json={"refresh_token": refresh_token}
                )
                auth_data = res.json()
                access_token = auth_data["access_token"]
                if not access_token:
                    raise RuntimeError(f"No token returned: {token_resp.text}")

                ac.headers.update({"Authorization": f"Bearer {access_token}"})

            return ac

        yield _client

import pytest


@pytest.mark.anyio
async def test_server_status(client):
    ac = await client()
    res = await ac.get("/status/")
    assert res.status_code == 200


@pytest.mark.anyio
async def test_docs_status(client):
    ac = await client()
    res = await ac.get("/docs/")
    assert res.status_code == 200


@pytest.mark.anyio
async def test_coverage_status(client):
    ac = await client()
    res = await ac.get("/coverage/")
    assert res.status_code == 200

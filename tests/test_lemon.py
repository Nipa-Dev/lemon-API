import pytest

from lemonapi.data import facts


@pytest.mark.anyio
async def test_random_fact(client):
    ac = await client(auth=True)
    res = await ac.get("/lemon/facts/random")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["message"] in facts.LEMON_FACTS


@pytest.mark.anyio
@pytest.mark.parametrize(
    "count, should_fail",
    [
        (0, True),
        (3, False),
        (6, True),
    ],
)
async def test_amount(client, count, should_fail):
    ac = await client(auth=True)
    res = await ac.get(f"/lemon/facts/amount?count={count}")

    if should_fail:
        assert res.status_code == 422
    else:
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        for fact in data["message"]:
            assert fact in facts.LEMON_FACTS


@pytest.mark.anyio
async def test_verbs(client):
    ac = await client(auth=True)
    res = await ac.get("/lemon/verbs")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["message"] in facts.LEMON_VERBS


@pytest.mark.anyio
async def test_nouns(client):
    ac = await client(auth=True)
    res = await ac.get("/lemon/nouns")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["message"] in facts.LEMON_NOUNS


@pytest.mark.anyio
async def test_random_quote(client):
    ac = await client(auth=True)
    response = await ac.get("/quotes/random")
    response.raise_for_status()
    data = response.json()

    assert "author" in data
    assert "quote" in data

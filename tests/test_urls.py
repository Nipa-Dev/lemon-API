import pytest


@pytest.mark.anyio
@pytest.mark.parametrize(
    "valid_url",
    [
        {"target_url": "http://127.0.0.1:8000/login"},
        {"target_url": "https://example.com"},
        {"target_url": "http://localhost:3000/api"},
        {"target_url": "https://sub.domain.com/path?query=123"},
    ],
)
async def test_create_url_valid(client, valid_url):
    ac = await client()
    res = await ac.post("/url/", json=valid_url)
    assert res.status_code == 200


@pytest.mark.anyio
@pytest.mark.anyio
@pytest.mark.parametrize(
    "bad_url",
    [
        {"target_url": "http://"},
        {"target_url": "://example.com"},
        {"target_url": "http://?foo=bar"},
        {"target_url": "http://#fragment"},
        {"target_url": "not a url"},
        {"target_url": "http://exa mple.com"},
    ],
)
async def test_create_url_fail(client, bad_url):
    ac = await client()
    res = await ac.post("/url/", json=bad_url)
    assert res.status_code == 422


@pytest.mark.anyio
async def test_url_lifecycle(client):
    ac = await client()

    create_res = await ac.post(
        "/url/", json={"target_url": "http://127.0.0.1:8000/login"}
    )
    assert create_res.status_code == 200

    create_data = create_res.json()
    url_key = create_data["url_key"]
    original_url = create_data["target_url"]
    secret_key = create_data["secret_key"]

    inspect_res = await ac.get(
        "/url/inspect", params={"target_url": f"http://127.0.0.1:8000/short/{url_key}"}
    )
    assert inspect_res.status_code == 200

    inspect_data = inspect_res.json()

    assert inspect_data["original_url"] == f"http://127.0.0.1:8000/short/{url_key}"
    assert inspect_data["short_key"] == url_key
    assert inspect_data["redirects_to"] == original_url
    assert "created_at" in inspect_data

    delete_res = await ac.delete(f"/admin/{secret_key}")
    assert delete_res.status_code == 200

    delete_data = delete_res.json()

    assert delete_data["url_key"] == url_key
    assert delete_data["target_url"] == original_url
    assert delete_data["deleted"] is True

    inspect_after_delete = await ac.get(
        "/url/inspect", params={"target_url": f"http://127.0.0.1:8000/short/{url_key}"}
    )
    assert inspect_after_delete.status_code == 404

    delete_again = await ac.delete(f"/admin/{secret_key}")
    assert delete_again.status_code == 404

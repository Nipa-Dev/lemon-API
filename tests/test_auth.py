import uuid

import pytest

BASE_TEST_USER = {
    "username": "testuser",
    "password": "TestPass123!",
    "email": "testuser@example.com",
    "full_name": "Test User",
}

NEW_PASSWORD = "NewTestPass456!"


@pytest.mark.anyio
async def test_user_flow(client):
    # Generate unique username and email per test run
    unique_id = uuid.uuid4().hex[:8]  # 8-char unique suffix
    test_user = {
        "username": f"{BASE_TEST_USER['username']}_{unique_id}",
        "password": BASE_TEST_USER["password"],
        "email": f"{unique_id}_{BASE_TEST_USER['email']}",
        "full_name": BASE_TEST_USER["full_name"],
    }

    # Step 0: get client
    ac = await client()

    # Step 1: Create user
    res = await ac.post(
        "/users/add/",
        params={
            "username": test_user["username"],
            "password": test_user["password"],
            "email": test_user["email"],
            "full_name": test_user["full_name"],
        },
    )
    assert res.status_code == 200

    # Step 2: Login to get refresh token
    res = await ac.post(
        "/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"],
        },
    )
    assert res.status_code == 200
    login_data = res.json()
    assert "refresh_token" in login_data
    refresh_token = login_data["refresh_token"]

    # Step 3: Authenticate to get access token
    res = await ac.post("/authenticate", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    auth_data = res.json()
    assert "access_token" in auth_data
    access_token = auth_data["access_token"]

    # Step 4: Use access token to get /users/me
    ac_auth = await client()
    ac.headers.update({"Authorization": f"Bearer {access_token}"})

    res = await ac_auth.get(
        "/users/me",
    )
    assert res.status_code == 200
    user_data = res.json()

    # uses the default session?
    assert user_data["username"] == test_user["username"]
    assert user_data["email"] == test_user["email"]

    # Step 5: Update password
    res = await ac_auth.patch(
        "/users/update/password",
        params={"new_password": NEW_PASSWORD},
    )
    assert res.status_code == 200

    # Step 6: Login again with new password
    res = await ac.post(
        "/token",
        data={"username": test_user["username"], "password": NEW_PASSWORD},
    )
    assert res.status_code == 200
    new_login_data = res.json()
    assert "refresh_token" in new_login_data

    await ac.aclose()
    await ac_auth.aclose()

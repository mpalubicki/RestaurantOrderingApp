def test_register_login_logout_flow(client):
    res = client.post(
        "/register",
        data={
            "email": "test@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
        },
        follow_redirects=False,
    )

    if res.status_code == 200:
        body = res.get_data(as_text=True)
        # This will show form validation messages in the pytest output
        raise AssertionError(f"Register did not redirect (200). Response body:\n{body[:2000]}")

    assert res.status_code in (302, 303)

    res = client.post(
        "/login",
        data={"email": "test@example.com", "password": "Password123!"},
        follow_redirects=False,
    )
    if res.status_code == 200:
        body = res.get_data(as_text=True)
        raise AssertionError(f"Login did not redirect (200). Response body:\n{body[:2000]}")
    assert res.status_code in (302, 303)

    res = client.get("/logout", follow_redirects=False)
    assert res.status_code in (302, 303)

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
    assert res.status_code in (302, 303)

    res = client.post(
        "/login",
        data={"email": "test@example.com", "password": "Password123!"},
        follow_redirects=False,
    )
    assert res.status_code in (302, 303)

    res = client.get("/logout", follow_redirects=False)
    assert res.status_code in (302, 303)

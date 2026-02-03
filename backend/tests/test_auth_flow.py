import re


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert match, "Could not find csrf_token in HTML"
    return match.group(1)


def test_register_login_logout_flow(client):
    res = client.get("/register")
    assert res.status_code == 200
    csrf_token = _extract_csrf_token(res.get_data(as_text=True))

    res = client.post(
        "/register",
        data={
            "csrf_token": csrf_token,
            "email": "test@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
        },
        follow_redirects=False,
    )

    assert res.status_code in (302, 303), f"Expected redirect after register, got {res.status_code}"

    res = client.get("/login")
    assert res.status_code == 200
    csrf_token = _extract_csrf_token(res.get_data(as_text=True))

    res = client.post(
        "/login",
        data={
            "csrf_token": csrf_token,
            "email": "test@example.com",
            "password": "Password123!",
        },
        follow_redirects=False,
    )
    assert res.status_code in (302, 303), f"Expected redirect after login, got {res.status_code}"

    res = client.get("/logout", follow_redirects=False)
    assert res.status_code in (302, 303)

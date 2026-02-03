import re


def _extract_csrf_token(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "Could not find csrf_token in HTML"
    return m.group(1)


def test_register_login_logout_flow(client):
    res = client.get("/register")
    assert res.status_code == 200
    csrf = _extract_csrf_token(res.get_data(as_text=True))

    res = client.post(
        "/register",
        data={
            "csrf_token": csrf,
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=False,
    )
    assert res.status_code in (302, 303), f"Expected redirect after register, got {res.status_code}"

    res = client.get("/register")
    assert res.status_code == 200
    csrf = _extract_csrf_token(res.get_data(as_text=True))

    res = client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    assert res.status_code in (302, 303), f"Expected redirect after logout, got {res.status_code}"

    res = client.get("/login")
    assert res.status_code == 200
    csrf = _extract_csrf_token(res.get_data(as_text=True))

    res = client.post(
        "/login",
        data={
            "csrf_token": csrf,
            "email": "test@example.com",
            "password": "Password123!",
        },
        follow_redirects=False,
    )
    assert res.status_code in (302, 303), f"Expected redirect after login, got {res.status_code}"

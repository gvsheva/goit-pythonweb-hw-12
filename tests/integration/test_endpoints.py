from datetime import date, timedelta


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}




def test_register_user(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert body["id"] > 0


def test_request_verification_and_verify(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text

    rv = client.post("/auth/request-verification", params={"email": email})
    assert rv.status_code == 200, rv.text
    token = rv.json()["verification_token"]

    rv2 = client.get("/auth/verify", params={"token": token})
    assert rv2.status_code == 200, rv2.text
    assert rv2.json()["detail"].lower().startswith("email")


def test_login_and_me_endpoint(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]

    me = client.get("/api/users/me", headers=auth_headers(access))
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_contacts_crud_endpoints(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    # Register and login
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]

    # Create contact 1
    c1 = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": fake.unique.email(),
            "phone": fake.unique.phone_number(),
            "birthday": None,
            "extra_info": None,
        },
    )
    assert c1.status_code == 201, c1.text
    contact1 = c1.json()

    # Create contact 2
    c2 = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "Soon",
            "last_name": "Person",
            "email": fake.unique.email(),
            "phone": fake.unique.phone_number(),
            "birthday": None,
            "extra_info": None,
        },
    )
    assert c2.status_code == 201, c2.text

    # List
    lst = client.get("/api/contacts", headers=auth_headers(access))
    assert lst.status_code == 200
    assert len(lst.json()) == 2

    # Filter
    flt = client.get(
        "/api/contacts",
        headers=auth_headers(access),
        params={"first_name": "jo"},
    )
    assert flt.status_code == 200
    assert len(flt.json()) == 1

    # Get by id
    got = client.get(f"/api/contacts/{contact1['id']}", headers=auth_headers(access))
    assert got.status_code == 200
    assert got.json()["email"] == contact1["email"]

    # Update
    upd = client.put(
        f"/api/contacts/{contact1['id']}",
        headers=auth_headers(access),
        json={"phone": "99999", "extra_info": "Friend"},
    )
    assert upd.status_code == 200
    assert upd.json()["phone"] == "99999"
    assert upd.json()["extra_info"] == "Friend"

    # Delete and ensure missing
    dele = client.delete(
        f"/api/contacts/{contact1['id']}", headers=auth_headers(access)
    )
    assert dele.status_code == 204

    missing = client.get(f"/api/contacts/{contact1['id']}", headers=auth_headers(access))
    assert missing.status_code == 404


def test_upcoming_birthdays_endpoint(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    # Register and login
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]

    today = date.today()
    in_3 = today + timedelta(days=3)
    in_10 = today + timedelta(days=10)
    yesterday = today - timedelta(days=1)

    def md(d: date) -> str:
        return date(2000, d.month, d.day).isoformat()

    # Create contacts with birthdays
    email_today = fake.unique.email()
    email_soon = fake.unique.email()
    email_later = fake.unique.email()
    email_past = fake.unique.email()
    c_today = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "Today",
            "last_name": "Person",
            "email": email_today,
            "phone": fake.unique.phone_number(),
            "birthday": md(today),
            "extra_info": None,
        },
    )
    assert c_today.status_code == 201, c_today.text

    c_soon = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "Soon",
            "last_name": "Person",
            "email": email_soon,
            "phone": fake.unique.phone_number(),
            "birthday": md(in_3),
            "extra_info": None,
        },
    )
    assert c_soon.status_code == 201, c_soon.text

    c_later = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "Later",
            "last_name": "Person",
            "email": email_later,
            "phone": fake.unique.phone_number(),
            "birthday": md(in_10),
            "extra_info": None,
        },
    )
    assert c_later.status_code == 201, c_later.text

    c_past = client.post(
        "/api/contacts",
        headers=auth_headers(access),
        json={
            "first_name": "Past",
            "last_name": "Person",
            "email": email_past,
            "phone": fake.unique.phone_number(),
            "birthday": md(yesterday),
            "extra_info": None,
        },
    )
    assert c_past.status_code == 201, c_past.text

    upc = client.get(
        "/api/contacts/upcoming_birthdays",
        headers=auth_headers(access),
        params={"days": 3},
    )
    assert upc.status_code == 200, upc.text
    emails = {c["email"] for c in upc.json()}
    assert email_soon in emails or email_today in emails
    assert email_later not in emails
    assert email_past not in emails


def test_refresh_token_flow(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPassw0rd!"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    refresh = r.json()["refresh_token"]

    ref = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert ref.status_code == 200, ref.text
    body = ref.json()
    assert "access_token" in body and "refresh_token" in body


def test_rate_limit_on_me_endpoint(test_client, fake):
    client = test_client
    email = fake.unique.email()
    password = "StrongPass2!"

    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]

    codes = []
    for _ in range(6):
        resp = client.get("/api/users/me", headers=auth_headers(access))
        codes.append(resp.status_code)
    assert codes[:4] == [200, 200, 200, 200]
    assert codes[4] == 429

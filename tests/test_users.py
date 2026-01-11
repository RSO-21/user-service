from app.models import User


def test_get_user_404(client):
    r = client.get("/users/non-existent")
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_get_user_ok_in_public(client, app_and_engine):
    _, engine = app_and_engine

    # Insert into public schema
    with engine.begin() as conn:
        conn.exec_driver_sql("SET search_path TO public")
        conn.exec_driver_sql(
            """
            INSERT INTO users (id, username, email, name, surname, address, longitude, latitude, partner_id, cart, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now(), now())
            """,
            (
                "00000000-0000-0000-0000-000000000001",
                "tina",
                "tina@example.com",
                "Tina",
                "Test",
                "Street 1",
                14.5,
                46.0,
                None,
                [],
            ),
        )

    r = client.get("/users/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "00000000-0000-0000-0000-000000000001"
    assert body["username"] == "tina"
    assert body["email"] == "tina@example.com"
    assert body["cart"] == []


def test_tenant_isolation(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000010"

    with engine.begin() as conn:
        conn.exec_driver_sql("SET search_path TO tenant_a")
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, cart, created_at, updated_at) VALUES (%s,%s,%s,%s, now(), now())",
            (user_id, "a", "a@example.com", []),
        )

        conn.exec_driver_sql("SET search_path TO tenant_b")
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, cart, created_at, updated_at) VALUES (%s,%s,%s,%s, now(), now())",
            (user_id, "b", "b@example.com", []),
        )

    r_a = client.get(f"/users/{user_id}", headers={"X-Tenant-Id": "tenant_a"})
    r_b = client.get(f"/users/{user_id}", headers={"X-Tenant-Id": "tenant_b"})

    assert r_a.status_code == 200
    assert r_a.json()["email"] == "a@example.com"

    assert r_b.status_code == 200
    assert r_b.json()["email"] == "b@example.com"


def test_patch_updates_only_sent_fields(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000002"

    with engine.begin() as conn:
        conn.exec_driver_sql("SET search_path TO public")
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, name, cart, created_at, updated_at) VALUES (%s,%s,%s,%s,%s, now(), now())",
            (user_id, "x", "x@example.com", "Old", []),
        )

    r = client.patch(f"/users/{user_id}", json={"name": "New"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New"
    assert body["email"] == "x@example.com"


def test_cart_duplicates_and_delete_removes_one(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000003"

    with engine.begin() as conn:
        conn.exec_driver_sql("SET search_path TO public")
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, cart, created_at, updated_at) VALUES (%s,%s,%s,%s, now(), now())",
            (user_id, "c", "c@example.com", []),
        )

    r1 = client.post(f"/users/{user_id}/cart/7")
    assert r1.status_code == 200
    assert r1.json()["cart"] == [7]

    r2 = client.post(f"/users/{user_id}/cart/7")
    assert r2.status_code == 200
    assert r2.json()["cart"] == [7, 7]

    r3 = client.delete(f"/users/{user_id}/cart/7")
    assert r3.status_code == 200
    assert r3.json()["cart"] == [7]

def _insert_user(engine, schema: str, user_id: str, username: str, email: str, cart=None):
    if cart is None:
        cart = []
    with engine.begin() as conn:
        conn.exec_driver_sql(f"SET search_path TO {schema}")
        conn.exec_driver_sql(
            """
            INSERT INTO users (id, username, email, cart, created_at, updated_at)
            VALUES (%s,%s,%s,%s, now(), now())
            """,
            (user_id, username, email, cart),
        )


def test_get_user_404(client):
    r = client.get("/non-existent")
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_get_user_ok_in_public(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000001"
    _insert_user(engine, "public", user_id, "tina", "tina@example.com", [])

    r = client.get(f"/{user_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == user_id
    assert body["username"] == "tina"
    assert body["email"] == "tina@example.com"
    assert body["cart"] == []


def test_tenant_isolation(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000010"

    _insert_user(engine, "tenant_a", user_id, "a", "a@example.com", [])
    _insert_user(engine, "tenant_b", user_id, "b", "b@example.com", [])

    r_a = client.get(f"/{user_id}", headers={"X-Tenant-Id": "tenant_a"})
    r_b = client.get(f"/{user_id}", headers={"X-Tenant-Id": "tenant_b"})

    assert r_a.status_code == 200
    assert r_a.json()["email"] == "a@example.com"

    assert r_b.status_code == 200
    assert r_b.json()["email"] == "b@example.com"


def test_patch_updates_only_sent_fields(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000002"
    _insert_user(engine, "public", user_id, "x", "x@example.com", [])

    r = client.patch(f"/{user_id}", json={"name": "New"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New"
    assert body["email"] == "x@example.com"


def test_cart_duplicates_and_delete_removes_one(client, app_and_engine):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000003"
    _insert_user(engine, "public", user_id, "c", "c@example.com", [])

    r1 = client.post(f"/{user_id}/cart/7")
    assert r1.status_code == 200
    assert r1.json()["cart"] == [7]

    r2 = client.post(f"/{user_id}/cart/7")
    assert r2.status_code == 200
    assert r2.json()["cart"] == [7, 7]

    r3 = client.delete(f"/{user_id}/cart/7")
    assert r3.status_code == 200
    assert r3.json()["cart"] == [7]


def test_clear_cart_endpoint(client, app_and_engine):
    """
    NOTE: clear_cart endpoint is NOT under router; it's defined as:
    DELETE /users/{user_id}/cart
    """
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000006"
    _insert_user(engine, "public", user_id, "cc", "cc@example.com", [1, 2, 2])

    r = client.delete(f"/users/{user_id}/cart")
    assert r.status_code == 200
    assert r.json()["cart"] == []

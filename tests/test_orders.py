import datetime

class _FakeTimestamp:
    def __init__(self, dt: datetime.datetime):
        self._dt = dt

    def ToDatetime(self):
        return self._dt


class _FakeOrder:
    def __init__(self, **kwargs):
        self.external_id = kwargs["external_id"]
        self.order_id = kwargs["order_id"]
        self.user_id = kwargs["user_id"]
        self.order_status = kwargs["order_status"]
        self.total_amount = kwargs["total_amount"]
        self.created_at = kwargs["created_at"]
        self.tenant_id = kwargs["tenant_id"]
        self.partner_id = kwargs["partner_id"]


class _FakeResp:
    def __init__(self, orders):
        self.orders = orders


def _insert_user(engine, schema: str, user_id: str, username: str, email: str, cart=None):
    if cart is None:
        cart = []
    with engine.begin() as conn:
        conn.exec_driver_sql(f"SET search_path TO {schema}")
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, cart, created_at, updated_at) VALUES (%s,%s,%s,%s, now(), now())",
            (user_id, username, email, cart),
        )


def test_get_user_orders_success(client, app_and_engine, monkeypatch):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000004"
    _insert_user(engine, "public", user_id, "o", "o@example.com", [])

    import app.main as main_mod

    dt = datetime.datetime(2025, 1, 1, 12, 0, 0)
    fake_resp = _FakeResp([
        _FakeOrder(
            external_id="ext-1",
            order_id=123,
            user_id=user_id,
            order_status="CREATED",
            total_amount=9.99,
            created_at=_FakeTimestamp(dt),
            tenant_id="public",
            partner_id="partner-x",
        )
    ])

    def _fake_get_orders_by_user(user_id: str, timeout_s: float = 2.0, tenant_id=None):
        return fake_resp

    monkeypatch.setattr(main_mod, "get_orders_by_user", _fake_get_orders_by_user)

    r = client.get(f"/{user_id}/orders")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == user_id
    assert len(body["orders"]) == 1
    assert body["orders"][0]["order_id"] == 123
    assert body["orders"][0]["external_id"] == "ext-1"
    assert "created_at" in body["orders"][0]


def test_get_user_orders_grpc_failure_returns_502(client, app_and_engine, monkeypatch):
    _, engine = app_and_engine
    user_id = "00000000-0000-0000-0000-000000000005"
    _insert_user(engine, "public", user_id, "f", "f@example.com", [])

    import app.main as main_mod

    def _boom(*args, **kwargs):
        raise RuntimeError("grpc down")

    monkeypatch.setattr(main_mod, "get_orders_by_user", _boom)

    r = client.get(f"/{user_id}/orders")
    assert r.status_code == 502
    assert "Order service unavailable" in r.json()["detail"]

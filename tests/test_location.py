def test_autocomplete_returns_predictions(client, monkeypatch):
    import app.main as main_mod

    class _FakeResp:
        def raise_for_status(self): 
            return None
        def json(self):
            return {
                "predictions": [
                    {"description": "Ljubljana, Slovenia", "place_id": "abc"},
                    {"description": "Maribor, Slovenia", "place_id": "def"},
                ]
            }

    class _FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def get(self, url, params=None): return _FakeResp()

    monkeypatch.setattr(main_mod.httpx, "AsyncClient", _FakeClient)

    r = client.get("/location/autocomplete", params={"input": "Lj"})
    assert r.status_code == 200
    assert r.json() == [
        {"description": "Ljubljana, Slovenia", "place_id": "abc"},
        {"description": "Maribor, Slovenia", "place_id": "def"},
    ]


def test_place_details_success(client, monkeypatch):
    import app.main as main_mod

    class _FakeResp:
        def raise_for_status(self): 
            return None
        def json(self):
            return {
                "result": {
                    "formatted_address": "Ljubljana, Slovenia",
                    "geometry": {"location": {"lat": 46.0569, "lng": 14.5058}},
                }
            }

    class _FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def get(self, url, params=None): return _FakeResp()

    monkeypatch.setattr(main_mod.httpx, "AsyncClient", _FakeClient)

    r = client.get("/location/place", params={"place_id": "abc"})
    assert r.status_code == 200
    body = r.json()
    assert body["formatted_address"] == "Ljubljana, Slovenia"
    assert body["latitude"] == 46.0569
    assert body["longitude"] == 14.5058


def test_place_details_not_found(client, monkeypatch):
    import app.main as main_mod

    class _FakeResp:
        def raise_for_status(self): 
            return None
        def json(self):
            return {"result": None}

    class _FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def get(self, url, params=None): return _FakeResp()

    monkeypatch.setattr(main_mod.httpx, "AsyncClient", _FakeClient)

    r = client.get("/location/place", params={"place_id": "missing"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Place not found"

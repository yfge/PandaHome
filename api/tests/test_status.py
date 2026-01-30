import types


def test_status_snapshot_success(client, monkeypatch):
    import src.app.services.status as status_module
    import src.app.main as main_module

    main_module.app.state.status_service._cache_ttl_seconds = 0.0
    main_module.app.state.status_service._cache = None

    monkeypatch.setattr(status_module.psutil, "cpu_percent", lambda interval=0.1: 12.5)
    monkeypatch.setattr(status_module.psutil, "cpu_count", lambda logical=True: 4)

    virtual_memory = types.SimpleNamespace(total=1000, available=400)
    monkeypatch.setattr(status_module.psutil, "virtual_memory", lambda: virtual_memory)

    disk_usage = types.SimpleNamespace(total=2000, used=500, free=1500)
    monkeypatch.setattr(status_module.psutil, "disk_usage", lambda path="/": disk_usage)

    monkeypatch.setattr(status_module.psutil, "boot_time", lambda: 100)
    monkeypatch.setattr(status_module.time, "time", lambda: 200)

    response = client.get("/api/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["code"] == 0
    data = payload["data"]

    assert data["cpu"]["usage"] == 12.5
    assert data["cpu"]["cores"] == 4

    assert data["memory"]["total"] == 1000
    assert data["memory"]["used"] == 600
    assert data["memory"]["free"] == 400

    assert data["disk"]["total"] == 2000
    assert data["disk"]["used"] == 500
    assert data["disk"]["free"] == 1500

    assert data["uptime"] == 100
    assert data["timestamp"] == 200

    assert isinstance(data["services"], list)
    assert any(service["name"] == "api" for service in data["services"])


def test_status_snapshot_handles_errors(client, monkeypatch):
    import src.app.services.status as status_module
    import src.app.main as main_module

    main_module.app.state.status_service._cache_ttl_seconds = 0.0
    main_module.app.state.status_service._cache = None

    def boom():
        raise RuntimeError("metrics unavailable")

    monkeypatch.setattr(status_module.psutil, "virtual_memory", boom)

    response = client.get("/api/status")
    assert response.status_code == 500
    assert response.json()["detail"] == "metrics unavailable"


def test_health_includes_timestamp_and_uptime(client, monkeypatch):
    import src.app.main as main_module

    main_module.app.state.started_at = 100
    monkeypatch.setattr(main_module.time, "time", lambda: 250)

    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["timestamp"] == 250
    assert payload["data"]["uptime"] == 150

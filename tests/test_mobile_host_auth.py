"""Transport boundary tests; domain persistence is exercised without a sidecar."""
import asyncio
import json

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient
from typer.testing import CliRunner

from learnloop import capture
from learnloop.db.repositories import Repository
from learnloop_mobile.cli import app as cli
from learnloop_mobile.config import MobileConfig
from learnloop_mobile.host import SchemaMismatch, create_app
from tests.helpers import create_basic_vault


@pytest.fixture
def mobile(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = MobileConfig(enabled=True, vault=paths.root, hostname="desktop.tail.ts.net",
                          owner_login="owner@example.com")
    app = create_app(config)
    repo = Repository.attach(paths.sqlite_path)
    pending = capture.create_pairing(repo, scope="app")
    device = capture.exchange_pairing(repo, secret=pending["secret"])
    headers = {"Tailscale-User-Login": config.owner_login,
               "Authorization": f"Bearer {device['token']}"}
    with TestClient(app, base_url=f"https://{config.hostname}") as client:
        yield client, app.state.host, repo, device, headers


def raw_request(host, headers, *, path="/api/v1/capture", chunks=None):
    received = 0
    messages = []
    async def run():
        nonlocal received
        async def receive():
            nonlocal received
            received += 1
            if chunks is None:
                raise AssertionError("unauthorized request body was read")
            return chunks.pop(0)
        async def send(message):
            messages.append(message)
        await host({"type": "http", "http_version": "1.1", "method": "POST",
                    "scheme": "https", "path": path, "raw_path": path.encode(),
                    "query_string": b"", "headers": headers}, receive, send)
    asyncio.run(run())
    return messages[0]["status"], received


@pytest.mark.parametrize("headers,status", [
    ([], 403),
    ([(b"host", b"evil.invalid")], 403),
    ([(b"host", b"desktop.tail.ts.net")], 403),
    ([(b"host", b"desktop.tail.ts.net"), (b"tailscale-user-login", b"owner@example.com")], 401),
    ([(b"host", b"desktop.tail.ts.net"), (b"tailscale-user-login", b"owner@example.com"),
      (b"authorization", b"Bearer invalid")], 401),
    ([(b"host", b"desktop.tail.ts.net"), (b"origin", b"https://evil.invalid")], 403),
])
def test_auth_rejects_before_body(mobile, headers, status):
    _, host, _, _, _ = mobile
    assert raw_request(host, headers) == (status, 0)


def test_scope_revocation_status_and_no_cors(mobile):
    client, _, repo, device, headers = mobile
    response = client.get("/api/v1/status", headers=headers)
    assert response.status_code == 200
    assert response.json()["schema_ok"] is True
    assert response.headers["cache-control"] == "no-store"
    assert not any(key.startswith("access-control") for key in response.headers)
    pending = capture.create_pairing(repo, scope="capture")
    narrow = capture.exchange_pairing(repo, code=pending["code"])
    narrow_headers = {**headers, "Authorization": f"Bearer {narrow['token']}"}
    assert client.get("/api/v1/status", headers=narrow_headers).status_code == 200
    assert client.post("/rpc", json={}, headers=narrow_headers).status_code == 403
    capture.revoke_device(repo, device["device_id"])
    assert client.get("/api/v1/status", headers=headers).status_code == 401


def test_pairing_is_identity_gated_static_and_one_use(mobile):
    client, _, repo, _, headers = mobile
    identity = {"Tailscale-User-Login": headers["Tailscale-User-Login"]}
    assert client.get("/pair").status_code == 403
    pending = capture.create_pairing(repo)
    page = client.get("/pair", headers=identity)
    assert page.status_code == 200
    assert pending["secret"] not in page.text
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    script = client.get("/pair.js", headers=identity)
    assert "history.replaceState" in script.text
    data = {"secret": pending["secret"], "device_label": "My phone"}
    response = client.post("/pair", json=data, headers=identity)
    assert response.status_code == 200
    assert response.json()["token"]
    assert client.post("/pair", json=data, headers=identity).status_code >= 400
    for path in ("/app/", "/pair.html", "/static/pair.html", "/state.sqlite", "/pair/../learnloop.toml"):
        assert client.get(path, headers=headers).status_code == 404


def test_limits_count_chunks_without_content_length(mobile):
    _, host, _, _, headers = mobile
    raw = [(b"host", b"desktop.tail.ts.net"), (b"content-type", b"application/json")]
    raw += [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    chunks = [{"type": "http.request", "body": b"x" * (256 * 1024 + 1), "more_body": False}]
    assert raw_request(host, raw, chunks=chunks)[0] == 413
    assert raw_request(host, raw + [(b"x-big", b"x" * 16384)])[0] == 431
    host.active["capture"] = 2
    assert raw_request(host, raw)[0] == 503
    host.active["capture"] = 0


def test_deadline(mobile, monkeypatch):
    import learnloop_mobile.host as module
    monkeypatch.setattr(module, "BODY_DEADLINE", 0.001)
    _, host, _, _, headers = mobile
    messages = []
    async def run():
        async def receive():
            await asyncio.sleep(1)
        async def send(message):
            messages.append(message)
        await host({"type": "http", "method": "POST", "path": "/api/v1/capture",
                    "headers": [(b"host", b"desktop.tail.ts.net"),
                                (b"content-type", b"application/json")] +
                    [(k.lower().encode(), v.encode()) for k, v in headers.items()]}, receive, send)
    asyncio.run(run())
    assert messages[0]["status"] == 408


def test_offline_backlog_flushes_without_per_device_throttle(mobile):
    """Spec §4.6 (revision 3+): no per-token rate limits; admission bounds work."""
    from learnloop.ids import new_ulid

    client, _, repo, device, headers = mobile
    backlog = [{"client_capture_id": new_ulid(), "kind": "text", "text": f"capture {index}"}
               for index in range(45)]
    receipts = []
    for payload in backlog:
        response = client.post("/api/v1/capture", json=payload, headers=headers)
        assert response.status_code == 201, response.text
        receipts.append(response.json())
    # A flush that lost its responses retries every receipt: same captures, 200.
    for payload, receipt in zip(backlog, receipts):
        response = client.post("/api/v1/capture", json=payload, headers=headers)
        assert response.status_code == 200
        assert response.json() == receipt
    for receipt in receipts:
        assert client.get(f"/api/v1/capture/{receipt['capture_id']}", headers=headers).status_code == 200
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM capture_inbox").fetchone()[0] == 45
        rows = [tuple(row) for row in connection.execute("SELECT * FROM mobile_request_log")]
    assert len(rows) == 90  # Admitted mutations only; status polling is not logged.
    assert device["token"] not in json.dumps(rows)


def test_rejected_requests_never_touch_devices_or_log(mobile, monkeypatch):
    client, host, repo, device, headers = mobile
    def forbidden(*args, **kwargs):
        pytest.fail("rejected traffic attempted a durable write")
    monkeypatch.setattr(capture, "touch_device", forbidden)
    monkeypatch.setattr(capture, "log_request", forbidden)
    assert client.post("/api/v1/capture", json={}, headers={
        **headers, "Authorization": "Bearer invalid",
    }).status_code == 401
    host.active["capture"] = 2
    try:
        assert client.post("/api/v1/capture", json={}, headers=headers).status_code == 503
    finally:
        host.active["capture"] = 0
    # Polling uses the same read-only authentication path, without a last-seen write.
    assert client.get("/api/v1/status", headers=headers).status_code == 200


def test_invalid_pairing_posts_have_bounded_logs(mobile):
    client, _, repo, _, headers = mobile
    identity = {"Tailscale-User-Login": headers["Tailscale-User-Login"]}
    for _ in range(30):
        assert client.post("/pair", json={}, headers=identity).status_code == 400
    for _ in range(5):
        assert client.post("/pair", json={}, headers=identity).status_code == 429
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM mobile_request_log").fetchone()[0] == 30


def test_startup_and_shutdown_never_prune(mobile, monkeypatch):
    _, host, _, _, _ = mobile
    def forbidden(*args, **kwargs):
        pytest.fail("startup attempted request-log maintenance")
    monkeypatch.setattr(capture, "prune_request_log", forbidden)
    with TestClient(create_app(host.config), base_url=f"https://{host.config.hostname}") as client:
        assert client.get("/healthz").status_code == 200


def test_slow_capture_has_separate_bounded_lane(mobile, monkeypatch):
    import threading
    import httpx

    _, host, _, _, headers = mobile
    started, release = threading.Event(), threading.Event()
    def slow_capture(*args, **kwargs):
        started.set()
        assert release.wait(10)
        return {"capture_id": "test", "status": "pending", "created": True}
    monkeypatch.setattr(capture, "create_capture", slow_capture)

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=host),
            base_url=f"https://{host.config.hostname}", headers=headers,
        ) as client:
            payload = {"kind": "text", "client_capture_id": "test"}
            first = asyncio.create_task(client.post("/api/v1/capture", json=payload))
            second = None
            try:
                async with asyncio.timeout(5):
                    while not started.is_set():
                        await asyncio.sleep(0.01)
                second = asyncio.create_task(client.post("/api/v1/capture", json=payload))
                async with asyncio.timeout(5):
                    while host.active["capture"] < 2:
                        await asyncio.sleep(0.01)
                assert (await client.post("/api/v1/capture", json=payload)).status_code == 503
                response = await asyncio.wait_for(client.get("/api/v1/status"), timeout=2)
                assert response.status_code == 200
            finally:
                release.set()
                results = await asyncio.gather(first, *([second] if second else []))
            assert all(response.status_code == 201 for response in results)
            assert host.active == {"short": 0, "capture": 0, "media": 0}
    asyncio.run(run())


def test_only_one_media_upload_is_admitted(mobile):
    _, host, _, _, headers = mobile
    raw = [(b"host", b"desktop.tail.ts.net"), (b"content-type", b"multipart/form-data; boundary=x")]
    raw += [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    host.active["media"] = 1
    try:
        assert raw_request(host, raw) == (503, 0)
    finally:
        host.active["media"] = 0


def test_multipart_accepts_body_buffer_without_full_copy():
    from learnloop_mobile.host import _multipart
    body = bytearray(
        b'--boundary\r\nContent-Disposition: form-data; name="kind"\r\n\r\nimage\r\n'
        b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="a.png"\r\n'
        b'Content-Type: image/png\r\n\r\nimage-bytes\r\n--boundary--\r\n'
    )
    scope = {"type": "http", "headers": [
        (b"content-type", b"multipart/form-data; boundary=boundary"),
    ]}
    assert _multipart(scope, body, 1024) == ({"kind": "image"}, b"image-bytes")


def test_strict_schema_and_disabled_startup(mobile):
    _, host, repo, _, _ = mobile
    with pytest.raises(SchemaMismatch):
        create_app(host.config.model_copy(update={"enabled": False}))
    with repo.connection() as connection:
        connection.execute("DELETE FROM schema_migrations WHERE version=(SELECT MAX(version) FROM schema_migrations)")
        connection.commit()
    with pytest.raises(SchemaMismatch):
        create_app(host.config)


def test_serve_rejects_non_loopback_without_loading_configuration():
    result = CliRunner().invoke(cli, ["serve", "--host", "0.0.0.0"])
    assert result.exit_code == 78
    assert "127.0.0.1" in result.output


@pytest.mark.parametrize("body", [
    b"", b"[", b"null", b'{"method":"a","method":"b"}', b'{"method":NaN}',
    b"\xff", b"[" * 2000, b'{"method":true}', b'{"method":"x","params":null}',
])
def test_malformed_json_is_bounded_invalid_request(mobile, body):
    client, _, _, _, headers = mobile
    response = client.post("/rpc", content=body,
                           headers={**headers, "Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"


def test_every_registry_method_is_http_denied(mobile):
    from learnloop_sidecar import handlers  # noqa: F401
    from learnloop_sidecar.registry import METHOD_REGISTRY
    client, host, _, _, headers = mobile
    assert METHOD_REGISTRY
    for method in METHOD_REGISTRY:
        response = client.post("/rpc", json={"method": method, "params": {}}, headers=headers)
        assert response.status_code == 403, method
        assert response.json()["error"]["code"] == "method_not_allowed"


@pytest.mark.parametrize("scope", ["app", "capture"])
def test_desktop_only_and_main_rpcs_are_http_denied_for_every_phone_scope(mobile, scope):
    from learnloop_sidecar import handlers  # noqa: F401
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.test_mobile_allowlist import (
        DAILY_PLAN_EXTENDED_RPCS,
        DAILY_PLAN_RPCS,
        DESKTOP_ONLY_CAPTURE_RPCS,
        MAIN_SIDECAR_RPCS,
    )
    client, _, repo, _, headers = mobile
    pending = capture.create_pairing(repo, scope=scope)
    device = capture.exchange_pairing(repo, secret=pending["secret"])
    phone = {**headers, "Authorization": f"Bearer {device['token']}"}
    # Daily-loop DL1's plan RPCs are pinned here too until mobile M2a allows them.
    for method in (
        DESKTOP_ONLY_CAPTURE_RPCS + MAIN_SIDECAR_RPCS + DAILY_PLAN_RPCS + DAILY_PLAN_EXTENDED_RPCS
    ):
        assert method in METHOD_REGISTRY
        response = client.post("/rpc", json={"method": method, "params": {"captureId": "c"}},
                               headers=phone)
        assert response.status_code == 403, (scope, method)


def test_serve_uses_hardened_uvicorn_options(mobile, monkeypatch):
    import learnloop_mobile.cli as module
    import uvicorn
    _, host, _, _, _ = mobile
    monkeypatch.setattr(module, "_config", lambda _: host.config)
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    result = CliRunner().invoke(cli, ["serve"])
    assert result.exit_code == 0
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["workers"] == 1
    assert calls[0]["proxy_headers"] is False
    assert calls[0]["access_log"] is False
    assert calls[0]["limit_concurrency"] == 32


def test_cli_schema_mismatch_is_configuration_exit(mobile, monkeypatch):
    import learnloop_mobile.cli as module
    _, host, repo, _, _ = mobile
    monkeypatch.setattr(module, "_config", lambda _: host.config)
    with repo.connection() as connection:
        connection.execute("DELETE FROM schema_migrations WHERE version=1")
        connection.commit()
    assert CliRunner().invoke(cli, ["serve"]).exit_code == 78

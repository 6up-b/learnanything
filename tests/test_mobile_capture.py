"""Host HTTP capture contract; sanitization internals have domain tests."""
from io import BytesIO

from PIL import Image
import pytest

from learnloop.ids import new_ulid
from tests.test_mobile_host_auth import mobile


def manifest(**changes):
    return {"client_capture_id": new_ulid(), "kind": "text", "text": "Keep as a reference", **changes}


def test_http_receipt_retry_conflict_and_read_only_status(mobile):
    client, host, repo, _, headers = mobile
    data = manifest()
    response = client.post("/api/v1/capture", json=data, headers=headers)
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["status"] == "received"
    retry = client.post("/api/v1/capture", json=data, headers=headers)
    assert retry.status_code == 200
    assert retry.json() == receipt
    conflict = client.post("/api/v1/capture", json={**data, "text": "different"}, headers=headers)
    assert conflict.status_code == 409
    assert host.read_repo._read_only
    status = client.get(f"/api/v1/capture/{receipt['capture_id']}", headers=headers)
    assert status.status_code == 200
    assert "text" not in status.json()
    assert "media" not in status.json()


def test_image_multipart_ignores_filename_and_returns_receipt(mobile):
    client, _, _, _, headers = mobile
    image = BytesIO()
    Image.new("RGB", (3, 3), "red").save(image, format="PNG")
    response = client.post("/api/v1/capture", headers=headers,
                           data=manifest(kind="image", text="A note"),
                           files={"file": ("../../outside.png", image.getvalue(), "image/png")})
    assert response.status_code == 201, response.text


@pytest.mark.parametrize("data,expected", [
    ({"kind": "text"}, 422),
    (manifest(text="x" * (64 * 1024 + 1)), 413),
    (manifest(vault_path="/etc/passwd"), 422),
    (manifest(kind="audio"), 422),
])
def test_capture_validation(mobile, data, expected):
    client, _, _, _, headers = mobile
    assert client.post("/api/v1/capture", json=data, headers=headers).status_code == expected


def test_multipart_requires_exactly_one_file(mobile):
    client, _, _, _, headers = mobile
    response = client.post("/api/v1/capture", headers=headers, data=manifest(kind="image"),
                           files=[("file", ("a.png", b"a")), ("file", ("b.png", b"b"))])
    assert response.status_code == 400


def test_http_rpc_envelope_and_default_deny(mobile):
    client, _, _, _, headers = mobile
    assert client.post("/rpc", json={"method": "run_cli_command", "params": {}},
                       headers=headers).status_code == 403
    for value in ([], {"method": "x", "params": []}, {"method": "x", "extra": True}):
        assert client.post("/rpc", json=value, headers=headers).status_code == 400

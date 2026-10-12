import hashlib
import io
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from learnloop.capture import (
    CaptureError, create_capture, dismiss_capture, get_capture, get_inbox_summary,
    list_captures, purge_capture, report_orphan_originals, route_capture,
    sanitize_image, validate_url,
)
from learnloop.db.repositories import Repository
from learnloop.content.sources.source_library import register_source_revision
from learnloop.ids import new_ulid
from learnloop.ingest.originals import canonical_source_raw_path
from tests.helpers import create_basic_vault


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository.attach(paths.sqlite_path)


def image_bytes(format="PNG", *, secret="private"):
    output = io.BytesIO()
    image = Image.new("RGB", (6, 4), "red")
    if format == "PNG":
        info = PngImagePlugin.PngInfo()
        info.add_text("comment", secret)
        image.save(output, format=format, pnginfo=info)
    else:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = secret
        image.save(output, format=format, exif=exif)
    return output.getvalue()


def test_global_idempotency_and_reference_only(repo):
    key = new_ulid()
    first = create_capture(repo, client_capture_id=key, kind="text", text="a question")
    second = create_capture(repo, client_capture_id=key, kind="text", text="a question")
    assert first == dict(capture_id=second["capture_id"], status="received", created=True)
    assert second["created"] is False
    with pytest.raises(CaptureError) as conflict:
        create_capture(repo, client_capture_id=key, kind="text", text="changed")
    assert conflict.value.code == "capture_conflict"
    assert len(list_captures(repo)) == 1
    assert get_inbox_summary(repo)["new_count"] == 1
    capture = get_capture(repo, first["capture_id"])
    assert capture["state"] == "new" and capture["route"] is None


@pytest.mark.parametrize("url", ["file:///tmp/a", "/tmp/a", "../a", "javascript:alert(1)", "https://", "https://u:p@host", "https://host\n/a"])
def test_reject_local_or_invalid_urls(url):
    with pytest.raises(CaptureError) as error:
        validate_url(url)
    assert error.value.status == 422


@pytest.mark.parametrize("url", ["https://arxiv.org/abs/2401.12345", "http://example.org/", "2401.12345v2", "arXiv:math/0301234"])
def test_valid_reference_urls(url):
    validate_url(url)


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_image_sanitization_and_raw_fingerprint(repo, format):
    raw = image_bytes(format)
    payload = dict(client_capture_id=new_ulid(), kind="image", media=raw)
    receipt = create_capture(repo, **payload)
    row = get_capture(repo, receipt["capture_id"])
    stored = canonical_source_raw_path(repo.sqlite_path.parent, row["media_sha256"]).read_bytes()
    assert b"private" not in stored
    assert row["media_sha256"] == "sha256:" + hashlib.sha256(stored).hexdigest()
    with Image.open(io.BytesIO(stored)) as clean:
        assert not clean.info
        assert not clean.getexif()
        assert clean.size == ((6, 4) if format == "PNG" else (4, 6))
    changed = image_bytes(format, secret="different metadata")
    assert sanitize_image(raw) == sanitize_image(changed)
    with pytest.raises(CaptureError, match="another request"):
        create_capture(repo, **{**payload, "media": changed})


def test_unsupported_and_decoded_image_limit(monkeypatch):
    with pytest.raises(CaptureError) as error:
        sanitize_image(b"\x00\x00\x00\x18ftypheic")
    assert error.value.status == 415
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)
    with pytest.raises(CaptureError) as error:
        sanitize_image(image_bytes())
    assert error.value.status == 413


def test_inbox_route_atomic_failure_and_orphan_reporting(repo):
    with repo.connection() as conn:
        conn.execute("""CREATE TRIGGER reject_route BEFORE INSERT ON capture_routes
                        BEGIN SELECT RAISE(ABORT,'injected'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        create_capture(repo, client_capture_id=new_ulid(), kind="image", media=image_bytes())
    assert list_captures(repo) == []
    assert len(report_orphan_originals(repo)) == 1


def test_routes_dismiss_and_readonly_status(repo):
    receipt = create_capture(repo, client_capture_id=new_ulid(), kind="text", text="problem")
    capture_id = receipt["capture_id"]
    dismiss_capture(repo, capture_id)
    assert get_inbox_summary(repo)["count"] == 0
    route = route_capture(repo, capture_id, route="make_card", result_refs={"item_id": "item"})
    assert route_capture(repo, capture_id, route="make_card", result_refs={"item_id": "item"}) == route
    with pytest.raises(CaptureError):
        route_capture(repo, capture_id, route="quick_add", result_refs={"source_id": "source"})
    assert get_capture(Repository.attach(repo.sqlite_path, read_only=True), capture_id)["state"] == "routed"


def test_purge_shared_original_and_retry_never_resurrects(repo):
    payload = dict(client_capture_id=new_ulid(), kind="image", media=image_bytes(), note="private")
    first = create_capture(repo, **payload)
    second = create_capture(repo, **{**payload, "client_capture_id": new_ulid()})
    first_row = get_capture(repo, first["capture_id"])
    path = canonical_source_raw_path(repo.sqlite_path.parent, first_row["media_sha256"])
    assert purge_capture(repo, first["capture_id"])["media_retained_shared"]
    assert path.exists()
    assert purge_capture(repo, second["capture_id"])["media_retained_shared"] is False
    assert not path.exists()
    retry = create_capture(repo, **payload)
    assert not retry["created"] and retry["capture_id"] == first["capture_id"]
    assert not path.exists()
    assert get_capture(repo, first["capture_id"])["note"] is None


def test_purge_file_failure_is_visible_and_retryable(repo, monkeypatch):
    receipt = create_capture(repo, client_capture_id=new_ulid(), kind="image", media=image_bytes(), text="secret")
    original = Path.unlink
    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", lambda *a, **kw: (_ for _ in ()).throw(PermissionError()))
        assert purge_capture(repo, receipt["capture_id"])["media_delete_pending"]
    assert get_capture(repo, receipt["capture_id"])["text"] is None
    assert get_capture(Repository.attach(repo.sqlite_path, read_only=True), receipt["capture_id"])["media_delete_pending"]
    assert not purge_capture(repo, receipt["capture_id"])["media_delete_pending"]
    assert Path.unlink is original


def test_interrupted_purge_keeps_durable_deletion_intent(repo, monkeypatch):
    receipt = create_capture(repo, client_capture_id=new_ulid(), kind="image", media=image_bytes())
    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", lambda *a, **kw: (_ for _ in ()).throw(KeyboardInterrupt()))
        with pytest.raises(KeyboardInterrupt):
            purge_capture(repo, receipt["capture_id"])
    row = get_capture(Repository.attach(repo.sqlite_path, read_only=True), receipt["capture_id"])
    assert row["status"] == "purged"
    assert row["media_delete_pending"]
    assert not purge_capture(repo, receipt["capture_id"])["media_delete_pending"]


def test_purge_retains_canonical_source_original(repo):
    receipt = create_capture(repo, client_capture_id=new_ulid(), kind="image", media=image_bytes())
    row = get_capture(repo, receipt["capture_id"])
    path = canonical_source_raw_path(repo.sqlite_path.parent, row["media_sha256"])
    register_source_revision(
        repo, acquisition_kind="file", canonical_uri="https://example.org/image.png",
        raw_bytes=path.read_bytes(), vault_root=repo.sqlite_path.parent,
    )
    assert purge_capture(repo, receipt["capture_id"])["media_retained_shared"]
    assert path.exists()
    assert report_orphan_originals(repo) == []


@pytest.mark.durability
def test_capture_concurrent_idempotency(repo):
    key = new_ulid()
    def capture(_):
        return create_capture(Repository.attach(repo.sqlite_path), client_capture_id=key, kind="text", text="shared")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(capture, range(8)))
    assert sum(result["created"] for result in results) == 1
    assert len({result["capture_id"] for result in results}) == 1


def test_old_handled_capture_is_reachable_past_100_newer_and_tombstones(repo, monkeypatch):
    sensitive = create_capture(repo, client_capture_id=new_ulid(), kind="image", media=image_bytes())
    dismiss_capture(repo, sensitive["capture_id"])
    newer = [create_capture(repo, client_capture_id=new_ulid(), kind="text", text=f"newer {index}")
             for index in range(120)]
    for receipt in newer[::2]:
        purge_capture(repo, receipt["capture_id"])  # Tombstones stay in the all-state listing.
    first = list_captures(repo, status=None, limit=100)
    assert sensitive["capture_id"] not in {row["capture_id"] for row in first}
    second = list_captures(repo, status=None, limit=100, offset=100)
    assert sensitive["capture_id"] in {row["capture_id"] for row in second}
    assert len(first) + len(second) == 121
    # A failed unlink stays directly discoverable, however many captures follow.
    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", lambda *a, **kw: (_ for _ in ()).throw(OSError("busy")))
        assert purge_capture(repo, sensitive["capture_id"])["media_delete_pending"]
    for index in range(30):
        create_capture(repo, client_capture_id=new_ulid(), kind="text", text=f"later {index}")
    summary = get_inbox_summary(repo)
    assert [row["capture_id"] for row in summary["delete_pending"]] == [sensitive["capture_id"]]
    assert summary["delete_pending_count"] == 1
    assert [row["capture_id"] for row in list_captures(repo, status="delete_pending")] == [
        sensitive["capture_id"]]
    purge_capture(repo, sensitive["capture_id"])
    assert get_inbox_summary(repo)["delete_pending"] == []

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Event

from PIL import Image
import pytest

from learnloop.capture import create_capture, get_capture, purge_capture
from learnloop.content.sources import source_library
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.originals import canonical_source_raw_path
from tests.helpers import create_basic_vault


@pytest.mark.durability
def test_source_publication_and_capture_purge_share_writer_reservation(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository.attach(paths.sqlite_path)
    image = BytesIO()
    Image.new("RGB", (2, 2), "red").save(image, format="PNG")
    receipt = create_capture(
        repository, client_capture_id=new_ulid(), kind="image", media=image.getvalue(),
    )
    capture = get_capture(repository, receipt["capture_id"])
    original = canonical_source_raw_path(paths.root, capture["media_sha256"])
    sanitized = original.read_bytes()
    stored = Event()
    publish = Event()
    purge_started = Event()
    store = source_library.store_original_bytes

    def paused_store(*args, **kwargs):
        result = store(*args, **kwargs)
        stored.set()
        assert publish.wait(10)
        return result

    monkeypatch.setattr(source_library, "store_original_bytes", paused_store)

    def register():
        return source_library.register_source_revision(
            Repository.attach(paths.sqlite_path), acquisition_kind="pdf",
            canonical_uri="https://example.com/image", raw_bytes=sanitized,
            vault_root=paths.root,
        )

    def purge():
        purge_started.set()
        return purge_capture(Repository.attach(paths.sqlite_path), capture["id"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        registration = pool.submit(register)
        assert stored.wait(10)
        purging = pool.submit(purge)
        assert purge_started.wait(10)
        # The publication holds the writer reservation while bytes exist but
        # their reference does not. Purge must not complete inside that gap.
        try:
            with pytest.raises(TimeoutError):
                purging.result(timeout=0.1)
        finally:
            publish.set()
        registered = registration.result(timeout=10)
        result = purging.result(timeout=10)
    assert result["media_retained_shared"] is True
    assert original.read_bytes() == sanitized
    assert registered.asset_hash == capture["media_sha256"]

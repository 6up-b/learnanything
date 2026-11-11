"""What other test files use from ``tests/test_mobile_v4_reader.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_basic_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, config_for, pair
from tests.reread_safety_helpers import _clock, _made_on, _persist


pdfium = pytest.importorskip("pypdfium2")
#: The app this stage builds: it answers probes and it has the Reader.
READER_APP = ("phone_probes", "phone_reader")
EXTRACTION = "ext1"
_BLOCKS = {
    "b0": ("SectionHeader", 0, "1 Vectors"),
    "b1": ("Text", 0, "A vector space is a set with addition and scalar multiplication, $u + v = v + u$."),
    "b2": ("Text", 0, "Every vector space has a zero vector."),
    "b3": ("SectionHeader", 1, "2 Spans"),
    "b4": ("Text", 1, "The span of a list is the set of all linear combinations of it."),
    "b5": ("SectionHeader", 2, "3 Exam review"),
    "b6": ("Text", 2, "Exam problem: prove that the zero vector is unique."),
}
_UNITS = (("u1", "1 Vectors", ["b0", "b1", "b2"]), ("u2", "2 Spans", ["b3", "b4"]),
          ("u3", "3 Exam review", ["b5", "b6"]))


def pdf_bytes(pages: int = 3) -> bytes:
    document = pdfium.PdfDocument.new()
    try:
        for _ in range(pages):
            document.new_page(612, 792)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()
    finally:
        document.close()


def _ir() -> DocumentIR:
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page,
                                  bbox=[40.0, 60.0 + 40 * index, 560.0, 90.0 + 40 * index],
                                  section_path=[next(label for _u, label, spans in _UNITS if span in spans)])
              for index, (span, (kind, page, text)) in enumerate(_BLOCKS.items())]
    units = [DocumentUnit(unit_id=unit, label=label, ordinal=index, semantic_hash=f"sha256:{unit}", page_start=0,
                          page_end=2, span_ids=spans) for index, (unit, label, spans) in enumerate(_UNITS)]
    return DocumentIR(extractor="marker", extractor_version="1", blocks=blocks, units=units, assets=[],
                      health=ExtractionHealth())


def add_book(root: Path, repository: Repository, *, source_id: str = "src1", revision_id: str = "rev1",
             extraction_id: str = EXTRACTION, held_out: bool = True, data: bytes | None = None) -> str:
    """One book: its original in the originals store, a completed reading of it, and (``held_out``) its third
    section held out for an exam, as the owner's exact mark records it."""

    from learnloop.ingest.originals import store_original_bytes

    data = data if data is not None else pdf_bytes()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    store_original_bytes(root, digest, data)
    now = "2026-10-14T09:00:00+00:00"
    with repository.connection() as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES (?,?,?,?,?)", (source_id, "pdf", "file:///home/owner/books/book.pdf", now, now))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           (revision_id, source_id, digest, now))
        connection.commit()
    repository.set_source_current_revision(source_id, revision_id)
    _persist(repository, _ir(), revision_id=revision_id, extraction_id=extraction_id, clock=_clock())
    if held_out:
        repository.upsert_unit_selection(extraction_id=extraction_id, source_id=source_id, revision_id=revision_id,
                                         selected_unit_ids=["u1", "u2", "u3"],
                                         exam_use_modes={"u3": "held_out_evaluation"},
                                         exam_paper_metadata=_made_on(extraction_id, revision_id))
    return digest


def call(ctx: SidecarContext, name: str, params: dict) -> Any:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def desktop(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    return ctx


def host(root: Path, cache: Path, **changes: Any):
    config = config_for(root).model_copy(update={"page_cache_dir": cache, **changes})
    return create_app(config)


@pytest.fixture
def world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    digest = add_book(paths.root, repository)
    device = pair(repository)
    app = host(paths.root, tmp_path / "pages")
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield {"phone": Phone(client, device, capabilities=READER_APP), "root": paths.root, "repo": repository,
               "digest": digest, "cache": tmp_path / "pages", "host": app.state.host, "client": client,
               "device": device}


def job(phone: Phone, method: str, params: dict, key: str) -> Any:
    """A long method (an outbox intent, the Ask) to its end."""

    from tests.mobile_host_helpers import poll_job

    response = phone.post(method, params, request_id=key)
    if response.status_code == 202:
        body = poll_job(phone, response.json()["accepted"]["job_id"])
        assert body["state"] == "completed", body
        return body["result"]
    assert response.status_code == 200, response.text
    return response.json()["result"]


def _png() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (200, 10, 10)).save(buffer, format="PNG")
    return buffer.getvalue()

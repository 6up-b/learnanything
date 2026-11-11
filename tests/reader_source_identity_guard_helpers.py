"""What other test files use from ``tests/test_reader_source_identity_guard.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop_sidecar.errors import SidecarError

from tests.helpers import NOW, append_config_toml, create_basic_vault
from tests.reading_path_fixtures import call, table_counts
from tests.source_inventory_helpers import _persist, _register_revision


MISMATCH = "span_extraction_mismatch"
#: Every switch the guarded handlers sit behind (the guard runs right after them).
_SWITCHES = """
[tutor_qa]
reader_enabled = true
[reader_inquiry]
enabled = true
[reader_intent]
enabled = true
[reader_active_reading]
enabled = true
[workbench]
enabled = true
[figures]
enabled = true
show_me_enabled = true
offers_enabled = true
[library_ask]
enabled = true
[source_service]
enabled = true
[reader_compare]
enabled = true
"""


def _ir(prefix: str, count: int) -> DocumentIR:
    spans = [f"{prefix}{index}" for index in range(count)]
    blocks = [
        DocumentBlock.build(span_id=span, block_type="Text", text=f"Passage {span} about symmetric matrices.",
                            ordinal=index, page=1, bbox=[10.0, 10.0 + 40 * index, 200.0, 40.0 + 40 * index],
                            section_path=["Ch1"])
        for index, span in enumerate(spans)
    ]
    unit = DocumentUnit(unit_id=f"u_{prefix}", label=f"Section {prefix}", ordinal=0, semantic_hash=f"sha256:{prefix}",
                        page_start=1, page_end=1, span_ids=spans)
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _refused(ctx, repository, method: str, params: dict[str, Any]) -> SidecarError:
    """The call is refused with the typed mismatch, and nothing is written."""

    before = table_counts(repository)
    with pytest.raises(SidecarError) as raised:
        call(ctx, method, params)
    assert raised.value.code == MISMATCH, (method, raised.value.code, raised.value.message)
    assert table_counts(repository) == before, method
    return raised.value


def _view(repository, *, source_id: str, revision_id: str, extraction_id: str) -> str:
    return repository.insert_render_view({
        "id": f"rv_{extraction_id}", "source_id": source_id, "revision_id": revision_id, "extraction_id": extraction_id,
        "renderer_version": "1", "schema_version": "1", "content_hash": f"sha256:{extraction_id}",
        "request_hash": f"req_{extraction_id}",
    })


@pytest.fixture
def twins(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    append_config_toml(paths.root, _SWITCHES)
    repository = Repository(paths.sqlite_path)
    for book in ("x", "y"):
        _register_revision(repository, source_id=f"src_{book}", revision_id=f"rev_{book}")
        _persist(repository, _ir("s", 3), revision_id=f"rev_{book}", extraction_id=f"ext_{book}")
        _view(repository, source_id=f"src_{book}", revision_id=f"rev_{book}", extraction_id=f"ext_{book}")
    # A later reading of book x (a re-extraction of the same source, another revision).
    with repository.connection() as connection:
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           ("rev_x2", "src_x", "sha256:x2", NOW.isoformat()))
        connection.commit()
    _persist(repository, _ir("s", 3), revision_id="rev_x2", extraction_id="ext_x2")
    return paths, repository

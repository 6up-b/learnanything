"""What other test files use from ``tests/test_reader_dialogue.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


_CLOCK = FrozenClock(NOW)


def _ir() -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Text", text="Intro paragraph.", ordinal=0,
                            page=1, bbox=[10.0, 10.0, 200.0, 40.0], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s1", block_type="Text",
                            text="A real square matrix is symmetric when A^T = A.", ordinal=1,
                            page=1, bbox=[10.0, 50.0, 200.0, 90.0], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s2", block_type="Text", text="The spectral theorem follows.",
                            ordinal=2, page=1, bbox=[10.0, 100.0, 200.0, 140.0], section_path=["Ch1"]),
    ]
    unit = DocumentUnit(unit_id="u1", label="Symmetric matrices", ordinal=0,
                        semantic_hash="sha256:sym", page_start=1, page_end=1,
                        span_ids=["s0", "s1", "s2"])
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks,
                      assets=[], health=ExtractionHealth())


def _setup(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir(), revision_id="rev1", extraction_id="ext1")
    return vault, repo

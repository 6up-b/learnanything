"""What other test files use from ``tests/test_reader_requests.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

from tests.structured_ai import StructuredClientFake
from tests.source_inventory_helpers import _persist, _register_revision


def _ingest(repo: Repository, *, n_blocks: int = 5, big: bool = False) -> None:
    _register_revision(repo, source_id="src1", revision_id="rev1")
    text = ("x" * 40000) if big else "Symmetric matrices have real eigenvalues."
    blocks = [
        DocumentBlock.build(span_id=f"s{i}", block_type="Text", text=f"{text} block {i}",
                            ordinal=i, page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"])
        for i in range(1, n_blocks + 1)
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s",
                            span_ids=[b.span_id for b in blocks])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")


class _FakePresetClient(StructuredClientFake):
    def __init__(self, content_md: str = "A worked example: diagonalize A.",
                 span_ids: list[str] | None = None) -> None:
        self.calls: list = []
        self._content_md = content_md
        self._span_ids = span_ids

    def run_reader_preset_synthesis(self, context):
        from learnloop.reader.ai_contracts import ReaderPresetSynthesis

        self.calls.append(context)
        span_ids = self._span_ids
        if span_ids is None:
            span_ids = [context.blocks[0]["span_id"]]
        return ReaderPresetSynthesis(content_md=self._content_md, span_ids=span_ids)

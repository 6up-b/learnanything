"""Demand-paged synthesis service (spec §6, §15.3): neighborhood, idempotency key,
fenced-lease drain, cache reuse, cancellation, and token caps."""

from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import reader_requests as RR
from tests.test_source_inventory import _persist, _register_revision


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


def test_neighborhood_is_bounded_to_smallest_window(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo, n_blocks=9)
    window = RR.neighborhood(repo, extraction_id="ext1", span_id="s5")
    # target + up to MAX_ADJACENT_BLOCKS per side, never the whole chapter.
    assert "s5" in window["span_ids"]
    assert len(window["span_ids"]) <= (2 * RR.MAX_ADJACENT_BLOCKS + 1)


def test_enqueue_is_idempotent_on_contract_and_versions_change_identity(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    a = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                           span_id="s1", preset="worked_example")
    b = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                           span_id="s1", preset="worked_example")
    assert b["deduplicated"] is True and b["request_key"] == a["request_key"]
    # A model change -> a different contract -> a successor request (§6.2).
    c = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                           span_id="s1", preset="worked_example", model="stub-2")
    assert c["deduplicated"] is False and c["request_key"] != a["request_key"]


def test_drain_produces_reviewable_proposals_not_evidence(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="worked_example")
    result = RR.drain_requests(repo)
    assert len(result["completed"]) == 1
    objs = repo.source_objects_for_source("src1")
    assert len(objs) == 1
    assert objs[0]["version"]["status"] == "proposed"  # never auto-admitted
    assert repo.mapping_proposals(status="proposed")  # reviewable mapping proposal


def test_drain_lease_is_fenced_and_reruns_are_noops(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="ask")
    first = RR.drain_requests(repo)
    assert len(first["completed"]) == 1
    second = RR.drain_requests(repo)  # nothing runnable -> no dup work
    assert second["completed"] == []


def test_token_cap_keeps_capture_and_never_expands_scope(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo, big=True)
    res = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                             span_id="s3", preset="worked_example")
    assert res["capped"] is True and res["cap_remaining"] < 0
    drain = RR.drain_requests(repo)
    # Capped request resolves partial with a visible reason; no synthesis produced.
    assert drain["partial"] and not drain["completed"]
    assert repo.source_objects_for_source("src1") == []


def test_cancel_request_never_cancels_the_local_capture(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    res = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                             span_id="s1", preset="ask")
    cancelled = RR.cancel_request(repo, request_id=res["request_id"])
    assert cancelled["status"] == "cancelled"
    # The drain skips a cancelled request; nothing runs.
    assert RR.drain_requests(repo)["completed"] == []

# ---------------------------------------------------------------------------
# model_synthesis: the real synthesize seam (grounded, candidate-only).
# ---------------------------------------------------------------------------


class _FakePresetClient:
    def __init__(self, content_md: str = "A worked example: diagonalize A.",
                 span_ids: list[str] | None = None) -> None:
        self.calls: list = []
        self._content_md = content_md
        self._span_ids = span_ids

    def run_reader_preset_synthesis(self, context):
        from learnloop.codex.schemas import ReaderPresetSynthesis

        self.calls.append(context)
        span_ids = self._span_ids
        if span_ids is None:
            span_ids = [context.blocks[0]["span_id"]]
        return ReaderPresetSynthesis(content_md=self._content_md, span_ids=span_ids)


def test_model_synthesis_lands_generated_content_as_proposed_object(tmp_path: Path) -> None:
    import json as json_mod

    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="worked_example")
    client = _FakePresetClient()
    result = RR.drain_requests(repo, synthesize=RR.model_synthesis(client))
    assert len(result["completed"]) == 1
    assert len(client.calls) == 1
    assert client.calls[0].preset == "worked_example"

    objs = repo.source_objects_for_source("src1")
    assert len(objs) == 1
    version = objs[0]["version"]
    assert version["status"] == "proposed"  # never auto-admitted
    assert version["object_type"] == "worked_example"
    content = json_mod.loads(version["content_json"])
    assert content["content_md"].startswith("A worked example")
    assert repo.mapping_proposals(status="proposed")


def test_model_synthesis_rejects_invented_spans(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="ask")
    client = _FakePresetClient(span_ids=["s99"])
    result = RR.drain_requests(repo, synthesize=RR.model_synthesis(client))
    # Invalid citation -> failed (retryable), and nothing is landed.
    assert result["failed"] and not result["completed"]
    assert repo.source_objects_for_source("src1") == []


def test_model_synthesis_without_provider_support_fails_visibly(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="ask")
    result = RR.drain_requests(repo, synthesize=RR.model_synthesis(object()))
    assert result["failed"] and not result["completed"]
    row = repo.get_reader_request(result["failed"][0])
    assert row["status"] == "failed"  # retryable; stub content never impersonates synthesis

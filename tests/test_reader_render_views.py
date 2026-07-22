"""Render views + crosswalk + block health + crop (spec §3, §15.1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth, PageHealth
from learnloop.services import block_health as BH
from learnloop.services import source_render_views as RV
from learnloop.services import span_view as SV
from tests.test_source_inventory import _persist, _register_revision


def _setup(tmp_path: Path, text: str = "Symmetric matrices have real eigenvalues.") -> Repository:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Section", text="# Chapter", ordinal=0, page=0, bbox=[10, 10, 300, 30]),
        DocumentBlock.build(span_id="s2", block_type="Text", text=text, ordinal=1, page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"]),
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s", span_ids=["s1", "s2"])],
        blocks=blocks, assets=[], health=ExtractionHealth(pages=[PageHealth(page=0, flags=[])]),
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    return repo


def test_render_view_is_idempotent_on_request_hash(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    v1 = RV.resolve_or_create_render_view(repo, extraction_id="ext1")
    v2 = RV.resolve_or_create_render_view(repo, extraction_id="ext1")
    assert v1["id"] == v2["id"]
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM source_render_views").fetchone()[0] == 1


def test_render_payload_states_six_authority_layers(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    view = RV.resolve_or_create_render_view(repo, extraction_id="ext1")
    payload = RV.render_payload(repo, view["id"])
    assert len(payload["layers"]) == 6
    assert "render_view" in payload["layers"]
    assert len(payload["blocks"]) == 2
    assert payload["blocks"][0]["display_node_id"].startswith("node-")


def test_unsafe_source_html_is_sanitized_inert(tmp_path: Path) -> None:
    repo = _setup(tmp_path, text="See <script>alert(1)</script> and a javascript:evil link.")
    view = RV.resolve_or_create_render_view(repo, extraction_id="ext1")
    payload = RV.render_payload(repo, view["id"])
    prose = next(b for b in payload["blocks"] if b["span_id"] == "s2")
    assert "<script" not in prose["markdown"]
    assert "javascript:" not in prose["markdown"]
    assert prose["sanitized"] is True


def test_reextraction_changes_render_version_not_content_hash_bytes(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    v1 = RV.resolve_or_create_render_view(repo, extraction_id="ext1")
    # A new extraction (bumped marker version) yields a NEW render view/request hash.
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Section", text="# Chapter", ordinal=0),
        DocumentBlock.build(span_id="s2", block_type="Text", text="Symmetric matrices have real eigenvalues.", ordinal=1),
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="2",
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s", span_ids=["s1", "s2"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext2")
    v2 = RV.resolve_or_create_render_view(repo, extraction_id="ext2")
    assert v2["id"] != v1["id"]
    assert v2["request_hash"] != v1["request_hash"]
    # The pinned revision id is unchanged across the render upgrade.
    assert v2["revision_id"] == v1["revision_id"] == "rev1"


def test_block_health_statuses_and_recommended_views(tmp_path: Path) -> None:
    # ok text block (has geometry, clean text).
    ok = DocumentBlock.build(span_id="a", block_type="Text", text="clean prose about eigenvalues", ordinal=0, page=0, bbox=[0, 0, 100, 20])
    h = BH.analyze_block_health(ok, PageHealth(page=0, flags=[]))
    assert h["status"] == "ok"
    assert h["recommended_view"] == "derived"

    # no geometry -> warn_link.
    nogeo = DocumentBlock.build(span_id="b", block_type="Text", text="prose without geometry", ordinal=1)
    h = BH.analyze_block_health(nogeo, None)
    assert "geometry_missing" in h["reason_flags"]
    assert h["recommended_view"] == "warn_link"

    # low-confidence equation with geometry -> suspect + crop_adjacent.
    eq = DocumentBlock.build(span_id="c", block_type="Equation", text="E = mc^2", ordinal=2, page=0, bbox=[0, 0, 100, 20])
    h = BH.analyze_block_health(eq, PageHealth(page=0, flags=[]), equation_confidence=0.2)
    assert h["status"] == "suspect"
    assert "equation_low_confidence" in h["reason_flags"]
    assert h["recommended_view"] == "crop_adjacent"

    # OCR-garbled block with geometry -> failed + crop_default.
    garbled = DocumentBlock.build(span_id="d", block_type="Text", text="a�����z", ordinal=3, page=0, bbox=[0, 0, 100, 20])
    h = BH.analyze_block_health(garbled, PageHealth(page=0, flags=[]))
    assert h["status"] == "failed"
    assert h["recommended_view"] == "crop_default"


def test_block_original_region_falls_back_when_no_pdf(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    region = SV.build_block_region(repo, "ext1", "s2")
    # No real PDF on disk -> region render is None with an explicit reason, never a crash.
    assert region["span_id"] == "s2"
    assert region["region_render"] is None
    assert region["reason"] in {"no_geometry", "page_fallback"}

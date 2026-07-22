"""reader.pdf_view sidecar RPC — Tier-2 embedded-PDF manifest contract."""

from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.originals import store_original_bytes
from tests.test_sidecar_reader_p3 import _rpc, _setup


def test_pdf_view_manifest_from_originals_store(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    stored = store_original_bytes(root, "sha256:abc", b"%PDF-1.7 fake body")
    out = _rpc(root, [("reader.pdf_view", {"extractionId": "ext1"})])
    result = out[1]["result"]
    assert result["available"] is True
    assert result["fileName"] == stored.name == "sha256-abc"
    assert result["extractionId"] == "ext1"
    assert result["sourceId"] == "src1"
    assert result["blocks"] == [
        {"spanId": "s1", "page": 0, "bbox": [10, 50, 300, 90], "blockType": "Text"}
    ]


def test_pdf_view_resolves_source_ref_like_render_view(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    store_original_bytes(root, "sha256:abc", b"%PDF-1.7 fake body")
    # Point the artifact's current revision at rev1 so a source id resolves.
    repo = Repository(root / "state.sqlite")
    with repo.connection() as connection:
        connection.execute("UPDATE source_artifacts SET current_revision_id='rev1' WHERE id='src1'")
        connection.commit()
    out = _rpc(root, [("reader.pdf_view", {"extractionId": "src1"})])
    assert out[1]["result"]["available"] is True


def test_pdf_view_unavailable_without_bytes_or_local_original(tmp_path: Path) -> None:
    # No store copy and original_uri (file:///book.pdf) does not exist on disk.
    root = _setup(tmp_path)
    out = _rpc(root, [("reader.pdf_view", {"extractionId": "ext1"})])
    result = out[1]["result"]
    assert result["available"] is False
    assert result["fileName"] is None
    assert result["blocks"] == []


def test_capture_from_pdf_selection_persists_paintable_geometry(tmp_path: Path) -> None:
    """The durable-trail contract: a pdf.js text-layer selection (whitespace
    differs from extraction text) still anchors exact, and source_annotations
    returns the segment geometry the PDF surface paints on reopen."""

    import json

    root = _setup(tmp_path)
    out = _rpc(root, [
        (
            "reader.capture",
            {
                "sourceId": "src1",
                "revisionId": "rev1",
                "extractionId": "ext1",
                "action": "highlight",
                "clientIdempotencyKey": "k-pdf-1",
                # Extraction text: "Symmetric matrices have real eigenvalues."
                "rawSelection": {"nodes": [{"spanId": "s1", "quote": "matrices  have\nreal"}]},
                "learnerText": "trail note",
            },
        ),
        ("reader.source_annotations", {"sourceId": "src1"}),
    ])
    assert out[1]["result"]["anchorStatus"] == "exact"
    row = out[2]["result"]["annotations"][0]
    assert row["anchor"]["status"] == "exact"
    segment = row["segments"][0]
    assert segment["exactQuote"] == "matrices have real"
    assert json.loads(segment["geometryJson"]) == {"page": 0, "bbox": [10.0, 50.0, 300.0, 90.0]}
    assert row["version"]["learnerText"] == "trail note"
    assert row["version"]["annotationType"] == "highlight"


def test_whole_block_tag_capture_clamps_offsets_to_full_text(tmp_path: Path) -> None:
    """Right-click tag with no selection sends start=0/end=huge; server-side
    clamping must anchor the whole block exactly, with paintable geometry."""

    import json

    root = _setup(tmp_path)
    out = _rpc(root, [
        (
            "reader.capture",
            {
                "sourceId": "src1",
                "revisionId": "rev1",
                "extractionId": "ext1",
                "action": "question",
                "clientIdempotencyKey": "k-tag-1",
                "rawSelection": {"nodes": [{"spanId": "s1", "start": 0, "end": 1000000}]},
                "learnerText": "",
            },
        ),
        ("reader.source_annotations", {"sourceId": "src1"}),
    ])
    assert out[1]["result"]["anchorStatus"] == "exact"
    row = out[2]["result"]["annotations"][0]
    segment = row["segments"][0]
    assert segment["exactQuote"] == "Symmetric matrices have real eigenvalues."
    assert row["version"]["annotationType"] == "question"
    assert json.loads(segment["geometryJson"]) == {"page": 0, "bbox": [10.0, 50.0, 300.0, 90.0]}


def test_pdf_view_backfills_store_from_live_local_original(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    raw = b"%PDF-1.7 live original"
    from learnloop.ingest.hashing import asset_hash

    local = tmp_path / "orig.pdf"
    local.write_bytes(raw)
    repo = Repository(root / "state.sqlite")
    with repo.connection() as connection:
        connection.execute(
            "UPDATE source_revisions SET asset_hash=?, original_uri=? WHERE id='rev1'",
            (asset_hash(raw), local.as_uri()),
        )
        connection.commit()
    out = _rpc(root, [("reader.pdf_view", {"extractionId": "ext1"})])
    result = out[1]["result"]
    assert result["available"] is True
    # The manifest triggered an on-demand backfill into the store.
    assert (root / "canonical-sources" / "raw" / result["fileName"]).read_bytes() == raw

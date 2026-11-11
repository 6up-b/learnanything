"""P3 reader sidecar RPC contract (render/annotate/capture over serve())."""

from __future__ import annotations

from pathlib import Path

from tests.sidecar_reader_p3_helpers import _rpc, _setup


def test_render_capture_annotate_flow(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.render_view", {"extractionId": "ext1"}),
        ("reader.translate_selection", {"extractionId": "ext1", "rawSelection": {"nodes": [{"spanId": "s1", "quote": "Symmetric"}]}}),
        ("reader.capture", {"sourceId": "src1", "revisionId": "rev1", "extractionId": "ext1", "action": "interpretation", "clientIdempotencyKey": "k1", "rawSelection": {"nodes": [{"spanId": "s1", "quote": "eigenvalues"}]}, "learnerText": "note"}),
        ("reader.drain_outbox", {}),
        ("reader.block_health", {"extractionId": "ext1", "spanId": "s1"}),
        ("reader.source_annotations", {"sourceId": "src1"}),
    ])
    render = out[1]["result"]
    assert len(render["blocks"]) == 1
    assert len(render["layers"]) == 6
    assert out[2]["result"]["status"] == "exact"
    capture = out[3]["result"]
    assert capture["receipt"] == "acknowledged"
    assert capture["anchorStatus"] == "exact"
    assert out[4]["result"]["drained"]
    assert out[5]["result"]["status"] == "ok"
    assert len(out[6]["result"]["annotations"]) == 1


def test_p3_reader_methods_gated_when_disabled(tmp_path: Path) -> None:
    root = _setup(tmp_path, reader_enabled=False)
    out = _rpc(root, [("reader.render_view", {"extractionId": "ext1"})])
    assert out[1]["error"]["data"]["code"] == "reader_disabled"


def test_render_view_resolves_source_and_revision_refs(tmp_path: Path) -> None:
    """The library can open a source directly: render_view resolves a source
    artifact id (or revision id) to its latest completed extraction."""

    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.render_view", {"extractionId": "src1"}),
        ("reader.render_view", {"extractionId": "rev1"}),
        ("reader.render_view", {"extractionId": "missing"}),
    ])
    by_source = out[1]["result"]
    assert by_source["extractionId"] == "ext1"
    assert by_source["sourceId"] == "src1"
    assert len(by_source["blocks"]) == 1
    assert out[2]["result"]["extractionId"] == "ext1"
    assert out[3]["error"]["data"]["code"] == "extraction_not_found"

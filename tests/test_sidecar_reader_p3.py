"""P3 reader sidecar RPC contract (render/annotate/capture over serve())."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth, PageHealth
from learnloop_sidecar.server import serve
from tests.helpers import create_basic_vault
from tests.test_source_inventory import _persist, _register_revision


def _setup(tmp_path: Path, *, reader_enabled: bool = True) -> Path:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    toml = root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    desired = f"reader_enabled = {'true' if reader_enabled else 'false'}"
    if "reader_enabled" in text:
        text = re.sub(r"reader_enabled = (true|false)", desired, text)
    else:
        text += f"\n[tutor_qa]\n{desired}\n"
    toml.write_text(text, encoding="utf-8")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="Symmetric matrices have real eigenvalues.", ordinal=1, page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"])]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s", span_ids=["s1"])],
        blocks=blocks, assets=[], health=ExtractionHealth(pages=[PageHealth(page=0, flags=[])]),
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    return root


def _rpc(root: Path, calls: list[tuple[str, dict]]) -> list[dict]:
    messages = [{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"vaultPath": str(root)}}]
    for i, (method, params) in enumerate(calls, start=1):
        messages.append({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


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

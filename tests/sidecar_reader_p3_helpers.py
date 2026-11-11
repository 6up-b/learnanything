"""What other test files use from ``tests/test_sidecar_reader_p3.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth, PageHealth
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


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

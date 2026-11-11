"""What other test files use from ``tests/test_sidecar_reader.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
import json

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop_sidecar.server import serve

from tests.helpers import append_config_toml, create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _init(vault_root):
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}


def _set_reader(vault_root, enabled: bool) -> None:
    """Pin tutor_qa.reader_enabled in the vault toml (L8): the reader RPCs are
    gated server-side on this flag. Set explicitly — the ship default flipped to
    enabled (owner decision 2026-07-20), so disabled tests must opt out."""

    append_config_toml(
        vault_root,
        f"""
        [tutor_qa]
        reader_enabled = {'true' if enabled else 'false'}
        """,
    )


def _setup(tmp_path, *, enable_reader: bool = True):
    paths = create_basic_vault(tmp_path / "vault")
    _set_reader(tmp_path / "vault", enable_reader)
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Text", text="Intro.", ordinal=0,
                            page=1, bbox=[10.0, 10.0, 200.0, 40.0], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s1", block_type="Text", text="A^T = A defines symmetry.",
                            ordinal=1, page=1, bbox=[10.0, 50.0, 200.0, 90.0], section_path=["Ch1"]),
    ]
    unit = DocumentUnit(unit_id="u1", label="Sym", ordinal=0, semantic_hash="sha256:s",
                        page_start=1, page_end=1, span_ids=["s0", "s1"])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks,
                    assets=[], health=ExtractionHealth())
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    return tmp_path / "vault"

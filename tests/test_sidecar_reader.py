"""P2 reader-dialogue sidecar contract tests (spec §7.6, U-033; design B.11).

Drives the real serve() over in-memory stdio (mirrors test_sidecar_golden_path).
Covers the non-AI reader RPCs; reader.ask (a live tutor call) is exercised at the
service level in test_reader_dialogue.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop_sidecar.server import serve

from tests.helpers import NOW, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision

_CLOCK = FrozenClock(NOW)


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

    import re

    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    desired = f"reader_enabled = {'true' if enabled else 'false'}"
    config_path.write_text(re.sub(r"reader_enabled = (true|false)", desired, text), encoding="utf-8")


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


def test_reader_prompt_contract_rpc(tmp_path):
    root = _setup(tmp_path, enable_reader=False)  # reader explicitly disabled
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.prompt_contract", "params": {}},
    ])
    result = resp[1]["result"]
    assert result["notSocraticByDefault"] is True
    assert result["readerEnabled"] is False  # explicitly disabled (§12.3.2 gating)


def test_reader_set_answer_mode_rpc(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.set_answer_mode",
         "params": {"extractionId": "ext1", "spanId": "s1", "answerMode": "help_me_reason"}},
    ])
    assert resp[1]["result"]["answerMode"] == "help_me_reason"
    assert resp[1]["result"]["eventId"]


def test_reader_guide_plan_rpc_returns_real_section_boundaries(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.guide_plan",
         "params": {"extractionId": "ext1"}},
    ])
    result = resp[1]["result"]
    assert result["sourceId"] == "src1"
    assert result["selectionBasis"] == "reviewed boundary placements + local learner state + active goal + source provenance"
    assert result["sections"] == [{
        "id": "u1",
        "label": "Sym",
        "startSpanId": "s0",
        "endSpanId": "s1",
        "spanIds": ["s0", "s1"],
        "question": None,
        "suggestedPassages": [],
    }]


def test_reader_present_and_skip_question_rpc(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.present_question",
         "params": {"practiceItemId": "pi_svd_define_001", "readingPhase": "before_section"}},
    ])
    result = resp[1]["result"]
    assert result["purpose"] == "instructional"
    assert result["readingPhase"] == "before_section"
    assert result["sourceVisible"] is True
    assert result["certificationEligible"] is False

    skip = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.skip_question",
         "params": {"administrationId": result["administrationId"]}},
    ])
    assert skip[1]["result"]["signal"] == "interaction_policy"


def test_reader_choose_disposition_rpc(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.choose_disposition",
         "params": {"disposition": "comprehension_only", "subjectId": "span:ext1/s1"}},
    ])
    assert resp[1]["result"]["mechanism"] == "logged_only"


def test_reader_routing_prior_rpc_empty(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.routing_prior",
         "params": {"targetKey": "tcv-unknown"}},
    ])
    result = resp[1]["result"]
    assert result["label"] == "heuristic"
    assert result["superseded"] is False
    assert result["reasons"] == {}


def test_reader_restore_source_rpc(tmp_path):
    root = _setup(tmp_path)
    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.restore_source",
         "params": {"extractionId": "ext1", "spanId": "s1"}},
    ])
    assert resp[1]["result"]["eventId"]
    assert resp[1]["result"]["coldEligibilityBurned"] is False


def test_reader_rpcs_are_gated_when_reader_disabled(tmp_path):
    """L8 contract test: with the reader disabled, every mutating/answering reader.* RPC
    is refused server-side; only reader.prompt_contract answers (it reports the flag)."""

    root = _setup(tmp_path, enable_reader=False)  # reader OFF (explicit opt-out)
    # prompt_contract still answers and reports the disabled flag.
    contract = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.prompt_contract", "params": {}},
    ])
    assert contract[1]["result"]["readerEnabled"] is False

    gated = {
        "reader.set_answer_mode": {"extractionId": "ext1", "spanId": "s1", "answerMode": "help_me_reason"},
        "reader.present_question": {"practiceItemId": "pi_svd_define_001", "readingPhase": "before_section"},
        "reader.choose_disposition": {"disposition": "comprehension_only", "subjectId": "span:ext1/s1"},
        "reader.routing_prior": {"targetKey": "t1"},
        "reader.restore_source": {"extractionId": "ext1", "spanId": "s1"},
    }
    for rpc_method, rpc_params in gated.items():
        resp = _rpc([
            _init(root),
            {"jsonrpc": "2.0", "id": 2, "method": rpc_method, "params": rpc_params},
        ])
        assert "error" in resp[1], f"{rpc_method} must be gated when reader disabled"
        assert resp[1]["error"]["data"]["code"] == "reader_disabled"


# ---------------------------------------------------------------------------
# Per-source reader gate (migration 104) + reader.watch_plan
# ---------------------------------------------------------------------------

def _repo_for(root) -> Repository:
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault = load_vault(root)
    return Repository(VaultPaths(vault.root, vault.config).sqlite_path)


def test_render_view_refused_for_reader_disabled_source(tmp_path):
    root = _setup(tmp_path)  # vault-level reader ON
    _repo_for(root).set_source_reader_enabled("src1", False)

    resp = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.render_view", "params": {"extractionId": "ext1"}},
    ])[1]
    assert "error" in resp
    assert resp["error"]["data"]["code"] == "reader_disabled_for_source"

    # Library card reports the flag so the picker can label it.
    library = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 3, "method": "get_source_library", "params": {}},
    ])[1]["result"]
    card = next(c for c in library["sources"] if c["sourceId"] == "src1")
    assert card["readerEnabled"] is False


def test_watch_plan_returns_video_id_for_youtube_source(tmp_path):
    root = _setup(tmp_path)
    _repo_for(root).upsert_source_artifact(
        id="src_yt",
        acquisition_kind="youtube",
        canonical_uri="https://www.youtube.com/watch?v=abc123XYZ_-",
    )

    plan = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.watch_plan", "params": {"sourceId": "src_yt"}},
    ])[1]["result"]
    assert plan["videoId"] == "abc123XYZ_-"
    assert plan["embedUrl"].startswith("https://www.youtube-nocookie.com/embed/abc123XYZ_-")
    assert plan["pausePoints"] == []

    # Non-video sources refuse watch mode.
    not_video = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.watch_plan", "params": {"sourceId": "src1"}},
    ])[1]
    assert not_video["error"]["data"]["code"] == "not_a_video"

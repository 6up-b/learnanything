"""P2 DIAGNOSTIC track -- sidecar contract tests (spec_p2 §9; design B.4-B.5).

Drives the real serve() over in-memory stdio, mirroring test_sidecar_golden_path.py.
"""

from __future__ import annotations

import io
import json

from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _init(vault_root):
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}


_SPEC = {
    "source_rev": "rev-1",
    "unit_id": "unit-a",
    "family_key": "method-selection",
    "exemplars": [{"exemplar_ref": "pi_svd_define_001", "unit_id": "unit-a", "family_key": "method-selection"}],
    "solution_recipes": [{"all_of": [
        {"facet": "f1", "capability": "method_selection"},
        {"facet": "f2", "capability": "procedure_execution"},
    ]}],
    "failure_signature_triage": {"wrong_method": "method_selection"},
}

_CONTRACT_BODY = {
    "purpose": "method selection",
    "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
    "required_capabilities": ["method_selection"],
    "baseline_milestone": "m0",
    "exemplars": [{"id": "pi_svd_define_001", "surface_ref": "pi_svd_define_001", "weight": 1.0}],
}

_CARDS = [
    {"card_slug": "card_target_setup", "coverage": ["method_selection x symmetric"]},
    {"card_slug": "card_method", "coverage": ["method_selection x confusable"]},
    {"card_slug": "card_procedure", "coverage": ["procedure_execution x symmetric"]},
]


def _register_and_review(vault_root) -> str:
    resp = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.register",
         "params": {"blueprintSlug": "bp1", "spec": _SPEC}},
    ])
    bv_id = resp[1]["result"]["blueprintVersionId"]
    _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.review",
         "params": {"blueprintVersionId": bv_id, "checks": {"one_family": True}}},
    ])
    return bv_id


def _confirm_and_triaging(vault_root, bv_id) -> str:
    run_id = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.confirm", "params": {
            "goalId": "g1", "blueprintVersionId": bv_id, "contractBody": _CONTRACT_BODY,
            "depthPreset": "master_tasks_like_these", "sourceRev": "rev-1", "unitId": "unit-a",
            "assessmentPracticeItemId": "pi_svd_define_001",
        }},
    ])[1]["result"]["runId"]
    for i, target in enumerate(("measuring", "triaging")):
        _rpc([
            _init(vault_root),
            {"jsonrpc": "2.0", "id": 2, "method": "golden_path.advance", "params": {
                "runId": run_id, "toState": target, "reason": target, "idempotencyKey": f"k{i}"}},
        ])
    return run_id


# ---------------------------------------------------------------------------
# pack_*
# ---------------------------------------------------------------------------

def test_pack_assemble_admit_review_list(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)

    pack = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.pack_assemble",
         "params": {"packSlug": "pack1", "blueprintVersionId": bv_id, "cards": _CARDS}},
    ])[1]["result"]
    assert pack["status"] == "draft"
    assert len(pack["cards"]) == 3
    pack_id = pack["packId"]

    for card in _CARDS:
        _rpc([
            _init(vault_root),
            {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.pack_admit",
             "params": {"packId": pack_id, "cardSlug": card["card_slug"]}},
        ])
    reviewed = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.pack_review",
         "params": {"packId": pack_id}},
    ])[1]["result"]
    assert reviewed["status"] == "reviewed"

    listing = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.pack_list",
         "params": {"blueprintVersionId": bv_id}},
    ])[1]["result"]
    assert [p["packId"] for p in listing["packs"]] == [pack_id]


def test_pack_wrong_count_returns_stable_error(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    resp = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.pack_assemble",
         "params": {"packSlug": "pack1", "blueprintVersionId": bv_id,
                    "cards": [{"card_slug": "solo", "coverage": ["x"]}]}},
    ])[1]
    assert resp["error"]["data"]["code"] == "invalid_pack"


# ---------------------------------------------------------------------------
# triage_*
# ---------------------------------------------------------------------------

def test_triage_decisive_routes_and_status(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    run_id = _confirm_and_triaging(vault_root, bv_id)

    result = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage", "params": {
            "runId": run_id, "attempt": {"attempt_id": "a1", "coarse_class": "dont_know",
                                         "exposure_history": "never_exposed"}}},
    ])[1]["result"]
    assert result["tier"] == "one" and result["decisive"] is True
    assert result["reason"] == "unfamiliar_or_missing_knowledge"
    assert result["routedTo"] == "instructing"

    status = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage_status", "params": {"runId": run_id}},
    ])[1]["result"]
    assert status["latest"]["kind"] == "triaged"
    assert len(status["trace"]) == 1


def test_triage_tier_two_is_decision_aid_then_decide(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    run_id = _confirm_and_triaging(vault_root, bv_id)

    aid = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage", "params": {
            "runId": run_id, "attempt": {"attempt_id": "a1", "coarse_class": "wrong",
                                         "error_signature": "wrong_method", "grader_confidence": 0.3}}},
    ])[1]["result"]
    assert aid["tier"] == "two" and aid["routed"] is False and aid["autoCommitted"] is False

    decided = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage_decide", "params": {
            "runId": run_id, "triageEventId": aid["eventId"], "chosenReason": aid["reason"]}},
    ])[1]["result"]
    assert decided["routed"] is True and decided["routedTo"] == "instructing"


def test_triage_override_logs_anchor_via_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    run_id = _confirm_and_triaging(vault_root, bv_id)

    aid = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage", "params": {
            "runId": run_id, "attempt": {"attempt_id": "a1", "coarse_class": "wrong",
                                         "error_signature": "wrong_method", "grader_confidence": 0.3}}},
    ])[1]["result"]
    overridden = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "diagnostic.triage_override", "params": {
            "runId": run_id, "triageEventId": aid["eventId"],
            "chosenReason": "procedure_execution", "actor": "owner"}},
    ])[1]["result"]
    assert overridden["kind"] == "overridden"
    assert overridden["anchorSampleId"] is not None

"""P2 golden-path spine -- sidecar contract tests (spec_p2 §9; design B.1-B.3).

Drives the real serve() over in-memory stdio, mirroring test_sidecar_contract.py.
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
    "solution_recipes": [{"all_of": [{"facet": "f1", "capability": "method_selection"}]}],
}

_CONTRACT_BODY = {
    "purpose": "method selection",
    "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
    "required_capabilities": ["method_selection"],
    "baseline_milestone": "m0",
    "exemplars": [{"id": "pi_svd_define_001", "surface_ref": "pi_svd_define_001", "weight": 1.0}],
}


def _register_and_review(vault_root) -> str:
    resp = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.register",
         "params": {"blueprintSlug": "bp1", "spec": _SPEC}},
    ])
    bv_id = resp[1]["result"]["blueprintVersionId"]
    review = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.review",
         "params": {"blueprintVersionId": bv_id, "checks": {"one_family": True}}},
    ])
    assert review[1]["result"]["status"] == "reviewed"
    return bv_id


def _confirm(vault_root, bv_id, goal_id="g1"):
    return _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.confirm", "params": {
            "goalId": goal_id,
            "blueprintVersionId": bv_id,
            "contractBody": _CONTRACT_BODY,
            "depthPreset": "master_tasks_like_these",
            "sourceRev": "rev-1",
            "unitId": "unit-a",
            "assessmentPracticeItemId": "pi_svd_define_001",
        }},
    ])[1]["result"]


def test_register_review_confirm_run_status(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)

    receipt = _confirm(vault_root, bv_id)
    assert receipt["mode"] == "certifying"
    assert receipt["currentState"] == "ready"
    assert receipt["minted"] is True
    run_id = receipt["runId"]

    status = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.run_status", "params": {"runId": run_id}},
    ])[1]["result"]
    assert status["currentState"] == "ready"
    assert status["nextAction"]["toState"] == "measuring"
    assert status["eventCount"] == 1


def test_advance_transition_via_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    run_id = _confirm(vault_root, bv_id)["runId"]

    advanced = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.advance", "params": {
            "runId": run_id, "toState": "measuring", "reason": "baseline", "idempotencyKey": "k1",
        }},
    ])[1]["result"]
    assert advanced["result"]["toState"] == "measuring"
    assert advanced["state"]["currentState"] == "measuring"


def test_illegal_transition_returns_stable_error(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id = _register_and_review(vault_root)
    run_id = _confirm(vault_root, bv_id)["runId"]

    response = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.advance", "params": {
            "runId": run_id, "toState": "assessing", "reason": "skip", "idempotencyKey": "bad",
        }},
    ])[1]
    assert response["error"]["data"]["code"] == "illegal_transition"


def test_invalid_blueprint_returns_stable_error(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bad_spec = dict(_SPEC)
    bad_spec["exemplars"] = [
        {"exemplar_ref": "a", "unit_id": "unit-a", "family_key": "method-selection"},
        {"exemplar_ref": "b", "unit_id": "unit-b", "family_key": "method-selection"},
    ]
    response = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.register",
         "params": {"blueprintSlug": "bp-bad", "spec": bad_spec}},
    ])[1]
    assert response["error"]["data"]["code"] == "invalid_blueprint"

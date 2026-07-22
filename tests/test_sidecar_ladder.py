"""P2 LEARNING + PRACTICE track -- sidecar contract tests (spec_p2 §9; design B.6-B.7).

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
    "solution_recipes": [{"all_of": [{"facet": "f1", "capability": "method_selection"}]}],
}

_CONTRACT_BODY = {
    "purpose": "method selection",
    "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
    "required_capabilities": ["method_selection"],
    "baseline_milestone": "m0",
    "exemplars": [{"id": "pi_svd_define_001", "surface_ref": "pi_svd_define_001", "weight": 1.0}],
}


def _register_review_confirm(vault_root) -> tuple[str, str]:
    reg = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.register",
         "params": {"blueprintSlug": "bp1", "spec": _SPEC}},
    ])
    bv_id = reg[1]["result"]["blueprintVersionId"]
    _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.review",
         "params": {"blueprintVersionId": bv_id, "checks": {"one_family": True}}},
    ])
    confirm = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.confirm", "params": {
            "goalId": "g1", "blueprintVersionId": bv_id, "contractBody": _CONTRACT_BODY,
            "depthPreset": "master_tasks_like_these", "sourceRev": "rev-1", "unitId": "unit-a",
            "assessmentPracticeItemId": "pi_svd_define_001",
        }},
    ])[1]["result"]
    return bv_id, confirm["runId"]


def _advance(vault_root, run_id, to_state, key):
    return _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.advance", "params": {
            "runId": run_id, "toState": to_state, "reason": "setup", "idempotencyKey": key,
        }},
    ])[1]["result"]


def test_ladder_policy_returns_the_seeded_ladder(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "ladder.policy", "params": {}},
    ])[1]["result"]
    assert result["policy"]["policySlug"] == "ladder_v1"
    assert len(result["stages"]) == 9
    assert all(s["mintsCertification"] == 0 for s in result["stages"])


def test_ladder_enter_and_advance_via_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _bv, run_id = _register_review_confirm(vault_root)
    _advance(vault_root, run_id, "measuring", "k1")
    _advance(vault_root, run_id, "triaging", "k2")
    _advance(vault_root, run_id, "instructing", "k3")

    entered = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "ladder.enter",
         "params": {"runId": run_id, "reason": "method_selection"}},
    ])[1]["result"]
    assert entered["stage"] == "setup_only"

    advanced = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "ladder.advance",
         "params": {"runId": run_id, "fromStage": "setup_only", "outcome": "pass", "surfaceId": "s1"}},
    ])[1]["result"]
    assert advanced["toStage"] == "independent_repair"

    status = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "ladder.status", "params": {"runId": run_id}},
    ])[1]["result"]
    assert status["currentStage"] == "independent_repair"


def test_practice_pool_assemble_and_admission_gate_via_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id, _run = _register_review_confirm(vault_root)

    pool = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.assemble", "params": {
            "poolSlug": "pool_rpc", "blueprintVersionId": bv_id,
            "surfaces": [{"surface_slug": "surf_a", "angle": "setup_only"}],
        }},
    ])[1]["result"]
    assert pool["poolSlug"] == "pool_rpc"
    assert pool["surfaces"][0]["admissionStatus"] == "candidate"
    pool_id = pool["poolId"]

    # Review before admission fails closed (U-028 -- nothing serves unreviewed).
    err = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.review", "params": {"poolId": pool_id}},
    ])[1]
    assert err["error"]["data"]["code"] == "invalid_pool"


def test_practice_pool_next_surface_empty_pool_is_fallback(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    bv_id, _run = _register_review_confirm(vault_root)
    pool = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.assemble", "params": {
            "poolSlug": "pool_empty", "blueprintVersionId": bv_id,
            "surfaces": [{"surface_slug": "surf_a", "angle": "setup_only"}],
        }},
    ])[1]["result"]
    selection = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.next_surface",
         "params": {"poolId": pool["poolId"]}},
    ])[1]["result"]
    assert selection["current"] is None and selection["fallback"] is True


# ---------------------------------------------------------------------------
# practice_pool.* run composition (for_run / seed_for_run / admit_anchor)
# ---------------------------------------------------------------------------

def _register_review_confirm_with(vault_root, *, anchor_ref: str, assessment_ref: str) -> tuple[str, str]:
    spec = {
        **_SPEC,
        "exemplars": [{"exemplar_ref": anchor_ref, "unit_id": "unit-a", "family_key": "method-selection"}],
    }
    body = {
        **_CONTRACT_BODY,
        "exemplars": [{"id": anchor_ref, "surface_ref": anchor_ref, "weight": 1.0}],
    }
    reg = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.register",
         "params": {"blueprintSlug": "bp_pool", "spec": spec}},
    ])
    bv_id = reg[1]["result"]["blueprintVersionId"]
    _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "blueprint.review",
         "params": {"blueprintVersionId": bv_id, "checks": {"one_family": True}}},
    ])
    confirm = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.confirm", "params": {
            "goalId": "g_pool", "blueprintVersionId": bv_id, "contractBody": body,
            "depthPreset": "master_tasks_like_these", "sourceRev": "rev-1", "unitId": "unit-a",
            "assessmentPracticeItemId": assessment_ref,
        }},
    ])[1]["result"]
    return bv_id, confirm["runId"]


def test_practice_pool_run_composition_seed_admit_review_serve(tmp_path):
    from tests.helpers import add_followup_item

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_followup_item(vault_root, "pi_svd_define_002")
    bv_id, run_id = _register_review_confirm_with(
        vault_root, anchor_ref="pi_svd_define_002", assessment_ref="pi_svd_define_001"
    )

    view = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.for_run", "params": {"runId": run_id}},
    ])[1]["result"]
    assert view["blueprintVersionId"] == bv_id
    assert view["poolId"] is None and view["pool"] is None
    anchors = {a["ref"]: a for a in view["anchors"]}
    assert anchors["pi_svd_define_002"]["inVault"] is True

    seeded = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.seed_for_run", "params": {"runId": run_id}},
    ])[1]["result"]
    pool_id = seeded["poolId"]
    assert pool_id is not None
    surfaces = seeded["pool"]["pool"]["surfaces"]
    assert [s["surfaceSlug"] for s in surfaces] == ["pi_svd_define_002"]
    assert surfaces[0]["admissionStatus"] == "candidate"

    admitted = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.admit_anchor",
         "params": {"runId": run_id, "poolId": pool_id, "surfaceSlug": "pi_svd_define_002"}},
    ])[1]["result"]
    surface = admitted["pool"]["pool"]["surfaces"][0]
    assert surface["admissionStatus"] == "admitted"
    assert surface["surfaceId"]

    reviewed = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.review", "params": {"poolId": pool_id}},
    ])[1]["result"]
    assert reviewed["status"] == "reviewed"

    selection = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.next_surface", "params": {"poolId": pool_id}},
    ])[1]["result"]
    assert selection["current"] is not None
    assert selection["current"]["surfaceId"] == surface["surfaceId"]


def test_practice_pool_admit_anchor_refuses_assessment_reserve_collision(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    # Anchor and assessment reserve are the SAME item -> identical surface hash;
    # admission must fail closed (§7.3 hard-collision refusal).
    _bv, run_id = _register_review_confirm_with(
        vault_root, anchor_ref="pi_svd_define_001", assessment_ref="pi_svd_define_001"
    )
    seeded = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.seed_for_run", "params": {"runId": run_id}},
    ])[1]["result"]
    err = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "practice_pool.admit_anchor",
         "params": {"runId": run_id, "poolId": seeded["poolId"], "surfaceSlug": "pi_svd_define_001"}},
    ])[1]
    assert err["error"]["data"]["code"] == "invalid_pool"


def test_golden_path_list_runs_exposes_reentry(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _bv, run_id = _register_review_confirm(vault_root)
    _advance(vault_root, run_id, "measuring", "k1")

    listed = _rpc([
        _init(vault_root),
        {"jsonrpc": "2.0", "id": 2, "method": "golden_path.list_runs", "params": {}},
    ])[1]["result"]
    runs = {r["runId"]: r for r in listed["runs"]}
    assert run_id in runs
    assert runs[run_id]["currentState"] == "measuring"
    assert runs[run_id]["goalId"] == "g1"

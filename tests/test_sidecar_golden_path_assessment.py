"""P2 ASSESSMENT + RESTORATION + MILESTONE track -- sidecar contract tests
(spec_p2 §9; design B.8-B.10). Drives real serve() over in-memory stdio."""

from __future__ import annotations

import io
import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import NOW, add_followup_item, create_basic_vault

CLOCK = FrozenClock(NOW)
HELD_OUT = "pi_svd_define_002"


def _rpc(messages):
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _init(vault_root):
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}


def _call(vault_root, method, params):
    return _rpc([_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])[1]


def _setup_run(vault_root):
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root, HELD_OUT)
    vault = load_vault(vault_root)
    repo = Repository(paths.sqlite_path)
    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": "pi_svd_define_001", "unit_id": "unit-a", "family_key": "method-selection"}],
        "solution_recipes": [{"all_of": [{"facet": "f1", "capability": "method_selection"}]}],
        "source_neighborhoods": {"method": ["span_intro"]},
        # Blueprint declares the reviewed edge the contract pins (C5).
        "depth_milestones": [{"edge_id": "e1", "reviewed": True, "milestone_slug": "m_transfer"}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    held = resolve_legacy_item(vault, repo, vault.practice_items[HELD_OUT], purpose="assessment", clock=CLOCK)
    body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"],
        "baseline_milestone": "m0",
        "depth_envelope": {
            "envelope_version": "denv_v1", "bounds": {},
            "reviewed_edges": [{"edge_id": "e1", "reviewed": True, "milestone_slug": "m_transfer"}],
        },
        "exemplars": [{"id": "pi_svd_define_001", "surface_ref": "pi_svd_define_001", "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a",
        assessment_surface_id=held.surface_id, clock=CLOCK,
    )
    from learnloop.services import golden_path_run as GPR
    GPR.advance(repo, receipt.run_id, to_state="ready_to_assess", reason="rta", idempotency_key="rta", clock=CLOCK)
    return receipt.run_id, held.surface_id


def test_assess_restore_and_depth_invitation_over_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    run_id, surface_id = _setup_run(vault_root)

    opened = _call(vault_root, "golden_path.assess_open", {"runId": run_id})["result"]
    admin_id = opened["administrationId"]

    result = _call(vault_root, "golden_path.assess_submit", {
        "runId": run_id, "administrationId": admin_id, "surfaceId": surface_id,
        "rubricScore": 4, "maxPoints": 4, "attemptId": "a1", "responseText": "ok",
    })["result"]
    assert result["passed"] is True
    assert result["claimLanguage"] in ("provisional", "calibrated")
    assert result["citedVersion"] == 1

    restored = _call(vault_root, "golden_path.restore", {"runId": run_id})["result"]
    assert restored["nextAction"] == "confirm_reviewed_edge"

    diff = _call(vault_root, "golden_path.boundary_diff", {"runId": run_id})["result"]
    assert diff["cells"]

    invite = _call(vault_root, "golden_path.depth_invitation", {"runId": run_id})["result"]
    assert invite["invitation"]["servedAs"] == "suggest_next"
    assert invite["invitation"]["activated"] is False

    # Explicit accept records intent WITHOUT activating (U-018 off).
    accepted = _call(vault_root, "golden_path.accept_edge", {"runId": run_id})["result"]
    assert accepted["activated"] is False
    assert accepted["intentRecorded"] is True


def test_practice_only_assess_open_returns_stable_error(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repo = Repository(paths.sqlite_path)
    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": "pi_svd_define_001", "unit_id": "unit-a", "family_key": "method-selection"}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    body = {
        "purpose": "x", "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"], "baseline_milestone": "m0",
        "exemplars": [{"id": "pi_svd_define_001", "surface_ref": "pi_svd_define_001", "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a", clock=CLOCK,
    )
    resp = _call(vault_root, "golden_path.assess_open", {"runId": receipt.run_id})
    assert resp["error"]["data"]["code"] == "practice_only_no_assessment"

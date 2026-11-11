"""P2 ASSESSMENT + RESTORATION + MILESTONE track -- sidecar contract tests
(spec_p2 §9; design B.8-B.10). Drives real serve() over in-memory stdio."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.curriculum import golden_path_confirm as GPC
from learnloop.curriculum import task_blueprints as TB
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault
from tests.sidecar_golden_path_assessment_helpers import CLOCK, _call, _setup_run

def test_assess_restore_and_depth_invitation_over_rpc(tmp_path):
    vault_root = tmp_path / "vault"
    run_id, surface_id = _setup_run(vault_root)

    opened = _call(vault_root, "golden_path.assess_open", {"runId": run_id})["result"]
    admin_id = opened["administrationId"]
    # Meas §3.A2/§3.A3: the cold assessment is a THIRD surface that asks a
    # learner to answer a Practice Item, and it carried the prompt alone. It now
    # reads the same presentation payload practice and exams do, so an error
    # hunt reserved onto a golden-path surface cannot be served solution-less.
    assert [block["kind"] for block in opened["presentation"]["blocks"]] == ["prompt"]
    assert opened["presentation"]["blocks"][0]["markdown"] == opened["prompt"]

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
    load_vault(vault_root)
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

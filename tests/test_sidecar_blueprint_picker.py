"""The library exemplar picker slice (blueprint.discover_candidates +
blueprint.compose_draft): a REAL, non-fixture desktop journey -- discover the
exemplar pool from vault items, compose + register a draft blueprint, owner-
review it, then atomically confirm a certifying run and read its state."""

from __future__ import annotations

import io
import json
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.services.item_authoring import author_item
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import add_followup_item, create_basic_vault

ANCHOR = "pi_svd_define_001"
LO = "lo_svd_definition"
GOAL = "goal_linear_algebra_ml"


def _rpc(root: Path, calls: list[tuple[str, dict]]) -> list[dict]:
    messages = [{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"vaultPath": str(root)}}]
    for i, (method_name, params) in enumerate(calls, start=1):
        messages.append({"jsonrpc": "2.0", "id": i, "method": method_name, "params": params})
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _vault_with_pool(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    add_followup_item(root)  # pi_svd_define_002
    repo = Repository(paths.sqlite_path)
    fresh = author_item(
        root,
        repo,
        learning_object_id=LO,
        prompt="Given a symmetric A, which decomposition reads off variances, and why?",
        expected_answer="The spectral decomposition; eigenvalues are the variances along principal axes.",
    )
    return root, fresh["id"]


def test_discover_compose_review_confirm_run(tmp_path: Path) -> None:
    root, held_out_id = _vault_with_pool(tmp_path)

    out = _rpc(root, [
        ("blueprint.discover_candidates", {}),
    ])
    pool = out[1]["result"]["pool"]
    assert len(pool) == 1 and pool[0]["learningObjectId"] == LO
    ids = {i["practiceItemId"] for i in pool[0]["items"]}
    assert {ANCHOR, "pi_svd_define_002", held_out_id} <= ids
    assert all(i["attempted"] is False for i in pool[0]["items"])

    out = _rpc(root, [
        ("blueprint.compose_draft", {
            "learningObjectId": LO,
            "anchorItemIds": [ANCHOR, "pi_svd_define_002"],
            "heldOutItemId": held_out_id,
        }),
    ])
    composed = out[1]["result"]
    blueprint = composed["blueprint"]
    assert blueprint["status"] == "draft"
    assert composed["warnings"] == []
    refs = {e["exemplarRef"]: e for e in blueprint["exemplars"]}
    assert refs[held_out_id]["heldOutWeight"] == 1.0
    assert refs[ANCHOR]["weight"] == 1.0
    contract_body = json.loads(composed["contractBodyJson"])
    assert contract_body["baseline_milestone"]  # snake_case survived the DTO layer

    version_id = blueprint["blueprintVersionId"]
    out = _rpc(root, [
        ("blueprint.review", {
            "blueprintVersionId": version_id,
            "checks": {"source_grounded": True, "rubric_verbatim": True, "one_family": True},
        }),
        ("golden_path.confirm", {
            "goalId": GOAL,
            "blueprintVersionId": version_id,
            "contractBody": contract_body,
            "depthPreset": "master_tasks_like_these",
            "sourceRev": composed["sourceRev"],
            "unitId": composed["unitId"],
            "assessmentPracticeItemId": held_out_id,
        }),
    ])
    # "reviewed" is confirmable -- the atomic confirmation activates it in-transaction.
    assert out[1]["result"]["status"] == "reviewed"
    receipt = out[2]["result"]
    run_id = receipt["runId"]
    assert receipt["mode"] == "certifying"

    out = _rpc(root, [("golden_path.run_status", {"runId": run_id})])
    state = out[1]["result"]
    assert state["runId"] == run_id
    assert state["mode"] == "certifying"


def test_compose_refuses_mixed_or_stale_selections(tmp_path: Path) -> None:
    root, held_out_id = _vault_with_pool(tmp_path)
    out = _rpc(root, [
        ("blueprint.compose_draft", {
            "learningObjectId": LO,
            "anchorItemIds": [ANCHOR],
            "heldOutItemId": ANCHOR,
        }),
        ("blueprint.compose_draft", {
            "learningObjectId": LO,
            "anchorItemIds": [],
            "heldOutItemId": held_out_id,
        }),
    ])
    assert out[1]["error"]["data"]["code"] == "validation_error"
    assert out[2]["error"]["data"]["code"] == "validation_error"

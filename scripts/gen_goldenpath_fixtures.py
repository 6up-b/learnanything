"""Deterministic P2 golden-path fixture generator (spec_tauri_ui §4, U-031).

Fixture vaults ARE the mock layer. This script builds the deterministic
golden-path fixture vault (``golden_path_fixture.build_golden_path_fixture``) and
drives the REAL sidecar ``serve()`` over in-memory stdio to capture the exact
camelCased JSON payloads every P2 Tauri screen renders. Output lands in
``apps/learnloop-tauri/src/fixtures/goldenpath/*.json`` so each new screen renders
offline (no live jobs, no AI providers) — the per-screen render acceptance item.

Run: ``uv run python scripts/gen_goldenpath_fixtures.py``
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from learnloop.services import golden_path_run as GPR
from learnloop.services import surface_pool as SP
from learnloop.services.activities import resolve_legacy_item
from learnloop.services.golden_path_fixture import (
    EXEMPLAR_A,
    EXEMPLAR_B,
    build_golden_path_fixture,
    stub_depth_edge,
    stub_diagnostic_pack,
    stub_pool_surfaces,
)
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop_sidecar.dto import to_camel
from learnloop_sidecar.server import serve

OUT_DIR = Path(__file__).resolve().parents[1] / "apps/learnloop-tauri/src/fixtures/goldenpath"


def _rpc(vault_root: Path, method: str, params: dict[str, Any]) -> dict[str, Any]:
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}
    call = {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}
    stdin = io.StringIO(json.dumps(init) + "\n" + json.dumps(call) + "\n")
    stdout = io.StringIO()
    serve(stdin, stdout)
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    resp = lines[1]
    if "error" in resp:
        raise RuntimeError(f"{method} failed: {resp['error']}")
    return resp["result"]


def _write(name: str, payload: Any) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{name}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"  wrote {name}.json")


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "vault"
        fixture = build_golden_path_fixture(root)
        run_id = fixture.receipt.run_id
        bv_id = fixture.blueprint_version_id
        surface_id = fixture.assessment_surface_id
        vault_root = fixture.root

        print("Capturing golden-path fixtures from the real sidecar...")

        # --- confirmation receipt (atomic confirmation screen) ------------------
        # camelCased to match golden_path.confirm's versioned() envelope.
        _write("confirmReceipt", {"version": 1, **to_camel(fixture.receipt.as_dict())})

        # --- blueprint version (exemplar selection / blueprint review) ----------
        _write("blueprintVersion", _rpc(vault_root, "blueprint.get_version", {"blueprintVersionId": bv_id}))

        # --- run status: ready (post-confirmation) ------------------------------
        _write("runStatusReady", _rpc(vault_root, "golden_path.run_status", {"runId": run_id}))

        # --- ladder policy (static nine-stage ladder) ---------------------------
        _write("ladderPolicy", _rpc(vault_root, "ladder.policy", {}))

        # --- reader prompt contract (reader gating) -----------------------------
        _write("readerPromptContract", _rpc(vault_root, "reader.prompt_contract", {}))

        # --- practice pool: assemble (rotating practice / owner admission) ------
        pool_stub = stub_pool_surfaces()
        pool = _rpc(vault_root, "practice_pool.assemble", {
            "poolSlug": pool_stub["pool_slug"],
            "blueprintVersionId": bv_id,
            "surfaces": pool_stub["surfaces"],
        })
        _write("poolAssembled", pool)
        _write("poolStatus", _rpc(vault_root, "practice_pool.status", {"poolId": pool["poolId"]}))

        # Admit + review two real practice surfaces so poolNextSurface exercises a
        # genuine ServedSurface (fresh/warmth/exposure flags), not the empty fallback (L5).
        repo = Repository(VaultPaths(vault_root, load_vault(vault_root).config).sqlite_path)
        vault = load_vault(vault_root)
        for slug, item_id in zip(
            [s["surface_slug"] for s in pool_stub["surfaces"]], (EXEMPLAR_A, EXEMPLAR_B)
        ):
            resolved = resolve_legacy_item(vault, repo, vault.practice_items[item_id], purpose="practice")
            SP.admit_pool_surface(repo, pool_id=pool["poolId"], surface_slug=slug, surface_id=resolved.surface_id)
        SP.review_pool(repo, pool_id=pool["poolId"])
        _write("poolNextSurface", _rpc(vault_root, "practice_pool.next_surface", {"poolId": pool["poolId"]}))

        # --- advance the run to ready_to_assess, then walk the cold assessment --
        GPR.advance(repo, run_id, to_state="ready_to_assess", reason="rta", idempotency_key="fixture-rta")
        _write("runStatusReadyToAssess", _rpc(vault_root, "golden_path.run_status", {"runId": run_id}))

        opened = _rpc(vault_root, "golden_path.assess_open", {"runId": run_id})
        _write("assessOpen", opened)
        admin_id = opened["administrationId"]

        submitted = _rpc(vault_root, "golden_path.assess_submit", {
            "runId": run_id, "administrationId": admin_id, "surfaceId": surface_id,
            "rubricScore": 4, "maxPoints": 4, "attemptId": "fixture-attempt-1", "responseText": "svd for symmetric",
        })
        _write("assessSubmit", submitted)
        _write("assessResult", _rpc(vault_root, "golden_path.assess_result", {"runId": run_id}))

        # --- restoration + boundary diff + milestone / depth invitation ---------
        _write("restore", _rpc(vault_root, "golden_path.restore", {"runId": run_id}))
        _write("boundaryDiff", _rpc(vault_root, "golden_path.boundary_diff", {"runId": run_id}))
        _write("depthInvitation", _rpc(vault_root, "golden_path.depth_invitation", {"runId": run_id}))
        _write("runStatusAssessed", _rpc(vault_root, "golden_path.run_status", {"runId": run_id}))

        # --- deterministic authoring stubs (owner-review artifacts, §C) ---------
        _write("stubDepthEdge", to_camel(stub_depth_edge()))
        _write("stubDiagnosticPack", to_camel(stub_diagnostic_pack()))
        _write("stubPoolSurfaces", to_camel(stub_pool_surfaces()))

    # --- two-tier triage decision aid on an isolated run (no state pollution) ---
    with TemporaryDirectory() as tmp2:
        root2 = Path(tmp2) / "vault"
        f2 = build_golden_path_fixture(root2)
        vr2 = f2.root
        rid2 = f2.receipt.run_id
        # Tier one: decisive fault route (a bad surface is never a learner deficit).
        _write("triageDecisive", _rpc(vr2, "diagnostic.triage", {
            "runId": rid2,
            "attempt": {"attempt_id": "fixture-triage-1", "surface_validity": "quarantined",
                        "grader_outcome_class": "fail", "grader_confidence": 0.9},
        }))
        # Tier two: provisional distribution presented as a decision aid.
        _write("triageProvisional", _rpc(vr2, "diagnostic.triage", {
            "runId": rid2,
            "attempt": {"attempt_id": "fixture-triage-2", "grader_outcome_class": "fail",
                        "grader_confidence": 0.4, "first_divergent_step": "decomposition_choice",
                        "provisional_distribution": {
                            "procedure_slip_or_execution_error": 0.45,
                            "method_selection_error": 0.35,
                            "false_belief_or_confusion": 0.2}},
        }))
        _write("triageStatus", _rpc(vr2, "diagnostic.triage_status", {"runId": rid2}))

    print(f"Done. Fixtures in {OUT_DIR}")


if __name__ == "__main__":
    main()

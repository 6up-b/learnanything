"""What other test files use from ``tests/test_sidecar_golden_path_assessment.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.curriculum import golden_path_confirm as GPC
from learnloop.curriculum import task_blueprints as TB
from learnloop.substrate.activities import resolve_legacy_item
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
    from learnloop.curriculum import golden_path_run as GPR
    GPR.advance(repo, receipt.run_id, to_state="ready_to_assess", reason="rta", idempotency_key="rta", clock=CLOCK)
    return receipt.run_id, held.surface_id

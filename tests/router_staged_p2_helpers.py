"""What other test files use from ``tests/test_router_staged_p2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.clock import FrozenClock
from learnloop.curriculum import golden_path_confirm as GPC
from learnloop.curriculum import task_blueprints as TB
from learnloop.db.repositories import Repository
from learnloop.scheduling import controller_ownership as own
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_basic_vault


CLOCK = FrozenClock(NOW)


def _run(tmp_path, *, toml: str | None = None):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    if toml:
        append_config_toml(root, toml)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]
    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": item.id, "unit_id": "unit-a", "family_key": "method-selection"}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": item.id, "surface_ref": resolved.surface_id, "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a",
        assessment_surface_id=resolved.surface_id, clock=CLOCK,
    )
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    return repo, receipt, vault


def _rows(repo) -> list[dict]:
    with repo.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM router_decisions ORDER BY created_at, id")]
    for row in rows:
        for column in ("candidates_json", "exclusions_json", "detail_json"):
            row[column] = json.loads(row[column])
    return rows

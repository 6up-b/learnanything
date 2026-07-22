"""P2 step 2 -- the ONE atomic confirmation (spec_p2 §3.1, §12.1, §12.6)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)

GOAL_ID = "goal-under-test"
FAULT_LABELS = [
    "blueprint_activated",
    "goal_contract_appended",
    "commitment_created",
    "reserve_created",
    "run_started",
]


def _setup(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    item = next(iter(vault.practice_items.values()))
    spec = {
        "source_rev": "rev-1",
        "unit_id": "unit-a",
        "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": item.id, "unit_id": "unit-a", "family_key": "method-selection"}],
        "solution_recipes": [{"all_of": [{"facet": "f1", "capability": "method_selection"}]}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    contract_body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": item.id, "surface_ref": resolved.surface_id, "weight": 1.0}],
    }
    return repo, bv, resolved.surface_id, contract_body


def _confirm(repo, bv_id, surface_id, contract_body, **over):
    kwargs = dict(
        goal_id=GOAL_ID,
        blueprint_version_id=bv_id,
        contract_body=contract_body,
        depth_preset="master_tasks_like_these",
        source_rev="rev-1",
        unit_id="unit-a",
        assessment_surface_id=surface_id,
        clock=CLOCK,
    )
    kwargs.update(over)
    return GPC.confirm_exemplar_and_start(repo, **kwargs)


def _counts(repo):
    with repo.connection() as c:
        runs = c.execute("SELECT COUNT(*) FROM golden_path_runs WHERE goal_id = ?", (GOAL_ID,)).fetchone()[0]
        commitments = c.execute("SELECT COUNT(*) FROM commitment_versions WHERE goal_id = ?", (GOAL_ID,)).fetchone()[0]
        live_reserves = c.execute(
            "SELECT COUNT(*) FROM activity_surface_reservations WHERE goal_id = ? AND status = 'reserved'",
            (GOAL_ID,),
        ).fetchone()[0]
    head = repo.fetch_goal_contract_head(GOAL_ID)
    return {"runs": runs, "commitments": commitments, "reserves": live_reserves, "head": head}


def test_confirmation_atomically_mints_contract_v1_and_pins_reserve(tmp_path):
    repo, bv, surface_id, body = _setup(tmp_path)
    receipt = _confirm(repo, bv.id, surface_id, body)
    assert receipt.minted is True and receipt.mode == "certifying"
    assert receipt.current_state == "ready"
    counts = _counts(repo)
    assert counts == {"runs": 1, "commitments": 1, "reserves": 1, "head": counts["head"]}
    assert counts["head"]["head_version"] == 1
    # Blueprint was activated inside the same transaction.
    assert repo.task_blueprint_version(bv.id)["status"] == "active"


def test_reconfirm_is_idempotent(tmp_path):
    repo, bv, surface_id, body = _setup(tmp_path)
    first = _confirm(repo, bv.id, surface_id, body)
    second = _confirm(repo, bv.id, surface_id, body)
    assert second.run_id == first.run_id and second.minted is False
    assert _counts(repo)["runs"] == 1


@pytest.mark.parametrize("label", FAULT_LABELS)
def test_fault_after_every_internal_boundary_leaves_no_partial_confirmation(tmp_path, label):
    repo, bv, surface_id, body = _setup(tmp_path)

    class _Boom(RuntimeError):
        pass

    def hook(stage):
        if stage == label:
            raise _Boom(stage)

    with pytest.raises(_Boom):
        _confirm(repo, bv.id, surface_id, body, fault_hook=hook)

    # Nothing became active: no run, no v1 head, no commitment, no live reserve, and
    # the blueprint activation rolled back too (§3.1 all-or-nothing).
    counts = _counts(repo)
    assert counts["runs"] == 0
    assert counts["commitments"] == 0
    assert counts["reserves"] == 0
    assert counts["head"] is None
    assert repo.task_blueprint_version(bv.id)["status"] == "reviewed"

    # A clean retry then yields exactly one of each side effect (§12.6).
    receipt = _confirm(repo, bv.id, surface_id, body)
    assert receipt.minted is True
    counts = _counts(repo)
    assert counts["runs"] == 1 and counts["commitments"] == 1 and counts["reserves"] == 1


def test_practice_only_when_no_fresh_assessment(tmp_path):
    repo, bv, _surface, body = _setup(tmp_path)
    receipt = _confirm(repo, bv.id, None, body, assessment_surface_id=None)
    assert receipt.mode == "practice_only"
    assert receipt.reserved_surface_id is None
    assert _counts(repo)["reserves"] == 0


def test_unreviewed_blueprint_refused(tmp_path):
    repo, _bv, surface_id, body = _setup(tmp_path)
    # A fresh draft blueprint (never reviewed) cannot be confirmed.
    draft = TB.register_blueprint_version(
        repo, blueprint_slug="bp-draft",
        spec={
            "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
            "exemplars": [{"exemplar_ref": "ex1", "unit_id": "unit-a", "family_key": "method-selection"}],
        },
        clock=CLOCK,
    )
    with pytest.raises(Exception):
        _confirm(repo, draft.id, surface_id, body, goal_id="goal-draft")
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM golden_path_runs WHERE goal_id = 'goal-draft'").fetchone()[0] == 0


def test_missing_baseline_not_confirmable(tmp_path):
    repo, bv, surface_id, body = _setup(tmp_path)
    body = dict(body)
    body.pop("baseline_milestone")
    with pytest.raises(GPC.NotConfirmable):
        _confirm(repo, bv.id, surface_id, body)


def test_reconfirm_differing_only_in_depth_preset_raises_mismatch(tmp_path):
    """C4: a re-confirm identical except for the depth preset must NOT silently return
    the run built with the original preset -- it raises an explicit mismatch."""

    repo, bv, surface_id, body = _setup(tmp_path)
    first = _confirm(repo, bv.id, surface_id, body, depth_preset="master_tasks_like_these")
    # Byte-identical re-confirm is still idempotent (same run, no second one).
    again = _confirm(repo, bv.id, surface_id, body, depth_preset="master_tasks_like_these")
    assert again.run_id == first.run_id and again.minted is False
    # A re-confirm that differs ONLY in the run-shaping depth preset is refused.
    with pytest.raises(GPC.ConfirmationMismatch):
        _confirm(repo, bv.id, surface_id, body, depth_preset="work_fluently")
    # No second run was minted for the goal.
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM golden_path_runs WHERE goal_id = ?", (GOAL_ID,)).fetchone()[0] == 1


def test_reviewed_edge_absent_from_blueprint_is_refused(tmp_path):
    """C5: a contract that pins a reviewed depth edge the blueprint does not declare is
    refused inside confirmation -- the run can never render an unreviewed depth edge."""

    repo, bv, surface_id, body = _setup(tmp_path)
    body = dict(body)
    body["depth_envelope"] = {
        "envelope_version": "denv_x",
        "reviewed_edges": [{"edge_id": "edge_not_in_blueprint", "reviewed": True, "milestone_slug": "m_x"}],
    }
    with pytest.raises(GPC.NotConfirmable):
        _confirm(repo, bv.id, surface_id, body, goal_id="goal-c5")
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM golden_path_runs WHERE goal_id = 'goal-c5'").fetchone()[0] == 0

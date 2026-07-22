"""P0.4 assessment reservation / burn enforcement + drift (spec §4.5, §7.3, §9.5)."""

from __future__ import annotations

import threading

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services import goal_contracts as gc
from learnloop.services.activities import (
    Administration,
    ExposureCollisionAtRender,
    RenderRefused,
    append_practice_successor_proposal,
    cancel_reservation,
    open_administration,
    render_assessment_with_replacement,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _add_item(root, item_id, *, prompt="Prompt.", stimulus=None):
    payload = {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "dont_know"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": prompt,
        "expected_answer": "Answer.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if stimulus is not None:
        payload["evidence_fingerprint"] = {"shared_stimulus_id": stimulus}
    upsert_practice_item(root, payload, clock=CLOCK)


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_a", prompt="Prompt A.")
    _add_item(root, "pi_b", prompt="Prompt B.")
    _add_item(root, "pi_stim_1", prompt="Stim prompt one.", stimulus="stim1")
    _add_item(root, "pi_stim_2", prompt="Stim prompt two.", stimulus="stim1")
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    return vault, repo, paths


def _item(vault, item_id):
    return vault.practice_items[item_id]


# --- §9.5 line 6 + §7.3 row 7: exposure collision at render refuses ---------

def test_exposure_collision_at_render_refuses(env):
    vault, repo, _ = env
    # Burn pi_a via a practice render (enters the shared ledger).
    practice = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=practice, clock=CLOCK)
    # An assessment render on the identical surface collides -> refuse.
    adapter = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=adapter.surface_id, purpose="assessment", clock=CLOCK)
    with pytest.raises(ExposureCollisionAtRender) as exc:
        open_administration(repo, resolved=adapter, reservation=reservation, clock=CLOCK)
    assert exc.value.reason == "exact_surface_collision"


def test_render_with_replacement_substitutes_fresh_surface(env):
    vault, repo, _ = env
    # Burn pi_a; leave pi_b fresh.
    practice = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=practice, clock=CLOCK)
    burned = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    fresh = resolve_legacy_item(vault, repo, _item(vault, "pi_b"), purpose="assessment", clock=CLOCK)
    result = render_assessment_with_replacement(
        repo, candidates=[burned, fresh], clock=CLOCK
    )
    assert isinstance(result, Administration)
    assert result.surface_id == fresh.surface_id


def test_render_with_replacement_refuses_when_exhausted(env):
    vault, repo, _ = env
    practice = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=practice, clock=CLOCK)
    burned = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    result = render_assessment_with_replacement(repo, candidates=[burned], clock=CLOCK)
    assert isinstance(result, RenderRefused)
    assert result.reason == "exact_surface_collision"


# --- §9.5 line 7: concurrent renders expose at most once (regression guard) --

def test_two_concurrent_renders_expose_once(env):
    vault, repo, paths = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    results: list[Administration] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(2)

    def worker():
        try:
            local = Repository(paths.sqlite_path)
            barrier.wait()
            results.append(open_administration(local, resolved=resolved, reservation=reservation, clock=CLOCK))
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    rendered = [e for e in repo.exposures_for_surface(resolved.surface_id) if e["kind"] == "rendered"]
    assert len(rendered) == 1
    assert results[0].administration_id == results[1].administration_id


# --- §9.5 line 4: failed + feedback appends practice-successor proposal ------

def test_failed_with_feedback_appends_practice_successor_proposal(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, clock=CLOCK)
    before = repo.exposures_for_surface(resolved.surface_id)
    append_practice_successor_proposal(
        repo, surface_id=resolved.surface_id, administration_id=admin.administration_id,
        not_before="2026-08-01T00:00:00Z", clock=CLOCK,
    )
    lifecycle = repo.surface_lifecycle_history(resolved.surface_id)
    proposals = [e for e in lifecycle if e["kind"] == "practice_successor_minted"]
    assert len(proposals) == 1
    import json
    assert json.loads(proposals[0]["detail_json"])["stage"] == "proposal"
    # Purpose + burn state unchanged.
    with connect(repo.sqlite_path) as connection:
        purpose = connection.execute(
            "SELECT purpose FROM activity_administrations WHERE id = ?", (admin.administration_id,)
        ).fetchone()["purpose"]
    assert purpose == "assessment"
    assert repo.exposures_for_surface(resolved.surface_id) == before  # no new exposure


# --- §9.5 line 5: regrade never reverses burn ------------------------------

def test_regrade_never_reverses_burn(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, clock=CLOCK)
    exposures_before = repo.exposures_for_surface(resolved.surface_id)
    lifecycle_before = repo.surface_lifecycle_history(resolved.surface_id)
    # A regrade appends an interpretation-style measurement event; burn is untouched.
    repo.append_measurement_event(
        administration_id=admin.administration_id,
        kind="measurement_reinterpretation",
        algorithm_version="mvp-0.8",
        clock=CLOCK,
    )
    assert repo.exposures_for_surface(resolved.surface_id) == exposures_before
    assert repo.surface_lifecycle_history(resolved.surface_id) == lifecycle_before
    rendered = [e for e in exposures_before if e["kind"] == "rendered"]
    assert len(rendered) == 1


# --- support recheck at render marks unrepresentative (§4.5) ----------------

def test_render_marks_unrepresentative_when_head_support_moved(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    admin = open_administration(
        repo, resolved=resolved, reservation=reservation,
        target_support_hash="old_support", head_support_hash="new_support", clock=CLOCK,
    )
    with connect(repo.sqlite_path) as connection:
        row = connection.execute(
            "SELECT eligibility_json FROM activity_administrations WHERE id = ?",
            (admin.administration_id,),
        ).fetchone()
    import json
    assert json.loads(row["eligibility_json"])["support_representative"] is False


# --- drift detection (§3) ---------------------------------------------------

def test_detect_contract_drift_and_doctor_surface(env):
    vault, repo, paths = env
    goal_id = "goal_linear_algebra_ml"
    # Confirm a contract from the goal's current draft fields + one exemplar.
    goal = next(g for g in vault.goals if g.id == goal_id)
    body = {
        "purpose": goal.title,
        "due_at": goal.due_at,
        "target_recall": goal.target_recall,
        "facet_scope": goal.facet_scope.model_dump(),
        "exam": goal.exam.model_dump(),
        "required_capabilities": ["state_definition"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": "ex1", "surface_ref": "s1"}],
    }
    version = gc.confirm_goal_contract(repo, goal_id=goal_id, contract_body=body, vault=vault, clock=CLOCK)
    # Mirror was written to goals.yaml.
    data = read_yaml(paths.goals_path)
    mirrored = next(g for g in data["goals"] if g["id"] == goal_id)
    assert mirrored["confirmed_contract_head_id"] == version.id

    # No drift right after confirm.
    assert gc.detect_contract_drift(vault, repo, goal_id).drifted is False

    # Edit the YAML draft directly (target_recall) -> drift detected, not reconciled.
    for g in data["goals"]:
        if g["id"] == goal_id:
            g["target_recall"] = 0.95
    from learnloop.vault.yaml_io import write_yaml
    write_yaml(paths.goals_path, data)
    reloaded = load_vault(paths.root)
    report = gc.detect_contract_drift(reloaded, repo, goal_id)
    assert report.drifted is True
    assert "target_recall" in report.field_diff
    assert report.would_be_change_class == "evaluation_change"
    # Head is unchanged (consumers still pin the confirmed head).
    assert gc.resolve_head(repo, goal_id).id == version.id

    # doctor surfaces it.
    from learnloop.services.doctor import run_doctor
    doctor = run_doctor(paths.root)
    assert any(issue.code == "goal:contract_drift" for issue in doctor.issues)

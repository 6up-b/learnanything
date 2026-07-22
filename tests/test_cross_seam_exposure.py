"""P4 §14.2 step 3 -- cross-seam exposure integrity over the ONE ledger (design §A.3, §C
gate d + scope items 3/5).

Both controllers (staged + legacy) reserve exposure through the single
``activity_exposure_events`` ledger inside the P0 ``open_administration_atomic`` in-lock
recheck. These tests prove the seam: two controllers targeting the same surface / near
clone concurrently -> EXACTLY ONE wins, the loser DEFERS to the winner (not a second
exposure); assessment reserves are never poached by practice; and an adversarial STALE
ownership read still cannot produce a double administration (the ledger, not ownership,
is the last-line authority -- invariant 11).
"""

from __future__ import annotations

import threading

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import constraint_engine as ce
from learnloop.services import controller_cutover as cut
from learnloop.services import controller_snapshot as cs
from learnloop.services import staged_policy as sp
from learnloop.services.activities import (
    Administration,
    ExposureCollisionAtRender,
    open_administration,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _add_item(root, item_id, *, prompt="Prompt.", stimulus=None):
    payload = {
        "id": item_id, "learning_object_id": LO_ID, "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": prompt, "expected_answer": "Answer.",
        "grading_rubric": {"max_points": 4,
                           "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                           "fatal_errors": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }
    if stimulus is not None:
        payload["evidence_fingerprint"] = {"shared_stimulus_id": stimulus}
    upsert_practice_item(root, payload, clock=CLOCK)


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_a", prompt="Prompt A.")
    _add_item(root, "pi_stim_1", prompt="Stim one.", stimulus="stim1")
    _add_item(root, "pi_stim_2", prompt="Stim two.", stimulus="stim1")
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    return vault, repo, paths


def test_same_surface_exactly_one_wins_via_shared_ledger(env):
    """Two controllers, two connections, same surface, aligned at a barrier -> exactly
    one fresh administration; the loser DEFERS to the winner (same administration id).
    No surface goes fresh twice across the seam (invariant 11)."""

    vault, repo, paths = env
    resolved = resolve_legacy_item(vault, repo, vault.practice_items["pi_a"], purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)

    def probe():
        return cut.cross_seam_exposure_probe(
            lambda: Repository(paths.sqlite_path),
            open_administration=lambda r: open_administration(
                r, resolved=resolved, reservation=reservation, clock=CLOCK
            ),
        )

    report = probe()
    assert report["errors"] == [None, None]
    assert report["fresh_opens"] == 1  # exactly one wins
    assert report["deferred"] == 1     # the loser defers, not a second exposure
    rendered = [e for e in repo.exposures_for_surface(resolved.surface_id) if e["kind"] == "rendered"]
    assert len(rendered) == 1
    ids = {r.administration_id for r in report["results"]}
    assert len(ids) == 1  # both observe the one winning administration


def test_near_clone_collision_loser_is_refused_not_double_exposed(env):
    """A near-kin (shared-stimulus) surface already burned by one controller cannot be
    freshly administered by the other for assessment: the loser is refused (a typed
    defer/refuse), never a second fresh exposure."""

    vault, repo, _ = env
    first = resolve_legacy_item(vault, repo, vault.practice_items["pi_stim_1"], purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=first, clock=CLOCK)
    near = resolve_legacy_item(vault, repo, vault.practice_items["pi_stim_2"], purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=near.surface_id, purpose="assessment", clock=CLOCK)
    with pytest.raises(ExposureCollisionAtRender) as exc:
        open_administration(repo, resolved=near, reservation=reservation, clock=CLOCK)
    assert exc.value.reason in ("near_clone_collision", "exact_surface_collision")


def test_assessment_reserve_not_poached_by_practice_at_plan_time(env):
    """The constraint engine excludes an assessment-reserved surface from a non-assessment
    (practice) block -- so a practice controller never selects a surface an assessment
    reserve holds (design §A.3; §5 leakage rule)."""

    vault, repo, _ = env
    reserved_surface = "surf-reserved"
    candidate = cs.Candidate(candidate_ref="c1", surface_id=reserved_surface, purpose="practice")
    snapshot = cs.ControllerSnapshot(
        snapshot_hash="h", session_id="s", available_minutes=15, energy=None,
        remaining_minutes=15.0, conservative_duration_minutes=3.0, candidates=(candidate,),
        exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=frozenset({reserved_surface}), commitments=(),
        affect_by_commitment={}, param_manifest_hash="p", projection_versions={},
    )
    practice_block = sp.AttentionBlock(
        action="practice", subtype=None, commitment_id=None, budget_minutes=10.0,
        compatible_purposes=("practice",),
    )
    feas = ce.evaluate(candidate, snapshot, practice_block)
    assert not feas.eligible
    assert any(e.constraint_key == "assessment_reservation" for e in feas.exclusions)


def test_stale_ownership_still_prevents_double_administration(env):
    """Adversarial (scope item 5): actually FORCE a stale ownership read. Read the
    commitment's owner (snapshot it), then TRANSITION ownership underneath that read, then
    drive two administrations that each act on a DIFFERENT (divergent) ownership belief --
    the staged controller still holding the pre-transition 'I own it' snapshot and the
    legacy controller seeing the post-transition owner. Both believe they may administer
    the same surface. The ledger's atomic in-lock recheck STILL admits exactly one:
    ownership is an optimization, the ONE ledger is the last-line authority (invariant 11).

    Pre-rewrite this test never touched an ownership row -- it was a plain concurrency
    test that could not exhibit the stale-read hazard it claimed to cover.
    """

    from learnloop.services import commitments as C
    from learnloop.services import controller_ownership as own

    vault, repo, paths = env
    item = vault.practice_items["pi_a"]
    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="own pi_a",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item.id, "role": "required"}],
        depth_preset="master_tasks_like_these", goal_id="g1", clock=CLOCK,
    )
    own.assign_p2_run(repo, commitment_id=commitment.id, clock=CLOCK)

    # (1) The STALE ownership snapshot the staged controller pins for its decision.
    stale_owner = own.resolve_owner(repo, commitment.id)
    assert stale_owner == own.STAGED

    # (2) Transition ownership underneath that pinned read -> now legacy.
    own.rollback_to_legacy(repo, reason="stale_read_test", clock=CLOCK)
    assert own.resolve_owner(repo, commitment.id) == own.LEGACY  # the read is now stale.

    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)

    results: list[Administration] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(2)

    def worker(believed_owner: str):
        # (3) Each controller administers on its own (divergent) ownership belief: the
        # staged controller acts on the STALE 'staged' snapshot, the legacy controller on
        # the fresh 'legacy' owner. Neither excludes the surface, so both race to render.
        try:
            local = Repository(paths.sqlite_path)
            barrier.wait(timeout=5)
            results.append(open_administration(local, resolved=resolved, reservation=reservation, clock=CLOCK))
        except Exception as exc:  # pragma: no cover -- surfaced by the assert
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(stale_owner,)),
        threading.Thread(target=worker, args=(own.LEGACY,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # (4) The ledger admits exactly one despite the divergent/stale ownership beliefs.
    assert not errors, errors
    rendered = [e for e in repo.exposures_for_surface(resolved.surface_id) if e["kind"] == "rendered"]
    assert len(rendered) == 1  # no double administration despite the stale ownership read
    assert results[0].administration_id == results[1].administration_id

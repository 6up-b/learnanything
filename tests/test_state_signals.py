"""P4 §14.2 cutover -- live StateSignals adapters (scope item 1).

Each of the five named signals is derived DETERMINISTICALLY from real vault state and
asserted against planted states: misspecification (open-set alarm), robust value (open
in-progress diagnostic episode), target-acquired (reached milestone), retention-limit
(due boundary), terminal-reserve (live assessment reservation). Each fails safe when the
evidence is absent.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_snapshot as cs
from learnloop.services import state_signals as ss
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    r = Repository(paths.sqlite_path)
    sync_vault_state(vault, r, clock=CLOCK)
    return r


def _snapshot(*, candidates=(), commitments=(), reserved=frozenset()):
    return cs.ControllerSnapshot(
        snapshot_hash="h", session_id="s", available_minutes=15, energy=None,
        remaining_minutes=15.0, conservative_duration_minutes=3.0, candidates=tuple(candidates),
        exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=reserved, commitments=tuple(commitments),
        affect_by_commitment={}, param_manifest_hash="p", projection_versions={},
    )


def _commitment(cid="cm1", *, milestones=()):
    return cs.CommitmentSummary(
        commitment_id=cid, created_action="select_exemplar", disposition="active",
        depth_policy="auto_within_envelope", depth_policy_version_id="dp1",
        depth_envelope_version_id="de1", goal_id="g1",
        reached_milestones=tuple(milestones), reviewed_edges=(),
    )


# --- target_acquired -------------------------------------------------------------

def test_target_acquired_true_with_reached_milestone():
    snap = _snapshot(commitments=(_commitment(milestones=("m1",)),))
    assert ss.target_acquired(snap, "cm1") is True


def test_target_not_acquired_without_milestone():
    snap = _snapshot(commitments=(_commitment(milestones=()),))
    assert ss.target_acquired(snap, "cm1") is False


# --- retention_near_limit --------------------------------------------------------

def test_retention_near_limit_when_overdue():
    overdue = cs.Candidate(candidate_ref="c1", due_at="2026-01-01T00:00:00Z")
    assert ss.retention_near_limit(_snapshot(candidates=(overdue,)), clock=CLOCK) is True


def test_retention_not_near_limit_when_future_due():
    future = cs.Candidate(candidate_ref="c1", due_at="2027-01-01T00:00:00Z")
    assert ss.retention_near_limit(_snapshot(candidates=(future,)), clock=CLOCK) is False


# --- terminal reserve ------------------------------------------------------------

def test_terminal_reserve_valid_when_reservation_present(repo):
    snap = _snapshot(reserved=frozenset({"surface-1"}))
    required, valid = ss.terminal_signals(repo, snap, "cm1", run_mode="certifying", terminal_shown=False)
    assert required is True and valid is True


def test_practice_only_run_never_requires_terminal(repo):
    snap = _snapshot(reserved=frozenset({"surface-1"}))
    required, valid = ss.terminal_signals(repo, snap, "cm1", run_mode="practice_only")
    assert required is False and valid is True


def test_terminal_reserve_invalid_without_reservation(repo):
    snap = _snapshot(reserved=frozenset())
    _required, valid = ss.terminal_signals(repo, snap, "cm1", run_mode="certifying")
    assert valid is False


# --- misspecification (open-set alarm) ------------------------------------------

def test_misspecification_true_with_pending_generation_need(repo):
    lo = "lo_x"
    repo.upsert_probe_generation_need(
        probe_episode_id="ep1", learning_object_id=lo, target_key="t1",
        missing_capability="cap", clock=CLOCK,
    )
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id=lo),))
    assert ss.misspecification(repo, snap, "cm1") is True


def test_misspecification_false_when_no_alarm(repo):
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id="lo_y"),))
    assert ss.misspecification(repo, snap, "cm1") is False


def test_misspecification_false_when_alarm_resolved(repo):
    lo = "lo_z"
    need_id = repo.upsert_probe_generation_need(
        probe_episode_id="ep2", learning_object_id=lo, target_key="t1",
        missing_capability="cap", clock=CLOCK,
    )
    repo.resolve_probe_generation_need(need_id, clock=CLOCK)
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id=lo),))
    assert ss.misspecification(repo, snap, "cm1") is False


# --- commitment scoping (audit M3/D4) -------------------------------------------

def test_misspecification_scoped_to_commitment_head_targets(repo):
    # Audit M3/D4: an UNRELATED commitment's learning object (present in the candidate
    # universe during the cutover) must NOT fire misspecification for an owned run.
    # Pre-fix _commitment_learning_object_ids returned every candidate LO, so an alarm on
    # any candidate LO -- including one this commitment does not own -- fired the signal.
    from learnloop.services import commitments as C

    owned_lo = "lo_owned"
    unrelated_lo = "lo_unrelated"
    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="own this",
        targets=[{"target_kind": "learning_object", "target_ref": owned_lo, "role": "required"}],
        depth_preset="master_tasks_like_these", goal_id="g1", clock=CLOCK,
    )
    # Pending alarm ONLY on the unrelated LO.
    repo.upsert_probe_generation_need(
        probe_episode_id="epU", learning_object_id=unrelated_lo, target_key="t",
        missing_capability="cap", clock=CLOCK,
    )
    snap = _snapshot(candidates=(
        cs.Candidate(candidate_ref="c_own", learning_object_id=owned_lo),
        cs.Candidate(candidate_ref="c_unrelated", learning_object_id=unrelated_lo),
    ))
    assert ss.misspecification(repo, snap, commitment.id) is False

    # An alarm on the commitment's OWN head-target LO does fire.
    repo.upsert_probe_generation_need(
        probe_episode_id="epO", learning_object_id=owned_lo, target_key="t",
        missing_capability="cap", clock=CLOCK,
    )
    assert ss.misspecification(repo, snap, commitment.id) is True


# --- decision_relevant_robust_value (open in-progress diagnostic episode) --------

def test_robust_value_positive_with_in_progress_episode(repo):
    lo = "lo_probe"
    repo.insert_probe_episode(
        learning_object_id=lo, status="in_progress", trigger="initial",
        hypothesis_set_id=None, active_state_segment_id=None, algorithm_version="v1",
        clock=CLOCK,
    )
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id=lo),))
    assert ss.decision_relevant_robust_value(repo, snap, "cm1") == ss.OPEN_EPISODE_ROBUST_VALUE


def test_robust_value_zero_without_open_episode(repo):
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id="lo_none"),))
    assert ss.decision_relevant_robust_value(repo, snap, "cm1") == 0.0


def test_pending_items_episode_is_not_measurement_value(repo):
    lo = "lo_pending"
    repo.insert_probe_episode(
        learning_object_id=lo, status="pending_items", trigger="initial",
        hypothesis_set_id=None, active_state_segment_id=None, algorithm_version="v1",
        clock=CLOCK,
    )
    snap = _snapshot(candidates=(cs.Candidate(candidate_ref="c1", learning_object_id=lo),))
    assert ss.decision_relevant_robust_value(repo, snap, "cm1") == 0.0


# --- aggregator ------------------------------------------------------------------

def test_derive_signals_composes_all_five(repo):
    lo = "lo_all"
    repo.upsert_probe_generation_need(
        probe_episode_id="epA", learning_object_id=lo, target_key="t", missing_capability="c",
        clock=CLOCK,
    )
    snap = _snapshot(
        candidates=(cs.Candidate(candidate_ref="c1", learning_object_id=lo,
                                 due_at="2026-01-01T00:00:00Z"),),
        commitments=(_commitment(milestones=("m1",)),),
        reserved=frozenset({"surface-1"}),
    )
    signals = ss.derive_signals(repo, snap, commitment_id="cm1", run_mode="certifying", clock=CLOCK)
    assert signals.model_misspecified is True
    assert signals.target_acquired is True
    assert signals.retention_near_limit is True
    assert signals.terminal_reserve_valid is True
    assert signals.terminal_required_unshown is True

"""P4 step 4 -- the single randomization layer (spec_p4 §9.3, U-024, §16.4).

Covers: randomization is inert unless genuinely near-equivalent (the ε margin); every
draw logs seed + true propensity BEFORE selection; MRT only on reversible candidates;
commitment-level parallel randomization for durable interventions; hypothesis-grade
labelling for unmodeled carryover; outcome windows anchored to the next spaced cold
review; the dormant propensity floor bind-logs when it binds.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_store as store
from learnloop.services import randomization_layer as RL

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


def _repo(tmp_path):
    return Repository(tmp_path / "state.sqlite")


def test_epsilon_tiebreak_is_inert_when_not_near_equivalent(tmp_path):
    repo = _repo(tmp_path)
    a = RL.epsilon_tiebreak(repo, experiment_id="e1", refs=["x", "y"], values=[1.0, 0.2],
                            seed="s", clock=CLOCK)
    assert a.randomized is False
    assert a.variant == "x"  # deterministic top
    assert a.propensity == 1.0
    # No assignment persisted for an inert (non-tie) decision.
    assert store.assignments_for_experiment(repo, "e1") == []


def test_epsilon_tiebreak_randomizes_near_equivalents_with_logged_propensity(tmp_path):
    repo = _repo(tmp_path)
    a = RL.epsilon_tiebreak(repo, experiment_id="e2", refs=["x", "y"], values=[1.0, 0.99],
                            seed="s", clock=CLOCK)
    assert a.randomized is True
    assert a.near_equivalent is True
    assert a.variant in ("x", "y")
    assert 0.0 < a.propensity <= 1.0
    rows = store.assignments_for_experiment(repo, "e2")
    assert len(rows) == 1
    # Propensity + seed + design are persisted (before-selection join validity, §9.3).
    assert rows[0]["propensity"] == a.propensity
    assert rows[0]["seed"] == "s"
    assert rows[0]["design"] == "epsilon_tiebreak"
    assert rows[0]["near_equivalent"] == 1


def test_epsilon_tiebreak_is_deterministic_for_a_seed(tmp_path):
    a = RL.epsilon_tiebreak(None, experiment_id="e", refs=["x", "y"], values=[1.0, 0.99], seed="fixed")
    b = RL.epsilon_tiebreak(None, experiment_id="e", refs=["x", "y"], values=[1.0, 0.99], seed="fixed")
    assert a.variant == b.variant and a.draw == b.draw


def test_micro_randomize_only_on_reversible(tmp_path):
    repo = _repo(tmp_path)
    ok = RL.micro_randomize(repo, experiment_id="mrt", variants=["v1", "v2"], seed="s",
                            reversible=True, clock=CLOCK)
    assert ok.randomized is True and ok.grade == "experimental"
    assert len(store.assignments_for_experiment(repo, "mrt")) == 1

    bad = RL.micro_randomize(repo, experiment_id="mrt2", variants=["v1", "v2"], seed="s",
                             reversible=False, clock=CLOCK)
    assert bad.randomized is False and bad.grade == "hypothesis_grade"
    assert store.assignments_for_experiment(repo, "mrt2") == []


def test_commitment_parallel_grade_depends_on_carryover_model(tmp_path):
    repo = _repo(tmp_path)
    modeled = RL.commitment_parallel_assign(
        repo, experiment_id="cp1", commitment_id="cm1", variants=["A", "B"], seed="s",
        carryover_modeled=True, clock=CLOCK)
    assert modeled.grade == "experimental" and modeled.unit_kind == "commitment"

    unmodeled = RL.commitment_parallel_assign(
        repo, experiment_id="cp2", commitment_id="cm2", variants=["A", "B"], seed="s",
        carryover_modeled=False, clock=CLOCK)
    assert unmodeled.grade == "hypothesis_grade"


def test_grade_for_enforcement():
    assert RL.grade_for(reversible=True, commitment_unit=False, carryover_modeled=False) == "experimental"
    assert RL.grade_for(reversible=False, commitment_unit=True, carryover_modeled=True) == "experimental"
    # Fits neither reversible-MRT nor commitment-parallel-with-carryover -> hypothesis-grade.
    assert RL.grade_for(reversible=False, commitment_unit=False, carryover_modeled=False) == "hypothesis_grade"
    assert RL.grade_for(reversible=False, commitment_unit=True, carryover_modeled=False) == "hypothesis_grade"


def test_outcome_window_anchored_to_next_spaced_cold_review(tmp_path):
    repo = _repo(tmp_path)
    unmodeled = RL.commitment_parallel_assign(
        repo, experiment_id="cp3", commitment_id="cm3", variants=["A", "B"], seed="s",
        carryover_modeled=False, clock=CLOCK)
    window_id = RL.open_outcome_window(
        repo, decision_id=None, assignment=unmodeled, card_ref="card1",
        commitment_id="cm3", next_spaced_cold_review_at="2026-06-01T00:00:00Z", clock=CLOCK)
    row = store.outcome_window_row(repo, window_id)
    assert row["horizon_kind"] == "next_spaced_cold_review"
    assert row["due_at"] == "2026-06-01T00:00:00Z"
    assert row["status"] == "pending"
    # An unmodeled-carryover assignment stamps the window hypothesis-grade.
    assert row["hypothesis_grade"] == 1

    store.resolve_outcome_window(repo, window_id, outcome={"cold_review": "recalled"}, clock=CLOCK)
    resolved = store.outcome_window_row(repo, window_id)
    assert resolved["status"] == "resolved"


def test_propensity_floor_binds_and_is_logged(tmp_path):
    repo = _repo(tmp_path)
    # Many variants -> uniform propensity below the floor -> bind-logged + clamped.
    variants = [f"v{i}" for i in range(50)]
    a = RL.micro_randomize(repo, experiment_id="floor", variants=variants, seed="s",
                           reversible=True, clock=CLOCK)
    assert a.propensity == RL.PROPENSITY_FLOOR
    events = repo.parameter_bind_events_for_path("randomization_layer:PROPENSITY_FLOOR")
    assert len(events) >= 1


def test_is_near_equivalent_margin():
    assert RL.is_near_equivalent([1.0, 0.98], margin=0.05) is True
    assert RL.is_near_equivalent([1.0, 0.5], margin=0.05) is False
    assert RL.is_near_equivalent([1.0], margin=0.05) is False

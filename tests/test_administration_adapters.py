"""P1 step 5 -- purpose-specific administration adapters (§3.10, §9.4, §9.2, rule 4)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import administration_adapters as AA
from learnloop.services import card_lineage as CL
from learnloop.services import activities as A
from learnloop.services.fsrs import Rating

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
SCHED = "fsrs6"


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _administration(repo, purpose):
    """A real P0 administration row under a family of the given purpose."""

    family_id = repo.ensure_activity_family(purpose=purpose, legacy_kind=None, title=purpose, clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval"}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    surface = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{purpose}", fingerprint=None,
        surface_json="{}", clock=CLOCK,
    )
    result = repo.open_administration_atomic(
        reservation_id=None, surface_id=surface, card_version_id=cv, family_id=family_id,
        purpose=purpose, surface_hash=f"sh-{purpose}", fingerprint=None,
        snapshot_hash=f"snap-{purpose}", snapshot_json="{}", consumes_unseen=False,
        algorithm_version=SCHED, clock=CLOCK,
    )
    admin_id = result["administration"]["id"]
    return family_id, card_id, cv, admin_id


# --- §9.4 purpose matrix: same response, four purposes, exact deltas ----------

def test_purpose_matrix_effects(repo):
    expected = {
        "diagnostic": dict(updates_practice_schedule=False, applies_fsrs_review=False,
                           evidence_class="frozen_episode_only", mints_unassisted_certification=False,
                           lifecycle_after_render="consumed_forever_for_diagnosis"),
        "instructional": dict(updates_practice_schedule=False, applies_fsrs_review=False,
                              evidence_class="no_unassisted_certification", mints_unassisted_certification=False,
                              lifecycle_after_render="reusable_per_policy"),
        "practice": dict(updates_practice_schedule=True, applies_fsrs_review=True,
                         evidence_class="practice_weighted", mints_unassisted_certification=False,
                         lifecycle_after_render="reusable_rotate_lazily"),
        "assessment": dict(updates_practice_schedule=False, applies_fsrs_review=False,
                           evidence_class="terminal_certification_only", mints_unassisted_certification=True,
                           lifecycle_after_render="p0_assessment_burn"),
    }
    for purpose, exp in expected.items():
        eff = AA.resolve_adapter(purpose).effects(eligible=True, failed=False)
        # Familiarity is full exposure under every purpose (§3.10 last column).
        assert eff.records_full_exposure is True
        for key, value in exp.items():
            assert getattr(eff, key) == value, (purpose, key)


def test_only_practice_eligible_updates_card_state(repo):
    review = {"rating": Rating.GOOD, "elapsed_days": 0.0}
    for purpose in AA.PURPOSES:
        family_id, card_id, cv, admin_id = _administration(repo, purpose)
        lineage_id = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=family_id, card_id=card_id, clock=CLOCK)
        result = AA.project_administration(
            repo, administration_id=admin_id, eligible=True, failed=False,
            card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED, review_event=review, clock=CLOCK,
        )
        state = repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED)
        if purpose == "practice":
            assert result.card_state is not None and state is not None
        else:
            assert result.card_state is None and state is None


def test_ineligible_practice_observation_leaves_card_state_untouched(repo):
    family_id, card_id, cv, admin_id = _administration(repo, "practice")
    lineage_id = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=family_id, card_id=card_id, clock=CLOCK)
    result = AA.project_administration(
        repo, administration_id=admin_id, eligible=False, failed=False,
        card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, clock=CLOCK,
    )
    assert result.card_state is None
    assert repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED) is None
    assert result.effects.applies_fsrs_review is False


# --- invariant 8: no opportunistic diagnosis ---------------------------------

def test_diagnostic_episode_requires_committed_presentation():
    adapter = AA.resolve_adapter("diagnostic")
    with pytest.raises(AA.OpportunisticDiagnosisRejected):
        adapter.update_episode(committed_episode_id=None)
    assert adapter.update_episode(committed_episode_id="ep-1") == "ep-1"


def test_practice_effects_never_touch_a_probe_episode(repo):
    # A practice adapter produces no frozen-episode evidence -- a cold practice
    # response cannot update an open probe episode (invariant 8, §9.4).
    eff = AA.resolve_adapter("practice").effects(eligible=True, failed=True)
    assert eff.evidence_class != "frozen_episode_only"


def test_practice_failure_opens_lapse_flag_but_instruction_never_does():
    assert AA.resolve_adapter("practice").effects(eligible=True, failed=True).opens_lapse_on_failure is True
    assert AA.resolve_adapter("instructional").effects(eligible=True, failed=True).opens_lapse_on_failure is False


def test_purpose_mismatch_rejected():
    with pytest.raises(AA.PurposeMismatch):
        AA.resolve_adapter("reading")


# --- §7.5 fail-safe: projection error never raises into the writer ------------

def test_project_administration_is_fail_safe_on_missing_administration(repo):
    result = AA.project_administration(
        repo, administration_id="does-not-exist", eligible=True, failed=False,
        card_lineage_id="x", scheduler_algorithm_version=SCHED,
    )
    assert result.deferred is True
    assert result.card_state is None


# --- version-gate: OFF keeps the hot path byte-identical (characterization) ----

def test_hot_path_gate_default_off_is_unconditional():
    assert AA.P1_PURPOSE_ADAPTERS_ENABLED is False
    # OFF -> always apply the review (byte-identical legacy behavior).
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt") is True
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", eligible=False) is True


def test_hot_path_gate_on_defers_to_practice_eligibility(monkeypatch):
    monkeypatch.setattr(AA, "P1_PURPOSE_ADAPTERS_ENABLED", True)
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", eligible=True) is True
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", eligible=False) is False

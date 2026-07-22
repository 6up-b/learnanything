"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change."""

from __future__ import annotations

import inspect

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.probe_episodes import (
    _bayes_update,
    _observation_likelihoods_from_row,
)
from learnloop.services.probe_families import (
    CompiledInstrument,
    instrument_observation_likelihoods,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def _vault_with_attempt(tmp_path):
    """A basic vault plus one real practice_attempt, returning (repository,
    attempt_id) so a probe_observation can satisfy its attempt FK."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="answer",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(NOW),
    )
    return repository, result.attempt_id


def _mirror_instrument() -> CompiledInstrument:
    # Prior rows (0.9375 / 0.0625) chosen so that after the fixed r=0.90
    # microprobe channel the composed conditionals are the clean 0.85 / 0.15.
    return CompiledInstrument(
        outcome_alphabet=("correct", "incorrect"),
        rows={
            "mastered": {"correct": 0.9375, "incorrect": 0.0625},
            "not_mastered": {"correct": 0.0625, "incorrect": 0.9375},
        },
        pseudo_count=8.0,
        grader_policy="diagnostic_microprobe_v1",
        provenance="instrument_card",
        family_template_id="fam_char",
        family_template_version=1,
        card_id="card_char",
        card_version=1,
    )


# --- Exact posterior-update math for a simple constructed case ----------------


def test_exact_posterior_update_for_uniform_prior():
    instrument = _mirror_instrument()
    slot_map = {"mastered": "mastered", "not_mastered": "not_mastered"}
    likelihoods = instrument_observation_likelihoods(instrument, slot_map, "correct")
    # Composed conditionals for observed `correct`: 0.85 / 0.15.
    assert likelihoods == {
        "mastered": pytest.approx(0.85),
        "not_mastered": pytest.approx(0.15),
    }
    prior = {"mastered": 0.5, "not_mastered": 0.5}
    posterior = _bayes_update(prior, likelihoods)
    # 0.5*0.85 = 0.425, 0.5*0.15 = 0.075, total 0.5 -> 0.85 / 0.15.
    assert posterior == {
        "mastered": pytest.approx(0.85),
        "not_mastered": pytest.approx(0.15),
    }


def test_exact_posterior_update_with_weight_damping():
    # Weighted step: L_w = w*L + (1-w)*marginal, no update at w=0.
    instrument = _mirror_instrument()
    slot_map = {"mastered": "mastered", "not_mastered": "not_mastered"}
    likelihoods = instrument_observation_likelihoods(instrument, slot_map, "correct")
    prior = {"mastered": 0.5, "not_mastered": 0.5}

    # marginal = 0.5*0.85 + 0.5*0.15 = 0.5
    # damped mastered L = 0.5*0.85 + 0.5*0.5 = 0.675
    # damped not L = 0.5*0.15 + 0.5*0.5 = 0.325
    # posterior mastered = 0.5*0.675 / (0.5*0.675 + 0.5*0.325) = 0.675
    damped = _bayes_update(prior, likelihoods, weight=0.5, prior_for_marginal=prior)
    assert damped["mastered"] == pytest.approx(0.675)
    assert damped["not_mastered"] == pytest.approx(0.325)

    # w = 0 leaves the posterior untouched.
    no_update = _bayes_update(prior, likelihoods, weight=0.0, prior_for_marginal=prior)
    assert no_update == {
        "mastered": pytest.approx(0.5),
        "not_mastered": pytest.approx(0.5),
    }


# --- grader_confidence does NOT influence the composed likelihood -------------


def test_composition_and_update_signatures_omit_grader_confidence():
    # The likelihood-composition and Bayes-update functions take no
    # grader_confidence parameter: the attempt's persisted confidence cannot
    # enter the posterior update through them.
    for func in (instrument_observation_likelihoods, _bayes_update):
        params = set(inspect.signature(func).parameters)
        assert "grader_confidence" not in params
    # Replay from a persisted observation row likewise ignores grader_confidence.
    assert "grader_confidence" not in set(
        inspect.signature(_observation_likelihoods_from_row).parameters
    )


def test_posterior_delta_identical_across_grader_confidence_values():
    # Two otherwise-identical submissions differing only in the persisted
    # grader_confidence produce IDENTICAL posterior deltas, because the composed
    # likelihood is a pure function of (instrument snapshot, slot_map, outcome)
    # and grader_confidence is never read into it.
    instrument = _mirror_instrument()
    slot_map = {"mastered": "mastered", "not_mastered": "not_mastered"}
    prior = {"mastered": 0.5, "not_mastered": 0.5}

    def posterior_for(grader_confidence: float) -> dict[str, float]:
        # grader_confidence is deliberately unused by the real pipeline; it is
        # carried here only to mirror an attribute persisted on the attempt.
        _ = grader_confidence
        outcome = "correct"
        likelihoods = instrument_observation_likelihoods(instrument, slot_map, outcome)
        return _bayes_update(prior, likelihoods)

    low_conf = posterior_for(0.10)
    high_conf = posterior_for(0.99)
    assert low_conf == high_conf
    assert low_conf["mastered"] == pytest.approx(0.85)


# --- Recorded observation stores policy/source/outcome, not the matrix --------


def test_recorded_grader_channel_stores_policy_source_outcome_only(tmp_path):
    # The exact grader_channel dict the submission path persists (§5.1):
    # grader_policy + grading_source + observed_outcome. No resolved confusion
    # matrix and no calibration model version are stored on the observation.
    repository, attempt_id = _vault_with_attempt(tmp_path)
    grader_channel = {
        "grader_policy": "diagnostic_microprobe_v1",
        "grading_source": "ai",
        "observed_outcome": "correct",
    }
    repository.insert_probe_observation(
        attempt_id=attempt_id,
        posterior_before={"mastered": 0.5, "not_mastered": 0.5},
        posterior_after={"mastered": 0.85, "not_mastered": 0.15},
        entropy_before=0.6931471805599453,
        entropy_after=0.4227414932452944,
        realized_information_gain=0.27040568731465086,
        independent_evidence_discount=1.0,
        grader_channel=grader_channel,
        updates_belief=True,
        eligible_for_completion=True,
    )
    record = repository.probe_observation_for_attempt(attempt_id)
    assert record is not None
    stored = record.grader_channel
    assert stored is not None

    # Exactly these three keys, nothing else.
    assert set(stored) == {"grader_policy", "grading_source", "observed_outcome"}
    assert stored["grader_policy"] == "diagnostic_microprobe_v1"
    assert stored["grading_source"] == "ai"
    assert stored["observed_outcome"] == "correct"

    # No resolved confusion matrix / calibration model version / reliability /
    # grader_confidence is persisted on the observation.
    for absent in (
        "confusion_matrix",
        "channel_matrix",
        "matrix",
        "rows",
        "calibration_model_version",
        "calibration_version",
        "reliability",
        "grader_confidence",
    ):
        assert absent not in stored


def test_stored_observation_carries_only_policy_so_matrix_is_recomputed(tmp_path):
    # Because only the grader_policy string is persisted, replay must
    # reconstruct the confusion channel fresh from the policy's fixed
    # reliability. Pin that the stored channel identifies the policy but does
    # not embed any per-outcome probabilities.
    repository, attempt_id = _vault_with_attempt(tmp_path)
    repository.insert_probe_observation(
        attempt_id=attempt_id,
        posterior_before={"mastered": 0.5, "not_mastered": 0.5},
        posterior_after={"mastered": 0.15, "not_mastered": 0.85},
        entropy_before=0.6931471805599453,
        entropy_after=0.4227414932452944,
        realized_information_gain=0.27040568731465086,
        independent_evidence_discount=1.0,
        grader_channel={
            "grader_policy": "diagnostic_longform_v1",
            "grading_source": "codex",
            "observed_outcome": "incorrect",
        },
        updates_belief=True,
        eligible_for_completion=True,
    )
    record = repository.probe_observation_for_attempt(attempt_id)
    assert record is not None
    stored = record.grader_channel
    assert stored is not None
    # The stored channel is a policy pointer, not numeric probabilities.
    assert stored["grader_policy"] == "diagnostic_longform_v1"
    assert all(not isinstance(value, (list, dict)) for value in stored.values())

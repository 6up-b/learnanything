from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probes import (
    Hypothesis,
    HypothesisSet,
    _apply_observation,
    _observation_likelihoods,
    build_hypothesis_set,
    current_hypothesis_set,
    enter_probe,
    persist_probe_beliefs,
    probe_posterior,
    record_probe_attempt,
    score_bucket,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem, Rubric, RubricFatalError

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _insert_misconception_error(repository: Repository) -> None:
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def _attempt(repository, loaded, *, points: int, fatal: list[str] | None = None, attempt_type="independent_attempt"):
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="answer",
            attempt_type=attempt_type,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4, fatal_errors=fatal),
        clock=FrozenClock(NOW),
    )


def test_score_bucket_boundaries():
    assert [score_bucket(s) for s in range(5)] == ["low", "low", "mid", "mid", "high"]


# --- Bug A: hypothesis posterior is updated and persisted -----------------


def test_low_score_with_misconception_shifts_posterior_and_persists_belief(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_misconception_error(repository)
    loaded = load_vault(vault_root)

    prior = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW)).prior
    prior_misconception = prior["misconception:conceptual_slip"]

    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    _attempt(repository, loaded, points=0, fatal=["conceptual_slip"])

    posterior = probe_posterior(loaded, repository, "lo_svd_definition")
    assert posterior is not None
    # A low score carrying the fatal error rules out `mastered` (a capable-no-error
    # learner cannot trigger a fatal error) and confirms the misconception: under the
    # corrected §5.1 model the probing item caps the misconception learner low and
    # attributes the score to E, so (low, E) is its diagnostic outcome.
    assert posterior.posterior["mastered"] == pytest.approx(0.0)
    assert posterior.posterior["misconception:conceptual_slip"] > prior_misconception
    assert max(posterior.posterior, key=posterior.posterior.get) == "misconception:conceptual_slip"

    # The misconception belief is persisted with the posterior marginal (Bug A).
    # The live pipeline routes new evidence through diagnostic episodes now, so
    # the frozen legacy persistence step is exercised directly.
    persist_probe_beliefs(loaded, repository, "lo_svd_definition", posterior, clock=FrozenClock(NOW))
    beliefs = repository.state_beliefs(scope_type="misconception", scope_id="conceptual_slip")
    assert len(beliefs) == 1
    assert beliefs[0]["belief_key"] == "lo_svd_definition"
    assert beliefs[0]["mean"] == pytest.approx(posterior.posterior["misconception:conceptual_slip"])
    assert beliefs[0]["variance"] >= 0.0
    assert beliefs[0]["evidence_count"] == 1


def test_realized_information_gain_is_positive_for_informative_attempt(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    before = probe_posterior(loaded, repository, "lo_svd_definition")
    assert before is not None
    assert before.realized_information_gain == pytest.approx(0.0)  # no attempts yet

    _attempt(repository, loaded, points=4)  # high score -> strongly indicates mastered

    after = probe_posterior(loaded, repository, "lo_svd_definition")
    assert after is not None
    assert after.realized_information_gain > 0.0
    assert 0.0 < after.normalized_information_gain <= 1.0
    assert after.posterior["mastered"] > before.posterior["mastered"]


def test_no_misconception_writes_no_belief_rows_but_updates_base_posterior(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    _attempt(repository, loaded, points=4)

    # mastered/unfamiliar carry no error type, so nothing fits learner_state_beliefs.
    assert repository.state_beliefs() == []
    posterior = probe_posterior(loaded, repository, "lo_svd_definition")
    assert posterior.posterior["mastered"] > posterior.prior["mastered"]


def test_probe_posterior_is_idempotent(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_misconception_error(repository)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    _attempt(repository, loaded, points=0, fatal=["conceptual_slip"])

    first = probe_posterior(loaded, repository, "lo_svd_definition")
    second = probe_posterior(loaded, repository, "lo_svd_definition")
    assert first.posterior == second.posterior
    assert first.attempts == second.attempts


def test_probe_posterior_none_when_not_probing(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)

    assert probe_posterior(loaded, repository, "lo_svd_definition") is None
    assert current_hypothesis_set(loaded, repository, "lo_svd_definition") is None


def test_dont_know_outcome_does_not_break_posterior(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_misconception_error(repository)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    # dont_know -> rubric_score 0 (low bucket) + recall_failure error type that is
    # not in the locked hypothesis set; the observation falls back to the bucket.
    complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=3),
        clock=FrozenClock(NOW),
    )

    posterior = probe_posterior(loaded, repository, "lo_svd_definition")
    assert posterior is not None
    assert posterior.posterior["unfamiliar"] > posterior.prior["unfamiliar"]
    assert sum(posterior.posterior.values()) == pytest.approx(1.0)


# --- Bug B: convergence honors the attempt target -------------------------


def test_mid_scores_run_probe_to_target_not_one(tmp_path):
    # Frozen legacy replay semantics (Checkpoint 0): the live pipeline no longer
    # advances lo_probe_state, so the legacy advancement step is driven directly.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    _attempt(repository, loaded, points=2)
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert repository.probe_state("lo_svd_definition").status == "in_progress"
    _attempt(repository, loaded, points=2)
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert repository.probe_state("lo_svd_definition").status == "in_progress"
    _attempt(repository, loaded, points=2)
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    final = repository.probe_state("lo_svd_definition")
    assert final.probe_attempts_completed == 3
    assert final.status == "complete"


def test_decisive_high_score_converges_early_on_hypothesis_family(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    _attempt(repository, loaded, points=4)
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    state = repository.probe_state("lo_svd_definition")
    assert state.status == "complete"
    assert state.probe_attempts_completed == 1
    assert "hypothesis" in state.families_converged


def test_scheduler_eig_uses_live_posterior(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    entry = current_hypothesis_set(loaded, repository, "lo_svd_definition")
    assert entry.prior == pytest.approx({"mastered": 0.5, "unfamiliar": 0.5})

    _attempt(repository, loaded, points=2)  # one mid attempt, probe still in progress

    live = current_hypothesis_set(loaded, repository, "lo_svd_definition")
    assert live is not None
    # The live posterior has moved off the entry prior. The probe item is slightly
    # hard (difficulty 0.55 -> b=0.25), so under the difficulty-aware graded model a
    # mid score weakly favors `mastered` over `unfamiliar` (its mid marginal is
    # fatter), the opposite of the old flat-mass model.
    assert live.prior["mastered"] > 0.5
    assert live.prior != pytest.approx(entry.prior)


# --- Robustness of the observation likelihood ------------------------------


def _probe_item() -> PracticeItem:
    return PracticeItem(
        id="pi_probe",
        learning_object_id="lo_svd_definition",
        practice_mode="short_answer",
        prompt="probe?",
        expected_answer="x",
        grading_rubric=Rubric(
            max_points=4,
            criteria=[],
            fatal_errors=[RubricFatalError(id="conceptual_slip", description="d", max_grade=1)],
        ),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )


def _three_hypothesis_set() -> HypothesisSet:
    return HypothesisSet(
        learning_object_id="lo_svd_definition",
        hypotheses=[
            Hypothesis(label="mastered"),
            Hypothesis(label="unfamiliar"),
            Hypothesis(label="misconception:conceptual_slip", error_type="conceptual_slip"),
        ],
        prior={"mastered": 1 / 3, "unfamiliar": 1 / 3, "misconception:conceptual_slip": 1 / 3},
    )


def test_high_score_with_error_type_falls_back_to_bucket_marginal():
    # (high, E) has zero joint mass under every hypothesis; the update must fall
    # back to the score bucket rather than zeroing the whole posterior.
    hypothesis_set = _three_hypothesis_set()
    item = _probe_item()
    posterior = _apply_observation(
        hypothesis_set, item, item.grading_rubric, "high", "conceptual_slip", dict(hypothesis_set.prior)
    )
    assert sum(posterior.values()) == pytest.approx(1.0)
    assert posterior["mastered"] > posterior["unfamiliar"]  # high bucket favors mastered (0.75 vs 0.05)


def test_unknown_error_type_uses_bucket_marginal():
    hypothesis_set = _three_hypothesis_set()
    item = _probe_item()
    likelihoods = _observation_likelihoods(hypothesis_set, item, item.grading_rubric, "low", "never_seen_error")
    # Unknown error type -> each hypothesis scored by its "low" bucket marginal, all positive.
    assert all(value > 0.0 for value in likelihoods.values())

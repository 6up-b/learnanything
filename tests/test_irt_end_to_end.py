"""End-to-end IRT scenarios through the real attempt pipeline.

Exercises Bayesian surprise, probe-EIG/posterior convergence, latent mastery
updates, and FSRS scheduling together on items of differing authored difficulty,
to confirm the difficulty-aware channels cooperate as the spec intends.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probes import enter_probe, probe_posterior
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

EASY_DIFFICULTY = 0.05    # b ~ -2.25
HARD_DIFFICULTY = 0.95    # b ~ +2.25


def _add_item(vault_root, item_id: str, difficulty: float) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"{item_id} prompt",
            "expected_answer": "U Sigma V^T",
            "difficulty": difficulty,
            "difficulty_source": "llm_estimate",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "c"}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )


def _setup(tmp_path, *, prior_mean: float = 0.0):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_easy", EASY_DIFFICULTY)
    _add_item(vault_root, "pi_hard", HARD_DIFFICULTY)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", prior_mean, 1.0, 1, NOW_ISO, "mvp-0.1", NOW_ISO)
    )
    return load_vault(vault_root), repository


def _attempt(loaded, repository, item_id: str, points: int, *, clock=None):
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="answer"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=clock or FrozenClock(NOW),
    )


# --- Latent mastery: difficulty modulates the mean jump ----------------------


def test_hard_correct_raises_mastery_more_than_easy_correct(tmp_path):
    easy_vault, easy_repo = _setup(tmp_path / "a")
    hard_vault, hard_repo = _setup(tmp_path / "b")

    easy = _attempt(easy_vault, easy_repo, "pi_easy", 4)
    hard = _attempt(hard_vault, hard_repo, "pi_hard", 4)

    # Acing the hard item is far stronger evidence of ability than acing the easy one.
    assert hard.mastery_mean > easy.mastery_mean
    assert hard.mastery_trace.mu_step > easy.mastery_trace.mu_step
    # The trace exposes the difficulty that drove each update.
    assert hard.mastery_trace.difficulty_b > 2.0
    assert easy.mastery_trace.difficulty_b < -2.0


# --- Bayesian surprise: direction depends on difficulty ----------------------


def test_surprise_direction_is_difficulty_aware(tmp_path):
    loaded, repository = _setup(tmp_path)
    # Fresh prior (mu=0) each scenario via separate repos to avoid carryover.
    hv, hr = _setup(tmp_path / "hard_correct")
    ev, er = _setup(tmp_path / "easy_correct")
    ew_v, ew_r = _setup(tmp_path / "easy_wrong")

    hard_correct = _attempt(hv, hr, "pi_hard", 4)
    easy_correct = _attempt(ev, er, "pi_easy", 4)
    # 1/4 on a trivial item (expected to ace) is a genuine failure with rubric
    # coverage; a 0/4 self-grade carries no evidence coverage so it cannot surprise.
    easy_wrong = _attempt(ew_v, ew_r, "pi_easy", 1)

    assert hard_correct.surprise_direction == "positive"   # aced a brutal item
    assert easy_correct.surprise_direction == "none"        # expected -> unsurprising
    assert easy_wrong.surprise_direction == "negative"      # flunked a trivial item


def test_hard_correct_has_larger_predictive_surprise_than_easy_correct(tmp_path):
    hv, hr = _setup(tmp_path / "h")
    ev, er = _setup(tmp_path / "e")
    hard = _attempt(hv, hr, "pi_hard", 4)
    easy = _attempt(ev, er, "pi_easy", 4)
    assert hard.predictive_surprise > easy.predictive_surprise


# --- FSRS: surprise modulates the review interval ----------------------------


def test_fsrs_interval_factor_stretches_on_positive_surprise(tmp_path):
    hv, hr = _setup(tmp_path / "h")
    result = _attempt(hv, hr, "pi_hard", 4)
    surprise = hr.latest_attempt_surprise(result.attempt_id)
    # Positive surprise pushes the FSRS interval factor above 1 (review later).
    assert surprise["fsrs_interval_factor"] > 1.0


def test_fsrs_interval_factor_compresses_on_negative_surprise(tmp_path):
    ev, er = _setup(tmp_path / "e")
    result = _attempt(ev, er, "pi_easy", 1)  # flunked a trivial item -> negative
    assert result.surprise_direction == "negative"
    surprise = er.latest_attempt_surprise(result.attempt_id)
    # Negative surprise pulls the FSRS interval factor below 1 (review sooner).
    assert surprise["fsrs_interval_factor"] < 1.0


def test_fsrs_interval_factor_stays_within_configured_bounds(tmp_path):
    loaded, repository = _setup(tmp_path)
    cfg = loaded.config.scheduler.surprise
    result = _attempt(loaded, repository, "pi_hard", 4)
    factor = repository.latest_attempt_surprise(result.attempt_id)["fsrs_interval_factor"]
    assert cfg.f_min <= factor <= cfg.f_max


# --- Probe EIG / posterior: hard items discriminate, converge faster ---------


def test_decisive_hard_correct_concentrates_posterior_more_than_trivial(tmp_path):
    hv, hr = _setup(tmp_path / "hard")
    ev, er = _setup(tmp_path / "easy")
    enter_probe(hv, hr, "lo_svd_definition", clock=FrozenClock(NOW))
    enter_probe(ev, er, "lo_svd_definition", clock=FrozenClock(NOW))

    _attempt(hv, hr, "pi_hard", 4)
    _attempt(ev, er, "pi_easy", 4)

    hard_posterior = probe_posterior(hv, hr, "lo_svd_definition")
    easy_posterior = probe_posterior(ev, er, "lo_svd_definition")

    # A high score on a hard item is far more diagnostic of mastery, so the
    # hypothesis posterior concentrates more (converges faster) than on a trivial one.
    assert hard_posterior.top_probability > easy_posterior.top_probability
    assert hard_posterior.posterior["mastered"] > easy_posterior.posterior["mastered"]
    assert hard_posterior.realized_information_gain > easy_posterior.realized_information_gain


def test_hard_correct_completes_probe_on_hypothesis_convergence(tmp_path):
    hv, hr = _setup(tmp_path / "hard")
    enter_probe(hv, hr, "lo_svd_definition", clock=FrozenClock(NOW))
    _attempt(hv, hr, "pi_hard", 4)
    state = hr.probe_state("lo_svd_definition")
    # The decisive hard-correct should converge the hypothesis family in one shot.
    assert "hypothesis" in state.families_converged
    assert state.status == "complete"

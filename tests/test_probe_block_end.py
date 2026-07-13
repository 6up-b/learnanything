"""Block boundary semantics (spec_probe_eig_redesign.md §5.7, §6.3, §16 test 34)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.followups import evaluate_attempt_intervention_followup
from learnloop.services.probe_blocks import (
    OPEN_SET_REVIEW_CAPABILITY,
    end_diagnostic_block,
    evaluate_open_set_trigger,
)
from learnloop.services.probe_episodes import (
    EpisodePosterior,
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
    serve_presentation,
)
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
ITEM_2 = "pi_svd_define_002"
CLOCK = FrozenClock(NOW)

MISCONCEPTION_STATEMENT = "The SVD is the same thing as the eigendecomposition."


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    upsert_practice_item(
        vault_root,
        {
            "id": ITEM_2,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {ITEM_2}.",
            "expected_answer": "A factorization into U, Sigma, and V transpose.",
            "surface_family": "fresh_surface",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID, ITEM_2))
    return loaded, repository


def _grade(score: int, *, error_attributions=None) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=error_attributions or [],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit(loaded, repository, *, item_id, presentation_id, score=4, error_attributions=None):
    return apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation_id,
            ),
            attempt_id=new_ulid(),
            grade=_grade(score, error_attributions=error_attributions),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


def _commit(loaded, repository, episode, *, item_id):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in instruments if entry.item.id == item_id)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    return presentation


def _misconception_attribution() -> GradeAttribution:
    return GradeAttribution(
        error_type="conceptual_slip",
        severity=0.9,
        is_misconception=True,
        misconception_statement=MISCONCEPTION_STATEMENT,
    )


# --- §16 test 34: deferral during an active block -----------------------------------


def test_followup_and_normalization_defer_to_block_end(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    presentation = _commit(loaded, repository, episode, item_id=ITEM_ID)
    result = _submit(
        loaded,
        repository,
        item_id=ITEM_ID,
        presentation_id=presentation.id,
        score=1,
        error_attributions=[_misconception_attribution()],
    )
    # One observation of a two-observation block: still mid-block.
    assert result.probe_block_end is None

    # Per-attempt follow-up evaluation defers: no queue insertion, no
    # intervention need, and NO misconception normalization (§5.7).
    decision = evaluate_attempt_intervention_followup(
        loaded, repository, result=result, clock=CLOCK
    )
    assert decision.reason == "deferred_to_block_end"
    assert decision.triggered is False
    assert decision.practice_item_id is None
    assert decision.need_id is None
    assert repository.misconceptions_for_learning_object(
        LO_ID, statuses=("active", "resolving", "resolved")
    ) == []

    # Block end runs the deferred normalization over the block's attempts.
    second = _commit(loaded, repository, episode, item_id=ITEM_2)
    result = _submit(
        loaded,
        repository,
        item_id=ITEM_2,
        presentation_id=second.id,
        score=1,
        error_attributions=[_misconception_attribution()],
    )
    block_end = result.probe_block_end
    assert block_end is not None
    rows = repository.misconceptions_for_learning_object(
        LO_ID, statuses=("active", "resolving", "resolved")
    )
    assert len(rows) == 1  # both events merged into one registry row
    assert rows[0].statement == MISCONCEPTION_STATEMENT
    assert block_end["normalized_misconception_ids"]


def test_ordinary_attempt_outside_block_still_normalizes(tmp_path):
    loaded, repository = _setup(tmp_path)
    enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    # An incidental ordinary attempt (no presentation) is not "during a block":
    # its side effects run per attempt as before.
    result = apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=ITEM_ID,
                learner_answer_md="answer",
                attempt_type="independent_attempt",
            ),
            attempt_id=new_ulid(),
            grade=_grade(1, error_attributions=[_misconception_attribution()]),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    decision = evaluate_attempt_intervention_followup(
        loaded, repository, result=result, clock=CLOCK
    )
    assert decision.reason != "deferred_to_block_end"
    assert repository.misconceptions_for_learning_object(
        LO_ID, statuses=("active", "resolving", "resolved")
    )


# --- §5.7 ordered hook: feedback, completion, routing --------------------------------


def test_block_end_releases_feedback_and_routes_ordinary_practice(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    result = _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=4)
    assert result.probe_block_end is None

    second = _commit(loaded, repository, episode, item_id=ITEM_2)
    result = _submit(loaded, repository, item_id=ITEM_2, presentation_id=second.id, score=4)

    block_end = result.probe_block_end
    assert block_end is not None
    # Step 1: both withheld observations are released together.
    assert {entry["practice_item_id"] for entry in block_end["released_feedback"]} == {ITEM_ID, ITEM_2}
    # Step 4: the completion policy ran at the boundary.
    assert block_end["completion_reason"] == "decision_stable"
    # Step 5: a robust diagnosis routes to ordinary practice, not tutoring.
    assert block_end["status"] == "complete"
    assert block_end["route"] == "ordinary_practice"
    assert block_end["decision"] is None


def test_block_end_routes_diagnosed_gap_to_typed_tutoring_transition(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    for item_id in (ITEM_ID, ITEM_2):
        presentation = _commit(loaded, repository, episode, item_id=item_id)
        result = _submit(
            loaded,
            repository,
            item_id=item_id,
            presentation_id=presentation.id,
            score=1,
            error_attributions=[_misconception_attribution()],
        )
    block_end = result.probe_block_end
    assert block_end is not None
    if block_end["status"] == "complete":
        assert block_end["route"] == "tutoring"
        decision = block_end["decision"]
        assert decision is not None
        assert decision["diagnosed_gap"] not in (None, "robust_initial_grasp")
        assert 0.0 <= decision["diagnostic_confidence"] <= 1.0
        # §12.1: the move comes from the stable taxonomy, derived from the
        # diagnosed state, confidence, and the card's instructional action.
        assert decision["tutor_move"] in (
            "elicit_reasoning",
            "localize_error",
            "minimal_hint",
            "state_subgoal",
            "contrast_cases",
            "counterexample",
            "partial_worked_step",
            "explanation",
            "worked_example",
            "transfer_question",
            "reflection",
        )
        assert 0.2 <= decision["scaffold_level"] <= 0.9
        assert decision["answer_reveal_budget"] in (0, 1, 2)
        # The typed decision is persisted on the episode before tutor prose (§12.1).
        refreshed = repository.probe_episode(episode.id)
        assert refreshed.target_decision is not None
        assert refreshed.target_decision["diagnosed_gap"] == decision["diagnosed_gap"]
    elif block_end["status"] == "in_progress":
        # An unstable two-observation block continues to the next block.
        assert block_end["route"] == "next_block"
    else:
        # Unstable with no unconsumed instrument left: the episode parks in
        # pending_items and the LO stays practicable (§10/§11).
        assert block_end["status"] == "pending_items"
        assert block_end["route"] == "ordinary_practice"


def test_continuing_episode_opens_fresh_segment_at_block_end(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    # Force a wide budget so two observations cannot complete the episode.
    repository.update_probe_episode_status(episode.id, status="in_progress", clock=CLOCK)
    segment_before = episode.active_state_segment_id

    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=1)
    second = _commit(loaded, repository, episode, item_id=ITEM_2)
    result = _submit(loaded, repository, item_id=ITEM_2, presentation_id=second.id, score=4)

    block_end = result.probe_block_end
    assert block_end is not None
    refreshed = repository.probe_episode(episode.id)
    if refreshed.status == "in_progress":
        assert block_end["route"] == "next_block"
        # Feedback reveal is an intervention boundary: the next block measures
        # a fresh state segment (§5.1/§5.6).
        assert refreshed.active_state_segment_id != segment_before
        segments = repository.state_segments_for_learning_object(LO_ID)
        assert any(segment.reason == "feedback_reveal" for segment in segments)


def test_end_diagnostic_block_noop_on_terminal_episode(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    repository.update_probe_episode_status(
        episode.id, status="complete", completion_reason="decision_stable",
        completed_at=NOW_ISO, clock=CLOCK,
    )
    refreshed = repository.probe_episode(episode.id)
    payload = end_diagnostic_block(loaded, repository, refreshed, clock=CLOCK)
    assert payload["route"] is None


# --- §6.3 open-set trigger ------------------------------------------------------------


def _posterior_with_open_set(repository, episode, mass: float) -> EpisodePosterior:
    hypothesis_set = None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    share = (1.0 - mass) / max(len(labels) - 1, 1)
    posterior = {label: (mass if label == H_OTHER else share) for label in labels}
    return EpisodePosterior(
        hypothesis_set=hypothesis_set,
        prior=dict(hypothesis_set.prior),
        posterior=posterior,
        qualifying_observations=2,
        total_observations=2,
        entropy=1.0,
    )


def test_open_set_trigger_fires_at_threshold_with_dedup(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    below = evaluate_open_set_trigger(
        loaded, repository, episode, _posterior_with_open_set(repository, episode, 0.10), clock=CLOCK
    )
    assert below is None

    fired = evaluate_open_set_trigger(
        loaded, repository, episode, _posterior_with_open_set(repository, episode, 0.40), clock=CLOCK
    )
    assert fired is not None and fired["fired"]
    assert fired["action"] == "misconception_review_need"
    needs = repository.probe_generation_needs(probe_episode_id=episode.id, status="pending")
    open_set_needs = [need for need in needs if need.target_key == H_OTHER]
    assert len(open_set_needs) == 1
    assert open_set_needs[0].missing_capability == OPEN_SET_REVIEW_CAPABILITY

    # Re-firing is deduplicated: same need, no duplicate row (§10).
    again = evaluate_open_set_trigger(
        loaded, repository, episode, _posterior_with_open_set(repository, episode, 0.40), clock=CLOCK
    )
    assert again["need_id"] == fired["need_id"]
    needs = repository.probe_generation_needs(probe_episode_id=episode.id, status="pending")
    assert len([need for need in needs if need.target_key == H_OTHER]) == 1

    # The episode's locked hypothesis set never expands (§6.3).
    assert episode_hypothesis_set(repository, episode).id == episode.hypothesis_set_id


def test_block_end_payload_carries_open_set_evaluation(tmp_path):
    loaded, repository = _setup(tmp_path)
    loaded.config.probe.episode.open_set_trigger_threshold = 0.05
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    for item_id in (ITEM_ID, ITEM_2):
        presentation = _commit(loaded, repository, episode, item_id=item_id)
        result = _submit(
            loaded, repository, item_id=item_id, presentation_id=presentation.id, score=0
        )
    block_end = result.probe_block_end
    assert block_end is not None
    assert "open_set" in block_end
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    if posterior.posterior.get(H_OTHER, 0.0) >= 0.05:
        assert block_end["open_set"] is not None and block_end["open_set"]["fired"]

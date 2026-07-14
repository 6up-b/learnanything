"""Diagnostic-episode integration tests (spec_probe_eig_redesign.md §16)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.ids import new_ulid
from learnloop.services.probe_episodes import (
    _resolved_slot_map_from_snapshot,
    commit_item_presentation,
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
    maybe_reprobe_for_misconception,
    next_probe_item,
    record_episode_evidence,
    serve_presentation,
    stop_diagnosing_and_teach,
)
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    CONTRAST_CONFUSABLE_V1,
    CardValidationError,
    InstrumentCard,
    PlantedTrial,
    ensure_builtin_families,
    instrument_expected_information_gain,
    map_episode_labels_to_slots,
    run_family_admission_gate,
    validate_and_compile_card,
)
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, with_card: bool = True, extra_item: bool = False):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if extra_item:
        _add_item(vault_root, "pi_svd_define_002", surface_family="fresh_surface")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    if with_card:
        items = (ITEM_ID, "pi_svd_define_002") if extra_item else (ITEM_ID,)
        admit_contrast_card(repository, items=items)
    return vault_root, loaded, repository


def _add_item(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "surface_family": surface_family,
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


def admit_contrast_card(
    repository: Repository,
    *,
    card_id: str = "card_svd_contrast",
    items: tuple[str, ...] = (ITEM_ID,),
    rows: dict | None = None,
) -> None:
    admit_probe_instrument_card(repository, card_id=card_id, items=items, rows=rows)


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


def _submit(
    loaded,
    repository,
    *,
    item_id: str = ITEM_ID,
    score: int = 4,
    attempt_type: str = "diagnostic_probe",
    hints_used: int = 0,
    presentation_id: str | None = None,
    grading_source: str = "ai",
    attempt_id: str | None = None,
    session_id: str | None = None,
    error_attributions=None,
    declared_dont_know: bool = False,
):
    attempt_id = attempt_id or new_ulid()
    result = apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type=attempt_type,
                hints_used=hints_used,
                session_id=session_id,
                probe_presentation_id=presentation_id,
                declared_dont_know=declared_dont_know,
            ),
            attempt_id=attempt_id,
            grade=_grade(score, error_attributions=error_attributions),
            grading_source=grading_source,
        ),
        clock=CLOCK,
    )
    return result


def _commit(loaded, repository, episode, *, item_id: str = ITEM_ID):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in instruments if entry.item.id == item_id)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    return presentation


# --- Entry, hypothesis set, unique identity (§5.2, §6, test 14) --------------------


def test_episode_entry_locks_actionable_set_with_open_set_mass(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    assert episode.status == "in_progress"
    hypothesis_set = episode_hypothesis_set(repository, episode)
    labels = {hypothesis.label for hypothesis in hypothesis_set.hypotheses}
    actionable = labels - {H_OTHER}
    assert len(actionable) >= 3
    assert H_OTHER in labels
    assert abs(sum(hypothesis_set.prior.values()) - 1.0) < 1e-9
    assert hypothesis_set.prior[H_OTHER] > 0
    assert episode.required_facets == ["recall"]

    # Re-entry is idempotent while open; a re-probe after completion mints a
    # fresh episode and hypothesis-set snapshot (§5.2, §6.5).
    assert enter_episode(loaded, repository, LO_ID, clock=CLOCK).id == episode.id


def test_new_misconception_triggers_unique_reprobe_episode(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    first = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    repository.update_probe_episode_status(
        first.id, status="complete", completion_reason="decision_stable", completed_at=NOW_ISO, clock=CLOCK
    )

    second = maybe_reprobe_for_misconception(loaded, repository, LO_ID, severity=0.9, clock=CLOCK)
    assert second is not None
    assert second.id != first.id
    assert second.trigger == "misconception"
    assert second.hypothesis_set_id != first.hypothesis_set_id

    assert maybe_reprobe_for_misconception(loaded, repository, LO_ID, severity=0.4, clock=CLOCK) is None


# --- Card validation (§9.3, tests 18/35) --------------------------------------------


def test_card_with_numeric_conditionals_is_rejected(tmp_path):
    rows = {
        slot: dict(row) for slot, row in CONTRAST_CONFUSABLE_DEFAULT_ROWS.items()
    }
    rows["unfamiliar"] = {**rows["unfamiliar"], "unanswered": 0.55}
    card = InstrumentCard(
        id="card_bad",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=rows,
    )
    try:
        validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
        raise AssertionError("numeric conditional was not rejected")
    except CardValidationError as exc:
        assert "numeric" in str(exc)


def test_card_with_incomplete_row_is_rejected(tmp_path):
    rows = {slot: dict(row) for slot, row in CONTRAST_CONFUSABLE_DEFAULT_ROWS.items()}
    rows["unfamiliar"].pop("unanswered")
    card = InstrumentCard(
        id="card_bad2",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=rows,
    )
    try:
        validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
        raise AssertionError("incomplete row was not rejected")
    except CardValidationError as exc:
        assert "incomplete" in str(exc)


def test_compiled_rows_carry_pseudo_counts_and_normalize(tmp_path):
    card = InstrumentCard(
        id="card_ok",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    )
    instrument = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    assert instrument.pseudo_count == 8.0
    for row in instrument.rows.values():
        assert abs(sum(row.values()) - 1.0) < 1e-9


# --- EIG semantics (§2.2/§7.2, tests 17/22) ------------------------------------------


def test_hypothesis_independent_item_receives_zero_eig(tmp_path):
    # Identical rows across hypotheses: ~50% marginal success, zero information.
    flat_row = {
        "correct_target_reason": "likely",
        "correct_weak_reason": "likely",
        "confusable_signature": "rare",
        "other_systematic_error": "rare",
        "hedge": "rare",
        "unanswered": "rare",
    }
    card = InstrumentCard(
        id="card_flat",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations={slot: flat_row for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots},
    )
    instrument = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    posterior = {slot: 1.0 / 5 for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots}
    slot_map = {slot: slot for slot in posterior}
    assert instrument_expected_information_gain(posterior, instrument, slot_map) < 1e-12


def test_lower_grader_reliability_lowers_eig(tmp_path):
    card = InstrumentCard(
        id="card_rel",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    )
    instrument = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    posterior = {slot: 1.0 / 5 for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots}
    slot_map = {slot: slot for slot in posterior}
    sharp = instrument_expected_information_gain(posterior, instrument, slot_map, grader_reliability=0.95)
    blunt = instrument_expected_information_gain(posterior, instrument, slot_map, grader_reliability=0.55)
    assert sharp > blunt > 0


# --- Advancement accounting (§5.3/§5.4, tests 3/4/5/6/7/8/11) ------------------------


def test_ordinary_and_hinted_attempts_never_advance_but_update_belief(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    prior = episode_posterior(loaded, repository, episode).posterior

    _submit(loaded, repository, attempt_type="independent_attempt", score=4, grading_source="ai")
    _submit(loaded, repository, attempt_type="hinted_attempt", score=4, hints_used=1, grading_source="ai")

    refreshed = repository.probe_episode(episode.id)
    assert refreshed.status == "in_progress"
    posterior = episode_posterior(loaded, repository, refreshed)
    assert posterior.qualifying_observations == 0
    assert posterior.total_observations == 0
    # Belief still moved: two successes shift mass toward capable hypotheses.
    assert posterior.posterior["unfamiliar"] < prior["unfamiliar"]


def test_exam_attempts_do_not_advance_probe(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    _submit(loaded, repository, attempt_type="exam_attempt", score=4, grading_source="ai")
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 0
    assert repository.probe_episode(episode.id).status == "in_progress"


def test_selected_diagnostic_probe_creates_exactly_one_observation(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)

    result = _submit(loaded, repository, presentation_id=presentation.id, score=4)

    observation = repository.probe_observation_for_attempt(result.attempt_id)
    assert observation is not None
    assert observation.eligible_for_completion
    assert observation.entropy_before > 0
    # Signed realized information (§13.2): a clean full-score observation on a
    # fresh episode concentrates the posterior, so the realized gain is positive.
    assert observation.realized_information_gain > 0
    assert observation.realized_information_gain == pytest.approx(
        observation.entropy_before - observation.entropy_after
    )
    assert repository.probe_presentation(presentation.id).status == "submitted"
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 1
    # §11: a single narrow success cannot complete a multi-hypothesis episode.
    assert repository.probe_episode(episode.id).status == "in_progress"


def test_retried_submission_is_idempotent(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)
    result = _submit(loaded, repository, presentation_id=presentation.id, score=4)

    record_episode_evidence(
        loaded,
        repository,
        learning_object_id=LO_ID,
        attempt_id=result.attempt_id,
        practice_item_id=ITEM_ID,
        attempt_type="diagnostic_probe",
        hints_used=0,
        probe_presentation_id=presentation.id,
        grading_source="ai",
        clock=CLOCK,
    )
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 1
    assert posterior.total_observations == 1


def test_declared_dont_know_keeps_probe_measurement_type(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)

    result = _submit(
        loaded,
        repository,
        presentation_id=presentation.id,
        score=0,
        attempt_type="diagnostic_probe",
        grading_source="deterministic",
        declared_dont_know=True,
    )

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    observation = repository.probe_observation_for_attempt(result.attempt_id)
    assert attempt["attempt_type"] == "diagnostic_probe"
    assert attempt["declared_dont_know"] is True
    assert observation is not None and observation.eligible_for_completion
    assert observation.grader_channel["observed_outcome"] == "unanswered"


def test_consumed_presentation_cannot_qualify_second_attempt(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)
    _submit(loaded, repository, presentation_id=presentation.id, score=4)

    second = _submit(loaded, repository, presentation_id=presentation.id, score=1)
    # The stale reference was stripped pre-persist: the attempt records as
    # incidental evidence, no second observation exists, progress is unchanged.
    assert repository.probe_observation_for_attempt(second.attempt_id) is None
    attempt = repository.fetch_practice_attempt(second.attempt_id)
    assert attempt.get("probe_presentation_id") is None
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 1


def test_hinted_probe_attempt_is_contaminated_and_never_completes(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)

    result = _submit(loaded, repository, presentation_id=presentation.id, score=4, hints_used=2)

    observation = repository.probe_observation_for_attempt(result.attempt_id)
    assert observation is not None
    assert not observation.eligible_for_completion
    assert observation.updates_belief
    assert observation.contamination == {"hints_used": 2}
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 0
    assert posterior.total_observations == 1


def test_self_graded_provider_parks_episode_without_observation(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)

    result = _submit(loaded, repository, presentation_id=presentation.id, score=4, grading_source="self")

    assert repository.probe_observation_for_attempt(result.attempt_id) is None
    assert repository.probe_presentation(presentation.id).status == "ended"
    assert repository.probe_presentation(presentation.id).end_reason == "invalidated"
    assert repository.probe_episode(episode.id).status == "pending_items"


# --- Completion policy (§11, tests 9/10) ---------------------------------------------


def test_two_independent_surfaces_complete_a_stable_episode(tmp_path):
    _, loaded, repository = _setup(tmp_path, extra_item=True)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=4)
    episode = repository.probe_episode(episode.id)
    assert episode.status == "in_progress"  # one narrow success is not enough

    second = _commit(loaded, repository, episode, item_id="pi_svd_define_002")
    _submit(loaded, repository, item_id="pi_svd_define_002", presentation_id=second.id, score=4)

    episode = repository.probe_episode(episode.id)
    assert episode.status == "complete"
    assert episode.completion_reason == "decision_stable"


def test_next_probe_item_peeks_the_unused_surface_without_committing(tmp_path):
    # §5.7 continuity: the Tauri UI asks this before every jump within a
    # block. It must never commit a presentation itself (that stays
    # get_probe_contract's job) and must respect the same §5.4 exposure rule
    # eligible_instruments already enforces.
    _, loaded, repository = _setup(tmp_path, extra_item=True)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    candidate = next_probe_item(loaded, repository, LO_ID)
    assert candidate is not None
    assert candidate.item.id == ITEM_ID

    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=4)

    # ITEM_ID was just observed, so the peek must move on to the other
    # surface instead of re-offering it — and it must not have consumed a
    # presentation of its own (no active presentation was committed by it).
    episode = repository.probe_episode(episode.id)
    assert repository.active_probe_presentation(episode.id) is None
    candidate = next_probe_item(loaded, repository, LO_ID)
    assert candidate is not None
    assert candidate.item.id == "pi_svd_define_002"

    second = _commit(loaded, repository, episode, item_id="pi_svd_define_002")
    _submit(loaded, repository, item_id="pi_svd_define_002", presentation_id=second.id, score=4)
    episode = repository.probe_episode(episode.id)
    assert episode.status == "complete"
    assert next_probe_item(loaded, repository, LO_ID) is None


def test_budget_exhaustion_completes_episode(tmp_path):
    # Four signature-distinct surfaces: §5.4 forbids re-serving an observed
    # item or surface family, so budget exhaustion needs four fresh instruments.
    vault_root, _stale, repository = _setup(tmp_path, with_card=False, extra_item=True)
    _add_item(vault_root, "pi_svd_define_003", surface_family="surface_three")
    _add_item(vault_root, "pi_svd_define_004", surface_family="surface_four")
    loaded = load_vault(vault_root)
    items = [ITEM_ID, "pi_svd_define_002", "pi_svd_define_003", "pi_svd_define_004"]
    admit_contrast_card(repository, items=tuple(items))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    scores = [4, 1, 1, 4]  # conflicting evidence keeps the posterior unstable
    for item_id, score in zip(items, scores):
        episode = repository.probe_episode(episode.id)
        if episode.status != "in_progress":
            break
        presentation = _commit(loaded, repository, episode, item_id=item_id)
        _submit(loaded, repository, item_id=item_id, presentation_id=presentation.id, score=score)
    episode = repository.probe_episode(episode.id)
    assert episode.status == "complete"
    assert episode.completion_reason == "observation_budget_exhausted"


def test_exhausted_instrument_pool_parks_episode_with_generation_need(tmp_path):
    _, loaded, repository = _setup(tmp_path, extra_item=True)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    # Conflicting evidence on both available surfaces: the posterior stays
    # unstable and §5.4 forbids repeats, so the episode parks for generation
    # (§10) instead of lingering open with nothing servable.
    for item_id, score in ((ITEM_ID, 4), ("pi_svd_define_002", 1)):
        episode = repository.probe_episode(episode.id)
        presentation = _commit(loaded, repository, episode, item_id=item_id)
        _submit(loaded, repository, item_id=item_id, presentation_id=presentation.id, score=score)
    episode = repository.probe_episode(episode.id)
    assert episode.status == "pending_items"
    needs = repository.probe_generation_needs(probe_episode_id=episode.id, status="pending")
    assert len(needs) == 1


# --- Open-set mass (§6.3, test 15) ----------------------------------------------------


def test_unmatched_systematic_signature_raises_open_set_probability(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    prior = episode_posterior(loaded, repository, episode).posterior
    presentation = _commit(loaded, repository, episode)

    # Low score with no recognized signature -> other_systematic_error.
    _submit(loaded, repository, presentation_id=presentation.id, score=1)

    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior
    assert posterior[H_OTHER] > prior[H_OTHER]


# --- Stop diagnosing and teach me (§3/§12.1, test 12) ----------------------------------


def test_stop_and_teach_ends_measurement_and_segments_evidence(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)
    _submit(loaded, repository, presentation_id=presentation.id, score=1)
    posterior_before = episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior

    decision = stop_diagnosing_and_teach(loaded, repository, LO_ID, clock=CLOCK)
    assert decision is not None
    assert decision["diagnosed_gap"] is not None
    episode = repository.probe_episode(episode.id)
    assert episode.status == "converted_to_tutoring"

    segments = repository.state_segments_for_learning_object(LO_ID)
    assert [segment.reason for segment in segments] == ["episode_entry", "tutoring_transition"]

    # Post-intervention evidence does not rewrite the pre-intervention posterior.
    later = FrozenClock(NOW.replace(hour=13))
    apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="post", attempt_type="independent_attempt"),
            attempt_id=new_ulid(),
            grade=_grade(4),
            grading_source="ai",
        ),
        clock=later,
    )
    posterior_after = episode_posterior(loaded, repository, episode).posterior
    assert posterior_after == posterior_before


# --- Missing items (§10, tests 13/31) ---------------------------------------------------


def test_missing_instruments_park_episode_with_one_deduplicated_need(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path, with_card=False)
    sync_vault_state(loaded, repository, clock=CLOCK)
    episode = repository.open_probe_episode(LO_ID)
    assert episode is not None
    assert episode.status == "pending_items"

    needs = repository.probe_generation_needs(learning_object_id=LO_ID)
    assert len(needs) == 1

    # Repeated sync neither duplicates the need nor reopens a second episode.
    sync_vault_state(loaded, repository, clock=CLOCK)
    sync_vault_state(loaded, repository, clock=CLOCK)
    assert len(repository.probe_generation_needs(learning_object_id=LO_ID)) == 1
    assert len(repository.probe_episodes_for_learning_object(LO_ID)) == 1


def test_pending_items_episode_keeps_lo_schedulable_with_belief_updates(tmp_path):
    from learnloop.services.scheduler import build_due_queue

    vault_root, loaded, repository = _setup(tmp_path, with_card=False)
    sync_vault_state(loaded, repository, clock=CLOCK)
    episode = repository.open_probe_episode(LO_ID)
    assert episode.status == "pending_items"

    queue = build_due_queue(loaded, repository, clock=CLOCK, persist_explanations=False)
    assert any(item.learning_object_id == LO_ID for item in queue)
    # No instrument -> no probe EIG; the item schedules as ordinary practice.
    scheduled = next(item for item in queue if item.learning_object_id == LO_ID)
    assert scheduled.components["probe_eig"] == 0.0

    prior = episode_posterior(loaded, repository, episode).posterior
    _submit(loaded, repository, attempt_type="independent_attempt", score=4, grading_source="ai")
    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior
    assert posterior["unfamiliar"] < prior["unfamiliar"]
    assert repository.probe_episode(episode.id).status == "pending_items"


# --- Session cap accounting (§5.9, test 36) ----------------------------------------------


def test_qualifying_observations_are_counted_per_session(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    presentation = _commit(loaded, repository, episode)
    _submit(loaded, repository, presentation_id=presentation.id, score=4, session_id="s1")
    # Incidental practice in the same session never counts toward the cap.
    _submit(loaded, repository, attempt_type="independent_attempt", score=4, session_id="s1")

    assert repository.qualifying_probe_observation_count_for_session("s1") == 1
    assert repository.qualifying_probe_observation_count_for_session("s2") == 0


# --- Family admission gate (§9.6, tests 20/21) -------------------------------------------


def _gate_card() -> InstrumentCard:
    return InstrumentCard(
        id="card_gate",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="x",
        bindings={},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        signature_error_types={"confusable_signature": ["conceptual_slip"]},
    )


def test_family_gate_accepts_reproducible_signatures(tmp_path):
    trials = [
        PlantedTrial("robust_initial_grasp", "correct_target_reason"),
        PlantedTrial("robust_initial_grasp", "correct_target_reason"),
        PlantedTrial("confuses_with_neighbor", "confusable_signature"),
        PlantedTrial("confuses_with_neighbor", "confusable_signature"),
        PlantedTrial("unfamiliar", "unanswered"),
    ]
    result = run_family_admission_gate(_gate_card(), CONTRAST_CONFUSABLE_V1, trials)
    assert result.accepted, result.reasons


def test_family_gate_rejects_failed_reverse_matching(tmp_path):
    # Planted confusable responses that grade as generic errors: the declared
    # signature cannot be reproduced (§9.6, test 20).
    trials = [
        PlantedTrial("confuses_with_neighbor", "other_systematic_error"),
        PlantedTrial("confuses_with_neighbor", "other_systematic_error"),
        PlantedTrial("confuses_with_neighbor", "other_systematic_error"),
    ]
    result = run_family_admission_gate(_gate_card(), CONTRAST_CONFUSABLE_V1, trials)
    assert not result.accepted
    assert any("reverse matching" in reason for reason in result.reasons)


def test_family_gate_rejects_overapplied_misconception(tmp_path):
    # A simulated belief-holder firing the signature on a non-applicable
    # control expresses the misconception as generalized incompetence (test 21).
    trials = [
        PlantedTrial("confuses_with_neighbor", "confusable_signature"),
        PlantedTrial("confuses_with_neighbor", "confusable_signature", non_applicable_control=True),
    ]
    result = run_family_admission_gate(_gate_card(), CONTRAST_CONFUSABLE_V1, trials)
    assert not result.accepted
    assert any("control" in reason for reason in result.reasons)


# --- Selection/replay identity (§7.2, test 2) ---------------------------------------------


def test_presentation_snapshot_matches_compiled_instrument(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = instruments[0]
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)

    snapshot = presentation.instrument_card_snapshot
    assert snapshot is not None
    assert snapshot["compiled_likelihood_hash"] == eligible.instrument.compiled_likelihood_hash()
    assert snapshot["rows"] == {slot: dict(row) for slot, row in eligible.instrument.rows.items()}
    assert snapshot["resolved_slot_map"] == eligible.slot_map
    assert presentation.entropy_at_selection is not None
    assert presentation.expected_information_gain is not None


def test_scheduler_slate_atomically_commits_its_selected_probe_presentation(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    sync_vault_state(loaded, repository, clock=CLOCK)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    queue = build_due_queue(
        loaded,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="probe_session"),
        limit=1,
    )
    assert queue and queue[0].practice_item_id == ITEM_ID
    assert queue[0].components["probe_committed"] == 1.0
    slate = repository.latest_scheduler_slate_by_session("probe_session")
    candidate = next(
        row for row in repository.scheduler_slate_candidates(slate["id"])
        if row["returned_rank"] == 1
    )
    presentation = repository.active_probe_presentation(episode.id)
    assert presentation is not None
    assert presentation.practice_item_id == candidate["practice_item_id"]
    assert presentation.scheduler_candidate_id == candidate["id"]
    assert presentation.status == "selected"

    refreshed_queue = build_due_queue(
        loaded,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="probe_session"),
        limit=1,
    )
    assert refreshed_queue[0].practice_item_id == presentation.practice_item_id
    assert repository.active_probe_presentation_for_session("probe_session").id == presentation.id
    assert len(
        [
            row
            for row in repository.probe_presentations_for_episode(episode.id)
            if row.status in ("selected", "served")
        ]
    ) == 1


def test_scheduler_slate_rolls_back_when_probe_assignment_cannot_bind(tmp_path):
    _, _loaded, repository = _setup(tmp_path)
    with pytest.raises(ValueError, match="top returned scheduler candidate"):
        repository.record_scheduler_slate(
            [
                {
                    "practice_item_id": ITEM_ID,
                    "selected_mode": "short_answer",
                    "priority": 1.0,
                    "components": {"selected": 1.0},
                    "target_scope": {"learning_object_id": LO_ID},
                }
            ],
            session_id="rollback_session",
            algorithm_version="test",
            probe_presentation={"practice_item_id": "not_the_selected_item"},
            clock=CLOCK,
        )
    assert repository.latest_scheduler_slate_by_session("rollback_session") is None


def test_item_excluded_from_live_slate_cannot_be_committed_as_a_probe(tmp_path):
    _, loaded, repository = _setup(tmp_path, extra_item=True)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=4)

    episode = repository.probe_episode(episode.id)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    assert ITEM_ID not in {
        entry.item.id
        for entry in eligible_instruments(
            loaded, repository, episode, hypothesis_set=hypothesis_set
        )
    }
    assert (
        commit_item_presentation(
            loaded,
            repository,
            episode,
            loaded.practice_items[ITEM_ID],
            hypothesis_set,
            clock=CLOCK,
        )
        is None
    )


def test_multi_confusable_set_keeps_instrument_eligible(tmp_path):
    """An LO with two confusables locks both `confuses_with:*` labels; a card
    bound to ONE of them must stay eligible — the other label abstains onto
    the open-set row — while a card matching neither abstains entirely."""

    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    instrument = instruments[0].instrument
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    labels_with_second = labels + [
        "confuses_with:eigendecomposition",
        "confuses_with:qr_decomposition",
    ]

    slot_map = map_episode_labels_to_slots(
        instrument, labels_with_second, bindings={"confusable_concept": "eigendecomposition"}
    )
    assert slot_map is not None
    assert slot_map["confuses_with:eigendecomposition"] == "confuses_with_neighbor"
    assert slot_map["confuses_with:qr_decomposition"] == "other_or_unknown"
    snapshot = instrument.snapshot()
    snapshot["resolved_slot_map"] = slot_map
    assert (
        _resolved_slot_map_from_snapshot(snapshot, instrument, labels_with_second)
        == slot_map
    )

    # A card bound to a confusable matching NONE of the live contrasts is the
    # wrong instrument and abstains entirely.
    assert (
        map_episode_labels_to_slots(
            instrument, labels_with_second, bindings={"confusable_concept": "lu_decomposition"}
        )
        is None
    )


def test_labels_map_through_open_set_abstention(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    instrument = instruments[0].instrument
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    slot_map = map_episode_labels_to_slots(instrument, labels)
    assert slot_map is not None
    # recall_without_mechanism is not a card slot: the instrument abstains via
    # the broad open-set row instead of fabricating a signature.
    assert slot_map.get("recall_without_mechanism") == "other_or_unknown"

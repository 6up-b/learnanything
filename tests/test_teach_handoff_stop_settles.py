"""A mid-check "Stop diagnosing and teach me" settles the answers already committed in the block.

The attempt pipeline defers an in-block answer's normalization and diagnosis to the block end
(``post_attempt._defers_to_block_end``); a stop converts the episode, so the block end never runs
for that block. Without the stop settling them, those answers are never normalized (the lesson's
brief misses their misconceptions), never diagnosed, and their withheld feedback is never released.
"""

from __future__ import annotations

from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.diagnosis.probe_dialogue import (
    begin_dialogue_block,
    end_dialogue_block,
    next_dialogue_turn,
    record_turn_submitted,
)
from learnloop.diagnosis.probe_episodes import enter_episode, stop_diagnosing_and_teach
from learnloop.diagnosis.split.jobs import DIAGNOSE_KIND
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault

from tests.diagnosis_split_helpers import blind_record
from tests.helpers import append_config_toml
from tests.probe_block_end_helpers import (
    CLOCK,
    ITEM_2,
    ITEM_ID,
    LO_ID,
    MISCONCEPTION_STATEMENT,
    _commit,
    _grade,
    _misconception_attribution,
    _setup,
    _submit,
)

_STATUSES = ("active", "resolving", "resolved")


def _three_answer_block(tmp_path):
    """Two misses fit in one block without closing it, so the stop meets committed answers."""

    loaded, repository = _setup(tmp_path)
    append_config_toml(loaded.root, "[probe.block]\ndefault_block_observations = 3")
    return load_vault(loaded.root), repository


def _forbid_model_calls(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("the stop asked for a model client")

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)


def _answer_in_block(loaded, repository, episode, item_id):
    presentation = _commit(loaded, repository, episode, item_id=item_id)
    result = _submit(
        loaded, repository, item_id=item_id, presentation_id=presentation.id, score=1,
        error_attributions=[_misconception_attribution()],
    )
    assert result.probe_block_end is None
    run_post_attempt_pipeline(loaded, repository, result=result, clock=CLOCK)
    return result


def test_a_mid_check_stop_normalizes_joint_answers_and_releases_their_feedback(tmp_path, monkeypatch):
    loaded, repository = _three_answer_block(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    answers = [_answer_in_block(loaded, repository, episode, item_id) for item_id in (ITEM_ID, ITEM_2)]
    # Deferred to a block end that the stop will never let run.
    assert repository.misconceptions_for_learning_object(LO_ID, statuses=_STATUSES) == []
    _forbid_model_calls(monkeypatch)

    stopped = stop_diagnosing_and_teach(loaded, repository, LO_ID, clock=CLOCK)

    assert stopped is not None
    assert repository.probe_episode(episode.id).status == "converted_to_tutoring"
    rows = repository.misconceptions_for_learning_object(LO_ID, statuses=_STATUSES)
    assert [row.statement for row in rows] == [MISCONCEPTION_STATEMENT]
    released = {entry["attempt_id"]: entry for entry in stopped.released_feedback}
    assert set(released) == {answer.attempt_id for answer in answers}
    for entry in released.values():
        # Claim-checked after normalization, as the block end releases it: never only the raw prose.
        assert entry["causal_feedback"]["receipt_id"]
    # The decision the lesson reads is the one the stop always persisted.
    assert repository.probe_episode(episode.id).target_decision["diagnosed_gap"] == stopped.decision["diagnosed_gap"]


def test_a_mid_check_stop_queues_the_blind_answers_diagnosis(tmp_path, monkeypatch):
    loaded, repository = _three_answer_block(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    attempt_ids = []
    for item_id in (ITEM_ID, ITEM_2):
        presentation = _commit(loaded, repository, episode, item_id=item_id)
        attempt_id = new_ulid()
        result = apply_attempt(
            loaded,
            repository,
            ApplyAttemptInput(
                draft=AttemptDraft(
                    practice_item_id=item_id, learner_answer_md="answer", attempt_type="diagnostic_probe",
                    probe_presentation_id=presentation.id,
                ),
                attempt_id=attempt_id,
                grade=_grade(1, error_attributions=[_misconception_attribution()]),
                grading_source="ai",
                grader_mode="blind",
            ),
            clock=CLOCK,
        )
        repository.insert_blind_grade_record(
            attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="test-blind",
            output_schema_version="test", context_hash="test",
            record=blind_record(score=1, max_points=4, criteria={"correctness": 1.0}),
            clock=CLOCK,
        )
        assert result.probe_block_end is None
        run_post_attempt_pipeline(loaded, repository, result=result, clock=CLOCK)
        attempt_ids.append(attempt_id)
    for attempt_id in attempt_ids:
        assert repository.post_attempt_jobs(attempt_id=attempt_id, kind=DIAGNOSE_KIND) == []
    _forbid_model_calls(monkeypatch)

    stopped = stop_diagnosing_and_teach(loaded, repository, LO_ID, clock=CLOCK)

    assert stopped is not None
    for attempt_id in attempt_ids:
        assert len(repository.post_attempt_jobs(attempt_id=attempt_id, kind=DIAGNOSE_KIND)) == 1
    assert {entry["attempt_id"] for entry in stopped.released_feedback} == set(attempt_ids)


def test_a_stop_with_nothing_committed_settles_nothing(tmp_path):
    loaded, repository = _three_answer_block(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    _commit(loaded, repository, episode, item_id=ITEM_ID)

    stopped = stop_diagnosing_and_teach(loaded, repository, LO_ID, clock=CLOCK)

    assert stopped is not None
    assert stopped.released_feedback == []


def test_the_calibration_dialogue_s_stop_settles_its_committed_turns(tmp_path, monkeypatch):
    """The dialogue's stop converts the episode before the dialogue ends its block, so the block end
    returns nothing: its committed turns are settled at the stop too."""

    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    attempt_ids = []
    for _ in range(2):
        state, turn = next_dialogue_turn(loaded, repository, state, clock=CLOCK)
        assert turn is not None
        loaded = load_vault(loaded.root)  # the turn's item was written to the vault
        result = _submit(
            loaded, repository, item_id=turn["practice_item_id"], presentation_id=turn["presentation_id"],
            score=1, error_attributions=[_misconception_attribution()],
        )
        run_post_attempt_pipeline(loaded, repository, result=result, clock=CLOCK)
        state = record_turn_submitted(state, turn["presentation_id"])
        attempt_ids.append(result.attempt_id)
    assert repository.misconceptions_for_learning_object(LO_ID, statuses=_STATUSES) == []
    _forbid_model_calls(monkeypatch)

    stopped = stop_diagnosing_and_teach(loaded, repository, LO_ID, clock=CLOCK)
    ended = end_dialogue_block(loaded, repository, state, clock=CLOCK)

    assert ended is None
    assert repository.probe_episode(episode.id).status == "converted_to_tutoring"
    rows = repository.misconceptions_for_learning_object(LO_ID, statuses=_STATUSES)
    assert [row.statement for row in rows] == [MISCONCEPTION_STATEMENT]
    assert [entry["attempt_id"] for entry in stopped.released_feedback] == attempt_ids

"""Owner decision 2026-11-23, "send the goal to the tutor": ``companion.ask`` carries the goal in view on the desk (the
goal lens's) into the tutor's context as the goal's own sentence and the depth the learner chose; a goal whose words
name a topic with a cold check due is withheld whole; with no goal in view the prompt is what it was."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.connection import connect
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.tutor.ai_contracts import READER_GOAL_SUFFIX
from learnloop_sidecar.errors import SidecarError
from tests.companion_rd3a_helpers import wait_job
from tests.goal_lens_helpers import build_lens_vault, lens_context, scoped_goal
from tests.reader_tutor_fakes import LookupTutor, Ready
from tests.reading_path_fixtures import call

GOAL_TASK = "context.goal_in_view is what the learner is working toward"


def _rows(repository: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _first_span(repository: Any, extraction_id: str) -> str:
    return _rows(repository, "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? "
                             "AND block_type = 'Text' ORDER BY ordinal LIMIT 1", (extraction_id,))[0][0]


def _due_check(repository: Any, lo_id: str) -> str:
    due = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    return C.create_commitment(
        repository, action="test_me_later", intent_text=f"check {lo_id}", depth_preset=DP.READY_DEPTH_PRESET,
        targets=[{"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}],
        client_idempotency_key=f"goal-context:{lo_id}", due_hint=due, provenance={"via": "deliverable_ready"}).id


@pytest.fixture
def goal_desk(tmp_path, monkeypatch):
    """The goal lens's vault behind a sidecar context, the tutor a fake that records what it was given."""

    import learnloop_sidecar.handlers.reader as reader_handler

    paths, repository = build_lens_vault(tmp_path / "vault")
    tutor = LookupTutor(answer_md="An eigenvalue scales its eigenvector.")
    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    ctx = lens_context(paths)
    yield paths, ctx, repository, tutor
    ctx.close()


def _ask(ctx: Any, repository: Any, request_id: str, **extra: Any) -> dict[str, Any]:
    span = _first_span(repository, "ext_book")
    call(ctx, "companion.ask", {"requestId": request_id, "surface": "reader", "extractionId": "ext_book",
                                "spanId": span, "question": "why does this matter?", **extra})
    return wait_job(ctx, request_id)


# -- 1: the goal in view -------------------------------------------------------------------------------------------


def test_with_no_goal_in_view_the_tutors_prompt_is_the_reader_asks_byte_for_byte(goal_desk):
    _paths, ctx, repository, tutor = goal_desk
    done = _ask(ctx, repository, "req_plain")
    assert done["status"] == "done" and done["goalInView"] is None
    companion_prompt = tutor.prompts[-1]
    span = _first_span(repository, "ext_book")
    call(ctx, "reader.ask", {"extractionId": "ext_book", "spanId": span, "question": "why does this matter?"})
    reader_prompt = tutor.prompts[-1]
    # The old Reader's Ask builds today's prompt; the companion's without a goal is the same bytes but the thread
    # the first exchange left on the same passage (the Reader sends its earlier exchanges there), so compare the
    # companion's with a fresh Reader ask's parts: no goal key, no goal task, no goal suffix.
    for prompt in (companion_prompt, reader_prompt):
        assert "goal_in_view" not in prompt and GOAL_TASK not in prompt and READER_GOAL_SUFFIX not in prompt
    assert companion_prompt.split('"context"')[0] == reader_prompt.split('"context"')[0]


def test_the_goal_in_view_reaches_the_tutor_as_its_sentence_and_depth(goal_desk):
    paths, ctx, repository, tutor = goal_desk
    goal_id = scoped_goal(paths, repository, sentence="determinants for my midterm")
    ctx.reload(maintenance=False)
    done = _ask(ctx, repository, "req_goal", goalId=goal_id)
    assert (done["status"], done["goalInView"]) == ("done", "given")
    given = tutor.contexts[-1]["goal_in_view"]
    assert given == {"sentence": "determinants for my midterm", "depth": "learn to use it",
                     "depth_means": "explanations, worked examples, practice"}
    assert GOAL_TASK in tutor.prompts[-1] and READER_GOAL_SUFFIX in tutor.prompts[-1]
    source_context = json.loads(_rows(repository, "SELECT source_context_json FROM question_events WHERE id = ?",
                                      (done["questionEventId"],))[0][0])
    assert source_context["goal_in_view"] == {"goal_id": goal_id, "given": True}
    assert _rows(repository, "SELECT goal_id FROM companion_exchange_context WHERE question_event_id = ?",
                 (done["questionEventId"],)) == [(goal_id,)]


def test_a_goal_naming_a_topic_whose_cold_check_is_due_is_given_and_withheld_whole_once_the_check_is_begun(goal_desk):
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers.companion_ask import goal_in_view
    from tests.inline_hold_helpers import hold_open

    paths, ctx, repository, tutor = goal_desk
    goal_id = scoped_goal(paths, repository, sentence="eigenvalues")
    commitment_id = _due_check(repository, "lo_eigen")
    ctx.reload(maintenance=False)
    # Due and not begun: the goal is given as any goal (withholding it would point at the due check's topic).
    done = _ask(ctx, repository, "req_due", goalId=goal_id)
    assert (done["status"], done["goalInView"]) == ("done", "given")
    assert tutor.contexts[-1]["goal_in_view"]["sentence"] == "eigenvalues"
    # Begun: a goal naming its topic is withheld whole (the companion itself waits for the check then).
    hold_open(repository, commitment_id)
    assert goal_in_view(load_vault(paths.root), repository, goal_id) == (None, "withheld")


def test_a_goal_that_names_no_held_topic_is_given_while_another_check_is_due(goal_desk):
    paths, ctx, repository, tutor = goal_desk
    goal_id = scoped_goal(paths, repository, sentence="determinants")
    _due_check(repository, "lo_eigen")
    ctx.reload(maintenance=False)
    done = _ask(ctx, repository, "req_other", goalId=goal_id)
    assert done["goalInView"] == "given" and tutor.contexts[-1]["goal_in_view"]["sentence"] == "determinants"
    assert "eigen" not in json.dumps(tutor.contexts[-1]["goal_in_view"]).casefold()


def test_an_unknown_goal_is_refused_before_anything_is_asked(goal_desk):
    _paths, ctx, repository, tutor = goal_desk
    span = _first_span(repository, "ext_book")
    with pytest.raises(SidecarError) as refused:
        call(ctx, "companion.ask", {"requestId": "req_nogoal", "surface": "reader", "extractionId": "ext_book",
                                    "spanId": span, "question": "why?", "goalId": "goal_missing"})
    assert refused.value.code == "goal_not_found" and tutor.prompts == []

"""Adaptive hints H2a: discriminating questions (spec_adaptive_hints_v1 §4.2, §5; G-H16).

Offered only with two or more open rivals; the writer's candidates are
compiled as instruments and ranked by the existing
``instrument_expected_information_gain`` (asserted by monkeypatch) under
uniform weights (labelled); a candidate whose rivals all predict the same
answer is never shown; with no positive EIG the hint is §4.2's downgrade with
its why line; the question passes leak control and states neither rival.
The learner's answer is a ``discriminate_answer`` row, absent from the
submitted answer and the blind-grading prompt, and writes no posterior or
probe observation; after one is answered on this work, ``discriminating``
leaves the options. Fakes only.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints import discriminating as D
from learnloop.hints import service as S
from learnloop.hints.kinds import NO_SEPARATING_QUESTION
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, add_hypothesis, assists, good_answer, hint_vault, \
    prefer, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'
RIVAL_A = "Adds one to a CDF value as if it were a density"
RIVAL_B = "Reads the CDF as the density"


def _setup(tmp_path, *, rivals: int = 2):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    for index, statement in enumerate([RIVAL_A, RIVAL_B, "Forgets the support"][:rivals]):
        add_hypothesis(paths.sqlite_path, f"h{index}", statement)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, answers=(), option="discriminating@L1", **overrides):
    writer = WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: ChooserFake(prefer(option, 0.9)), seed="d")
    return result, writer


def _candidates(*predicted, question="What does your formula give at x = 0?"):
    def answer(context):
        payload = good_answer(context)
        rivals = [rival["id"] for rival in context["rivals"]]
        payload["candidates"] = [{"question_md": question, "predictions": [
            {"rival_id": rival, "answer": value} for rival, value in zip(rivals, predicted)]}]
        return payload
    return answer


def test_offered_only_with_two_open_rivals(tmp_path):
    from learnloop.hints.options import build_options
    from learnloop.hints.state import assemble_state

    for count, offered in ((1, False), (2, True)):
        paths, vault, repository = _setup(tmp_path / str(count), rivals=count)
        state = assemble_state(vault, repository, vault.practice_items[ITEM], session_id="s1", submission_id="k1",
                               work_md=WORK)
        assert build_options(state, request="more").has("discriminating") is offered


def test_candidates_are_ranked_by_the_existing_instrument_eig(tmp_path, monkeypatch):
    from learnloop.diagnosis import probe_families

    calls = []
    original = probe_families.instrument_expected_information_gain

    def spy(posterior, instrument, slot_map, **kwargs):
        calls.append((dict(posterior), instrument.outcome_alphabet, kwargs))
        return original(posterior, instrument, slot_map, **kwargs)

    monkeypatch.setattr(probe_families, "instrument_expected_information_gain", spy)
    paths, vault, repository = _setup(tmp_path)

    def two(context):
        payload = good_answer(context)
        a, b = [rival["id"] for rival in context["rivals"]]
        payload["candidates"] = [
            {"question_md": "What is F at x = 1?", "predictions": [{"rival_id": a, "answer": "1"},
                                                                    {"rival_id": b, "answer": "1"}]},
            {"question_md": "What does your formula give at x = 0?",
             "predictions": [{"rival_id": a, "answer": "1"}, {"rival_id": b, "answer": "0"}]}]
        return payload

    result, _writer = _ask(vault, repository, [two])
    assert len(calls) == 2 and all(set(posterior.values()) == {0.5} for posterior, _a, _k in calls)
    # The zero-EIG candidate (both predict "1") is never shown; the separating one is.
    assert result.kind == "discriminating" and result.hint_md == "What does your formula give at x = 0?"
    assert result.discriminating["weights_basis"] == "uniform"
    assert result.discriminating["eig_nats"] == pytest.approx(0.6931, abs=1e-3)
    assert result.labels["kind"] == "a question that tells apart two explanations"
    row = assists(paths.sqlite_path)[0]
    assert row["eig_nats"] == pytest.approx(0.6931, abs=1e-3)
    assert json.loads(row["rivals_json"])["weights_basis"] == "uniform"
    assert json.loads(row["predicted_answers_json"])["chosen_index"] == 1


@pytest.mark.parametrize("level", [1, 3])
def test_no_positive_eig_downgrades_and_says_why(tmp_path, level):
    paths, vault, repository = _setup(tmp_path)
    result, _writer = _ask(vault, repository, [_candidates("$0$", "0")], option=f"discriminating@L{level}")
    assert result.status == S.READY and result.kind == ("approach_question" if level == 1 else "next_step")
    assert str(result.hint_md).startswith(NO_SEPARATING_QUESTION[level])
    row = assists(paths.sqlite_path)[0]
    # The row keeps the drawn option and its propensity, and records the served kind.
    assert json.loads(row["drawn_option_json"])["kind"] == "discriminating"
    assert row["hint_kind"] == result.kind and row["eig_nats"] == 0.0


def test_a_question_that_states_a_rival_is_never_shown(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    stating = _candidates("1", "0", question=f"Maybe you {RIVAL_A.lower()}: what does it give at 0?")
    result, writer = _ask(vault, repository, [stating, _candidates("1", "0")])
    assert "discriminating_states_a_rival" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert result.hint_md == "What does your formula give at x = 0?"


def test_a_question_that_leaks_is_never_shown(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    leaking = _candidates("1", "0", question="Is P(X ≤ 1/2) = 1/4?")
    result, writer = _ask(vault, repository, [leaking, _candidates("1", "0")])
    assert "discriminating_question_leaks" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert result.status == S.READY and "1/4" not in str(result.hint_md)


def test_the_rank_drops_zero_eig_by_construction():
    rivals = [D.Rival("a", "x", "hypothesis", "1", "candidate"), D.Rival("b", "y", "hypothesis", "2", "candidate")]
    ranked = D.rank_candidates([
        {"question_md": "q1", "predictions": [{"rival_id": "a", "answer": " 2 "}, {"rival_id": "b", "answer": "$2$"}]},
        {"question_md": "q2", "predictions": [{"rival_id": "a", "answer": "2"}]},  # one rival: not a candidate
    ], rivals)
    assert [entry.question_md for entry in ranked] == ["q1"] and ranked[0].eig_nats == pytest.approx(0.0)
    assert D.best_candidate(ranked) is None


# -- the answer ---------------------------------------------------------------------------


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _tables(path):
    with closing(sqlite3.connect(path)) as connection:
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in ("probe_episodes", "probe_observations", "probe_posteriors", "causal_hypotheses",
                              "reveal_events", "practice_attempts")
                if connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone()}


def test_the_answer_is_an_assist_row_that_moves_nothing_and_never_reaches_the_grader(tmp_path):
    from learnloop.attempts.blind_grading import blind_grading_context, blind_grading_prompt

    paths, vault, repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_writer_client = WriterFake([_candidates("1", "0")])
    ctx.hint_chooser_client = ChooserFake(prefer("discriminating@L1", 0.9))
    ctx.hint_seed = "d"
    append = '[hints]\nchoice_policy = "argmax"\n'
    assert append  # (the vault is argmax already)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM,
                                               "submissionId": "k1", "answerMd": WORK})
    question = job["result"]
    assert question["kind"] == "discriminating" and question["discriminating"]["answerBox"] is True
    before = _tables(paths.sqlite_path)
    answer = _call(ctx, "practice.answer_discriminating", {
        "sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
        "questionAssistId": question["assistId"], "answerMd": "UNIQUE-ANSWER-0"})
    assert answer["recorded"] is True and answer["settled"] is False
    assert _tables(paths.sqlite_path) == before
    row = next(row for row in assists(paths.sqlite_path) if row["assist_kind"] == "discriminate_answer")
    assert (row["counted_by"], row["hint_kind"], row["feedback_text"]) == (None, None, "UNIQUE-ANSWER-0")
    # The next hint's context carries it, and "discriminating" leaves the options on this work.
    ctx.hint_writer_client = WriterFake()
    nxt = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM,
                                               "submissionId": "k1", "answerMd": WORK})["result"]
    options = json.loads(assists(paths.sqlite_path)[-1]["options_json"])
    assert options["excluded"]["discriminating@L1"] == "answered_here"
    assert ctx.hint_writer_client.contexts[0]["discriminating_answers"][0]["answer"] == "UNIQUE-ANSWER-0"
    assert nxt["status"] == "ready"
    # A settling answer says so.
    settled = _call(ctx, "practice.answer_discriminating", {
        "sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
        "questionAssistId": question["assistId"], "answerMd": "0"})
    assert settled["settled"] is True and settled["consistentRivals"]
    # Never part of the submitted answer: the blind prompt of this attempt's answer has none of it.
    prompt = blind_grading_prompt(blind_grading_context(vault, vault.practice_items[ITEM], attempt_id="a1",
                                                        learner_answer_md=WORK))
    assert "UNIQUE-ANSWER-0" not in prompt and RIVAL_A not in prompt and "formula give at x = 0" not in prompt


def test_an_answer_names_a_shown_discriminating_question_of_this_attempt(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    result, _writer = _ask(vault, repository, option="next_step@L3")
    S.deliver(repository, str(result.assist_id))
    with pytest.raises(S.HintRequestError):
        S.record_discriminate_answer(vault, repository, practice_item_id=ITEM, session_id="s1",
                                     submission_id="k1", question_assist_id=str(result.assist_id), answer_md="0")


def test_on_new_work_a_new_discriminating_question_may_be_offered(tmp_path):
    from learnloop.hints.options import build_options
    from learnloop.hints.state import assemble_state

    _paths, vault, repository = _setup(tmp_path)
    asked, _writer = _ask(vault, repository, [_candidates("1", "0")])
    S.deliver(repository, str(asked.assist_id))
    S.record_discriminate_answer(vault, repository, practice_item_id=ITEM, session_id="s1", submission_id="k1",
                                 question_assist_id=str(asked.assist_id), answer_md="1")
    item = vault.practice_items[ITEM]
    same = assemble_state(vault, repository, item, session_id="s1", submission_id="k1", work_md=WORK)
    moved = assemble_state(vault, repository, item, session_id="s1", submission_id="k1", work_md=WORK + "\nF(0) = 0")
    assert not build_options(same, request="more").has("discriminating")
    assert build_options(moved, request="more").has("discriminating")

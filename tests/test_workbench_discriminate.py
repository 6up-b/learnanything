"""Reader workbench RW2b: a question that tells explanations apart (spec_reader_workbench_v1 §5.2, §5.8; G37, G-H16).

With two or more rivals open on the questionable step (the check's own
guesses among them), rung 1 is a ``discriminating`` question and level 1's
only option; with one, rung 1 is an ordinary question. Whether rung 1 is
suggested is the sampled draw: a Decider that puts its probability on it gets
it suggested, one that puts it elsewhere leaves it takeable. Candidates are
ranked by ``instrument_expected_information_gain`` (asserted by monkeypatch);
a candidate whose rivals all predict the same answer is never offered and a
rung 1 with no positive EIG serves an approach question saying why. The
question states neither rival and passes leak control. Its answer reaches the
diagnoser's trace and the next hint's context and writes no posterior or
probe observation; after one is answered, ``discriminating`` leaves the
options on that step. ``workbench.discriminate_enabled`` off removes it.
Fakes only.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.workbench_help_fakes import CheckFake, call, check_answer, help_rows, open_problem, run_job, sidecar, wb_answer


def _rival_check() -> CheckFake:
    """The default check: step 2 questionable with two rival readings."""

    return CheckFake()


def _one_rival(context):
    payload = check_answer(context)
    payload["error_readings"] = payload["error_readings"][:1]
    return payload


def _setup(tmp_path, config="", **kwargs):
    paths, ctx, session = sidecar(tmp_path, config, **kwargs)
    wb, chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    return paths, ctx, session, wb, chains


def _suggest(ctx, wb):
    return run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))


def _options(paths, wb):
    rows = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    return json.loads(rows[-1]["options_json"])["options"]


def test_with_two_rivals_open_rung_one_is_the_discriminating_question_and_its_only_option(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path)
    suggestion = _suggest(ctx, wb)["suggestion"]
    rung_one = suggestion["rungs"][0]
    assert rung_one["discriminating"] is True and rung_one["label"].startswith("a question that tells apart")
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert question["status"] == "ready" and question["kind"] == "discriminating" and question["level"] == 1
    assert _options(paths, wb) == ["discriminating@L1"]
    assert question["labels"]["kind"] == "a question that tells apart two explanations"


def test_with_one_rival_rung_one_is_an_ordinary_question(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, check=CheckFake([_one_rival]))
    suggestion = _suggest(ctx, wb)["suggestion"]
    assert suggestion["rungs"][0]["discriminating"] is False
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert question["kind"] == "approach_question"
    assert "discriminating@L1" not in _options(paths, wb)


def test_the_suggestion_is_the_draw_rung_one_when_the_decider_leans_there_takeable_otherwise(tmp_path):
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("discriminating@L1", 0.97)))
    assert _suggest(ctx, wb)["suggestion"]["level"] == 1
    _paths2, ctx2, _session2, wb2, _chains2 = _setup(tmp_path / "elsewhere",
                                                    chooser=ChooserFake(prefer("next_step@L3", 0.97)))
    suggestion = _suggest(ctx2, wb2)["suggestion"]
    assert suggestion["level"] == 3 and suggestion["rungs"][0]["discriminating"] is True
    taken = run_job(ctx2, call(ctx2, "workbench.request_help", {"sessionId": wb2, "takenLevel": 1,
                                                                "offeredLevel": 3,
                                                                "suggestionId": suggestion["suggestionId"]}))
    assert taken["kind"] == "discriminating"


def test_candidates_are_ranked_by_the_instrument_eig(tmp_path, monkeypatch):
    import learnloop.diagnosis.probe_families as families

    calls = []
    original = families.instrument_expected_information_gain

    def spy(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(families, "instrument_expected_information_gain", spy)
    paths, ctx, _session, wb, _chains = _setup(tmp_path)
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert question["kind"] == "discriminating" and calls
    [row] = [row for row in help_rows(paths, wb) if row["hint_kind"] == "discriminating"]
    assert row["eig_nats"] > 0 and json.loads(row["rivals_json"])["weights_basis"]


def test_a_rung_one_whose_candidates_all_have_zero_eig_asks_about_the_approach_and_says_why(tmp_path):
    def same(context):
        payload = wb_answer(context)
        if context["chosen"]["kind"] == "discriminating":
            payload["candidates"] = [{"question_md": "What is F(0)?",
                                      "predictions": [{"rival_id": rival["id"], "answer": "0"}
                                                      for rival in context.get("rivals") or []]}]
            payload["fallback_hint_md"] = "What would your first move be?"
            payload["asks_about"] = "first_move"
        return payload

    _paths, ctx, _session, wb, _chains = _setup(tmp_path, writer=WriterFake([same] * 6))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert hint["status"] == "ready" and hint["kind"] == "approach_question"
    assert hint["hintMd"].startswith("No question separates these readings")


def test_the_question_states_neither_rival(tmp_path):
    def stating(context):
        payload = wb_answer(context)
        if context["chosen"]["kind"] == "discriminating":
            rivals = context.get("rivals") or []
            payload["candidates"] = [{"question_md": f"Is it that you {rivals[0]['statement'].lower()}?",
                                      "predictions": [{"rival_id": rival["id"], "answer": str(index)}
                                                      for index, rival in enumerate(rivals)]}]
        return payload

    _paths, ctx, _session, wb, _chains = _setup(tmp_path, writer=WriterFake([stating] * 6))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    # Never shown as a discriminating question that states a rival.
    assert hint["status"] != "ready" or "treats a cdf value" not in (hint.get("hintMd") or "").lower()


def test_its_answer_reaches_the_next_hint_and_writes_no_posterior_or_probe_observation(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path)

    def counts():
        with closing(sqlite3.connect(paths.sqlite_path)) as connection:
            return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("probe_observations", "facet_recall_state", "grading_evidence", "practice_attempts")}

    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    before = counts()
    answered = call(ctx, "workbench.answer_discriminating", {"sessionId": wb, "questionAssistId": question["assistId"],
                                                             "answerMd": "0"})
    assert answered["recorded"] is True and answered["message"]
    assert counts() == before
    [answer] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "discriminate_answer"]
    assert (answer["surface"], answer["counted_by"], answer["workbench_session_id"]) == ("workbench", None, wb)
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert ctx.hint_writer_client.contexts[-1]["discriminating_answers"][0]["answer"] == "0"
    # After one is answered on the step, discriminating leaves its options.
    again = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert again["kind"] == "approach_question"


def test_with_the_switch_off_rung_one_is_an_ordinary_question(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, "[workbench]\ndiscriminate_enabled = false\n")
    suggestion = _suggest(ctx, wb)["suggestion"]
    assert suggestion["rungs"][0]["discriminating"] is False
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert hint["kind"] == "approach_question"
    options = json.loads([row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"][-1]["options_json"])
    assert options["excluded"].get("discriminating@L1") == "switched_off"

"""Reader workbench RW2b: the diagnoser's step trace and the blind grader (spec_reader_workbench_v1 §5.4; W8, G6, G37, G38).

At Submit the split diagnoser's context gains, for a workbench attempt only,
the assists in order (each check with its verdicts, step graph and error-kind
guess labelled as a guess; each hint with its kind and level; each
discriminating question with the learner's answer) and the work before each,
under ``+workbench-v1``; never an approach map. Every other attempt's
context renders exactly as before. The blind grader sees the composed steps
only: no step history, hint, kind, check or map. Fakes only.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.context import AssembledContext, KnownIds
from learnloop.diagnosis.split.contract import diagnosis_prompt_version
from learnloop.diagnosis.split.live import current_attempt_for
from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION
from learnloop.diagnosis.split.workbench_trace import SUFFIX, trace_for_attempt
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, WORK
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import STEP_2, call, open_problem, run_job, sidecar


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _assembled(current) -> AssembledContext:
    empty = frozenset()
    return AssembledContext(mode="exact", blocks={}, current=current.render(),
                            known=KnownIds(empty, empty, empty, empty, empty, empty), receipt={}, context_hash="h",
                            tokens=0)


def _worked_problem(tmp_path):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    call(ctx, "workbench.answer_discriminating", {"sessionId": wb, "questionAssistId": question["assistId"],
                                                  "answerMd": "zero"})
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    return paths, ctx, session, attempt, hint


def test_a_workbench_attempt_carries_its_trace_under_the_suffix_and_never_a_map(tmp_path, grader):
    paths, _ctx, _session, attempt, hint = _worked_problem(tmp_path)
    row = _attempt(paths, attempt["attemptId"])
    repository = Repository.attach(paths.sqlite_path)
    trace = trace_for_attempt(repository, row)
    kinds = [entry["assist"] for entry in trace["assists"]]
    assert kinds == ["check", "hint", "discriminating_answer", "hint"]
    check = trace["assists"][0]
    assert check["first_questionable_step"] == 2 and check["error_kind_guess"].endswith("(the check's guess, not a diagnosis)")
    assert check["verdicts"][1]["depends_on_steps"] == [1]
    assert trace["assists"][0]["work_before"][1]["text"] == STEP_2
    assert trace["assists"][2]["answer"] == "zero"
    assert trace["assists"][3]["kind"] == hint["kind"] and trace["assists"][3]["level"] == 3
    blob = json.dumps(trace)
    assert "map_node_id" not in blob and "r_ref" not in blob and '"cdf"' not in blob
    vault = load_vault(paths.root)
    current = current_attempt_for(vault, row, {"rubric_score": 0, "criteria": []}, repository)
    assert current.workbench_trace == trace and "workbench_trace" in current.render()
    assert diagnosis_prompt_version(_assembled(current)) == f"{DIAGNOSIS_PROMPT_VERSION}{SUFFIX}"


def test_every_other_attempt_renders_exactly_as_before(tmp_path, grader):
    paths, ctx, session, _attempt_row, _hint = _worked_problem(tmp_path)
    box = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                       "attemptType": "independent_attempt", "hintsUsed": 0, "submissionId": "box"})
    row = _attempt(paths, box["attemptId"])
    repository = Repository.attach(paths.sqlite_path)
    assert trace_for_attempt(repository, row) is None
    current = current_attempt_for(load_vault(paths.root), row, {"rubric_score": 0, "criteria": []}, repository)
    assert current.workbench_trace is None and "workbench_trace" not in current.render()
    assert diagnosis_prompt_version(_assembled(current)) == DIAGNOSIS_PROMPT_VERSION


def test_the_blind_grader_sees_the_composed_steps_only(tmp_path, grader):
    _paths, _ctx, _session, _attempt_row, hint = _worked_problem(tmp_path)
    graded = json.dumps(grader.contexts[-1], default=str)
    assert STEP_2 in graded
    for leaked in (hint["hintMd"], "zero", "model's guess", "workbench_trace", "discriminating", "r_ref"):
        assert leaked not in graded, leaked

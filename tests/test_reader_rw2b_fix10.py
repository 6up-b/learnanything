"""Reader workbench RW2b + hints H3, fix round 10: the switch on every read path, and one counting rule.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 10 (orchestrator)":

1. with ``workbench.symbolic_checks_enabled`` off, every read path maps a
   stored ``checked``/``checked_numerically`` verdict or claim to the model's
   reading (help_state, a recheck of unchanged steps, the hint context a new
   hint row copies, the report, the claims); the view carries the switch;
2. counting: (a) no RW2b server assist on any open problem -> RW2a's count
   exactly, as at ``7d4c5f4ce`` (``authoredHints`` ignored); (b) otherwise the
   client part, the book once and the UNION of server assist ids over all
   open problems; (c) the refold unions the ids it saw before grading with
   those it sees in its transaction.

Fakes only; no model is reached.
"""

from __future__ import annotations

from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest

import learnloop_sidecar.handlers.practice as practice_handler
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.hints.report_workbench import build_workbench_report
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, help_rows, open_problem, run_job,
                                        sidecar, step_check, wb_answer)

ROOT = Path(__file__).resolve().parents[1]
BASE = "7d4c5f4ce"


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


# -- Item 1: a stored symbolic result never reads as checked while the switch is off ----------------


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _answer(_context):
    return {"steps": [step_check(1, "questionable", reason="the model's reading",
                                 transformation=_transformation(kind="equivalence", expression="x+x", result="2*x")),
                      step_check(2, "unchecked")],
            "first_questionable_step": 1, "error_kind_guess": "invalid_algebra", "error_kind_reason": "",
            "error_readings": [], "assumptions": []}


def _switch_off(paths, ctx):
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
    ctx.reload()


@pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")
def test_item1_enable_check_disable_then_resume_recheck_hint_and_report_never_read_checked(tmp_path):
    claim = {"step": 1, "statement": "x + x = 2x", **_transformation(kind="equivalence", expression="x+x",
                                                                         result="2*x")}
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}] + [wb_answer] * 6)
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, writer=writer,
                                   check=CheckFake([_answer] * 3), chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    on = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    assert on["verdicts"][0]["method"] == "checked" and on["symbolicEnabled"] is True
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert [entry["status"] for entry in hint["claims"]] == ["checked"]
    assert build_workbench_report(paths.sqlite_path, symbolic_enabled=True)["checks"]["verdict_methods"]["checked"] == 1

    _switch_off(paths, ctx)
    # Resume: help_state.
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["check"]["symbolicEnabled"] is False
    assert [entry["method"] for entry in state["check"]["verdicts"]] == ["model", "model"]
    assert not {entry["mark"] for entry in state["check"]["verdicts"]} & {"✓", "≠"}
    assert [entry["status"] for entry in state["hints"][0]["claims"]] == ["model"]
    assert state["hints"][0]["symbolicEnabled"] is False
    # Recheck the unchanged steps: the stored check is reused, read as the model's.
    again = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    assert {entry["method"] for entry in again["check"]["verdicts"]} == {"model"}
    # A new hint: the context's verdicts are never copied as checked.
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 2}))
    newest = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"][-1]
    assert {entry["method"] for entry in json.loads(newest["step_verdicts_json"] or "[]")} <= {"model"}
    # The report folds historical symbolic counts into model while the switch is off.
    block = build_workbench_report(paths.sqlite_path)
    assert "checked" not in block["checks"]["verdict_methods"]
    assert "checked" not in block["checks"]["symbolic_outcomes"]
    # The stored rows are history and stay as they were.
    [check_row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert json.loads(check_row["step_verdicts_json"])[0]["method"] == "checked"


# -- Item 2: one counting rule ----------------------------------------------------------------------


def _box_submit(ctx, session, key, *, hints_used=0, authored=None):
    payload = {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
               "hintsUsed": hints_used, "submissionId": key}
    if authored is not None:
        payload["authoredHints"] = authored
    return call(ctx, "submit_attempt", payload)


def _two_open_problems(ctx):
    first, _chains = open_problem(ctx)
    call(ctx, "workbench.abandon", {"sessionId": first})
    second, _chains = open_problem(ctx)
    call(ctx, "workbench.reopen", {"sessionId": first})
    return first, second


def test_item2_an_older_client_counts_the_union_of_assists_over_two_open_problems(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    first, second = _two_open_problems(ctx)
    for wb in (first, second):
        assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    # No authoredHints (an older client): two distinct checks.
    attempt = _box_submit(ctx, session, "old-two")
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_item3_the_refold_never_drops_an_assist_it_already_counted(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path, "[workbench]\nmax_calls_per_session = 10\n")
    first, second = _two_open_problems(ctx)
    for wb in (first, second):
        assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    real = practice_handler._server_hint_fold
    done = []

    entered = []

    def during_grading(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not entered:
            entered.append(True)
            # Another process submits problem A, then problem B shows a second check.
            done.append(call(ctx, "workbench.submit", {"sessionId": first, "practiceSessionId": session}))
            call(ctx, "workbench.save_step", {"sessionId": second, "clientIdempotencyKey": "more", "op": "add",
                                              "bodyMd": "so P = 1/4"})
            done.append(run_job(ctx, call(ctx, "workbench.check", {"sessionId": second})))
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", during_grading)
    attempt = _box_submit(ctx, session, "refold-three")
    assert len(done) == 2 and done[1]["shown"] is True
    # A1 and B1 seen before grading, B2 in the transaction. Fix round 13
    # (H2b's R1 rule over the item's window, superseding open question 5's
    # two-attempt rule): A's attempt committed first and took the window, A1
    # and B1; this one takes B2. Every assist is counted exactly once.
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1
    assert _attempt(paths, done[0]["attempt"]["attemptId"])["hints_used"] == 2


def _run_sequence(code_root: Path, vault_dir: Path) -> dict:
    script = code_root / "tests" / "rw2b_fix10_base_sequence.py"
    if not script.exists():
        shutil.copy(ROOT / "tests" / "rw2b_fix10_base_sequence.py", script)
    env = {**os.environ, "PYTHONPATH": str(code_root / "src")}
    done = subprocess.run([sys.executable, "-m", "tests.rw2b_fix10_base_sequence", str(vault_dir)], cwd=code_root,
                          env=env, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-3000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_item4_with_help_off_and_no_rw2b_assist_the_counts_equal_the_base_codes(tmp_path):
    if shutil.which("git") is None or subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", BASE],
                                                     capture_output=True).returncode != 0:
        pytest.skip(f"git or commit {BASE} is not available")
    base = tmp_path / "base"
    base.mkdir()
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", BASE, "src", "tests", "migrations"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive, check=True)
    at_base = _run_sequence(base, tmp_path / "vault-base")
    # The code under test (its src, beside its tests and migrations).
    import learnloop

    at_tip = _run_sequence(Path(learnloop.__file__).resolve().parents[2], tmp_path / "vault-tip")
    assert at_tip == at_base
    # RW2a's own count: the larger of the book and the carried hint, never their sum.
    assert at_tip["workbench_submit"][0] == 1

"""Reader workbench RW2b + hints H3, fix round 11: one accessor for stored symbolic results; the client floor; the base refold.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 11 (orchestrator)":

1. every reader of a stored symbolic verdict or claim status goes through
   ``learnloop.symbolic_view`` with the CURRENT switch: a cached hint job read
   after the switch went off, and the diagnoser's workbench trace, read as
   the model's (``tests/test_architecture.py`` keeps other modules off the
   raw fields);
2. the client floor applies to the non-server subtotal, and the union of
   server assist ids adds to it (in the refold too);
3. while no RW2b server assist exists before grading or in the transaction,
   the refold keeps RW2a's pre-grading count and type exactly, as the base.

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
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.live import current_attempt_for
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, open_problem, run_job, sidecar,
                                        step_check, wb_answer)

ROOT = Path(__file__).resolve().parents[1]
BASE = "7d4c5f4ce"
needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _switch_off(paths, ctx):
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
    ctx.reload()


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


# -- Item 1: the cached hint job and the diagnoser's trace read the switch now ---------------------


@needs_bwrap
def test_item1_a_hint_job_finished_while_on_reads_as_the_models_after_the_switch_goes_off(tmp_path):
    claim = {"step": 1, "statement": "x + x = 2x", **_transformation(kind="equivalence", expression="x+x",
                                                                         result="2*x")}
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, writer=writer,
                                   chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    ctx.hints_inline = False
    started = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    assert ctx.workbench_help_jobs.get(started["jobId"]).done.wait(30)
    ctx.hints_inline = True
    # Finished with the switch on; disabled and reloaded before the first poll.
    _switch_off(paths, ctx)
    for _read in range(2):  # the first delivery, then a later read of the cached payload
        payload = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})
        assert payload["state"] == "done"
        result = payload["result"]
        assert result["symbolicEnabled"] is False
        assert [(entry["status"], entry["label"]) for entry in result["claims"]] == [
            ("model", "model's reading, not checked")]


def _answer(_context):
    return {"steps": [step_check(1, "questionable", reason="the model's reading",
                                 transformation=_transformation(kind="equivalence", expression="x+x", result="2*x")),
                      step_check(2, "unchecked")],
            "first_questionable_step": 1, "error_kind_guess": "invalid_algebra", "error_kind_reason": "",
            "error_readings": [], "assumptions": []}


@needs_bwrap
def test_item1_the_diagnosers_trace_reads_a_stored_checked_verdict_as_the_models_when_off(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, check=CheckFake([_answer]))
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    assert view["verdicts"][0]["method"] == "checked"
    _switch_off(paths, ctx)
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    row = _attempt(paths, attempt["attemptId"])
    current = current_attempt_for(load_vault(paths.root), row, {"rubric_score": 0, "criteria": []},
                                  Repository.attach(paths.sqlite_path))
    [check] = [entry for entry in current.workbench_trace["assists"] if entry["assist"] == "check"]
    assert {verdict["method"] for verdict in check["verdicts"]} == {"model"}


# -- Item 2: the client floor applies to the non-server subtotal --------------------------------------


def test_item2_a_client_held_book_and_a_check_on_another_problem_are_two(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    # The answer box kept bookLeft (its problem was abandoned): hintsUsed 1, no authored reveal.
    attempt = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                           "attemptType": "independent_attempt", "hintsUsed": 1, "authoredHints": 0,
                                           "submissionId": "book-left"})
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_item2_the_refold_applies_the_same_floor(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    real = practice_handler._server_hint_fold
    done = []

    def during_grading(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not done:
            done.append(run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb})))
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", during_grading)
    attempt = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                           "attemptType": "independent_attempt", "hintsUsed": 1, "authoredHints": 0,
                                           "submissionId": "book-left-late"})
    assert done and done[0]["shown"] is True
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


# -- Item 3: the base refold, against the base code ---------------------------------------------------


def _run_sequence(code_root: Path, vault_dir: Path) -> dict:
    script = code_root / "tests" / "rw2b_fix11_base_sequence.py"
    if not script.exists():
        shutil.copy(ROOT / "tests" / "rw2b_fix11_base_sequence.py", script)
    env = {**os.environ, "PYTHONPATH": str(code_root / "src")}
    done = subprocess.run([sys.executable, "-m", "tests.rw2b_fix11_base_sequence", str(vault_dir)], cwd=code_root,
                          env=env, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-3000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_item3_a_book_opened_during_grading_leaves_the_count_and_type_as_the_base_stores_them(tmp_path):
    if shutil.which("git") is None or subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", BASE],
                                                     capture_output=True).returncode != 0:
        pytest.skip(f"git or commit {BASE} is not available")
    base = tmp_path / "base"
    base.mkdir()
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", BASE, "src", "tests", "migrations"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive, check=True)
    at_base = _run_sequence(base, tmp_path / "vault-base")
    import learnloop

    at_tip = _run_sequence(Path(learnloop.__file__).resolve().parents[2], tmp_path / "vault-tip")
    assert at_tip["book_counted_during_grading"] is True
    assert at_tip == at_base
    assert at_tip["attempt"] == [0, 0, "independent_attempt"]

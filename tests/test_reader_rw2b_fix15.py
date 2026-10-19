"""Reader workbench RW2b + hints H3, fix round 15 (``docs/reviews/reader-rw2b-h3-codex-review.md``).

1. the chooser's state (``decider_extra``, for the suggestion and the
   taken-rung draw) reads the verdicts through the live-masked context;
2. the diagnoser's context masks the workbench trace at the final
   prompt-construction boundary, after every blocking step.

Fakes only; no model is reached.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split import context as context_module
from learnloop.diagnosis.split.jobs import live_history_store, settings_from_config
from learnloop.diagnosis.split.live import current_attempt_for
from learnloop.hints import workbench as hint_workbench
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, open_problem, run_job, sidecar,
                                        step_check, wb_answer)

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _context_with_a_checked_verdict(switch):
    step = hint_workbench.WorkbenchStep(chain_id="c1", step_id="s1", number=1, kind="step", body_md="x + x = 2x")
    verdict = hint_workbench.StepVerdict(chain_id="c1", verdict="valid", method="checked",
                                         content_hash=step.content_hash)
    kwargs = {"_raw_verdicts": (verdict,)} if "_raw_verdicts" in hint_workbench.WorkbenchHintContext.__dataclass_fields__ \
        else {"verdicts": (verdict,)}
    return hint_workbench.WorkbenchHintContext(workbench_session_id="wb", steps=(step,), symbolic_now=switch, **kwargs)


def test_item1_the_choosers_state_reads_the_switch_now():
    switch = {"on": True}
    context = _context_with_a_checked_verdict(lambda: switch["on"])
    assert hint_workbench.decider_extra(context)["check"]["symbolically_checked"] == 1
    switch["on"] = False  # off before the chooser builds its inputs
    assert hint_workbench.decider_extra(context)["check"]["symbolically_checked"] == 0
    assert {row.method for row in context.verdicts} == {"model"}


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


@needs_bwrap
def test_item2_a_switch_off_during_context_assembly_masks_the_rendered_trace(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, check=CheckFake([_answer]),
                                  writer=WriterFake([wb_answer]), chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"][0]["method"] == "checked"
    attempt_id = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]["attemptId"]
    vault = load_vault(paths.root)
    repository = Repository.attach(paths.sqlite_path)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        attempt = dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())
    current = current_attempt_for(vault, attempt, {"rubric_score": 0, "criteria": []}, repository)
    [check] = [entry for entry in current.workbench_trace["assists"] if entry["assist"] == "check"]
    assert check["verdicts"][0]["method"] == "checked"  # still on

    def blocking_retrieval(retriever, store, current_, before, exact, *, limit):
        # The registry's embeddings are awaited; meanwhile the switch goes off.
        toml = paths.root / "learnloop.toml"
        toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
        return list(exact), {"method": "knn", "matches": []}

    monkeypatch.setattr(context_module, "_registry_shortlist", blocking_retrieval)
    assembled = context_module.assemble_diagnosis_context(
        vault, live_history_store(vault, repository), current, settings_from_config(vault),
        registry_retriever=object())
    rendered = assembled.rendered()
    assert '"method": "checked"' not in rendered and '"method":"checked"' not in rendered
    [shown] = [entry for entry in assembled.current["workbench_trace"]["assists"] if entry["assist"] == "check"]
    assert {verdict["method"] for verdict in shown["verdicts"]} == {"model"}
    # The hash and the receipt are those of the masked context.
    import hashlib

    from learnloop.diagnosis.split.context import DIAGNOSIS_CONTEXT_VERSION

    assert assembled.context_hash == assembled.receipt["context_hash"] == hashlib.sha256(
        f"{DIAGNOSIS_CONTEXT_VERSION}\n{assembled.mode}\n{rendered}".encode("utf-8")).hexdigest()

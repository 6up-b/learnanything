"""Reader workbench RW2b: the workbench rows of ``learnloop hints report`` (spec_reader_workbench_v1 §13 RW2b checkpoint, §15).

Read-only, from ``help_assists``, the ``hint_fit`` verdicts and the
attempts: checks (shown, latency, verdict methods, guesses), the rung taken
against the rung suggested by facet and week, recovery after a check,
"doesn't connect" by shortcut and kind, goals after a waypoint and the
discriminating questions; never a step's or a hint's text. Absent when the
vault has no workbench rows. Fakes only.
"""

from __future__ import annotations

import json

from learnloop.hints.report_workbench import build_workbench_report
from learnloop.vault.loader import load_vault
from tests.workbench_help_fakes import STEP_2, call, open_problem, run_job, sidecar


def test_the_block_counts_checks_rungs_replies_and_questions_and_never_the_text(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    assert build_workbench_report(paths.sqlite_path) is None
    wb, chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    suggestion = run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))["suggestion"]
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1,
                                                                 "offeredLevel": suggestion["level"],
                                                                 "suggestionId": suggestion["suggestionId"]}))
    call(ctx, "workbench.answer_discriminating", {"sessionId": wb, "questionAssistId": question["assistId"],
                                                  "answerMd": "0"})
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "request": "feedback",
                                                      "answeredAssistId": hint["assistId"],
                                                      "feedbackShortcut": "too_big", "feedbackText": "far"}))
    vault = load_vault(paths.root)
    facets = {item.id: list(item.evidence_facets) for item in vault.practice_items.values()}
    block = build_workbench_report(paths.sqlite_path, item_facets=facets)
    assert block["problems"] == 1 and block["checks"]["shown"] == 1
    assert block["checks"]["verdict_methods"] == {"model": 2}
    assert block["checks"]["error_kind_guesses"] == {"conceptual": 1}
    asked = block["discriminating"]
    assert asked["asked"] == 1 and asked.get("answered_both_stand", 0) + asked.get("answered_settled", 0) == 1
    assert block["doesnt_connect"][0]["shortcut"] == "too_big"
    assert block["kinds_by_rung"]["1"] == {"discriminating": 1}
    assert any(row["suggested"] == suggestion["level"] and row["taken"] == 1 for row in block["taken_vs_suggested"])
    assert block["rungs_by_facet_and_week"]
    assert block["recovery_after_check"] == {"no_later_check": 1}
    blob = json.dumps(block)
    assert STEP_2 not in blob and (hint["hintMd"] or "x") not in blob

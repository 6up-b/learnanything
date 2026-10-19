"""RW2b fix round 10, item 4: one help-disabled RW2a sequence, run as a script
against EITHER the base code (``git archive 7d4c5f4ce``) or the tip, so a test
can require both to store the same counts (``test_reader_rw2b_fix10.py``).

Usage: ``python -m tests.rw2b_fix10_base_sequence <vault-dir>``; prints JSON.
Only APIs present at ``7d4c5f4ce`` are used. Fakes only: no model.
"""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys


def main(root: Path) -> dict:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    import learnloop.attempts.attempts as attempts_module
    from learnloop.config.schema import WorkbenchConfig
    import learnloop_sidecar.handlers.practice as practice
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.hint_fakes import ITEM, WORK, hint_vault
    from tests.split_live_helpers import ReadyRuntime
    from tests.test_stuck_prompt import StuckFake

    attempts_module.AUTO_PRIME_REVEAL_THRESHOLD = 10.0
    grader = StuckFake()
    practice.ready_grading_provider = lambda vault, override=None: ("fake", ReadyRuntime(), grader)

    def call(ctx, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    # Help switched off where the switch exists (the tip); the base has no RW2b help at all.
    config = "[workbench]\nhelp_enabled = false\n" if "help_enabled" in WorkbenchConfig.model_fields else ""
    paths = hint_vault(root, config=config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]

    def open_problem(origin, entry, **extra):
        view = call(ctx, "workbench.open", {"origin": origin, "entry": entry, "practiceItemId": ITEM,
                                            "stemMd": "Find P(X <= 1/2).", **extra})["session"]
        call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s0", "op": "add",
                                          "bodyMd": "F(x) = x^2 on [0, 1]", "afterStepId": None})
        return view["sessionId"]

    # The verify's item 4: A with the book counted, abandoned; B carrying one
    # authored reveal; A reopened; B submitted. Then an answer-box submit
    # with A still open and one authored reveal.
    first = open_problem("reader", "work_through")
    call(ctx, "workbench.abandon", {"sessionId": first})
    second = open_problem("practice", "practice_screen", carriedHints=1)
    call(ctx, "workbench.reopen", {"sessionId": first})
    attempt = call(ctx, "workbench.submit", {"sessionId": second, "practiceSessionId": session})["attempt"]
    box = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                       "attemptType": "independent_attempt", "hintsUsed": 1,
                                       "submissionId": "box-after"})
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        rows = {row[0]: (row[1], row[2], row[3]) for row in connection.execute(
            "SELECT id, hints_used, primed, attempt_type FROM practice_attempts")}
    return {"workbench_submit": rows[attempt["attemptId"]], "answer_box": rows[box["attemptId"]]}


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]))))

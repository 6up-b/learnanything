"""RW2b fix round 11, item 3: an independent answer-box attempt while another
process opens the book on the item's open problem during grading, run as a
script against EITHER the base code (``git archive 7d4c5f4ce``) or the code
under test, so a test can require both to store the same count and type
(``test_reader_rw2b_fix11.py``). Only APIs present at ``7d4c5f4ce``.

Usage: ``python -m tests.rw2b_fix11_base_sequence <vault-dir>``; prints JSON.
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

    config = "[workbench]\nhelp_enabled = false\n" if "help_enabled" in WorkbenchConfig.model_fields else ""
    paths = hint_vault(root, config=config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    # An open Reader problem with the book hidden ("Check me").
    problem = call(ctx, "workbench.open", {"origin": "reader", "entry": "check_me", "practiceItemId": ITEM,
                                           "stemMd": "Find P(X <= 1/2)."})["session"]["sessionId"]
    real = practice._server_hint_fold
    opened = []

    def fold_then_open_the_book(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not opened:
            opened.append(call(ctx, "workbench.set_book", {"sessionId": problem, "visible": True}))
        return fold

    practice._server_hint_fold = fold_then_open_the_book
    attempt = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                           "attemptType": "independent_attempt", "hintsUsed": 0,
                                           "submissionId": "box-book-during-grading"})
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        row = connection.execute("SELECT hints_used, primed, attempt_type FROM practice_attempts WHERE id = ?",
                                 (attempt["attemptId"],)).fetchone()
    book = opened[0]["session"]["record"]["bookCounted"] if opened else None
    return {"attempt": list(row), "book_counted_during_grading": book}


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]))))

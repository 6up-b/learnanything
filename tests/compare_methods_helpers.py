"""What other test files use from ``tests/test_compare_methods.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.db.connection import connect

from tests.approach_map_fakes import add_attempt, write_item
from tests.workbench_help_fakes import STEP_1, STEP_2, CheckFake, open_problem, sidecar


SIBLING = "pi_cdf_2"


def _lines(context):
    steps = [entry["step"] for entry in context["steps"]]
    return {"learner_route_valid": True, "same_method": False, "differences": [
        {"kind": "method", "learner_step": steps[0], "line": "You took the CDF first; the book integrates directly."},
        {"kind": "step", "learner_step": 99, "line": "A step that does not exist."},
        {"kind": "assumption", "learner_step": 0, "line": "The book assumes the support is [0, 1]."},
    ]}


def _submitted(tmp_path, *, correctness=1.0, config=""):
    """A workbench problem submitted with ``correctness`` (the attempt and
    the session's submitted state written as the submit leaves them)."""

    paths, ctx, _session = sidecar(tmp_path, config, check=CheckFake([_lines] * 4))
    write_item(paths, SIBLING, family_id="fam_cdf")
    ctx.load(paths.root)
    wb, _chains = open_problem(ctx)
    created = utc_now_iso(FrozenClock(datetime.now(UTC) - timedelta(minutes=5)))
    add_attempt(paths.sqlite_path, "att_wb", correctness=correctness, answer=f"{STEP_1}\n{STEP_2}",
                created_at=created)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE workbench_sessions SET status = 'submitted', attempt_id = 'att_wb' WHERE id = ?",
                           (wb,))
        connection.commit()
    return paths, ctx, wb

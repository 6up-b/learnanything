"""Reader workbench RW2b: the switch-off pins (spec_reader_workbench_v1 §5.9, W3, W11).

With ``workbench.help_enabled`` off every RW2b RPC refuses before reading or
writing, and the RW2a workbench is byte-identical: the same config DTO
``workbench`` key, the same session views and record line, the same submit,
no help rows. With it on and no help taken the workbench reads as RW2a's
apart from the DTO's ``help`` key. Fakes only.
"""

from __future__ import annotations

from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, help_rows, open_problem, sidecar


def _shape(tmp_path, config):
    paths, ctx, session = sidecar(tmp_path, config)
    snapshot = ctx.app_snapshot()["config"]
    wb, chains = open_problem(ctx)
    view = call(ctx, "workbench.get", {"sessionId": wb})["session"]
    left = call(ctx, "workbench.leave", {"sessionId": wb})["session"]
    submitted = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})
    strip = ("sessionId", "createdAt", "updatedAt", "closedAt", "attemptId", "practiceSessionId", "steps",
             "lastEditedStepId")
    return {
        "workbench_key": snapshot.get("workbench"),
        "view": {key: value for key, value in view.items() if key not in strip},
        "left": {key: value for key, value in left.items() if key not in strip},
        "submitted": {key: value for key, value in submitted["session"].items() if key not in strip},
        "attempt_keys": sorted(submitted["attempt"]),
        "help_rows": help_rows(paths),
    }


def test_switched_off_the_rw2a_workbench_is_byte_identical(tmp_path, grader):
    off = _shape(tmp_path / "off", "[workbench]\nhelp_enabled = false\n")
    on = _shape(tmp_path / "on", "")
    assert off["workbench_key"] == {"enabled": True, "openSessionDays": 30}
    # RW2b fix round 13: the help block carries the symbolic switch (off by default).
    assert on["workbench_key"] == {**off["workbench_key"], "help": {"enabled": True, "bridge": True,
                                                                     "symbolic": False}}
    for key in ("view", "left", "submitted", "attempt_keys", "help_rows"):
        assert on[key] == off[key], key
    assert "help" not in off["view"]["record"]

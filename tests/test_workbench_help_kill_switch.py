"""Reader workbench RW2b: the switch-off pins (spec_reader_workbench_v1 §5.9, W3, W11).

With ``workbench.help_enabled`` off every RW2b RPC refuses before reading or
writing, and the RW2a workbench is byte-identical: the same config DTO
``workbench`` key, the same session views and record line, the same submit,
no help rows. With it on and no help taken the workbench reads as RW2a's
apart from the DTO's ``help`` key. Fakes only.
"""

from __future__ import annotations

from tests.hint_h2b_review_helpers import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, help_rows, open_problem, sidecar


def _shape(tmp_path, config):
    paths, ctx, session = sidecar(tmp_path, config)
    snapshot = ctx.app_snapshot()["config"]
    wb, chains = open_problem(ctx)
    view = call(ctx, "workbench.get", {"sessionId": wb})["session"]
    left = call(ctx, "workbench.leave", {"sessionId": wb})["session"]
    submitted = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})
    # The served contract's version id is a fresh ULID per vault, like the session ids (at the head every
    # served item snapshots its assessment contract, so it is set on both sides; below, it was None).
    assert view["assessmentContractVersionId"] is not None
    strip = ("sessionId", "createdAt", "updatedAt", "closedAt", "attemptId", "practiceSessionId", "steps",
             "lastEditedStepId", "assessmentContractVersionId")
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
    # IH6 (the head's tag, failure_share_tag) adds ``openItem`` beside RW2a's keys, whatever the help switch.
    assert off["workbench_key"] == {"enabled": True, "openSessionDays": 30, "openItem": True}
    # RW2b fix round 13: the help block carries the symbolic switch (off by default).
    # Reader RW2c's three DTO flags are on by default (present only while on).
    assert on["workbench_key"] == {**off["workbench_key"], "help": {"enabled": True, "bridge": True,
                                                                     "symbolic": False, "examples": True,
                                                                     "compareMethods": True, "passageDraw": True}}
    for key in ("view", "left", "submitted", "attempt_keys", "help_rows"):
        assert on[key] == off[key], key
    assert "help" not in off["view"]["record"]

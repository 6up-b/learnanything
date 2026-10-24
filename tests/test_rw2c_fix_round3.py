"""Reader workbench RW2c, fix round 3 (orchestrator verify of a1027ed04): one Medium and four Low.

M1. A worked example's unaided progress reads the verdicts standing at its
    delivery (its own, its hint's, or the last shown check before it); none
    on record is ``unknown``. A reworded step that was already valid is not
    progress for the hint or for its example (the reviewer's probe).
L4. The compare worker uses the LIVE vault and switch: a switch-off between
    opening the comparison and the model call makes no call.
L8. An example that cannot start never fails the read of a delivered hint.
L6. The compare RPCs pass the workbench's withheld-exercise gate.

Fakes only: no model is called.
"""

from __future__ import annotations

from contextlib import closing
import json
import threading

import pytest

from learnloop.db.connection import connect
from learnloop.hints.report_workbench import workbench_unaided_progress
from learnloop.workbench import compare_methods
from learnloop.workbench.help_outcomes import help_outcomes
from tests.hint_fakes import WriterFake, reveals
from tests.test_compare_methods import _submitted
from tests.test_help_outcomes import FACET, _facets, _insert, _only, _row
from tests.test_rw2c_fix_round2 import _Spans, _span
from tests.test_workbench_route_example import ROUTE, FindFake
from tests.workbench_help_fakes import CheckFake, call, help_rows, open_problem, run_job, sidecar, wb_answer


def _verdicts(entries):
    return json.dumps([{"chain_id": chain, "verdict": verdict, "hash": hash_} for chain, verdict, hash_ in entries])


def _snapshot(entries):
    return json.dumps([{"chain_id": chain, "number": index, "hash": hash_}
                       for index, (chain, _verdict, hash_) in enumerate(entries, start=1)])


# -- M1: the reviewer's probe ---------------------------------------------------------------------


def test_m1_rewording_an_already_valid_step_is_progress_for_neither_the_hint_nor_its_example(tmp_path):
    """a valid, b questionable, c valid; a hint about b (continuing from a),
    its worked example, then the next check only rewords c (still valid, b
    still questionable): neither the hint nor the example continued."""

    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    delivered = [("a", "valid", "h_a"), ("b", "questionable", "h_b"), ("c", "valid", "h_c")]
    later = [("a", "valid", "h_a"), ("b", "questionable", "h_b"), ("c", "valid", "h_c_reworded")]
    _insert(paths, [
        _row("ha_c1", wb, "check", 0, step_verdicts_json=_verdicts(delivered), step_snapshot_json=_snapshot(delivered),
             first_questionable_step_id="b"),
        _row("ha_h", wb, "hint", 1, hint_kind="next_step", level=3, about_step_id="b", continue_from_step_id="a",
             step_snapshot_json=_snapshot(delivered), step_verdicts_json=_verdicts(delivered)),
        # The example as a1027ed04 wrote it: a snapshot, no verdicts of its own.
        _row("ha_ex", wb, "example", 1, about_step_id="b", step_snapshot_json=_snapshot(delivered),
             placement_json=json.dumps({"hint_assist_id": "ha_h", "trigger": "after_hint", "status": "found",
                                        "role": "worked_example"}), shown_at="2026-10-20T10:01:30Z"),
        _row("ha_c2", wb, "check", 2, step_verdicts_json=_verdicts(later), step_snapshot_json=_snapshot(later)),
    ])
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T10:30:00Z", item_facets=_facets(paths))
    assert dict(_only(result, "hint", "next_step").continuation) == {"not_continued": 1}
    assert dict(_only(result, "example").continuation) == {"not_continued": 1}


def _rows(example: dict, *, check_before: bool) -> list[dict]:
    delivered = [("a", "valid", "h_a"), ("b", "questionable", "h_b")]
    later = [("a", "valid", "h_a2"), ("b", "questionable", "h_b")]
    rows = []
    if check_before:
        rows.append({"id": "ha_c0", "assist_kind": "check", "shown": 1, "shown_at": "2026-10-20T10:00:00Z",
                     "step_verdicts_json": _verdicts(delivered), "step_snapshot_json": _snapshot(delivered)})
    rows.append({"id": "ha_ex", "assist_kind": "example", "shown": 1, "shown_at": "2026-10-20T10:01:00Z",
                 "placement_json": json.dumps({"trigger": "show_me"}), "step_snapshot_json": _snapshot(delivered),
                 **example})
    rows.append({"id": "ha_c1", "assist_kind": "check", "shown": 1, "shown_at": "2026-10-20T10:02:00Z",
                 "step_verdicts_json": _verdicts(later), "step_snapshot_json": _snapshot(later)})
    return rows


def test_m1_a_show_me_example_with_no_verdicts_on_record_is_unknown_never_continued():
    rows = _rows({}, check_before=False)
    assert workbench_unaided_progress(rows[0], rows) == "unknown"


def test_m1_a_show_me_example_reads_its_own_verdicts_or_the_last_check_before_it():
    # The last shown check before it: step a was valid then, its rewording is not progress.
    rows = _rows({}, check_before=True)
    assert workbench_unaided_progress(rows[1], rows) == "not_continued"
    # Its own stored verdicts (the new rows): the same answer.
    own = _rows({"step_verdicts_json": _verdicts([("a", "valid", "h_a"), ("b", "questionable", "h_b")])},
                check_before=False)
    assert workbench_unaided_progress(own[0], own) == "not_continued"


def _reader(tmp_path, hits):
    paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = _Spans([_span("s1")])
    ctx.workbench_example_find = FindFake(hits)
    wb, chains = open_problem(ctx, origin="reader", entry="work_through")
    return paths, ctx, wb, chains


def test_m1_example_rows_store_the_verdicts_they_were_searched_against(tmp_path):
    paths, ctx, wb, chains = _reader(tmp_path, [ROUTE])
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    call(ctx, "workbench.help_job", {"jobId": hint["exampleJobId"]})
    run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb, "focusedStepId": chains[1]}))
    rows = help_rows(paths, wb)
    [hint_row] = [row for row in rows if row["assist_kind"] == "hint"]
    after_hint, show_me = [row for row in rows if row["assist_kind"] == "example"]
    assert hint_row["step_verdicts_json"] and after_hint["step_verdicts_json"] == hint_row["step_verdicts_json"]
    stored = json.loads(show_me["step_verdicts_json"])
    assert {entry["chain_id"] for entry in stored} == set(chains)


# -- L4: the compare worker reads the live switch -------------------------------------------------


def test_l4_switching_compare_methods_off_after_the_open_makes_no_call(tmp_path, monkeypatch):
    paths, ctx, _wb = _submitted(tmp_path)
    ctx.workbench_check_client = CheckFake([lambda context: {"learner_route_valid": True, "same_method": True,
                                                             "differences": []}])
    real = compare_methods._steps
    entered, release = threading.Event(), threading.Event()

    def held_steps(repository, session_id):
        if threading.current_thread() is not threading.main_thread():
            entered.set()
            assert release.wait(20)
        return real(repository, session_id)

    monkeypatch.setattr(compare_methods, "_steps", held_steps)
    ctx.hints_inline = False
    opened = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    assert opened["linesJobId"] and entered.wait(20)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text() + "\n[workbench]\ncompare_methods_enabled = false\n")
    ctx.reload()
    release.set()
    job = ctx.workbench_help_jobs.get(opened["linesJobId"])
    assert job.done.wait(20)
    assert ctx.workbench_check_client.contexts == []
    assert (job.result or {}).get("reason") == "disabled"
    ctx.hints_inline = True


# -- L8: a failing example start never fails a delivered hint's read ------------------------------


def test_l8_an_example_that_cannot_start_never_fails_the_delivered_hints_read(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import workbench_rw2c

    def broken(*args, **kwargs):
        raise RuntimeError("example start failed")

    monkeypatch.setattr(workbench_rw2c, "start_example_after_hint", broken)
    _paths, ctx, wb, _chains = _reader(tmp_path, [ROUTE])
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert hint["status"] == "ready" and hint["shown"] is True
    assert hint["bridgeJobId"] and hint["exampleJobId"] is None
    assert ctx.workbench_example_find.calls == []


# -- L6: the compare RPCs pass the withheld-exercise gate -----------------------------------------


def test_l6_the_compare_rpcs_refuse_a_problem_whose_exercise_is_withheld_now(tmp_path, monkeypatch):
    from learnloop.reader import workbench as WB

    paths, ctx, _wb = _submitted(tmp_path)
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_wb"})["available"] is True
    monkeypatch.setattr(WB, "statement_cleared", lambda vault, repository, session: False)
    for name in ("workbench.compare_offer", "workbench.compare_methods"):
        with pytest.raises(Exception) as refused:
            call(ctx, name, {"attemptId": "att_wb"})
        assert getattr(refused.value, "code", None) == "exercise_withheld", name
    vault, repository = ctx.require_vault()
    # The domain read refuses too (any caller), before the reference is read.
    assert compare_methods.offer(vault, repository, "att_wb") == {"available": False, "reason": "exercise_withheld"}
    with pytest.raises(compare_methods.CompareRefused):
        compare_methods.open_comparison(vault, repository, "att_wb")
    assert reveals(paths.sqlite_path) == []
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM help_assists WHERE assist_kind = 'compare_methods'"
                                  ).fetchone()[0] == 0

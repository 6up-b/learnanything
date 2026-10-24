"""Reader workbench RW2c, fix round 2 (orchestrator verify of bf7f9926c): three High and five Medium.

1. After waiting for its bridge, the example worker re-checks its cancel
   flag and the CURRENT vault (switches, routes, caps) before it reserves
   or searches.
2. "another passage" revalidates a cached option against the current exam,
   held-out and item-bound exclusions before delivery, with no model call.
3. With RW2c's switches off, a problem with RW2c history restores exactly
   the base code's payload (7e7bdff1b).
4. A bridge draws only between the spans T6's judge passed (the manifest's
   ``span_keys``), never a referenced block appended after verification.
5. S5's outcomes at ``as_of`` come from S5's own historical read (inputs and
   grades as they stood then, expiry judged then), linked and standalone.
6. A hint's "continued" is progress where it was placed (its next step, its
   target node, its questionable step), never an unrelated earlier edit.
7. The book a drawn bridge passage is in survives the result, the stored
   placement, the restored view and a resumed pick.

Fakes only: no model is called.
"""

from __future__ import annotations

from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

import pytest

from learnloop.db.connection import connect
from learnloop.hints.report_workbench import workbench_unaided_progress
from learnloop.workbench.help_outcomes import help_outcomes
from tests.approach_map_fakes import ITEM, LO
from tests.hint_fakes import WriterFake
from tests.rw2c_base_sequence import SWITCHES
from tests.test_help_outcomes import FACET, _facets, _grading, _insert, _only, _row, _snapshot, _vault, _verdicts, _world
from tests.test_workbench_route_example import ROUTE, FindFake
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar, wb_answer

ROOT = Path(__file__).resolve().parents[1]
BASE = "7e7bdff1b"


def _switches_off(paths) -> None:
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text() + "\n[workbench]\n" + "".join(f"{name} = false\n" for name in SWITCHES))


class _Spans:
    """T6's ``TutorSpanProvider`` faked: verified picks named by the manifest's
    ``span_keys`` and, optionally, referenced blocks appended after them."""

    def __init__(self, verified, referenced=()):
        self.verified = [dict(span) for span in verified]
        self.referenced = [dict(span, relation="referenced") for span in referenced]
        self.calls = 0

    def __call__(self, vault, repository, *, context, question_md, learning_object_ids, item):
        self.calls += 1
        return self.verified + self.referenced, {
            "basis": "retrieved_verified",
            "span_keys": [f"{span['extraction_id']}/{span['span_id']}" for span in self.verified]}


def _span(span_id, extraction_id="ext", **extra):
    return {"span_id": span_id, "extraction_id": extraction_id, "label": f"Book · §{span_id}", "text": "a step",
            **extra}


# -- 1 (High): the example after a hint re-reads the live vault after its wait ----------------


@pytest.mark.parametrize("how", ["switches_off", "cancelled"])
def test_fr2_1_an_example_waiting_on_its_bridge_never_searches_after_switch_off_or_cancel(tmp_path, monkeypatch,
                                                                                            how):
    import learnloop.workbench.bridge as bridge_module

    real = bridge_module.bridge_for_hint
    release = threading.Event()

    def held_bridge(*args, **kwargs):
        assert release.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(bridge_module, "bridge_for_hint", held_bridge)
    paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = _Spans([_span("s1")])
    ctx.workbench_example_find = FindFake([ROUTE])
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    # Threaded jobs: the delivering read starts the bridge and the example,
    # and the example waits on the (held) bridge.
    ctx.hints_inline = False
    started = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    jobs = ctx.workbench_help_jobs
    assert jobs.get(started["jobId"]).done.wait(30)
    hint = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["result"]
    assert hint["shown"] is True and hint["bridgeJobId"] and hint["exampleJobId"]
    example = jobs.get(hint["exampleJobId"])
    assert not example.done.is_set()
    if how == "switches_off":
        _switches_off(paths)
        ctx.reload()
    else:
        assert call(ctx, "workbench.cancel_help", {"jobId": hint["exampleJobId"]})["cancelled"] is True
    release.set()
    assert jobs.get(hint["bridgeJobId"]).done.wait(30)
    assert example.done.wait(90)
    assert ctx.workbench_example_find.calls == []
    assert not [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    assert (example.result or {}).get("status") == "unavailable"
    ctx.hints_inline = True


# -- 2 (High): "another passage" revalidates the cached option now -----------------------------


def _drawn_example(tmp_path, hits):
    paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = _Spans([])
    ctx.workbench_example_find = FindFake(hits)
    ctx.passage_draw_seed = "seed-fr2"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    shown = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    assert shown["status"] == "ready" and shown["alternatives"] == len(hits) - 1
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    options = [option["option_id"] for option in json.loads(row["options_json"])]
    return paths, ctx, wb, shown, options


THREE_BOOKS = [dict(ROUTE, span_id=f"w{index}", extraction_id=f"ext_{name}", section=f"3.{index}")
               for index, name in enumerate(("a", "b", "c"), start=1)]


def _hold_out(monkeypatch, extraction_ids):
    """The one exam predicate now says these extractions' chapters are held
    out (an owner's held-out mark made after the draw)."""

    from learnloop.source_retrieval import corpus

    real = corpus.exam_withheld
    monkeypatch.setattr(corpus, "exam_withheld", lambda vault, repository, keys: frozenset(
        key for key in keys if key[0] in extraction_ids) | real(vault, repository, keys))


def test_fr2_2_another_passage_skips_an_option_held_out_since_the_draw(tmp_path, monkeypatch):
    paths, ctx, wb, shown, options = _drawn_example(tmp_path, THREE_BOOKS)
    at = options.index(f"{shown['extractionId']}:{shown['spanId']}")
    unshown_next, after_it = options[(at + 1) % 3], options[(at + 2) % 3]
    _hold_out(monkeypatch, {unshown_next.split(":")[0]})
    calls = len(ctx.workbench_example_find.calls)
    picked = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": shown["assistId"]})["passage"]
    # The held-out option is skipped for the next one; nothing is searched.
    assert f"{picked['extractionId']}:{picked['spanId']}" == after_it
    assert len(ctx.workbench_example_find.calls) == calls


def test_fr2_2_another_passage_is_refused_when_every_other_option_is_withheld_now(tmp_path, monkeypatch):
    paths, ctx, wb, shown, options = _drawn_example(tmp_path, THREE_BOOKS[:2])
    [other] = [option for option in options if option != f"{shown['extractionId']}:{shown['spanId']}"]
    _hold_out(monkeypatch, {other.split(":")[0]})
    before = len(help_rows(paths, wb))
    with pytest.raises(Exception) as refused:
        call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": shown["assistId"]})
    assert getattr(refused.value, "code", None) == "no_alternatives"
    assert getattr(refused.value, "details", {}) == {"reason": "withheld"}
    assert len(help_rows(paths, wb)) == before  # no pick row: nothing was shown


def test_fr2_2_an_option_that_is_now_the_items_own_passage_or_reproduces_its_answer_is_withheld(tmp_path,
                                                                                                monkeypatch):
    from learnloop.source_retrieval import corpus
    from learnloop.workbench import passage_draw

    paths, ctx, wb, shown, _options = _drawn_example(tmp_path, THREE_BOOKS[:2])
    vault, repository = ctx.require_vault()
    item = vault.practice_items[ITEM]
    option = {"option_id": "ext_b:w2", "extraction_id": "ext_b", "span_id": "w2"}
    assert passage_draw.option_withheld(vault, repository, item, option, workbench_session_id=wb) is None
    real = corpus.item_exclusions
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: type(real(repository, item))(
        extractions=frozenset({"ext_b"}), spans=frozenset()))
    assert passage_draw.option_withheld(vault, repository, item, option, workbench_session_id=wb) == "item_linked"
    assert passage_draw.option_withheld(vault, repository, item, {**option, "extraction_id": "ext_a",
                                                                   "option_id": "ext_a:w2", "role": "solution"},
                                        workbench_session_id=wb) == "exercise_or_solution"


# -- 3 (High): switched off, RW2c history serializes as the base code ---------------------------


def _run_state(code_root: Path, vault_root: Path, session_id: str) -> dict:
    script = code_root / "tests" / "rw2c_state_parity.py"
    if not script.exists():
        script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "tests" / "rw2c_state_parity.py", script)
    env = {**os.environ, "PYTHONPATH": str(code_root / "src")}
    done = subprocess.run([sys.executable, "-m", "tests.rw2c_state_parity", str(vault_root), session_id],
                          cwd=code_root, env=env, capture_output=True, text=True, timeout=600)
    assert done.returncode == 0, done.stderr[-3000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_fr2_3_with_every_switch_off_a_problem_with_rw2c_history_restores_the_base_payload(tmp_path):
    if shutil.which("git") is None or subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", BASE],
                                                     capture_output=True).returncode != 0:
        pytest.skip(f"git or commit {BASE} is not available")
    paths, ctx, _session = sidecar(tmp_path / "vault", writer=WriterFake([wb_answer] * 8))
    # History made with RW2c on: a drawn bridge in Book B and a pick on it, a
    # drawn worked example under the hint and a "show me" one.
    ctx.workbench_bridge_provider = _Spans([_span(f"s{index}", "ext_b", source_id="src_b") for index in (1, 2, 3)])
    ctx.workbench_example_find = FindFake([dict(ROUTE, source_id="src_b"),
                                           dict(ROUTE, span_id="w4", section="3.6", source_id="src_b")])
    ctx.passage_draw_seed = "seed-history"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    hint_job = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    hint = run_job(ctx, hint_job)
    assert hint["exampleJobId"]
    bridge = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    assert bridge["alternatives"] == 2
    call(ctx, "workbench.help_job", {"jobId": hint["exampleJobId"]})
    call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": bridge["assistId"]})
    run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    on = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert on["hints"][0]["bridge"]["alternatives"] == 2 and on["examples"]
    _switches_off(paths)
    # Against the base code's serializer, on the same database.
    base = tmp_path / "base"
    base.mkdir()
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", BASE, "src", "tests", "migrations"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive, check=True)
    at_base = _run_state(base, paths.root, wb)
    import learnloop

    at_tip = _run_state(Path(learnloop.__file__).resolve().parents[2], paths.root, wb)
    assert at_base["help_state"]["hints"] and at_base["help_state"]["hints"][0]["bridge"]
    for key in ("help_state", "problem"):
        assert at_tip[key] == at_base[key], key
    # In process, after a reload: the restored state carries no RW2c key.
    ctx.reload()
    off = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert set(off["hints"][0]["bridge"]) == {"assistId", "line", "spanId", "extractionId", "label"}
    assert "example" not in off["hints"][0] and "examples" not in off
    # A cached bridge job read again after the switch-off is the base's too.
    again = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    assert not {"alternatives", "sourceId"} & set(again)
    hint_again = call(ctx, "workbench.help_job", {"jobId": hint_job["jobId"]})["result"]
    assert hint_again["bridgeJobId"] and "exampleJobId" not in hint_again


# -- 4 (Medium): bridge draws only between judged spans -----------------------------------------


def _bridge(tmp_path, provider):
    paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = provider
    ctx.passage_draw_seed = "seed-fr2-4"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    result = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    return ctx, wb, result, row


def test_fr2_4_a_referenced_block_appended_after_verification_is_never_a_draw_option(tmp_path):
    _ctx, _wb, result, row = _bridge(tmp_path, _Spans([_span("s1")], referenced=[_span("r9")]))
    # One judged passage: no draw, the judged one shown, nothing logged.
    assert result["spanId"] == "s1" and "alternatives" not in result
    assert (row["options_json"], row["propensity"], row["seed"]) == (None, None, None)


def test_fr2_4_the_draw_is_between_the_judged_spans_only(tmp_path):
    _ctx, _wb, result, row = _bridge(tmp_path / "two", _Spans([_span("s1"), _span("s2")], referenced=[_span("r9")]))
    assert [option["span_id"] for option in json.loads(row["options_json"])] == ["s1", "s2"]
    assert row["propensity"] == pytest.approx(0.5) and result["alternatives"] == 1


# -- 5 (Medium): S5 outcomes at as_of from S5's historical read ---------------------------------


def _rebuild_s5(paths) -> None:
    from learnloop.db.repositories import Repository
    from learnloop.substrate.intervention_outcomes import rebuild_intervention_outcomes

    repository = Repository.attach(paths.sqlite_path)
    with repository.atomic():
        rebuild_intervention_outcomes(_vault(paths), repository)


def _s5_row(paths, intervention_id: str) -> dict:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return dict(connection.execute("SELECT * FROM retrieval_intervention_outcomes WHERE intervention_id = ?",
                                       (intervention_id,)).fetchone())


def test_fr2_5_an_s5_record_read_before_its_censoring_horizon_is_pending_not_expired(tmp_path):
    from learnloop.db.stores.source_service import insert_intervention

    paths, _ctx, _wb = _world(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        insert_intervention(connection, id="ri_old", created_at="2026-09-01T09:00:00Z", kind="source_passage",
                            caller_kind="tutor", targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.commit()
    _rebuild_s5(paths)
    # Today's persisted reading (reference time Oct 20): past the horizon.
    assert _s5_row(paths, "ri_old")["cold_outcome_state"] == "right_censored_expired"
    early = help_outcomes(paths.sqlite_path, [FACET], "2026-09-10T00:00:00Z", item_facets=_facets(paths),
                          vault=_vault(paths))
    [retrieval] = [entry for entry in early.helps if entry.help == "retrieval"]
    assert dict(retrieval.later_independent) == {"pending": 1}


def test_fr2_5_a_later_regrade_never_changes_s5s_outcome_at_as_of_linked_or_standalone(tmp_path):
    """The cold attempt was graded 1/4 at noon and regraded 4/4 at 14:00; S5
    rebuilt after it reads a success today. At 13:00 it was a failure, for
    the standalone S5 record and for the workbench example S5 names."""

    from learnloop.db.stores.source_service import insert_intervention

    paths, _ctx, wb = _world(tmp_path)
    _insert(paths, [_row("ha_ex", wb, "example", 0, placement_json=json.dumps(
        {"trigger": "show_me", "status": "found", "role": "worked_example"}),
        requested_at="2026-10-19T11:30:00Z", shown_at="2026-10-19T11:30:00Z")])
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET latency_seconds = 60, evidence_facets_json = ? "
                           "WHERE id = 'att_later'", (json.dumps([FACET]),))
        for ident, ref in (("ri_tutor", None), ("ri_ex", "ha_ex")):
            insert_intervention(connection, id=ident, created_at="2026-10-19T11:30:00Z", kind="source_passage",
                                caller_kind="workbench" if ref else "tutor", caller_ref=ref,
                                targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.commit()
    _grading(paths, "att_later", points=1.0, at="2026-10-20T12:00:00Z", revision=0,
             superseded_at="2026-10-20T14:00:00Z")
    _grading(paths, "att_later", points=4.0, at="2026-10-20T14:00:00Z", revision=1)
    _rebuild_s5(paths)
    assert _s5_row(paths, "ri_tutor")["cold_outcome_state"] == "cold_success"  # today's reading
    vault = _vault(paths)
    then = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths), vault=vault)
    [retrieval] = [entry for entry in then.helps if entry.help == "retrieval"]
    assert (dict(retrieval.later_independent), dict(_only(then, "example").later_independent)) == (
        {"fail": 1}, {"fail": 1})
    now = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T15:00:00Z", item_facets=_facets(paths), vault=vault)
    [retrieval] = [entry for entry in now.helps if entry.help == "retrieval"]
    assert dict(retrieval.later_independent) == {"pass": 1}


def test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone(tmp_path):
    """S5's replayer is unchanged: the historical read at the replayer's own
    reference time, with today's grades, gives the persisted rows."""

    from datetime import datetime

    from learnloop.db.stores.source_service import insert_intervention
    from learnloop.held_grades import held_for_review_attempts
    from learnloop.substrate.intervention_outcomes import outcomes_as_of

    paths, _ctx, _wb = _world(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET latency_seconds = 60, evidence_facets_json = ? "
                           "WHERE id = 'att_later'", (json.dumps([FACET]),))
        insert_intervention(connection, id="ri_1", created_at="2026-10-19T11:30:00Z", kind="source_passage",
                            caller_kind="tutor", targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.commit()
    _rebuild_s5(paths)
    persisted = _s5_row(paths, "ri_1")
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        held = held_for_review_attempts(connection)
        grades = {row["id"]: (row["correctness"], row["id"] in held)
                  for row in connection.execute("SELECT id, correctness FROM practice_attempts")}
        read = outcomes_as_of(_vault(paths), connection, datetime.fromisoformat(persisted["as_of"]), grades=grades)
    for column in ("next_attempt_id", "next_correctness", "cold_attempt_id", "cold_outcome_state"):
        assert read["ri_1"].get(column) == persisted[column], column


# -- 6 (Medium): continuation is progress where the hint was placed -----------------------------


def test_fr2_6_an_unrelated_edit_to_an_earlier_valid_step_is_not_progress_after_a_waypoint(tmp_path):
    def rows(wb, one, two):
        delivered = _verdicts(one, questionable=two)
        return [
            _row("ha_c1", wb, "check", 0, step_verdicts_json=delivered, step_snapshot_json=_snapshot(one, two),
                 first_questionable_step_id=two),
            _row("ha_w", wb, "hint", 1, hint_kind="waypoint", level=3, continue_from_step_id=one,
                 target_node_id="n_goal", step_snapshot_json=_snapshot(one, two), step_verdicts_json=delivered),
            # Step 1 (valid at delivery) is reworded; the target is still not reached.
            _row("ha_c2", wb, "check", 2, step_verdicts_json=_verdicts(one, questionable=two,
                                                                         hashes={one: "h_one_reworded"}),
                 step_snapshot_json=_snapshot(one, two, hashes={one: "h_one_reworded"})),
        ]

    paths, ctx, _session = sidecar(tmp_path)
    wb, (one, two) = open_problem(ctx)
    _insert(paths, rows(wb, one, two))
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T10:30:00Z", item_facets=_facets(paths))
    assert dict(_only(result, "hint", "waypoint").continuation) == {"not_continued": 1}


def _progress(hint: dict, following: dict) -> str:
    rows = [{"id": "ha_h", "assist_kind": "hint", "shown": 1, "shown_at": "2026-10-20T10:01:00Z", **hint},
            {"id": "ha_c", "assist_kind": "check", "shown": 1, "shown_at": "2026-10-20T10:02:00Z", **following}]
    return workbench_unaided_progress(rows[0], rows)


def _verdict(chain, verdict="valid", hash_=None, node=None):
    return {"chain_id": chain, "verdict": verdict, "hash": hash_ or f"h_{chain}",
            **({"map_node_id": node} if node else {})}


def test_fr2_6_progress_is_measured_where_the_hint_was_placed():
    delivered = {"step_snapshot_json": _snapshot("a", "b"),
                 "step_verdicts_json": json.dumps([_verdict("a"), _verdict("b", "questionable")])}
    snapshot_abc = _snapshot("a", "b", "c")
    # The waypoint's target reached by a new step: continued.
    waypoint = {**delivered, "hint_kind": "waypoint", "continue_from_step_id": "a", "target_node_id": "n3"}
    reached = {"step_snapshot_json": snapshot_abc,
               "step_verdicts_json": json.dumps([_verdict("a"), _verdict("b", "questionable"),
                                                 _verdict("c", node="n3")])}
    assert _progress(waypoint, reached) == "continued"
    # Only step a (valid at delivery, before the placement) reworded: not progress.
    reworded = {"step_snapshot_json": _snapshot("a", "b", hashes={"a": "h_a2"}),
                "step_verdicts_json": json.dumps([_verdict("a", hash_="h_a2"), _verdict("b", "questionable")])}
    assert _progress(waypoint, reworded) == "not_continued"
    # The questionable step it was about, fixed: continued.
    about = {**delivered, "hint_kind": "next_step", "about_step_id": "b", "continue_from_step_id": "a"}
    fixed = {"step_snapshot_json": _snapshot("a", "b", hashes={"b": "h_b2"}),
             "step_verdicts_json": json.dumps([_verdict("a"), _verdict("b", hash_="h_b2")])}
    assert _progress(about, fixed) == "continued"
    # A new step after the one it continues from (its next step): continued.
    nxt = {"step_snapshot_json": snapshot_abc,
           "step_verdicts_json": json.dumps([_verdict("a"), _verdict("b", "questionable"), _verdict("c")])}
    assert _progress(about, nxt) == "continued"
    # Nothing recorded at delivery: still unknown.
    assert _progress({"hint_kind": "next_step"}, nxt) == "unknown"


# -- 7 (Medium): book identity through drawn results, placement, views and picks ----------------


def test_fr2_7_a_drawn_bridge_in_book_b_names_book_b_initially_and_after_a_resumed_pick(tmp_path):
    spans = [_span(f"s{index}", "ext_b", source_id="src_b") for index in (1, 2)]
    ctx, wb, result, row = _bridge(tmp_path, _Spans(spans))
    assert (result["sourceId"], result["extractionId"]) == ("src_b", "ext_b") and result["alternatives"] == 1
    assert json.loads(row["placement_json"])["source_id"] == "src_b"
    restored = call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]["bridge"]
    assert (restored["sourceId"], restored["extractionId"]) == ("src_b", "ext_b")
    picked = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": result["assistId"]})["passage"]
    assert picked["sourceId"] == "src_b"
    resumed = call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]["bridge"]
    assert (resumed["assistId"], resumed["sourceId"], resumed["extractionId"]) == (
        picked["assistId"], "src_b", "ext_b")

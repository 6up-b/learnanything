"""Follow-ups batch 6, scoped Codex verify fixes V1 and V2.

V1: a prebuild's rich job never asks the plan again, sends or stores while its saved context
touches a passage of an item the stored day plan holds open, on the Reader's retry path and in
the worker too (one core: ``service.item_passages`` always reads the stored plan). V2: a pass's
plan-wait retries run only when the pass carries real learner activity: the gap worker's passes
(poll ticks, deferred drains) and Today's reads (which background work can fire) never retry.

Fakes only: the judge, the authors, the renderer and the power reader are injected; real rows in
synthetic vaults; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.clock import FrozenClock
from learnloop.daily_plan import records as RECORDS
from learnloop.daily_plan.engine import PlanEnv, load_records
from learnloop.db.stores import daily_plans as PLAN_STORE
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.source_retrieval import corpus
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, call, context, flagship
from tests.test_figure_rich_job import WHY
from tests.test_figure_rich_rpc import _ctx
from tests.test_figures_prefetch import TWO, JudgeFake, make_vault
from tests.test_followups_batch6_prefetch_plan_wait import _env, _pass, _prebuild_jobs, _rig, _waiting


@pytest.fixture(autouse=True)
def mains(monkeypatch):
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    yield
    P.set_power_reader(None)


def _today() -> str:
    return datetime.now(UTC).astimezone().date().isoformat()


def _plan_row(connection, plan_id: str, local_date: str, created_at: str, *, split_json: object = None) -> None:
    PLAN_STORE.insert_plan(connection, {
        "id": plan_id, "local_date": local_date, "kind": "normal", "minutes_budget": 25.0, "remembered_minutes": 25,
        "minutes_source": "carried", "split_json": split_json if split_json is not None else {},
        "admission_json": {}, "estimator_version": "test", "source": "test", "chooser": "test", "status": "open",
        "algorithm_version": "test", "config_hash": "test", "created_at": created_at, "updated_at": created_at})


def _block(connection, plan_id: str, block_id: str, ordinal: int | None, created_at: str) -> None:
    PLAN_STORE.insert_plan_block(connection, {
        "id": block_id, "action": "practice", "budget_minutes": 5.0, "neighborhood": {}, "content_hash": block_id,
        "created_at": created_at, "daily_plan_id": plan_id, "plan_ordinal": ordinal, "lane": "new",
        "chosen_by": "chooser"})


def _event(connection, block_id: str, kind: str, **detail: object) -> None:
    PLAN_STORE.append_block_event(connection, event_id=f"{block_id}:{kind}:{json.dumps(detail, sort_keys=True)}",
                                  block_id=block_id, kind=kind, detail=detail, created_at="2026-11-02T10:00:00+00:00")


def _plan_holds(repository, item_id: str, *resolved_by: str, plan_id: str = "dp_v1", local_date: str | None = None) -> None:
    """Today's stored plan has selected ``item_id``, not yet answered (``resolved_by``: the
    events that have resolved it since)."""

    with repository.connection() as connection:
        _plan_row(connection, plan_id, local_date or _today(), "2026-11-02T09:00:00+00:00")
        _block(connection, plan_id, f"{plan_id}_b1", 1, "2026-11-02T09:00:00+00:00")
        _event(connection, f"{plan_id}_b1", "item_planned", practice_item_id=item_id, learning_object_id="lo")
        for kind in resolved_by:
            _event(connection, f"{plan_id}_b1", kind, practice_item_id=item_id)
        connection.commit()


def _worked_answer_at(monkeypatch, item_id: str, span: str) -> None:
    """``item_id``'s worked answer is ``span`` of the prebuild's source."""

    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, span)}) if item.id == item_id else frozenset()))


def _neighbour(job) -> str:
    base = job["payload"]["base"]
    others = [span for span in base["input_span_ids"] if span not in base["span_ids"]]
    assert others, base
    return others[0]


def _waiting_rig(tmp_path, monkeypatch):
    """A prebuild that met the plan's limit; the item its saved context answers is named, unplanned."""

    unavailable = AIProviderUnavailable("usage limit reached")
    paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [unavailable, RF.scene_output()])
    _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    assert _waiting(job) and rich_author.calls == 1
    item_id = sorted(load_vault(paths.root).practice_items)[0]
    _worked_answer_at(monkeypatch, item_id, _neighbour(job))
    return paths, repository, ctx, rich_author, job, item_id


# --- V1: the stored plan's open items, on every path -------------------------------------------------


def test_v1_the_readers_read_never_requeues_a_prebuild_a_later_plan_holds(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    _plan_holds(repository, item_id)  # the day plan selects the question after the plan's limit was met
    assert FS.prefetch_plan_waits(load_vault(paths.root), repository, EXTRACTION) == []
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 1 and _waiting(_prebuild_jobs(repository)[0])
    assert FS.list_figures(load_vault(paths.root), repository, EXTRACTION) == []


def test_v1_the_reader_and_the_pass_read_the_same_rule(tmp_path, monkeypatch):
    paths, repository, _ctx_, _rich, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    vault = load_vault(paths.root)
    assert FS.prefetch_plan_waits(vault, repository, EXTRACTION) == [job["id"]]
    assert FS.prefetch_plan_waits(vault, repository, None) == [job["id"]]
    assert PF.item_protection(_env(paths, repository, [])).covers(EXTRACTION, [_neighbour(job)]) is False
    _plan_holds(repository, item_id)
    assert FS.prefetch_plan_waits(vault, repository, EXTRACTION) == []
    assert FS.prefetch_plan_waits(vault, repository, None) == []
    assert PF.item_protection(_env(paths, repository, [])).covers(EXTRACTION, [_neighbour(job)]) is True
    retried: list[str] = []
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == []


def test_v1_the_worker_stops_a_requeued_prebuild_a_later_plan_holds_before_any_request(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    _plan_holds(repository, item_id)
    # However it was requeued (an older sidecar's read, a retry press), the worker's own gate refuses.
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    (stopped,) = _prebuild_jobs(repository)
    assert rich_author.calls == 1
    assert stopped["status"] == "failed" and (stopped.get("error") or {}).get("code") == "exam_material"
    assert FS.list_figures(load_vault(paths.root), repository, EXTRACTION) == []


def test_v1_the_worker_rechecks_the_plan_before_the_store(tmp_path, monkeypatch):
    """The plan selects the question while the author writes: nothing is stored."""

    paths, repository, ctx, rich_author, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    complete = rich_author.complete

    def complete_then_planned(request):
        out = complete(request)
        _plan_holds(repository, item_id)
        return out

    monkeypatch.setattr(rich_author, "complete", complete_then_planned)
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    (stopped,) = _prebuild_jobs(repository)
    assert rich_author.calls == 2  # the request was sent before the plan selected the item
    assert stopped["status"] == "failed" and (stopped.get("error") or {}).get("code") == "exam_material"
    assert FS.list_figures(load_vault(paths.root), repository, EXTRACTION) == []


def test_v1_an_unreadable_stored_plan_fails_closed_everywhere(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job, _item_id = _waiting_rig(tmp_path, monkeypatch)
    with repository.connection() as connection:
        _plan_row(connection, "dp_bad", _today(), "2026-11-02T09:00:00+00:00", split_json="{not json")
        connection.commit()
    vault = load_vault(paths.root)
    assert FS.item_passages(vault, repository) is None
    assert FS.prefetch_plan_waits(vault, repository, EXTRACTION) == []
    assert PF.item_protection(_env(paths, repository, [])).available is False
    assert FS.rich_base_item_protected(vault, repository, job["payload"]["base"]) == FS.ITEM_PASSAGE_PROTECTED
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 1
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    assert rich_author.calls == 1


@pytest.mark.parametrize("resolved_by", ["item_done", "item_skipped", "item_displaced"])
def test_v1_an_answered_planned_item_lets_the_retry_through(tmp_path, monkeypatch, resolved_by):
    paths, repository, _ctx_, _rich, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    _plan_holds(repository, item_id, resolved_by)
    assert FS.prefetch_plan_waits(load_vault(paths.root), repository, EXTRACTION) == [job["id"]]


def test_v1_only_todays_plan_holds_an_item(tmp_path, monkeypatch):
    paths, repository, _ctx_, _rich, job, item_id = _waiting_rig(tmp_path, monkeypatch)
    yesterday = (datetime.now(UTC).astimezone() - timedelta(days=1)).date().isoformat()
    _plan_holds(repository, item_id, local_date=yesterday)
    vault = load_vault(paths.root)
    assert FS.prefetch_plan_waits(vault, repository, EXTRACTION) == [job["id"]]
    # The clock names the day: on the plan's own day, it holds.
    then = FrozenClock(datetime.now(UTC) - timedelta(days=1))
    assert FS.prefetch_plan_waits(vault, repository, EXTRACTION, clock=then) == []
    assert FS.rich_base_item_protected(vault, repository, job["payload"]["base"], clock=then) == FS.ITEM_PASSAGE_PROTECTED


def test_v1_a_learners_own_press_keeps_its_behaviour(tmp_path, monkeypatch):
    paths, repository, ctx, author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    item_id = sorted(load_vault(paths.root).practice_items)[0]
    _worked_answer_at(monkeypatch, item_id, "p3")  # the very passage pressed
    _plan_holds(repository, item_id)
    result = build(ctx)
    (line,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert result["figure"]["figureId"] == line["figureId"] and line["fuller"]["state"] == "ready"
    assert author.calls == 1 and rich_author.calls == 1


def _fold_cases(connection) -> None:
    """One day's plans, older first, with every event that opens, moves or resolves an item."""

    day = "2026-11-02"
    _plan_row(connection, "dp_a", day, "2026-11-02T08:00:00+00:00")
    _block(connection, "dp_a", "a1", 1, "2026-11-02T08:00:00+00:00")
    _event(connection, "a1", "item_planned", practice_item_id="older_plan_open")
    _plan_row(connection, "dp_other_day", "2026-11-01", "2026-11-01T08:00:00+00:00")
    _block(connection, "dp_other_day", "o1", 1, "2026-11-01T08:00:00+00:00")
    _event(connection, "o1", "item_planned", practice_item_id="other_day_open")
    _plan_row(connection, "dp_b", day, "2026-11-02T09:00:00+00:00")
    _block(connection, "dp_b", "b2", 2, "2026-11-02T09:00:00+00:00")
    _event(connection, "b2", "item_planned", practice_item_id="second_block_open")
    _block(connection, "dp_b", "b1", 1, "2026-11-02T09:00:00+00:00")
    for item in ("planned", "served", "done", "skipped", "displaced", "slot_open", "slot_done", "planned_twice"):
        _event(connection, "b1", "item_planned", practice_item_id=item)
    _event(connection, "b1", "item_served", practice_item_id="served")
    _event(connection, "b1", "item_done", practice_item_id="done")
    _event(connection, "b1", "item_skipped", practice_item_id="skipped")
    _event(connection, "b1", "item_displaced", practice_item_id="displaced", reason="x")
    _event(connection, "b1", "item_substituted", practice_item_id="drawn_open", slot_item_id="slot_open")
    _event(connection, "b1", "item_substituted", practice_item_id="drawn_done", slot_item_id="slot_done")
    _event(connection, "b1", "item_done", practice_item_id="drawn_done")
    _event(connection, "b1", "item_done", practice_item_id="never_planned")
    _event(connection, "b1", "item_substituted", practice_item_id="drawn_nowhere", slot_item_id="never_planned")
    PLAN_STORE.append_block_event(connection, event_id="b1:again", block_id="b1", kind="item_planned",
                                  detail={"practice_item_id": "planned_twice"}, created_at="2026-11-02T10:00:00+00:00")
    _event(connection, "b1", "item_done", practice_item_id="planned_twice")
    _block(connection, "dp_b", "receipt", None, "2026-11-02T09:00:00+00:00")
    _event(connection, "receipt", "item_planned", practice_item_id="in_a_receipt")


def test_v1_the_open_items_are_the_plan_records_own(tmp_path):
    """The core's read and what the plan itself says is open never disagree."""

    _paths, repository, _vault = make_vault(tmp_path)
    with repository.connection() as connection:
        _fold_cases(connection)
        connection.commit()
    record = load_records(repository, local_date_value="2026-11-02")[-1]
    expected = [item.practice_item_id for item in record.items() if not item.resolved]
    assert isinstance(record, RECORDS.PlanRecord) and "drawn_open" in expected and "planned_twice" in expected
    assert "in_a_receipt" not in expected and "older_plan_open" not in expected
    day = FrozenClock(datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    assert FS.stored_plan_open_items(repository, clock=day) == expected
    assert "second_block_open" in expected and "other_day_open" not in expected and "done" not in expected
    assert FS.stored_plan_open_items(repository, clock=FrozenClock(datetime(2026, 10, 1, 12, 0, tzinfo=UTC))) == []


# --- V2: retries ride on real learner activity only ---------------------------------------------------


def _due(job_id: str) -> None:
    RICH._LAST_REQUEUE.pop(job_id, None)


def test_v2_deferred_gap_drains_fire_passes_that_never_retry_a_plan_wait(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import jobs

    paths, repository, ctx, rich_author, job, _item = _waiting_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(jobs, "process_next_gap_job", lambda *args, **kwargs: SimpleNamespace(state="deferred"))
    requeued: list[str] = []
    real = ctx.ingest_jobs.retry_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "retry_figure_rich",
                        lambda job_id, **kwargs: requeued.append(job_id) or real(job_id, **kwargs))
    worker = ctx.post_attempt_worker
    assert worker.after_gaps == ctx._prefetch_gaps  # the sidecar's own wiring
    before = len(ctx.figure_prefetch.results)
    for _tick in range(2):  # two ticks of the worker's poll: no call from the app, no new gap stored
        _due(job["id"])
        worker._run_gaps(SimpleNamespace(root=paths.root), repository, max_jobs=5, clock=None)
    passes = ctx.figure_prefetch.results[before:]
    assert [result.trigger for result in passes] == ["gap", "gap"]  # the passes still fire (see the record)
    assert [result.plan_wait_retries for result in passes] == [[], []]
    assert requeued == [] and rich_author.calls == 1 and _waiting(_prebuild_jobs(repository)[0])


def test_v2_todays_read_never_retries_a_plan_wait(tmp_path, monkeypatch):
    """``get_daily_plan`` is a read: the queue revision's poll refetches it when background
    work lands, with nobody at the keyboard."""

    from learnloop_sidecar.handlers.daily_plan import _schedule_prefetch

    paths, repository, ctx, rich_author, job, _item = _waiting_rig(tmp_path, monkeypatch)
    _plan_holds(repository, "not_in_the_vault")
    before = len(ctx.figure_prefetch.results)
    _due(job["id"])
    _schedule_prefetch(ctx, PlanEnv(vault=load_vault(paths.root), repository=repository))
    passes = ctx.figure_prefetch.results[before:]
    assert [result.trigger for result in passes] == ["plan", "gap"]
    assert [result.plan_wait_retries for result in passes] == [[], []] and rich_author.calls == 1


def test_v2_a_trigger_that_names_no_provenance_never_retries(tmp_path, monkeypatch):
    from learnloop_sidecar import prefetch_runtime as RT

    _paths, _repository, ctx, rich_author, job, _item = _waiting_rig(tmp_path, monkeypatch)
    _due(job["id"])
    assert RT.notify(ctx, "offer", "tutor:q2", blocks=[(EXTRACTION, "p3")])
    assert ctx.figure_prefetch.results[-1].plan_wait_retries == [] and rich_author.calls == 1
    _due(job["id"])
    assert RT.notify(ctx, "offer", "tutor:q3", blocks=[(EXTRACTION, "p3")], learner_activity=True)
    assert ctx.figure_prefetch.results[-1].plan_wait_retries == [job["id"]] and rich_author.calls == 2


def _record_triggers(monkeypatch) -> list[PF.Trigger]:
    from learnloop_sidecar import prefetch_runtime as RT

    seen: list[PF.Trigger] = []
    monkeypatch.setattr(RT.PrefetchRuntime, "submit", lambda self, ctx, trigger: seen.append(trigger))
    return seen


def test_v2_section_progress_carries_learner_activity(tmp_path, monkeypatch):
    paths, _repository, _vault = make_vault(tmp_path, two=True)
    ctx = context(paths.root, author=AuthorFake())
    ctx.figure_prefetch_inline = True
    seen = _record_triggers(monkeypatch)
    call(ctx, "reader.mark_section_progress", {"extractionId": TWO, "sectionId": "s1", "spansSeen": 1, "spanCount": 3})
    assert [(trigger.kind, trigger.learner_activity) for trigger in seen] == [("section", True)]


@pytest.mark.parametrize("origin", ["tutor", "library"])
def test_v2_an_offer_from_the_learners_own_question_carries_learner_activity(tmp_path, monkeypatch, origin):
    from learnloop_sidecar import handlers, prefetch_runtime as RT

    paths, _repository, _vault = make_vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake())
    ctx.figure_prefetch_inline = True
    monkeypatch.setattr(handlers.figures, "offered_spans", lambda *args: {(EXTRACTION, "p3")})
    seen = _record_triggers(monkeypatch)
    assert RT.notify_offer(ctx, origin, "ask_1")
    assert [(trigger.kind, trigger.learner_activity) for trigger in seen] == [("offer", True)]


def test_v2_a_lessons_turn_carries_learner_activity(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import lesson as LESSON

    paths, _repository, _vault = make_vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake())
    ctx.figure_prefetch_inline = True
    monkeypatch.setattr(LESSON.S, "require_active", lambda vault: None)
    monkeypatch.setattr(LESSON.S, "take_turn", lambda *args, **kwargs: {"lesson_id": "les_1", "plan": {"nodes": []}})
    seen = _record_triggers(monkeypatch)
    call(ctx, "lesson.turn", {"action": "reply", "lessonId": "les_1", "text": "go on"})
    assert [(trigger.kind, trigger.ref, trigger.learner_activity) for trigger in seen] == [
        ("lesson", "les_1", True), ("gap", "lesson:les_1", True)]


def test_v2_characterization_a_worker_origin_pass_still_runs_ordinary_builds(tmp_path, monkeypatch):
    """Recorded, not decided here: V2 changes only the retry step. A build the pass deferred for
    power is built by the next pass, whatever fired it, the gap worker's poll tick included."""

    paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [RF.scene_output()])
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    _pass(ctx, "tutor:q1")
    assert rich_author.calls == 0
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    ctx.figure_prefetch_judge_client = JudgeFake()
    ctx.figure_prefetch_rng = np.random.default_rng(0)
    ctx._prefetch_gaps()  # what a nonempty drain calls
    assert ctx.figure_prefetch.results[-1].trigger == "gap"
    assert rich_author.calls == 1 and _prebuild_jobs(repository)[0]["status"] == "completed"

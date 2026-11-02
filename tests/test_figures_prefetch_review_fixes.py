"""Reader RW5d P5, Codex review fixes (docs/reviews/reader-rw5d-p5-prefetch-codex-review.md).

* **F1** a judge retry never resends a passage that became withheld (section and gap modes).
* **F2** a prebuild is never metered: the figure author's route and the durable rich job's route are
  checked against the vault as configured NOW, before every request.
* **F3** a recovered prebuild intent stays a prebuild (switch off: nothing starts).
* **F4** an item under a live administration, outside today's plan too, holds its passages back,
  over the author's whole context (the neighbours).
* **F5** a deferral for the power or the plan is retried, never decided twice.
* **F6** the daily cap is spent when a build starts (a resumed one included); the rich worker
  checks the render minutes.
* **F7** the judge, a quick build's requests and a prebuild's rich job yield to foreground work;
  a prebuild's rich job in flight holds the next prebuild.
* **F8** the lesson trigger builds only planned visuals (TE1's real plans carry none).
* **F9** outcomes read only what happened before the horizon; an ask is the same request.
* **F10** a speculative rich-only prebuild shows no pending or failure line.
* **F11** the Reader hears that a prebuild is coming; unpressed prebuilt lines keep to the cue budget.
* **F12** an unknown Linux power inventory is not mains.
* **F13** the gap judge's verdict is a ``judgment_ledger`` row.
* **F14** known tokens move the plan load; a build's expected requests are measured.
* **F15** ``figures.prefetch_enabled`` is on by default (Q21); the suite's env keeps hooks inert.

Fakes only: the judge, the authors, the renderer and the power reader are injected; no model is reached.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from types import SimpleNamespace

import pytest

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import FrozenClock
from learnloop.figures import foreground as FG
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import prefetch_model as PM
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests.figure_fixtures import EQUATION_TEXT, EXTRACTION, AuthorFake, build, call, context, flagship, rows, set_config
from tests.test_figure_rich_job import WHY, _Rig
from tests.test_figures_prefetch import TWO, JudgeFake, decisions, env_for, make_vault, plan_record, switch


@pytest.fixture(autouse=True)
def mains():
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    yield
    P.set_power_reader(None)


def _held(monkeypatch, spans: set[str]) -> None:
    real = FS.withheld_message
    monkeypatch.setattr(FS, "withheld_message",
                        lambda v, r, e, found: "held out" if spans & set(found) else real(v, r, e, found))


def _prefetch_request(spans=("p3",), **fields) -> FS.FigureRequest:
    return FS.FigureRequest(extraction_id=EXTRACTION, span_ids=list(spans), origin="prefetch", **fields)


def _rich_rig(tmp_path, monkeypatch, answers, rich_answers=None) -> _Rig:
    rig = _Rig(tmp_path, monkeypatch, answers, rich_answers)
    set_config(rig.paths, "figures", price_per_million=2.0)
    return rig


# ---------------------------------------------------------------------------
# F1: retries revalidate the prompt's passages
# ---------------------------------------------------------------------------

def test_f1_a_section_judge_retry_is_not_sent_once_a_block_is_held_out(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    held: set[str] = set()
    _held(monkeypatch, held)

    def bad_then_hold(context):
        held.add("p3")  # the equation the first prompt carried becomes held out before the retry
        return {"blocks": [{"block": "b99", "goal": "", "p_open": 0.5}]}

    judge = JudgeFake([bad_then_hold])
    result = PF.run_trigger(env_for(vault, repository, judge=judge), PF.Trigger("plan", "dp_1"))
    assert judge.calls == 1 and all(EQUATION_TEXT not in prompt for prompt in judge.prompts[1:])
    assert any("protection_changed" in note for note in result.notes) and decisions(repository) == []


def test_f1_a_gap_judge_retry_is_not_sent_once_its_passage_is_held_out(tmp_path, monkeypatch):
    from learnloop.figures import learner_state as LS

    _paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(PF, "_touched_topics", lambda env: ["lo_matrices"])
    monkeypatch.setattr(LS, "open_gap_statements", lambda vault, repository, los: [
        {"id": "learner_text_gap:g1", "learning_object_id": "lo_matrices", "kind": "gap", "topic": "Matrices",
         "statement": "unsure the mass left of zero is p"}])
    held: set[str] = set()
    _held(monkeypatch, held)

    def bad_then_hold(context):
        held.add("p2")
        return {"goal": " ", "p_open": 0.5}

    judge = JudgeFake([bad_then_hold])
    env = env_for(vault, repository, judge=judge, passages=lambda v, r, lo: [(EXTRACTION, "p2")])
    result = PF.run_trigger(env, PF.Trigger("gap", "gaps"))
    assert judge.calls == 1 and decisions(repository) == []
    assert any("protection_changed" in note for note in result.notes)


# ---------------------------------------------------------------------------
# F2: never metered, as configured now
# ---------------------------------------------------------------------------

def test_f2_a_quick_prebuild_on_a_metered_author_route_sends_nothing(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    set_config(paths, "figures", price_per_million=2.0)
    vault = load_vault(paths.root)
    author = AuthorFake(provider_type="openrouter")
    with pytest.raises(FS.FigureRefused) as refused:
        FS.build_prefetch_figure(vault, repository, _prefetch_request(), author_client=author)
    assert refused.value.code == "figures_changed" and author.calls == 0
    assert FS.PREFETCH_AUTHOR_NOT_PLAN in refused.value.message


def test_f2_a_queued_prebuild_rich_job_is_not_sent_once_its_route_is_metered(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    assert rig.job()["payload"]["build_mode"] == "prefetch"
    rig.rich_author.provider_type = "openrouter"  # the rich author's route changed after it was queued
    rig.ingest.drain()
    job = rig.job()
    assert job["status"] == "failed" and job["error"]["code"] == "figures_changed"
    assert RICH.PREFETCH_NOT_PLAN in job["error"]["message"] and rig.rich_author.calls == 0


# ---------------------------------------------------------------------------
# F3: recovery keeps a prebuild a prebuild
# ---------------------------------------------------------------------------

def test_f3_a_recovered_prebuild_intent_keeps_its_guards(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])

    def lost(payload):
        raise RuntimeError("the sidecar stopped before the enqueue")

    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author, spawn_rich=lost)
    RF.configure(rig.paths, prefetch_enabled=False)
    off = load_vault(rig.paths.root)
    assert off.config.figures.prefetch_enabled is False
    assert FS.resume_rich_intents(off, rig.repository, EXTRACTION, rig.spawn) == 0 and rig.batches == []
    RF.configure(rig.paths, prefetch_enabled=True)
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 1
    assert rig.job()["payload"]["build_mode"] == "prefetch"


# ---------------------------------------------------------------------------
# F4: live administrations, outside the plan, over the whole author context
# ---------------------------------------------------------------------------

def test_f4_a_cold_items_passage_and_its_neighbours_are_never_prebuilt(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP
    from learnloop.source_retrieval import corpus

    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)  # today's plan holds no item
    real = LP.withheld_items

    def withheld(v, r):
        found = real(v, r)
        return LP.Withheld(reasons={**found.reasons, "pi_eigen_1": LP.WITHHELD_COLD}, known_items=found.known_items,
                           exam=found.exam)

    monkeypatch.setattr(LP, "withheld_items", withheld)
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, "p2")}) if item.id == "pi_eigen_1" else frozenset()))
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"))))
    # p3's context carries p2 (its neighbour, the cold item's worked answer); p6's does not.
    assert [json.loads(row["anchor_json"])["span_ids"] for row in decisions(repository)] == [["p6"]]
    # The section judge never reads the cold item's passage either.
    judge = JudgeFake()
    PF.judge_section(env_for(vault, repository, judge=judge), EXTRACTION, "u54")
    assert "two-sided exponential has density" not in json.dumps(judge.contexts[0])


def test_f4_unreadable_protection_prebuilds_nothing(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP

    _paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(LP, "withheld_items", lambda v, r: LP.Withheld(available=False))
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p6"),)))
    assert decisions(repository) == [] and author.calls == 0


def test_f4_a_build_rechecks_the_protection_before_it_starts(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP
    from learnloop.source_retrieval import corpus

    _paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    with FG.foreground("lesson"):
        PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p6"),)))
    real = LP.withheld_items
    monkeypatch.setattr(LP, "withheld_items", lambda v, r: LP.Withheld(
        reasons={**real(v, r).reasons, "pi_eigen_1": LP.WITHHELD_COLD}, known_items=real(v, r).known_items))
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, "p5")}) if item.id == "pi_eigen_1" else frozenset()))
    result = PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:r", blocks=()))
    assert author.calls == 0 and any("an item's own passage now" in note for note in result.notes)


# ---------------------------------------------------------------------------
# F5: deferrals are retried
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deferral", ["deferred_power", "deferred_plan"])
def test_f5_a_deferred_decision_is_built_once_the_condition_clears(tmp_path, deferral):
    from learnloop.clock import utc_now_iso as now_iso

    _paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    if deferral == "deferred_power":
        P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
        env = env_for(vault, repository, author=author)
    else:
        env = env_for(vault, repository, author=author,
                      pause_reader=lambda: {"code": "usage_limit", "at": now_iso(), "id": "x"})
    PF.run_trigger(env, PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    (row,) = decisions(repository)
    assert row["decision"] == deferral and author.calls == 0
    # Mains and the plan back: the next pass (any trigger) builds it, deciding nothing twice.
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    (row,) = decisions(repository)
    assert row["decision"] == deferral and row["request_id"] is not None and author.calls == 1
    # Once built and closed, it informs the opening model.
    assert PL.observations([{**row, "outcome": "neither"}])


# ---------------------------------------------------------------------------
# F6: caps when work starts
# ---------------------------------------------------------------------------

def test_f6_a_resumed_build_spends_todays_cap(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, two=True, max_daily_builds=1)
    yesterday = FrozenClock(datetime(2099, 3, 1, 12, tzinfo=UTC))
    today = FrozenClock(datetime(2099, 3, 2, 12, tzinfo=UTC))
    PF.judge_section(env_for(vault, repository, clock=yesterday), TWO, "s2")  # judged (cached) while idle
    with FG.foreground("lesson"):  # yesterday's build waited (s2 is not read yet: its horizon is open)
        PF.run_trigger(env_for(vault, repository, clock=yesterday),
                       PF.Trigger("section", "x", extraction_id=TWO, section_id="s1"))
    (pending,) = decisions(repository)
    assert pending["decision"] == "build" and pending["request_id"] is None
    author = AuthorFake()
    result = PF.run_trigger(env_for(vault, repository, author=author, clock=today),
                            PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    # Today: the resumed build and today's new one, but one build a day: one starts.
    assert author.calls == 1 and any("used up" in note for note in result.notes)
    with repository.connection() as connection:
        assert len(PL.started_today(connection, today="2099-03-02", offset=timedelta(0))) == 1


def test_f6_a_prebuilds_rich_job_checks_the_render_minutes_when_it_starts(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    set_config(rig.paths, "figures.prefetch", max_daily_render_minutes=0)
    rig.ingest.drain()
    job = rig.job()
    assert job["status"] == "failed" and RICH.PREFETCH_RENDER_CAP in job["error"]["message"]
    assert rig.rich_author.calls == 0 and rig.renders.calls == []


# ---------------------------------------------------------------------------
# F7: yielding and one pipeline at a time
# ---------------------------------------------------------------------------

def test_f7_the_judge_waits_for_foreground_work(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    judge = JudgeFake()
    with FG.foreground("lesson"):
        result = PF.run_trigger(env_for(vault, repository, judge=judge), PF.Trigger("plan", "dp_1"))
    assert judge.calls == 0 and any("judge waiting" in note for note in result.notes)


def test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    with FG.foreground("tutor"):
        with pytest.raises(FS.FigureRefused) as refused:
            FS.build_prefetch_figure(vault, repository, _prefetch_request(), author_client=author)
    assert refused.value.code == "figures_changed" and author.calls == 0
    assert P.YIELDED in refused.value.message


def test_f7_a_prebuilds_rich_job_yields_to_foreground_work(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    monkeypatch.setattr(FG, "FOREGROUND_WAIT_SECONDS", 0.0)
    with FG.foreground("figure"):
        rig.ingest.drain()
    job = rig.job()
    assert job["status"] == "failed" and P.YIELDED in job["error"]["message"] and rig.rich_author.calls == 0
    # The batch is background work: below every pressed figure's band.
    with rig.repository.connection() as connection:
        (priority,) = connection.execute("SELECT priority FROM ingest_batches WHERE id = ?", (rig.batches[-1],)).fetchone()
    assert priority == 0


def test_f7_a_prebuilds_rich_job_in_flight_holds_the_next_prebuild_and_the_judge(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    from tests.test_figures_prefetch import seed_wait

    seed_wait(rig.repository)
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    assert PF.rich_in_flight(env_for(rig.vault, rig.repository))
    author = AuthorFake()
    result = PF.run_trigger(env_for(rig.vault, rig.repository, author=author),
                            PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p6"),)))
    assert author.calls == 0 and any("background animation" in note for note in result.notes)
    plan_record(monkeypatch)
    judge = JudgeFake()
    PF.run_trigger(env_for(rig.vault, rig.repository, judge=judge, author=author), PF.Trigger("plan", "dp_1"))
    assert judge.calls == 0


# ---------------------------------------------------------------------------
# F8: only planned visuals, through TE1's real plan
# ---------------------------------------------------------------------------

def test_f8_a_te1_lesson_plan_has_no_planned_visual_so_nothing_is_prebuilt(tmp_path):
    from learnloop.teacher import service as S
    from learnloop.teacher.service import load_state
    from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths, "figures", prefetch_enabled=True)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(TeacherFake([plan_turn])))
    state = load_state(repository, view["lesson_id"])
    assert state.plans and all(PF.planned_visual(node) is None for node in state.plans[-1]["outline"])
    vault = load_vault(paths.root)
    result = PF.PassResult("ok", "lesson")
    env = env_for(vault, repository)
    assert PF.candidates(env, PF.Trigger("lesson", view["lesson_id"]), call=True, result=result) == []
    PF.run_trigger(env, PF.Trigger("lesson", view["lesson_id"]))
    assert decisions(repository) == []


# ---------------------------------------------------------------------------
# F9: outcomes bounded by the horizon; asks by request identity
# ---------------------------------------------------------------------------

def test_f9_an_open_after_the_horizon_is_not_an_outcome(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    day = FrozenClock(datetime(2099, 3, 1, 12, tzinfo=UTC))
    PF.run_trigger(env_for(vault, repository, clock=day), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    (built,) = decisions(repository)
    assert built["request_id"]
    figure_id = rows(repository, "interactive_figures")[0]["id"]
    next_morning = FrozenClock(datetime(2099, 3, 2, 12, tzinfo=UTC) + (datetime.now().astimezone().utcoffset()
                                                                         or timedelta(0)) * -1)
    log_interaction_event(repository, kind="reader_action_invoked", origin="learner", subject_type="reader_extraction",
                          subject_id=EXTRACTION, payload=salience_payload({"event": "figure_opened",
                                                                           "figure_id": figure_id}),
                          clock=next_morning)
    assert PF.close_horizons(env_for(vault, repository, clock=FrozenClock(datetime(2099, 3, 3, 12, tzinfo=UTC)))) == 1
    (row,) = decisions(repository)
    assert row["outcome"] == "neither"


def test_f9_an_ask_is_the_same_request_before_the_horizon(tmp_path):
    paths, repository, vault = make_vault(tmp_path, wait=False)  # every decision a skip (no measured wait)
    earlier = FrozenClock(datetime.now(UTC) - timedelta(days=2))
    PF.run_trigger(env_for(vault, repository, clock=earlier),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    ctx = context(paths.root, author=AuthorFake())
    build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})  # today: after p3's horizon (two days ago)
    # Today's pass (on battery: nothing builds) closes p3, with the press after its horizon, and
    # decides p6 and p5.
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    PF.run_trigger(env_for(vault, repository),
                   PF.Trigger("offer", "tutor:r", blocks=((EXTRACTION, "p6"), (EXTRACTION, "p5"))))
    assert not any(row["request_id"] for row in decisions(repository))
    build(ctx, {"goalText": "slide lambda", "origin": "show_me",
                "anchor": {"extractionId": EXTRACTION, "spanIds": ["p6"]}}, rpc="figure.request")
    build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p5"]})
    later = FrozenClock(datetime.now(UTC) + timedelta(days=2))
    PF.close_horizons(env_for(vault, repository, clock=later))
    outcomes = {json.loads(row["anchor_json"])["span_ids"][0]: row["outcome"] for row in decisions(repository)}
    # p3: pressed only after its horizon; p6: pressed with a goal, a different request than its
    # anchor-only one; p5: the same request, before its horizon.
    assert outcomes == {"p3": "neither", "p6": "neither", "p5": "asked"}


# ---------------------------------------------------------------------------
# F10: speculation invisible until useful
# ---------------------------------------------------------------------------

def test_f10_a_rich_only_prebuild_shows_no_pending_or_failure_line(tmp_path, monkeypatch):
    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [wrong, wrong])
    outcome = FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                                       spawn_rich=rig.spawn)
    assert outcome.view is None and outcome.rich is not None
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    RF.configure(rig.paths, prefetch_enabled=False)
    assert FS.rich_pending(load_vault(rig.paths.root), rig.repository, EXTRACTION) == []
    RF.configure(rig.paths, prefetch_enabled=True)
    rig.ingest.drain()
    assert rig.job()["status"] in ("completed", "failed")
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    assert FS.list_figures(rig.vault, rig.repository, EXTRACTION) == []  # the failed prebuild lists nothing


# ---------------------------------------------------------------------------
# F11: the Reader hears of a prebuild to come; the cue budget
# ---------------------------------------------------------------------------

def test_f11_reader_figures_says_a_prebuild_is_coming_until_it_lands(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    with FG.foreground("lesson"):
        PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    ctx = context(paths.root, author=AuthorFake())
    from learnloop_sidecar.prefetch_runtime import PrefetchRuntime

    runtime = PrefetchRuntime()
    runtime._running = True  # re-review F18: an unstarted decision is coming while a pass runs
    ctx.figure_prefetch = runtime
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION}).get("prefetchPending") is True
    PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=()))
    found = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert "prefetchPending" not in found and len(found["figures"]) == 1
    switch(paths, False)
    ctx = context(paths.root, author=AuthorFake())
    assert "prefetchPending" not in call(ctx, "reader.figures", {"extractionId": EXTRACTION})


def test_f11_unpressed_prebuilt_lines_keep_to_the_cue_budget(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    set_config(paths, "cues", density="fewer")  # one cue a section
    vault = load_vault(paths.root)
    PF.run_trigger(env_for(vault, repository),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"))))
    assert len(rows(repository, "interactive_figures")) == 2
    listed = FS.list_figures(vault, repository, EXTRACTION)
    assert len(listed) == 1
    # Pressed, a prebuilt figure is the learner's like any figure: never cut.
    other = next(row for row in rows(repository, "interactive_figures") if row["id"] != listed[0]["figure_id"])
    build(context(paths.root, author=AuthorFake()), {"extractionId": EXTRACTION, "spanIds": json.loads(other["span_ids_json"])})
    assert len(FS.list_figures(vault, repository, EXTRACTION)) == 2
    set_config(paths, "cues", enabled=False)
    assert len(FS.list_figures(load_vault(paths.root), repository, EXTRACTION)) == 1


# ---------------------------------------------------------------------------
# F12: an unknown inventory is not mains
# ---------------------------------------------------------------------------

def test_f12_an_unknown_linux_power_inventory_fails_closed(tmp_path):
    profile = lambda: "balanced"  # noqa: E731
    missing = P.linux_power_state(tmp_path / "missing", profile=profile)
    assert missing.on_mains is False and missing.reason == P.UNKNOWN
    empty = tmp_path / "empty"
    empty.mkdir()
    assert P.linux_power_state(empty, profile=profile).on_mains is True  # a desktop: nothing listed
    odd = tmp_path / "odd"
    (odd / "AC").mkdir(parents=True)  # a supply whose type can't be read
    assert P.linux_power_state(odd, profile=profile).reason == P.UNKNOWN
    statusless = tmp_path / "statusless"
    (statusless / "BAT0").mkdir(parents=True)
    (statusless / "BAT0" / "type").write_text("Battery\n", encoding="utf-8")
    (statusless / "AC").mkdir()
    (statusless / "AC" / "type").write_text("Mains\n", encoding="utf-8")
    (statusless / "AC" / "online").write_text("1\n", encoding="utf-8")
    assert P.linux_power_state(statusless, profile=profile).reason == P.UNKNOWN


# ---------------------------------------------------------------------------
# F13: the gap judge's judgment
# ---------------------------------------------------------------------------

def test_f13_the_gap_judges_verdict_is_a_judgment_ledger_row_once(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    judge = JudgeFake()
    env = env_for(vault, repository, judge=judge)
    gap = {"id": "learner_text_gap:g1", "statement": "unsure the mass left of zero is p", "topic": "Mixtures"}
    passage = {"extraction_id": EXTRACTION, "span_id": "p2", "text": "The two-sided exponential has density"}
    first = PF.judge_gap(env, gap, passage)
    second = PF.judge_gap(env, gap, passage)
    assert first == second and judge.calls == 1
    (row,) = [row for row in rows(repository, "judgment_ledger") if row["task"] == PF.LEDGER_TASK]
    assert row["left_kind"] == "learner_gap" and row["left_id"] == gap["id"]
    assert row["right_id"] == f"{EXTRACTION}:p2" and row["prompt_version"] == PF.JUDGE_PROMPT_VERSION
    assert row["judge_model"] and row["input_hash"] and row["verdict"] == "judged"
    assert json.loads(row["rationale"]) == {"mode": "gap", "goal": first[0], "p_open": first[1]}


# ---------------------------------------------------------------------------
# F14: tokens and measured incremental load
# ---------------------------------------------------------------------------

def test_f14_known_tokens_move_the_load_and_missing_tokens_count_as_an_average_request():
    light, heavy = PM.PlanDay(10, 1_000, False, 10), PM.PlanDay(10, 9_000, True, 10)
    per = PM.tokens_per_request([light, heavy])
    assert PM.plan_load(light, per) < PM.plan_load(heavy, per)
    partly = PM.PlanDay(10, 2_500, False, 5)  # five requests reported 2,500 tokens, five reported none
    assert PM.plan_load(partly, 500.0) == 5 + 5
    assert PM.plan_load(PM.PlanDay(7, 0, False, 0), per) == 7.0  # nothing reported: the requests
    pause = PM.pause_posterior([light, heavy, PM.PlanDay(10, 1_200, False, 10)])
    assert pause.per_request == per or pause.per_request is not None


def test_f14_a_builds_expected_requests_are_measured(tmp_path):
    _paths, repository, _vault = make_vault(tmp_path, wait=False)
    with repository.connection() as connection:
        for index, (purpose, owner) in enumerate([("figure_author", "figure:a"), ("figure_author", "figure:a"),
                                                  ("figure_author", "figure:b"), ("figure_rich_author", "figure_rich:x"),
                                                  ("figure_rich_author", "figure_rich:x"),
                                                  ("figure_rich_author", "figure_rich:x")]):
            connection.execute(
                "INSERT INTO model_call_receipts (id, owner_kind, owner_id, purpose, provider, status, started_at, "
                "finished_at) VALUES (?, ?, ?, ?, 'fake_figures', 'completed', ?, ?)",
                (f"mcr_{index}", purpose, owner, purpose, "2026-10-01T10:00:00+00:00", "2026-10-01T10:00:30+00:00"))
        connection.commit()
        found = PL.incremental(connection)
    assert found.author_calls == 1.5 and found.rich_calls == 3.0
    waits = PM.waits({"grammar": [0.5], "manim": [3.0]}, ["grammar", "manim"])
    model = PM.Model(PM.open_posterior([]), PM.pause_posterior([]), waits, None, 0.0, found)
    assert model.expected_requests("plan") == pytest.approx(1.5 + 0.5 * 3.0)
    assert PM.Model(PM.open_posterior([]), PM.pause_posterior([]), waits, None, 0.0).expected_requests("plan") == 1.5


# ---------------------------------------------------------------------------
# F15: on by default; the suite keeps the hooks inert
# ---------------------------------------------------------------------------

def test_f15_figures_ahead_of_need_are_on_by_default_and_the_suite_keeps_hooks_inert(tmp_path):
    from learnloop.config.schema import FiguresConfig
    from learnloop_sidecar.prefetch_runtime import PREFETCH_ENV, notify, runs_here

    assert FiguresConfig().prefetch_enabled is True
    paths, repository, _vault = make_vault(tmp_path, two=True)
    ctx = context(paths.root, author=AuthorFake())
    import os

    assert os.environ.get(PREFETCH_ENV) == "off" and runs_here(ctx) is False
    assert notify(ctx, "section", "x", extraction_id=TWO, section_id="s1") is False
    assert "figure_prefetch" not in ctx.__dict__ and decisions(repository) == []
    ctx.figure_prefetch_inline = True  # a test that injects the seams runs it
    assert runs_here(ctx) is True


# ===========================================================================
# Codex re-review (F1 reopened, F16-F18)
# ===========================================================================

def _newer_snapshot_holds(monkeypatch, newer, spans: set[str]) -> None:
    """``withheld_message`` holds ``spans`` back only on the newer vault snapshot."""

    real = FS.withheld_message
    monkeypatch.setattr(FS, "withheld_message",
                        lambda v, r, e, found: "held out" if v is newer and spans & set(found) else real(v, r, e, found))


def test_f1_rereview_a_section_judge_retry_revalidates_on_the_vault_loaded_now(tmp_path, monkeypatch):
    paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    newer = load_vault(paths.root)
    loaded = {"vault": vault}
    _newer_snapshot_holds(monkeypatch, newer, {"p3"})

    def bad_then_newer(context):
        loaded["vault"] = newer  # a newer snapshot marks the equation held out before the retry
        return {"blocks": [{"block": "b99", "goal": "", "p_open": 0.5}]}

    judge = JudgeFake([bad_then_newer])
    env = env_for(vault, repository, judge=judge, live_vault=lambda: loaded["vault"])
    result = PF.run_trigger(env, PF.Trigger("plan", "dp_1"))
    assert judge.calls == 1 and all(EQUATION_TEXT not in prompt for prompt in judge.prompts[1:])
    assert any("protection_changed" in note for note in result.notes) and decisions(repository) == []


def test_f1_rereview_a_gap_judge_retry_revalidates_on_the_vault_loaded_now(tmp_path, monkeypatch):
    from learnloop.figures import learner_state as LS

    paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(PF, "_touched_topics", lambda env: ["lo_matrices"])
    monkeypatch.setattr(LS, "open_gap_statements", lambda vault, repository, los: [
        {"id": "learner_text_gap:g1", "learning_object_id": "lo_matrices", "kind": "gap", "topic": "Matrices",
         "statement": "unsure the mass left of zero is p"}])
    newer = load_vault(paths.root)
    loaded = {"vault": vault}
    _newer_snapshot_holds(monkeypatch, newer, {"p2"})

    def bad_then_newer(context):
        loaded["vault"] = newer
        return {"goal": " ", "p_open": 0.5}

    judge = JudgeFake([bad_then_newer])
    env = env_for(vault, repository, judge=judge, live_vault=lambda: loaded["vault"],
                  passages=lambda v, r, lo: [(EXTRACTION, "p2")])
    result = PF.run_trigger(env, PF.Trigger("gap", "gaps"))
    assert judge.calls == 1 and decisions(repository) == []
    assert any("protection_changed" in note for note in result.notes)


def test_f1_rereview_an_unreadable_current_vault_sends_no_judge_request(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    judge = JudgeFake()

    def unreadable():
        raise OSError("learnloop.toml unreadable")

    env = env_for(vault, repository, judge=judge, live_vault=unreadable)
    with pytest.raises(PF.JudgeUnavailable) as stopped:
        PF.judge_section(env, EXTRACTION, "u54")
    assert stopped.value.reason == "protection_changed" and judge.calls == 0


def test_f1_rereview_a_builds_protection_is_read_on_the_vault_loaded_now(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP
    from learnloop.source_retrieval import corpus

    paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    with FG.foreground("lesson"):
        PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p6"),)))
    newer = load_vault(paths.root)
    real = LP.withheld_items

    def withheld(v, r):
        found = real(v, r)
        if v is not newer:
            return found
        return LP.Withheld(reasons={**found.reasons, "pi_eigen_1": LP.WITHHELD_COLD}, known_items=found.known_items)

    monkeypatch.setattr(LP, "withheld_items", withheld)
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, "p5")}) if item.id == "pi_eigen_1" else frozenset()))
    result = PF.run_trigger(env_for(vault, repository, author=author, live_vault=lambda: newer),
                            PF.Trigger("offer", "tutor:r", blocks=()))
    assert author.calls == 0 and any("an item's own passage now" in note for note in result.notes)


def test_f16_a_prebuilds_rich_request_rechecks_the_switch_after_waiting_for_foreground_work(tmp_path, monkeypatch):
    from learnloop.ai.execution import active_request_gate

    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    admitting = {"now": False}
    complete = rig.rich_author.complete

    def admitted_then_complete(request):
        # As a real transport does: the physical request is admitted by the request gate first.
        admitting["now"] = True
        try:
            active_request_gate().admit(rig.rich_author, purpose=request.purpose, prompt="", budget=None)
        finally:
            admitting["now"] = False
        return complete(request)

    def wait_then_switch_off(timeout, **_kwargs):
        if admitting["now"]:  # the learner switches figures ahead of need off while the request waits
            RF.configure(rig.paths, prefetch_enabled=False)
        return True

    monkeypatch.setattr(rig.rich_author, "complete", admitted_then_complete)
    monkeypatch.setattr(FG, "wait_idle", wait_then_switch_off)
    with FG.foreground("figure"):
        rig.ingest.drain()
    job = rig.job()
    assert rig.rich_author.calls == 0
    assert job["status"] == "failed" and P.SWITCHED_OFF in job["error"]["message"]


def test_f16_the_gate_waits_before_it_reads_the_vault_it_checks():
    from learnloop.figure_admission import FiguresChanged, FiguresGate

    def snapshot(name):
        return SimpleNamespace(root=None, name=name, config=SimpleNamespace(figures=SimpleNamespace(enabled=True)))

    loaded = {"vault": snapshot("before")}
    order = []

    def wait():
        order.append("wait")
        loaded["vault"] = snapshot("after")  # the configuration changes while the unit waits

    def hold(current):
        order.append(f"hold:{current.name}")
        return "switched off" if current.name == "after" else None

    gate = FiguresGate(loaded["vault"], lambda vault: 1, live_vault=lambda: loaded["vault"], hold=hold, wait=wait)
    with pytest.raises(FiguresChanged):
        gate.check("request")
    assert order == ["wait", "hold:after"] and gate.held


def test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read(tmp_path, monkeypatch):
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop_sidecar.handlers.figures import _rich_spawner
    from tests.test_figure_rich_rpc import _ctx

    _paths, repository, ctx, _author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)],
        [AIProviderUnavailable("usage limit reached"), RF.scene_output()])
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    retried = []
    original_retry = ctx.ingest_jobs.retry_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "retry_figure_rich",
                        lambda job_id, **kwargs: retried.append(job_id) or original_retry(job_id, **kwargs))
    FS.build_prefetch_figure(ctx.vault, repository, _prefetch_request(), author_client=ctx.figure_author_client,
                             spawn_rich=_rich_spawner(ctx, ctx.vault, granted=False))
    (job,) = repository.ingest_jobs_by_types(["figure_rich"])
    assert job["status"] == "failed" and job["error"]["code"] == RICH.WAITING_FOR_PLAN
    assert FS.rich_pending(ctx.vault, repository, EXTRACTION) == []  # still invisible (F10)
    assert FS.prefetch_plan_waits(ctx.vault, repository, EXTRACTION) == [job["id"]]
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert retried == [job["id"]] and listed.get("richPending") == []
    # Paced: a second read inside the interval asks nothing more.
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert retried == [job["id"]]
    assert rich_author.calls == 2


def test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off(tmp_path, monkeypatch):
    from learnloop.ai.errors import AIProviderUnavailable

    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)],
                    [AIProviderUnavailable("usage limit reached"), RF.scene_output()])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    rig.ingest.drain()
    job = rig.job()
    assert job["error"]["code"] == RICH.WAITING_FOR_PLAN
    assert FS.prefetch_plan_waits(rig.vault, rig.repository, EXTRACTION) == [job["id"]]
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    assert FS.prefetch_plan_waits(rig.vault, rig.repository, EXTRACTION) == []
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    RF.configure(rig.paths, prefetch_enabled=False)
    assert FS.prefetch_plan_waits(load_vault(rig.paths.root), rig.repository, EXTRACTION) == []


def test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery(tmp_path):
    from learnloop_sidecar.prefetch_runtime import PrefetchRuntime

    paths, repository, vault = make_vault(tmp_path)
    with FG.foreground("lesson"):  # the build yields: a decision to build with no request
        PF.run_trigger(env_for(vault, repository), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    (row,) = decisions(repository)
    assert row["decision"] == "build" and row["request_id"] is None
    assert FS.prefetch_pending(vault, repository, EXTRACTION) is False  # no worker: reads would not resume it
    assert FS.prefetch_pending(vault, repository, EXTRACTION, pass_running=True) is True
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    assert FS.prefetch_pending(vault, repository, EXTRACTION, pass_running=True) is False
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    ctx = context(paths.root, author=AuthorFake())
    assert "prefetchPending" not in call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    runtime = PrefetchRuntime()
    runtime._running = True  # a pass is draining the queue now
    ctx.figure_prefetch = runtime
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION}).get("prefetchPending") is True
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    assert "prefetchPending" not in call(ctx, "reader.figures", {"extractionId": EXTRACTION})


def test_f18_a_prebuilds_rich_job_is_pending_on_mains_only(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    assert FS.prefetch_pending(rig.vault, rig.repository, EXTRACTION) is True  # queued: a worker will run it
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    assert FS.prefetch_pending(rig.vault, rig.repository, EXTRACTION) is False


# ---------------------------------------------------------------------------
# Landing ruling R1 (final verify F18): a speculative fuller version whose rich
# intent is not queued is pending only while background admission would start it
# ---------------------------------------------------------------------------

def _unqueued_prebuild_intent(tmp_path, monkeypatch) -> _Rig:
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])

    def lost(payload):
        raise RuntimeError("the sidecar stopped before the enqueue")

    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author, spawn_rich=lost)
    assert rig.ingest.repo.ingest_jobs_by_types(["figure_rich"]) == []
    return rig


def _quick_row(rig: _Rig) -> dict:
    from learnloop.db.stores import figures as store

    with rig.repository.connection() as connection:
        found = store.figures_for_extraction(connection, EXTRACTION)
    (quick,) = [row for row in found if not FS.rich_row(row)]
    return quick


def test_r1_an_unqueued_speculative_fuller_is_not_pending_on_battery(tmp_path, monkeypatch):
    rig = _unqueued_prebuild_intent(tmp_path, monkeypatch)
    quick = _quick_row(rig)
    on_mains = FS.fuller_state(rig.vault, rig.repository, quick)
    # On mains the next read starts it (resume_rich_intents): pending, and marked speculative.
    assert on_mains["state"] == "pending" and on_mains["speculative"] is True
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    assert FS.fuller_state(rig.vault, rig.repository, quick) is None
    (listed,) = rig.listed()
    assert listed["fuller"] is None  # the Reader has nothing to poll for


def test_r1_an_unqueued_speculative_fuller_is_not_pending_switched_off_or_held_out(tmp_path, monkeypatch):
    rig = _unqueued_prebuild_intent(tmp_path, monkeypatch)
    quick = _quick_row(rig)
    RF.configure(rig.paths, prefetch_enabled=False)
    assert FS.fuller_state(load_vault(rig.paths.root), rig.repository, quick) is None
    RF.configure(rig.paths, prefetch_enabled=True)
    assert FS.fuller_state(rig.vault, rig.repository, quick)["state"] == "pending"
    _held(monkeypatch, {"p3"})
    assert FS.fuller_state(rig.vault, rig.repository, quick) is None


def test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])

    def lost(payload):
        raise RuntimeError("the sidecar stopped before the enqueue")

    FS.build_figure(rig.vault, rig.repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                    author_client=rig.author, spawn_rich=lost)
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    fuller = FS.fuller_state(rig.vault, rig.repository, _quick_row(rig))
    assert fuller["state"] == "pending" and "speculative" not in fuller


def test_r1_a_queued_speculative_fuller_is_marked_speculative(tmp_path, monkeypatch):
    rig = _rich_rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    FS.build_prefetch_figure(rig.vault, rig.repository, _prefetch_request(), author_client=rig.author,
                             spawn_rich=rig.spawn)
    fuller = FS.fuller_state(rig.vault, rig.repository, _quick_row(rig))
    assert fuller["state"] == "pending" and fuller["speculative"] is True

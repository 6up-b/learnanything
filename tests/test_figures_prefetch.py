"""Reader RW5d P5: figures ahead of need (docs/specs/spec_reader_show_me_figures_v1.md §10b; gates G-SM27-G-SM30).

* **The switch** (``figures.prefetch_enabled``, default on, Q21): off, no pass runs, nothing is read, written or
  called, and a prebuilt figure nobody pressed for is not listed (rev 1 exactly).
* **The five triggers**: the stored plan's reading section, the next section after reading progress,
  RW5b's offers (anchor-only, no judge), a lesson plan's nodes not yet reached (with a teacher's planned
  goal), and open gaps on the plan's or a lesson's topics (the gap judge writes the goal).
* **The judge** (``figure_prefetch_judge``): listwise, at most three blocks, ids and probabilities checked
  (a bad answer retried once, then nothing), cached by the section's content, the ChatGPT plan only.
* **The decision**: a Thompson draw decides, its propensity and the posterior's digest are logged;
  no measured wait, no prebuild; caps cut the queue in sampled-EU order; off mains ``deferred_power``;
  a plan pause or a metered route ``deferred_plan``.
* **Builds**: origin ``prefetch`` (refused from every RPC), one at a time, never while foreground work is in
  flight (the queue waits for the next pass), stopped by the switch or the power; a later press reuses the
  figure by its input hash.
* **Outcomes** at the structural horizon: opened, asked, neither, void, set once.

Fakes only: the judge, the author and the power reader are injected; no model is reached.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import FrozenClock
from learnloop.figures import foreground as FG
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import prefetch_model as PM
from learnloop.figures import service as FS
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    call,
    context,
    rows,
)
from tests.figures_prefetch_helpers import (
    JudgeFake,
    TWO,
    count,
    decisions,
    env_for,
    make_vault,
    plan_record,
    switch,
)
from tests.figures_prefetch_helpers import mains  # noqa: F401 - fixtures, used by parameter name

# ---------------------------------------------------------------------------
# The switch
# ---------------------------------------------------------------------------

def test_switch_off_nothing_builds_nothing_is_written_and_nothing_is_called(tmp_path, monkeypatch):
    paths, repository, vault = make_vault(tmp_path, on=False, two=True)
    plan_record(monkeypatch)
    judge, author = JudgeFake(), AuthorFake()
    env = env_for(vault, repository, judge=judge, author=author)
    for trigger in (PF.Trigger("plan", "dp_1"), PF.Trigger("section", "x", extraction_id=TWO, section_id="s1"),
                    PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)), PF.Trigger("lesson", "les_1"),
                    PF.Trigger("gap", "gaps")):
        assert PF.run_trigger(env, trigger).status == "off"
    assert judge.calls == 0 and author.calls == 0
    for table in ("figure_prefetch_decisions", "plan_usage_pauses", "interactive_figures", "figure_requests"):
        assert count(repository, table) == 0
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?",
                                  (PF.LEDGER_TASK,)).fetchone()[0] == 0
    # The sidecar's hooks queue nothing (no runtime is even made).
    ctx = context(paths.root, author=AuthorFake())
    ctx.figure_prefetch_inline = True
    ctx.figure_prefetch_judge_client = judge
    call(ctx, "reader.mark_section_progress", {"extractionId": TWO, "sectionId": "s1", "spansSeen": 1,
                                              "spanCount": 3, "completed": True})
    assert "figure_prefetch" not in ctx.__dict__ and judge.calls == 0
    assert rows(repository, "figure_prefetch_decisions") == []


def test_the_switch_defaults_on():
    from learnloop.config.schema import FiguresConfig

    config = FiguresConfig()
    assert config.prefetch_enabled is True  # Q21's recommended default (Codex review F15)
    assert config.prefetch.max_daily_builds == 10 and config.prefetch.max_daily_render_minutes == 30.0


# ---------------------------------------------------------------------------
# The triggers
# ---------------------------------------------------------------------------

def test_plan_trigger_judges_the_reading_section_decides_logs_and_builds(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    judge, author = JudgeFake(), AuthorFake()
    result = PF.run_trigger(env_for(vault, repository, judge=judge, author=author), PF.Trigger("plan", "dp_1"))
    assert result.status == "ok" and judge.calls == 1 and author.calls == 1
    context = judge.contexts[0]
    assert context["mode"] == "section" and context["max_blocks"] == PF.PREFETCH_SECTION_CANDIDATES
    assert [block["type"] for block in context["blocks"]] == ["SectionHeader", "Text", "Equation", "Figure", "Text",
                                                              "Text"]
    (row,) = decisions(repository)
    assert row["trigger_kind"] == "plan" and row["trigger_ref"] == "dp_1" and row["decision"] == "build"
    assert json.loads(row["anchor_json"]) == {"extraction_id": EXTRACTION, "span_ids": ["p3"]}
    assert row["goal_text"] is None and row["p_open_content"] == 0.8
    # The test vaults sit below the figure wait estimate's tag (mvp-0.58), so they decide as prefetch_decision_v1.
    assert row["model_version"] == PM.MODEL_VERSION_V1 and len(row["posterior_digest"]) == 64
    assert 0.0 <= row["propensity"] <= 1.0 and row["sampled_eu"] > 0 and row["w_minutes"] > 0
    assert row["horizon_kind"] == "plan_day_ended" and row["outcome"] is None
    (request,) = rows(repository, "figure_requests")
    assert request["origin"] == "prefetch" and request["build_mode"] == "prefetch"
    assert request["prefetch_decision_id"] == row["id"] and row["request_id"] == request["id"]
    (figure,) = rows(repository, "interactive_figures")
    assert figure["origin"] == "prefetch" and row["input_hash"] == figure["input_hash"]
    # The judgment is cached by content and the figure exists: a second pass asks and builds nothing.
    again = PF.run_trigger(env_for(vault, repository, judge=judge, author=author), PF.Trigger("plan", "dp_1"))
    assert again.decisions == [] and judge.calls == 1 and author.calls == 1


def test_a_press_reuses_the_prebuilt_figure_by_its_input_hash(tmp_path, monkeypatch):
    paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    PF.run_trigger(env_for(vault, repository), PF.Trigger("plan", "dp_1"))
    (prebuilt,) = rows(repository, "interactive_figures")
    pressing = AuthorFake()
    result = build(context(paths.root, author=pressing), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    shown = result["figure"]
    assert result["reused"] is True and (shown.get("figureId") or shown.get("figure_id")) == prebuilt["id"]
    assert pressing.calls == 0
    assert [row["build_mode"] for row in rows(repository, "figure_requests")] == ["prefetch", "pressed"]


def test_section_trigger_takes_the_next_section_in_book_order(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, two=True)
    judge = JudgeFake()
    PF.run_trigger(env_for(vault, repository, judge=judge),
                   PF.Trigger("section", f"{TWO}:s1", extraction_id=TWO, section_id="s1"))
    assert [block["text"] for block in judge.contexts[0]["blocks"]][0] == "2 Damping"
    (row,) = decisions(repository)
    assert row["trigger_kind"] == "section" and row["trigger_ref"] == f"{TWO}:s2"
    assert json.loads(row["anchor_json"]) == {"extraction_id": TWO, "span_ids": ["q6"]}
    assert row["horizon_kind"] == "section_read"
    # The last section has no next one.
    assert PF.next_section(env_for(vault, repository), TWO, "s2") is None


def test_offer_trigger_is_anchor_only_and_needs_no_judge(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    judge = JudgeFake()
    PF.run_trigger(env_for(vault, repository, judge=judge),
                   PF.Trigger("offer", "tutor:qe_1", blocks=((EXTRACTION, "p3"),)))
    assert judge.calls == 0
    (row,) = decisions(repository)
    assert row["trigger_kind"] == "offer" and row["p_open_content"] is None and row["goal_text"] is None
    assert row["horizon_kind"] == "thread_closed" and row["decision"] == "build"


def test_lesson_trigger_builds_the_planned_visuals_of_nodes_not_yet_reached(tmp_path, monkeypatch):
    """A stored node carrying a planned ``visual`` (spec §10.4; RW5d P4b's ``write_plan`` node
    ``PlannedVisualV1``): only that node is a candidate (Codex review F8: n3, with no visual, is not),
    built as the lesson step's own request (landing ruling R5: no passage, the delivered passages as
    grounding keys; the end-to-end reuse through the real lesson is in
    ``test_figures_prefetch_review_fixes``)."""

    from learnloop.teacher import service as TS

    _paths, repository, vault = make_vault(tmp_path)
    state = SimpleNamespace(
        lesson_id="les_1", closed=False, landed=["n1"],
        plans=[{"outline": [{"id": "n1", "anchors": ["S1"]},
                            {"id": "n2", "anchors": ["S2"],
                             "visual": {"goal": "slide p, watch the left mass", "anchors": ["S2"]}},
                            {"id": "n3", "anchors": ["S1"]}]}],
        book=SimpleNamespace(passages={"S1": {"extraction_id": EXTRACTION, "span_id": "p2"},
                                       "S2": {"extraction_id": EXTRACTION, "span_id": "p3"}}))
    monkeypatch.setattr(TS, "load_state", lambda repository, lesson_id: state)
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("lesson", "les_1"))
    (row,) = decisions(repository)
    assert row["trigger_ref"] == "les_1:n2" and row["goal_author"] == "teacher"
    assert row["goal_text"] == "slide p, watch the left mass" and row["horizon_kind"] == "lesson_closed"
    (request,) = rows(repository, "figure_requests")
    assert request["goal_author"] == "teacher" and request["origin"] == "prefetch"
    assert json.loads(request["grounding_manifest_json"])["given"] == [[EXTRACTION, "p3"]]
    assert author.contexts[0]["learner_request"] == {"text": "slide p, watch the left mass", "written_by": "teacher"}


def test_gap_trigger_sends_the_statement_and_a_passage_never_an_attempt(tmp_path, monkeypatch):
    from learnloop.figures import learner_state as LS

    _paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(PF, "_touched_topics", lambda env: ["lo_matrices"])
    gap = {"id": "learner_text_gap:g1", "learning_object_id": "lo_matrices", "kind": "named misconception",
           "topic": "Matrices", "statement": "thinks the mass left of zero depends on lambda"}
    monkeypatch.setattr(LS, "open_gap_statements", lambda vault, repository, los: [gap])
    judge = JudgeFake()
    env = env_for(vault, repository, judge=judge, passages=lambda v, r, lo: [("ext_exam", "x1"), (EXTRACTION, "p2")])
    PF.run_trigger(env, PF.Trigger("gap", "gaps"))
    (context,) = judge.contexts
    assert context["mode"] == "gap" and context["unsure_of"] == gap["statement"]
    assert "two-sided exponential" in context["passage"]
    assert not {"attempt", "item", "rubric", "key", "answer"} & set(context)
    (row,) = decisions(repository)
    assert row["trigger_ref"] == "learner_text_gap:g1" and row["goal_author"] == "prefetch"
    assert json.loads(row["anchor_json"]) == {"extraction_id": EXTRACTION, "span_ids": ["p2"]}
    # Decided once: the next pass asks nothing for the same gap.
    PF.run_trigger(env_for(vault, repository, judge=judge, passages=env.passages), PF.Trigger("gap", "gaps"))
    assert judge.calls == 1 and len(decisions(repository)) == 1


# ---------------------------------------------------------------------------
# The judge's listwise contract
# ---------------------------------------------------------------------------

def test_the_section_judges_answer_is_checked_and_retried_once(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    bad = {"blocks": [{"block": "b99", "goal": "", "p_open": 0.5}, {"block": "b3", "goal": "", "p_open": 0.5},
                      {"block": "b3", "goal": "", "p_open": 1.5}, {"block": "b4", "goal": "", "p_open": 0.5}]}
    judge = JudgeFake([bad])
    PF.run_trigger(env_for(vault, repository, judge=judge), PF.Trigger("plan", "dp_1"))
    assert judge.calls == 2
    assert "problems_with_the_last_answer" in judge.contexts[1]
    assert len(decisions(repository)) == 1


def test_a_judge_that_never_answers_well_decides_nothing(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    bad = {"blocks": [{"block": "b99", "goal": "", "p_open": 0.5}]}
    judge, author = JudgeFake([bad, bad]), AuthorFake()
    result = PF.run_trigger(env_for(vault, repository, judge=judge, author=author), PF.Trigger("plan", "dp_1"))
    assert judge.calls == PF.MAX_JUDGE_ATTEMPTS and author.calls == 0 and decisions(repository) == []
    assert any("judge waiting: invalid_output" in note for note in result.notes)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?",
                                  (PF.LEDGER_TASK,)).fetchone()[0] == 0


def test_the_judge_is_never_called_on_a_metered_route_or_with_models_off(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    metered = JudgeFake(provider_type="openrouter")
    result = PF.run_trigger(env_for(vault, repository, judge=metered), PF.Trigger("plan", "dp_1"))
    assert metered.calls == 0 and any("not_plan" in note for note in result.notes)
    # No injected client and LEARNLOOP_FIGURE_MODELS=off (the suite): no real client is reached.
    env = env_for(vault, repository)
    env.judge_client = None
    result = PF.run_trigger(env, PF.Trigger("plan", "dp_1"))
    assert any("models_off" in note for note in result.notes) and decisions(repository) == []


def test_a_metered_author_route_defers_for_the_plan(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake(provider_type="openrouter")
    PF.run_trigger(env_for(vault, repository, author=author),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert [row["decision"] for row in decisions(repository)] == ["deferred_plan"] and author.calls == 0


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------

def test_the_thompson_decision_is_logged_with_its_propensity_and_is_reproducible(tmp_path):
    first, second = [], []
    for out, root in ((first, tmp_path / "a"), (second, tmp_path / "b")):
        _paths, repository, vault = make_vault(root)
        PF.run_trigger(env_for(vault, repository, seed=7),
                       PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
        out.extend((row["sampled_eu"], row["propensity"], row["posterior_digest"]) for row in decisions(repository))
    assert first == second and len(first) == 1


def test_no_measured_wait_means_no_prebuild():
    model = PM.Model(PM.open_posterior([]), PM.pause_posterior([]), PM.waits({}, []), None, 0.0)
    decision = model.decide(PM.Candidate("plan", "src", 0.9), np.random.default_rng(0))
    assert decision.build is False and decision.propensity == 0.0 and decision.w_minutes is None


def test_the_opening_posterior_learns_from_closed_built_decisions():
    opened = [PM.Observation("section", "src_a", 0.9, True) for _ in range(30)]
    ignored = [PM.Observation("offer", "src_a", None, False) for _ in range(30)]
    posterior = PM.open_posterior(opened + ignored)
    summary = posterior.summary()
    assert summary["observations"] == 60
    assert summary["beta_kind"]["offer"]["posterior"]["mean"] < summary["beta_kind"]["section"]["posterior"]["mean"]
    assert summary["alpha"]["posterior"]["sd"] < PM.ALPHA_PRIOR_SD
    assert abs(sum(entry["weight"] for entry in summary["pooling_grid"]) - 1.0) < 1e-6
    waits = PM.waits({"grammar": [0.5, 0.7]}, ["grammar"])
    model = PM.Model(posterior, PM.pause_posterior([]), waits, None, 0.0)
    rng = np.random.default_rng(1)
    section = model.decide(PM.Candidate("section", "src_a", 0.9), rng)
    offer = model.decide(PM.Candidate("offer", "src_a", None), rng)
    assert section.p_open > offer.p_open and 0.0 <= offer.propensity <= 1.0


def test_the_pause_cost_reads_measured_pauses():
    days = [PM.PlanDay(5, 0, False), PM.PlanDay(50, 0, True), PM.PlanDay(8, 0, False), PM.PlanDay(60, 0, True)]
    pause = PM.pause_posterior(days)
    assert pause.days == 4 and pause.pauses == 2 and pause.mean[1] > PM.PAUSE_SLOPE_PRIOR_MEAN - 2
    waits = PM.waits({"manim": [3.0]}, ["manim"])
    busy = PM.Model(PM.open_posterior([]), pause, waits, blocked_minutes=10.0, load_today=60.0)
    quiet = PM.Model(PM.open_posterior([]), pause, waits, blocked_minutes=10.0, load_today=0.0)
    rng = np.random.default_rng(0)
    assert busy.decide(PM.Candidate("plan", None, 0.5), rng).cost_minutes > \
        quiet.decide(PM.Candidate("plan", None, 0.5), np.random.default_rng(0)).cost_minutes


# ---------------------------------------------------------------------------
# Caps, power, the plan's pauses, the foreground
# ---------------------------------------------------------------------------

def test_the_daily_cap_cuts_the_queue_in_sampled_eu_order(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, max_daily_builds=1)
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"))))
    found = sorted(decisions(repository), key=lambda row: -row["sampled_eu"])
    assert [row["decision"] for row in found] == ["build", "capped"] and author.calls == 1


def test_the_render_minutes_cap_holds_every_build(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, max_daily_render_minutes=0)
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert [row["decision"] for row in decisions(repository)] == ["capped"] and author.calls == 0


def test_on_battery_nothing_starts_and_no_judge_is_asked(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    judge, author = JudgeFake(), AuthorFake()
    env = env_for(vault, repository, judge=judge, author=author)
    PF.run_trigger(env, PF.Trigger("plan", "dp_1"))
    PF.run_trigger(env, PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert judge.calls == 0 and author.calls == 0
    assert [row["decision"] for row in decisions(repository)] == ["deferred_power"]


def test_a_background_build_stops_off_mains_before_any_request(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    P.set_power_reader(lambda: P.PowerState(False, P.UNKNOWN, "test"))
    author = AuthorFake()
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="prefetch")
    with pytest.raises(FS.FigureRefused) as refused:
        FS.build_prefetch_figure(vault, repository, request, author_client=author)
    assert refused.value.code == "figures_changed" and author.calls == 0
    assert P.background_hold(vault) == P.NOT_ON_MAINS


def test_a_plan_pause_is_recorded_once_and_defers_the_builds(tmp_path):
    from learnloop.clock import utc_now_iso

    _paths, repository, vault = make_vault(tmp_path)
    pause = {"code": "usage_limit", "at": utc_now_iso(), "id": "abc"}
    author = AuthorFake()
    env = env_for(vault, repository, author=author, pause_reader=lambda: pause)
    PF.run_trigger(env, PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    PF.run_trigger(env, PF.Trigger("offer", "tutor:r", blocks=((EXTRACTION, "p6"),)))
    with repository.connection() as connection:
        (recorded,) = [dict(row) for row in connection.execute("SELECT * FROM plan_usage_pauses")]
    assert recorded["reset_at"] > recorded["hit_at"]
    assert {row["decision"] for row in decisions(repository)} == {"deferred_plan"} and author.calls == 0


def test_prebuilds_yield_to_foreground_work_and_resume_on_the_next_pass(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    with FG.foreground("lesson"):
        result = PF.run_trigger(env_for(vault, repository, author=author),
                                PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert author.calls == 0 and any("yielded" in note for note in result.notes)
    (row,) = decisions(repository)
    assert row["decision"] == "build" and row["request_id"] is None
    # Idle again: the next pass (any trigger) builds what waited, deciding nothing twice.
    PF.run_trigger(env_for(vault, repository, author=author), PF.Trigger("offer", "tutor:q", blocks=()))
    (row,) = decisions(repository)
    assert author.calls == 1 and row["request_id"] is not None


def test_the_switch_going_off_stops_the_queue(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    author = AuthorFake()
    switch(paths, False)
    off = load_vault(paths.root)
    env = env_for(vault, repository, author=author, live_vault=lambda: off)
    result = PF.run_trigger(env, PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert author.calls == 0 and any("switched off" in note for note in result.notes)


# ---------------------------------------------------------------------------
# Origin, listing, outcomes, the report
# ---------------------------------------------------------------------------

def test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake())
    with pytest.raises(SidecarError) as refused:
        call(ctx, "figure.request", {"origin": "prefetch", "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}})
    assert refused.value.code == "validation_error"
    with pytest.raises(FS.FigureRefused) as direct:
        FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="prefetch"),
                        author_client=AuthorFake())
    assert direct.value.code == "validation_error"


def test_a_prebuilt_figure_lists_only_while_on_or_once_pressed(tmp_path):
    paths, repository, vault = make_vault(tmp_path)
    PF.run_trigger(env_for(vault, repository), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    assert len(FS.list_figures(vault, repository, EXTRACTION)) == 1
    switch(paths, False)
    off = load_vault(paths.root)
    assert off.config.figures.prefetch_enabled is False
    assert FS.list_figures(off, repository, EXTRACTION) == []
    build(context(paths.root, author=AuthorFake()), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert len(FS.list_figures(off, repository, EXTRACTION)) == 1


def test_outcomes_close_once_at_the_structural_horizon(tmp_path, monkeypatch):
    paths, repository, vault = make_vault(tmp_path, two=True)
    PF.run_trigger(env_for(vault, repository), PF.Trigger("section", "x", extraction_id=TWO, section_id="s1"))
    (built,) = decisions(repository)
    assert PF.close_horizons(env_for(vault, repository)) == 0  # s2 not read yet
    figure_id = rows(repository, "interactive_figures")[0]["id"]
    log_interaction_event(repository, kind="reader_action_invoked", origin="learner", subject_type="reader_extraction",
                          subject_id=TWO, payload=salience_payload({"event": "figure_opened", "figure_id": figure_id}))
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True)
    assert PF.close_horizons(env_for(vault, repository)) == 1
    (row,) = decisions(repository)
    assert row["id"] == built["id"] and row["outcome"] == "opened" and row["outcome_at"]
    assert PF.close_horizons(env_for(vault, repository)) == 0


def test_unbuilt_candidates_close_asked_or_neither_and_withheld_ones_void(tmp_path, monkeypatch):
    paths, repository, vault = make_vault(tmp_path, wait=False)  # no measured wait: every decision is a skip
    PF.run_trigger(env_for(vault, repository),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"), (EXTRACTION, "p2"))))
    assert {row["decision"] for row in decisions(repository)} == {"skip"}
    build(context(paths.root, author=AuthorFake()), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    real = FS.withheld_message
    monkeypatch.setattr(FS, "withheld_message", lambda v, r, e, spans: "held out" if "p2" in spans else real(v, r, e, spans))
    tomorrow = FrozenClock(datetime(2099, 1, 2, tzinfo=UTC))
    assert PF.close_horizons(env_for(vault, repository, clock=tomorrow)) == 3
    outcomes = {json.loads(row["anchor_json"])["span_ids"][0]: row["outcome"] for row in decisions(repository)}
    assert outcomes == {"p3": "asked", "p6": "neither", "p2": "void"}


def test_the_report_block_appears_only_with_the_switch(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    _paths, repository, vault = make_vault(tmp_path)
    PF.run_trigger(env_for(vault, repository), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    on = PL.add_report_block(build_reader_report(repository.sqlite_path, figures_enabled=True),
                             repository.sqlite_path, plan_providers=PL.plan_providers(vault))
    block = on["figures"]["prefetch"]
    assert block["decisions_by_trigger"]["offer"]["built"] == 1
    assert set(block) >= {"posterior", "measured_wait", "pauses", "skipped"}
    assert block["posterior"]["opening"]["alpha"]["prior"] == {"mean": 1.0, "sd": 1.0}
    off = build_reader_report(repository.sqlite_path, figures_enabled=True)
    assert "prefetch" not in off["figures"]


# ---------------------------------------------------------------------------
# The sidecar
# ---------------------------------------------------------------------------

def test_reading_progress_queues_the_section_trigger_on_the_desktop_only(tmp_path):
    paths, repository, _vault = make_vault(tmp_path, two=True)
    ctx = context(paths.root, author=AuthorFake())
    ctx.figure_prefetch_inline = True
    ctx.figure_prefetch_judge_client = judge = JudgeFake()
    ctx.figure_prefetch_pause_reader = lambda: None
    ctx.figure_prefetch_rng = np.random.default_rng(0)
    call(ctx, "reader.mark_section_progress", {"extractionId": TWO, "sectionId": "s1", "spansSeen": 1,
                                              "spanCount": 3})
    assert judge.calls == 1
    assert [row["trigger_ref"] for row in decisions(repository)] == [f"{TWO}:s2"]
    from learnloop_sidecar.prefetch_runtime import notify

    ctx.secondary = True  # a phone or MCP host never runs prefetch
    assert notify(ctx, "section", "x", extraction_id=TWO, section_id="s1") is False


def test_the_gap_worker_fires_the_gap_trigger_after_a_drain(monkeypatch):
    from learnloop.diagnosis.text_gaps import jobs
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    results = [SimpleNamespace(state="done"), None]
    monkeypatch.setattr(jobs, "process_next_gap_job", lambda *args, **kwargs: results.pop(0))
    worker = PostAttemptWorker(autostart=False)
    fired: list[int] = []
    worker.after_gaps = lambda: fired.append(1)
    worker._run_gaps(SimpleNamespace(root=Path(".")), None, max_jobs=5, clock=None)
    assert fired == [1]
    worker._run_gaps(SimpleNamespace(root=Path(".")), None, max_jobs=5, clock=None) if results else None
    assert fired == [1]


# ---------------------------------------------------------------------------
# power_state()
# ---------------------------------------------------------------------------

def _supply(root: Path, name: str, **files: str) -> None:
    folder = root / name
    folder.mkdir(parents=True)
    for key, value in files.items():
        (folder / key).write_text(value + "\n", encoding="utf-8")


def test_power_state_reads_linux_supplies_and_fails_closed(tmp_path):
    profile = lambda: "balanced"  # noqa: E731
    none = tmp_path / "none"
    none.mkdir()
    assert P.linux_power_state(none, profile=profile).on_mains is True  # no battery listed (a desktop)
    assert P.linux_power_state(tmp_path / "missing", profile=profile).reason == P.UNKNOWN  # no inventory
    desk = tmp_path / "desk"
    _supply(desk, "BAT0", type="Battery", status="Charging")
    _supply(desk, "AC", type="Mains", online="1")
    assert P.linux_power_state(desk, profile=profile).on_mains is True
    laptop = tmp_path / "laptop"
    _supply(laptop, "BAT0", type="Battery", status="Discharging")
    _supply(laptop, "AC", type="Mains", online="0")
    assert P.linux_power_state(laptop, profile=profile).reason == P.BATTERY
    unplugged = tmp_path / "unplugged"
    _supply(unplugged, "BAT0", type="Battery", status="Unknown")
    assert P.linux_power_state(unplugged, profile=profile).on_mains is False
    mouse = tmp_path / "mouse"
    _supply(mouse, "hidpp_battery_0", type="Battery", status="Discharging", scope="Device")
    assert P.linux_power_state(mouse, profile=profile).on_mains is True
    assert P.linux_power_state(desk, profile=lambda: "power-saver").reason == P.POWER_SAVER
    P.set_power_reader(lambda: (_ for _ in ()).throw(OSError("boom")))
    assert P.power_state().on_mains is False


def test_mac_power_state_reads_pmset():
    def run(output: str):
        return lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=output)

    assert P.mac_power_state(run("Now drawing from 'AC Power'")).on_mains is True
    assert P.mac_power_state(run("Now drawing from 'Battery Power'")).on_mains is False
    assert P.mac_power_state(run("?")).reason == P.UNKNOWN


def test_the_ledger_reads_nothing_before_migration_236(tmp_path):
    database = tmp_path / "empty.sqlite"
    sqlite3.connect(database).close()
    with sqlite3.connect(database) as connection:
        assert PL.decisions(connection) == [] and PL.pauses(connection) == []
        assert PL.has_tables(connection) is False

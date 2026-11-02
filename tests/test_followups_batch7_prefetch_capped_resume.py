"""Follow-ups batch 7 (A): a decision capped for today's budget resumes while its horizon is open.

A positive decision became ``capped`` when today's capacity was exhausted, and that was final:
``pending_builds`` left it out, so the next day, with the section still unread and capacity free,
no build ran and the row stayed open (Codex verify job 20261102-181511-QNGSpd, P2).

Now a capped decision waits as a power-deferred one does: the same queue, every background guard
again, plus both caps rechecked before any request; no new draw (the original row and its propensity
stay the record); the report and the model count the build. A closed horizon stays closed. Fakes for
the judge and the author; the real pass, its real model and real rows.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import FrozenClock
from learnloop.db.stores import figures as figure_store
from learnloop.figures import foreground as FG
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import prefetch_model as PM
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.ops.settings_store import apply_config_updates
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import EXTRACTION, AuthorFake, rows
from tests.test_figures_prefetch import TWO, count, decisions, env_for, make_vault, mains, switch  # noqa: F401

DAY_ONE = datetime(2099, 3, 1, 12, tzinfo=UTC)
DAY_TWO = DAY_ONE + timedelta(days=1)
DAY_THREE = DAY_ONE + timedelta(days=2)
SECTION = PF.Trigger("section", "x", extraction_id=TWO, section_id="s1")
OFFER = PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),))
#: A later section trigger that names nothing new (s2 has no following section): only the queue runs.
LATER = PF.Trigger("section", "x", extraction_id=TWO, section_id="s2")


def _clock(when: datetime) -> FrozenClock:
    return FrozenClock(when)


def _caps(paths: Any, **values: Any) -> None:
    """Set ``figures.prefetch`` keys, whether the vault's file has them yet or not."""

    apply_config_updates(paths.root / "learnloop.toml",
                         {("figures", "prefetch", key): value for key, value in values.items()})


def _section_row(repository: Any) -> dict[str, Any]:
    return next(row for row in decisions(repository) if row["trigger_kind"] == "section")


def _capped_section(tmp_path: Any, **config: Any) -> tuple[Any, Any, Any, AuthorFake, dict[str, Any]]:
    """Day one: an offer takes the day's one build, so the next section's decision is ``capped``."""

    paths, repository, vault = make_vault(tmp_path, two=True, max_daily_builds=1, **config)
    author = AuthorFake()
    day_one = env_for(vault, repository, author=author, clock=_clock(DAY_ONE))
    PF.run_trigger(day_one, OFFER)
    PF.run_trigger(day_one, SECTION)
    row = _section_row(repository)
    assert row["decision"] == "capped" and row["request_id"] is None and row["outcome"] is None
    assert author.calls == 1
    return paths, repository, vault, author, row


@pytest.fixture
def draws(monkeypatch):
    """Every draw the model makes."""

    made: list[Any] = []
    real = PM.Model.decide

    def decide(self: Any, candidate: Any, rng: Any) -> Any:
        made.append(candidate)
        return real(self, candidate, rng)

    monkeypatch.setattr(PM.Model, "decide", decide)
    return made


def test_a_capped_decision_is_built_the_next_day_with_no_new_draw_and_its_row_stays_the_record(tmp_path, draws):
    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    before = len(decisions(repository))
    made = len(draws)
    result = PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), LATER)
    assert result.built == [capped["id"]] and author.calls == 2
    assert len(decisions(repository)) == before and len(draws) == made  # no new row, no new draw
    row = _section_row(repository)
    assert row["request_id"] is not None and row["input_hash"] is not None and row["outcome"] is None
    # What was decided stays as it was decided: the row and its propensity are the record.
    for column in ("id", "decision", "propensity", "sampled_eu", "posterior_digest", "created_at", "w_minutes",
                   "cost_minutes", "p_open_content", "request_key"):
        assert row[column] == capped[column], column
    with repository.connection() as connection:
        assert PL.started_today(connection, today="2099-03-02", offset=timedelta(0)) == {capped["id"]}
        assert PL.started_today(connection, today="2099-03-01", offset=timedelta(0)) != {capped["id"]}


def test_a_pass_with_unchanged_inputs_adds_no_row_and_no_draw_and_its_capped_job_fires_nothing(tmp_path, draws):
    _paths, repository, vault, author, _capped = _capped_section(tmp_path)
    before = decisions(repository)
    made = len(draws)
    day_one = env_for(vault, repository, author=author, clock=_clock(DAY_ONE))
    for trigger in (SECTION, LATER, SECTION):  # the same day: the cap stays exhausted
        result = PF.run_trigger(day_one, trigger)
        assert result.decisions == [] and result.built == []
        assert any("used up" in note for note in result.notes)
    assert author.calls == 1 and len(draws) == made
    assert decisions(repository) == before


def test_exhausted_render_minutes_fire_no_request_and_the_next_budget_builds_it(tmp_path, draws):
    paths, repository, vault = make_vault(tmp_path, two=True, max_daily_render_minutes=0)
    author = AuthorFake()
    PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_ONE)), SECTION)
    (capped,) = decisions(repository)
    assert capped["decision"] == "capped" and author.calls == 0
    made = len(draws)
    # A new day, the render budget still nil: the build cap has room, but no request goes out.
    result = PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), SECTION)
    assert author.calls == 0 and result.built == [] and any("render minutes" in note for note in result.notes)
    assert count(repository, "figure_requests") == 0
    # And nothing was reserved for it: the day's builds are still all there.
    assert PF.started_today(env_for(vault, repository, clock=_clock(DAY_TWO))) == set()
    _caps(paths, max_daily_render_minutes=30)
    result = PF.run_trigger(env_for(load_vault(paths.root), repository, author=author, clock=_clock(DAY_THREE)), SECTION)
    assert result.built == [capped["id"]] and author.calls == 1 and len(draws) == made
    assert len(decisions(repository)) == 1


def test_a_decision_whose_horizon_closed_stays_closed(tmp_path):
    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_ONE + timedelta(hours=1)))
    for when in (DAY_TWO, DAY_THREE):
        result = PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(when)), LATER)
        assert result.built == []
    row = _section_row(repository)
    assert row["id"] == capped["id"] and row["outcome"] == "neither" and row["request_id"] is None
    assert author.calls == 1


@pytest.mark.parametrize("guard", ["battery", "foreground", "paused", "switched_off", "not_the_plan", "rich_in_flight",
                                   "protected", "cancelled"])
def test_every_background_guard_a_power_deferred_resume_rechecks_holds_a_capped_one(tmp_path, monkeypatch, guard):
    paths, repository, vault, author, capped = _capped_section(tmp_path)
    kwargs: dict[str, Any] = {}
    if guard == "battery":
        P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    elif guard == "paused":
        kwargs["pause_reader"] = lambda: {"code": "usage_limit", "at": DAY_TWO.isoformat(), "id": "x"}
    elif guard == "switched_off":
        switch(paths, False)
        kwargs["live_vault"] = lambda: load_vault(paths.root)
    elif guard == "not_the_plan":
        monkeypatch.setattr(PF, "_author_ready", lambda env: "ai.routing.figure_author is not the ChatGPT plan")
    elif guard == "rich_in_flight":
        monkeypatch.setattr(PF, "rich_in_flight", lambda env: True)
    elif guard == "protected":
        monkeypatch.setattr(PF, "protected", lambda env, candidate, protection: True)
    elif guard == "cancelled":
        kwargs["cancelled"] = lambda: True
    env = env_for(vault, repository, author=author, clock=_clock(DAY_TWO), **kwargs)
    if guard == "foreground":
        with FG.foreground("lesson"):
            PF.run_trigger(env, LATER)
    else:
        PF.run_trigger(env, LATER)
    assert author.calls == 1, guard
    row = _section_row(repository)
    assert row["id"] == capped["id"] and row["request_id"] is None and row["outcome"] is None, guard


def test_the_report_and_the_model_count_a_resumed_build(tmp_path):
    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    with repository.connection() as connection:
        block = PL.report_block(connection, now=DAY_ONE)
    section = block["decisions_by_trigger"]["section"]
    assert section["decisions"] == {"capped": 1} and section["built"] == 0 and section["open"] == 1
    assert block["skipped"]["caps"] == 1 and block["resumed"]["caps"] == 0
    PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), LATER)
    # A pause the day it was built, after it: a prebuild earlier that day, whatever day it was decided on.
    hit = DAY_TWO + timedelta(hours=1)
    with repository.connection() as connection:
        connection.execute("INSERT INTO plan_usage_pauses (id, hit_at, reset_at, plan_requests_today, "
                           "plan_tokens_today_known, observed_at) VALUES ('pup_1', ?, ?, 0, 0, ?)",
                           (hit.isoformat(), (hit + timedelta(hours=1)).isoformat(), hit.isoformat()))
        connection.commit()
    with repository.connection() as connection:
        block = PL.report_block(connection, now=hit)
    section = block["decisions_by_trigger"]["section"]
    assert section["decisions"] == {"capped": 1} and section["built"] == 1 and section["open"] == 1
    # Built, it is no longer a build the caps skipped.
    assert block["skipped"]["caps"] == 0 and block["resumed"] == {"power": 0, "plan": 0, "caps": 1}
    assert block["pauses"] == {"count": 1, "with_prebuilds_earlier_that_day": 1, "without_prebuilds": 0}
    # Closed, the build is an observation of opening, as a power-deferred one's is.
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_TWO + timedelta(hours=2)))
    PF.close_horizons(env_for(vault, repository, clock=_clock(DAY_TWO + timedelta(hours=3))))
    row = _section_row(repository)
    assert row["outcome"] == "neither"
    observed = [item for item in PL.observations(decisions(repository)) if item.trigger_kind == "section"]
    assert len(observed) == 1 and observed[0].opened is False


def test_a_capped_decision_that_never_built_is_no_observation(tmp_path):
    _paths, repository, vault, author, _capped = _capped_section(tmp_path)
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_ONE + timedelta(hours=1)))
    PF.close_horizons(env_for(vault, repository, clock=_clock(DAY_TWO)))
    assert _section_row(repository)["outcome"] == "neither"
    assert not [item for item in PL.observations(decisions(repository)) if item.trigger_kind == "section"]


def test_the_highest_sampled_eu_of_a_capped_batch_goes_first(tmp_path):
    paths, repository, vault = make_vault(tmp_path, max_daily_builds=0)
    author = AuthorFake()
    both = PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"), (EXTRACTION, "p2")))
    PF.run_trigger(env_for(vault, repository, author=author), both)
    capped = decisions(repository)
    assert {row["decision"] for row in capped} == {"capped"} and len(capped) == 3 and author.calls == 0
    best = max(capped, key=lambda row: row["sampled_eu"])
    _caps(paths, max_daily_builds=1)
    result = PF.run_trigger(env_for(load_vault(paths.root), repository, author=author), both)
    assert result.built == [best["id"]] and author.calls == 1


# ---------------------------------------------------------------------------
# The press came first, and a planned visual stays the lesson step's own request
# ---------------------------------------------------------------------------

def test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds(tmp_path):
    paths, repository, vault, author, capped = _capped_section(tmp_path)
    pressed = FS.FigureRequest(extraction_id=TWO, span_ids=["q6"], origin="selection")
    FS.build_figure(vault, repository, pressed, author_client=author, clock=_clock(DAY_ONE + timedelta(hours=1)))
    assert author.calls == 2
    requests = count(repository, "figure_requests")
    env = env_for(vault, repository, author=author, clock=_clock(DAY_TWO))
    result = PF.run_trigger(env, LATER)
    # Nothing to build: no request recorded for the decision, none of today's builds spent on it.
    assert result.built == [] and author.calls == 2 and count(repository, "figure_requests") == requests
    assert PF.started_today(env) == set()
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_TWO + timedelta(hours=1)))
    PF.close_horizons(env_for(vault, repository, clock=_clock(DAY_TWO + timedelta(hours=2))))
    row = _section_row(repository)
    # Demand without the cue: the press is an ask, never an observation of opening a prebuild.
    assert row["id"] == capped["id"] and row["outcome"] == "asked" and row["request_id"] is None
    assert not [item for item in PL.observations(decisions(repository)) if item.trigger_kind == "section"]


def test_a_decision_whose_build_stored_its_request_but_never_linked_it_is_still_linked(tmp_path, monkeypatch):
    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(PF, "_link", lambda env, decision_id: None)  # the pass died before it linked
        PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), LATER)
    assert author.calls == 2 and _section_row(repository)["request_id"] is None
    PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), LATER)
    assert author.calls == 2  # reused, no new request
    assert _section_row(repository)["request_id"] is not None


@pytest.mark.parametrize("deferral", ["capped", "deferred_power"])
def test_a_resumed_planned_visual_is_the_lesson_steps_own_request(tmp_path, deferral):
    """``pending_builds`` rebuilt a lesson's candidate from its anchor alone, so a resumed planned
    visual was built on that passage, with a rich job on the menu, under an input hash the step
    never asks for. It is the very request the step will make, as a fresh one is (landing ruling R5)."""

    from learnloop.teacher import service as S
    from tests.test_figures_prefetch_review_fixes import _planned_lesson
    from tests.test_reader_rw5d_p4b_teacher_visuals import _clients, _spec

    author = AuthorFake([_spec()])
    paths, repository, fake, build, view = _planned_lesson(tmp_path, author)
    lesson_id = view["lesson_id"]
    trigger = PF.Trigger("lesson", lesson_id)
    if deferral == "capped":
        _caps(paths, max_daily_builds=0)
    else:
        P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    PF.run_trigger(env_for(load_vault(paths.root), repository, author=author), trigger)
    (row,) = decisions(repository)
    assert row["decision"] == deferral and author.calls == 0
    _caps(paths, max_daily_builds=10)
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    result = PF.run_trigger(env_for(load_vault(paths.root), repository, author=author), trigger)
    assert result.built == [row["id"]] and author.calls == 1
    (prebuilt,) = rows(repository, "interactive_figures")
    assert prebuilt["origin"] == "prefetch" and prebuilt["extraction_id"] is None
    assert decisions(repository)[0]["input_hash"] == prebuilt["input_hash"]
    # The step delivers it with no author call.
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply", payload={"text": "go"},
                clients=_clients(fake, build))
    assert author.calls == 1 and len(rows(repository, "interactive_figures")) == 1


def test_a_planned_visual_the_lesson_no_longer_plans_is_not_built(tmp_path, monkeypatch):
    from tests.test_figures_prefetch_review_fixes import _planned_lesson
    from tests.test_reader_rw5d_p4b_teacher_visuals import _spec

    author = AuthorFake([_spec()])
    paths, repository, _fake, _build, view = _planned_lesson(tmp_path, author)
    trigger = PF.Trigger("lesson", view["lesson_id"])
    _caps(paths, max_daily_builds=0)
    PF.run_trigger(env_for(load_vault(paths.root), repository, author=author), trigger)
    (row,) = decisions(repository)
    assert row["decision"] == "capped"
    _caps(paths, max_daily_builds=10)
    monkeypatch.setattr(PF, "_lesson_candidates", lambda env, lesson_id: [])  # replanned, or the node landed
    result = PF.run_trigger(env_for(load_vault(paths.root), repository, author=author), trigger)
    assert result.built == [] and author.calls == 0
    assert decisions(repository)[0]["request_id"] is None


# ---------------------------------------------------------------------------
# The Reader's "a prebuild is coming"
# ---------------------------------------------------------------------------

def test_a_capped_decision_is_coming_only_while_the_budget_has_room(tmp_path):
    paths, repository, vault = make_vault(tmp_path, max_daily_builds=1)
    PF.run_trigger(env_for(vault, repository, author=AuthorFake()),
                   PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p6"))))
    assert {row["decision"] for row in decisions(repository) if not row["request_id"]} == {"capped"}
    # The day's one build is spent: a read must not poll for work no pass will do today.
    assert FS.prefetch_pending(vault, repository, EXTRACTION, pass_running=True) is False
    _caps(paths, max_daily_builds=2)
    raised = load_vault(paths.root)
    assert FS.prefetch_pending(raised, repository, EXTRACTION, pass_running=True) is True
    assert FS.prefetch_pending(raised, repository, EXTRACTION) is False  # no pass running: nobody will build it
    _caps(paths, max_daily_render_minutes=0)
    assert FS.prefetch_pending(load_vault(paths.root), repository, EXTRACTION, pass_running=True) is False


# ---------------------------------------------------------------------------
# Codex review F1: a stored request is linked before horizons close and before any build guard
# ---------------------------------------------------------------------------

def _stored_unlinked(monkeypatch: Any, tmp_path: Any) -> tuple[Any, Any, Any, AuthorFake, dict[str, Any], dict[str, Any]]:
    """Day two: the resumed build stored its request and quick figure, and the pass died before ``_link``."""

    paths, repository, vault, author, capped = _capped_section(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(PF, "_link", lambda env, decision_id: None)
        PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO)), LATER)
    assert author.calls == 2 and _section_row(repository)["request_id"] is None
    (request,) = [row for row in rows(repository, "figure_requests") if row["prefetch_decision_id"] == capped["id"]]
    assert request["figure_id"]
    return paths, repository, vault, author, capped, request


def _opened_at(repository: Any, figure_id: str, when: datetime) -> None:
    log_interaction_event(repository, kind="reader_action_invoked", origin="learner", subject_type="reader_extraction",
                          subject_id=TWO, payload=salience_payload({"event": "figure_opened", "figure_id": figure_id}),
                          clock=_clock(when))


@pytest.mark.parametrize("blocker", ["render_minutes", "todays_builds", "battery", "rich_job_in_flight"])
def test_a_stored_request_is_linked_whatever_holds_new_builds_and_its_opening_is_observed(tmp_path, monkeypatch, blocker):
    paths, repository, vault, author, capped, request = _stored_unlinked(monkeypatch, tmp_path)
    _opened_at(repository, request["figure_id"], DAY_TWO + timedelta(minutes=30))
    when = DAY_TWO + timedelta(hours=1)
    if blocker == "render_minutes":
        _caps(paths, max_daily_render_minutes=0)
    elif blocker == "todays_builds":
        _caps(paths, max_daily_builds=0)
        when = DAY_THREE  # the request is yesterday's, so today's cap does not count it as started
    elif blocker == "battery":
        P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    else:
        monkeypatch.setattr(PF, "rich_in_flight", lambda env: True)
    current = load_vault(paths.root)
    result = PF.run_trigger(env_for(current, repository, author=author, clock=_clock(when)), LATER)
    # Bookkeeping: no model call, no build, nothing of today's budget.
    assert author.calls == 2 and result.built == []
    row = _section_row(repository)
    assert row["id"] == capped["id"] and row["request_id"] == request["id"] and row["input_hash"]
    assert len([item for item in rows(repository, "figure_requests") if item["prefetch_decision_id"] == capped["id"]]) == 1
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(when + timedelta(hours=1)))
    PF.run_trigger(env_for(current, repository, author=author, clock=_clock(when + timedelta(hours=2))), LATER)
    row = _section_row(repository)
    assert row["outcome"] == "opened" and author.calls == 2
    (observed,) = [item for item in PL.observations(decisions(repository)) if item.trigger_kind == "section"]
    assert observed.opened is True
    with repository.connection() as connection:
        block = PL.report_block(connection, now=when + timedelta(hours=2))
    assert block["decisions_by_trigger"]["section"]["built"] == 1 and block["skipped"]["caps"] == 0


def test_a_stored_request_is_linked_when_its_horizon_passed_before_the_next_pass(tmp_path, monkeypatch):
    """The same pass closes it, so the link comes first, with no budget to run out at all."""

    _paths, repository, vault, author, _capped, request = _stored_unlinked(monkeypatch, tmp_path)
    _opened_at(repository, request["figure_id"], DAY_TWO + timedelta(minutes=30))
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_TWO + timedelta(hours=1)))
    PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO + timedelta(hours=2))), LATER)
    row = _section_row(repository)
    assert row["request_id"] == request["id"] and row["outcome"] == "opened" and author.calls == 2


def test_close_horizons_itself_links_first(tmp_path, monkeypatch):
    _paths, repository, vault, _author, _capped, request = _stored_unlinked(monkeypatch, tmp_path)
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True, clock=_clock(DAY_TWO + timedelta(hours=1)))
    PF.close_horizons(env_for(vault, repository, clock=_clock(DAY_TWO + timedelta(hours=2))))
    row = _section_row(repository)
    # Built and not opened: an observation of not opening, not a decision with no build.
    assert row["request_id"] == request["id"] and row["outcome"] == "neither"
    (observed,) = [item for item in PL.observations(decisions(repository)) if item.trigger_kind == "section"]
    assert observed.opened is False


def _orphan_request(repository: Any, decision_id: str, when: datetime) -> str:
    """A rich-only build's request whose job never started (the enqueue failed, or the sidecar stopped)."""

    asked = FS._request_row(FS.FigureRequest(extraction_id=TWO, span_ids=["q6"], origin="prefetch",
                                             prefetch_decision_id=decision_id),
                            FS.Grounding("anchor"), figure_id=None, clock=_clock(when))
    with repository.atomic():
        figure_store.insert_request(repository.connection(), asked)
    return str(asked["id"])


def test_a_request_with_no_figure_and_no_job_is_not_linked_and_its_build_is_still_retried(tmp_path):
    """Linking this one would drop the retry: nothing was built, so nothing could ever be opened."""

    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    orphan = _orphan_request(repository, capped["id"], DAY_TWO)
    PF.close_horizons(env_for(vault, repository, clock=_clock(DAY_TWO + timedelta(minutes=1))))
    assert _section_row(repository)["request_id"] is None
    env = env_for(vault, repository, author=author, clock=_clock(DAY_TWO + timedelta(minutes=2)))
    result = PF.run_trigger(env, LATER)
    assert result.built == [capped["id"]] and author.calls == 2
    # Linked to the request that holds the figure, or an opening of it could never be seen.
    linked = _section_row(repository)["request_id"]
    assert linked != orphan
    (served,) = [row for row in rows(repository, "figure_requests") if row["id"] == linked]
    assert served["figure_id"]


def test_a_rich_only_request_whose_job_exists_is_linked_with_no_figure_yet(tmp_path, monkeypatch):
    _paths, repository, vault, author, capped = _capped_section(tmp_path)
    orphan = _orphan_request(repository, capped["id"], DAY_TWO)
    monkeypatch.setattr(PF, "rich_in_flight", lambda env: True)
    monkeypatch.setattr(RICH, "rich_job_for_request",
                        lambda repo, request_id: {"id": "job_1"} if request_id == orphan else None)
    result = PF.run_trigger(env_for(vault, repository, author=author, clock=_clock(DAY_TWO + timedelta(minutes=1))), LATER)
    assert result.built == [] and author.calls == 1
    assert _section_row(repository)["request_id"] == orphan

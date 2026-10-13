"""Daily-loop DL1: regressions for the Codex review findings (F1-F10) and its re-review (F11-F13).

Each test reproduces one finding against the fixed engine. Fakes only: the
plan reads the scheduler's ranked list through ``PlanEnv.eligible`` (or the
real ``build_due_queue`` where the finding is about real scheduler
components), and no model or embedding client is ever constructed.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.daily_plan.engine import PlanEnv, get_or_create_today
from learnloop.db.repositories import MasteryState, Repository
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.daily_plan_fakes import NOW, MovableClock, iso, record_attempt, seed_open_problem
from tests.helpers import ALGORITHM_VERSION, create_daily_plan_vault


def _no_goals(paths: VaultPaths) -> None:
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})


def _ended_session(repository: Repository, session_id: str, moment) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, available_minutes) VALUES (?, ?, ?, 40)",
            (session_id, iso(moment - timedelta(minutes=30)), iso(moment)),
        )
        connection.commit()


# -- F1: never-attempted items are new material, and repair has a bound --
# (the recency bound is the fallback while the diagnosis split is off; with it
# on, repair is an open diagnosed problem: owner decision 2026-10-12)


def _failed_and_unseen(tmp_path, *, error_days_ago: float, plan_toml: str | None = None):
    """One LO with a failed (attempted) item and an unseen sibling, real scheduler state."""

    paths = create_daily_plan_vault(
        tmp_path / "vault",
        learning_objects={"lo_err": [("pi_failed", 1.0), ("pi_unseen", 1.0)]},
        plan_toml=plan_toml,
    )
    _no_goals(paths)
    repository = Repository(paths.sqlite_path)
    failed_at = NOW - timedelta(days=error_days_ago)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_err",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at=iso(failed_at),
            algorithm_version=ALGORITHM_VERSION,
            updated_at=iso(failed_at),
        )
    )
    repository.upsert_practice_item_state(
        "pi_failed",
        difficulty=6.0,
        stability=1.0,
        due_at=iso(failed_at + timedelta(days=1)),
        last_attempt_at=iso(failed_at),
        active=True,
    )
    _ended_session(repository, "s_failed", failed_at + timedelta(minutes=5))
    record_attempt(repository, "pi_failed", "lo_err", failed_at, session_id="s_failed")
    repository.insert_error_event(
        {
            "id": "err_failed",
            "learning_object_id": "lo_err",
            "error_type": "conceptual_slip",
            "severity": 0.9,
            "is_misconception": False,
            "status": "active",
            "created_at": iso(failed_at),
            "updated_at": iso(failed_at),
        }
    )
    vault = load_vault(paths.root)
    env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(NOW))
    return env


def _real_components(env):
    queue = build_due_queue(env.vault, env.repository, clock=env.clock, limit=None)
    return {item.practice_item_id: item.components for item in queue}


def test_f1_reentry_never_plans_an_unseen_sibling_of_an_old_error(tmp_path):
    env = _failed_and_unseen(tmp_path, error_days_ago=80)
    components = _real_components(env)
    # The real scheduler: the unseen sibling is eligible and its recent_error
    # never reaches zero, however old the error.
    assert "pi_unseen" in components and 0 < components["pi_unseen"]["recent_error"] < 1e-3
    record = get_or_create_today(env)
    assert record.kind == "reentry"
    planned = {item.practice_item_id: item.lane for item in record.items()}
    pool = {row["practice_item_id"]: row["lane"] for row in record.split["pool"]}
    assert "pi_unseen" not in planned and "pi_unseen" not in pool  # new material: not in re-entry
    # An 80-day-old error is not "recent": the due failed item is maintenance.
    assert planned.get("pi_failed") == "maintain"
    assert all(lane != "repair" for lane in planned.values())


def test_f1_an_open_diagnosis_repairs_the_failed_item_and_the_unseen_one_is_new(tmp_path):
    # Owner decision 2026-10-12 (at DL1's merge): with the diagnosis split on,
    # repair is an open diagnosed problem, not a recent error, so the failed
    # item's LO carries an unresolved hypothesis here. A recent error alone is
    # a due review (tests/test_daily_plan_owner_decisions.py).
    env = _failed_and_unseen(tmp_path, error_days_ago=1)
    seed_open_problem(env.repository, "lo_err")
    components = _real_components(env)
    assert components["pi_unseen"]["recent_error"] > 0.5
    record = get_or_create_today(env)
    assert record.kind == "normal"
    pool = {row["practice_item_id"]: row["lane"] for row in record.split["pool"]}
    assert pool["pi_failed"] == "repair"
    assert pool["pi_unseen"] == "new"
    admitted = {row["practice_item_id"] for row in record.admission["admitted"]}
    assert "pi_unseen" in admitted
    planned = {item.practice_item_id: item for item in record.items()}
    if "pi_unseen" in planned:
        assert planned["pi_unseen"].lane == "new" and planned["pi_unseen"].new_admitted


def test_f1_admission_off_serves_no_never_attempted_item(tmp_path):
    env = _failed_and_unseen(tmp_path, error_days_ago=1, plan_toml="[plan]\nnew_admission_enabled = false\n")
    record = get_or_create_today(env)
    assert record.admission["stopped_by"] == "admission_disabled"
    seen = set()
    for _ in range(10):
        from learnloop.daily_plan.engine import advance

        record, step = advance(env, serve=False)
        if step["kind"] != "item":
            break
        seen.add(step["practice_item_id"])
        advance(env, serve=False, skip_practice_item_id=step["practice_item_id"])
    assert "pi_unseen" not in seen and "pi_unseen" not in {i.practice_item_id for i in record.items()}


def test_f1_repair_needs_a_recent_error_not_any_active_one():
    from types import SimpleNamespace

    from learnloop.daily_plan.lanes import REPAIR_MIN_RECENT_ERROR, classify_item
    from tests.daily_plan_fakes import scheduled

    attempted = SimpleNamespace(due_at=iso(NOW - timedelta(days=1)), last_attempt_at=iso(NOW - timedelta(days=9)))

    def lane(recent_error, state=attempted, **extra):
        item = scheduled("pi_x", "lo_x", recent_error=recent_error, **extra)
        return classify_item(
            item, rank=0, state=state, requested=False, now=NOW, est_minutes=3.0, check=None, probe_slot_available=False
        ).lane

    assert lane(0.9 * 2.718281828 ** (-80 / 7)) == "maintain"  # an 80-day-old error: due review
    assert lane(REPAIR_MIN_RECENT_ERROR * 0.99) == "maintain"
    assert lane(REPAIR_MIN_RECENT_ERROR) == "repair"
    assert lane(0.9) == "repair"
    assert lane(0.9, state=None) == "new"  # never attempted: new material
    assert lane(0.0, state=None, intervention_followup=1.0) == "repair"  # follow-ups stay repair


# -- F2: a session left open yesterday is activity, not a break --


def _single_due(tmp_path):
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_a": [("pi_a", 1.0)]})
    _no_goals(paths)
    env = make_env(paths.root, [scheduled("pi_a", "lo_a", forgetting_risk=0.5)], clock=MovableClock(NOW))
    seed_due(env.repository, "pi_a", due=NOW - timedelta(days=1), last=NOW - timedelta(days=1))
    _ended_session(env.repository, "s_old", NOW - timedelta(days=12))  # the last ENDED session
    return env


def _open_session(repository: Repository, session_id: str, started) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, available_minutes) VALUES (?, ?, NULL, 25)",
            (session_id, iso(started)),
        )
        connection.commit()


def test_f2_practice_in_a_session_left_open_yesterday_is_not_a_break(tmp_path):
    env = _single_due(tmp_path)
    # Yesterday the learner began (a re-entry) and practised; Done and closing
    # the app ended no session.
    _open_session(env.repository, "s_yday", NOW - timedelta(days=1, hours=1))
    record_attempt(env.repository, "pi_a", "lo_a", NOW - timedelta(days=1), session_id="s_yday")
    record = get_or_create_today(env)  # Start reads the plan before Begin ends stale sessions
    assert record.kind == "normal"
    assert record.split["reentry_gap"]["gap_days"] == 1
    assert record.split["reentry_gap"]["last_activity_at"] == iso(NOW - timedelta(days=1))


def test_f2_a_stale_session_without_attempts_counts_from_its_start(tmp_path):
    env = _single_due(tmp_path)
    _open_session(env.repository, "s_yday", NOW - timedelta(days=2))
    record = get_or_create_today(env)
    assert record.kind == "normal" and record.split["reentry_gap"]["gap_days"] == 2


def test_f2_the_break_still_shows_when_the_only_open_session_began_today(tmp_path):
    env = _single_due(tmp_path)
    # Today's own session (begun before the plan was first read) is not
    # activity that ends the break: the re-entry stands.
    _open_session(env.repository, "s_today", NOW - timedelta(minutes=5))
    record_attempt(env.repository, "pi_a", "lo_a", NOW - timedelta(minutes=2), session_id="s_today")
    record = get_or_create_today(env)
    assert record.kind == "reentry" and record.split["reentry_gap"]["gap_days"] == 12


# -- F3: the view's projection never runs the live chooser --


def test_f3_plan_reads_never_call_the_live_chooser(tmp_path):
    from dataclasses import dataclass, field

    from learnloop.daily_plan.chooser import LaneQuotaChooser
    from learnloop.daily_plan.engine import PlanPolicy, advance_with_context, legacy_source
    from learnloop.daily_plan.view import plan_view
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    @dataclass
    class GuardedChooser:
        """A router-like chooser: every call is a (paid, logged) decision."""

        name: str = "fake_router"
        armed: bool = False
        calls: list = field(default_factory=list)

        def choose(self, state, feasible):
            self.calls.append(len(feasible))
            if self.armed:
                raise AssertionError("a plan read called the live chooser")
            choice = LaneQuotaChooser().choose(state, feasible)
            from dataclasses import replace

            return replace(choice, chosen_by="mixture", propensity=0.5)

    los = {f"lo_p{i}": [(f"pi_p{i}", 1.0)] for i in range(10)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    chooser = GuardedChooser()
    policy = PlanPolicy(source_name="fake_source", chooser=chooser, make_source=legacy_source)
    env = make_env(
        paths.root, [scheduled(f"pi_p{i}", f"lo_p{i}", forgetting_risk=0.7) for i in range(10)],
        clock=MovableClock(NOW), policy=policy,
    )
    for i in range(10):
        seed_due(env.repository, f"pi_p{i}", due=NOW - timedelta(days=1), last=NOW - timedelta(days=30))
    record, step, context = advance_with_context(env, serve=False)  # the first block: a real decision
    assert chooser.calls and record.blocks[0].chosen_by == "mixture"
    chooser.armed = True
    before = len(chooser.calls)
    view = plan_view(env, record, context=context, next_step=step)
    assert len(chooser.calls) == before
    assert view["plan"]["projected"]  # still projected, deterministically
    assert all(row["why"] for row in view["plan"]["projected"])
    # Same figures on every read.
    assert plan_view(env, record, context=context, next_step=step)["plan"]["projected"] == view["plan"]["projected"]


# -- F4: mid-plan follow-ups respect the item cap and their lane --


def _assert_lanes_within_allotments(record):
    allotment, spent = record.ledger()
    for lane in allotment:
        assert spent[lane] <= allotment[lane] + 1e-6, (lane, spent, allotment)
    assert record.minutes_planned() <= record.budget + 1e-6


def test_f4_followups_keep_a_reentry_plan_within_its_item_cap_and_lanes(tmp_path):
    from learnloop.daily_plan.engine import advance
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    los = {f"lo_r{i}": [(f"pi_r{i}", 1.0)] for i in range(14)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    state = {"followups": []}
    base = [scheduled(f"pi_r{i}", f"lo_r{i}", forgetting_risk=0.7) for i in range(8)]
    clock = MovableClock(NOW)
    env = make_env(paths.root, lambda: list(state["followups"]) + base, clock=clock)
    for i in range(14):
        seed_due(env.repository, f"pi_r{i}", due=NOW - timedelta(days=10), last=NOW - timedelta(days=30))
    _ended_session(env.repository, "s_old", NOW - timedelta(days=12))
    record = get_or_create_today(env)
    assert record.kind == "reentry" and record.split["items_cap"] == 8
    record, step = advance(env, serve=True)
    clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
    # The answer produces six follow-ups at once.
    state["followups"] = [
        scheduled(f"pi_r{i}", f"lo_r{i}", followup_kind="intervention_followup") for i in (8, 9, 10, 11, 12, 13)
    ]
    clock.advance(1)
    for _ in range(40):
        record, step = advance(env, serve=False)
        assert record.item_count() <= 8
        _assert_lanes_within_allotments(record)
        if step["kind"] != "item":
            break
        clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
        clock.advance(1)
    assert record.item_count() <= record.split["items_cap"]
    followups = [item for item in record.items() if item.origin == "followup"]
    assert followups and not any(item.displaced for item in followups)  # never displaced by a later follow-up
    # Displaced to make room: the plan's unserved tail, never a follow-up.
    displaced = [item for item in record.items() if item.displaced]
    assert displaced and all(item.origin == "chooser" for item in displaced)
    # Repair had no allotment of its own: the follow-ups' minutes are released
    # to it from maintain, and recorded.
    assert any(item.lane_release for item in followups)
    assert all(
        entry["from"] in record.lanes_allowed for item in followups if item.lane_release for entry in item.lane_release["released"]
    )


def test_f4_a_followup_that_cannot_fit_is_declined_not_appended(tmp_path):
    from learnloop.daily_plan.engine import advance, build_plan
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    los = {f"lo_{key}": [(f"pi_{key}", 1.5)] for key in "abcd"} | {"lo_f": [("pi_f", 9.5)]}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    state = {"followups": []}
    base = [scheduled(f"pi_{key}", f"lo_{key}", forgetting_risk=0.7) for key in "abcd"]
    clock = MovableClock(NOW)
    env = make_env(paths.root, lambda: list(state["followups"]) + base, clock=clock)
    for key in "abcdf":
        seed_due(env.repository, f"pi_{key}", due=NOW - timedelta(days=2), last=NOW - timedelta(days=9))
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    record, step = advance(env, serve=True)
    planned_before = [item.practice_item_id for item in record.items()]
    assert planned_before == ["pi_a", "pi_b", "pi_c"]  # 6 of 10 minutes, merged small maintain groups
    clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
    state["followups"] = [scheduled("pi_f", "lo_f", followup_kind="intervention_followup")]
    record, step = advance(env, serve=False)
    # A 10-minute follow-up cannot fit even with the whole unserved tail (4
    # minutes) displaced, so it is declined and nothing is displaced for it.
    assert "pi_f" not in {item.practice_item_id for item in record.items()}
    assert not any(item.displaced for item in record.items())
    assert record.minutes_planned() <= record.budget + 1e-6


# -- F5: plan builds publish no offer the learner never saw --


def _rpc(ctx, name, params):
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _offer_receipts(path):
    import sqlite3

    with sqlite3.connect(path) as connection:
        return connection.execute(
            "SELECT entry_surface, returned_candidate_ids_json FROM scheduler_offer_receipts ORDER BY rowid"
        ).fetchall()


def test_f5_plan_rpcs_finalize_no_offer_and_picks_keep_the_list_offer(tmp_path, monkeypatch):
    import json

    import learnloop.clock as clock_module
    from learnloop_sidecar.context import SidecarContext

    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]}
    )
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: NOW)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = _rpc(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    before = _offer_receipts(paths.sqlite_path)
    _rpc(ctx, "get_daily_plan", {"sessionId": session_id})
    served = _rpc(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    _rpc(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})
    assert _offer_receipts(paths.sqlite_path) == before  # nothing "offered" that no screen showed
    step = served["step"]
    # The served plan item still binds: its candidate is a returned one of the
    # plan build's slate in this session.
    assert Repository(paths.sqlite_path).bind_submission_offer(
        submission_id="sub_f5", session_id=session_id, practice_item_id=step["practiceItemId"],
        scheduler_candidate_id=step["schedulerCandidateId"],
    ) == step["schedulerCandidateId"]
    # The full list, when shown, is published as the desktop queue's offer...
    queue = _rpc(ctx, "get_today_queue", {"sessionId": session_id})
    receipts = _offer_receipts(paths.sqlite_path)
    assert len(receipts) == len(before) + 1 and receipts[-1][0] == "desktop_queue"
    listed = {
        item["practiceItemId"]: item["schedulerCandidateId"]
        for section in queue["sections"]
        for item in section["items"]
    }
    planned_ids = {item["practiceItemId"] for block in served["plan"]["blocks"] for item in block["items"]}
    pick_id = next(item_id for item_id in listed if item_id not in planned_ids)
    # ...and a pick from it is served with that offer, not the plan build's.
    picked = _rpc(
        ctx, "plan_learner_pick",
        {"practiceItemId": pick_id, "sessionId": session_id, "schedulerCandidateId": listed[pick_id]},
    )
    assert picked["step"]["schedulerCandidateId"] == listed[pick_id]
    assert listed[pick_id] in json.loads(receipts[-1][1])
    assert _offer_receipts(paths.sqlite_path) == receipts


# -- F6: every stop decision is an append-only receipt --


def _small_plan_env(tmp_path, *, policy=None, count=3, minutes=3.0):
    from learnloop.daily_plan.engine import DEFAULT_POLICY
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    los = {f"lo_s{i}": [(f"pi_s{i}", minutes)] for i in range(count)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    clock = MovableClock(NOW)
    env = make_env(
        paths.root, [scheduled(f"pi_s{i}", f"lo_s{i}", forgetting_risk=0.7) for i in range(count)],
        clock=clock, policy=policy or DEFAULT_POLICY,
    )
    for i in range(count):
        seed_due(env.repository, f"pi_s{i}", due=NOW - timedelta(days=2), last=NOW - timedelta(days=9))
    return env, clock


def _drain(env, clock):
    from learnloop.daily_plan.engine import advance

    for _ in range(30):
        record, step = advance(env, serve=False)
        if step["kind"] != "item":
            return record
        clock.advance(1)
        advance(env, serve=False, skip_practice_item_id=step["practice_item_id"])
    raise AssertionError("the plan never finished")


def test_f6_a_reopened_plan_that_stops_again_keeps_both_stop_receipts(tmp_path):
    from learnloop.daily_plan.engine import build_plan, set_minutes
    from learnloop.daily_plan.types import STOP_FOR_TODAY

    env, clock = _small_plan_env(tmp_path)
    build_plan(env, kind="normal", budget=5.0, remembered=5, minutes_source="chip")
    record = _drain(env, clock)
    assert record.status == "complete" and len(record.stops()) == 1
    clock.advance(5)
    set_minutes(env, 15)  # a larger chip reopens the completed plan
    record = _drain(env, clock)
    assert record.status == "complete"
    stops = record.stops()
    assert len(stops) == 2 and stops[0].created_at < stops[1].created_at
    for stop in stops:
        assert stop.chosen["candidate_id"] == STOP_FOR_TODAY
        assert stop.chosen["chooser"] == "lane_quota_v1" and stop.chosen["propensity"] == 1.0
        assert "candidate_set" in stop.chosen and "state" in stop.chosen
    # Stops are receipts, not blocks: no minutes, no items, no block numbers.
    assert all(block.action != STOP_FOR_TODAY for block in record.blocks)
    assert [block.ordinal for block in record.blocks] == list(range(1, len(record.blocks) + 1))


def test_f6_a_router_stop_keeps_its_propensity_and_candidates(tmp_path):
    from dataclasses import dataclass

    from learnloop.daily_plan.engine import PlanPolicy, build_plan, legacy_source
    from learnloop.daily_plan.types import STOP_FOR_TODAY, BlockChoice

    @dataclass
    class StoppingRouter:
        name: str = "fake_router"

        def choose(self, state, feasible):
            return BlockChoice(STOP_FOR_TODAY, "mixture", 0.3, "stop here", "model_written", "rd_1")

    env, _clock = _small_plan_env(tmp_path, policy=PlanPolicy("fake_source", StoppingRouter(), legacy_source))
    # Four minutes: STOP is offered while a 3.5-minute item is still feasible.
    record = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    assert record.status == "complete" and not record.blocks
    (stop,) = record.stops()
    assert stop.chosen_by == "mixture" and stop.decision_ref == "rd_1"
    assert stop.chosen["propensity"] == 0.3 and stop.chosen["fallback"] is False
    assert stop.chosen["feasible_ids"] and stop.chosen["candidate_set"]


# -- F10: a pick after the plan closed keeps its learner_pick record --


def test_f10_a_pick_after_the_plan_closed_is_recorded(tmp_path):
    from learnloop.daily_plan.engine import learner_pick, stop_today
    from learnloop.daily_plan.records import RECEIPT_OPEN_LIST_PICK

    env, _clock = _small_plan_env(tmp_path)
    get_or_create_today(env)
    record = stop_today(env)
    assert record.status == "stopped"
    record, step = learner_pick(env, "pi_s2")
    assert step["origin"] == "open_list" and step["plan_id"] is None
    assert record.minutes_planned() == 0 or "pi_s2" not in {item.practice_item_id for item in record.items()}
    (receipt,) = [r for r in record.receipts if r.action == RECEIPT_OPEN_LIST_PICK]
    assert receipt.chosen_by == "learner_pick" and receipt.chosen["propensity"] is None
    assert receipt.chosen["practice_item_id"] == "pi_s2"
    import sqlite3

    with sqlite3.connect(env.repository.sqlite_path) as connection:
        served = connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE block_id = ? AND kind = 'item_served'", (receipt.id,)
        ).fetchone()
    assert served is not None and '"serving_origin":"learner_pick"' in served[0]


# -- F7: a chooser's output is validated at the seam --


def test_f7_malformed_choices_fall_back_and_are_flagged(tmp_path):
    import pytest as _pytest  # noqa: F401
    from dataclasses import dataclass

    from learnloop.daily_plan.engine import PlanPolicy, build_plan, legacy_source
    from learnloop.daily_plan.types import BlockChoice

    @dataclass
    class Router:
        chosen_by: str
        propensity: object
        why_kind: str = "model_written"
        name: str = "fake_router"

        def choose(self, state, feasible):
            return BlockChoice(feasible[0].candidate_id, self.chosen_by, self.propensity, "pick", self.why_kind, "rd_x")

    cases = [
        (Router("learner_pick", None), "chosen_by_not_allowed"),
        (Router("mixture", None), "propensity_out_of_range"),
        (Router("mixture", 0.0), "propensity_out_of_range"),
        (Router("mixture", 1.5), "propensity_out_of_range"),
        (Router("staged", float("nan")), "propensity_out_of_range"),
        (Router("mixture", True), "propensity_out_of_range"),
        (Router("mixture", 0.4, why_kind="vibes"), "why_kind_unknown"),
    ]
    for index, (router, reason) in enumerate(cases):
        env, _clock = _small_plan_env(tmp_path / f"case{index}", policy=PlanPolicy("fake_source", router, legacy_source))
        record = build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
        block = record.blocks[0]
        assert block.chosen["fallback"] is True and block.chosen["fallback_reason"] == reason, (router, block.chosen)
        assert block.chosen_by == "lane_quota" and block.chosen["propensity"] == 1.0
        assert block.decision_ref is None
    # A well-formed sampled choice is kept as given.
    env, _clock = _small_plan_env(tmp_path / "ok", policy=PlanPolicy("fake_source", Router("mixture", 0.4), legacy_source))
    block = build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip").blocks[0]
    assert block.chosen["fallback"] is False and block.chosen_by == "mixture"
    assert block.chosen["propensity"] == 0.4 and block.decision_ref == "rd_x"


# -- F8: an out-of-range expected_minutes never rejects a generated item --


def test_f8_out_of_range_expected_minutes_reach_the_writer_bounded(tmp_path):
    import math

    import yaml

    from learnloop.content.proposals.ai_contracts import PracticeItemPatchPayload
    from learnloop.vault.models import PracticeItem
    from learnloop.vault.writer import upsert_practice_item

    bounds = {meta.__class__.__name__: meta for meta in PracticeItem.model_fields["expected_minutes"].metadata}
    assert bounds["Le"].le == 240.0 and bounds["Gt"].gt == 0.0  # the wire keeps to the model's bounds
    cases = [(0, None), (-2, None), (math.nan, None), (math.inf, None), ("soon", None), (True, None),
             (300, 240.0), (240, 240.0), (4.5, 4.5)]
    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_w": [(f"pi_w{index}", None) for index in range(len(cases))]}
    )
    vault = load_vault(paths.root)
    for index, (raw, kept) in enumerate(cases):
        item_id = f"pi_w{index}"
        wire = PracticeItemPatchPayload.model_validate({"prompt": "p", "expected_minutes": raw})
        assert wire.expected_minutes == kept, raw
        # The generated payload as the proposal stores it, written through the
        # vault writer (which validates PracticeItem): never rejected.
        payload = {**vault.practice_items[item_id].model_dump(mode="json", exclude_none=True),
                   **wire.model_dump(exclude_none=True, include={"expected_minutes"})}
        path = upsert_practice_item(paths.root, payload)
        written = yaml.safe_load(path.read_text())
        assert written.get("expected_minutes") == kept, (raw, written.get("expected_minutes"))


# -- F9: displayed numbers match what is served --


def _load_vault_env(tmp_path, *, plan_toml=None, requested=()):
    """Four reviews due daily (L = 14 min/day) and eight new LOs."""

    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    los = {f"lo_rev{i}": [(f"pi_rev{i}", None)] for i in range(4)}
    los |= {f"lo_n{i}": [(f"pi_n{i}", 3.0)] for i in range(8)}
    los |= {"lo_req": [("pi_req", 5.0)]}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, plan_toml=plan_toml)
    _no_goals(paths)
    items = [scheduled("pi_req", "lo_req")] + [scheduled(f"pi_n{i}", f"lo_n{i}", new_material=1.0) for i in range(8)]
    clock = MovableClock(NOW)
    env = make_env(paths.root, items, clock=clock, requested=requested)
    for i in range(4):
        # Interval one day, due tomorrow: 14 reviews in 14 days of 3.5 minutes.
        seed_due(env.repository, f"pi_rev{i}", due=NOW + timedelta(days=1), last=NOW)
    return env, clock


def test_f9_extensions_hold_the_review_load_to_the_days_budget(tmp_path):
    import pytest

    from learnloop.daily_plan.engine import build_plan, keep_going, stop_today

    env, _clock = _load_vault_env(tmp_path, plan_toml="[plan]\nmax_new_items_per_day = 30\n")
    day_plan = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert day_plan.admission["review_load_per_day"] == pytest.approx(14.0)
    assert day_plan.admission["ceiling_basis"] == "plan_minutes"
    assert day_plan.admission["ceiling_minutes"] == pytest.approx(32.0)
    stop_today(env)
    extension = keep_going(env)
    assert extension.kind == "keep_going" and extension.budget == 10.0
    # L (14 min/day) is a daily load: it is held to 0.80 of the day's 40, not
    # of the extension's 10 (which would admit nothing past the floor).
    assert extension.admission["ceiling_basis"] == "remembered_minutes"
    assert extension.admission["ceiling_minutes"] == pytest.approx(32.0)
    assert extension.admission["stopped_by"] != "load_ceiling"
    assert len(extension.admission["admitted"]) >= 2


def test_f9_more_new_preview_is_what_confirming_plans(tmp_path):
    from learnloop.daily_plan.engine import advance_with_context, get_or_create_today, more_new, stop_today
    from learnloop.daily_plan.view import plan_view

    env, _clock = _load_vault_env(tmp_path, requested=["pi_req"])
    get_or_create_today(env)
    stop_today(env)
    _record, preview = more_new(env, confirm=False)
    # The requested item (5.5 min) goes first in the extension's 10 minutes, so
    # only one 3.5-minute new item fits; a greedy fit that ignored it said two.
    assert preview["items"] == 1 and preview["est_minutes"] == 3.5
    plan, confirmed = more_new(env, confirm=True)
    assert confirmed == preview
    record, step, context = advance_with_context(env, serve=False)
    assert record.id == plan.id
    projected = plan_view(env, record, context=context, next_step=step)["plan"]["projected"]
    planned_new = [item.practice_item_id for item in record.items() if item.new_admitted]
    assert planned_new == preview["practice_item_ids"]
    assert sum(row["item_count"] for row in projected if row["lane"] == "new") == 0


def test_f9_reentry_panel_names_only_what_it_counts(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import learnloop.scheduling.reentry_summary as summary_module
    from learnloop.daily_plan.reentry import ReentryGap, reentry_panel
    from learnloop.scheduling.reentry_summary import SlippedFacet
    from tests.daily_plan_fakes import seed_due

    los = {"lo_a": [("pi_a", 1.0)], "lo_b": [("pi_b", 1.0)], "lo_c": [("pi_c", 1.0)]}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    last = NOW - timedelta(days=20)
    # lo_a and lo_b were solid at the last activity and have slipped since;
    # lo_c is still solid (a long stability).
    seed_due(repository, "pi_a", due=NOW, last=last - timedelta(days=1), stability=3.0)
    seed_due(repository, "pi_b", due=NOW, last=last - timedelta(days=1), stability=6.0)
    seed_due(repository, "pi_c", due=NOW + timedelta(days=300), last=last, stability=900.0)

    def facet(lo_id, weight):
        return SlippedFacet(lo_id, vault.learning_objects[lo_id].title, "recall", weight)

    # The goal's facets name lo_c (not slipped at the LO level) first.
    fake = SimpleNamespace(show=True, slipped_top=[facet("lo_c", 0.9), facet("lo_b", 0.5)])
    monkeypatch.setattr(summary_module, "reentry_summary", lambda *args, **kwargs: fake)
    gap = ReentryGap(True, 20, 7, iso(last))
    panel = reentry_panel(vault, repository, now=NOW, gap=gap, goal=SimpleNamespace(id="goal"))
    titles = {lo_id: vault.learning_objects[lo_id].title for lo_id in los}
    assert panel.slipped_count == 2
    # Blueprint order first among the counted LOs, then the rest by drop.
    assert panel.slipped_names == (titles["lo_b"], titles["lo_a"])
    assert panel.named_by == "goal_blueprint_weight"
    # Nothing slipped: nothing named, whatever the goal's facets say.
    seed_due(repository, "pi_a", due=NOW, last=NOW - timedelta(hours=1), stability=900.0)
    seed_due(repository, "pi_b", due=NOW, last=NOW - timedelta(hours=1), stability=900.0)
    panel = reentry_panel(vault, repository, now=NOW, gap=gap, goal=SimpleNamespace(id="goal"))
    assert panel.slipped_count == 0 and panel.slipped_names == ()


# -- F10: other gaps --


def test_f10_more_new_on_an_open_plan_is_refused_and_keeps_the_plan(tmp_path):
    import pytest

    from learnloop.daily_plan.engine import PlanStillOpenError, more_new

    env, _clock = _load_vault_env(tmp_path)
    record = get_or_create_today(env)
    assert record.is_open
    planned = [item.practice_item_id for item in record.items()]
    _record, preview = more_new(env, confirm=False)  # the preview is read-only
    with pytest.raises(PlanStillOpenError):
        more_new(env, confirm=True)
    after = get_or_create_today(env)
    assert after.id == record.id and after.is_open
    assert [item.practice_item_id for item in after.items()] == planned


def test_f10_keep_going_with_nothing_left_is_idempotent(tmp_path):
    from learnloop.daily_plan.engine import day_records, keep_going, stop_today
    from tests.daily_plan_fakes import make_env

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_a": [("pi_a", 1.0)]})
    _no_goals(paths)
    env = make_env(paths.root, [], clock=MovableClock(NOW))  # nothing eligible at all
    get_or_create_today(env)
    stop_today(env)
    first = keep_going(env)
    assert first.kind == "keep_going" and not first.is_open and not first.blocks
    for _ in range(3):
        again = keep_going(env)
        assert again.id == first.id
    assert [record.kind for record in day_records(env)] == ["normal", "keep_going"]


def test_f10_a_crash_before_the_first_block_keeps_requests_first(tmp_path, monkeypatch):
    import pytest

    from learnloop.daily_plan import engine
    from learnloop.daily_plan.engine import advance

    env, _clock = _load_vault_env(tmp_path, requested=["pi_req"])
    real_boundary = engine._boundary

    def crash(*args, **kwargs):
        raise RuntimeError("the app died between the two writes")

    monkeypatch.setattr(engine, "_boundary", crash)
    with pytest.raises(RuntimeError):
        get_or_create_today(env)
    monkeypatch.setattr(engine, "_boundary", real_boundary)
    record = get_or_create_today(env)
    assert record.is_open and not record.blocks and record.split["requested"]
    record, step = advance(env, serve=False)
    first = record.blocks[0]
    assert first.items[0].practice_item_id == "pi_req" and first.items[0].origin == "requested"
    assert step["practice_item_id"] == "pi_req"


# -- N1 (found re-measuring the fixture copies): estimates and the stored split agree --


def test_n1_an_item_whose_estimate_is_its_lanes_whole_load_is_planned(tmp_path):
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    # 9.26134 + 0.5 of feedback: an estimate with more decimals than the
    # stored split (4), equal to the maintain lane's whole load.
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_long": [("pi_long", 9.26134)]})
    _no_goals(paths)
    env = make_env(paths.root, [scheduled("pi_long", "lo_long", forgetting_risk=0.6)], clock=MovableClock(NOW))
    seed_due(env.repository, "pi_long", due=NOW - timedelta(days=3), last=NOW - timedelta(days=40))
    _ended_session(env.repository, "s_old", NOW - timedelta(days=30))
    record = get_or_create_today(env)
    assert record.kind == "reentry"
    assert [item.practice_item_id for item in record.items()] == ["pi_long"]
    allotment, spent = record.ledger()
    assert spent["maintain"] <= allotment["maintain"]


# -- Re-review F11: a requested or follow-up item is planned once, and the plan ends --


def _due_request_env(tmp_path, *, count=4, requested=("pi_q0",)):
    """``count`` attempted, due items (maintain lane); ``requested`` are asked for."""

    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    los = {f"lo_q{i}": [(f"pi_q{i}", 1.0)] for i in range(count)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    clock = MovableClock(NOW)
    state = {"items": [scheduled(f"pi_q{i}", f"lo_q{i}", forgetting_risk=0.6) for i in range(count)]}
    env = make_env(paths.root, lambda: list(state["items"]), clock=clock, requested=list(requested))
    for i in range(count):
        seed_due(env.repository, f"pi_q{i}", due=NOW - timedelta(days=1), last=NOW - timedelta(days=3))
    return env, clock, state


def _planned_once(record) -> None:
    for block in record.blocks:
        ids = [item.practice_item_id for item in block.items]
        assert len(ids) == len(set(ids)), (block.ordinal, ids)
    ids = [item.practice_item_id for item in record.items() if not item.displaced]
    assert len(ids) == len(set(ids)), ids


def _answer_through(env, clock, *, limit=30):
    from learnloop.daily_plan.engine import advance

    served = []
    for _ in range(limit):
        record, step = advance(env, serve=True)
        _planned_once(record)
        if step["kind"] != "item":
            return record, served
        served.append(step["practice_item_id"])
        clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
        clock.advance(1)
    raise AssertionError(f"the plan never finished: served {served}")


def test_f11_a_requested_due_item_is_planned_once_and_served_to_the_end(tmp_path):
    from learnloop.daily_plan.engine import build_plan

    env, clock, _state = _due_request_env(tmp_path)
    record = build_plan(env, kind="normal", budget=30.0, remembered=30, minutes_source="chip")
    first = record.blocks[0]
    assert first.items[0].practice_item_id == "pi_q0" and first.items[0].origin == "requested"
    assert first.items[0].lane == "maintain"
    _planned_once(record)
    record, served = _answer_through(env, clock)
    assert len(served) == len(set(served)) and served[0] == "pi_q0"
    assert record.status == "complete"
    assert all(item.done for item in record.items() if not item.displaced)


def test_f11_the_crash_recovery_boundary_plans_a_request_once(tmp_path, monkeypatch):
    import pytest

    from learnloop.daily_plan import engine

    env, clock, _state = _due_request_env(tmp_path)
    real_boundary = engine._boundary

    def crash(*args, **kwargs):
        raise RuntimeError("the app died between the two writes")

    monkeypatch.setattr(engine, "_boundary", crash)
    with pytest.raises(RuntimeError):
        get_or_create_today(env)
    monkeypatch.setattr(engine, "_boundary", real_boundary)
    record, served = _answer_through(env, clock)
    assert served[0] == "pi_q0" and len(served) == len(set(served))
    assert record.status == "complete"


def test_f11_a_followup_already_in_the_universe_is_forced_once(tmp_path):
    from learnloop.daily_plan.engine import advance, build_plan
    from tests.daily_plan_fakes import make_env, scheduled, seed_due

    # Eight recent errors: twelve repair minutes, more than one block packs.
    los = {f"lo_r{i}": [(f"pi_r{i}", 1.0)] for i in range(8)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    clock = MovableClock(NOW)
    state = {"items": [scheduled(f"pi_r{i}", f"lo_r{i}", recent_error=0.6) for i in range(8)]}
    env = make_env(paths.root, lambda: list(state["items"]), clock=clock)
    for i in range(8):
        seed_due(env.repository, f"pi_r{i}", due=NOW - timedelta(days=1), last=NOW - timedelta(days=3))
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    first = record.blocks[0]
    first_ids = {item.practice_item_id for item in first.items}
    target = next(item_id for item_id in record.split["universe"] if item_id not in first_ids)
    # Answer the whole first block; an answer turns ``target`` (still in the
    # universe, not planned) into a follow-up, forced into the next block,
    # whose repair lane still has minutes for the chooser.
    for _ in range(len(first.items)):
        record, step = advance(env, serve=True)
        clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
        clock.advance(1)
    state["items"] = [
        scheduled(item.practice_item_id, item.learning_object_id, followup_kind="intervention_followup", recent_error=0.6)
        if item.practice_item_id == target
        else item
        for item in state["items"]
    ]
    record, _step = advance(env, serve=False)
    _planned_once(record)
    second = record.blocks[1]
    assert second.items[0].practice_item_id == target and second.items[0].origin == "followup"
    assert len(second.items) > 1  # the chooser still packed the rest of the lane
    record, served = _answer_through(env, clock)
    assert len(served) == len(set(served)) and target in served
    assert record.status == "complete"


def test_f11_simulated_blocks_plan_a_forced_request_once(tmp_path):
    from learnloop.daily_plan.engine import _context, _prepare_plan, simulate_blocks

    env, _clock, _state = _due_request_env(tmp_path)
    prepared = _prepare_plan(env, kind="normal", budget=30.0, remembered=30, minutes_source="chip")
    assert [item.practice_item_id for item in prepared.requests] == ["pi_q0"]
    draft = prepared.record()
    context = _context(env, draft, prepared.built, day=prepared.day)
    simulated = simulate_blocks(draft, context, env.policy, forced=prepared.requests)
    ids = [item.practice_item_id for _decision, block in simulated for item in block.items]
    assert ids[0] == "pi_q0" and len(ids) == len(set(ids)), ids


# -- Re-review F12: a pick after the plan closed is not feedback time --


def test_f12_a_pick_after_the_plan_closed_adds_no_feedback_dwell(tmp_path):
    from learnloop.daily_plan.engine import learner_pick
    from learnloop.daily_plan.estimates import load_duration_evidence

    env, clock, _state = _due_request_env(tmp_path, count=3, requested=())
    record = get_or_create_today(env)
    record, served = _answer_through(env, clock)
    assert record.status == "complete" and len(served) == 3
    before = load_duration_evidence(env.repository, latency_cap_minutes=10.0).feedback_dwell
    assert before and all(minutes == 1.0 for minutes in before)  # one minute between answer and next item
    # Three minutes on the done screen, then a pick from the full list: served
    # as an open-list pick receipt, not as the plan's next item.
    clock.advance(3)
    _record, step = learner_pick(env, "pi_q0")
    assert step["origin"] == "open_list"
    after = load_duration_evidence(env.repository, latency_cap_minutes=10.0).feedback_dwell
    assert after == before


# -- Re-review F13: a pick keeps only a live, shown offer --


def test_f13_a_pick_ignores_a_used_or_unshown_offer(tmp_path, monkeypatch):
    import sqlite3
    from types import SimpleNamespace

    import learnloop.clock as clock_module
    from learnloop.daily_plan.engine import _offered_candidate
    from learnloop_sidecar.context import SidecarContext

    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]}
    )
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: NOW)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = _rpc(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _rpc(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    queue = _rpc(ctx, "get_today_queue", {"sessionId": session_id})
    listed = {
        item["practiceItemId"]: item["schedulerCandidateId"]
        for section in queue["sections"]
        for item in section["items"]
    }
    planned_ids = {item["practiceItemId"] for block in served["plan"]["blocks"] for item in block["items"]}
    pick_id = next(item_id for item_id in listed if item_id not in planned_ids)
    offer = listed[pick_id]
    picked = _rpc(ctx, "plan_learner_pick", {"practiceItemId": pick_id, "sessionId": session_id, "schedulerCandidateId": offer})
    assert picked["step"]["schedulerCandidateId"] == offer
    # The learner answers under that offer: it is used up.
    _rpc(
        ctx, "submit_dont_know",
        {"sessionId": session_id, "practiceItemId": pick_id, "schedulerCandidateId": offer, "submissionId": "sub_f13_first"},
    )
    with sqlite3.connect(paths.sqlite_path) as connection:
        (used_by,) = connection.execute(
            "SELECT chosen_attempt_id FROM scheduler_slate_candidates WHERE id = ?", (offer,)
        ).fetchone()
    assert used_by is not None
    # A pick from the stale list (the same, used offer) is served with a live
    # candidate, and the answer under it binds.
    again = _rpc(ctx, "plan_learner_pick", {"practiceItemId": pick_id, "sessionId": session_id, "schedulerCandidateId": offer})
    candidate = again["step"]["schedulerCandidateId"]
    assert candidate != offer
    repository = Repository(paths.sqlite_path)
    assert repository.bind_submission_offer(
        submission_id="sub_f13_again", session_id=session_id, practice_item_id=pick_id, scheduler_candidate_id=candidate,
    ) == candidate
    # A plan build's own candidate was never shown as the list: it is not "the
    # full list's offer", whatever its returned flag says.
    step = served["step"]
    env = SimpleNamespace(repository=repository, session_id=session_id)
    assert step["schedulerCandidateId"] is not None
    assert _offered_candidate(env, step["schedulerCandidateId"], step["practiceItemId"]) is None
    assert _offered_candidate(env, offer, pick_id) is None  # used up
    fresh = _rpc(ctx, "get_today_queue", {"sessionId": session_id})
    shown = next(item for section in fresh["sections"] for item in section["items"])
    assert _offered_candidate(env, shown["schedulerCandidateId"], shown["practiceItemId"]) == shown["schedulerCandidateId"]

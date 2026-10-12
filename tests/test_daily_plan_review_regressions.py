"""Daily-loop DL1: regressions for the Codex review findings (F1-F10).

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
from tests.daily_plan_fakes import NOW, MovableClock, iso, record_attempt
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


# -- F1: never-attempted items are new material, and repair has a recency bound --


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


def test_f1_a_recent_error_repairs_the_failed_item_and_the_unseen_one_is_new(tmp_path):
    env = _failed_and_unseen(tmp_path, error_days_ago=1)
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

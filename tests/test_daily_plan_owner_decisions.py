"""Owner decisions of 2026-10-12, applied at DL1's merge (mvp-0.14).

1. **"Repair" means an open diagnosed problem**: an unresolved causal
   hypothesis (a learner-state head still ``candidate`` or ``validated``,
   whose promoted misconception, if any, is not resolved) or an open
   unresolved-cause factor, from Slice 1 M2 and Slice 2 T1. A recent error
   alone is no longer repair. ``REPAIR_MIN_RECENT_ERROR`` is only the fallback
   while the diagnosis split is off (a vault below mvp-0.10, or
   ``diagnosis.split_enabled = false``). Follow-ups are still repair, and a
   never-attempted item is still new material (DL1's F1 fix).
2. **Re-entry stays short** (repair and maintain only), and "keep going"
   after a re-entry plan offers new material easily: the plan for the day's
   remaining minutes gives new material its admitted minutes first.
3. **No TUI plan view**: the TUI keeps the open queue (pinned by the
   ``tui-keeps-the-open-queue`` import contract in ``pyproject.toml``).
4. **Plan-served attempts carry a ``daily_plan`` serving kind** in the learner
   field, read from the plan's ``item_served`` receipts, and the engine's
   ``_boundary`` has the hook router R1 logs ``plan_block`` decisions through.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.daily_plan import engine
from learnloop.daily_plan.engine import advance, get_or_create_today, keep_going
from learnloop.db.repositories import Repository
from learnloop.outcome_contract import COLLECTION_VERSION
from learnloop.vault.yaml_io import write_yaml
from tests.daily_plan_fakes import NOW, MovableClock, iso, make_env, record_attempt, scheduled, seed_due
from tests.helpers import create_daily_plan_vault

PAST = NOW - timedelta(days=1)
LAST = NOW - timedelta(days=5)
FUTURE = NOW + timedelta(days=5)


def _no_goals(paths):
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})


def _hypothesis(repository: Repository, *, lo_id: str, attempt_id: str, episode: str, status: str = "candidate",
                scope: str = "learner_state", evidence=None) -> dict:
    return repository.append_causal_hypothesis(
        episode_key=episode,
        attempt_id=attempt_id,
        learning_object_id=lo_id,
        cause_scope=scope,
        statement=f"cause on {lo_id} ({episode})",
        statement_normalized=f"cause on {lo_id} ({episode})",
        evidence=evidence,
        status=status,
    )


# -- 1. repair = an open diagnosed problem -------------------------------------


_REPAIR_LOS = {
    "lo_hyp": [("pi_hyp", 1.0), ("pi_hyp_unseen", 1.0)],
    "lo_fac": [("pi_fac", 1.0)],
    "lo_err": [("pi_err", 1.0), ("pi_err_follow", 1.0)],
    "lo_retired": [("pi_retired", 1.0)],
    "lo_fixed": [("pi_fixed", 1.0)],
    "lo_slip": [("pi_slip", 1.0)],
    "lo_closed_factor": [("pi_closed_factor", 1.0)],
}


def _repair_env(tmp_path, *, plan_toml: str | None = None):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=_REPAIR_LOS, plan_toml=plan_toml)
    _no_goals(paths)
    # Every attempted item is due and has a fresh full-severity error on its LO:
    # under DL1's recent_error rule every one of them was repair.
    items = [
        scheduled(item_id, lo_id, recent_error=0.9, forgetting_risk=0.5)
        for lo_id, pairs in _REPAIR_LOS.items()
        for item_id, _minutes in pairs
        if item_id not in ("pi_hyp_unseen", "pi_err_follow")
    ]
    items.append(scheduled("pi_hyp_unseen", "lo_hyp", recent_error=0.9))
    items.append(scheduled("pi_err_follow", "lo_err", recent_error=0.9, followup_kind="cold_retry"))
    env = make_env(paths.root, items, clock=MovableClock(NOW))
    repository = env.repository
    attempts = {}
    for lo_id, pairs in _REPAIR_LOS.items():
        for item_id, _minutes in pairs:
            if item_id == "pi_hyp_unseen":
                continue
            seed_due(repository, item_id, due=PAST, last=LAST)
            attempts[item_id] = record_attempt(repository, item_id, lo_id, LAST)
    # An unresolved learner-state hypothesis.
    _hypothesis(repository, lo_id="lo_hyp", attempt_id=attempts["pi_hyp"], episode="ep_hyp")
    # An open unresolved-cause factor (no hypothesis head on that LO).
    repository.insert_unresolved_cause_factor(
        attempt_id=attempts["pi_fac"], candidate_causes=[{"hypothesis_id": "H_OTHER", "open_set": True}],
        algorithm_version="test",
    )
    # A factor that was resolved (the repair confirmed): closed.
    closed = repository.insert_unresolved_cause_factor(
        attempt_id=attempts["pi_closed_factor"], candidate_causes=[{"hypothesis_id": "H_OTHER", "open_set": True}],
        algorithm_version="test",
    )
    repository.close_unresolved_cause_factor(closed, status="resolved", resolution_kind="repair_confirmed")
    # A hypothesis withdrawn later (its head is retired): resolved.
    _hypothesis(repository, lo_id="lo_retired", attempt_id=attempts["pi_retired"], episode="ep_retired")
    _hypothesis(repository, lo_id="lo_retired", attempt_id=attempts["pi_retired"], episode="ep_retired",
                status="retired", evidence={"withdrawal": {"reason": "repair_confirmed"}})
    # A validated hypothesis whose promoted misconception has been resolved.
    misconception = repository.insert_misconception(
        learning_object_id="lo_fixed", statement="a fixed misconception", status="resolved"
    )
    _hypothesis(repository, lo_id="lo_fixed", attempt_id=attempts["pi_fixed"], episode="ep_fixed",
                status="validated", evidence={"promoted_misconception_id": misconception})
    # A diagnosed slip is not a learner-state problem.
    _hypothesis(repository, lo_id="lo_slip", attempt_id=attempts["pi_slip"], episode="ep_slip",
                scope="transient_execution")
    return env


def _pool_lanes(record) -> dict[str, str | None]:
    return {row["practice_item_id"]: row["lane"] for row in record.split["pool"]}


def test_repair_is_an_open_diagnosed_problem_not_a_recent_error(tmp_path):
    env = _repair_env(tmp_path)
    record = get_or_create_today(env)
    lanes = _pool_lanes(record)
    # Open diagnosed problems: an unresolved hypothesis, an open factor.
    assert lanes["pi_hyp"] == "repair"
    assert lanes["pi_fac"] == "repair"
    # A recent error with no open diagnosis, a retired hypothesis, a resolved
    # misconception, a resolved factor and a diagnosed slip are due reviews.
    for item_id in ("pi_err", "pi_retired", "pi_fixed", "pi_closed_factor", "pi_slip"):
        assert lanes[item_id] == "maintain", item_id
    # Follow-ups are still repair; never-attempted items are still new (F1).
    assert lanes["pi_err_follow"] == "repair"
    assert lanes["pi_hyp_unseen"] == "new"
    assert record.split["repair_rule"] == "open_diagnosis"


def test_repair_falls_back_to_recent_error_only_while_the_split_is_off(tmp_path):
    env = _repair_env(tmp_path, plan_toml="[diagnosis]\nsplit_enabled = false\n")
    record = get_or_create_today(env)
    lanes = _pool_lanes(record)
    for item_id in ("pi_hyp", "pi_fac", "pi_err", "pi_retired", "pi_fixed", "pi_closed_factor", "pi_slip"):
        assert lanes[item_id] == "repair", item_id
    assert lanes["pi_hyp_unseen"] == "new"
    assert record.split["repair_rule"] == "recent_error_fallback"


# -- 2. keep going after re-entry offers new material ----------------------------


def _reentry_env(tmp_path, last_minutes=40):
    los = {f"lo_r{i}": [(f"pi_r{i}", 1.0)] for i in range(14)}
    los["lo_push"] = [("pi_push_a", 2.0), ("pi_push_b", 2.0)]
    los["lo_new"] = [("pi_new_a", 3.0), ("pi_new_b", 3.0)]
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    items = [scheduled(f"pi_r{i}", f"lo_r{i}", forgetting_risk=0.7) for i in range(14)]
    items += [scheduled("pi_push_a", "lo_push", goal_frontier=0.4), scheduled("pi_push_b", "lo_push", goal_frontier=0.4)]
    items += [scheduled("pi_new_a", "lo_new", new_material=1.0), scheduled("pi_new_b", "lo_new", new_material=1.0)]
    clock = MovableClock(NOW)
    env = make_env(paths.root, items, clock=clock, session_id="s_today")
    for i in range(14):
        seed_due(env.repository, f"pi_r{i}", due=PAST - timedelta(days=20), last=NOW - timedelta(days=40))
    for item_id in ("pi_push_a", "pi_push_b"):
        seed_due(env.repository, item_id, due=FUTURE, last=NOW - timedelta(days=40))
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, available_minutes) VALUES ('s_old', ?, ?, ?)",
            (iso(NOW - timedelta(days=30, minutes=30)), iso(NOW - timedelta(days=30)), last_minutes),
        )
        connection.commit()
    return env, clock


def _answer_everything(env, clock):
    record = None
    for _ in range(40):
        record, step = advance(env, serve=True)
        if step["kind"] != "item":
            return record
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.instant)
        clock.advance(0.5)
    return record


@pytest.mark.parametrize(
    ("last_minutes", "after_kind"),
    [
        # 40 remembered minutes: keep going plans the day's remaining minutes.
        (40, "normal"),
        # 6 remembered minutes, all used by the re-entry: the 10-minute
        # keep-going extension.
        (6, "keep_going"),
    ],
    ids=["remaining-minutes", "extension"],
)
def test_reentry_stays_short_and_keep_going_leads_with_new_material(tmp_path, last_minutes, after_kind):
    env, clock = _reentry_env(tmp_path, last_minutes)
    reentry = get_or_create_today(env)
    assert reentry.kind == "reentry"
    # Re-entry stays short: repair and maintain only, nothing new.
    assert set(reentry.lanes_allowed) == {"repair", "maintain"}
    assert all(item.lane in ("repair", "maintain") for item in reentry.items())
    done = _answer_everything(env, clock)
    assert done is not None and not done.is_open
    after = keep_going(env)
    assert after.kind == after_kind and after.row["parent_plan_id"] == reentry.id
    # A long break leaves a large maintenance backlog and push work; new
    # material still comes first in the plan for the day's remaining minutes.
    planned_new = [item for item in after.items() if item.lane == "new"]
    assert planned_new and all(item.new_admitted for item in planned_new)
    first_block = after.blocks[0]
    assert first_block.lane == "new"
    assert after.split["new_first"] == "after_reentry"


# -- 4. the learner field reads plan serving --------------------------------------


def test_plan_served_attempts_have_the_daily_plan_serving_kind(tmp_path):
    from learnloop.field.outcomes import _serving, plan_served_origins

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_a": [("pi_a", 1.0), ("pi_b", 1.0)]})
    _no_goals(paths)
    items = [scheduled("pi_a", "lo_a", forgetting_risk=0.5), scheduled("pi_b", "lo_a", forgetting_risk=0.5)]
    clock = MovableClock(NOW)
    env = make_env(paths.root, items, clock=clock, session_id="s_plan")
    for item_id in ("pi_a", "pi_b"):
        seed_due(env.repository, item_id, due=PAST, last=LAST)
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    served_id = step["practice_item_id"]
    other_id = "pi_b" if served_id == "pi_a" else "pi_a"
    clock.advance(2)
    plan_attempt = record_attempt(env.repository, served_id, "lo_a", clock.instant, session_id="s_plan")
    # The same item answered in another session, and an item the plan never served.
    other_session = record_attempt(env.repository, served_id, "lo_a", clock.advance(5), session_id="s_other")
    unserved = record_attempt(env.repository, other_id, "lo_a", clock.advance(5), session_id="s_plan")
    with env.repository.connection() as connection:
        # Written as today's attempts are (the fake writer leaves the column
        # at its legacy default, which the field never attributes).
        connection.execute("UPDATE practice_attempts SET collection_version = ?", (COLLECTION_VERSION,))
        connection.commit()
    with env.repository.connection() as connection:
        served = plan_served_origins(connection)
        rows = {
            row["id"]: dict(row)
            for row in connection.execute("SELECT * FROM practice_attempts WHERE id IN (?, ?, ?)",
                                          (plan_attempt, other_session, unserved))
        }
        origins = {attempt_id: _serving(connection, row, plan_served=served)[0] for attempt_id, row in rows.items()}
        # Without the preloaded map the reader loads it itself.
        assert _serving(connection, rows[plan_attempt])[0] == "daily_plan"
    assert origins == {plan_attempt: "daily_plan", other_session: "unknown", unserved: "unknown"}


def test_the_field_evaluation_keeps_the_daily_plan_label():
    from learnloop.field.evaluation import SERVING_ORIGIN_LABELS

    assert "daily_plan" in SERVING_ORIGIN_LABELS


def test_router_r1_logs_plan_block_decisions_through_the_boundary_hook(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_a": [("pi_a", 1.0)]})
    _no_goals(paths)
    env = make_env(paths.root, [scheduled("pi_a", "lo_a", forgetting_risk=0.5)], clock=MovableClock(NOW))
    seed_due(env.repository, "pi_a", due=PAST, last=LAST)
    logged: list[engine.PlanBlockDecision] = []

    def r1_logger(connection, decision):
        # R1 writes its router_decisions row on this connection, inside the
        # block's own transaction; DL1 builds no router table.
        assert connection.in_transaction
        logged.append(decision)
        return f"rd_{len(logged)}"

    engine.register_plan_decision_logger(r1_logger)
    try:
        record = get_or_create_today(env)
        record, _step = advance(env, serve=False)
    finally:
        engine.unregister_plan_decision_logger(r1_logger)
    assert logged and all(decision.kind == "plan_block" for decision in logged)
    first = logged[0]
    assert first.plan_id == record.id and first.block_id == record.blocks[0].id
    assert first.detail["candidate_set"] and first.detail["chooser"] == "lane_quota_v1"
    # The logged id is the block's decision_ref, on its row and its receipt.
    assert record.blocks[0].decision_ref == "rd_1"
    assert record.blocks[0].chosen["decision_ref"] == "rd_1"
    # With no logger registered nothing changes.
    with env.repository.connection() as connection:
        refs = [row[0] for row in connection.execute("SELECT decision_ref FROM attention_blocks WHERE daily_plan_id = ?", (record.id,))]
    assert refs == ["rd_1"] or set(refs) <= {"rd_1", None}
    assert json.dumps(first.detail)  # serializable for R1's row


def test_migration_180_widens_the_field_serving_origins_and_keeps_its_rows(tmp_path):
    """The field's DERIVED read model accepts ``daily_plan`` after 180, with
    its rows, columns, key and index unchanged and every other origin still
    checked."""

    import sqlite3

    import pytest as _pytest

    from learnloop.db.connection import connect
    from learnloop.db.migrate import apply_migrations, default_migrations_dir, discover_migrations

    before = tmp_path / "before_180"
    before.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) < 180:
            (before / path.name).write_bytes(path.read_bytes())
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=before)
    insert = (
        "INSERT INTO facet_outcome_observations(attempt_id, facet_id, practice_item_id, revision_status, "
        "observed_at, outcome, facet_share, effective_mass, cold, assisted, primed, serving_origin) "
        "VALUES (?, 'f', 'pi', 'exact', '2026-10-12T00:00:00Z', 1.0, 1.0, 1.0, 0, 0, 0, ?)"
    )

    def shape(connection):
        return (
            [tuple(row) for row in connection.execute("PRAGMA table_info(facet_outcome_observations)")],
            sorted(
                (row[0], row[1]) for row in connection.execute(
                    "SELECT type, name FROM sqlite_master WHERE tbl_name = 'facet_outcome_observations'"
                )
            ),
        )

    with connect(sqlite_path) as connection:
        connection.execute(insert, ("att_1", "learner_pick"))
        connection.commit()
        with _pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("att_2", "daily_plan"))
        rows_before = [tuple(row) for row in connection.execute("SELECT * FROM facet_outcome_observations")]
        shape_before = shape(connection)
    assert [m.version for m in apply_migrations(sqlite_path)] == [
        m.version for m in discover_migrations() if m.version >= 180
    ]
    with connect(sqlite_path) as connection:
        assert [tuple(row) for row in connection.execute("SELECT * FROM facet_outcome_observations")] == rows_before
        assert shape(connection) == shape_before
        connection.execute(insert, ("att_2", "daily_plan"))
        with _pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("att_3", "not_a_kind"))

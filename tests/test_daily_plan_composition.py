"""DL1 composed with main at its merge (mvp-0.14).

- **Diagnosis-decided placement** (Phase 6 owner decisions): a check miss whose
  diagnosis is pending leaves the assumption open and serves no second check.
  The plan's maintain lane takes assumed checks only from the scheduler, which
  subtracts ``awaiting_diagnosis_learning_object_ids`` from the due checks, and
  the headline reads placement at its own time (the wait is bounded), so the
  LO stays "assumed" until the diagnosis decides it.
- **The stuck prompt**: an empty "I'm stuck" answer on a plan-served item is an
  ordinary attempt; the plan marks the item done and moves on, and the learner
  field labels the attempt ``daily_plan`` from the plan's receipt.
- **T6's tutor**: a tutor reveal while a plan item is open primes the attempt
  but changes nothing in the plan's item flow.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import PlanEnv, advance, get_or_create_today
from learnloop.daily_plan.headline import classify_learning_objects, today_headline
from learnloop.db.repositories import Repository
from learnloop.placement.decisions import record_self_report
from learnloop.placement.state import load_placement_state
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.daily_plan_fakes import MovableClock, make_env, record_attempt, scheduled, seed_due
from tests.diagnosis_split_helpers import at
from tests.helpers import create_daily_plan_vault
from tests.split_live_helpers import drain_jobs, split_vault, submit
from tests.test_placement_diagnosis_decides import WRONG, _Diagnosed

LO = "lo_svd_compute"
DUE_HOURS = 14 * 24


def _plan_env(vault, repository, hours: float) -> PlanEnv:
    clock = FrozenClock(at(hours))
    return PlanEnv(
        vault=vault,
        repository=repository,
        clock=clock,
        eligible=lambda minutes: build_due_queue(
            vault, repository, clock=clock,
            session=SchedulerSession(available_minutes=int(round(minutes))), limit=None,
        ),
    )


def test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.14", seed=False)
    record_self_report(vault, repository, learning_object_ids=[LO], report="know_this", clock=FrozenClock(at(0)))
    # The check is due: it is the plan's maintain lane (a scheduled check).
    due = _plan_env(vault, repository, DUE_HOURS + 0.5)
    checks = [
        row for row in get_or_create_today(due).split["pool"]
        if row["learning_object_id"] == LO and row["check_kind"] == "assumed_check"
    ]
    assert checks and {row["lane"] for row in checks} == {"maintain"}
    assert classify_learning_objects(vault, repository, now=due.now())[LO] == "assumed"

    # The check is missed; its diagnosis is pending (not drained yet).
    client = _Diagnosed(causal_class="transient_execution")
    miss = submit(vault, repository, client, item_id="pi_svd_compute_001", answer=WRONG, when=at(DUE_HOURS + 1))
    pending_at = at(DUE_HOURS + 1.5)
    state = load_placement_state(vault, repository, now_iso=pending_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert state.awaiting_diagnosis_learning_object_ids == {LO}
    # The scheduler serves no second check meanwhile, so neither does the plan.
    queue = build_due_queue(vault, repository, clock=FrozenClock(pending_at), persist_explanations=False)
    assert not [s for s in queue if s.learning_object_id == LO and s.components.get("assumed_check")]
    # The headline, read at its own time, keeps the LO assumed while it waits
    # (and its counts agree with its classes).
    headline = today_headline(vault, repository, now=pending_at)
    assert headline["learning_object_classes"][LO] == "assumed"
    assert headline["counts"]["assumed"] == sum(1 for value in headline["learning_object_classes"].values() if value == "assumed")

    # The diagnosis lands: a slip keeps the topic, now in maintenance.
    drain_jobs(vault, repository, client, clock=FrozenClock(at(DUE_HOURS + 2)))
    decided = load_placement_state(vault, repository, now_iso=at(DUE_HOURS + 2.5).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert decided.awaiting_diagnosis_learning_object_ids == frozenset()
    assert classify_learning_objects(vault, repository, now=at(DUE_HOURS + 2.5))[LO] != "assumed"
    assert miss.attempt_id


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_an_empty_stuck_answer_on_a_plan_item_is_done_and_labelled_daily_plan(tmp_path, monkeypatch):
    from learnloop.field.outcomes import _serving

    moment = {"now": datetime(2026, 10, 12, 9, 0, tzinfo=UTC)}
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: moment["now"])
    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]}
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "item"
    moment["now"] += timedelta(minutes=3)
    # The desktop's empty "I'm stuck" (submit_dont_know at the stuck prompt's
    # versions records the empty stuck answer).
    _call(
        ctx, "submit_dont_know",
        {
            "sessionId": session_id, "practiceItemId": step["practiceItemId"], "latencySeconds": 150,
            "submissionId": "sub_stuck", "schedulerCandidateId": step["schedulerCandidateId"],
        },
    )
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        attempt = dict(connection.execute(
            "SELECT * FROM practice_attempts WHERE practice_item_id = ? ORDER BY created_at DESC LIMIT 1",
            (step["practiceItemId"],),
        ).fetchone())
        assert bool(attempt["declared_stuck"]) is True
        # The learner field reads the plan's receipt: daily_plan, not unknown.
        assert _serving(connection, attempt)[0] == "daily_plan"
    # A rebuild writes the label into the field's DERIVED read model, whose
    # serving_origin CHECK accepts daily_plan (migration 180).
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault

    rebuild_all_derived_state(load_vault(paths.root), repository)
    with repository.connection() as connection:
        labels = {
            row[0] for row in connection.execute(
                "SELECT serving_origin FROM facet_outcome_observations WHERE attempt_id = ?", (attempt["id"],)
            )
        }
    assert labels == {"daily_plan"}
    moment["now"] += timedelta(minutes=1)
    peek = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})
    done = [item for block in peek["plan"]["blocks"] for item in block["items"] if item["state"] == "done"]
    assert [item["practiceItemId"] for item in done] == [step["practiceItemId"]]
    assert peek["step"]["kind"] in ("item", "done")
    if peek["step"]["kind"] == "item":
        assert peek["step"]["practiceItemId"] != step["practiceItemId"]


def test_a_tutor_reveal_during_a_plan_item_leaves_the_item_flow_alone(tmp_path):
    from learnloop.attempts.reveal_ledger import record_reveal

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_a": [("pi_a", 1.0), ("pi_b", 1.0)]})
    now = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    clock = MovableClock(now)
    env = make_env(
        paths.root,
        [scheduled("pi_a", "lo_a", forgetting_risk=0.5), scheduled("pi_b", "lo_a", forgetting_risk=0.5)],
        clock=clock, session_id="s_tutor",
    )
    for item_id in ("pi_a", "pi_b"):
        seed_due(env.repository, item_id, due=now - timedelta(days=1), last=now - timedelta(days=5))
    _record, step = advance(env, serve=True)
    served = step["practice_item_id"]
    # T6: the tutor answers a question about the open item, citing a source span.
    assert record_reveal(
        env.repository, practice_item_id=served, source_kind="source_review", amount=0.5,
        learning_object_id="lo_a", basis="tutor span", clock=FrozenClock(clock.advance(1)),
    )
    record_attempt(env.repository, served, "lo_a", clock.advance(2), session_id="s_tutor")
    record, nxt = advance(env, serve=False)
    assert [item.practice_item_id for item in record.items() if item.done_at] == [served]
    assert nxt["kind"] == "item" and nxt["practice_item_id"] != served

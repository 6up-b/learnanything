"""Fakes for daily-loop DL1 engine tests: a ranked list, a clock, answers.

The plan container reads the scheduler's ranked eligible list through
``PlanEnv.eligible``; tests hand it a fixed list of ``ScheduledItem`` rows with
the components the lanes classify on (§6.1), and seed item state so due dates
are what the test says. No model is ever called.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.daily_plan.engine import DEFAULT_POLICY, PlanEnv, PlanPolicy
from learnloop.db.repositories import Repository
from learnloop.scheduling.scheduler import ScheduledItem
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


@dataclass
class MovableClock:
    instant: datetime = NOW

    def now(self) -> datetime:
        return self.instant

    def advance(self, minutes: float) -> datetime:
        self.instant = self.instant + timedelta(minutes=minutes)
        return self.instant


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def scheduled(
    item_id: str,
    lo_id: str,
    *,
    priority: float = 0.5,
    followup_kind: str | None = None,
    **components: float,
) -> ScheduledItem:
    base = {"forgetting_risk": 0.0, "recent_error": 0.0, "probe_eig": 0.0, "goal_frontier": 0.0}
    base.update(components)
    if followup_kind is not None:
        base["intervention_followup"] = 1.0
    return ScheduledItem(
        practice_item_id=item_id,
        learning_object_id=lo_id,
        priority=priority,
        components=base,
        readiness_factor=None,
        selected_mode="short_answer",
        plain_english=[],
        followup_kind=followup_kind,
    )


def seed_due(repository: Repository, item_id: str, *, due: datetime | None, last: datetime | None, stability: float = 5.0) -> None:
    repository.upsert_practice_item_state(
        item_id,
        difficulty=5.0,
        stability=stability if last is not None else None,
        due_at=iso(due) if due is not None else None,
        last_attempt_at=iso(last) if last is not None else None,
        active=True,
    )


def seed_open_problem(repository: Repository, lo_id: str, *, attempt_id: str | None = None) -> dict[str, Any]:
    """An open diagnosed problem on ``lo_id``: an unresolved learner-state hypothesis.

    Owner decision 2026-10-12: the plan's repair lane is an open diagnosed
    problem (with the diagnosis split on), not a recent error. The hypothesis
    names an attempt id only as a reference (no attempt row is written, so
    estimates and reconciliation are untouched).
    """

    return repository.append_causal_hypothesis(
        episode_key=f"ep_open_{lo_id}",
        attempt_id=attempt_id or f"att_seed_{lo_id}",
        learning_object_id=lo_id,
        cause_scope="learner_state",
        statement=f"an open problem on {lo_id}",
        statement_normalized=f"an open problem on {lo_id}",
        status="candidate",
    )


def record_attempt(repository: Repository, item_id: str, lo_id: str, at: datetime, *, latency_seconds: int | None = 120, session_id: str | None = None) -> str:
    attempt_id = f"att_{item_id}_{int(at.timestamp())}"
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
            "attempt_type, latency_seconds, created_at, session_id) "
            "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, ?, ?)",
            (attempt_id, item_id, lo_id, latency_seconds, iso(at), session_id),
        )
        connection.commit()
    return attempt_id


def make_env(
    root: Any,
    items: Callable[[], Sequence[ScheduledItem]] | Sequence[ScheduledItem],
    *,
    clock: MovableClock | None = None,
    session_id: str | None = None,
    policy: PlanPolicy = DEFAULT_POLICY,
    requested: Iterable[str] = (),
) -> PlanEnv:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    requested_ids = list(requested)
    # The real signature (``Repository.requested_practice_item_ids``): DL2's intent passes the
    # commitments whose requests its control owns; the fake's requests belong to none of them.
    def requested_practice_item_ids(*, skip_commitment_ids: Sequence[str] = ()) -> list[str]:
        return list(requested_ids)

    repository.requested_practice_item_ids = requested_practice_item_ids  # type: ignore[method-assign]
    supplier = items if callable(items) else (lambda: list(items))
    return PlanEnv(
        vault=vault,
        repository=repository,
        clock=clock or MovableClock(),
        session_id=session_id,
        eligible=lambda minutes: list(supplier()),
        policy=policy,
    )

"""Time estimates (``spec_daily_loop_v1.md`` §6.4, Q12).

The learner's own durations, with an authored estimate as the starting guess::

    est_minutes(item) = answer_minutes(item) + feedback_minutes
    answer_minutes    = (sum own latencies + k * g) / (n_item + k)
    g                 = (n_mode * median_mode + k * prior) / (n_mode + k)
    prior             = item.expected_minutes if present, else 3.0
    k                 = 3 pseudo-observations

Own latencies are ``practice_attempts.latency_seconds`` winsorized at
``plan.latency_cap_minutes``; ``median_mode`` is the learner's median for the
item's ``practice_mode``. ``feedback_minutes`` is the learner's median feedback
dwell (a plan item's ``item_done`` to the next ``item_served``, capped at five
minutes), 0.5 until ten observations exist.

Estimates are planning labels ("about N min"). They never write evidence,
mastery, certification, coldness or FSRS state (L4).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from statistics import median
from typing import Any

from learnloop.clock import parse_utc

ESTIMATOR_VERSION = "duration_shrinkage_v1"
#: The plan works in the estimates it stores: every item and reading estimate
#: it plans with is quantized to the 4 decimals the split, the admission and
#: the item events persist, so an item whose estimate is its lane's whole load
#: still fits the stored allotment (review N1; a 9.76134-minute item missed a
#: 9.7613-minute lane by 4e-5 and the re-entry plan came out empty).
ESTIMATE_DECIMALS = 4
#: k: pseudo-observations behind each prior (§6.4).
PSEUDO_OBSERVATIONS = 3.0
#: The existing conservative constant (controller_snapshot, action_loss).
FALLBACK_PRIOR_MINUTES = 3.0
DEFAULT_FEEDBACK_MINUTES = 0.5
FEEDBACK_MIN_OBSERVATIONS = 10
FEEDBACK_CAP_MINUTES = 5.0


@dataclass(frozen=True)
class DurationEvidence:
    """What the estimator reads, loaded once per plan decision."""

    #: practice_item_id -> winsorized own latencies, in minutes.
    latencies_by_item: Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    #: practice_mode -> winsorized latencies, in minutes.
    latencies_by_mode: Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    #: observed feedback dwell, in minutes (already capped).
    feedback_dwell: tuple[float, ...] = ()


@dataclass(frozen=True)
class ItemEstimate:
    minutes: float
    answer_minutes: float
    feedback_minutes: float
    n_item: int
    n_mode: int
    prior_minutes: float
    prior_source: str  # expected_minutes | fallback

    def as_dict(self) -> dict[str, Any]:
        return {
            "minutes": round(self.minutes, 4),
            "answer_minutes": round(self.answer_minutes, 4),
            "feedback_minutes": round(self.feedback_minutes, 4),
            "n_item": self.n_item,
            "n_mode": self.n_mode,
            "prior_minutes": self.prior_minutes,
            "prior_source": self.prior_source,
        }


def winsorize_minutes(latency_seconds: float, cap_minutes: float) -> float:
    return min(max(float(latency_seconds), 0.0) / 60.0, float(cap_minutes))


def feedback_minutes(dwell: Sequence[float]) -> float:
    if len(dwell) < FEEDBACK_MIN_OBSERVATIONS:
        return DEFAULT_FEEDBACK_MINUTES
    return min(float(median(dwell)), FEEDBACK_CAP_MINUTES)


def mode_prior(
    mode_latencies: Sequence[float], prior_minutes: float, *, k: float = PSEUDO_OBSERVATIONS
) -> float:
    """g: the practice-mode median shrunk toward the item prior."""

    n_mode = len(mode_latencies)
    if n_mode == 0:
        return float(prior_minutes)
    return (n_mode * float(median(mode_latencies)) + k * float(prior_minutes)) / (n_mode + k)


def answer_minutes(
    own_latencies: Sequence[float], g: float, *, k: float = PSEUDO_OBSERVATIONS
) -> float:
    n_item = len(own_latencies)
    return (sum(own_latencies) + k * g) / (n_item + k)


@dataclass(frozen=True)
class Estimator:
    evidence: DurationEvidence
    read_words_per_minute: int = 120
    version: str = ESTIMATOR_VERSION

    def feedback_minutes(self) -> float:
        return feedback_minutes(self.evidence.feedback_dwell)

    def estimate(self, item_id: str, practice_mode: str | None, expected_minutes: float | None) -> ItemEstimate:
        if expected_minutes is not None and expected_minutes > 0:
            prior, prior_source = float(expected_minutes), "expected_minutes"
        else:
            prior, prior_source = FALLBACK_PRIOR_MINUTES, "fallback"
        mode_latencies = self.evidence.latencies_by_mode.get(practice_mode or "", ())
        g = mode_prior(mode_latencies, prior)
        own = self.evidence.latencies_by_item.get(item_id, ())
        answer = answer_minutes(own, g)
        feedback = self.feedback_minutes()
        return ItemEstimate(
            minutes=answer + feedback,
            answer_minutes=answer,
            feedback_minutes=feedback,
            n_item=len(own),
            n_mode=len(mode_latencies),
            prior_minutes=prior,
            prior_source=prior_source,
        )

    def item_minutes(self, vault: Any, item_id: str) -> float:
        """The item's planning estimate, as the plan stores it (4 decimals)."""

        item = vault.practice_items.get(item_id)
        minutes = self.estimate(
            item_id,
            getattr(item, "practice_mode", None),
            getattr(item, "expected_minutes", None),
        ).minutes
        return round(minutes, ESTIMATE_DECIMALS)

    def reading_minutes(self, words_left: int) -> float:
        """A reading block's estimate, as the plan stores it (4 decimals)."""

        return round(reading_minutes(words_left, self.read_words_per_minute), ESTIMATE_DECIMALS)


def reading_minutes(words_left: int, words_per_minute: int) -> float:
    """A reading block's estimate: the section's words left / reading pace (§6.4)."""

    return max(int(words_left), 0) / max(int(words_per_minute), 1)


def load_duration_evidence(
    repository: Any,
    *,
    latency_cap_minutes: float,
    attempt_rows: Any = None,
    event_visible: Any = None,
) -> DurationEvidence:
    """Read own latencies (by item and by mode) and plan feedback dwell.

    ``attempt_rows``: the ``practice_attempts`` rows to read latencies from
    instead of the whole table. Adaptive difficulty passes its material view's
    rows (A8; Codex verify F28), so a withheld answer's duration never moves an
    AD candidate's estimate; None reads the table, as the plan does.
    ``event_visible(kind, detail, block_id)``: which plan events the feedback dwell may
    pair (adaptive difficulty passes its material view's rule, Codex verify F28
    round 10); None pairs every event, as the plan does."""

    by_item: dict[str, list[float]] = defaultdict(list)
    by_mode: dict[str, list[float]] = defaultdict(list)
    dwell: list[float] = []
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT practice_item_id, practice_mode, latency_seconds FROM practice_attempts "
            "WHERE latency_seconds IS NOT NULL AND latency_seconds > 0"
        ) if attempt_rows is None else [
            row for row in attempt_rows
            if row.get("latency_seconds") is not None and float(row["latency_seconds"]) > 0
        ]
        for row in rows:
            minutes = winsorize_minutes(row["latency_seconds"], latency_cap_minutes)
            by_item[str(row["practice_item_id"])].append(minutes)
            by_mode[str(row["practice_mode"])].append(minutes)
        has_plans = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'daily_plans'"
        ).fetchone()
        if has_plans is not None:
            dwell = _feedback_dwell(connection, event_visible=event_visible)
    return DurationEvidence(
        latencies_by_item={key: tuple(values) for key, values in by_item.items()},
        latencies_by_mode={key: tuple(values) for key, values in by_mode.items()},
        feedback_dwell=tuple(dwell),
    )


def _feedback_dwell(connection: Any, *, event_visible: Any = None) -> list[float]:
    """item_done -> the next item_served in the same plan, capped at five minutes.

    Only the plan's numbered blocks count: a pick served after the plan closed
    is an open-list pick receipt (no ordinal), and the time before it is spent
    on the done screen, not on feedback (re-review F12).
    """

    import json

    rows = connection.execute(
        "SELECT b.daily_plan_id AS plan_id, e.block_id AS block_id, e.kind AS kind, e.detail_json AS detail, "
        "e.created_at AS created_at "
        "FROM attention_block_events e JOIN attention_blocks b ON b.id = e.block_id "
        "WHERE b.daily_plan_id IS NOT NULL AND b.plan_ordinal IS NOT NULL "
        "AND e.kind IN ('item_done', 'item_served') "
        "ORDER BY b.daily_plan_id, e.created_at, e.id"
    ).fetchall()
    dwell: list[float] = []
    pending_done: dict[str, Any] = {}
    for row in rows:
        plan_id = str(row["plan_id"])
        detail = json.loads(row["detail"]) if row["detail"] else {}
        if event_visible is not None and not event_visible(row["kind"], detail, str(row["block_id"])):
            # A withheld event is skipped as if it had never been written (A8's "protected ==
            # absent"): it neither starts, ends nor breaks a pair.
            continue
        if row["kind"] == "item_done":
            pending_done[plan_id] = parse_utc(detail.get("done_at") or row["created_at"])
            continue
        done_at = pending_done.pop(plan_id, None)
        served_at = parse_utc(row["created_at"])
        if done_at is None or served_at is None:
            continue
        minutes = (served_at - done_at).total_seconds() / 60.0
        if minutes >= 0:
            dwell.append(min(minutes, FEEDBACK_CAP_MINUTES))
    return dwell


__all__ = [
    "DEFAULT_FEEDBACK_MINUTES",
    "DurationEvidence",
    "ESTIMATE_DECIMALS",
    "ESTIMATOR_VERSION",
    "Estimator",
    "FALLBACK_PRIOR_MINUTES",
    "FEEDBACK_CAP_MINUTES",
    "FEEDBACK_MIN_OBSERVATIONS",
    "ItemEstimate",
    "PSEUDO_OBSERVATIONS",
    "answer_minutes",
    "feedback_minutes",
    "load_duration_evidence",
    "mode_prior",
    "reading_minutes",
    "winsorize_minutes",
]

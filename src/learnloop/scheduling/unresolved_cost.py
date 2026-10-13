"""EVSI calibration Part C: what leaving a misconception unresolved costs, measured.

Today's loss ``L(h, a) = minutes(a) + minutes(e)`` charges a wrong repair only
its own minutes and the delay of the right one. It ignores that the
misconception stays: the learner keeps making the same mistake until something
else catches it. This module estimates that cost ``U`` in minutes, so the
measured-loss regime (``evsi.measured_loss_enabled``, default off) can charge
it on every off-diagonal cell (:func:`action_loss.build_loss_table`).

* **Personal measurement.** Each recurrence class (a causal hypothesis
  statement, or a merged Slice 2 T1 recurrence group) of a persistent cause
  (``cause_scope`` ``learner_state`` or ``unknown``) is one misconception's
  history: the attempts after its first are repeated errors, and their logged
  minutes (``practice_attempts.latency_seconds``) are what it cost. A class
  first seen recently is right-censored (it may still recur); the count is
  reported, not hidden.
* **Population prior (Eedi).** The NeurIPS 2020 answers show that after a
  misconception-consistent error, a later item testing the same misconception
  repeats it at an excess rate of ``EEDI_EXCESS_REPEAT_RATE`` per encounter
  over learners who first answered correctly (``learnloop evsi simulate``;
  school-age, multiple choice, ordinary teaching in between). Times
  ``ENCOUNTERS_UNTIL_CAUGHT`` (heuristic: Eedi does not say how often a
  learner meets the misconception again) times the learner's own median
  attempt minutes gives the prior ``U_prior``.
* **Shrinkage.** ``U = (k * U_prior + n * mean_personal) / (k + n)`` with
  ``k = evsi.unresolved_cost_prior_pseudo_count`` recurrence classes: the
  prior dominates until the learner has about ``k`` classes of their own.

Every number carries its provenance (``measured`` / ``population_prior`` /
``heuristic``) into the loss cell, and from there into the EVSI receipts.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.scheduling import action_loss as AL

UNRESOLVED_COST_VERSION = "unresolved_cost_v1"

# Eedi NeurIPS 2020 (task 1/2, 370 misconception triples, fitted 2026-10-13 by
# `learnloop evsi simulate`): excess repeat-error rate per later encounter after
# a misconception-consistent error, median over triples. Population prior.
EEDI_EXCESS_REPEAT_RATE = 0.151  # decision parameter: population prior (Eedi), 95% CI 0.138-0.162
# How many more times a learner meets an unresolved misconception before it is
# caught another way. Not in Eedi and not yet measured here. Heuristic.
ENCOUNTERS_UNTIL_CAUGHT = 6.0  # decision parameter: heuristic
#: A class first seen this recently may still recur (right-censored).
CENSOR_DAYS = 14.0  # decision parameter: heuristic
# ``latency_seconds`` is wall-clock presentation-to-submit time, so one long
# break reads as a long attempt: the pooled median needs this many timed
# attempts before it replaces the heuristic, and one attempt counts at most
# this many minutes.
MIN_TIMED_ATTEMPTS = 20  # decision parameter: heuristic
LATENCY_CAP_MINUTES = 15.0  # decision parameter: heuristic

PERSISTENT_SCOPES = ("learner_state", "unknown")


@dataclass(frozen=True)
class UnresolvedCost:
    """The shrunk estimate and every input it came from."""

    minutes: float
    provenance: str  # 'measured' | 'population_prior'
    prior_minutes: float
    prior_weight: float
    personal_mean_minutes: float | None
    personal_classes: int
    censored_classes: int
    minutes_per_repeat: float
    minutes_per_repeat_source: str
    pseudo_count: float
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": UNRESOLVED_COST_VERSION,
            "minutes": round(self.minutes, 6),
            "provenance": self.provenance,
            "source": "shrunk_personal" if self.personal_classes else "eedi_population_prior",
            "prior_minutes": round(self.prior_minutes, 6),
            "prior_weight": round(self.prior_weight, 6),
            "personal_mean_minutes": (
                round(self.personal_mean_minutes, 6) if self.personal_mean_minutes is not None else None
            ),
            "personal_classes": self.personal_classes,
            "censored_classes": self.censored_classes,
            "minutes_per_repeat": round(self.minutes_per_repeat, 6),
            "minutes_per_repeat_source": self.minutes_per_repeat_source,
            "pseudo_count": self.pseudo_count,
            "parameters": [
                {"name": "unresolved_cost.EEDI_EXCESS_REPEAT_RATE", "value": EEDI_EXCESS_REPEAT_RATE,
                 "provenance": "population_prior", "source": "Eedi NeurIPS 2020 (school maths, multiple choice)"},
                {"name": "unresolved_cost.ENCOUNTERS_UNTIL_CAUGHT", "value": ENCOUNTERS_UNTIL_CAUGHT,
                 "provenance": "heuristic"},
                {"name": "minutes_per_repeat", "value": round(self.minutes_per_repeat, 6),
                 "provenance": "measured" if self.minutes_per_repeat_source == "pooled_attempt_latency" else "heuristic",
                 "source": self.minutes_per_repeat_source},
                {"name": "evsi.unresolved_cost_prior_pseudo_count", "value": self.pseudo_count,
                 "provenance": "heuristic"},
            ],
            **({"detail": dict(self.detail)} if self.detail else {}),
        }


def _parse_time(value: Any) -> float | None:
    moment = parse_utc(str(value)) if value else None
    return moment.timestamp() if moment is not None else None


def _personal_history(repository: Repository) -> tuple[list[float], int, dict[str, Any]]:
    """Repeated-error minutes per recurrence class (+ censored count, detail)."""

    with repository.connection() as connection:
        has_groups = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'hypothesis_recurrence_groups'"
        ).fetchone() is not None
        group_of: dict[str, str] = {}
        if has_groups:
            group_of = {
                str(row["episode_key"]): str(row["group_key"])
                for row in connection.execute("SELECT episode_key, group_key FROM hypothesis_recurrence_groups")
            }
        placeholders = ", ".join("?" for _ in PERSISTENT_SCOPES)
        rows = connection.execute(
            "SELECT h.episode_key, h.statement_normalized, h.attempt_id, a.created_at, a.latency_seconds "
            "FROM causal_hypotheses h JOIN practice_attempts a ON a.id = h.attempt_id "
            f"WHERE h.cause_scope IN ({placeholders}) AND h.version = 1",
            PERSISTENT_SCOPES,
        ).fetchall()
        newest = connection.execute("SELECT MAX(created_at) FROM practice_attempts").fetchone()[0]
    attempts_by_class: dict[str, dict[str, tuple[float | None, float | None]]] = {}
    for row in rows:
        key = group_of.get(str(row["episode_key"]), f"statement:{row['statement_normalized']}")
        latency = row["latency_seconds"]
        attempts_by_class.setdefault(key, {})[str(row["attempt_id"])] = (
            _parse_time(row["created_at"]),
            min(float(latency), LATENCY_CAP_MINUTES * 60.0) if latency is not None else None,
        )
    now = _parse_time(newest)
    pooled = [lat for cls in attempts_by_class.values() for (_t, lat) in cls.values() if lat is not None]
    fallback_seconds = statistics.median(pooled) if pooled else None
    minutes: list[float] = []
    censored = 0
    untimed = 0
    for attempts in attempts_by_class.values():
        ordered = sorted(attempts.values(), key=lambda pair: (pair[0] or 0.0))
        first_time = ordered[0][0]
        repeats = ordered[1:]
        if not repeats and now is not None and first_time is not None and (now - first_time) < CENSOR_DAYS * 86400:
            censored += 1
            continue
        total = 0.0
        for _when, latency in repeats:
            if latency is None:
                untimed += 1
                latency = fallback_seconds
            total += (latency or 0.0) / 60.0
        minutes.append(total)
    detail = {
        "classes_seen": len(attempts_by_class),
        "recurrence_groups_used": has_groups and bool(group_of),
        "untimed_repeat_attempts": untimed,
    }
    return minutes, censored, detail


def estimate_unresolved_cost(repository: Repository, *, pseudo_count: float) -> UnresolvedCost:
    """The shrunk minutes an unresolved persistent misconception costs."""

    seconds, sample = repository.median_attempt_latency_seconds()
    if seconds is not None and sample >= MIN_TIMED_ATTEMPTS:
        per_repeat = min(float(seconds) / 60.0, LATENCY_CAP_MINUTES)
        per_repeat_source = "pooled_attempt_latency"
    else:
        per_repeat, per_repeat_source = AL.DEFAULT_INTERVENTION_MINUTES, "heuristic_default"
    prior = EEDI_EXCESS_REPEAT_RATE * ENCOUNTERS_UNTIL_CAUGHT * per_repeat
    personal, censored, detail = _personal_history(repository)
    detail = {**detail, "timed_attempts": int(sample or 0)}
    n = len(personal)
    k = max(float(pseudo_count), 0.0)
    mean_personal = statistics.fmean(personal) if personal else None
    if n == 0 or mean_personal is None:
        value, weight, provenance = prior, 1.0, "population_prior"
    else:
        weight = k / (k + n) if (k + n) > 0 else 0.0
        value = weight * prior + (1.0 - weight) * mean_personal
        provenance = "measured"
    return UnresolvedCost(
        minutes=max(value, 0.0),
        provenance=provenance,
        prior_minutes=prior,
        prior_weight=weight,
        personal_mean_minutes=mean_personal,
        personal_classes=n,
        censored_classes=censored,
        minutes_per_repeat=per_repeat,
        minutes_per_repeat_source=per_repeat_source,
        pseudo_count=k,
        detail=detail,
    )


def unresolved_minutes_for_hypotheses(
    repository: Repository,
    hypothesis_ids: Sequence[str],
    *,
    pseudo_count: float,
) -> tuple[dict[str, dict[str, Any]], UnresolvedCost]:
    """``({hypothesis: {"minutes": U, provenance...}}, estimate)`` for a causal loss table.

    A hypothesis whose cause is not persistent (a transient slip, the item's
    contract, the grader's reading, the interaction context) costs nothing
    later once the moment passes: it gets 0 minutes with that reason. The
    per-cell entry is compact; the full estimate goes on the receipt.
    """

    estimate = estimate_unresolved_cost(repository, pseudo_count=pseudo_count)
    full = estimate.as_dict()
    out: dict[str, dict[str, Any]] = {}
    for hypothesis_id in hypothesis_ids:
        row = repository.causal_hypothesis(str(hypothesis_id))
        scope = str((row or {}).get("cause_scope") or "unknown")
        if scope in PERSISTENT_SCOPES:
            out[str(hypothesis_id)] = {
                "minutes": estimate.minutes,
                "provenance": estimate.provenance,
                "source": full["source"],
                "prior_weight": full["prior_weight"],
                "personal_classes": estimate.personal_classes,
                "version": UNRESOLVED_COST_VERSION,
                "cause_scope": scope,
            }
        else:
            out[str(hypothesis_id)] = {
                "minutes": 0.0,
                "provenance": "structural",
                "source": "not_a_persistent_cause",
                "version": UNRESOLVED_COST_VERSION,
                "cause_scope": scope,
            }
    return out, estimate

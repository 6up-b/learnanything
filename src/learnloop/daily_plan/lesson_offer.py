"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): lesson offers as candidates of the router objective.

At a reversible ``plan_block`` boundary where the objective serves (its tag, ``router.lesson_suggestions.in_objective``
and TE1b's suggestions on), TE1b's best ``instruct(lesson)`` candidate by its staged value (``log P(accept) +
log(1 − p)``, :mod:`learnloop.router.lesson_suggestions`) joins the decision's support as a plan block of its own (no
items, no reading: the offer card), beside staged's top ``router.k``: one offer a decision (``keep``, one card at a
time), its alternatives (up to two, ``keep``) the next candidates, shown and never valued. TE1b's acceptance model is
the offer's sensor, never a gate: its posterior predictive's mean and spread (moment-matched to a Beta, the draws'
``p``) value the offer's two branches in RO4's offer interface (``router_objective.value``):

* **accepted**: the lesson action (TE3a's lesson curve on the target through ``objective_inputs``, at the lesson-check
  mass §12.1 learned, ``learner.lesson_weight``), its active minutes log-normal (:func:`duration_model`: seeded at the
  card's 15 minutes, learned from TE2-log's ``lesson_activity_intervals``), its retention check committed at its
  date (``teacher.delayed``'s seeded fallback: the lesson's own date is set from retrievability at its close, after
  this decision) so its information enters ``E[V(x′)]``;
* **declined**: the tail's next non-offer block at the same session minutes (RO4's offer interface as built).

Nothing here is drawn: the offer is drawn by the objective's logged mix like any candidate (G3), and answered on that
decision (:mod:`learnloop.daily_plan.lesson_suggestion`'s ``respond``; ``ignored`` at the next boundary's step). No
offer: below the tag or switched off; at a boundary with forced items (a follow-up, a request, a check: never inside a
cold check, a probe or a randomized-check block); while an accepted offer's lesson waits to open; once the day's
shown offers and cards reach ``router.lesson_suggestions.ceiling_per_day`` (``keep``; the bind is logged on the
decision); with no candidate.

The context is read at hour resolution (:data:`CONTEXT_RESOLUTION_DAYS`, numerical: a prefetch and its serve then
share one boundary key) and frozen with the candidate; every number the value reads is in its annotations, so the
logged candidate set and the trace recompute.
"""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from learnloop.adf_numeric import NODES, WEIGHTS, sigmoid
from learnloop.clock import parse_utc
from learnloop.daily_plan.types import LESSON_OFFER_PREFIX, LESSON_OFFER_SUBTYPE, BlockCandidate
from learnloop.db.stores import router_suggestions as store
from learnloop.router import lesson_suggestions as LS

LOG = logging.getLogger(__name__)

OFFER_VERSION = "lesson_offer_v1"
#: The duration model's identity (a changed prior is a new version).
DURATION_VERSION = "lesson_duration_lognormal_v1"

# --- the lesson's active minutes, log-normal (spec §15.1a "duration") ------------------------------------------
#: The seeded median: the card's own estimate ("about 15 min", ``lesson_suggestions.CARD_MINUTES``; basis legacy).
DURATION_PRIOR_MEDIAN = float(LS.CARD_MINUTES)
#: The spread of one lesson's active minutes on the log scale (basis legacy, "a wide log-sd": about a factor of two
#: either way); a labelled prior the closed lessons' minutes refine through the median's posterior.
DURATION_LOG_SD = 0.7
#: The prior sd of the log median (basis legacy: as wide as one lesson's own spread).
DURATION_MEDIAN_PRIOR_SD = 0.7
#: Numerical resolution of the offer's context (days): the local hour, the days since the last suggestion and since a
#: "Not now" are read at one hour, so a prefetch and its serve, minutes apart, share one boundary key.
CONTEXT_RESOLUTION_DAYS = 1.0 / 24.0


def offers_on(vault: Any) -> bool:
    """Lesson offers serve: TE3b's tag and switch with the objective serving and TE1b's suggestions on
    (``router_objective_switches.lesson_offers_on``), on a plan the objective decides (``policy.objective_active``)."""

    from learnloop.daily_plan.policy import objective_active
    from learnloop.router_objective_switches import lesson_offers_on

    return lesson_offers_on(vault.config) and objective_active(vault)


def is_offer(candidate: Any) -> bool:
    return getattr(candidate, "subtype", None) == LESSON_OFFER_SUBTYPE


def offer_ref(learning_object_id: str) -> str:
    return f"{LESSON_OFFER_PREFIX}{learning_object_id}"


@dataclass(frozen=True)
class Offer:
    """One boundary's offer (``candidate`` None: none, ``record`` says why) and its record for the decision."""

    candidate: BlockCandidate | None
    record: Mapping[str, Any] = field(default_factory=dict)


# =============================================================================
# The sensors
# =============================================================================


def accept_moments(state: LS.AcceptanceState, context: LS.Context, candidate: LS.Candidate) -> tuple[float, float]:
    """``P(accept)``'s posterior mean and sd: the recovery grid's mixture of ``σ(h·θ)``, ``h·θ ~ N(h·m, h·Σ·h)`` per
    grid point, each by AD's quadrature (the mean is :meth:`LS.AcceptanceState.p_accept`'s)."""

    weights = state.weights()
    first = second = 0.0
    for weight, bank in zip(weights, state.banks):
        h = LS.design_vector(context, candidate, bank.recovery_days)
        m, v = float(h @ bank.mean), max(float(h @ bank.cov @ h), 0.0)
        p = sigmoid(m + math.sqrt(v) * NODES)
        first += float(weight) * float((WEIGHTS * p).sum())
        second += float(weight) * float((WEIGHTS * p * p).sum())
    mean = min(max(first, 0.0), 1.0)
    return mean, math.sqrt(max(second - mean * mean, 0.0))


def beta_from_moments(mean: float, sd: float) -> tuple[float, float]:
    """The Beta with this mean and sd (moment matching; structural): the value's per-draw ``p``. A spread at or past
    the Bernoulli's own is held just inside it."""

    m = min(max(float(mean), 1e-9), 1.0 - 1e-9)
    variance = min(max(float(sd) ** 2, 1e-12), m * (1.0 - m) * (1.0 - 1e-9))
    k = m * (1.0 - m) / variance - 1.0
    return m * k, (1.0 - m) * k


def _union_seconds(rows: Sequence[tuple[str, str]]) -> float:
    total, reach = 0.0, None
    for began, ended in sorted((parse_utc(a), parse_utc(b)) for a, b in rows):
        if reach is None or began > reach:
            total += (ended - began).total_seconds()
            reach = ended
        elif ended > reach:
            total += (ended - reach).total_seconds()
            reach = ended
    return max(total, 0.0)


def lesson_active_minutes(connection: Any, *, at: str) -> list[float]:
    """Each lesson closed by ``at`` with foreground intervals: its active minutes (TE2-log §11.6: the union of its
    foreground intervals inside its opening and close; a lesson with none has active unknown and is left out)."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'lesson_activity_intervals'"
                          ).fetchone() is None:
        return []
    out: list[float] = []
    lessons = connection.execute(
        "SELECT id, opened_at, closed_at FROM lessons WHERE closed_at IS NOT NULL AND closed_at <= ? "
        "ORDER BY closed_at, id", (at,)).fetchall()
    for lesson_id, opened, closed in lessons:
        rows = [(max(str(a), str(opened)), min(str(b), str(closed))) for a, b in connection.execute(
            "SELECT started_at, ended_at FROM lesson_activity_intervals WHERE lesson_id = ? AND foreground = 1 "
            "AND ended_at > ? AND started_at < ?", (lesson_id, opened, closed))]
        rows = [(a, b) for a, b in rows if b > a]
        if rows:
            seconds = _union_seconds(rows)
            if seconds > 0:
                out.append(seconds / 60.0)
    return out


def duration_model(connection: Any, *, at: str) -> dict[str, Any]:
    """The lesson's active minutes, log-normal: the log median's normal posterior from its labelled prior and the
    closed lessons' active minutes (known spread :data:`DURATION_LOG_SD`), and the predictive's median and log-sd
    (sampled in the value, never averaged)."""

    minutes = lesson_active_minutes(connection, at=at)
    prior_precision = 1.0 / DURATION_MEDIAN_PRIOR_SD ** 2
    precision = prior_precision + len(minutes) / DURATION_LOG_SD ** 2
    mean = (math.log(DURATION_PRIOR_MEDIAN) * prior_precision
            + sum(math.log(value) for value in minutes) / DURATION_LOG_SD ** 2) / precision
    log_sd = math.sqrt(DURATION_LOG_SD ** 2 + 1.0 / precision)
    return {"version": DURATION_VERSION, "median_minutes": round(math.exp(mean), 6), "log_sd": round(log_sd, 6),
            "source": f"fitted, n={len(minutes)}" if minutes else "seed",
            "prior": {"median_minutes": DURATION_PRIOR_MEDIAN, "log_sd": DURATION_LOG_SD,
                      "median_prior_sd": DURATION_MEDIAN_PRIOR_SD, "basis": "legacy: the card's own estimate"}}


def check_mass(vault: Any, repository: Any, learning_object_id: str, *, at: str) -> dict[str, Any]:
    """The lesson-check mass the lesson's effect is scaled by (RO4's placeholder, ``γ`` at it; spec §12.1's learned
    weight, ``learner.lesson_weight``): its posterior mean and sd as of ``at`` on the target (no confidence or
    prediction term). Unreadable: its seeded prior's (σ of η₀ ~ N(0, 1)), said so."""

    try:
        from learnloop.learner import lesson_weight as LW

        state = LW.replay_state(vault, repository, as_of=at)
        weights = state.tau_weights()
        moments = state.eta_moments(learning_object_id, 0.0, 0.0)
        source = f"lesson_weight ({LW.PRIORS_VERSION}, {state.updates} updates)"
    except Exception:  # noqa: BLE001 - the prior stands in, and the record says so
        LOG.warning("lesson offer: the lesson-check mass was not read", exc_info=True)
        weights, moments, source = np.array([1.0]), [(0.0, 1.0)], "prior (not read)"
    first = second = 0.0
    for weight, (m, v) in zip(weights, moments):
        p = sigmoid(m + math.sqrt(max(v, 0.0)) * NODES)
        first += float(weight) * float((WEIGHTS * p).sum())
        second += float(weight) * float((WEIGHTS * p * p).sum())
    return {"mean": round(first, 9), "sd": round(math.sqrt(max(second - first * first, 0.0)), 9), "source": source}


# =============================================================================
# The ledger, read together with TE1b's
# =============================================================================


def _quantized(context: LS.Context) -> LS.Context:
    step = CONTEXT_RESOLUTION_DAYS

    def days(value: float | None) -> float | None:
        return None if value is None else math.floor(float(value) / step) * step

    return LS.Context(local_hour=float(math.floor(context.local_hour)), minutes_left=context.minutes_left,
                      reentry=context.reentry, days_since_last=days(context.days_since_last))


def shown_today(decisions: Sequence[Mapping[str, Any]], today: str) -> int:
    """The day's shown cards and drawn offers together (the ceiling's count)."""

    return sum(1 for decision in decisions if (decision.get("detail") or {}).get("shown") and decision["day"] == today)


def pending_start(connection: Any, decisions: Sequence[Mapping[str, Any]]) -> bool:
    """An accepted card or offer whose lesson never opened (TE1b ruling R2's reservation) is still waiting."""

    from learnloop.daily_plan.lesson_suggestion import card_view

    return any((card_view(connection, decision) or {}).get("pending_lesson") is not None for decision in decisions)


# =============================================================================
# The boundary's offer
# =============================================================================


def build(vault: Any, repository: Any, *, today: str, now_iso: str, local_hour: float, minutes_left: float | None,
          reentry: bool, forced: bool) -> Offer:
    """This boundary's offer, or none with why (module docstring)."""

    from learnloop.daily_plan import lesson_suggestion as LSS

    if forced:
        # Never beside a follow-up, a request or a check (so never inside a cold check, a probe or a
        # randomized-check block).
        return Offer(None, {"version": OFFER_VERSION, "status": "none:forced_items"})
    config = vault.config.router
    ceiling = int(config.lesson_suggestions.ceiling_per_day)
    base: dict[str, Any] = {"version": OFFER_VERSION, "ceiling": {"per_day": ceiling}}
    with repository.connection() as connection:
        if not store.tables_present(connection):
            return Offer(None, {**base, "status": "none:no_ledger"})
        decisions = store.all_decisions(connection)
        responses = store.responses(connection)
        releases = store.releases(connection)
        shown = shown_today(decisions, today)
        if shown >= ceiling:
            # ``keep``: the anti-nagging ceiling binds across the day's offers and cards; each bind is logged.
            return Offer(None, {**base, "status": "none:ceiling_bound",
                                "ceiling": {"per_day": ceiling, "shown_today": shown, "bound": True}})
        if pending_start(connection, decisions):
            return Offer(None, {**base, "status": "none:pending_start"})
    candidates, excluded = LSS.build_candidates(vault, repository, now_iso=now_iso)
    if not candidates:
        return Offer(None, {**base, "status": "none:no_candidate", "excluded": excluded,
                            "ceiling": {"per_day": ceiling, "shown_today": shown, "bound": False}})
    details = {str(d["id"]): d["detail"] for d in decisions}
    state = LS.replay(LS.observations(details, responses))
    now = parse_utc(now_iso)
    shown_rows = [d for d in decisions if (d.get("detail") or {}).get("shown")]
    since = None
    if shown_rows:
        since = LS.days_between(now, parse_utc(str(shown_rows[-1]["created_at"])))
    elif decisions:
        since = LS.days_between(now, parse_utc(str(decisions[0]["created_at"])))
    context = _quantized(LS.Context(local_hour=float(local_hour), minutes_left=minutes_left, reentry=bool(reentry),
                                    days_since_last=since))
    declined = LS.declines_by_learning_object(details, [*responses, *(r for r in releases
                                                                      if r["response"] == "released")])
    dated = []
    for candidate in candidates:
        days = [LS.days_between(now, parse_utc(declined[lo])) for lo in candidate.learning_object_ids
                if declined.get(lo)]
        step = CONTEXT_RESOLUTION_DAYS
        dated.append(replace(candidate, days_since_decline=(math.floor(min(days) / step) * step) if days else None))
    scored = LS.score(state, context, dated, k=max(int(config.k), 1 + LS.MAX_ALTERNATIVES))
    top, alternatives = scored[0], list(scored[1:1 + LS.MAX_ALTERNATIVES])
    lo = top.candidate.learning_object_ids[0]
    mean, sd = accept_moments(state, context, top.candidate)
    a, b = beta_from_moments(mean, sd)
    with repository.connection() as connection:
        duration = duration_model(connection, at=now_iso)
    mass = check_mass(vault, repository, lo, at=now_iso)
    delayed = vault.config.teacher.delayed
    checks = [{"lo": lo, "purpose": "retention", "days": float(delayed.fallback_retention_days),
               "basis": "teacher.delayed.fallback_retention_days (the lesson's own date is set at its close)"}]
    record = {
        **base, "status": "offered", "context": context.as_dict(), "priors_version": LS.PRIORS_VERSION,
        "card": {"candidates": [top.as_dict(), *(entry.as_dict() for entry in alternatives)]},
        "reason": top.candidate.reason, "learning_object_id": lo,
        "p_accept": {"mean": round(mean, 9), "sd": round(sd, 9), "beta": [round(a, 9), round(b, 9)],
                     "basis": "TE1b's acceptance model's posterior predictive, moment-matched to a Beta"},
        "duration": duration, "mass": mass, "checks": checks, "model": state.summary(),
        "ceiling": {"per_day": ceiling, "shown_today": shown, "bound": False},
        "candidates_considered": len(candidates),
        "staged_value": round(top.value, 12),
    }
    title = top.candidate.title or lo
    candidate = BlockCandidate(
        candidate_id=offer_ref(lo), lane="new", action="instruct", subtype=LESSON_OFFER_SUBTYPE,
        learning_object_ids=(lo,), item_ids=(), reading=None, est_minutes=float(duration["median_minutes"]),
        planner_value=round(top.value, 12), reason=LSS.REASON_WORDS.get(top.candidate.reason, ""),
        annotations={"reversible": True, "reason_code": "lesson_offer", "topic": title,
                     "lesson_offer": json.loads(json.dumps(record, sort_keys=True))})
    return Offer(candidate, {key: value for key, value in record.items() if key not in ("model", "card")}
                 | {"candidate_id": candidate.candidate_id})


#: The offer block's ``block_ended`` outcomes: the learner's response, or ``ignored`` (moved on without one).
ENDED_OUTCOMES: tuple[str, ...] = ("accepted", "chose_alternative", "declined", "ignored")


def _block_state(connection: Any, block_id: str | None) -> tuple[bool, str | None]:
    """Whether the offer's block has ended, and its plan's status."""

    if not block_id:
        return True, None
    ended = connection.execute(
        "SELECT 1 FROM attention_block_events WHERE block_id = ? AND kind = 'block_ended' LIMIT 1", (block_id,)
    ).fetchone() is not None
    plan = connection.execute(
        "SELECT p.status FROM attention_blocks b JOIN daily_plans p ON p.id = b.daily_plan_id WHERE b.id = ?",
        (block_id,)).fetchone()
    return ended, (str(plan[0]) if plan is not None else None)


def end_block(connection: Any, block_id: str | None, outcome: str, *, at: str) -> None:
    """End the offer's block with the learner's response (once; a block already ended is left as it is)."""

    from learnloop.db.stores import daily_plans as plan_store
    from learnloop.ids import new_ulid

    if not block_id or outcome not in ENDED_OUTCOMES:
        return
    ended, _status = _block_state(connection, block_id)
    if ended:
        return
    plan_store.append_block_event(connection, event_id=new_ulid(), block_id=block_id, kind="block_ended",
                                  detail={"outcome": outcome, "minutes_counted": 0.0, "lesson_offer": True},
                                  created_at=at)


def record_ignored(connection: Any, decision: Mapping[str, Any], *, at: str, why: str) -> bool:
    """The boundary passed with no answer (spec §15.1a): ``ignored`` on the offer's own decision, once (the ledger's
    one response a decision), its block ended so."""

    primary = ((decision.get("detail") or {}).get("card") or {}).get("candidates") or [{}]
    written = store.insert_response(
        connection, decision_id=str(decision["id"]), response="ignored", candidate_ref=str(primary[0].get("ref") or ""),
        learning_object_ids=list(primary[0].get("learning_object_ids") or []), responded_at=at,
        detail={"recorded": why, "shown_on": decision.get("day"), "plan_offer": True})
    end_block(connection, (decision.get("detail") or {}).get("block_id"), "ignored", at=at)
    return written


def sweep_ignored(connection: Any, *, today: str, now_iso: str) -> int:
    """Every drawn offer left unanswered whose boundary has passed (its block ended, its plan no longer open, or an
    earlier day): ``ignored`` (the next boundary's step)."""

    if not store.tables_present(connection):
        return 0
    written = 0
    for decision in store.offer_decisions(connection):
        if store.response_for(connection, str(decision["id"])) is not None:
            continue
        ended, status = _block_state(connection, (decision.get("detail") or {}).get("block_id"))
        if ended or status != "open" or str(decision.get("day") or "") < today:
            written += int(record_ignored(connection, decision, at=now_iso, why="next_boundary_step"))
    return written


def card(candidate: BlockCandidate) -> dict[str, Any]:
    """The offer card a drawn offer's block shows and its decision records (``lesson_offer`` on the block's detail
    and the decision row): its context and candidates (the acceptance model's replay inputs), the value's sensors."""

    return dict((candidate.annotations or {}).get("lesson_offer") or {})


def action_inputs(candidate: BlockCandidate) -> dict[str, Any]:
    """What the value estimator reads for the offer (``objective_inputs.action_for``)."""

    record = card(candidate)
    lo = str(record.get("learning_object_id") or (candidate.learning_object_ids or ("",))[0])
    duration = record.get("duration") or {}
    p_accept = record.get("p_accept") or {}
    beta = p_accept.get("beta") or [1.0, 1.0]
    return {"lo": lo, "minutes": float(duration.get("median_minutes") or candidate.est_minutes),
            "log_sd": float(duration.get("log_sd") or 0.0), "mass": float((record.get("mass") or {}).get("mean") or 0.5),
            "accept": (float(beta[0]), float(beta[1])),
            "checks": tuple((str(check.get("lo") or lo), float(check.get("days") or 0.0))
                            for check in record.get("checks") or ())}


__all__ = [
    "CONTEXT_RESOLUTION_DAYS", "DURATION_LOG_SD", "DURATION_MEDIAN_PRIOR_SD", "DURATION_PRIOR_MEDIAN",
    "DURATION_VERSION", "OFFER_VERSION", "Offer", "accept_moments", "action_inputs", "beta_from_moments", "build",
    "card", "check_mass", "duration_model", "is_offer", "lesson_active_minutes", "offer_ref", "offers_on",
    "pending_start", "shown_today",
]

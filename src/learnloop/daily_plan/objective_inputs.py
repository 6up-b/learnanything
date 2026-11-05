"""Router objective RO4 (spec §8.1, §8.4-§8.6): the frozen belief one block decision values its candidates on.

It reads, at the decision and never later:

* **the valued topics**: the candidates' LOs, then every active goal's scope (dated goals first), then the LOs the
  learner has practised (newest first), at most :data:`TOPIC_LIMIT` (``keep``; the trace states what was left out);
* **per topic**, AD's predictive ``p̄`` on the logit scale (``adaptive_difficulty.readiness``) with the mastery
  posterior's variance (AD's cold-start variance for an untested cell), the FSRS state of its practised items (median
  stability and difficulty, median days since the last review), its undated density ``c_L`` (the largest of its
  active goals' copied densities, the config's for a retention topic) and every dated use ``ω_{g,L}`` at its date;
* **the session**: active minutes in the objective's session (a gap of ``session_gap_minutes`` ends it), the plan's
  remembered minutes ``m̄`` and their source, the learner's own return gaps (next day with none), the stop offer's
  acceptance posterior from §4 row 7, the spread of the learner's own durations;
* **the candidates** as :class:`~learnloop.router_objective.value.Action` (§8.1's interfaces), the stop offer as
  its two branches.

Every number's source is in ``sources``; nothing here writes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
import json
import logging
import math
from statistics import median, pstdev
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.types import STOP_FOR_TODAY, BlockCandidate, PlanState
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V

LOG = logging.getLogger(__name__)

#: ``keep``: the most topics one decision values (work bound; the trace counts what was left out).
TOPIC_LIMIT = 120
#: ``keep``: the newest return gaps and durations read (work bounds, never judgements).
RETURN_GAP_LIMIT = 60
DURATION_LIMIT = 500
_PROBE_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "probe"})


def _logit(p: float) -> float:
    p = min(max(float(p), 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def _days(later: datetime, earlier: datetime) -> float:
    return max((later - earlier).total_seconds() / 86400.0, 0.0)


def plan_minutes(repository: Any, plan_id: str | None) -> tuple[float, str]:
    """``m̄`` and where it came from (the plan's remembered minutes: the learner's choice, carried, or a default)."""

    if plan_id:
        with repository.connection() as connection:
            row = connection.execute("SELECT remembered_minutes, minutes_source FROM daily_plans WHERE id = ?",
                                     (plan_id,)).fetchone()
        if row is not None and row[0] is not None:
            return float(row[0]), str(row[1] or "unknown")
    return 0.0, "missing"


def _goal_uses(vault: Any, repository: Any, now: datetime) -> tuple[dict[str, float], list[V.DatedUse], dict[str, Any],
                                                                   list[str]]:
    from learnloop.goals.goal_projection import resolve_goal_scope
    from learnloop.goals.use_weights import for_goal

    densities: dict[str, float] = {}
    dated: list[V.DatedUse] = []
    goals: dict[str, Any] = {}
    order: list[str] = []
    for goal in getattr(vault, "goals", None) or ():
        if getattr(goal, "status", None) != "active":
            continue
        try:
            scope = sorted(resolve_goal_scope(vault, goal, repository))
        except Exception:  # noqa: BLE001 - a malformed goal never blocks the plan
            continue
        weights = for_goal(goal, repository, vault.config)
        due = parse_utc(str(goal.due_at)) if getattr(goal, "due_at", None) else None
        days = _days(due, now) if due is not None else None
        goals[str(goal.id)] = {**weights.as_dict(), "due_at": getattr(goal, "due_at", None), "days_to_date": days,
                               "scope": len(scope), "los": list(scope)}
        for lo in scope:
            densities[lo] = max(densities.get(lo, 0.0), weights.undated_density)
            if due is not None and due > now:
                dated.append(V.DatedUse(goal_id=str(goal.id), lo=lo, at_days=float(days), weight=weights.for_lo(lo)))
        order.extend(lo for lo in scope if lo not in order)
    return densities, dated, goals, order


def _practiced(connection: Any, vault: Any) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    items = getattr(vault, "practice_items", {})
    by_lo: dict[str, list[dict[str, Any]]] = {}
    newest: dict[str, str] = {}
    for row in connection.execute(
            "SELECT practice_item_id, stability, difficulty, last_attempt_at FROM practice_item_state "
            "WHERE stability IS NOT NULL AND last_attempt_at IS NOT NULL"):
        item = items.get(str(row[0]))
        lo = getattr(item, "learning_object_id", None)
        if not lo:
            continue
        by_lo.setdefault(str(lo), []).append({"s": float(row[1]), "d": float(row[2] or 5.0), "last": str(row[3])})
        if str(row[3]) > newest.get(str(lo), ""):
            newest[str(lo)] = str(row[3])
    return by_lo, sorted(newest, key=lambda lo: newest[lo], reverse=True)


def _mastery(connection: Any, los: Sequence[str]) -> dict[str, tuple[float, float]]:
    if not los:
        return {}
    marks = ",".join("?" for _ in los)
    return {str(row[0]): (float(row[1]), float(row[2])) for row in connection.execute(
        f"SELECT learning_object_id, logit_mean, logit_variance FROM learning_object_mastery "
        f"WHERE learning_object_id IN ({marks})", list(los)) if row[1] is not None and row[2] is not None}


def _ad(vault: Any, repository: Any, los: Sequence[str]) -> dict[str, Any]:
    try:
        from learnloop.adaptive_difficulty.readiness import decision_state_fields

        return dict(decision_state_fields(vault, repository, list(los), reading_doses=True))
    except Exception:  # noqa: BLE001 - AD unavailable: the mastery posterior stands in, and the trace says so
        LOG.warning("router objective: adaptive difficulty's predictive was not read", exc_info=True)
        return {"status": "unavailable"}


def _return_gaps(connection: Any, gap_minutes: float) -> list[float]:
    rows = [str(row[0]) for row in connection.execute(
        "SELECT started_at FROM sessions ORDER BY started_at DESC LIMIT ?", (RETURN_GAP_LIMIT + 1,))]
    starts = sorted(filter(None, (parse_utc(row) for row in rows)))
    gaps = []
    for earlier, later in zip(starts, starts[1:]):
        days = _days(later, earlier)
        if days * 1440.0 >= gap_minutes:
            gaps.append(days)
    return gaps


def _stop_accept(connection: Any, prior: tuple[float, float]) -> tuple[tuple[float, float], dict[str, int]]:
    """§4 row 7: an offered stop the learner took (an end, ``offered_stop_accepted``) or overrode (a
    ``stop_response``); Beta(a + taken, b + overridden)."""

    counts = {"accepted": 0, "overridden": 0}
    try:
        for reason, kind, n in connection.execute(
                "SELECT end_reason, kind, COUNT(*) FROM session_receipts WHERE end_reason IN "
                "('offered_stop_accepted', 'offered_stop_overridden') GROUP BY end_reason, kind"):
            if reason == "offered_stop_accepted" and kind == "end":
                counts["accepted"] += int(n)
            elif reason == "offered_stop_overridden":
                counts["overridden"] += int(n)
    except Exception:  # noqa: BLE001 - below migration 243: the prior alone
        return prior, counts
    return (prior[0] + counts["accepted"], prior[1] + counts["overridden"]), counts


def _duration_spread(connection: Any) -> tuple[float, int]:
    """The pooled spread of the learner's own durations on the log scale (none observed: 0, the mean only)."""

    rows = [float(row[0]) for row in connection.execute(
        "SELECT latency_seconds FROM practice_attempts WHERE latency_seconds > 0 ORDER BY created_at DESC LIMIT ?",
        (DURATION_LIMIT,))]
    if len(rows) < 2:
        return 0.0, len(rows)
    return float(pstdev([math.log(value) for value in rows])), len(rows)


def _reading_los(vault: Any, repository: Any, candidate: BlockCandidate) -> tuple[str, ...]:
    if candidate.learning_object_ids:
        return tuple(candidate.learning_object_ids)
    reading = candidate.reading
    if reading is None:
        return ()
    try:
        from learnloop.section_map import learning_objects_for_section

        return tuple(learning_objects_for_section(vault, repository, extraction_id=reading.extraction_id,
                                                  section_id=reading.section_id))
    except Exception:  # noqa: BLE001 - an unmapped section has no topic: its value is its cost alone, said so
        return ()


def action_for(vault: Any, repository: Any, candidate: BlockCandidate, *, practiced: set[str],
               spread: float) -> V.Action:
    """§8.1's interface for one candidate block."""

    items = getattr(vault, "practice_items", {})
    modes = [getattr(items.get(item), "practice_mode", None) for item in candidate.item_ids]
    item_los = tuple(str(getattr(items.get(item), "learning_object_id", None) or
                         (candidate.learning_object_ids[0] if candidate.learning_object_ids else ""))
                     for item in candidate.item_ids)
    minutes = float(candidate.est_minutes)
    if candidate.reading is not None:
        return V.Action(ref=candidate.candidate_id, kind=V.READING, item_los=_reading_los(vault, repository, candidate),
                        minutes=minutes, minutes_log_sd=spread)
    if any(mode in _PROBE_MODES for mode in modes):
        lo = item_los[0] if item_los else ""
        repair = V.Action(ref=f"{candidate.candidate_id}:repair", kind=V.REPAIR, item_los=(lo,) * max(len(item_los), 1),
                          minutes=minutes, minutes_log_sd=spread)
        return V.Action(ref=candidate.candidate_id, kind=V.PROBE, item_los=(lo,), minutes=minutes,
                        minutes_log_sd=spread, repair=repair)
    if modes and all(mode == "teach_back" for mode in modes):
        return V.Action(ref=candidate.candidate_id, kind=V.TEACH_BACK, item_los=item_los, minutes=minutes,
                        minutes_log_sd=spread)
    if candidate.lane == "repair":
        kind = V.REPAIR
    elif candidate.lane == "maintain":
        kind = V.REVIEW
    elif candidate.lane == "new":
        kind = V.NEW_PRACTICE
    else:
        kind = V.REVIEW if all(lo in practiced for lo in item_los) else V.NEW_PRACTICE
    return V.Action(ref=candidate.candidate_id, kind=kind, item_los=item_los, minutes=minutes, minutes_log_sd=spread)


def _step(action: V.Action) -> V.Action:
    """A block as one step of a sequence: a probe step is its observation alone (what follows it in the sequence,
    then the tail, is what uses the information), never a nested repair bundle."""

    return replace(action, repair=None) if action.kind == V.PROBE else action


def build(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str],
          candidates: Mapping[str, BlockCandidate], now_iso: str, kappa0: float = 0.0,
          kappa_how: str = "unset",
          sequences: Mapping[str, Sequence[BlockCandidate]] | None = None) -> tuple[V.Inputs, list[V.Action], dict[str, Any]]:
    """The decision's frozen inputs, its actions in support order, and the sources the trace records.

    ``sequences``: a ref valued as the ordered sub-actions of these blocks (each its own interface: a mid-block
    alternative, §8.3; Codex review F5) instead of as its candidate alone.

    ``sources["population"]`` is §8.7's evaluation population, frozen from the active goals' scopes and the
    retention commitments (the LOs with FSRS memory) alone, so candidate support never changes it (F11); a
    candidate's LO outside it is still valued in the rollouts (at the config's density), and listed apart."""

    from learnloop.params.fitted_params import resolve_fsrs_weights
    from learnloop.router_objective import price as P

    config = vault.config
    section = config.router_objective
    now = parse_utc(now_iso) or datetime.now().astimezone()
    densities, dated, goals, goal_order = _goal_uses(vault, repository, now)
    remembered, remembered_source = plan_minutes(repository, state.plan_id)
    with repository.connection() as connection:
        by_lo, practiced_order = _practiced(connection, vault)
        session_minutes, session_start, session_basis = P.session_active_minutes(
            connection, now=now_iso, gap_minutes=float(section.session_gap_minutes))
        gaps = _return_gaps(connection, float(section.session_gap_minutes))
        accept, accept_counts = _stop_accept(connection, (float(section.stop_accept_prior_a),
                                                          float(section.stop_accept_prior_b)))
        spread, spread_n = _duration_spread(connection)
        candidate_los = [lo for ref in support if ref in candidates
                         for lo in (*candidates[ref].learning_object_ids,
                                    *(getattr(vault.practice_items.get(item), "learning_object_id", None) or ""
                                      for item in candidates[ref].item_ids)) if lo]
        reading_los = [lo for ref in support if ref in candidates and candidates[ref].reading is not None
                       for lo in _reading_los(vault, repository, candidates[ref])]
        dated_los = [use.lo for use in sorted(dated, key=lambda use: use.at_days)]
        ordered = list(dict.fromkeys([*candidate_los, *reading_los, *dated_los, *goal_order, *practiced_order]))
        kept = ordered[:TOPIC_LIMIT]
        mastery = _mastery(connection, kept)
    ad = _ad(vault, repository, kept)
    ad_los = ad.get("los") or {}
    from learnloop.adaptive_difficulty.priors import COLD_START_VARIANCE, DOSE_SCALES, GAMMA_PRIOR, READING_PRIORS

    default_c = float(section.undated_use_density)
    topics: list[V.Topic] = []
    topic_sources: dict[str, Any] = {}
    for lo in kept:
        fields = ad_los.get(lo) or {}
        raw = fields.get("p_bar_at_top_raw")
        if raw is not None:
            eta = _logit(float(raw))
            variance = mastery.get(lo, (0.0, COLD_START_VARIANCE))[1] if not fields.get("untested") else COLD_START_VARIANCE
            eta_source = "ad_predictive" + (":untested" if fields.get("untested") else "")
        elif lo in mastery:
            eta, variance = mastery[lo]
            eta_source = "mastery_posterior"
        else:
            eta, variance, eta_source = 0.0, COLD_START_VARIANCE, "ad_cold_start_prior"
        memory = by_lo.get(lo) or []
        practiced = bool(memory)
        stability = median(row["s"] for row in memory) if practiced else 0.0
        difficulty = median(row["d"] for row in memory) if practiced else 5.0
        elapsed = median(_days(now, parse_utc(row["last"]) or now) for row in memory) if practiced else 0.0
        in_goal = lo in densities
        enrolled = in_goal or practiced or lo in candidate_los or lo in reading_los
        c = densities.get(lo, default_c) if enrolled else 0.0
        dose = fields.get("reading_dose")
        topics.append(V.Topic(lo=lo, eta_mean=float(eta), eta_var=float(max(variance, 1e-9)), practiced=practiced,
                              difficulty=float(difficulty), stability=float(stability), elapsed_days=float(elapsed),
                              undated_density=float(c), reading_count=float(dose or 0.0)))
        topic_sources[lo] = {"eta": eta_source, "fsrs_items": len(memory),
                             "density": "goal" if in_goal else ("config" if practiced else
                                                                ("candidate_only" if enrolled else "not_enrolled")),
                             "ad_cell": fields.get("cell"),
                             "reading_dose": ("ad_reading_window" if dose is not None else "none_read: 0")}
    # §8.7's population: the active goals' scopes and the retention commitments, never the candidates (F11).
    population = {lo: float(densities.get(lo, default_c)) for lo in dict.fromkeys([*goal_order, *practiced_order])}
    spread_used = spread if spread_n >= 2 else 0.0
    practiced_set = {topic.lo for topic in topics if topic.practiced}
    actions: list[V.Action] = []
    for ref in support:
        if ref == STOP_FOR_TODAY:
            actions.append(V.Action(ref=ref, kind=V.STOP))
        elif sequences is not None and ref in sequences:
            steps = tuple(_step(action_for(vault, repository, part, practiced=practiced_set, spread=spread_used))
                          for part in sequences[ref])
            actions.append(V.Action(ref=ref, kind=V.SEQUENCE, steps=steps,
                                    item_los=tuple(lo for step in steps for lo in step.item_los),
                                    minutes=sum(step.minutes for step in steps)))
        elif ref in candidates:
            actions.append(action_for(vault, repository, candidates[ref], practiced=practiced_set, spread=spread_used))
    blocks = [candidates[ref] for ref in support if ref in candidates]
    block_minutes = (sum(float(block.est_minutes) for block in blocks) / len(blocks)) if blocks else max(remembered, 1.0)
    block_items = max(int(round(sum(max(len(block.item_ids), 1) for block in blocks) / len(blocks))), 1) if blocks else 1
    inputs = V.Inputs(
        topics=tuple(topics), dated=tuple(use for use in dated if use.lo in {t.lo for t in topics}),
        session_minutes=float(session_minutes),
        price=V.Price(kappa0=float(kappa0), remembered=max(float(remembered), 1.0), remembered_source=remembered_source,
                      regime=P.SEED),
        tail_block_minutes=float(block_minutes), tail_block_items=int(block_items),
        horizon_days=float(section.horizon_days), fsrs_weights=tuple(resolve_fsrs_weights(repository)),
        return_gaps_days=tuple(gaps), stop_accept=accept, combiner=M.Combiner(),
        learning=V.Learning(gamma=(GAMMA_PRIOR[1], GAMMA_PRIOR[2]),
                            gbar=((READING_PRIORS[0][1], READING_PRIORS[0][2]), (READING_PRIORS[1][1], READING_PRIORS[1][2])),
                            dose_scales=tuple(DOSE_SCALES), source="adaptive_difficulty.priors (prior means: the "
                                                                   "posterior is not read at this version)"),
    )
    sources = {
        "topics": topic_sources, "topic_limit": TOPIC_LIMIT, "topics_left_out": max(len(ordered) - len(kept), 0),
        "population": {"los": population, "basis": "active goals' scopes and retention commitments (LOs with FSRS "
                                                   "memory) at the decision; never the candidates"},
        "goals": goals, "remembered_minutes": remembered, "remembered_source": remembered_source,
        "session": {"minutes": session_minutes, "start": session_start, **session_basis},
        "return_gaps": {"n": len(gaps), "model": "empirical gaps, the same after every session's end (no return model "
                                                 "before RO5: the return effect is zero by construction)"
                        if gaps else "next day (no history)"},
        "stop_accept": {"prior": [float(section.stop_accept_prior_a), float(section.stop_accept_prior_b)],
                        "posterior": list(accept), **accept_counts},
        "durations": {"log_sd": spread_used, "n": spread_n,
                      "basis": "the learner's own latencies, pooled" if spread_n >= 2 else "none observed: the mean only"},
        "ad_status": ad.get("status"), "ad_state_hash": ad.get("state_hash"),
        "kappa0": kappa0, "kappa_how": kappa_how,
    }
    return inputs, actions, sources


__all__ = ["DURATION_LIMIT", "RETURN_GAP_LIMIT", "TOPIC_LIMIT", "action_for", "build", "plan_minutes"]

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
from learnloop.daily_plan.types import LESSON_OFFER_SUBTYPE, STOP_FOR_TODAY, BlockCandidate, PlanState
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V

LOG = logging.getLogger(__name__)

#: ``keep``: the most topics one decision values (work bound; the trace counts what was left out).
TOPIC_LIMIT = 120
#: ``keep``: the newest return gaps and durations read (work bounds, never judgements).
RETURN_GAP_LIMIT = 60
DURATION_LIMIT = 500
_PROBE_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "probe"})


def _lessons_on(config: Any) -> bool:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): at its tag with its switch on, lessons' active minutes count on
    the objective's clock (``price.activity_spans``) and LOs with a pending lesson delayed check join §8.7's
    population; off, or below the tag, mvp-0.52 exactly."""

    from learnloop.router_objective_switches import lesson_offers_on

    return lesson_offers_on(config)


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


def _ad(vault: Any, repository: Any, los: Sequence[str], *, learning_moments: bool = False,
        eta_moments: bool = False) -> dict[str, Any]:
    try:
        from learnloop.adaptive_difficulty.readiness import decision_state_fields

        if eta_moments:
            # The follow-up batch's landing ruling R10 (with R9's link): AD's latent posterior beside the predictive.
            return dict(decision_state_fields(vault, repository, list(los), reading_doses=True,
                                              learning_moments=learning_moments, eta_moments=True))
        if learning_moments:
            # RO5 §9 item 7: AD's fitted γ and reading curve beside the predictive (one read of the snapshot).
            return dict(decision_state_fields(vault, repository, list(los), reading_doses=True, learning_moments=True))
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


def _learning(ad: Mapping[str, Any], fitted: bool, gamma_prior: Any, reading_priors: Any, dose_scales: Any) -> V.Learning:
    """AD's learning parameters for the rollouts: RO4's prior means and variances, or (RO5 §9 item 7, at the tag with
    ``fitted_models``) the subject view's fitted posterior moments of ``γ`` and the reading curve, each parameter
    falling back to its prior where AD has none."""

    prior = V.Learning(gamma=(gamma_prior[1], gamma_prior[2]),
                       gbar=((reading_priors[0][1], reading_priors[0][2]), (reading_priors[1][1], reading_priors[1][2])),
                       dose_scales=tuple(dose_scales), source="adaptive_difficulty.priors (prior means: the "
                                                              "posterior is not read at this version)")
    moments = ad.get("learning") if fitted else None
    if not moments:
        return prior
    gamma = tuple(moments.get("gamma") or prior.gamma)
    gbar = (tuple(moments.get("gbar:1") or prior.gbar[0]), tuple(moments.get("gbar:2") or prior.gbar[1]))
    return V.Learning(gamma=(float(gamma[0]), float(gamma[1])),
                      gbar=((float(gbar[0][0]), float(gbar[0][1])), (float(gbar[1][0]), float(gbar[1][1]))),
                      dose_scales=tuple(dose_scales),
                      source="adaptive_difficulty subject view (fitted posterior moments; RO5 §9 item 7)",
                      lesson=_lesson_curve(ad.get("lesson_curve")))


def _lesson_curve(read: Any) -> V.LessonCurve | None:
    """Teacher TE3a (spec_teacher_v1 rev 5 §14.2): the lesson interface's effect, AD's ``landed`` curve as
    ``decision_state_fields`` read it through AD's read-only entry (present only at TE3a's tag with its switch on;
    absent: RO4's placeholder). With its seeded prior's moments (Codex review F2): the objective adds to the
    placeholder only what lessons taught the curve beyond them (none read: nothing learned, the placeholder)."""

    if not isinstance(read, Mapping) or not read.get("mean") or not read.get("cov"):
        return None

    def pair(value: Any) -> tuple[float, float]:
        return float(value[0]), float(value[1])

    def matrix(value: Any) -> tuple[tuple[float, float], tuple[float, float]]:
        return pair(value[0]), pair(value[1])

    prior_mean, prior_cov = read.get("prior_mean"), read.get("prior_cov")
    return V.LessonCurve(mean=pair(read["mean"]), cov=matrix(read["cov"]),
                         positions={str(lo): float(n) for lo, n in (read.get("positions") or {}).items()},
                         version=str(read.get("version") or ""),
                         source=f"adaptive_difficulty subject view ({read.get('source') or 'unknown'})",
                         prior_mean=pair(prior_mean) if prior_mean else None,
                         prior_cov=matrix(prior_cov) if prior_cov else None)


def _ad_link(vault: Any) -> V.AdLink | None:
    """The follow-up batch's landing ruling R9: AD's own predicted success (its lapse, its residual spread and its
    Gauss-Hermite rule, read from AD's model) at the batch's tag with ``[router_objective] ad_predictive_link``;
    None (mvp-0.49's ``σ``) below it or off."""

    from learnloop.router_objective_switches import followup_on

    if vault is None or not followup_on(vault.config, "ad_predictive_link"):
        return None
    from learnloop.adaptive_difficulty import model as ADM
    from learnloop.adaptive_difficulty import priors as ADP

    return V.AdLink(lapse=float(ADP.LAPSE), spread=float(ADP.A * ADP.TAU0),
                    nodes=tuple(float(x) for x in ADM.X32), weights=tuple(float(w) for w in ADM.W32))


def _combiner_prior(vault: Any, **fields: Any) -> M.Combiner:
    """The combiner's labelled prior: the follow-up batch's landing ruling R6 makes it monotone in ability at its tag
    (``memory.FORM_MONOTONE``, the fit in the same form); below it, RO4's linear one."""

    from learnloop.router_objective_switches import monotone_combiner_on

    if vault is not None and monotone_combiner_on(vault.config):
        return M.monotone_prior(**fields)
    return M.Combiner(**fields)


def _combiner(repository: Any, now_iso: str, vault: Any = None) -> M.Combiner:
    """RO5 §9 item 7: the memory model's Bayesian logistic combination fitted on resolved randomized checks (each
    check's sensors frozen at its administration against §6.2's label); with none resolved, the labelled prior. The
    checks stand as of the decision (landing ruling R1: ``checks.Closure`` at ``now_iso``). With ``vault`` at the
    follow-up batch's tag and ``combiner_trace_outcomes``, the traces' outcomes too (:func:`_combiner_with_traces`)."""

    from learnloop.router_objective import checks as C

    try:
        with repository.connection() as connection:
            resolved = C.resolve(connection, closure=C.Closure.at(now_iso))
    except Exception:  # noqa: BLE001 - the prior stands in, and the trace says so
        LOG.warning("router objective RO5: the combiner's checks were not read", exc_info=True)
        return _combiner_prior(vault)
    rows = []
    for entry in resolved:
        sensors = entry.sensors or {}
        if entry.status != "completed" or entry.outcome is None or sensors.get("eta") is None:
            continue
        rows.append((float(sensors["eta"]), sensors.get("retrievability"), int(entry.outcome >= 0.5)))
    if vault is not None:
        from learnloop.router_objective_switches import followup_on

        if followup_on(vault.config, "combiner_trace_outcomes"):
            return _combiner_with_traces(vault, repository, now_iso, rows,
                                         {str(entry.attempt_id) for entry in resolved if entry.attempt_id})
    if not rows:
        return _combiner_prior(vault, source="prior (no resolved randomized check yet)")
    fitted = M.fit_combiner(rows, prior=_combiner_prior(vault))
    return M.Combiner(mean=fitted.mean, variance=fitted.variance, n=fitted.n, form=fitted.form,
                      source="laplace_fit on resolved randomized checks")


def _combiner_with_traces(vault: Any, repository: Any, now_iso: str, check_rows: list[tuple[float, Any, int]],
                          check_attempts: set[str]) -> M.Combiner:
    """The follow-up batch's item 2 (RO4's item 6): the checks' rows plus the traces' frozen sensors joined to
    resolved cold outcomes (``router_objective.combiner_data``: RO2's resolver, per protocol, as of ``now_iso``
    through the availability predicate), refitted with the labelled prior. The trace names the fit's sources."""

    import numpy as np

    from learnloop.adaptive_difficulty.history_resolve import resolve_curves
    from learnloop.params.fitted_params import resolve_fsrs_weights
    from learnloop.router_objective import combiner_data as CD
    from learnloop.router_objective_switches import known_at

    joined: list[tuple[float, Any, int]] = []
    counts: dict[str, Any] = {"version": CD.JOIN_VERSION, "status": "not_read"}
    try:
        fsrs = M.Fsrs(tuple(resolve_fsrs_weights(repository)))

        def retrievability(stability: float, elapsed: float) -> float:
            return float(fsrs.retrievability(np.array([stability]), np.array([elapsed]))[0])

        with repository.connection() as connection:
            groups, skipped = CD.groups(connection, now=now_iso)
            resolved = resolve_curves(connection, vault, repository, groups, now=now_iso) if groups else []
            joined, counts = CD.rows(connection, resolved, now=now_iso,
                                     known_at=lambda row: known_at(row, vault.config),
                                     retrievability=retrievability, exclude=check_attempts)
        counts = {**counts, "status": "read", "decisions_joined_nothing": skipped}
    except Exception:  # noqa: BLE001 - the checks' fit (or the prior) stands in, and the trace says so
        LOG.warning("router objective: the combiner's trace outcomes were not read", exc_info=True)
        counts = {"version": CD.JOIN_VERSION, "status": "unavailable"}
    sources = {"randomized_checks": len(check_rows), "trace_outcomes": len(joined), "join": counts}
    rows = [*check_rows, *joined]
    if not rows:
        return _combiner_prior(vault, source="prior (no resolved outcome yet)", sources=sources)
    fitted = M.fit_combiner(rows, prior=_combiner_prior(vault))
    return M.Combiner(mean=fitted.mean, variance=fitted.variance, n=fitted.n, sources=sources, form=fitted.form,
                      source="laplace_fit on resolved randomized checks and the traces' sensors joined to resolved "
                             "cold outcomes")


def population(vault: Any, repository: Any, now_iso: str) -> dict[str, float]:
    """§8.7's population at ``now_iso`` with each LO's undated density: the active goals' scopes and the retention
    commitments (LOs with FSRS memory), never the candidates (RO5's checks draw over it, the traces' uses freeze
    it)."""

    now = parse_utc(now_iso) or datetime.now().astimezone()
    densities, _dated, _goals, goal_order = _goal_uses(vault, repository, now)
    with repository.connection() as connection:
        _by_lo, practiced_order = _practiced(connection, vault)
        lesson_order = _pending_lesson_check_los(connection, vault, now_iso)
    default_c = float(vault.config.router_objective.undated_use_density)
    return {lo: float(densities.get(lo, default_c)) for lo in dict.fromkeys([*goal_order, *practiced_order,
                                                                            *lesson_order])
            if lo in getattr(vault, "learning_objects", {})}


def _pending_lesson_check_los(connection: Any, vault: Any, now_iso: str) -> list[str]:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, owner decision 5): at its tag with its switch on, the LOs with a
    pending lesson delayed check as of the decision are retention commitments of §8.7's population (at their undated
    density, after the goals' scopes and the practised LOs: a population member already there keeps its place);
    off, or below the tag, none (the population is mvp-0.52's)."""

    if vault is None or not _lessons_on(vault.config):
        return []
    from learnloop.db.stores import lessons as lesson_store

    return list(dict.fromkeys(entry["learning_object_id"]
                              for entry in lesson_store.pending_delayed_checks(connection, at=now_iso,
                                                                               config=vault.config)))


def check_eligible_items(vault: Any, repository: Any, los: Sequence[str], exclude: Any = ()) -> dict[str, list[str]]:
    """RO5 §9 item 2's eligibility rule, per LO in id order: unseen (never attempted), unrevealed (no reveal row at
    all), unassisted so far (no help row), not exam-reserved, held out or protected, nor in any routine serving
    exclusion, and servable (the delayed checks' candidate rule)."""

    from learnloop import delayed_checks as D
    from learnloop.learner_protection import withheld_items
    from learnloop.scheduling.serving_exclusions import routine_serving_exclusions

    with repository.connection() as connection:
        attempted = {str(r[0]) for r in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}
        revealed = {str(r[0]) for r in connection.execute(
            "SELECT DISTINCT practice_item_id FROM reveal_events WHERE practice_item_id IS NOT NULL")}
        assisted: set[str] = set()
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'").fetchone():
            assisted = {str(r[0]) for r in connection.execute(
                "SELECT DISTINCT practice_item_id FROM help_assists WHERE practice_item_id IS NOT NULL")}
    withheld = withheld_items(vault, repository)
    excluded = set(routine_serving_exclusions(vault, repository).out_of_timing_item_ids) | assisted | set(exclude)
    out: dict[str, list[str]] = {}
    for lo in los:
        items = D.candidates(vault, repository, lo, exclude=excluded, withheld=withheld, attempted=attempted,
                             revealed=revealed)
        out[lo] = [str(item.id) for item in items if getattr(item, "status", "active") == "active"]
    return out


def check_sensors(vault: Any, repository: Any, lo: str, now_iso: str) -> dict[str, Any]:
    """RO5: a topic's sensors at a randomized check's administration (§9 item 7: the combiner is fitted on these
    against the check's outcome): AD's predictive on the logit scale and the FSRS retrievability of the LO's
    practised items (the decisions' own reads)."""

    out: dict[str, Any] = {"lo": lo}
    try:
        ad = _ad(vault, repository, [lo])
        raw = ((ad.get("los") or {}).get(lo) or {}).get("p_bar_at_top_raw")
        out["eta"] = _logit(float(raw)) if raw is not None else None
        with repository.connection() as connection:
            by_lo, _order = _practiced(connection, vault)
        memory = by_lo.get(lo) or []
        out["retrievability"] = None
        if memory:
            import numpy as np

            from learnloop.params.fitted_params import resolve_fsrs_weights

            now = parse_utc(now_iso) or datetime.now().astimezone()
            stability = median(row["s"] for row in memory)
            elapsed = median(_days(now, parse_utc(row["last"]) or now) for row in memory)
            r = M.Fsrs(tuple(resolve_fsrs_weights(repository))).retrievability(np.array([stability]), np.array([elapsed]))
            out["retrievability"] = float(r[0])
    except Exception:  # noqa: BLE001 - sensors are context for the combiner, never block the check
        LOG.warning("router objective RO5: the check's sensors for %s were not read", lo, exc_info=True)
        out["status"] = "unavailable"
    return out


def _return_model(connection: Any, config: Any) -> tuple[tuple[float, float] | None, dict[str, Any] | None]:
    """RO5 §9 item 1: stop's return model, from the sessions a stop coin was drawn in. None while the coin is off
    (the predecessor's frame) or before any such session has an observed return (its prior mean: no effect)."""

    from learnloop.router_objective import stop_coin as SC
    from learnloop.router_objective_switches import stop_coin_rate

    if stop_coin_rate(config) <= 0:
        return None, None
    section = config.router_objective
    rows = SC.return_rows(connection, gap_minutes=float(section.session_gap_minutes), lessons=_lessons_on(config))
    slope = SC.fit_return_slope(rows, float(section.return_slope_prior_sd))
    identified = slope.source == "posterior_randomized_coin"
    record = {**slope.as_dict(), "in_value": identified, "rows": len(rows),
              "contrasted": sum(1 for row in rows if row.weight != 0.0),
              "basis": "the stop coin's randomized offer against present-next as an instrument for the session's "
                       "minutes, availability before the draw as covariates (realized minutes are never the "
                       "treatment: Codex review F3; the observational form is rejected, T9)"}
    if not identified:
        record["note"] = "no randomized contrast with an observed return yet: the prior mean, no return effect"
        return None, record
    return (slope.mean, slope.variance), record


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
        from learnloop.adaptive_difficulty.switches import ad_enabled

        if not ad_enabled(getattr(vault, "config", None)):
            return _reading_los_outside_ad(vault, repository, reading)
        # AD on (RO2's ruling R6 at RO4's landing): the section's LOs as AD maps them, through the reading
        # chokepoint after the withheld rule, so the doses land where AD's reading curve counts them.
        from learnloop.adaptive_difficulty.reading import section_learning_objects

        return tuple(section_learning_objects(vault, repository, reading.extraction_id, reading.section_id))
    except Exception:  # noqa: BLE001 - an unmapped section has no topic: its value is its cost alone, said so
        return ()


def _reading_los_outside_ad(vault: Any, repository: Any, reading: Any) -> tuple[str, ...]:
    """AD off: no AD operation, no reading curve; the plan's own mapping (the raw-loading wrapper, as every
    caller outside AD)."""

    from learnloop.section_map import learning_objects_for_section

    return tuple(learning_objects_for_section(vault, repository, extraction_id=reading.extraction_id,
                                              section_id=reading.section_id))


def action_for(vault: Any, repository: Any, candidate: BlockCandidate, *, practiced: set[str],
               spread: float) -> V.Action:
    """§8.1's interface for one candidate block."""

    if candidate.subtype == LESSON_OFFER_SUBTYPE:
        # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer, valued by RO4's offer branches: accepted, the
        # lesson (TE3a's curve at the learned check mass, its minutes log-normal, its retention check committed);
        # declined, the tail's next non-offer block. ``p`` per draw from the acceptance model's Beta.
        from learnloop.daily_plan.lesson_offer import action_inputs

        offer = action_inputs(candidate)
        return V.Action(ref=candidate.candidate_id, kind=V.LESSON, item_los=(offer["lo"],), minutes=offer["minutes"],
                        minutes_log_sd=offer["log_sd"], mass=offer["mass"], accept=offer["accept"],
                        commitments=offer["checks"])
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
            connection, now=now_iso, gap_minutes=float(section.session_gap_minutes), lessons=_lessons_on(config))
        gaps = _return_gaps(connection, float(section.session_gap_minutes))
        return_slope, return_record = _return_model(connection, config)
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
        # Teacher TE3b (owner decision 5): LOs with a pending lesson delayed check (none off or below its tag).
        lesson_los = [lo for lo in _pending_lesson_check_los(connection, vault, now_iso)
                      if lo in getattr(vault, "learning_objects", {})]
        ordered = list(dict.fromkeys([*candidate_los, *reading_los, *dated_los, *goal_order, *practiced_order,
                                      *lesson_los]))
        kept = ordered[:TOPIC_LIMIT]
        mastery = _mastery(connection, kept)
    from learnloop.router_objective_switches import fitted_models_on

    fitted = fitted_models_on(config)
    link = _ad_link(vault)
    if link is not None:
        # R10: with R9's link, AD's latent posterior too (the rollouts start from it).
        ad = _ad(vault, repository, kept, learning_moments=fitted, eta_moments=True)
    else:
        ad = _ad(vault, repository, kept, learning_moments=True) if fitted else _ad(vault, repository, kept)
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
        enrolled = in_goal or practiced or lo in candidate_los or lo in reading_los or lo in lesson_los
        c = densities.get(lo, default_c) if enrolled else 0.0
        dose = fields.get("reading_dose")
        latent = fields.get("eta_at_top") if link is not None and raw is not None else None
        topics.append(V.Topic(lo=lo, eta_mean=float(eta), eta_var=float(max(variance, 1e-9)), practiced=practiced,
                              difficulty=float(difficulty), stability=float(stability), elapsed_days=float(elapsed),
                              undated_density=float(c), reading_count=float(dose or 0.0),
                              eta_latent=((float(latent["mean"]), float(max(latent["variance"], 1e-9)))
                                          if latent else None)))
        if latent:
            eta_source = f"{eta_source}+ad_latent_posterior"
        topic_sources[lo] = {"eta": eta_source, "fsrs_items": len(memory),
                             "density": "goal" if in_goal else ("config" if practiced or lo in lesson_los else
                                                                ("candidate_only" if enrolled else "not_enrolled")),
                             "ad_cell": fields.get("cell"),
                             "reading_dose": ("ad_reading_window" if dose is not None else "none_read: 0")}
    # §8.7's population: the active goals' scopes and the retention commitments, never the candidates (F11).
    population = {lo: float(densities.get(lo, default_c))
                  for lo in dict.fromkeys([*goal_order, *practiced_order, *lesson_los])}
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
    # The tail's block is the support's practice and reading blocks (TE3b: never a lesson offer's card).
    blocks = [candidates[ref] for ref in support if ref in candidates
              and candidates[ref].subtype != LESSON_OFFER_SUBTYPE]
    block_minutes = (sum(float(block.est_minutes) for block in blocks) / len(blocks)) if blocks else max(remembered, 1.0)
    block_items = max(int(round(sum(max(len(block.item_ids), 1) for block in blocks) / len(blocks))), 1) if blocks else 1
    inputs = V.Inputs(
        topics=tuple(topics), dated=tuple(use for use in dated if use.lo in {t.lo for t in topics}),
        session_minutes=float(session_minutes),
        price=V.Price(kappa0=float(kappa0), remembered=max(float(remembered), 1.0), remembered_source=remembered_source,
                      regime=P.SEED),
        tail_block_minutes=float(block_minutes), tail_block_items=int(block_items),
        horizon_days=float(section.horizon_days), fsrs_weights=tuple(resolve_fsrs_weights(repository)),
        return_gaps_days=tuple(gaps), stop_accept=accept, return_slope=return_slope,
        combiner=_combiner(repository, now_iso, vault) if fitted else _combiner_prior(vault),
        learning=_learning(ad, fitted, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES),
        ad_link=_ad_link(vault),
    )
    sources = {
        "topics": topic_sources, "topic_limit": TOPIC_LIMIT, "topics_left_out": max(len(ordered) - len(kept), 0),
        "population": {"los": population, "basis": "active goals' scopes and retention commitments (LOs with FSRS "
                                                   "memory) at the decision; never the candidates"
                       + ("; with LOs holding a pending lesson delayed check (teacher TE3b)" if _lessons_on(config)
                          else "")},
        "goals": goals, "remembered_minutes": remembered, "remembered_source": remembered_source,
        "session": {"minutes": session_minutes, "start": session_start, **session_basis},
        "return_gaps": {"n": len(gaps), "model": "empirical gaps, the same after every session's end (no return model "
                                                 "before RO5: the return effect is zero by construction)"
                        if gaps else "next day (no history)",
                        **({"return_model": return_record} if return_record is not None else {})},
        "stop_accept": {"prior": [float(section.stop_accept_prior_a), float(section.stop_accept_prior_b)],
                        "posterior": list(accept), **accept_counts},
        "durations": {"log_sd": spread_used, "n": spread_n,
                      "basis": "the learner's own latencies, pooled" if spread_n >= 2 else "none observed: the mean only"},
        "ad_status": ad.get("status"), "ad_state_hash": ad.get("state_hash"),
        "kappa0": kappa0, "kappa_how": kappa_how,
    }
    if inputs.learning.lesson is not None:
        # Teacher TE3a: the lesson interface's effect source (absent: RO4's placeholder, as before).
        curve = inputs.learning.lesson
        sources["lesson_curve"] = {"version": curve.version, "source": curve.source, "mean": list(curve.mean),
                                   "cov": [list(row) for row in curve.cov], "positions": dict(curve.positions),
                                   "prior_mean": list(curve.prior_mean) if curve.prior_mean else None,
                                   "prior_cov": [list(row) for row in curve.prior_cov] if curve.prior_cov else None,
                                   "effect": "RO4's placeholder plus the curve's learned shift from its prior"}
    from learnloop.router_objective_switches import followups_tag

    if followups_tag(config):
        # The follow-up batch (RO4's landing ruling R3, closed): the numbers the rollouts drew γ and the reading
        # curve from, beside their source, so a trace shows which posterior (or prior) valued its candidates.
        learning = inputs.learning
        sources["learning"] = {"gamma": list(learning.gamma), "gbar": [list(part) for part in learning.gbar],
                               "dose_scales": list(learning.dose_scales), "source": learning.source,
                               "ad_parameters_read": sorted((ad.get("learning") or {}) if fitted else ())}
    return inputs, actions, sources


__all__ = ["DURATION_LIMIT", "RETURN_GAP_LIMIT", "TOPIC_LIMIT", "action_for", "build", "plan_minutes"]

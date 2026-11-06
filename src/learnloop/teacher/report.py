"""The learned lesson-check weight's report lines (spec_teacher_v1 §12.1 "Kill switch and monitoring").

Read-only (``learnloop teacher report``; TE2 adds the lesson rows). Nothing
switches on any of these numbers: they show how far each learned quantity has
moved off its seeded prior, and how much its prior still decides.

* **Contraction:** each term's prior sd beside its posterior sd (η₀, β_c, β_p),
  and the per-LO offset scale's grid weights.
* **Prior sensitivity:** the global mass re-run with each prior mean shifted by
  ±1 prior sd.
* **Prequential log loss:** of the learned mass and of the fixed 0.5, side by
  side, over every resolved check (each scored before its own update).
* **The pool weight** λ̂ per forecaster, and the tap/hedge recalibration beside
  today's fixed map.

Teacher TE2-log (§11.10) adds: the pool weight's trajectory per forecaster (λ̂ and
its posterior sd from the seeded prior through every update of the trace
``lesson_weight_trace`` holds, so an earlier doctrine's or model's posterior stays
in view); the lessons (opened, closed by reason, active and elapsed minutes apart
with the intervals missing, delayed checks); the episodes; the probe and placement
forecasts scored, natural and randomized outcomes apart and labelled; and the
coverage of item 5's fields (:func:`lesson_report`).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from datetime import date
from typing import Any

from learnloop.learner import lesson_weight as LW


def _posterior_sd(state: LW.WeightState, index: int) -> float:
    weights = state.tau_weights()
    means = [float(bank.mean[index]) for bank in state.banks]
    mean = sum(w * m for w, m in zip(weights, means))
    second = sum(w * (float(bank.cov[index, index]) + float(bank.mean[index]) ** 2) for w, bank in zip(weights, state.banks))
    return math.sqrt(max(second - mean * mean, 0.0))


def report(vault: Any, repository: Any, *, today: str | None = None) -> dict[str, Any]:
    state = LW.replay_state(vault, repository)
    priors = {"eta0": LW.ETA0_PRIOR_SD, "beta_c": LW.BETA_C_PRIOR_SD, "beta_p": LW.BETA_P_PRIOR_SD}
    contraction = {}
    for term, index in LW.PRIOR_TERMS.items():
        sd = _posterior_sd(state, index)
        contraction[term] = {"prior_sd": priors[term], "posterior_sd": round(sd, 6),
                             "contraction": round(1.0 - sd / priors[term], 6)}
    baseline = state.learned_mass("", 0.0, 0.0)
    sensitivity = {}
    for term, sd in priors.items():
        sensitivity[term] = {
            sign: round(LW.replay_state(vault, repository, prior_shift={term: factor * sd}).learned_mass("", 0.0, 0.0), 6)
            for sign, factor in (("minus_1sd", -1.0), ("plus_1sd", 1.0))}
    learned_ll = sum(learned for learned, _fixed in state.prequential)
    fixed_ll = sum(fixed for _learned, fixed in state.prequential)
    lines = [
        f"lesson-check mass (global, no confidence or prediction effect): {baseline:.3f} "
        f"(prior centre 0.5; {state.updates} resolved check(s))",
        *[f"{term}: prior sd {entry['prior_sd']:.2f} -> posterior sd {entry['posterior_sd']:.3f}"
          for term, entry in contraction.items()],
        f"prequential log loss over {len(state.prequential)} resolved check(s): learned {-learned_ll:.4f} nats, "
        f"fixed 0.5 {-fixed_ll:.4f} nats",
        *[f"pool weight {family}: λ̂ = {state.pool_lambda(family):.3f} ({state.pool_updates.get(family, 0)} update(s); "
          "seeded prior Beta(1, 4), mean 0.2)" for family in sorted(state.pools)],
        "tap recalibration: " + ", ".join(
            f"{tap}: {state.tap_probability(tap):.2f} (map {LW.TAP_PRIOR_MAP[tap]:.2f})" for tap in LW.TAP_PRIOR_MAP)
        + f" ({state.tap.updates} answer(s))",
        "hedge recalibration: " + ", ".join(
            f"{value}: {state.hedge_probability(value):.2f}" for value in LW.HEDGE_VALUES)
        + f" ({state.hedge.updates} answer(s))",
    ]
    trajectory = LW.pool_trajectory(state.trace)
    for family, points in sorted(trajectory.items()):
        lines.append(f"pool weight trajectory {family}: " + ", ".join(
            f"{'prior' if p['at'] is None else str(p['at'])[:10]} λ̂ {p['lambda']:.3f} ± {p['sd']:.3f}" for p in points))
    lessons = lesson_report(vault, repository, today=today)
    lines.extend(lessons["lines"])
    return {
        "pool_trajectory": trajectory,
        **{key: value for key, value in lessons.items() if key != "lines"},
        "priors_version": LW.PRIORS_VERSION,
        "global_mass": round(baseline, 6),
        "resolved_checks": state.updates,
        "contraction": contraction,
        "tau_weights": dict(zip([str(t) for t in LW.TAU_GRID], [round(float(w), 6) for w in state.tau_weights()])),
        "prior_sensitivity": sensitivity,
        "prequential_log_loss": {"n": len(state.prequential), "learned_nats": round(-learned_ll, 6),
                                 "fixed_half_nats": round(-fixed_ll, 6)},
        "pool": {family: {"lambda": round(state.pool_lambda(family), 6), "updates": state.pool_updates.get(family, 0)}
                 for family in sorted(state.pools)},
        "calibration": {"tap": {str(t): round(state.tap_probability(t), 6) for t in LW.TAP_PRIOR_MAP},
                        "tap_updates": state.tap.updates,
                        "hedge": {v: round(state.hedge_probability(v), 6) for v in LW.HEDGE_VALUES},
                        "hedge_updates": state.hedge.updates},
        "lines": lines,
    }


# =============================================================================
# Teacher TE2-log (spec_teacher_v1 §11.10): the lessons, episodes, forecasts and coverage
# =============================================================================

#: Item 5's fields, as the coverage line counts them (an episode "has" a field when its column is set).
COVERAGE_FIELDS: dict[str, tuple[str, ...]] = {
    "hypothesis": ("hypothesis_hash",),
    "repair_class": ("repair_class",),
    "teacher_p": ("teacher_p",),
    "predicted_success": ("predicted_success",),
    "mastery": ("mastery_mean", "mastery_variance"),
    "open_misconceptions_and_hypotheses": ("open_misconceptions", "open_hypotheses"),
    "elapsed_minutes": ("elapsed_seconds",),
    "active_minutes": ("active_seconds",),
    "origin": ("origin",),
    "objective_trace": ("objective_trace_id",),
    "experiment_assignments": ("experiment_assignment_ids",),
    "outcome": ("outcome_attempt_id", "recheck_attempt_id", "gap_result", "lo_undo_state"),
}


def _scores(pairs: list[tuple[float, float]]) -> dict[str, Any]:
    if not pairs:
        return {"n": 0, "brier": None, "log_loss": None, "mean_p": None, "rate": None}
    eps = 1e-12
    brier = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
    loss = -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y in pairs) / len(pairs)
    return {"n": len(pairs), "brier": round(brier, 6), "log_loss": round(loss, 6),
            "mean_p": round(sum(p for p, _ in pairs) / len(pairs), 6), "rate": round(sum(y for _, y in pairs) / len(pairs), 6)}


def _score_words(scores: Mapping[str, Any]) -> str:
    if not scores["n"]:
        return "none scored yet"
    return (f"{scores['n']} scored, mean forecast {scores['mean_p']:.2f} against {scores['rate']:.2f} right, "
            f"Brier {scores['brier']:.3f}, log loss {scores['log_loss']:.3f} nats")


def _has(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() \
        is not None


def _lessons_part(vault: Any, repository: Any, connection: Any, today: str) -> tuple[dict[str, Any], list[str]]:
    from learnloop.db.stores import lessons as store
    from learnloop.teacher import episodes as E

    rows = connection.execute("SELECT id, opened_at, closed_at, close_reason FROM lessons ORDER BY opened_at, id") \
        .fetchall() if _has(connection, "lessons") else []
    by_reason = Counter(str(row[3]) for row in rows if row[2] is not None)
    active = elapsed = 0.0
    measured = unmeasured = missing = 0
    for lesson_id, opened_at, closed_at, _reason in rows:
        if closed_at is None:
            continue
        minutes = E.lesson_minutes(repository, {"id": lesson_id, "opened_at": opened_at, "closed_at": closed_at})
        elapsed += float(minutes["elapsed_minutes"] or 0.0)
        missing += int(minutes["missing_intervals"] or 0)
        if minutes["active_minutes"] is None:
            unmeasured += 1
        else:
            measured += 1
            active += float(minutes["active_minutes"])
    committed = due = answered = 0
    results: Counter[str] = Counter()
    for lesson_id, _opened, closed_at, _reason in rows:
        if closed_at is None:
            continue
        receipt = store.receipt(connection, lesson_id) or {}
        for entry in receipt.get("delayed_checks") or []:
            if not entry.get("commitment_id"):
                continue
            committed += 1
            if str(entry.get("due") or "9999") <= today:
                due += 1
            item = entry.get("item_id")
            row = connection.execute(
                "SELECT correctness FROM practice_attempts WHERE practice_item_id = ? AND created_at > ? "
                "AND correctness IS NOT NULL ORDER BY created_at, id LIMIT 1", (item, closed_at)).fetchone() \
                if item else None
            if row is not None:
                answered += 1
                results["right" if row[0] >= 1.0 else ("wrong" if row[0] <= 0.0 else "partly right")] += 1
    part = {"opened": len(rows), "open": sum(1 for row in rows if row[2] is None), "closed_by_reason": dict(by_reason),
            "active_minutes": round(active, 3), "lessons_with_intervals": measured,
            "lessons_without_intervals": unmeasured, "elapsed_minutes": round(elapsed, 3),
            "missing_intervals": missing,
            "delayed_checks": {"committed": committed, "due": due, "answered": answered, "results": dict(results)}}
    reasons = ", ".join(f"{reason} {count}" for reason, count in sorted(by_reason.items())) or "none closed"
    lines = [
        f"lessons: {part['opened']} opened, {part['open']} open; closed: {reasons}",
        # Two clocks, never one number: active is the screen's foreground time, elapsed the wall clock.
        f"lesson minutes: active {active:.1f} (over {measured} lesson(s) with intervals; {unmeasured} with none, "
        f"active unknown) · elapsed {elapsed:.1f} · {missing} interval(s) missing",
        f"delayed checks: {committed} committed, {due} due, {answered} answered"
        + (" (" + ", ".join(f"{k} {v}" for k, v in sorted(results.items())) + ")" if results else ""),
    ]
    return part, lines


def _episodes_part(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    from learnloop.teacher import episodes as E

    kinds = Counter(str(row["kind"]) for row in episodes)
    probes = [row for row in episodes if row["kind"] == "probe"]
    detours = Counter(str(row["repair_class"]) for row in episodes if row["kind"] == "detour")
    gaps = Counter(f"{row['repair_class'] or 'unknown'}:{row['gap_result'] or 'pending'}"
                   for row in episodes if row["kind"] == "gap")
    probe_part = {"generated": sum(1 for row in probes if row["generated_item_id"]),
                  "refused": sum(1 for row in probes if row["close_reason"] == "refused"),
                  "retired": sum(1 for row in probes if row["close_reason"] == "retired"),
                  "answered": sum(1 for row in probes if row["outcome_attempt_id"])}
    part = {"by_kind": {kind: kinds.get(kind, 0) for kind in E.KINDS}, "probes": probe_part,
            "detours_by_repair": dict(detours), "unlogged_detours": detours.get(E.UNLOGGED, 0),
            "gaps": dict(gaps)}
    lines = [
        "episodes: " + ", ".join(f"{kind} {kinds.get(kind, 0)}" for kind in E.KINDS),
        f"probes: {probe_part['generated']} generated, {probe_part['refused']} refused, {probe_part['retired']} "
        f"retired unused, {probe_part['answered']} answered",
        "detours by repair: " + (", ".join(f"{k} {v}" for k, v in sorted(detours.items())) or "none")
        + f" ({part['unlogged_detours']} unlogged)",
        "gaps: " + (", ".join(f"{k} {v}" for k, v in sorted(gaps.items())) or "none"),
    ]
    return part, lines


def _coverage_part(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    total = len(episodes)

    def has(row: Mapping[str, Any], columns: tuple[str, ...]) -> bool:
        return any(row.get(column) not in (None, [], {}) for column in columns)

    counts = {name: sum(1 for row in episodes if has(row, columns)) for name, columns in COVERAGE_FIELDS.items()}
    line = (f"coverage of item 5's fields over {total} episode(s): "
            + ", ".join(f"{name} {count}/{total}" for name, count in counts.items()))
    return {"episodes": total, "fields": counts}, [line]


def _forecasts_part(vault: Any, connection: Any, today: str) -> tuple[dict[str, Any], list[str]]:
    """``lesson_probe_correct`` against the probes' grades; ``lesson_node_held`` against natural outcomes (the first
    qualifying cold outcome: self-selected) and, apart, against RO5's randomized checks (each with its ``r``)."""

    from learnloop.evsi_calibration.forecast_report import resolved_receipts
    from learnloop.scheduling.forecast_receipts import LESSON_NODE_HELD

    rows = [(receipt, resolution) for receipt, resolution in resolved_receipts(vault)
            if receipt["kind"] in (LESSON_NODE_HELD, "lesson_probe_correct")]
    natural: list[tuple[float, float]] = []
    probes: list[tuple[float, float]] = []
    held = [receipt for receipt, _ in rows if receipt["kind"] == LESSON_NODE_HELD]
    for receipt, resolution in rows:
        if resolution.get("state") != "resolved" or receipt.get("p") is None:
            continue
        pair = (float(receipt["p"]), 1.0 if resolution.get("emission") == "success" else 0.0)
        (natural if receipt["kind"] == LESSON_NODE_HELD else probes).append(pair)
    randomized: list[tuple[float, float]] = []
    rates: list[float] = []
    if held and _has(connection, "policy_experiment_assignments"):
        from learnloop.router_objective import checks as RC

        # As of the end of ``today`` (RO5's closure: a read never moves with later activity).
        completed = [slot for slot in RC.resolve(connection, through=today) if slot.status == "completed"
                     and slot.attempt_id
                     and slot.outcome is not None]
        times = {}
        for slot in completed:
            row = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?", (slot.attempt_id,)).fetchone()
            times[slot.assignment_id] = None if row is None else str(row[0])
        for receipt in held:
            lo = (receipt.get("inputs") or {}).get("learning_object_id") or receipt.get("learning_object_id")
            later = sorted((times[slot.assignment_id], slot) for slot in completed
                           if slot.topic == lo and times.get(slot.assignment_id)
                           and times[slot.assignment_id] > str(receipt["created_at"]))
            if later and receipt.get("p") is not None:
                slot = later[0][1]
                randomized.append((float(receipt["p"]), 1.0 if float(slot.outcome) >= 1.0 else 0.0))
                rates.append(float(slot.r))
    part = {"lesson_probe_correct": _scores(probes),
            "lesson_node_held": {"receipts": len(held), "natural": {**_scores(natural), "label": "self-selected"},
                                 "randomized": {**_scores(randomized), "label": "randomized", "r": rates}}}
    r_words = (f", r {', '.join(f'{r:.3f}' for r in rates)}" if rates else "")
    lines = [
        f"probe forecasts (lesson_probe_correct) against their grades: {_score_words(part['lesson_probe_correct'])}",
        f"placement forecasts (lesson_node_held, {len(held)} receipt(s)) against natural outcomes (self-selected): "
        f"{_score_words(part['lesson_node_held']['natural'])}",
        f"placement forecasts against RO5's randomized checks (randomized{r_words}): "
        f"{_score_words(part['lesson_node_held']['randomized'])}",
    ]
    return part, lines


def lesson_report(vault: Any, repository: Any, *, today: str | None = None) -> dict[str, Any]:
    """TE2-log's report lines (spec §11.10), read-only: lessons (opened, closed by reason, active and elapsed minutes
    apart with the intervals missing, delayed checks committed, due, answered and their results), episodes (by kind;
    probes generated, refused, retired and answered; detours by repair with the unlogged ones; gaps by kind and
    outcome), forecasts (probe and placement forecasts scored, natural and randomized apart, each labelled) and the
    coverage of item 5's fields. Nothing in it decides anything."""

    from learnloop.db.stores import lessons as store

    with repository.connection() as connection:
        day = today or date.today().isoformat()
        lessons, lesson_lines = _lessons_part(vault, repository, connection, day)
        episodes = store.episodes(connection) if store.episode_tables_present(connection) else []
        forecasts, forecast_lines = _forecasts_part(vault, connection, day)
    episode_part, episode_lines = _episodes_part(episodes)
    coverage, coverage_lines = _coverage_part(episodes)
    return {"lessons": lessons, "episodes": episode_part, "forecasts": forecasts, "coverage": coverage,
            "lines": [*lesson_lines, *episode_lines, *forecast_lines, *coverage_lines]}


__all__ = ["COVERAGE_FIELDS", "lesson_report", "report"]

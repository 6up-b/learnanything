"""`learnloop eval` — calibration report over logged decisions.

The Adaptive Elicitation framing: the system's health metric is whether its
*predictions of future answers* are calibrated (Brier / ECE / log-loss), not
whether internal scores look plausible. Strictly read-only; every section
consumes rows the live path already logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.numeric import percentiles
from learnloop.services.fsrs import MemoryState, apply_review, forgetting_curve
from learnloop.services.fitted_params import resolve_fsrs_weights
from learnloop.vault.models import LoadedVault

from math import log

_CLIP = 1e-6


# ── metric primitives ────────────────────────────────────────────────────────


def brier_score(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    return sum((predicted - actual) ** 2 for predicted, actual in pairs) / len(pairs)


def log_loss(pairs: list[tuple[float, float]], *, clip: float = _CLIP) -> float:
    """Cross-entropy with soft targets in [0, 1]."""

    if not pairs:
        return 0.0
    total = 0.0
    for predicted, actual in pairs:
        clipped = min(max(predicted, clip), 1.0 - clip)
        total += -(actual * log(clipped) + (1.0 - actual) * log(1.0 - clipped))
    return total / len(pairs)


@dataclass(frozen=True)
class CalibrationBin:
    lo: float
    hi: float
    count: int
    mean_predicted: float
    mean_realized: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "lo": self.lo,
            "hi": self.hi,
            "count": self.count,
            "mean_predicted": self.mean_predicted,
            "mean_realized": self.mean_realized,
        }


def ece_equal_width(pairs: list[tuple[float, float]], *, bins: int = 10) -> tuple[float, list[CalibrationBin]]:
    if not pairs or bins <= 0:
        return 0.0, []
    buckets: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for predicted, actual in pairs:
        index = min(int(predicted * bins), bins - 1)
        buckets[index].append((predicted, actual))
    table: list[CalibrationBin] = []
    ece = 0.0
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        mean_predicted = sum(p for p, _ in bucket) / len(bucket)
        mean_realized = sum(a for _, a in bucket) / len(bucket)
        table.append(
            CalibrationBin(index / bins, (index + 1) / bins, len(bucket), mean_predicted, mean_realized)
        )
        ece += (len(bucket) / len(pairs)) * abs(mean_predicted - mean_realized)
    return ece, table


# ── report sections ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EvalReport:
    predictions: dict[str, Any] | None
    gates: dict[str, Any] | None
    retention: dict[str, Any] | None
    propensity: dict[str, Any] | None
    coverage: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "predictions": self.predictions,
            "gates": self.gates,
            "retention": self.retention,
            "propensity": self.propensity,
            "coverage": self.coverage,
        }

    def format_text(self) -> str:
        lines: list[str] = []
        if self.predictions is not None:
            lines.extend(_format_predictions(self.predictions))
        if self.coverage is not None:
            lines.extend(_format_coverage(self.coverage))
        if self.gates is not None:
            lines.extend(_format_gates(self.gates))
        if self.retention is not None:
            lines.extend(_format_retention(self.retention))
        if self.propensity is not None:
            lines.extend(_format_propensity(self.propensity))
        return "\n".join(lines) if lines else "No sections selected."


def build_eval_report(
    vault: LoadedVault,
    repository: Repository,
    *,
    sections: set[str],
    bins: int = 10,
) -> EvalReport:
    return EvalReport(
        predictions=_predictions_section(repository, bins=bins) if "predictions" in sections else None,
        gates=_gates_section(vault, repository) if "gates" in sections else None,
        retention=_retention_section(vault, repository, bins=bins) if "retention" in sections else None,
        propensity=_propensity_section(repository) if "propensity" in sections else None,
        coverage=_coverage_section(repository) if "coverage" in sections else None,
    )


def _predictions_section(repository: Repository, *, bins: int) -> dict[str, Any]:
    rows = repository.chosen_candidate_outcomes()
    pairs = [(float(row["predicted_correctness"]), float(row["correctness"])) for row in rows]
    ece, table = ece_equal_width(pairs, bins=bins)

    by_mode: dict[str, list[tuple[float, float]]] = {}
    for row, pair in zip(rows, pairs):
        by_mode.setdefault(str(row["selected_mode"] or "unknown"), []).append(pair)

    deciles: list[dict[str, Any]] = []
    if len(pairs) >= 10:
        chunk = len(pairs) // 10
        for index in range(10):
            start = index * chunk
            end = start + chunk if index < 9 else len(pairs)
            slice_pairs = pairs[start:end]
            deciles.append({"decile": index + 1, "count": len(slice_pairs), "brier": brier_score(slice_pairs)})

    return {
        "count": len(pairs),
        "brier": brier_score(pairs),
        "log_loss": log_loss(pairs),
        "ece": ece,
        "reliability": [bin.as_dict() for bin in table],
        "by_intent": {
            mode: {"count": len(mode_pairs), "brier": brier_score(mode_pairs)}
            for mode, mode_pairs in sorted(by_mode.items())
        },
        "by_attempt_decile": deciles,
    }


_COVERAGE_Z80 = 1.2815515655446004  # central 80% of the latent Gaussian
_COLD_ATTEMPT_COUNT = 3  # attempts 1..3 on an LO count as the cold regime


def _coverage_section(repository: Repository) -> dict[str, Any]:
    """Prospective 80% predictive-interval coverage, sliced cold vs warm.

    Each attempt_surprise row logged sigma(a(mu_z ± z80·sigma_z − b)) implicitly;
    the observed score fraction either lands inside that interval or not. The
    cold/warm split (first N attempts per LO vs later) is the slice every prior-
    width and observation-weight experiment needs to read.
    """

    from math import exp

    def sig(value: float) -> float:
        return 1.0 / (1.0 + exp(-value))

    slices: dict[str, list[dict[str, float]]] = {"cold": [], "warm": []}
    seen_per_lo: dict[str, int] = {}
    for row in repository.prediction_interval_rows():
        dist = row["predicted_score_dist"]
        if not isinstance(dist, dict):
            continue
        try:
            a = float(dist["a"])
            b = float(dist["b"])
            mu = float(dist["mu_z"])
            sigma = float(dist["sigma_z"])
            predicted = float(dist.get("expected_correctness", sig(a * (mu - b))))
        except (KeyError, TypeError, ValueError):
            continue
        lo_id = str(row["learning_object_id"])
        ordinal = seen_per_lo.get(lo_id, 0) + 1
        seen_per_lo[lo_id] = ordinal
        p_lo = sig(a * (mu - _COVERAGE_Z80 * sigma - b))
        p_hi = sig(a * (mu + _COVERAGE_Z80 * sigma - b))
        observed = float(row["correctness"])
        regime = "cold" if ordinal <= _COLD_ATTEMPT_COUNT else "warm"
        slices[regime].append(
            {
                "covered": 1.0 if p_lo <= observed <= p_hi else 0.0,
                "width": p_hi - p_lo,
                "predicted": predicted,
                "observed": observed,
            }
        )

    def summarize(rows: list[dict[str, float]]) -> dict[str, Any]:
        if not rows:
            return {"count": 0}
        pairs = [(entry["predicted"], entry["observed"]) for entry in rows]
        return {
            "count": len(rows),
            "interval_coverage": sum(entry["covered"] for entry in rows) / len(rows),
            "mean_interval_width": sum(entry["width"] for entry in rows) / len(rows),
            "brier": brier_score(pairs),
            "log_loss": log_loss(pairs),
        }

    combined = slices["cold"] + slices["warm"]
    return {
        "nominal_coverage": 0.8,
        "cold_attempt_count": _COLD_ATTEMPT_COUNT,
        "overall": summarize(combined),
        "cold": summarize(slices["cold"]),
        "warm": summarize(slices["warm"]),
    }


def _gates_section(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    followup = vault.config.scheduler.followup
    rows = repository.gate_training_rows()
    outcome_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    false_negative_reasons: dict[str, int] = {}
    auto_fired = 0
    manual = 0
    false_negatives = 0
    signals: dict[str, dict[str, list[float]]] = {
        "bayesian_surprise": {"fired": [], "silent": []},
        "max_error_severity": {"fired": [], "silent": []},
        "grader_confidence": {"fired": [], "silent": []},
    }
    for row in rows:
        gate = row.get("gate_diagnostics")
        if not isinstance(gate, dict):
            continue
        outcome = str(gate.get("outcome"))
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        reason = str(gate.get("decisive_reason"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if gate.get("would_auto_fire"):
            auto_fired += 1
        if gate.get("manual_override"):
            manual += 1
            if gate.get("would_auto_fire") is False:
                false_negatives += 1
                false_negative_reasons[reason] = false_negative_reasons.get(reason, 0) + 1
        bucket = "fired" if outcome in ("queued", "need_recorded") else "silent"
        for name in ("bayesian_surprise", "max_error_severity", "grader_confidence"):
            value = gate.get(name)
            if isinstance(value, (int, float)):
                signals[name][bucket].append(float(value))

    thresholds = {
        "bayesian_surprise": followup.tau_followup_nats,
        "max_error_severity": followup.tau_severe_error,
        "grader_confidence": followup.gamma_min,
    }
    signal_tables: dict[str, Any] = {}
    for name, split in signals.items():
        threshold = thresholds[name]
        all_values = split["fired"] + split["silent"]
        signal_tables[name] = {
            "threshold": threshold,
            "fraction_above_threshold": (
                sum(1 for value in all_values if value >= threshold) / len(all_values)
                if all_values
                else None
            ),
            "fired_percentiles": {str(q): v for q, v in percentiles(split["fired"]).items()},
            "silent_percentiles": {str(q): v for q, v in percentiles(split["silent"]).items()},
        }

    return {
        "count": sum(outcome_counts.values()),
        "outcomes": dict(sorted(outcome_counts.items())),
        "decisive_reasons": dict(sorted(reason_counts.items())),
        "would_auto_fire": auto_fired,
        "manual_overrides": manual,
        "gate_false_negatives": false_negatives,
        "gate_false_negative_rate": (false_negatives / manual) if manual else None,
        "false_negative_decisive_reasons": dict(sorted(false_negative_reasons.items())),
        "signals": signal_tables,
    }


def _retention_section(vault: LoadedVault, repository: Repository, *, bins: int) -> dict[str, Any]:
    from learnloop.services.attempts import fsrs_rating_for_attempt

    weights = resolve_fsrs_weights(repository)
    # Replay each item's graded attempts to reconstruct stability *after* each
    # attempt (not snapshotted historically).
    stability_after: dict[str, float] = {}
    state_by_item: dict[str, MemoryState] = {}
    last_seen: dict[str, Any] = {}
    skipped = 0
    for row in repository.item_attempt_history():
        item = vault.practice_items.get(row["practice_item_id"])
        observed_at = parse_utc(row["created_at"])
        if item is None or observed_at is None:
            skipped += 1
            continue
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        rating = fsrs_rating_for_attempt(item, int(row["rubric_score"]), max_points, int(row["hints_used"] or 0))
        previous_at = last_seen.get(item.id)
        elapsed = max(0.0, (observed_at - previous_at).total_seconds() / 86400) if previous_at else 0.0
        state = apply_review(state_by_item.get(item.id), rating, elapsed, weights)
        state_by_item[item.id] = state
        last_seen[item.id] = observed_at
        stability_after[row["id"]] = state.stability

    # Cross-check: reconstructed final stability vs the stored live state.
    mismatches = 0
    checked = 0
    for item_id, state in state_by_item.items():
        stored = repository.practice_item_state(item_id)
        if stored is None or stored.stability is None:
            continue
        checked += 1
        if abs(stored.stability - state.stability) > 1e-6:
            mismatches += 1

    bands = [(0.0, 1.0, "<1d"), (1.0, 3.0, "1-3d"), (3.0, 7.0, "3-7d"), (7.0, float("inf"), ">7d")]
    pairs: list[tuple[float, float]] = []
    by_band: dict[str, list[tuple[float, float]]] = {label: [] for _, _, label in bands}
    unmatched = 0
    for label_row in repository.retention_label_rows():
        stability = stability_after.get(label_row["source_attempt_id"])
        if stability is None:
            unmatched += 1
            continue
        elapsed_days = float(label_row["elapsed_seconds"] or 0.0) / 86400
        predicted = forgetting_curve(stability, elapsed_days, weights)
        actual = float(label_row["label_value"])
        pairs.append((predicted, actual))
        for lo, hi, band_label in bands:
            if lo <= elapsed_days < hi:
                by_band[band_label].append((predicted, actual))
                break

    ece, table = ece_equal_width(pairs, bins=bins)
    return {
        "count": len(pairs),
        "unmatched_labels": unmatched,
        "reconstruction": {
            "items_checked": checked,
            "stability_mismatches": mismatches,
            "skipped_attempts": skipped,
            "note": "stability reconstructed by replaying attempts through FSRS; mismatches indicate drift vs live state",
        },
        "brier": brier_score(pairs),
        "log_loss": log_loss(pairs),
        "ece": ece,
        "reliability": [bin.as_dict() for bin in table],
        "by_elapsed_band": {
            label: {"count": len(band_pairs), "brier": brier_score(band_pairs)}
            for label, band_pairs in by_band.items()
        },
    }


def _propensity_section(repository: Repository) -> dict[str, Any]:
    rows = repository.candidate_propensity_rows()
    slates = {row["slate_id"] for row in rows}
    chosen = [row for row in rows if row["chosen_attempt_id"] is not None]
    propensities = [
        float(row["selection_propensity"]) for row in chosen if row["selection_propensity"] is not None
    ]
    null_count = sum(1 for row in chosen if row["selection_propensity"] is None)
    near_one = sum(1 for value in propensities if value >= 0.999)
    exploration = sum(1 for row in chosen if row["exploration_flag"])

    histogram = [0] * 10
    for value in propensities:
        histogram[min(int(value * 10), 9)] += 1

    degenerate = bool(chosen) and (near_one + null_count) / len(chosen) > 0.90
    return {
        "slates": len(slates),
        "chosen_candidates": len(chosen),
        "exploration_fraction": (exploration / len(chosen)) if chosen else None,
        "null_propensities": null_count,
        "propensities_near_one": near_one,
        "histogram": histogram,
        "off_policy_readiness": "DEGENERATE" if degenerate else ("OK" if chosen else "NO DATA"),
    }


# ── text formatting ──────────────────────────────────────────────────────────


def _format_predictions(section: dict[str, Any]) -> list[str]:
    lines = ["── Predictions (predicted_correctness vs realized) ──"]
    if not section["count"]:
        return [*lines, "  no data", ""]
    lines.append(
        f"  n={section['count']}  brier={section['brier']:.4f}  "
        f"log-loss={section['log_loss']:.4f}  ece={section['ece']:.4f}"
    )
    lines.append("  bin        n   predicted  realized   gap")
    for bin_row in section["reliability"]:
        gap = bin_row["mean_realized"] - bin_row["mean_predicted"]
        lines.append(
            f"  {bin_row['lo']:.1f}-{bin_row['hi']:.1f}  {bin_row['count']:5d}   "
            f"{bin_row['mean_predicted']:.3f}      {bin_row['mean_realized']:.3f}     {gap:+.3f}"
        )
    for mode, stats in section["by_intent"].items():
        lines.append(f"  intent {mode}: n={stats['count']} brier={stats['brier']:.4f}")
    for decile in section["by_attempt_decile"]:
        lines.append(f"  decile {decile['decile']:2d}: n={decile['count']} brier={decile['brier']:.4f}")
    lines.append("")
    return lines


def _format_coverage(section: dict[str, Any]) -> list[str]:
    lines = ["── Predictive-interval coverage (80% nominal, cold vs warm) ──"]
    if not section["overall"].get("count"):
        return [*lines, "  no data", ""]
    for label in ("overall", "cold", "warm"):
        stats = section[label]
        if not stats.get("count"):
            lines.append(f"  {label}: no data")
            continue
        lines.append(
            f"  {label}: n={stats['count']}  coverage={stats['interval_coverage']:.0%}"
            f"  width={stats['mean_interval_width']:.3f}  brier={stats['brier']:.4f}"
            f"  log-loss={stats['log_loss']:.4f}"
        )
    lines.append(f"  (cold = first {section['cold_attempt_count']} attempts per LO)")
    lines.append("")
    return lines


def _format_gates(section: dict[str, Any]) -> list[str]:
    lines = ["── Follow-up gate ──"]
    if not section["count"]:
        return [*lines, "  no data", ""]
    lines.append(f"  evaluations={section['count']}  would_auto_fire={section['would_auto_fire']}")
    lines.append(f"  outcomes: {section['outcomes']}")
    lines.append(f"  decisive reasons: {section['decisive_reasons']}")
    rate = section["gate_false_negative_rate"]
    lines.append(
        f"  manual overrides={section['manual_overrides']}  "
        f"gate false negatives={section['gate_false_negatives']}"
        + (f" ({rate:.0%} of overrides)" if rate is not None else "")
    )
    if section["false_negative_decisive_reasons"]:
        lines.append(f"  false-negative reasons: {section['false_negative_decisive_reasons']}")
    for name, table in section["signals"].items():
        lines.append(f"  {name} (threshold {table['threshold']}):")
        fraction = table["fraction_above_threshold"]
        if fraction is not None:
            lines.append(f"    above threshold: {fraction:.0%}")
        for split in ("fired", "silent"):
            values = table[f"{split}_percentiles"]
            if values:
                rendered = "  ".join(f"p{int(float(q) * 100)}={value:.3f}" for q, value in values.items())
                lines.append(f"    {split}: {rendered}")
    lines.append("")
    return lines


def _format_retention(section: dict[str, Any]) -> list[str]:
    lines = ["── Retention (FSRS predicted vs same_item_retention labels) ──"]
    reconstruction = section["reconstruction"]
    if reconstruction["stability_mismatches"]:
        lines.append(
            f"  CAVEAT: {reconstruction['stability_mismatches']}/{reconstruction['items_checked']} "
            "items' reconstructed stability differs from live state (fitted-weight or content drift)"
        )
    if not section["count"]:
        return [*lines, "  no matched labels", ""]
    lines.append(
        f"  n={section['count']} (unmatched {section['unmatched_labels']})  "
        f"brier={section['brier']:.4f}  log-loss={section['log_loss']:.4f}  ece={section['ece']:.4f}"
    )
    for band, stats in section["by_elapsed_band"].items():
        if stats["count"]:
            lines.append(f"  {band}: n={stats['count']} brier={stats['brier']:.4f}")
    lines.append("")
    return lines


def _format_propensity(section: dict[str, Any]) -> list[str]:
    lines = ["── Selection propensities (off-policy readiness) ──"]
    if not section["chosen_candidates"]:
        return [*lines, "  no data", f"  off-policy readiness: {section['off_policy_readiness']}", ""]
    fraction = section["exploration_fraction"]
    lines.append(
        f"  slates={section['slates']}  chosen={section['chosen_candidates']}  "
        f"exploration={fraction:.1%}" if fraction is not None else "  n/a"
    )
    lines.append(
        f"  null propensities={section['null_propensities']}  near-1.0={section['propensities_near_one']}"
    )
    lines.append(f"  histogram (0.0→1.0): {section['histogram']}")
    lines.append(f"  off-policy readiness: {section['off_policy_readiness']}")
    lines.append("")
    return lines

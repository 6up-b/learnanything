"""EVSI calibration Part B: record the forecast every live VOI decision runs on.

A value-of-information decision (choose this check, or stop) is a forecast:
"this check's answer will be distributed like *this*, it will move belief by
*this* many nats, it is worth *this* many minutes, and with probability *p* it
will change what we do". Each decision site records that forecast here, as a
``voi_forecasts`` receipt, beside the decision and without changing it. The
calibration report (``learnloop evsi calibration``) later joins the realized
answer and, when it becomes known, the truth.

The forecast body is self-contained so the join needs nothing but the
realized emission: the chosen check's mean-member likelihood ``P(e | h)``,
the belief it was chosen under, the action recommended after each emission
(``action_by_emission``) and the action before it. Every number the decision
used is listed in ``parameters`` with a coarse **provenance** (``measured``,
``population_prior``, ``heuristic``, ``structural``) and its fine source
(the decision-value spec §4.1 vocabulary where one applies).

Never raises into serving: :func:`record_forecast` swallows and logs every
failure, writes nothing on a read-only repository, and is off when
``evsi.forecast_logging`` is false.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.stores import voi_forecasts as store
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV

logger = logging.getLogger(__name__)

FORECAST_VERSION = "voi_forecast_v1"

#: Decision sites that record forecasts. A successor that puts another
#: decision on value of information (teach-back, project probes, ...) adds its
#: site here; the table itself does not constrain the vocabulary.
VOI_SITES = (
    "probe_selection",
    "probe_robust_selection",
    "followup_selection",
    "causal_shadow_selection",
    "staged_diagnostic_selection",
)

PROVENANCES = ("measured", "population_prior", "heuristic", "structural")

#: Duration-estimate sources -> coarse provenance.
SOURCE_PROVENANCE = {
    "logged_attempt_durations": "measured",
    "pooled_attempt_durations": "measured",
    "pooled_empirical": "measured",
    "empirical_family": "measured",
    "empirical_repair_class": "measured",
    "learned_cold_outcome": "measured",
    "population_prior": "population_prior",
    "eedi_population_prior": "population_prior",
    "shrunk_personal": "measured",
    "authored_prior": "heuristic",
    "heuristic_default": "heuristic",
    "override": "heuristic",
    "structural_bound": "structural",
}

#: Candidates kept on a forecast body (the chosen one is always kept).
MAX_RECORDED_CANDIDATES = 10


def provenance_of(source: str | None) -> str:
    return SOURCE_PROVENANCE.get(str(source or ""), "heuristic")


def parameter(
    name: str,
    value: Any,
    provenance: str,
    *,
    source: str | None = None,
    sample_count: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if provenance not in PROVENANCES:
        raise ValueError(f"unknown provenance {provenance!r}")
    entry: dict[str, Any] = {"name": name, "value": value, "provenance": provenance}
    if source is not None:
        entry["source"] = source
    if sample_count is not None:
        entry["sample_count"] = int(sample_count)
    if note is not None:
        entry["note"] = note
    return entry


# -- forecast arithmetic (bookkeeping over the decision's own inputs) -----------------------------


def _normalized(belief: Mapping[str, float], labels: Sequence[str]) -> dict[str, float]:
    weights = {h: max(float(belief.get(h, 0.0)), 0.0) for h in labels}
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {h: w / total for h, w in weights.items()}


def entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * math.log(p) for p in distribution.values() if p > 0)


def predictive(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> dict[str, float]:
    labels = [h for h in belief if h in likelihood]
    weights = _normalized(belief, labels)
    out: dict[str, float] = {}
    for h, w in weights.items():
        for e, p in likelihood[h].items():
            out[e] = out.get(e, 0.0) + w * float(p)
    return out


def posterior(
    likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float], emission: str
) -> dict[str, float]:
    labels = [h for h in belief if h in likelihood]
    weights = _normalized(belief, labels)
    raw = {h: w * float(likelihood[h].get(emission, 0.0)) for h, w in weights.items()}
    total = sum(raw.values())
    if total <= 0:
        return dict(weights)
    return {h: v / total for h, v in raw.items()}


def expected_information_gain(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> float:
    """Hypothesis EIG in nats: prior entropy minus expected posterior entropy."""

    labels = [h for h in belief if h in likelihood]
    weights = _normalized(belief, labels)
    if len(weights) <= 1:
        return 0.0
    expected = 0.0
    for e, p in predictive(likelihood, weights).items():
        if p > 0:
            expected += p * entropy(posterior(likelihood, weights, e))
    return max(entropy(weights) - expected, 0.0)


def forecast_block(
    likelihood: Mapping[str, Mapping[str, float]],
    belief: Mapping[str, float],
    *,
    action_of: Callable[[Mapping[str, float]], str | None],
    action_proxy: str,
) -> dict[str, Any]:
    """Predicted answers, EIG, action after each answer and P(action change)."""

    labels = sorted(h for h in belief if h in likelihood)
    prior = _normalized(belief, labels)
    predicted = predictive(likelihood, prior)
    current = action_of(prior)
    by_emission: dict[str, str | None] = {}
    change = 0.0
    for e, p in sorted(predicted.items()):
        after = action_of(posterior(likelihood, prior, e))
        by_emission[e] = after
        if p > 0 and after != current:
            change += p
    return {
        "emission_alphabet": sorted(predicted),
        "predicted_outcomes": {e: round(p, 8) for e, p in sorted(predicted.items())},
        "prior": {h: round(p, 8) for h, p in sorted(prior.items())},
        "likelihood": {h: {e: round(float(p), 8) for e, p in sorted(likelihood[h].items())} for h in labels},
        "current_action": current,
        "action_by_emission": by_emission,
        "action_proxy": action_proxy,
        "eig_nats": round(expected_information_gain(likelihood, prior), 8),
        "p_action_change": round(min(max(change, 0.0), 1.0), 8),
    }


def loss_summary(loss_table: AL.LossTable) -> dict[str, Any]:
    return {
        "table_hash": loss_table.table_hash,
        "calibration_label": loss_table.calibration_label,
        "scope": loss_table.scope,
        "version": loss_table.version,
        "effective_action": dict(sorted(loss_table.effective_action.items())),
        "minutes": {
            h: {a: round(loss_table.loss(h, a), 6) for a in loss_table.actions} for h in loss_table.hypotheses
        },
    }


def loss_table_parameters(
    loss_table: AL.LossTable,
    *,
    duration_estimates: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Provenance of every number in a minutes loss table.

    ``duration_estimates`` (the estimator's own ``{action: {minutes, source,
    sample_count}}``) wins over the cell labels: ``build_loss_table`` labels
    every override ``logged_attempt_durations`` whatever its real origin.
    """

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    if duration_estimates:
        for action, estimate in sorted(duration_estimates.items()):
            source = str(estimate.get("source") or "")
            out.append(parameter(
                f"minutes[{action}]", round(float(estimate.get("minutes") or 0.0), 6), provenance_of(source),
                source=source, sample_count=int(estimate.get("sample_count") or 0),
            ))
            seen.add(action)
    unresolved: dict[str, Mapping[str, Any]] = {}
    for cell in loss_table.cells.values():
        d = cell.derivation
        for key in ("wasted", "delay"):
            source = d.get(f"{key}_source")
            action = d.get("wasted_intervention" if key == "wasted" else "effective_intervention")
            if isinstance(source, Mapping) and action and action not in seen:
                label = str(source.get("source") or "")
                out.append(parameter(
                    f"minutes[{action}]", source.get("minutes"), provenance_of(label),
                    source=label, sample_count=int(source.get("sample_count") or 0),
                ))
                seen.add(str(action))
        if "unresolved_minutes" in d and cell.hypothesis not in unresolved:
            unresolved[cell.hypothesis] = {"minutes": d["unresolved_minutes"], **dict(d.get("unresolved_source") or {})}
    for hypothesis, payload in sorted(unresolved.items()):
        out.append(parameter(
            f"unresolved_minutes[{hypothesis}]", payload.get("minutes"),
            str(payload.get("provenance") or "heuristic") if payload.get("provenance") in PROVENANCES else "heuristic",
            source=str(payload.get("source") or "unresolved_cost"),
        ))
    return out


def evsi_parameters(
    *,
    quantile: float = EV.ROBUST_QUANTILE,
    perturbation_delta: float = EV.PERTURBATION_DELTA,
    lambda_time: float = EV.LAMBDA_TIME,
    burden_cost: float = EV.BURDEN_COST,
) -> list[dict[str, Any]]:
    return [
        parameter("evsi.PERTURBATION_DELTA", perturbation_delta, "heuristic", source="registry:heuristic"),
        parameter("robust_composition.ROBUST_QUANTILE", quantile, "heuristic", source="registry:heuristic"),
        parameter("robust_composition.LAMBDA_TIME", lambda_time, "structural", source="minutes numeraire (U-023)"),
        parameter("robust_composition.BURDEN_COST", burden_cost, "heuristic", source="registry:heuristic"),
    ]


def _candidate_forecast(
    candidate: EV.DiagnosticCandidate, loss_table: AL.LossTable
) -> dict[str, Any]:
    return forecast_block(
        candidate.members[0],
        candidate.prior,
        action_of=lambda belief: loss_table.argmin_action(
            {h: belief.get(h, 0.0) for h in loss_table.hypotheses}
        ),
        action_proxy="loss_table_argmin",
    )


def rank_forecast(
    result: EV.RankResult,
    candidates: Sequence[EV.DiagnosticCandidate],
    loss_table: AL.LossTable,
    *,
    chosen_ref: str | None = None,
    committed: bool = False,
) -> dict[str, Any]:
    """The forecast body of one ``rank_feasible`` decision.

    It describes ``chosen_ref`` when given (the candidate actually committed,
    after any near-tie randomization), else the ranking's best. ``forecast_of``
    says which: ``committed`` (administered) or ``nominal_best`` (what the
    ranking preferred; nothing administered, e.g. a stop, an abstention or a
    shadow comparison). When the committed candidate is not the ranking's best,
    the best one's forecast is kept beside it under ``nominal`` so the two stay
    separately identifiable.
    """

    by_ref = {c.ref: c for c in candidates}
    target = chosen_ref if chosen_ref is not None else result.best_ref
    chosen = by_ref.get(target) if target is not None else None
    body: dict[str, Any] = {
        "verdict": result.verdict,
        "reason": result.reason,
        "forecast_of": "committed" if committed and chosen is not None else "nominal_best",
        "chosen_ref": target,
        "nominal_best_ref": result.best_ref,
        "excluded": [dict(entry) for entry in result.excluded],
        "candidates": [
            {"ref": r.ref, "rank_value": round(r.rank_value, 6), "evsi_point": round(r.evsi.point, 6),
             "evsi_lcb": round(r.evsi.lcb, 6), "evsi_ucb": round(r.evsi.ucb, 6),
             "stop_threshold": round(r.stop_threshold, 6), "expected_minutes": r.expected_minutes,
             "action_flipped": r.evsi.action_flipped}
            for r in result.ranked[:MAX_RECORDED_CANDIDATES]
        ],
        "loss": loss_summary(loss_table),
    }
    if chosen is not None and chosen.members:
        body.update(_candidate_forecast(chosen, loss_table))
        body["expected_minutes"] = chosen.expected_minutes
        body["burden_minutes"] = chosen.burden_minutes
        body["prior_basis"] = chosen.prior_basis
    nominal = by_ref.get(result.best_ref) if result.best_ref is not None else None
    if nominal is not None and nominal is not chosen and nominal.members:
        body["nominal"] = {"chosen_ref": nominal.ref, **_candidate_forecast(nominal, loss_table)}
    return body


def forecast_enabled(vault: Any) -> bool:
    """The ``evsi.forecast_logging`` kill switch (on without a vault config)."""

    config = getattr(getattr(vault, "config", None), "evsi", None)
    return bool(getattr(config, "forecast_logging", True)) if config is not None else True


def record_forecast(
    repository: Repository | None,
    *,
    vault: Any = None,
    site: str,
    receipt_key: str,
    verdict: str,
    forecast: Mapping[str, Any],
    parameters: Sequence[Mapping[str, Any]],
    versions: Mapping[str, Any] | None = None,
    candidate_count: int = 0,
    clock: Clock | None = None,
    **columns: Any,
) -> str | None:
    """Append one ``voi_forecasts`` receipt. Never raises; returns its id or None."""

    if repository is None or getattr(repository, "_read_only", False):
        return None
    if vault is not None and not forecast_enabled(vault):
        return None
    try:
        if site not in VOI_SITES:
            raise ValueError(f"unknown VOI site {site!r}")
        payload_versions = {
            "forecast_version": FORECAST_VERSION,
            "evsi_schema_version": EV.EVSI_SCHEMA_VERSION,
            "loss_table_version": AL.LOSS_TABLE_VERSION,
            **dict(versions or {}),
        }
        algorithm_version = None
        if vault is not None:
            algorithm_version = getattr(getattr(getattr(vault, "config", None), "algorithms", None),
                                        "algorithm_version", None)
        values: dict[str, Any] = {
            "eig_nats": _maybe_float(forecast.get("eig_nats")),
            "p_action_change": _maybe_float(forecast.get("p_action_change")),
        }
        values.update(columns)
        with repository.connection() as connection:
            if not store.has_table(connection):
                return None
            forecast_id = store.insert_forecast(
                connection,
                receipt_key=receipt_key,
                site=site,
                verdict=verdict,
                forecast=forecast,
                parameters=list(parameters),
                versions=payload_versions,
                forecast_version=FORECAST_VERSION,
                candidate_count=candidate_count,
                algorithm_version=algorithm_version,
                clock=clock,
                **values,
            )
            connection.commit()
        return forecast_id
    except Exception:  # noqa: BLE001 - logging must never break a decision
        logger.warning("voi forecast not recorded (site=%s, key=%s)", site, receipt_key, exc_info=True)
        return None


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def record_rank_feasible_forecast(
    repository: Repository | None,
    *,
    vault: Any = None,
    site: str,
    receipt_key: str,
    result: EV.RankResult,
    candidates: Sequence[EV.DiagnosticCandidate],
    loss_table: AL.LossTable,
    extra_parameters: Sequence[Mapping[str, Any]] = (),
    duration_estimates: Mapping[str, Mapping[str, Any]] | None = None,
    extra: Mapping[str, Any] | None = None,
    chosen_ref: str | None = None,
    committed: bool = False,
    clock: Clock | None = None,
    **columns: Any,
) -> str | None:
    """Record one ``rank_feasible`` decision (EVSI point/robust, P(change), loss).

    ``chosen_ref``/``committed``: see :func:`rank_forecast`. The EVSI columns
    are the described candidate's.
    """

    if vault is not None and not forecast_enabled(vault):
        return None
    try:
        body = rank_forecast(result, candidates, loss_table, chosen_ref=chosen_ref, committed=committed)
        if extra:
            body["extra"] = dict(extra)
        target = body.get("chosen_ref")
        best = next((r for r in result.ranked if r.ref == target), None) if target is not None else None
        parameters = [
            *evsi_parameters(),
            *loss_table_parameters(loss_table, duration_estimates=duration_estimates),
            *extra_parameters,
        ]
    except Exception:  # noqa: BLE001
        logger.warning("voi forecast not built (site=%s)", site, exc_info=True)
        return None
    return record_forecast(
        repository,
        vault=vault,
        site=site,
        receipt_key=receipt_key,
        verdict=result.verdict,
        forecast=body,
        parameters=parameters,
        versions={"loss_table_hash": loss_table.table_hash},
        candidate_count=len(candidates),
        clock=clock,
        chosen_ref=body.get("chosen_ref"),
        evsi_point_minutes=best.evsi.point if best is not None else None,
        evsi_lcb_minutes=best.evsi.lcb if best is not None else None,
        **columns,
    )

"""The forecast-score replayer (spec_adaptive_difficulty_v1 §8.3; DERIVED ``item_forecast_scores``).

Each ``item_unassisted_success`` receipt is joined to its bound attempt through
the exact chain ``plan_presentations`` -> ``practice_attempts.plan_presentation_id``
(an item-scoped receipt to its revision's first bound presentation). The outcome
is §5.3's event, read exactly as the update reads it: any help, or a reveal
during the presentation, makes it 0; a presentation exposed before it was
served is not scored; a pending presentation (or a skipped or abandoned one) is
right-censored, never a failure. A receipt whose inputs postdate the serve is
invalid for scoring (§8.1).

Splits: field's first-attempt split (the first attempt on a never-seen LO, the
primary score, D17) and the first surface in a never-seen cell.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import math
from collections.abc import Mapping
from typing import Any

from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import replay as RP

SCORE_VERSION = "ad_forecast_scores_v1"
CLIP = (0.005, 0.995)


def log_loss(p: float, y: float) -> float:
    q = min(max(float(p), CLIP[0]), CLIP[1])
    return -(y * math.log(q) + (1.0 - y) * math.log(1.0 - q))


def brier(p: float, y: float) -> float:
    return (float(p) - float(y)) ** 2


@entry(read_only=True)
def score_rows(connection: Any, vault: Any, repository: Any) -> list[dict[str, Any]]:
    """The scores of every item forecast receipt (pure reads; zero model calls)."""

    from learnloop.scheduling.forecast_receipts import valid_for_serve

    from learnloop.adaptive_difficulty.material_view import material_view

    # One material view for the rebuild (A8): a withheld item's presentations, attempts and
    # forecasts are not scored (its receipts read ``pending``, with no bound presentation).
    view = material_view(vault, repository)
    events = RP.load_events(connection, vault, repository, view=view)
    by_presentation = {e.plan_presentation_id: e for e in events.attempts if e.plan_presentation_id}
    served = {pid: str(row["served_at"]) for pid, row in view.presentations(connection).items()}
    first_presentation: dict[str, str] = {}
    pre_exposed: set[str] = set()
    for row in view.rows(connection, "item_serve_inputs", "plan_presentation_id IS NOT NULL", order="served_at, id"):
        first_presentation.setdefault(str(row["content_hash"]), str(row["plan_presentation_id"]))
        if row.get("pre_exposed") == 1:
            pre_exposed.add(str(row["plan_presentation_id"]))
    seen_los: set[str] = set()
    seen_cells: set[tuple[str, str]] = set()
    first_lo: dict[str, bool] = {}
    first_cell: dict[str, bool] = {}
    for event in events.attempts:
        if not event.eligible or event.spec is None:
            continue
        first_lo[event.attempt_id] = event.learning_object_id not in seen_los
        cell = event.spec.cell()
        first_cell[event.attempt_id] = cell not in seen_cells
        seen_los.add(event.learning_object_id)
        seen_cells.add(cell)
    rows: list[dict[str, Any]] = []
    for receipt in view.forecast_receipts(connection, kind="item_unassisted_success"):
        presentation = receipt.get("plan_presentation_id")
        if receipt.get("scope") == "item":
            presentation = first_presentation.get(str(receipt.get("item_content_hash") or ""))
        row: dict[str, Any] = {"receipt_id": str(receipt["id"]), "forecaster": str(receipt["forecaster"]),
                               "practice_item_id": receipt.get("practice_item_id"),
                               "plan_presentation_id": presentation, "p": receipt.get("p"), "detail": {}}
        if receipt.get("status") not in (None, "ok") or receipt.get("p") is None:
            rows.append({**row, "status": "invalid", "detail": {"why": f"status:{receipt.get('status')}"}})
            continue
        if presentation is None or presentation not in served:
            rows.append({**row, "status": "pending", "detail": {"why": "no_bound_presentation"}})
            continue
        if not valid_for_serve(receipt, served[presentation]):
            rows.append({**row, "status": "invalid", "detail": {"why": "inputs_after_serve"}})
            continue
        if presentation in pre_exposed:
            rows.append({**row, "status": "pre_exposed"})
            continue
        attempt = by_presentation.get(presentation)
        if attempt is None:
            rows.append({**row, "status": "pending", "detail": {"why": "no_attempt"}})
            continue
        if not attempt.eligible:
            rows.append({**row, "attempt_id": attempt.attempt_id, "status": "excluded",
                         "detail": {"why": attempt.reason}})
            continue
        outcome = O.unassisted_success(attempt.category)
        p = float(receipt["p"])
        rows.append({
            **row, "attempt_id": attempt.attempt_id, "outcome": outcome, "status": "scored",
            "log_loss": round(log_loss(p, outcome), 12), "brier": round(brier(p, outcome), 12),
            "first_attempt_lo": first_lo.get(attempt.attempt_id), "first_surface_cell": first_cell.get(attempt.attempt_id),
            "capability": attempt.spec.capability if attempt.spec else None,
            "detail": {"category": attempt.category, "warmth": round(attempt.warmth, 12)},
        })
    return rows


def rebuild(vault: Any, repository: Any) -> dict[str, Any]:
    """Clear and rebuild ``item_forecast_scores`` (zero model calls)."""

    from learnloop.adaptive_difficulty.successor import successor_active

    with repository.atomic():
        connection = repository.connection()
        if not store.has_table(connection, store.SCORES):
            return {"written": 0, "skipped": "schema"}
        if not successor_active(vault.config):
            store.clear_derived(connection, (store.SCORES,))
            return {"written": 0, "skipped": "below_successor"}
        rows = score_rows(connection, vault, repository)
        store.clear_derived(connection, (store.SCORES,))
        written = store.write_scores(connection, rows)
    return {"written": written}


# -- router objective RO2: the history forecaster's comparisons (spec_router_objective_v1 §6.4) ------------

#: The history forecaster's report version.
HISTORY_REPORT_VERSION = "ad_history_report_v1"
HISTORY_SUBJECT = "llm_history_v1:H3"
#: The comparators on the same presentations (spec §6.4).
HISTORY_COMPARATORS = ("mastery_ekf", "lo_general+composite", "llm_v3:llm")
#: The calibration slope's seeded prior (a labelled prior, never a fixed weight): a calibrated
#: forecaster (intercept 0, slope 1 of the outcome's log-odds on the forecast's), each with its prior
#: sd. A model and prompt version's slope starts from the population's posterior over every version
#: (the hierarchical prior), never from an older version's slope; ``learnloop ad forecast-audit
#: --mode prior-sweep`` reports how the slopes move with the prior's strength.
SLOPE_PRIOR = {"intercept": (0.0, 1.0), "slope": (1.0, 0.5)}
def _paired(left: Mapping[str, tuple[float, float]], right: Mapping[str, tuple[float, float]]) -> dict[str, Any]:
    """The mean paired log-loss difference ``left - right`` (below zero, ``left`` scores better) on the keys
    both hold (each ``(p, y)``, the same outcome), with AD's anytime-valid confidence sequence on it
    (``monitoring.confidence_sequence`` over each difference's predictable range, §8.3 ``[choe2023]``);
    an interval covering zero is never read as "no difference"."""

    from learnloop.adaptive_difficulty import monitoring as MON

    keys = sorted(set(left) & set(right))
    terms = [MON.log_loss_difference(left[key][0], right[key][0], left[key][1]) for key in keys]
    out: dict[str, Any] = {"n": len(terms), "mean": None, "interval": None}
    if not terms:
        return out
    sequence = MON.confidence_sequence([value for value, _range in terms], ranges=[rng for _value, rng in terms])
    out["mean"] = round(float(sequence["mean"]), 6)
    out["interval"] = [round(float(sequence["lower"]), 6), round(float(sequence["upper"]), 6)]
    return out


def _calibration(points: list[tuple[float, float]]) -> dict[str, Any]:
    if not points:
        return {"n": 0}
    n = len(points)
    return {"n": n, "mean_p": round(sum(p for p, _y in points) / n, 6), "mean_y": round(sum(y for _p, y in points) / n, 6),
            "log_loss": round(sum(log_loss(p, y) for p, y in points) / n, 6),
            "brier": round(sum(brier(p, y) for p, y in points) / n, 6)}


def _logit(p: float) -> float:
    q = min(max(float(p), CLIP[0]), CLIP[1])
    return math.log(q / (1.0 - q))


def _map_fit(points: list[tuple[float, float]], prior: Mapping[str, tuple[float, float]], scale: float = 1.0,
             iterations: int = 50) -> dict[str, Any]:
    """The MAP intercept and slope of ``y ~ Bernoulli(sigmoid(a + b * logit(p)))`` under independent normal
    priors (each sd times ``scale``), by Newton's method, with the Laplace sd of each."""

    (a0, sa), (b0, sb) = prior["intercept"], prior["slope"]
    sa, sb = sa * scale, sb * scale
    a, b = a0, b0
    hessian = [[1.0 / sa ** 2, 0.0], [0.0, 1.0 / sb ** 2]]
    for _ in range(iterations):
        ga, gb = -(a - a0) / sa ** 2, -(b - b0) / sb ** 2
        haa, hab, hbb = 1.0 / sa ** 2, 0.0, 1.0 / sb ** 2
        for p, y in points:
            x = _logit(p)
            mu = 1.0 / (1.0 + math.exp(-(a + b * x)))
            ga += y - mu
            gb += (y - mu) * x
            w = mu * (1.0 - mu)
            haa += w
            hab += w * x
            hbb += w * x * x
        det = haa * hbb - hab * hab
        if det <= 0:
            break
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        hessian = [[haa, hab], [hab, hbb]]
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            break
    det = hessian[0][0] * hessian[1][1] - hessian[0][1] ** 2
    sd_a = math.sqrt(hessian[1][1] / det) if det > 0 else None
    sd_b = math.sqrt(hessian[0][0] / det) if det > 0 else None
    return {"n": len(points), "intercept": round(a, 6), "slope": round(b, 6),
            "intercept_sd": None if sd_a is None else round(sd_a, 6), "slope_sd": None if sd_b is None else round(sd_b, 6)}


def calibration_slopes(points: Mapping[str, list[tuple[float, float]]], *, scale: float = 1.0,
                       prior: Mapping[str, tuple[float, float]] = SLOPE_PRIOR) -> dict[str, Any]:
    """Each model and prompt version's calibration slope under the hierarchical prior: the population
    (every version pooled) is fitted under the seeded prior, and each version under a prior centred at
    the population's posterior with the seeded spread, so a new version starts from the population."""

    pooled = [point for version in points.values() for point in version]
    population = _map_fit(pooled, prior, scale)
    centred = {"intercept": (population["intercept"], prior["intercept"][1]),
               "slope": (population["slope"], prior["slope"][1])}
    return {"prior": {"seeded": {k: list(v) for k, v in prior.items()}, "scale": scale,
                      "label": "seeded: a calibrated forecaster; versions shrink to the population"},
            "population": population,
            "versions": {version: _map_fit(found, centred, scale) for version, found in sorted(points.items())}}


@entry(read_only=True)
def history_report(connection: Any, vault: Any, repository: Any, *, now: str | None = None) -> dict[str, Any]:
    """RO2's comparisons (spec §6.4): ``llm_history_v1:H3`` against ``mastery_ekf``,
    ``lo_general+composite`` and ``llm_v3:llm`` on the same presentations (log loss and calibration on
    field's first-attempt split first, then repeats), delayed cold between the rungs (intention to
    treat) and its calibration (per protocol, conditional on observation), H3 against each lower rung,
    the missing pairs and the skips per rung, and the calibration slopes per model and prompt version.
    Every comparison is exploratory, on whatever has resolved (no minimum sample). Pure reads."""

    from learnloop.adaptive_difficulty import history_resolve as HR
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.db.stores import ad_receipts as receipt_store

    view = material_view(vault, repository)
    scored = [row for row in score_rows(connection, vault, repository) if row.get("status") == "scored"]
    splits = {"first_attempt": lambda row: row.get("first_attempt_lo") is True,
              "repeats": lambda row: row.get("first_attempt_lo") is False}
    losses: dict[str, dict[str, dict[str, tuple[float, float]]]] = {name: {} for name in splits}
    points: dict[str, dict[str, list[tuple[float, float]]]] = {name: {} for name in splits}
    for row in scored:
        for name, member in splits.items():
            if member(row):
                losses[name].setdefault(row["forecaster"], {})[str(row["plan_presentation_id"])] = (
                    float(row["p"]), float(row["outcome"]))
                points[name].setdefault(row["forecaster"], []).append((float(row["p"]), float(row["outcome"])))
    history = sorted({name for split in losses.values() for name in split if name.startswith("llm_history_v1:")})
    comparisons = {split: {comparator: _paired(losses[split].get(HISTORY_SUBJECT, {}), losses[split].get(comparator, {}))
                           for comparator in HISTORY_COMPARATORS} for split in splits}
    ladder = {split: {rung: _paired(losses[split].get(HISTORY_SUBJECT, {}), losses[split].get(rung, {}))
                      for rung in history if rung != HISTORY_SUBJECT} for split in splits}
    calibration = {split: {name: _calibration(found) for name, found in sorted(points[split].items())
                           if name in (HISTORY_SUBJECT, *HISTORY_COMPARATORS) or name in history} for split in splits}
    cold = HR.resolve(connection, vault, repository, now=now)
    itt = {}
    pp_points: dict[str, list[tuple[float, float]]] = {}
    statuses: dict[str, dict[str, int]] = {}
    for row in cold:
        tally = statuses.setdefault(row["binding"], {})
        label = row["status"] if row["status"] != "censored" else f"censored:{row['reason']}"
        tally[label] = tally.get(label, 0) + 1
        if row["status"] != "scored" or row.get("p") is None or row.get("y") is None:
            continue
        if row["binding"] == HR.INTENTION_TO_TREAT:
            itt.setdefault(row["forecaster"], {})[row["plan_presentation_id"]] = (float(row["p"]), float(row["y"]))
        else:
            pp_points.setdefault(row["forecaster"], []).append((float(row["p"]), float(row["y"])))
    delayed = {rung: _paired(itt.get(HISTORY_SUBJECT, {}), itt.get(rung, {}))
               for rung in sorted(itt) if rung != HISTORY_SUBJECT}
    # The slopes per model and prompt version (p_now on the first-attempt split; the receipts' versions).
    versions: dict[str, list[tuple[float, float]]] = {}
    receipts = {str(r["id"]): r for r in view.forecast_receipts(connection, kind="item_unassisted_success")
                if str(r.get("forecaster", "")).startswith("llm_history_v1:")}
    for row in scored:
        receipt = receipts.get(str(row["receipt_id"]))
        if receipt is None:
            continue
        found = receipt.get("versions") or {}
        versions.setdefault(f"{found.get('model')}|{found.get('prompt')}", []).append(
            (float(row["p"]), float(row["outcome"])))
    # The draw: each drawn presentation's pair, and why a rung is missing (never imputed).
    draws = view.rows(connection, receipt_store.HISTORY_DRAWS, order="served_at, id") \
        if receipt_store.has_table(connection, receipt_store.HISTORY_DRAWS) else []
    now_receipts = [r for r in view.forecast_receipts(connection, kind="item_unassisted_success")
                    if str(r.get("forecaster", "")).startswith("llm_history_v1:")]
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for receipt in now_receipts:
        by_pair.setdefault((str(receipt.get("plan_presentation_id")), str(receipt["forecaster"])), []).append(receipt)
    missing: dict[str, int] = {}
    skips: dict[str, dict[str, int]] = {}
    complete = 0
    for receipt in now_receipts:
        if receipt.get("censor_reason"):
            rung = str(receipt["forecaster"]).rpartition(":")[2]
            tally = skips.setdefault(rung, {})
            tally[str(receipt["censor_reason"])] = tally.get(str(receipt["censor_reason"]), 0) + 1
    for drawn in draws:
        pid = str(drawn["plan_presentation_id"])
        ok = []
        for rung in (str(drawn["anchor_rung"]), str(drawn["drawn_rung"])):
            found = by_pair.get((pid, f"llm_history_v1:{rung}"), [])
            if any(r.get("status") == "ok" and r.get("p") is not None for r in found):
                ok.append(rung)
                continue
            reasons = sorted({str(r.get("censor_reason")) for r in found if r.get("censor_reason")})
            why = f"{rung}:{reasons[-1] if reasons else 'no_receipt'}"
            missing[why] = missing.get(why, 0) + 1
        complete += len(ok) == 2
    return {
        "version": HISTORY_REPORT_VERSION, "resolver_version": HR.RESOLVER_VERSION, "exploratory": True,
        "notes": ["Every comparison is exploratory, on whatever has resolved (no minimum sample); an interval "
                  "covering zero is not read as no difference.",
                  "Delayed cold reads natural first checks: conditional on observation (whether and when a check "
                  "happens depends on the policy and on returning); the intended lag estimand comes from RO5's "
                  "randomized checks.",
                  "Nothing stops automatically: adaptive_difficulty.outside_forecasters turns the forecaster off."],
        "subject": HISTORY_SUBJECT, "comparisons": comparisons, "ladder": ladder, "calibration": calibration,
        "delayed_cold": {"intention_to_treat": delayed, "statuses": statuses,
                         "per_protocol_calibration": {name: _calibration(found)
                                                      for name, found in sorted(pp_points.items())}},
        "calibration_slopes": calibration_slopes(versions),
        "draws": {"presentations": len(draws), "complete_pairs": complete, "missing": dict(sorted(missing.items())),
                  "skipped_by_rung": {rung: dict(sorted(t.items())) for rung, t in sorted(skips.items())}},
    }


__all__ = ["CLIP", "HISTORY_COMPARATORS", "HISTORY_REPORT_VERSION", "SCORE_VERSION", "SLOPE_PRIOR", "brier",
           "calibration_slopes", "history_report", "log_loss", "rebuild", "score_rows"]

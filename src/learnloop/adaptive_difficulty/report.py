"""The AD report (``learnloop ad report``; spec_adaptive_difficulty_v1 §10.4, §5.8, §5.9, §7.4, §9.6).

Read-only (the database opened read-only, never migrated) and zero model
calls. Run it on a backup copy. Every report computes, as monitors and never as
preconditions (D3):

* the prequential scores of every arm (:mod:`.arms`), first-attempt split first,
  then the never-seen-cell split, then all; reliability by decile and in the
  band region;
* field §7.4's rule for ``@subject`` against ``mastery_ekf``, ``@lo`` and
  ``@subject_uniform`` (log loss overall and on the first-attempt split, the
  bootstrap interval at margin 0, the fast-track miss rate with AD as the
  predictor), the anytime-valid confidence sequences, and the honest line
  ("helping", "hurting" or "can't tell yet") for sharing, coupling, reading and
  the verdict term;
* the auto-flags, each with the switch it recommends;
* the identifiability diagnostics (§5.8): feature-time correlation, aliased
  directions, contraction, prior sensitivity, the hyperparameter posterior and
  each reading kind's contraction; and the honest statement;
* time to a usable estimate (§5.9), realized success on AD-selected practice,
  the trivial-success rate, the commission miss rate;
* the dose arm's counts and the dose-and-burden analysis (:mod:`.dose_report`),
  with the self-check calibration (D22).

No outcome of the report changes any switch, config or served item.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import timedelta
from typing import Any

import numpy as np

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import arms as A
from learnloop.adaptive_difficulty import dose_report as DR
from learnloop.adaptive_difficulty import monitoring as MON
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S

REPORT_VERSION = "ad_report_v1"
HONEST_STATEMENT = (
    "The estimated rise in your skill and the estimated hardness of each kind of question are conditional on two "
    "assumptions: that the hardness of a question kind is stable over time, and that generated questions really have "
    "the features they were asked for. Your answers alone cannot separate a rise in skill from questions at a level "
    "being easier than assumed. On something you have not practised yet, the first estimate leans on your other "
    "answers, on how related LearnLoop judges the topics to be, and on what you have read; your first answers there "
    "correct it."
)
SPLITS = ("first_attempt_lo", "first_surface_cell", None)
COMPARISONS = (("sharing", A.SUBJECT, A.LO, "first_attempt_lo", "sharing_worse_than_topic_only"),
               ("coupling", A.SUBJECT, A.UNIFORM, "first_attempt_lo", "coupling_worse_than_uniform"),
               ("reading", A.SUBJECT, A.NOREAD, "after_reading", "reading_worse_than_no_reading"),
               ("verdicts", A.SUBJECT, A.NOVERDICT, "after_verdict", "verdicts_worse_than_no_verdicts"))
FAST_TRACK_Q = 0.9


def arm_scores(records: Sequence[A.Record], arm: str, split: str | None) -> dict[str, Any]:
    rows = [r for r in records if (split is None or getattr(r, split)) and r.p.get(arm) is not None]
    if not rows:
        return {"n": 0}
    p = np.array([r.p[arm] for r in rows])
    y = np.array([r.y for r in rows])
    return {
        "n": len(rows),
        "log_loss": float(np.mean([MON.log_loss(a, b) for a, b in zip(p, y)])),
        "brier": float(np.mean((p - y) ** 2)),
        "band_region_error": MON.band_region_error(p, y),
        "reliability": MON.reliability(p, y),
    }


def _arm_names(records: Sequence[A.Record]) -> list[str]:
    names: set[str] = set()
    for record in records:
        names.update(record.p)
    return sorted(names)


def _field_rule(records: Sequence[A.Record], challenger: str, comparator: str) -> dict[str, Any]:
    out = {}
    for split in ("all", "first_attempt_lo"):
        diffs, ranges = MON.difference_terms([r.__dict__ | {"p": r.p, "y": r.y} for r in records], challenger,
                                             comparator, split=None if split == "all" else split)
        boot = MON.bootstrap_interval([-d for d in diffs])  # improvement = comparator - challenger
        out[split] = {"improvement": boot, "beats": bool(boot["ci"] and boot["ci"][0] > 0.0),
                      "sequence": MON.confidence_sequence(diffs, ranges=ranges)}
    first = [r for r in records if r.first_attempt_lo and r.p.get(challenger) is not None]
    fast = [r for r in first if r.p[challenger] >= FAST_TRACK_Q]
    misses = sum(1 for r in fast if r.y < 1.0)
    out["fast_track"] = {"predicted": len(fast), "missed": misses,
                         "miss_rate": (misses / len(fast)) if fast else None, "wilson": MON.wilson(misses, len(fast))}
    return out


def _flags_and_lines(records: Sequence[A.Record], previous_errors: Sequence[float | None], *,
                     selected_outcomes: Sequence[float], delivered: Sequence[Mapping[str, Any]],
                     lowerings: Sequence[str], now: str) -> tuple[list[dict[str, Any]], list[str]]:
    dicts = [r.__dict__ | {"p": r.p, "y": r.y} for r in records]
    flags, lines = [], []
    for subject, challenger, comparator, split, flag in COMPARISONS:
        diffs, ranges = MON.difference_terms(dicts, challenger, comparator, split=split)
        result = MON.comparison_flag(flag, diffs, ranges)
        flags.append(result.as_dict())
        lines.append(MON.honest_line({"sharing": "Sharing across topics against topic-only",
                                      "coupling": "The learned coupling against uniform sharing",
                                      "reading": "Reading against no reading",
                                      "verdicts": "Self-check verdicts against none"}[subject],
                                     MON.verdict(result.detail), result.detail.get("n", 0)))
    subject_scores = arm_scores(records, A.SUBJECT, None)
    errors = list(previous_errors) + [subject_scores.get("band_region_error")]
    flags.append(MON.readiness_flag(errors).as_dict())
    flags.append(MON.band_missed_flag(selected_outcomes).as_dict())
    flags.append(MON.dose_burden_flag(delivered, lowerings, now=now).as_dict())
    return flags, lines


CONFOUNDED_R = 0.6
ALIASED_SHARE = 0.05


def feature_time_correlation(points: Sequence[Mapping[str, Any] | None]) -> dict[str, dict[str, Any]]:
    """§5.8's first diagnostic: per dimension, the correlation between the served feature level and
    time (the order served); ``confounded`` when ``|r| > 0.6``."""

    correlations: dict[str, dict[str, Any]] = {}
    for dimension in ("complexity", "transfer", "scaffolding", "span", "response", "tools"):
        levels = []
        for features in points:
            features = features or {}
            if features.get(dimension) is None:
                continue
            levels.append(S.feature_level(dimension, features.get(dimension)))
        if len(levels) >= 3 and len(set(levels)) > 1:
            r = float(np.corrcoef(np.arange(len(levels)), levels)[0, 1])
            correlations[dimension] = {"r": r, "confounded": abs(r) > CONFOUNDED_R, "n": len(levels)}
        else:
            correlations[dimension] = {"r": None, "confounded": False, "n": len(levels), "constant": True}
    return correlations


def aliased_coordinates(posterior: np.ndarray, prior_variances: Sequence[float], names: Sequence[str]
                        ) -> set[str]:
    """§5.8's aliased directions: eigenvectors of the data's contribution to the posterior precision
    of ``(β, α)``, in prior-sd units, with eigenvalue below 5% of the prior precision; the
    coordinates loading on them (``|v| > 0.5``) are "prior-dependent"."""

    prior = np.asarray(prior_variances, dtype=float)
    try:
        precision_post = np.linalg.inv(np.asarray(posterior, dtype=float) + 1e-12 * np.eye(len(names)))
    except np.linalg.LinAlgError:
        return set(names)
    D = np.diag(np.sqrt(prior))
    data = D @ (precision_post - np.diag(1.0 / prior)) @ D
    values, vectors = np.linalg.eigh(0.5 * (data + data.T))
    aliased = [i for i, value in enumerate(values) if value < ALIASED_SHARE]
    return {names[j] for i in aliased for j in range(len(names)) if abs(vectors[j, i]) > 0.5}


def _identifiability(snapshot: RP.Snapshot, records: Sequence[A.Record]) -> dict[str, Any]:
    bank = snapshot.subject.bank
    weights = bank.weights()[0]
    top = int(np.argmax(weights))
    events = [e for e in snapshot.events.attempts if e.eligible and e.spec is not None]
    correlations = feature_time_correlation([event.spec.features for event in events])
    names = list(P.BETA_NAMES) + [name for name, _m, _v in P.ALPHA_PRIORS]
    prior_var = {name: var for name, _m, var in list(P.BETA_PRIORS) + list(P.ALPHA_PRIORS)}
    idx = [bank.index[name] for name in names]
    posterior = bank.S[top][np.ix_(idx, idx)]
    contraction = {name: float(1.0 - posterior[i, i] / prior_var[name]) for i, name in enumerate(names)}
    dependent = aliased_coordinates(posterior, [prior_var[name] for name in names], names)
    aliased = sorted(dependent)
    prior_dependent = sorted(dependent)
    grid = []
    for i, point in enumerate(bank.points):
        grid.append({**point.as_dict(), "weight": float(weights[i])})
    margins = {}
    for key in ("split", "coupling", "implication"):
        values = sorted({getattr(p, key) for p in bank.points})
        posterior_margin = {v: float(sum(w for p, w in zip(bank.points, weights) if getattr(p, key) == v))
                            for v in values}
        prior_margin = 1.0 / len(values)
        margins[key] = {"posterior": posterior_margin,
                        "contraction": float(max(posterior_margin.values()) - prior_margin)}
    reading = {}
    for kind in P.READING_KINDS:
        for m in (1, 2):
            name = f"delta:{kind}:{m}"
            i = bank.index[name]
            prior = 0.0049 if m == 1 else 0.01
            reading[f"{kind}:{m}"] = {"mean": float(np.dot(weights, bank.mu[:, i])),
                                      "contraction": float(1.0 - np.dot(weights, bank.S[:, i, i]) / prior)}
    return {"feature_time_correlation": correlations, "aliased_directions": len(aliased),
            "prior_dependent": prior_dependent, "contraction": contraction, "hyperparameters": grid,
            "hyperparameter_margins": margins, "reading_kinds": reading,
            "statement": HONEST_STATEMENT}


def _sensitivity(vault: Any, repository: Any, connection: Any, snapshot: RP.Snapshot,
                 selections: Sequence[Mapping[str, Any]], *, limit: int = 50) -> dict[str, Any]:
    """Each β prior mean shifted ±1 sd: how many of the latest serve draws' modes or near-tie sets change
    (re-scored on the current state; a bounded check, §5.8)."""

    from learnloop.adaptive_difficulty import predict as PR

    serves = [row for row in selections if row["kind"] == "serve" and row.get("support")][-limit:]
    if not serves:
        return {"selections": 0, "changed": {}}
    constants = S.constants_from_config(vault.config)

    def decisions(snap: RP.Snapshot) -> list[tuple[str, tuple[str, ...]]]:
        out = []
        for row in serves:
            specs = [PR.current_spec(vault, connection, vault.practice_items[ref["ref"]], at=row["created_at"])
                     for ref in row["support"] if ref["ref"] in vault.practice_items]
            if not specs:
                out.append(("", ()))
                continue
            scored = PR.score(snap.subject, specs, constants=constants, information=False)
            mode, _pi, tied, _o, _q = S.propensities(scored, constants)
            out.append((mode, tuple(tied)))
        return out

    base = decisions(snapshot)
    changed: dict[str, int] = {}
    events = snapshot.events
    for name, mean, var in P.BETA_PRIORS:
        for sign in (-1, 1):
            settings = replace(snapshot.settings, prior_means=((name, mean + sign * math.sqrt(var)),))
            shifted = RP.run(events, settings, trace=False)
            changed[f"{name}{'+' if sign > 0 else '-'}1sd"] = sum(1 for a, b in zip(base, decisions(shifted)) if a != b)
    return {"selections": len(serves), "changed": changed}


def _selection_stats(connection: Any, snapshot: RP.Snapshot) -> dict[str, Any]:
    selections = store.selections(connection)
    serves = [row for row in selections if row["kind"] == "serve"]
    modes = Counter(row["mode"] for row in serves)
    by_presentation = {}
    for pid, block_id, item_id in connection.execute("SELECT id, block_id, practice_item_id FROM plan_presentations"):
        by_presentation[(str(block_id), str(item_id))] = str(pid)
    attempts = {e.plan_presentation_id: e for e in snapshot.events.attempts if e.plan_presentation_id}
    realized = []
    for row in serves:
        if row["mode"] not in ("band", "calibrate") or not row.get("chosen_item_id"):
            continue
        pid = by_presentation.get((str(row.get("block_id")), str(row["chosen_item_id"])))
        attempt = attempts.get(pid) if pid else None
        if attempt is not None and attempt.eligible and attempt.category is not None:
            realized.append(1.0 if attempt.category == 2 else 0.0)
    # Time to usable (§5.9): eligible answers in the subject before its first band-mode draw.
    eligible = [e for e in snapshot.events.attempts if e.eligible and e.spec is not None]
    first_band: dict[str, str] = {}
    lo_subject = snapshot.events.lo_subject
    for row in serves:
        if row["mode"] == "band":
            subject = lo_subject.get(str(row.get("learning_object_id")), "default")
            first_band.setdefault(subject, str(row["created_at"]))
    usable = {}
    for subject, at in first_band.items():
        usable[subject] = sum(1 for e in eligible if e.spec.subject == subject and e.created_at < at)
    per_lo = {}
    for row in serves:
        lo = str(row.get("learning_object_id"))
        if row["mode"] == "band" and lo not in per_lo:
            per_lo[lo] = sum(1 for e in eligible if e.learning_object_id == lo and e.created_at < row["created_at"])
    structure = snapshot.events.structure
    coupled = {lo: bool(structure.coupling(lo)) for lo in per_lo}
    results = store.commission_results(connection)
    by_point = defaultdict(lambda: Counter())
    commissions = {row["id"]: row for row in selections if row["kind"] == "commission"}
    for result in results:
        commission = commissions.get(result["selection_id"])
        key = S.point_key(commission.get("chosen_point") or {}) if commission else "unknown"
        by_point[key][result["status"]] += 1
    return {
        "serve_draws": len(serves), "modes": dict(modes),
        "band_mode_share": (modes.get("band", 0) / len(serves)) if serves else None,
        "realized_success": {"n": len(realized), "rate": float(np.mean(realized)) if realized else None,
                             "target": [0.70, 0.80]},
        "realized_outcomes": realized,
        "time_to_usable_by_subject": usable,
        "own_answers_before_band_by_lo": {lo: {"answers": n, "coupled": coupled[lo]} for lo, n in sorted(per_lo.items())},
        "commissions": {"draws": len(commissions), "results": len(results),
                        "miss_rate_by_point": {k: (v["realized_out_of_band"] / sum(v.values())) for k, v in by_point.items()}},
    }


def _trivial_success(connection: Any, snapshot: RP.Snapshot) -> dict[str, Any]:
    """§9.6: the share of successes on items whose p̄ at serve exceeded 0.95 (``ad_threshold@subject``)."""

    attempts = {e.plan_presentation_id: e for e in snapshot.events.attempts if e.plan_presentation_id}
    successes = trivial = 0
    for pid, p in connection.execute(
            "SELECT plan_presentation_id, p FROM forecast_receipts WHERE kind = 'item_unassisted_success' AND "
            "forecaster = 'ad_threshold@subject' AND plan_presentation_id IS NOT NULL"):
        attempt = attempts.get(str(pid))
        if attempt is None or not attempt.eligible or attempt.category != 2:
            continue
        successes += 1
        trivial += 1 if p is not None and float(p) > 0.95 else 0
    return {"successes": successes, "trivial": trivial, "rate": (trivial / successes) if successes else None}


def _visits(connection: Any, snapshot: RP.Snapshot) -> list[dict[str, Any]]:
    """Reader visits with their active minutes (a cost, read as the Reader report reads it) and the
    count of each kind of opportunity inside them."""

    import json

    if not store.has_table(connection, "interaction_events"):
        return []
    opened: dict[str, str] = {}
    visits = []
    for kind, payload, created_at in connection.execute(
            "SELECT kind, payload_json, created_at FROM interaction_events WHERE kind IN "
            "('reader_view_opened', 'reader_view_closed') ORDER BY created_at, id"):
        try:
            data = json.loads(payload or "{}")
        except ValueError:
            data = {}
        visit = data.get("visit_id")
        if not visit:
            continue
        if kind == "reader_view_opened":
            opened.setdefault(str(visit), str(created_at))
        elif str(visit) in opened:
            start, end = opened[str(visit)], str(created_at)
            counts = Counter(o.kind for o in snapshot.events.opportunities if start <= o.created_at <= end)
            visits.append({"visit_id": str(visit), "active_minutes": float(data.get("active_seconds") or 0.0) / 60.0,
                           "counts": dict(counts)})
    return visits


def _offer_outcomes(connection: Any, snapshot: RP.Snapshot) -> dict[str, list[DR.OfferOutcome]]:
    """Each dose draw's matured cold outcome (§5.12): the first graded attempt on an item of one of
    the section's LOs at least one day after the decision, with no reveal of that item in between."""

    rows = store.dose_rows(connection)
    draws = [row for row in rows if row["row_kind"] == "draw"]
    taken = {row["draw_id"] for row in rows if row["row_kind"] == "taken"}
    reveals = defaultdict(list)
    if store.has_table(connection, "reveal_events"):
        for item_id, created_at in connection.execute("SELECT practice_item_id, created_at FROM reveal_events"):
            reveals[str(item_id)].append(str(created_at))
    attempts = sorted((e for e in snapshot.events.attempts if e.eligible and e.category is not None),
                      key=lambda e: e.created_at)
    by_variant: dict[str, list[DR.OfferOutcome]] = defaultdict(list)
    for draw in draws:
        decided = parse_utc(str(draw["created_at"]))
        if decided is None:
            continue
        cold = (decided + timedelta(days=1)).isoformat().replace("+00:00", "Z")
        los = set(draw.get("learning_object_ids") or [])
        outcome = None
        for attempt in attempts:
            if attempt.learning_object_id in los and attempt.created_at >= cold:
                if any(str(draw["created_at"]) <= r <= attempt.created_at for r in reveals.get(attempt.practice_item_id, ())):
                    continue
                outcome = 1.0 if attempt.category == 2 else 0.0
                break
        forecast = draw.get("forecast_p")
        band = None if forecast is None else ("below_50" if forecast < 0.5 else "50_80" if forecast <= 0.8 else "above_80")
        propensities = draw.get("propensities") or {}
        taken_doses = (draw.get("detail") or {}).get("dose_taken") or {}
        for variant in propensities:
            if variant != "none":
                kind = {"extra_worked_example": "worked_example", "extra_question": "in_passage_question"}.get(variant)
                by_variant[variant].append(DR.OfferOutcome(str(draw.get("chosen_variant")), propensities, outcome,
                                                           int(taken_doses.get(kind, 0) or 0), band,
                                                           draw["id"] in taken))
    return by_variant


def _dose_arm(connection: Any) -> dict[str, Any]:
    rows = store.dose_rows(connection)
    draws = [row for row in rows if row["row_kind"] == "draw"]
    uptake = Counter((row["row_kind"]) for row in rows if row["row_kind"] != "draw")
    variants = Counter(row.get("chosen_variant") for row in draws)
    delivered = []
    by_draw = defaultdict(set)
    for row in rows:
        if row["row_kind"] != "draw":
            by_draw[row["draw_id"]].add(row["row_kind"])
    for draw in draws:
        if draw.get("chosen_variant") not in (None, "none") and "delivered" in by_draw.get(draw["id"], set()):
            delivered.append({"draw_id": draw["id"], "dismissed": "dismissed" in by_draw[draw["id"]]})
    return {"eligible_draws": len(draws), "by_variant": dict(variants), "uptake": dict(uptake),
            "delivered": delivered}


def _self_check(records: Sequence[A.Record]) -> dict[str, Any]:
    out = {}
    for klass in ("self_check:matched", "self_check:missed"):
        rows = [r for r in records if r.verdict_class == klass]
        realized = [r.y for r in rows]
        out[klass] = {
            "n": len(rows),
            "realized": float(np.mean(realized)) if rows else None,
            "wilson": MON.wilson(int(len(rows) - sum(realized)), len(rows)) if rows else None,
            "predicted_with_term": float(np.mean([r.p[A.SUBJECT] for r in rows if A.SUBJECT in r.p])) if rows else None,
            "predicted_without_term": float(np.mean([r.p[A.NOVERDICT] for r in rows if A.NOVERDICT in r.p]))
            if rows and any(A.NOVERDICT in r.p for r in rows) else None,
        }
    return out


def _median_doses(records: Sequence[A.Record]) -> dict[str, float]:
    out = {}
    for kind in P.READING_KINDS:
        values = [r.doses.get(kind, 0.0) for r in records if r.doses.get(kind, 0.0) > 0]
        out[kind] = float(np.median(values)) if values else 0.0
    return out


def _answer_minutes(connection: Any) -> float | None:
    values = [float(v) / 60.0 for (v,) in connection.execute(
        "SELECT latency_seconds FROM practice_attempts WHERE latency_seconds IS NOT NULL AND latency_seconds > 0")]
    return float(np.median(values)) if values else None


def build(vault: Any, repository: Any, connection: Any, *, arms: Sequence[str] = A.DEFAULT_ARMS,
          previous_errors: Sequence[float | None] = (), sensitivity: bool = True,
          now: str | None = None) -> dict[str, Any]:
    """The whole report (a pure read; zero model calls)."""

    now = now or utc_now_iso()
    log = A.prequential(vault, repository, connection, arms=arms)
    records: list[A.Record] = log["records"]
    settings = RP.ReplaySettings(coupling=True, reading=True, verdicts=True)
    snapshot = RP.run(log["events"], settings, trace=False)
    names = _arm_names(records)
    scores = {name: {("all" if split is None else split): arm_scores(records, name, split) for split in SPLITS}
              for name in names}
    rule = {comparator: _field_rule(records, A.SUBJECT, comparator)
            for comparator in ("mastery_ekf", A.LO, A.UNIFORM) if comparator in names}
    stats = _selection_stats(connection, snapshot)
    dose_arm = _dose_arm(connection)
    flags, lines = _flags_and_lines(records, previous_errors, selected_outcomes=stats["realized_outcomes"],
                                    delivered=dose_arm["delivered"], lowerings=(), now=now)
    selections = store.selections(connection)
    dose = DR.analyse(snapshot.subject, visits=_visits(connection, snapshot), answer_minutes=_answer_minutes(connection),
                      median_doses=_median_doses(records), offers=_offer_outcomes(connection, snapshot),
                      records=[{"y": r.y, "p": r.p.get(A.SUBJECT), "doses": r.doses} for r in records])
    report = {
        "version": REPORT_VERSION,
        "generated_at": now,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "versions": {**P.versions(), "replay": RP.REPLAY_VERSION, "select": S.SELECT_VERSION,
                     "dose": DR.DOSE_REPORT_VERSION},
        "inputs": dict(log["events"].summary),
        "field_coverage": log["field_coverage"],
        "auto_flags": flags,
        "honest_lines": lines,
        "scores": scores,
        "field_rule_monitor": rule,
        "identifiability": _identifiability(snapshot, records),
        "prior_sensitivity": _sensitivity(vault, repository, connection, snapshot, selections) if sensitivity else None,
        "selection": {k: v for k, v in stats.items() if k != "realized_outcomes"},
        "trivial_success": _trivial_success(connection, snapshot),
        "dose_arm": {k: v for k, v in dose_arm.items() if k != "delivered"},
        "dose_and_burden": dose,
        "self_check_calibration": _self_check(records),
        "records": len(records),
    }
    return report


def render_markdown(report: Mapping[str, Any]) -> str:
    """A plain rendering for the owner (the JSON is the record)."""

    lines = [f"# Adaptive difficulty report ({report['generated_at']})", "",
             f"Algorithm version {report['algorithm_version']}; {report['records']} scored first-surface attempts.", "",
             "## Auto-flags"]
    for flag in report["auto_flags"]:
        lines.append(f"- {flag['flag']}: {'FIRES -> recommends ' + flag['recommends'] if flag['fires'] else 'quiet'}")
    lines += ["", "## Is it helping?"]
    lines += [f"- {line}" for line in report["honest_lines"]]
    lines += ["", "## Scores (first attempts at never-seen topics first)"]
    for arm, by_split in sorted(report["scores"].items()):
        first = by_split.get("first_attempt_lo") or {}
        everything = by_split.get("all") or {}
        if not everything.get("n"):
            continue
        lines.append(f"- {arm}: first-attempt log loss {first.get('log_loss') if first.get('n') else 'n/a'} "
                     f"(n {first.get('n', 0)}); all {everything.get('log_loss'):.4f} (n {everything.get('n')})")
    lines += ["", "## What helps you (dose and burden)"]
    lines += [f"- {line}" for line in report["dose_and_burden"]["lines"]]
    lines += ["", "## The honest statement", report["identifiability"]["statement"]]
    return "\n".join(lines) + "\n"


__all__ = ["HONEST_STATEMENT", "REPORT_VERSION", "SPLITS", "aliased_coordinates", "arm_scores", "build",
           "feature_time_correlation", "render_markdown"]

"""The four-way difficulty replay (refactor step H2): what the old difficulty scalar does, before anything changes.

    uv run python scripts/difficulty_four_way.py <vault copy> --out <private.json> [--as-of ISO] [--top-k 10]

Run it on a copy of a vault, never on a live one. The input is copied once more (databases through the backup
API) into a scratch directory, and every arm replays the whole history on its own backup copy of that scratch
database through the ordinary shadow rebuild (``learnloop.substrate.shadow_rebuild``), so neither the input nor
the scratch vault is written; the input's databases are hashed before and after to show it.

The arms (``docs/specs/spec_router_objective_v1.md`` §11, ``docs/specs/refactor_strategy_v3.md`` §2.11 H2):

* ``a_today``: the vault's own config. A plain shadow rebuild.
* ``b_label_off_mastery``: ``mastery.irt.difficulty_from_prior=false``, so every reader of the IRT seam gets
  ``b = difficulty_default`` instead of the label's.
* ``c_surprise_from_ad``: today's mastery; the surprise row reads adaptive difficulty's predictive success for the
  item (below) instead of the label's ``b``.
* ``d_both``: (b)'s config and (c)'s surprise.
* ``e_surprise_from_receipt``: today's mastery; the surprise row reads the forecast adaptive difficulty recorded when
  it served the item (the attempt's plan presentation's ``ad_threshold@subject`` or ``ad_threshold_repeat@subject``
  receipt), and mastery's own prediction where no receipt applies (H3's design,
  ``docs/reviews/refactor-h3-h6-design.md`` §2.2).
* ``f_label_off_and_receipt``: (b)'s config and (e)'s surprise: H3 as designed.

Each arm is reported against (a): mastery, surprise, stored due dates, the due queue at ``--as-of``, and once
(it does not depend on the arm) adaptive difficulty's prequential scoring with and without ``z_llm``. The JSON
holds values and ids and stays private; stdout prints counts and summary statistics only.

Zero model calls: the shadow rebuild, adaptive difficulty's replay and the queue read are all model-free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_VERSION = "difficulty_four_way_v2"
LABEL_OFF = "mastery.irt.difficulty_from_prior=false"


#: Where an arm's surprise reads its prediction: the mastery path's own (None), AD's prediction replayed up to the
#: attempt (``ad_prefix``), or AD's forecast recorded at the serve (``receipt``).
AD_PREFIX, RECEIPT = "ad_prefix", "receipt"


@dataclass(frozen=True)
class Arm:
    name: str
    assignments: tuple[str, ...]
    surprise_source: str | None
    description: str

    @property
    def surprise_from_ad(self) -> bool:
        return self.surprise_source is not None


ARMS: tuple[Arm, ...] = (
    Arm("a_today", (), None, "today: the vault's own config"),
    Arm("b_label_off_mastery", (LABEL_OFF,), None, "the label off the mastery path (b = difficulty_default)"),
    Arm("c_surprise_from_ad", (), AD_PREFIX, "surprise from adaptive difficulty's item-conditioned predictive"),
    Arm("d_both", (LABEL_OFF,), AD_PREFIX, "both: (b)'s config and (c)'s surprise"),
    Arm("e_surprise_from_receipt", (), RECEIPT,
        "surprise from AD's serve-time receipt, mastery's own prediction where none applies"),
    Arm("f_label_off_and_receipt", (LABEL_OFF,), RECEIPT, "H3 as designed: (b)'s config and (e)'s surprise"),
)
BASELINE = ARMS[0].name


# -- adaptive difficulty's predictive, per attempt ---------------------------------------------------------------

@dataclass(frozen=True)
class Predictive:
    """AD's predictive success for one attempt, from AD's state as it stood before the attempt.

    ``tier``: ``item`` (the item's cell exists in AD's subject view: the item-conditioned predictive),
    ``population`` (AD can read the item but has no cell for it yet: the prediction reads the cell's population
    prior through AD's own projection), or ``default`` (AD cannot read the attempt at all: no spec, AD's
    material view unavailable, or an attempt AD never reads; surprise then uses ``b = difficulty_default``)."""

    p: float | None
    tier: str
    reason: str | None = None


def _without_z_llm(events: Any) -> Any:
    """The same events with ``z_llm`` dropped from every item's signals (its coefficient stays at its prior and
    reads nothing, which is what retiring the signal from AD's predictor means)."""

    attempts = []
    for attempt in events.attempts:
        spec = attempt.spec
        if spec is not None and "z_llm" in spec.signals:
            spec = replace(spec, signals={k: v for k, v in spec.signals.items() if k != "z_llm"})
            attempt = replace(attempt, spec=spec)
        attempts.append(attempt)
    return replace(events, attempts=attempts)


def _load_ad_events(vault: Any, repository: Any) -> tuple[Any, Any]:
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.db.connection import connect

    settings = RP.ReplaySettings.from_config(vault.config)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository, settings=settings)
    return events, settings


def _changes_state(kind: str, event: Any) -> bool:
    """Whether a stream entry can move AD's subject view: a claim, an opportunity, a trained attempt, or an
    attempt that closes reading windows. An attempt that trains nothing and closes nothing leaves it as it was."""

    if kind != "attempt":
        return True
    trains = event.eligible and event.spec is not None and event.category is not None
    return bool(trains or event.closes)


def ad_predictive(events: Any, settings: Any) -> dict[str, Predictive]:
    """AD's predictive success ``p̄`` for every attempt AD's events hold, each from AD's replay of everything
    before it in AD's own order (a prefix replay, so a later answer never informs an earlier prediction).

    AD's own observer hook runs only before trained attempts; a repeat, which trains nothing, is exactly the
    attempt surprise most needs a prediction for, so the state before each attempt is rebuilt as a replay of
    the stream's prefix. Consecutive attempts with nothing state-changing between them share one replay."""

    from learnloop.adaptive_difficulty import model as M
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.predict import predict

    stream = events.ordered()
    out: dict[str, Predictive] = {}
    last_change = 0  # entries stream[:last_change] hold every state change seen so far
    cached: tuple[int, Any] | None = None
    for index, (kind, event) in enumerate(stream):
        if kind == "attempt":
            if event.spec is None:
                out[event.attempt_id] = Predictive(None, "default", event.reason or "no_spec")
            else:
                if cached is None or cached[0] != last_change:
                    prefix = stream[:last_change]
                    sub = replace(
                        events,
                        attempts=[e for k, e in prefix if k == "attempt"],
                        claims=[e for k, e in prefix if k == "claim"],
                        opportunities=[e for k, e in prefix if k == "opportunity"],
                    )
                    cached = (last_change, RP.run(sub, settings, trace=False))
                view = cached[1].subject
                # Couplings and loadings in force are read at the attempt's time, as the replay reads them.
                events.structure.now = event.at
                facet, capability = event.spec.cell()
                tier = "item" if view.bank.has(M.cell_name(facet, capability)) else "population"
                p = float(predict(view, event.spec, warmth=event.warmth).p_bar)
                out[event.attempt_id] = Predictive(p, tier, event.reason)
        if _changes_state(kind, event):
            last_change = index + 1
    events.structure.now = math.inf
    return out


def ad_observer_predictions(events: Any, settings: Any) -> dict[str, float]:
    """``p̄`` before each trained attempt, from AD's own observer hook in one replay (the prefix replay's check)."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.predict import predict

    out: dict[str, float] = {}

    def observer(attempt: Any, subject: Any, _lo_view: Any, _context: Any) -> None:
        out[attempt.attempt_id] = float(predict(subject, attempt.spec, warmth=attempt.warmth).p_bar)

    RP.run(events, settings, trace=False, observer=observer)
    return out


def ad_scoring(events: Any, settings: Any) -> dict[str, Any]:
    """AD's prequential score on its own forecast event (an unassisted success, category 2), with ``z_llm`` as
    served and with it out. Every trained attempt is predicted from the state before it, then updates it."""

    from learnloop.adaptive_difficulty import outcomes as O
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.predict import predict

    with_llm = sum(1 for e in events.attempts
                   if e.eligible and e.spec is not None and e.category is not None and "z_llm" in e.spec.signals)
    variants: dict[str, dict[str, Any]] = {}
    per_attempt: dict[str, dict[str, Any]] = {}
    for name, variant in (("with_z_llm", events), ("without_z_llm", _without_z_llm(events))):
        rows: list[tuple[float, float, bool]] = []

        def observer(attempt: Any, subject: Any, _lo_view: Any, context: Any, rows=rows, name=name) -> None:
            p = float(predict(subject, attempt.spec, warmth=attempt.warmth).p_bar)
            y = O.unassisted_success(attempt.category)
            if y is None:
                return
            rows.append((p, float(y), bool(context.first_attempt_lo)))
            per_attempt.setdefault(attempt.attempt_id, {"y": y})[name] = p

        RP.run(variant, settings, trace=False, observer=observer)
        variants[name] = {"all": _scores(rows), "first_attempt_lo": _scores([r for r in rows if r[2]]),
                          "later": _scores([r for r in rows if not r[2]])}
    shifts = [abs(v["with_z_llm"] - v["without_z_llm"]) for v in per_attempt.values()
              if "with_z_llm" in v and "without_z_llm" in v]
    return {"scored_attempts": len(per_attempt), "attempts_with_z_llm": with_llm, "variants": variants,
            "abs_p_shift": _summary(shifts), "per_attempt": per_attempt}


def _scores(rows: Sequence[tuple[float, float, bool]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "log_loss": None, "brier": None, "mean_p": None, "base_rate": None}
    eps = 1e-12
    log_loss = -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y, _ in rows) / len(rows)
    brier = sum((p - y) ** 2 for p, y, _ in rows) / len(rows)
    return {"n": len(rows), "log_loss": round(log_loss, 6), "brier": round(brier, 6),
            "mean_p": round(sum(p for p, _, _ in rows) / len(rows), 6),
            "base_rate": round(sum(y for _, y, _ in rows) / len(rows), 6)}


# -- AD's serve-time forecast receipts, per attempt (arms e and f) ------------------------------------------------

#: The receipts H3's surprise reads: the subject view's forecast, as AD served the item.
RECEIPT_FORECASTERS = ("ad_threshold@subject", "ad_threshold_repeat@subject")


def _has_table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def receipt_predictions(connection: Any) -> dict[str, Predictive]:
    """For every attempt, the serve-time receipt H3's surprise would read, or why none applies.

    The rule (``docs/reviews/refactor-h3-h6-design.md`` §2.2): the attempt's plan presentation
    (``practice_attempts.plan_presentation_id``); only the first attempt bound to it, on the presentation's item;
    an ``item_unassisted_success`` receipt of the subject view (:data:`RECEIPT_FORECASTERS`) bound to that
    presentation, with status ``ok``, a probability, and inputs no later than the serve (AD1's validity rule). Tier
    ``receipt`` carries the receipt's ``p``; tier ``fallback`` carries the reason: ``unbound``,
    ``not_first_on_presentation``, ``no_presentation``, ``item_mismatch``, ``no_receipt``, ``receipt_not_ok``,
    ``receipt_without_p`` or ``receipt_after_serve``."""

    from learnloop.scheduling.forecast_receipts import valid_for_serve

    if not _has_table(connection, "practice_attempts"):
        return {}
    columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")}
    bound = "plan_presentation_id" in columns
    attempts = connection.execute(
        "SELECT id, practice_item_id, " + ("plan_presentation_id" if bound else "NULL")
        + ", created_at FROM practice_attempts ORDER BY created_at, id").fetchall()
    presentations: dict[str, tuple[str, str]] = {}
    if _has_table(connection, "plan_presentations"):
        presentations = {str(r[0]): (str(r[1]), str(r[2])) for r in connection.execute(
            "SELECT id, practice_item_id, served_at FROM plan_presentations")}
    receipts: dict[str, list[dict[str, Any]]] = {}
    if _has_table(connection, "forecast_receipts"):
        marks = ", ".join("?" for _ in RECEIPT_FORECASTERS)
        for r in connection.execute(
                "SELECT plan_presentation_id, practice_item_id, forecaster, status, p, inputs_as_of "
                f"FROM forecast_receipts WHERE kind = 'item_unassisted_success' AND forecaster IN ({marks}) "
                "AND plan_presentation_id IS NOT NULL ORDER BY forecaster, created_at, id", RECEIPT_FORECASTERS):
            receipts.setdefault(str(r[0]), []).append(
                {"practice_item_id": r[1], "forecaster": r[2], "status": r[3], "p": r[4], "inputs_as_of": r[5]})
    out: dict[str, Predictive] = {}
    first: set[str] = set()
    for attempt_id, item_id, presentation_id, _created in attempts:
        attempt_id = str(attempt_id)
        if not presentation_id:
            out[attempt_id] = Predictive(None, "fallback", "unbound")
            continue
        presentation_id = str(presentation_id)
        if presentation_id in first:
            out[attempt_id] = Predictive(None, "fallback", "not_first_on_presentation")
            continue
        first.add(presentation_id)
        presentation = presentations.get(presentation_id)
        if presentation is None:
            out[attempt_id] = Predictive(None, "fallback", "no_presentation")
            continue
        if presentation[0] != str(item_id):
            out[attempt_id] = Predictive(None, "fallback", "item_mismatch")
            continue
        found = [r for r in receipts.get(presentation_id, []) if str(r["practice_item_id"] or item_id) == str(item_id)]
        if not found:
            out[attempt_id] = Predictive(None, "fallback", "no_receipt")
            continue
        receipt = found[0]  # ``@subject`` sorts before ``_repeat@subject``; a presentation holds one or the other
        if receipt["status"] != "ok":
            out[attempt_id] = Predictive(None, "fallback", "receipt_not_ok")
        elif receipt["p"] is None:
            out[attempt_id] = Predictive(None, "fallback", "receipt_without_p")
        elif not valid_for_serve(receipt, presentation[1]):
            out[attempt_id] = Predictive(None, "fallback", "receipt_after_serve")
        else:
            out[attempt_id] = Predictive(float(receipt["p"]), "receipt", str(receipt["forecaster"]))
    return out


def receipt_against_prefix(receipts: Mapping[str, Predictive], prefix: Mapping[str, Predictive]) -> dict[str, Any]:
    """How far AD's forecast at the serve is from AD's prediction replayed up to the attempt, where both exist."""

    pairs = [(receipts[k].p, prefix[k].p) for k in receipts
             if receipts[k].p is not None and k in prefix and prefix[k].p is not None]
    return {"both": len(pairs), "abs_p_difference": _summary([abs(a - b) for a, b in pairs]),
            "p_difference": _summary([a - b for a, b in pairs])}


# -- the surprise patch (arms c to f), inside the scratch replay only ------------------------------------------------

_GRADE_INPUTS: ContextVar[Any] = ContextVar("difficulty_four_way_grade_inputs", default=None)


@dataclass
class SurprisePatchLog:
    tiers: Counter = field(default_factory=Counter)
    outside_grade: int = 0


@contextmanager
def surprise_from_ad(predictive: Mapping[str, Predictive], *, fallback: str = "default") -> Iterator[SurprisePatchLog]:
    """FIREWALL CROSSING, SCRATCH REPLAY ONLY. Adaptive difficulty may not feed a stored surprise row today (the
    firewall's A2 and A12); arm (c) is the experiment the owner rules on, so it exists only here, around one
    shadow rebuild of a discarded scratch copy, and is undone on exit.

    The grade path computes mastery and surprise from one IRT ``(a, b)``. Inside this context the surprise alone
    reads AD's predictive ``p̄`` for the attempt: it is handed ``b' = μ_prior - logit(p̄)/a``, the ``b`` at which
    the 2PL link at the prior mean equals ``p̄``, so its innovation, variance and interval factor are the usual
    formulae around AD's prediction. Mastery keeps its own ``b``. A primed attempt takes the same priming offset
    the label's ``b`` takes. Where AD has no prediction for the attempt: ``fallback="default"`` (arms c, d) reads
    ``b' = difficulty_default``; ``fallback="mastery"`` (arms e, f, H3's design) leaves the surprise on the mastery
    path's own ``b`` (priming already applied by the grade)."""

    from learnloop.attempts import attempts as grade_module

    original_belief = grade_module._belief_update
    original_surprise = grade_module.compute_surprise
    log = SurprisePatchLog()

    def belief_update(inputs: Any, *args: Any, **kwargs: Any) -> Any:
        token = _GRADE_INPUTS.set(inputs)
        try:
            return original_belief(inputs, *args, **kwargs)
        finally:
            _GRADE_INPUTS.reset(token)

    def compute_surprise(*, prior: Any, config: Any, item_a: float = 1.0, item_b: float = 0.0, **kwargs: Any) -> Any:
        inputs = _GRADE_INPUTS.get()
        if inputs is None:
            log.outside_grade += 1
            return original_surprise(prior=prior, config=config, item_a=item_a, item_b=item_b, **kwargs)
        irt = config.mastery.irt
        entry = predictive.get(str(inputs.attempt_id))
        if (entry is None or entry.p is None) and fallback == "mastery":
            log.tiers["fallback"] += 1
            return original_surprise(prior=prior, config=config, item_a=item_a, item_b=item_b, **kwargs)
        if entry is None or entry.p is None:
            log.tiers["default"] += 1
            b = float(irt.difficulty_default)
        else:
            log.tiers[entry.tier] += 1
            p = min(max(entry.p, 1e-6), 1.0 - 1e-6)
            b = float(prior.logit_mean) - math.log(p / (1.0 - p)) / float(item_a)
        if inputs.draft.primed:
            b -= float(irt.priming_b_offset)
        return original_surprise(prior=prior, config=config, item_a=item_a, item_b=b, **kwargs)

    grade_module._belief_update = belief_update
    grade_module.compute_surprise = compute_surprise
    try:
        yield log
    finally:
        grade_module._belief_update = original_belief
        grade_module.compute_surprise = original_surprise


# -- what each arm's replayed copy holds ---------------------------------------------------------------------------

def read_replayed(vault: Any, repository: Any, *, as_of: datetime) -> dict[str, Any]:
    """Mastery, surprise rows, stored due dates and the due queue of one replayed copy."""

    from learnloop.clock import FrozenClock
    from learnloop.scheduling.scheduler import read_due_queue

    with closing(repository.connection()) as connection:
        mastery = {str(r[0]): {"logit_mean": r[1], "logit_variance": r[2], "evidence_count": r[3]}
                   for r in connection.execute(
                       "SELECT learning_object_id, logit_mean, logit_variance, evidence_count "
                       "FROM learning_object_mastery")}
        surprise = {}
        for r in connection.execute(
                "SELECT attempt_id, predictive_surprise, bayesian_surprise, surprise_direction, fsrs_interval_factor, "
                "predicted_score_dist_json FROM attempt_surprise"):
            try:
                predicted = json.loads(r[5]) if r[5] else {}
            except ValueError:
                predicted = {}
            surprise[str(r[0])] = {"predictive_surprise": r[1], "bayesian_surprise": r[2], "surprise_direction": r[3],
                                   "fsrs_interval_factor": r[4],
                                   "expected_correctness": predicted.get("expected_correctness"),
                                   "b": predicted.get("b")}
        items = {str(r[0]): r[1] for r in connection.execute("SELECT practice_item_id, due_at FROM practice_item_state")}
        cards = {"|".join(str(v) for v in r[:3]): r[3] for r in connection.execute(
            "SELECT learner_id, card_lineage_id, scheduler_algorithm_version, due_at FROM activity_card_state")}
    queue: list[str] | None
    queue_error = None
    try:
        queue = [entry.practice_item_id for entry in read_due_queue(vault, repository, clock=FrozenClock(as_of))]
    except Exception as exc:  # noqa: BLE001 - a queue that cannot be read is reported, never fatal to the arms
        queue, queue_error = None, type(exc).__name__
    return {"mastery": mastery, "surprise": surprise, "due": {"practice_item_state": items, "activity_card_state": cards},
            "queue": queue, "queue_error": queue_error}


# -- comparisons -------------------------------------------------------------------------------------------------

def _summary(values: Sequence[float]) -> dict[str, Any]:
    clean = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    n = len(clean)
    if not n:
        return {"n": 0}
    mean = sum(clean) / n
    variance = sum((v - mean) ** 2 for v in clean) / n

    def q(fraction: float) -> float:
        position = fraction * (n - 1)
        low = math.floor(position)
        high = min(low + 1, n - 1)
        return clean[low] + (clean[high] - clean[low]) * (position - low)

    return {"n": n, "mean": round(mean, 6), "variance": round(variance, 6), "min": round(clean[0], 6),
            "p10": round(q(0.1), 6), "median": round(q(0.5), 6), "p90": round(q(0.9), 6), "max": round(clean[-1], 6)}


def compare_mastery(base: Mapping[str, Any], arm: Mapping[str, Any]) -> dict[str, Any]:
    common = sorted(set(base) & set(arm))
    changed = [k for k in common if (base[k]["logit_mean"], base[k]["logit_variance"])
               != (arm[k]["logit_mean"], arm[k]["logit_variance"])]
    return {
        "rows": len(arm), "rows_baseline": len(base), "only_baseline": len(set(base) - set(arm)),
        "only_arm": len(set(arm) - set(base)), "changed": len(changed),
        "logit_mean": _summary([arm[k]["logit_mean"] for k in arm]),
        "logit_variance": _summary([arm[k]["logit_variance"] for k in arm]),
        "delta_logit_mean": _summary([arm[k]["logit_mean"] - base[k]["logit_mean"] for k in common]),
        "delta_logit_variance": _summary([arm[k]["logit_variance"] - base[k]["logit_variance"] for k in common]),
    }


def _negative(rows: Mapping[str, Any], tau: float | None) -> dict[str, Any]:
    """Negative-direction rows, and those whose Bayesian surprise is above the follow-up gate's static threshold
    (``scheduler.followup.tau_followup_nats``; the live gate also scores and learns, so this is an indication)."""

    negative = [v for v in rows.values() if v["surprise_direction"] == "negative"]
    above = None if tau is None else sum(1 for v in negative if (v["bayesian_surprise"] or 0.0) > tau)
    return {"negative": len(negative), "negative_above_tau": above}


def compare_surprise(base: Mapping[str, Any], arm: Mapping[str, Any], tau: float | None = None) -> dict[str, Any]:
    common = sorted(set(base) & set(arm))
    fields = ("predictive_surprise", "bayesian_surprise", "surprise_direction", "fsrs_interval_factor")
    changed = [k for k in common if any(base[k][f] != arm[k][f] for f in fields)]
    transitions = Counter(f"{base[k]['surprise_direction']}->{arm[k]['surprise_direction']}" for k in common
                          if base[k]["surprise_direction"] != arm[k]["surprise_direction"])
    return {
        "rows": len(arm), "rows_baseline": len(base), "changed": len(changed),
        "direction_changed": sum(transitions.values()), "direction_transitions": dict(sorted(transitions.items())),
        "directions": dict(sorted(Counter(str(v["surprise_direction"]) for v in arm.values()).items())),
        "gate_rule": _negative(arm, tau), "gate_rule_baseline": _negative(base, tau),
        "interval_factor_changed": sum(1 for k in common
                                       if base[k]["fsrs_interval_factor"] != arm[k]["fsrs_interval_factor"]),
        "predictive_surprise": _summary([v["predictive_surprise"] for v in arm.values()]),
        "expected_correctness": _summary([v["expected_correctness"] for v in arm.values()]),
        "delta_expected_correctness": _summary([arm[k]["expected_correctness"] - base[k]["expected_correctness"]
                                                for k in common if arm[k]["expected_correctness"] is not None
                                                and base[k]["expected_correctness"] is not None]),
        "delta_predictive_surprise": _summary([arm[k]["predictive_surprise"] - base[k]["predictive_surprise"]
                                               for k in common if arm[k]["predictive_surprise"] is not None
                                               and base[k]["predictive_surprise"] is not None]),
        "delta_bayesian_surprise": _summary([arm[k]["bayesian_surprise"] - base[k]["bayesian_surprise"]
                                             for k in common if arm[k]["bayesian_surprise"] is not None
                                             and base[k]["bayesian_surprise"] is not None]),
    }


def _parse(value: Any) -> datetime | None:
    from learnloop.clock import parse_utc

    return parse_utc(str(value)) if value else None


def compare_due(base: Mapping[str, Any], arm: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for projection in ("practice_item_state", "activity_card_state"):
        old, new = base[projection], arm[projection]
        shifts = []
        for key in sorted(set(old) & set(new)):
            a, b = _parse(old[key]), _parse(new[key])
            if a is not None and b is not None and a != b:
                shifts.append((b - a).total_seconds() / 86400.0)
        out[projection] = {"rows": len(new), "moved": len(shifts), "earlier": sum(1 for s in shifts if s < 0),
                           "later": sum(1 for s in shifts if s > 0), "shift_days": _summary(shifts),
                           "abs_shift_days": _summary([abs(s) for s in shifts])}
    return out


def _ranks(order: Sequence[str], keep: set[str]) -> dict[str, int]:
    kept = [item for item in order if item in keep]
    return {item: rank for rank, item in enumerate(kept)}


def _spearman(x: Mapping[str, int], y: Mapping[str, int]) -> float | None:
    keys = sorted(x)
    n = len(keys)
    if n < 2:
        return None
    d2 = sum((x[k] - y[k]) ** 2 for k in keys)
    return round(1.0 - 6.0 * d2 / (n * (n * n - 1)), 6)


def _kendall(x: Mapping[str, int], y: Mapping[str, int]) -> float | None:
    keys = sorted(x)
    n = len(keys)
    if n < 2:
        return None
    score = 0
    for i in range(n):
        for j in range(i + 1, n):
            a = x[keys[i]] - x[keys[j]]
            b = y[keys[i]] - y[keys[j]]
            score += (a > 0) - (a < 0) if b == 0 else ((a > 0) - (a < 0)) * ((b > 0) - (b < 0))
    return round(score / (n * (n - 1) / 2), 6)


def compare_queue(base: Sequence[str] | None, arm: Sequence[str] | None, top_k: Sequence[int]) -> dict[str, Any]:
    if base is None or arm is None:
        return {"available": False}
    common = set(base) & set(arm)
    rx, ry = _ranks(base, common), _ranks(arm, common)
    out: dict[str, Any] = {"available": True, "length": len(arm), "length_baseline": len(base),
                           "entered": len(set(arm) - set(base)), "left": len(set(base) - set(arm)),
                           "common": len(common), "same_order": list(base) == list(arm),
                           "spearman_common": _spearman(rx, ry), "kendall_common": _kendall(rx, ry), "top_k": {}}
    for k in top_k:
        a, b = set(base[:k]), set(arm[:k])
        out["top_k"][str(k)] = {"overlap": len(a & b), "entered": len(b - a), "left": len(a - b),
                                "size": len(b), "size_baseline": len(a)}
    return out


# -- the run -------------------------------------------------------------------------------------------------------

def _database_digests(root: Path) -> dict[str, str]:
    """SHA-256 of every database under ``root``, its main file followed by its ``-wal`` (the input-untouched
    proof). A read-only open of a WAL database creates an empty ``-wal`` and a ``-shm``, so a missing ``-wal``
    and an empty one digest the same, and the ``-shm`` (an index of the ``-wal``, never content) is left out."""

    from learnloop.db.copies import is_companion_file_name, is_database_file_name

    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_companion_file_name(path.name) or not is_database_file_name(path.name):
            continue
        digest = hashlib.sha256()
        for part in (path, path.with_name(path.name + "-wal")):
            if not part.is_file():
                continue
            with part.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
        digests[str(path.relative_to(root))] = digest.hexdigest()
    return digests


def _refuse_live_vault(root: Path) -> None:
    home = Path.home()
    for name in ("learnloop-vaults", "learnloop-retired"):
        try:
            root.resolve().relative_to((home / name).resolve())
        except ValueError:
            continue
        raise SystemExit(f"refusing a live vault under ~/{name}: run on a backup-API copy")


def run_four_way(
    vault_copy: Path,
    *,
    as_of: datetime,
    top_k: Sequence[int] = (10,),
    scratch_root: Path | None = None,
    ad_without_z_llm: bool = False,
    arms: Sequence[Arm] = ARMS,
    on_arm: Callable[[str, Any], None] | None = None,
) -> dict[str, Any]:
    """Every arm on its own scratch replay; the comparisons against (a); AD's scoring. ``on_arm(name, result)``
    sees each arm's shadow result (the tests' hook)."""

    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.substrate.shadow_rebuild import shadow_rebuild
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault_copy = Path(vault_copy).resolve()
    _refuse_live_vault(vault_copy)
    if arms[0].name != BASELINE:
        raise ValueError("the first arm must be the baseline, a_today")
    input_before = _database_digests(vault_copy)
    with tempfile.TemporaryDirectory(prefix="difficulty-four-way-", dir=scratch_root) as scratch:
        root = Path(scratch) / "vault"
        copy_tree_with_databases(vault_copy, root)
        vault = load_vault(root, load_environment=False)
        live_path = VaultPaths(vault.root, vault.config).sqlite_path.resolve()
        from learnloop.db.connection import connect

        with closing(connect(live_path, read_only=True)) as connection:
            receipts = receipt_predictions(connection)
        tau = float(vault.config.scheduler.followup.tau_followup_nats)
        shared: dict[str, Any] = {}
        states: dict[str, Any] = {}
        meta: dict[str, Any] = {}
        for arm in arms:
            def observe(loaded: Any, repository: Any, arm: Arm = arm) -> Any:
                if Path(repository.sqlite_path).resolve() == live_path:
                    return None  # the stored side: each arm is compared with (a)'s replay, never with it
                events, settings = _load_ad_events(loaded, repository)
                from learnloop.adaptive_difficulty.replay import events_fingerprint

                fingerprint = events_fingerprint(events)
                if arm.name == BASELINE:
                    # AD's events read the ledgers, receipts and content, never mastery or surprise, so (a)'s
                    # replay gives every arm's predictive (each arm's fingerprint below checks that).
                    source = _without_z_llm(events) if ad_without_z_llm else events
                    shared["predictive"] = ad_predictive(source, settings)
                    shared["scoring"] = ad_scoring(events, settings)
                    shared["ad_enabled"] = _ad_enabled(loaded.config)
                    shared["ad_summary"] = dict(events.summary)
                return {"state": read_replayed(loaded, repository, as_of=as_of), "ad_events": fingerprint}

            if arm.surprise_source is not None:
                source, fallback = ((receipts, "mastery") if arm.surprise_source == RECEIPT
                                    else (shared["predictive"], "default"))
                with surprise_from_ad(source, fallback=fallback) as log:
                    result = shadow_rebuild(vault, assignments=arm.assignments, observe=observe)
                patch = {"tiers": dict(sorted(log.tiers.items())), "outside_grade": log.outside_grade}
            else:
                result = shadow_rebuild(vault, assignments=arm.assignments, observe=observe)
                patch = None
            if not result.live_database_unchanged:  # pragma: no cover - shadow_rebuild raises first
                raise RuntimeError("the scratch vault's database changed during a shadow replay")
            if on_arm is not None:
                on_arm(arm.name, result)
            states[arm.name] = result.observed_after["state"]
            meta[arm.name] = {"description": arm.description, "applied_overrides": dict(result.applied_overrides),
                              "surprise_from_ad": arm.surprise_from_ad, "surprise_source": arm.surprise_source,
                              "surprise_patch": patch,
                              "ad_events_fingerprint": result.observed_after["ad_events"],
                              "replayed_attempts": result.rebuild.replayed_attempts}
        algorithm_version = vault.config.algorithms.algorithm_version
        interval_factor_removed = bool(vault.config.scheduler.surprise.remove_interval_factor)
    input_after = _database_digests(vault_copy)
    if input_after != input_before:
        moved = sorted(k for k in set(input_before) | set(input_after) if input_before.get(k) != input_after.get(k))
        raise RuntimeError(f"the input vault's databases changed during the replay: {moved}")

    base = states[BASELINE]
    comparisons = {}
    for arm in arms[1:]:
        state = states[arm.name]
        comparisons[arm.name] = {
            "mastery": compare_mastery(base["mastery"], state["mastery"]),
            "surprise": compare_surprise(base["surprise"], state["surprise"], tau),
            "due": compare_due(base["due"], state["due"]),
            "queue": compare_queue(base["queue"], state["queue"], top_k),
        }
    predictive = shared.get("predictive", {})
    fingerprints = {meta[a.name]["ad_events_fingerprint"] for a in arms}
    return {
        "version": REPORT_VERSION,
        "as_of": as_of.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "algorithm_version": algorithm_version,
        "interval_factor_removed": interval_factor_removed,
        "top_k": list(top_k),
        "ad_without_z_llm_in_predictive": ad_without_z_llm,
        "input_databases_unchanged": True,
        "input_database_digests": input_before,
        "arms": meta,
        "baseline": {
            "mastery": compare_mastery(base["mastery"], base["mastery"]),
            "surprise_rows": len(base["surprise"]),
            "queue_length": None if base["queue"] is None else len(base["queue"]),
            "queue_error": base["queue_error"],
        },
        "comparisons": comparisons,
        "receipts": {
            "tiers": dict(sorted(Counter(r.tier for r in receipts.values()).items())),
            "fallback_reasons": dict(sorted(Counter(r.reason for r in receipts.values()
                                                    if r.tier != "receipt").items())),
            "forecasters": dict(sorted(Counter(r.reason for r in receipts.values() if r.tier == "receipt").items())),
            "against_prefix": receipt_against_prefix(receipts, predictive),
            "per_attempt": {k: {"p": v.p, "tier": v.tier, "reason": v.reason} for k, v in sorted(receipts.items())},
        },
        "ad": {
            "enabled": shared.get("ad_enabled"),
            "events_identical_across_arms": len(fingerprints) == 1,
            "events_summary": shared.get("ad_summary"),
            "predictive_tiers": dict(sorted(Counter(p.tier for p in predictive.values()).items())),
            "predictive": {k: {"p": v.p, "tier": v.tier, "reason": v.reason} for k, v in sorted(predictive.items())},
            "scoring": shared.get("scoring"),
        },
        "values": {name: states[name] for name in states},
    }


def _ad_enabled(config: Any) -> bool:
    from learnloop.adaptive_difficulty.switches import ad_enabled

    return bool(ad_enabled(config))


# -- stdout: counts and summary statistics only --------------------------------------------------------------------

def _fmt(summary: Mapping[str, Any] | None, key: str = "median") -> str:
    if not summary or not summary.get("n"):
        return "n=0"
    return f"n={summary['n']} mean={summary['mean']:+.4f} {key}={summary[key]:+.4f} max={summary['max']:+.4f}"


def summary_lines(report: Mapping[str, Any]) -> list[str]:
    """What stdout may show: counts and summary statistics, never an id or item text."""

    lines = [f"difficulty four-way replay ({report['version']}) at {report['algorithm_version']}; "
             f"interval factor removed: {report['interval_factor_removed']}; input databases unchanged: "
             f"{report['input_databases_unchanged']}"]
    base = report["baseline"]
    lines.append(f"a_today: mastery rows {base['mastery']['rows']}, surprise rows {base['surprise_rows']}, "
                 f"queue length {base['queue_length']}" + (f" (queue unavailable: {base['queue_error']})"
                                                         if base["queue_error"] else ""))
    for name, entry in report["comparisons"].items():
        m, s, d, q = entry["mastery"], entry["surprise"], entry["due"], entry["queue"]
        items = d["practice_item_state"]
        cards = d["activity_card_state"]
        lines.append(f"{name}: mastery changed {m['changed']}/{m['rows']} (delta mean {_fmt(m['delta_logit_mean'])}; "
                     f"delta variance {_fmt(m['delta_logit_variance'])})")
        lines.append(f"  surprise changed {s['changed']}/{s['rows']}, direction changed {s['direction_changed']}, "
                     f"interval factor changed {s['interval_factor_changed']} "
                     f"(delta predictive {_fmt(s['delta_predictive_surprise'])})")
        lines.append(f"  due dates: items moved {items['moved']}/{items['rows']} (earlier {items['earlier']}, later "
                     f"{items['later']}, |shift| days {_fmt(items['abs_shift_days'])}); cards moved "
                     f"{cards['moved']}/{cards['rows']}")
        if q.get("available"):
            tops = ", ".join(f"top-{k} overlap {v['overlap']}/{v['size_baseline']}" for k, v in q["top_k"].items())
            lines.append(f"  queue: length {q['length']} vs {q['length_baseline']}, entered {q['entered']}, left "
                         f"{q['left']}, {tops}, spearman {q['spearman_common']}, kendall {q['kendall_common']}")
        else:
            lines.append("  queue: unavailable")
        gate = s.get("gate_rule") or {}
        base_gate = s.get("gate_rule_baseline") or {}
        lines.append(f"  negative direction {gate.get('negative')} (a: {base_gate.get('negative')}); above the "
                     f"follow-up threshold {gate.get('negative_above_tau')} (a: {base_gate.get('negative_above_tau')})")
        patch = report["arms"][name]["surprise_patch"]
        if patch is not None:
            lines.append(f"  surprise source tiers {patch['tiers']}")
    receipts = report.get("receipts") or {}
    if receipts:
        against = receipts["against_prefix"]
        lines.append(f"receipts: tiers {receipts['tiers']}, fallback reasons {receipts['fallback_reasons']}, "
                     f"forecasters {receipts['forecasters']}")
        lines.append(f"  receipt p against AD replayed to the attempt: both {against['both']}, "
                     f"|difference| {_fmt(against['abs_p_difference'])}")
    ad = report["ad"]
    lines.append(f"AD: enabled {ad['enabled']}, events identical across arms {ad['events_identical_across_arms']}, "
                 f"predictive tiers {ad['predictive_tiers']}")
    scoring = ad.get("scoring") or {}
    for variant, scores in (scoring.get("variants") or {}).items():
        overall = scores["all"]
        lines.append(f"  AD scoring {variant}: n={overall['n']} log loss {overall['log_loss']} brier {overall['brier']} "
                     f"(first attempt on the LO: n={scores['first_attempt_lo']['n']} "
                     f"log loss {scores['first_attempt_lo']['log_loss']})")
    if scoring:
        lines.append(f"  attempts carrying z_llm: {scoring['attempts_with_z_llm']}; "
                     f"|p shift| {_fmt(scoring['abs_p_shift'])}")
    return lines


def _as_of(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    parsed = _parse(value)
    if parsed is None:
        raise SystemExit(f"unreadable --as-of {value!r}")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vault_copy", type=Path, help="a backup-API copy of a vault (never a live vault)")
    parser.add_argument("--out", type=Path, required=True, help="the private JSON report (values and ids)")
    parser.add_argument("--as-of", default=None, help="the instant the due queue is read at (default: now, UTC)")
    parser.add_argument("--top-k", type=int, action="append", default=None, help="queue top-k sizes (default 10)")
    parser.add_argument("--scratch", type=Path, default=None, help="where the scratch copies go (default: TMPDIR)")
    parser.add_argument("--ad-without-z-llm", action="store_true",
                        help="arms c and d read AD's predictive with z_llm dropped")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    try:
        out.relative_to(args.vault_copy.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("--out must be outside the vault copy: the input is never written")
    report = run_four_way(args.vault_copy, as_of=_as_of(args.as_of), top_k=tuple(args.top_k or (10,)),
                          scratch_root=args.scratch, ad_without_z_llm=args.ad_without_z_llm)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    for line in summary_lines(report):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

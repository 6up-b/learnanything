"""Instruct hand-off IH4 (spec_instruct_handoff_v1 §7): what the learner said would help, in the numeric policy.

Two facts stay apart. "I would take this" is about acceptance: a request for a lesson updates TE1b's acceptance model
(``router.lesson_suggestions``, its own offset). "This would help me" is a claim that has to be checked against outcomes,
and that is this module.

**The choice model** (:class:`ChoiceState`). ``P(chosen kind | the link was used here, decision features)``, in the
acceptance model's form: per kind a Gaussian over the effects (:data:`TERMS`), AD's assumed-density step, predictions by
the same Gaussian-sigmoid mean, normalized over the kinds a decision holds. Seeded (:data:`PRIORS_VERSION`): TE1b's width on
every effect (``LS.PRIOR_SD``), each effect's centre 0 but the intercept's, which is where a kind's predictive is one in
the six offered (structural, TE1b's own construction, ``LS._centre_for``), so with nothing on record every kind has the
same probability, and a kind that was offered and passed over doesn't fall below one that was never offered. It is frozen
in each ``plan_block`` trace as a sensor (``preference``).

**What each row contributes.** One observation per preference with frozen features: the offered kinds, chosen or not. A
pick that agrees with the plan's own draw counts like any other choice among what was offered, since it says as much; it
wrote no ``learner_pick``, and only the report's agreement reads the difference. A preference with no draw (a null
``decision_id``) counts too: the model is over kinds given features and needs no draw. A row written with the switch off
froze no features and is not read.

**Not using the link is not a choice.** No row exists for a decision where the link wasn't used, and none is invented:
the model is conditional on use. So it can't say how much the learner wants what it favours, or that they were content
with what was served, and the served action is never an implicit choice. Its limit: use is itself selected (the link is
more likely used when something feels wrong), so it under-represents what the learner would have accepted silently.

**Entering the value.** ``Ṽ = V_tail + ŵ·V_residual + w_pref·V_pref``. ``V_pref`` is the frozen probability of each
candidate's kind on the tail's own scale (:func:`scaled`): standardized over the decision's candidates and multiplied by the
spread of their ``Q̄``. So ``w_pref`` is dimensionless, as ``ŵ`` is: at 1, one spread of the learner's model is worth one
spread of the tail's, and the most the coefficient can do. That is what makes RO6's labelled prior on a share
(``residual_weight_prior_sd``) and its clip to ``[0, 1]`` mean the same here, with no new number; read in raw probability
they would claim that a preference could be worth a whole use, and a simulated null moved the choice. ``w_pref`` is one
coefficient, from :func:`learned_tail.residual_weight` with RO6's prior, slope, rank, clip and least favourable fill. Its
data are the mix's own draws, never a pick: at a decision with a frozen sensor, with ``π`` the exact served distribution,
``d(a) = V_pref(a) − Σ_b π(b)·V_pref(b)``, the served action's ``Ĉ = d(A)·Ĝ`` has
``E[Ĉ | x] = Σ_a π(a)·d(a)·G(a)``. So under ``G(a) = c(x) + α·Q_tail(a) + b·V_pref(a)``, ``E[Ĉ | x] = α·Σπ·d·Q_tail +
b·Σπ·d²``: the state's level ``c(x)`` cancels and ``b`` is ``residual_weight``'s slope, with no intercept. ``Ĝ`` is RO6's
window return observed through the randomized checks, each term ``Y − m⁰``, a cold outcome less its frozen forecast
(``scores.observed_returns``, with its missing terms bounded). The cohort is fixed before the draw (a frozen sensor with
something on record, some spread under ``π``, a closed window).

**What ``w_pref`` can and can't identify.** It is fitted only on rows that are not self-selected: ``learner_pick`` decisions
have no trace and no propensity, so no pick is in its cohort, and a drawn decision the learner then overrode stays in it as
what was drawn (intention to treat; dropping it would select on what the draw led to). It can say: where the mix happened to
draw a kind the learner's choices favour, cold outcomes beat the tail's forecast by this share of the tail's own spread. It
can't say whether a pick works, whether following the learner works because they asked, or whether one kind differs from
another (one coefficient for all). It only sees actions the mix gave some probability, and its scale is the window's return,
not the cutoff's. With no sensor on record, or windows still open, it is exactly 0.

A leaf over the vault's tables and the router objective's modules; numpy and the standard library.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import json
import logging
import math
from typing import Any

import numpy as np

from learnloop.adf_numeric import adf_update, gaussian_sigmoid_mean, sigmoid
from learnloop.clock import parse_utc
from learnloop.db.stores import router as router_store
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import tail_data as TD

LOG = logging.getLogger(__name__)

VERSION = "ih4_preference_value_v1"
WEIGHT_VERSION = "ih4_w_pref_slope_rank_v1"
#: The model's form and its features (a changed prior set is a new version, as TE1b's).
CHOICE_VERSION = "choice_model_v1"
PRIORS_VERSION = "choice_priors_v1"
#: What a preference's ``offered_json`` froze for this model.
FEATURES_KEY = "choice_features"

LESSON, QUESTION, REVIEW, NEW, READ, STOP = LS.LESSON_KIND, "question", "review", "new", "read", "stop"
#: The kinds, in the order they are shown. Plain words for each are in :data:`WORDS`.
KINDS: tuple[str, ...] = (QUESTION, REVIEW, NEW, READ, LESSON, STOP)
WORDS: Mapping[str, str] = {
    QUESTION: "Another question",
    REVIEW: "Review something from earlier",
    NEW: "Something new",
    READ: "Read the source",
    LESSON: "Learn this",
    STOP: "Stop for today",
}
#: The effects, in order. Each is 0 at the reference (no time of day aside, a lesson fits in the minutes left, nothing
#: missed), as TE1b's context.
TERMS: tuple[str, ...] = ("intercept", "hour_sin", "hour_cos", "minutes_short", "last_miss")
_LESSON_SUBTYPE = "lesson_offer"


def kind_of(*, reading: Any, subtype: str | None, lane: str | None) -> str:
    """The plain kind of a block: a lesson offer, a reading, new material, a review, or another question (repair and
    push practice). A description of the block, never a rule that picks one."""

    if reading is not None:
        return READ
    if subtype == _LESSON_SUBTYPE:
        return LESSON
    if lane == "new":
        return NEW
    if lane == "maintain":
        return REVIEW
    return QUESTION


# -- the features ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Features:
    """What the choice model reads at a decision and froze at a preference: one function at both."""

    local_hour: float
    minutes_left: float | None
    last_miss: float

    def vector(self) -> np.ndarray:
        angle = 2.0 * math.pi * (float(self.local_hour) % 24.0) / 24.0
        short = 0.0
        if self.minutes_left is not None:
            short = min(max(float(self.minutes_left), 0.0), float(LS.CARD_MINUTES)) / float(LS.CARD_MINUTES) - 1.0
        return np.array([1.0, math.sin(angle), math.cos(angle), short, float(self.last_miss)], dtype=np.float64)

    def as_dict(self) -> dict[str, Any]:
        return {"local_hour": float(self.local_hour),
                "minutes_left": None if self.minutes_left is None else round(float(self.minutes_left), 6),
                "last_miss": round(float(self.last_miss), 6)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Features":
        minutes = value.get("minutes_left")
        return cls(local_hour=float(value.get("local_hour") or 0.0), minutes_left=None if minutes is None else float(minutes),
                   last_miss=float(value.get("last_miss") or 0.0))


def _local_hour(at: str) -> float:
    moment = parse_utc(at)
    return float(moment.astimezone().hour) if moment is not None else 0.0


def features_at(connection: Any, config: Any, *, at: str, minutes_left: float | None) -> Features:
    """The features at ``at``: its local hour (read at hour resolution, as a lesson offer's context), the plan's minutes
    left, and how far the latest graded answer known by then fell short (0 with none; through THE availability
    predicate). A number for a learned effect: nothing here picks an action."""

    from learnloop.router_objective_switches import attempt_time_sql

    known = attempt_time_sql(config, connection)
    row = connection.execute(
        f"SELECT correctness FROM practice_attempts WHERE attempt_type != 'self_report' AND {known} <= ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (at,)).fetchone()
    latest = float(row[0]) if row is not None and row[0] is not None else 1.0
    return Features(local_hour=_local_hour(at), minutes_left=minutes_left, last_miss=max(1.0 - latest, 0.0))


# -- the choice model -----------------------------------------------------------------------------------------------


def _prior() -> tuple[np.ndarray, np.ndarray]:
    """One kind's seeded Gaussian. At the reference ``h·θ`` has the intercept's and the time of day's variance
    (``sin² + cos² = 1``), as TE1b's: its intercept is centred where a kind's predictive is ``1/len(KINDS)``."""

    mean = np.zeros(len(TERMS), dtype=np.float64)
    mean[TERMS.index("intercept")] = LS._centre_for(1.0 / len(KINDS), 2.0 * LS.PRIOR_SD ** 2)
    return mean, np.eye(len(TERMS), dtype=np.float64) * LS.PRIOR_SD ** 2


@dataclass
class ChoiceState:
    """The model's posterior as of some instant: per kind, the effects' Gaussian."""

    kinds: dict[str, tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)
    updates: int = 0

    def observe(self, features: Features, offered: Sequence[str], chosen: str) -> None:
        """One use of the link: the chosen kind and each other offered kind, one step each."""

        h = features.vector()
        for kind in sorted({*offered, chosen}):
            y = 1.0 if kind == chosen else 0.0

            def log_lik(eta: np.ndarray, y: float = y) -> np.ndarray:
                p = np.clip(sigmoid(eta), 1e-12, 1.0 - 1e-12)
                return y * np.log(p) + (1.0 - y) * np.log(1.0 - p)

            mean, cov = self.kinds.get(kind) or _prior()
            mean, cov, _record = adf_update(mean, cov, h, log_lik)
            self.kinds[kind] = (mean, cov)
        self.updates += 1

    def predict(self, features: Features, kinds: Sequence[str]) -> dict[str, float]:
        """``P(kind | the link was used here)`` over ``kinds``: each kind's predictive, normalized over them. A kind never
        offered stays at its prior."""

        h = features.vector()
        raw: dict[str, float] = {}
        for kind in dict.fromkeys(kinds):
            mean, cov = self.kinds.get(kind) or _prior()
            raw[kind] = gaussian_sigmoid_mean(float(h @ mean), float(h @ cov @ h))
        total = sum(raw.values())
        return {kind: value / total for kind, value in raw.items()} if total > 0 else raw


def replay(rows: Sequence[Mapping[str, Any]], *, at: str | None = None) -> tuple[ChoiceState, dict[str, int]]:
    """The model as of ``at`` from ``router_learner_preferences`` rows, and what they were: ``on_record``, ``read``,
    ``no_frozen_features`` (written with the switch off), and of those read ``agreed`` and ``no_draw``."""

    state = ChoiceState()
    counts = {"on_record": 0, "read": 0, "no_frozen_features": 0, "agreed": 0, "no_draw": 0}
    for row in sorted(rows, key=lambda found: (str(found["created_at"]), str(found["id"]))):
        if at is not None and str(row["created_at"]) > at:
            continue
        counts["on_record"] += 1
        offered = json.loads(row.get("offered_json") or "{}")
        frozen = offered.get(FEATURES_KEY)
        if not isinstance(frozen, Mapping):
            counts["no_frozen_features"] += 1
            continue
        kinds = [str(option["kind"]) for option in offered.get("options") or () if option.get("kind")]
        state.observe(Features.from_dict(frozen), kinds, str(row["chosen_kind"]))
        counts["read"] += 1
        parent = row.get("decision_id")
        counts["no_draw"] += 1 if parent is None else 0
        counts["agreed"] += 1 if parent is not None and row.get("served_decision_id") == parent else 0
    return state, counts


def mark(connection: Any, config: Any) -> dict[str, Any]:
    """What a boundary's identity names so a new preference never reuses a job made before it: the ledger's size and
    latest row, or nothing (switch off, none on record, or the table absent), so every other key keeps its bytes."""

    from learnloop.router_objective_switches import preferences_inform_router_on

    if not preferences_inform_router_on(config) or not router_store.preferences_present(connection):
        return {}
    row = connection.execute("SELECT COUNT(*), MAX(created_at || ' ' || id) FROM router_learner_preferences").fetchone()
    return {"preferences": {"n": int(row[0]), "latest": row[1]}} if row and row[0] else {}


# -- w_pref ---------------------------------------------------------------------------------------------------------


def scaled(p: Mapping[str, float], q: Mapping[str, float]) -> dict[str, float]:
    """``V_pref`` per candidate: ``p`` standardized over the candidates, times the spread of their ``Q̄`` (uniform over the
    support: the mix's ``μ`` does not exist yet when the numeric policy answers, and depends on it). Zero where either has
    no spread: every candidate one kind, or the tail indifferent."""

    refs = [ref for ref in p if ref in q]
    values = np.asarray([float(p[ref]) for ref in refs], dtype=np.float64)
    tail = np.asarray([float(q[ref]) for ref in refs], dtype=np.float64)
    if not refs or values.max() == values.min() or tail.max() == tail.min():
        return dict.fromkeys(refs, 0.0)
    out = (values - values.mean()) / values.std() * tail.std()
    return {ref: float(value) for ref, value in zip(refs, out)}


def with_values(preference: Mapping[str, Any], q: Mapping[str, float]) -> dict[str, Any]:
    """The sensor with each candidate's ``V_pref`` at the evaluation that answered (the tail's ``Q̄``), frozen exactly, so
    the shift and the contrasts read one number."""

    entries = preference.get("candidates") or {}
    values = scaled({ref: float(entry["p"]) for ref, entry in entries.items()}, q)
    return {**dict(preference), "candidates": {ref: {**dict(entry), **({"v_pref": _exact(values[ref])} if ref in values else {})}
                                               for ref, entry in entries.items()}}


def frozen_values(row: Any) -> dict[str, float] | None:
    """A logged decision's frozen ``V_pref`` by ref, or None: no sensor, nothing on record then, or a candidate without
    one. Fixed before the draw, so reading it selects nothing on the outcome."""

    sensor = getattr(row, "preference", None)
    if not isinstance(sensor, Mapping) or sensor.get("status") != "applied":
        return None
    if int((sensor.get("choice") or {}).get("updates") or 0) <= 0:
        return None
    entries = sensor.get("candidates") or {}
    values = {ref: float(entries[ref]["v_pref"]) for ref in row.support
              if isinstance(entries.get(ref), Mapping) and entries[ref].get("v_pref") is not None}
    return values if values and len(values) == len(row.support) else None


def contrast(*, decision_id: str, decided_at: str, window_closes_at: str, served: str, distribution: Mapping[str, float],
             values: Mapping[str, float], tail: Mapping[str, float], found: S.Bounded) -> LT.Contrast | None:
    """One draw's contrast (module docstring): ``Ĉ = d(A)·Ĝ`` against ``Σπ·d·Q_tail`` and ``Σπ·d²``; None with no spread
    under ``π`` (every candidate one kind: nothing to test, known before the draw)."""

    if found.value is None or served not in values:
        return None
    centre = sum(float(distribution.get(ref, 0.0)) * value for ref, value in values.items())
    d = {ref: value - centre for ref, value in values.items()}
    spread = sum(float(distribution.get(ref, 0.0)) * d[ref] * d[ref] for ref in d)
    if spread <= 0.0:
        return None
    predicted = sum(float(distribution.get(ref, 0.0)) * d[ref] * float(tail[ref]) for ref in d)
    realized = d[served] * float(found.value)
    ends = sorted((d[served] * (float(found.value) + float(found.lo)), d[served] * (float(found.value) + float(found.hi))))
    missing = int(found.missing)
    return LT.Contrast(decision_id=decision_id, decided_at=decided_at, window_closes_at=window_closes_at, realized=realized,
                       tail=predicted, residual=spread, forced=True, forced_probability=1.0,
                       realized_lo=ends[0] if missing else None, realized_hi=ends[1] if missing else None,
                       missing=missing, excluded=int(found.excluded))


def contrasts(connection: Any, config: Any, rows: Sequence[Any], *, at: str) -> tuple[list[LT.Contrast], dict[str, Any]]:
    """Every logged draw with a frozen sensor whose window closed before ``at`` (:class:`tail_data.Logged` rows: the mix's
    draws only; a pick has no trace), with its missing terms bounded (RO6's landing ruling R1)."""

    eligible = [row for row in rows if frozen_values(row) is not None and row.q_tail is not None
                and row.window_closes_at and str(row.window_closes_at) < at]
    returns = S.observed_returns(connection, config, at=at, rows=TD._with_traces(connection, eligible), complete=True) \
        if eligible else {}
    out: list[LT.Contrast] = []
    no_spread = 0
    for row in eligible:
        found = returns.get(row.decision_id)
        if not isinstance(found, S.Bounded):
            found = S.Bounded(value=None, reason="window_open")
        one = contrast(decision_id=row.decision_id, decided_at=row.created_at,
                       window_closes_at=str(row.window_closes_at), served=row.served, distribution=row.served_dist,
                       values=frozen_values(row) or {}, tail=row.q_measurable or row.q_tail, found=found)
        if one is None:
            no_spread += 1
            continue
        out.append(one)
    with_missing = [one for one in out if one.missing]
    with_excluded = [one for one in out if one.excluded]
    record = {"status": "identified", "cohort": len(eligible), "assigned": {"draws": len(out)},
              "observed": {"draws": len(out)},
              "missing": {"windows": len(with_missing), "terms": sum(one.missing for one in with_missing)},
              "excluded": {"windows": len(with_excluded), "terms": sum(one.excluded for one in with_excluded)},
              "before_coin": {"no_spread_or_no_return": no_spread}}
    return out, record


def weight(connection: Any, config: Any, rows: Sequence[Any], *, at: str) -> tuple[LT.WeightFit, dict[str, Any]]:
    """``w_pref`` as of ``at``: RO6's :func:`learned_tail.residual_weight` over :func:`contrasts`, at RO6's labelled prior
    (``residual_weight_prior_sd``), with its clip to ``[0, 1]`` times ``P(rank > 0)``. The clip keeps a negative slope at
    0 rather than steering against the learner, and a unit of probability worth at most one use's whole range. With no
    contrast, exactly 0."""

    found, record = contrasts(connection, config, rows, at=at)
    return fitted(found, prior_sd=float(config.router_objective.residual_weight_prior_sd), at=at), \
        LT.calibration_summary(found, record, at=at)


def fitted(found: Sequence[LT.Contrast], *, prior_sd: float, at: str | None = None) -> LT.WeightFit:
    """:func:`learned_tail.residual_weight` over ``found``, its noise with the fit's degrees of freedom off: every row
    here is a draw, so with few of them a fit through the rows would otherwise report no noise and drop the prior."""

    fit = replace(LT.residual_weight(found, prior_sd=prior_sd, at=at, noise_dof=True), version=WEIGHT_VERSION)
    return fit if found else replace(fit, source="prior: no randomized draw with a frozen preference sensor and a "
                                                 "closed window")


# -- the decision's record ------------------------------------------------------------------------------------------


def _exact(value: float) -> str:
    """As ``tail_serve._exact``: the trace rounds every float, and the shift must recompute."""

    return repr(float(value))


def record(repository: Any, config: Any, *, kinds: Mapping[str, str], minutes_left: float | None, now_iso: str,
           fit: bool = True) -> dict[str, Any] | None:
    """A ``plan_block`` decision's sensor and ``w_pref``, or None with nothing to say (no preference with frozen features
    known at ``now_iso``), so its trace and every value are the predecessor's. ``kinds``: each candidate's kind.
    ``fit``: RO6's learned tail is on; off, ``w_pref`` is not fitted (0) and the sensor still freezes. Never raises: a
    failure leaves the policy as it was and the trace says why."""

    try:
        with repository.connection() as connection:
            state, counts = replay(router_store.learner_preference_rows(connection), at=now_iso)
            if state.updates <= 0:
                return None
            features = features_at(connection, config, at=now_iso, minutes_left=minutes_left)
            weighed: LT.WeightFit | None = None
            summary: dict[str, Any] | None = None
            if fit:
                rows = TD.logged(connection, config, at=now_iso)
                weighed, summary = weight(connection, config, rows, at=now_iso)
        p = state.predict(features, list(kinds.values()))
        return {
            "status": "applied", "version": VERSION,
            "choice": {"version": CHOICE_VERSION, "priors_version": PRIORS_VERSION, "updates": state.updates,
                       "rows": counts, "features": features.as_dict(), "p": p, "self_selected": True,
                       "basis": "conditional on the link being used: a decision where it wasn't used is no row, and "
                                "never reads as a preference for what was served"},
            "candidates": {ref: {"kind": kind, "p": _exact(p[kind])} for ref, kind in kinds.items()},
            "w_pref": float(weighed.w_hat) if weighed is not None else 0.0,
            "weight": weighed.as_dict() if weighed is not None else None, "contrasts": summary,
            "claim": "fitted only on the mix's randomized draws, never on a pick; no causal claim about following the "
                     "learner",
        }
    except Exception as exc:  # noqa: BLE001 - a sensor never blocks the numeric policy
        LOG.warning("router objective: the preference sensor was not computed", exc_info=True)
        return {"status": "failed", "version": VERSION, "error": f"{type(exc).__name__}: {str(exc)[:200]}"}


def moves_the_value(preference: Mapping[str, Any] | None) -> bool:
    """``w_pref`` has moved: only then does anything shift (at 0 the evaluation is handed on untouched, bit for bit)."""

    return isinstance(preference, Mapping) and preference.get("status") == "applied" and float(
        preference.get("w_pref") or 0.0) > 0.0


def shifted(evaluation: Any, preference: Mapping[str, Any], *, tail: Mapping[str, float]) -> Any:
    """The evaluation the numeric policy's argmax reads: each candidate's draws moved by ``w_pref·V_pref``, a constant
    per candidate, so the paired precision is the tail's (as ``tail_serve.shifted``). ``tail``: the candidates' ``Q̄``,
    which set ``V_pref``'s scale. ``Q̄`` in the trace stays the tail's."""

    w_pref = float(preference.get("w_pref") or 0.0)
    values = with_values(preference, tail)["candidates"]
    rows = tuple(replace(row, q_draws=tuple(float(q) + w_pref * float((values.get(row.ref) or {}).get("v_pref") or 0.0)
                                            for q in row.q_draws)) for row in evaluation.valued)
    return replace(evaluation, valued=rows)


__all__ = ["CHOICE_VERSION", "ChoiceState", "FEATURES_KEY", "Features", "KINDS", "LESSON", "NEW", "PRIORS_VERSION", "QUESTION",
           "READ", "REVIEW", "STOP", "TERMS", "VERSION", "WEIGHT_VERSION", "WORDS", "contrast", "contrasts", "features_at", "fitted",
           "frozen_values", "scaled", "with_values",
           "kind_of", "mark", "moves_the_value", "record", "replay", "shifted", "weight"]

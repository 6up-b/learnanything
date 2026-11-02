"""Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4).

The functional core: the acceptance model, the decline recovery and the day's
draw. Pure numerics over plain values: no vault, repository, clock or model
client (the shell is ``learnloop.daily_plan.lesson_suggestion``).

**The candidate** is ``instruct(lesson)`` on one learning object, proposed for
one of the spec's three reasons (``new_goal``: an LO on an active goal the
learner has not started; ``cold_failing``: its two latest cold checks were not
right; ``below_band``: the mastery model predicts success below adaptive
difficulty's own ``calibrate_below``). Declining costs nothing, so it is
reversible and drawn.

**The acceptance model** ``P(accept | context, candidate) = σ(h · θ)`` is a
logistic model with latent effects: a Gaussian over ``θ`` (the intercept, the
time of day as a sine and cosine pair, the share of a lesson that fits in the
minutes left, re-entry, the reason given, a suggestion shown within the last
day, and the decline depth ``D``), one Gaussian per point of the per-learner
recovery grid, the grid
weights ``W_t(R) ∝ W_{t−1}(R) · Z_t(R)`` from their seeded prior (AD's
``ad_hyper`` mechanism, as ``learner.lesson_weight`` does for τ). For a goal
the learner declined ("Not now"), the decline term is ``−D · g_R(d)`` with
``g_R(d) = max(0, 1 − log(1 + d) / log(1 + R))``: ``log(1 + days since the
Not now)`` scaled by the per-learner recovery rate ``1 / log(1 + R)`` (the grid
posterior), so the goal is muted at once and recovered after ``R`` days. Every
shown suggestion's response is one observation (accepted: 1; declined or
ignored: 0; a chosen alternative: 0 on the card's suggestion and 1 on the
alternative), entered by AD's assumed-density step
(:func:`learnloop.adf_numeric.adf_update`), in response order. Re-acceptance
after a decline is what teaches ``D`` and the grid.

**The draw** (one a day, at Today's open): each candidate's value is
``log P(accept) + log(1 − p)``, ``p`` its predicted success (room to learn;
structural, no weight), so suggestions come as often as they are predicted to
be taken. The card's suggestion is drawn from ``π ∝ exp(value)`` with the
router's own floor ``router.epsilon_min`` on each of the top ``router.k``
candidates, then shown with probability ``P(accept)`` of the drawn candidate:
shown and not-shown days are both logged, each with its exact propensity
(``π(c) · P(c)`` for a shown ``c``, ``Σ π(i) · (1 − P(i))`` for none), so
the policy is evaluated intention-to-treat on ``R_cold``
(``router.outcomes``). No per-day quota and no fixed mute length: the seeded
priors reproduce revision 3's defaults (about one a day, about a 7-day mute
after a "Not now") until the responses move them.

Every number below is a seeded prior labelled with its basis, a structural
form or numerical resolution (§18.4; registered in
``params.parameter_registry``). A changed prior is a new
:data:`PRIORS_VERSION`.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.adf_numeric import adf_update, gaussian_sigmoid_mean, normalized_log_weights, sigmoid

#: The decision row's shape (its candidates and detail JSON).
SUGGESTION_VERSION = "lesson_suggestion_v1"
#: The prior set's identity: a changed prior is a successor (the playbook).
PRIORS_VERSION = "suggestion_priors_v1"
DECISION_KIND = "lesson_suggestion"
#: The assignment mechanism (registered in ``db.stores.router.ROUTER_DESIGNS``).
DESIGN = "lesson_suggestion_draw"
POLICY = "lesson_suggestion_v1"
SURFACE = "today_card"
CANDIDATE_KIND = "instruct_lesson"
#: The day's draw showed no card.
NO_SUGGESTION = "no_suggestion"
REASONS: tuple[str, ...] = ("new_goal", "cold_failing", "below_band")
RESPONSES: tuple[str, ...] = ("accepted", "chose_alternative", "declined", "ignored")

#: The state vector, in order (``decline`` is ``D``, entered as ``−g_R(d)``).
#: Every context feature is 0 at the reference context (a lesson fits in the minutes left, or no plan
#: says otherwise; not a re-entry; a goal LO not started; no suggestion within the last day; no "Not
#: now"), so the seeded centres below are the reference context's (structural: bounded features).
TERMS: tuple[str, ...] = (
    "intercept", "hour_sin", "hour_cos", "minutes_short", "reentry",
    "reason_cold_failing", "reason_below_band", "recent_suggestion", "decline",
)

# --- seeded priors (suggestion_priors_v1; spec §18.4: basis legacy, 1.0 logit per effect) ---------
#: Revision 3's default of about one suggestion a day: with no data a card is shown on about nine
#: days in ten (basis legacy; the intercept's centre).
LEGACY_DAILY_SHOW = 0.9
#: Revision 3's "Not now" mute: a goal just declined starts at about one chance in a hundred (basis
#: legacy; with the intercept, the decline depth's centre).
LEGACY_DECLINED_SHOW = 0.01
#: Every effect's prior width (the LP spec's rule for legacy priors: >= 1 logit).
PRIOR_SD = 1.0
#: The recovery grid (days until a declined goal is back at its undeclined value): centred on
#: revision 3's 7-day mute (basis legacy), a factor of two either side at half-octave steps;
#: its weights start uniform and are learned.
RECOVERY_DAYS_GRID: tuple[float, ...] = tuple(7.0 * 2.0 ** (step / 2.0) for step in (-2, -1, 0, 1, 2))

#: Presentation (spec §19 copy, ``keep``): the card's "about 15 min".
CARD_MINUTES = 15
#: Presentation (``keep``, spec §18.4): up to two alternatives on the card.
MAX_ALTERNATIVES = 2

_SECONDS_PER_DAY = 86_400.0


def _centre_for(target: float, variance: float) -> float:
    """The logit centre ``m`` with ``E[σ(N(m, variance))] = target`` (bisection; numerical resolution)."""

    low, high = -40.0, 40.0
    for _ in range(100):
        mid = 0.5 * (low + high)
        if gaussian_sigmoid_mean(mid, variance) < target:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def _prior_mean() -> np.ndarray:
    """The seeded centres: the prior predictive reproduces the legacy targets at the reference context.

    At the reference context ``h · θ`` has the intercept's and the time of day's prior variance
    (``sin² + cos² = 1``: one effect's width, whatever the hour), so the intercept is centred where
    ``E[σ] = LEGACY_DAILY_SHOW``; a goal just declined adds the decline depth's variance, and ``D`` is
    centred where ``E[σ] = LEGACY_DECLINED_SHOW``."""

    variance = 2.0 * PRIOR_SD ** 2
    intercept = _centre_for(LEGACY_DAILY_SHOW, variance)
    declined = _centre_for(LEGACY_DECLINED_SHOW, variance + PRIOR_SD ** 2)
    mean = np.zeros(len(TERMS), dtype=np.float64)
    mean[TERMS.index("intercept")] = intercept
    mean[TERMS.index("decline")] = intercept - declined
    return mean


@dataclass
class _Bank:
    """One recovery grid point's Gaussian over the effects."""

    recovery_days: float
    mean: np.ndarray
    cov: np.ndarray
    log_w: float = 0.0


@dataclass(frozen=True)
class Context:
    """The day's draw context (stored on the decision row, read back by replay)."""

    local_hour: float
    minutes_left: float | None
    reentry: bool
    days_since_last: float | None

    def as_dict(self) -> dict[str, Any]:
        return {"local_hour": round(float(self.local_hour), 6),
                "minutes_left": None if self.minutes_left is None else round(float(self.minutes_left), 6),
                "reentry": bool(self.reentry),
                "days_since_last": None if self.days_since_last is None else round(float(self.days_since_last), 6)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Context":
        minutes = value.get("minutes_left")
        days = value.get("days_since_last")
        return cls(local_hour=float(value.get("local_hour") or 0.0),
                   minutes_left=None if minutes is None else float(minutes),
                   reentry=bool(value.get("reentry")),
                   days_since_last=None if days is None else float(days))


@dataclass(frozen=True)
class Candidate:
    """One ``instruct(lesson)`` candidate."""

    ref: str
    learning_object_ids: tuple[str, ...]
    reason: str
    predicted_success: float | None
    #: Days since the learner's latest "Not now" on this goal (None: none since its last acceptance).
    days_since_decline: float | None = None
    title: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"ref": self.ref, "kind": CANDIDATE_KIND, "learning_object_ids": list(self.learning_object_ids),
                "reason": self.reason, "title": self.title,
                "predicted_success": None if self.predicted_success is None else round(float(self.predicted_success), 6),
                "days_since_decline": (None if self.days_since_decline is None
                                       else round(float(self.days_since_decline), 6))}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Candidate":
        p = value.get("predicted_success")
        d = value.get("days_since_decline")
        return cls(ref=str(value["ref"]), learning_object_ids=tuple(str(x) for x in value.get("learning_object_ids") or ()),
                   reason=str(value.get("reason") or "new_goal"),
                   predicted_success=None if p is None else float(p),
                   days_since_decline=None if d is None else float(d), title=str(value.get("title") or ""))


def lesson_ref(learning_object_id: str) -> str:
    return f"lesson:{learning_object_id}"


def decline_shape(days: float | None, recovery_days: float) -> float:
    """``g_R(d)``: 1 at the "Not now", 0 from ``R`` days on (``log(1 + d)`` against ``log(1 + R)``)."""

    if days is None:
        return 0.0
    return max(0.0, 1.0 - math.log1p(max(float(days), 0.0)) / math.log1p(float(recovery_days)))


def design_vector(context: Context, candidate: Candidate, recovery_days: float) -> np.ndarray:
    """``h`` for one candidate in one context at one recovery grid point."""

    angle = 2.0 * math.pi * (float(context.local_hour) % 24.0) / 24.0
    h = np.zeros(len(TERMS), dtype=np.float64)
    h[TERMS.index("intercept")] = 1.0
    h[TERMS.index("hour_sin")] = math.sin(angle)
    h[TERMS.index("hour_cos")] = math.cos(angle)
    if context.minutes_left is not None:
        fits = min(max(float(context.minutes_left), 0.0), float(CARD_MINUTES)) / float(CARD_MINUTES)
        h[TERMS.index("minutes_short")] = fits - 1.0
    h[TERMS.index("reentry")] = 1.0 if context.reentry else 0.0
    h[TERMS.index("reason_cold_failing")] = 1.0 if candidate.reason == "cold_failing" else 0.0
    h[TERMS.index("reason_below_band")] = 1.0 if candidate.reason == "below_band" else 0.0
    if context.days_since_last is not None:
        h[TERMS.index("recent_suggestion")] = min(max(float(context.days_since_last), 0.0), 1.0) - 1.0
    h[TERMS.index("decline")] = -decline_shape(candidate.days_since_decline, recovery_days)
    return h


@dataclass
class AcceptanceState:
    """The acceptance model's posterior as of some instant."""

    banks: list[_Bank] = field(default_factory=lambda: [
        _Bank(recovery_days=r, mean=_prior_mean(), cov=np.eye(len(TERMS)) * PRIOR_SD ** 2)
        for r in RECOVERY_DAYS_GRID])
    updates: int = 0

    def weights(self) -> np.ndarray:
        return normalized_log_weights(np.array([bank.log_w for bank in self.banks]))

    def p_accept(self, context: Context, candidate: Candidate) -> float:
        """The posterior predictive ``P(accept)``: the grid mixture of ``E[σ(h · θ)]``."""

        total = 0.0
        for weight, bank in zip(self.weights(), self.banks):
            h = design_vector(context, candidate, bank.recovery_days)
            total += float(weight) * gaussian_sigmoid_mean(float(h @ bank.mean), float(h @ bank.cov @ h))
        return min(max(total, 0.0), 1.0)

    def observe(self, context: Context, candidate: Candidate, accepted: bool) -> None:
        """One response: AD's assumed-density step in every bank, the grid weights by ``log Z``."""

        y = 1.0 if accepted else 0.0

        def log_lik(eta: np.ndarray) -> np.ndarray:
            p = np.clip(sigmoid(eta), 1e-12, 1.0 - 1e-12)
            return y * np.log(p) + (1.0 - y) * np.log(1.0 - p)

        for bank in self.banks:
            h = design_vector(context, candidate, bank.recovery_days)
            bank.mean, bank.cov, record = adf_update(bank.mean, bank.cov, h, log_lik)
            bank.log_w += record.log_z
        self.updates += 1

    def summary(self) -> dict[str, Any]:
        """Posterior means (grid-weighted) and the recovery grid's weights, for the decision row."""

        weights = self.weights()
        mean = sum(float(w) * bank.mean for w, bank in zip(weights, self.banks))
        return {"priors_version": PRIORS_VERSION, "updates": self.updates,
                "means": {term: round(float(value), 6) for term, value in zip(TERMS, mean)},
                "recovery_days": [round(bank.recovery_days, 6) for bank in self.banks],
                "recovery_weights": [round(float(w), 6) for w in weights]}


# =============================================================================
# Replay: the observations a response ledger gives
# =============================================================================


@dataclass(frozen=True)
class Observation:
    context: Context
    candidate: Candidate
    accepted: bool
    at: str


def observations(decisions: Mapping[str, Mapping[str, Any]],
                 responses: Iterable[Mapping[str, Any]]) -> list[Observation]:
    """The acceptance observations of a response ledger, in response order.

    ``decisions`` maps a decision id to its stored draw (``detail_json`` parsed:
    ``context`` and ``card`` with the shown candidates' inputs); ``responses``
    are ``router_suggestion_responses`` rows. Each candidate enters with the
    inputs stored at its draw, so a replay never depends on today's state."""

    out: list[Observation] = []
    for response in sorted(responses, key=lambda row: (str(row["responded_at"]), str(row["id"]))):
        detail = decisions.get(str(response["decision_id"]))
        if not detail:
            continue
        context = Context.from_dict(detail.get("context") or {})
        card = detail.get("card") or {}
        shown = [Candidate.from_dict(entry) for entry in card.get("candidates") or ()]
        if not shown:
            continue
        primary, by_ref = shown[0], {candidate.ref: candidate for candidate in shown}
        kind, at = str(response["response"]), str(response["responded_at"])
        if kind == "accepted":
            out.append(Observation(context, primary, True, at))
        elif kind == "chose_alternative":
            out.append(Observation(context, primary, False, at))
            chosen = by_ref.get(str(response["candidate_ref"]))
            if chosen is not None and chosen.ref != primary.ref:
                out.append(Observation(context, chosen, True, at))
        elif kind in ("declined", "ignored"):
            out.append(Observation(context, primary, False, at))
    return out


def replay(observed: Iterable[Observation]) -> AcceptanceState:
    state = AcceptanceState()
    for observation in observed:
        state.observe(observation.context, observation.candidate, observation.accepted)
    return state


def declines_by_learning_object(decisions: Mapping[str, Mapping[str, Any]],
                                responses: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Per LO, the time of its latest "Not now" not followed by an acceptance of a lesson on it."""

    latest: dict[str, str] = {}
    for response in sorted(responses, key=lambda row: (str(row["responded_at"]), str(row["id"]))):
        los = json.loads(response.get("learning_object_ids_json") or "[]") if isinstance(
            response.get("learning_object_ids_json"), str) else list(response.get("learning_object_ids") or ())
        kind = str(response["response"])
        for lo in los:
            if kind == "declined":
                latest[str(lo)] = str(response["responded_at"])
            elif kind in ("accepted", "chose_alternative"):
                latest.pop(str(lo), None)
    return latest


# =============================================================================
# The draw
# =============================================================================


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: Candidate
    p_accept: float
    room: float
    value: float
    pi: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {**self.candidate.as_dict(), "p_accept": round(self.p_accept, 12), "room": round(self.room, 12),
                "value": round(self.value, 12), "pi": round(self.pi, 12)}


@dataclass(frozen=True)
class Draw:
    scored: tuple[ScoredCandidate, ...]
    drawn: ScoredCandidate
    shown: bool
    alternatives: tuple[ScoredCandidate, ...]
    propensity: float
    propensity_kind: str
    p_no_card: float
    seed: str
    ceiling_bound: bool = False

    @property
    def chosen_ref(self) -> str:
        return self.drawn.candidate.ref if self.shown else NO_SUGGESTION


def score(state: AcceptanceState, context: Context, candidates: Sequence[Candidate], *, k: int) -> list[ScoredCandidate]:
    """Each candidate's ``P(accept)``, room and value; the top ``k`` by value (ties by ref)."""

    scored = []
    for candidate in candidates:
        p = state.p_accept(context, candidate)
        room = 1.0 if candidate.predicted_success is None else min(max(1.0 - float(candidate.predicted_success), 0.0), 1.0)
        value = math.log(max(p, 1e-300)) + math.log(max(room, 1e-300))
        scored.append(ScoredCandidate(candidate, p, room, value))
    scored.sort(key=lambda s: (-s.value, s.candidate.ref))
    return scored[:max(int(k), 1)]


def seed_for(day: str, snapshot_hash: str) -> str:
    return hashlib.sha256(f"{SUGGESTION_VERSION}|{day}|{snapshot_hash}".encode("utf-8")).hexdigest()


def _uniforms(seed: str) -> tuple[float, float]:
    return int(seed[:16], 16) / float(1 << 64), int(seed[16:32], 16) / float(1 << 64)


def _propensity(p: float) -> tuple[float, str]:
    if p >= 1.0 - 1e-12:
        return 1.0, "deterministic"
    return p, "exact"


def draw(scored: Sequence[ScoredCandidate], *, epsilon: float, seed: str, ceiling_bound: bool = False) -> Draw:
    """The day's draw over ``scored`` (non-empty): ``π`` with the router's floor, then the show coin.

    ``ceiling_bound``: the anti-nagging ceiling binds (``keep``), so no card is
    shown whatever the draw (logged with a deterministic propensity)."""

    if not scored:
        raise ValueError("a draw needs a candidate")
    n = len(scored)
    top = max(s.value for s in scored)
    w = np.array([math.exp(s.value - top) for s in scored], dtype=np.float64)
    floor = float(epsilon) if n * float(epsilon) < 1.0 else 1.0 / n
    pi = (1.0 - n * floor) * w / w.sum() + floor
    pi = pi / pi.sum()
    with_pi = tuple(ScoredCandidate(s.candidate, s.p_accept, s.room, s.value, float(p)) for s, p in zip(scored, pi))
    u_draw, u_show = _uniforms(seed)
    index = int(np.searchsorted(np.cumsum(pi), u_draw, side="right"))
    index = min(index, n - 1)
    drawn = with_pi[index]
    p_no_card = float(sum(s.pi * (1.0 - s.p_accept) for s in with_pi))
    if ceiling_bound:
        return Draw(with_pi, drawn, False, (), 1.0, "deterministic", 1.0, seed, ceiling_bound=True)
    shown = u_show < drawn.p_accept
    if shown:
        propensity, kind = _propensity(drawn.pi * drawn.p_accept)
        others = sorted((s for s in with_pi if s.candidate.ref != drawn.candidate.ref),
                        key=lambda s: (-s.pi, s.candidate.ref))
        alternatives = tuple(others[:MAX_ALTERNATIVES])
    else:
        propensity, kind = _propensity(p_no_card)
        alternatives = ()
    return Draw(with_pi, drawn, shown, alternatives, propensity, kind, p_no_card, seed)


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def days_between(later: Any, earlier: Any) -> float:
    """Days between two aware datetimes (never negative)."""

    return max((later - earlier).total_seconds() / _SECONDS_PER_DAY, 0.0)


__all__ = [
    "AcceptanceState",
    "CANDIDATE_KIND",
    "CARD_MINUTES",
    "Candidate",
    "Context",
    "DECISION_KIND",
    "DESIGN",
    "Draw",
    "MAX_ALTERNATIVES",
    "NO_SUGGESTION",
    "Observation",
    "POLICY",
    "PRIORS_VERSION",
    "REASONS",
    "RECOVERY_DAYS_GRID",
    "RESPONSES",
    "SURFACE",
    "SUGGESTION_VERSION",
    "ScoredCandidate",
    "canonical_hash",
    "days_between",
    "decline_shape",
    "declines_by_learning_object",
    "design_vector",
    "draw",
    "lesson_ref",
    "observations",
    "replay",
    "score",
    "seed_for",
]

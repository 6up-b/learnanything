"""Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4).

The functional core: the acceptance model, the decline recovery and the day's
draw. Pure numerics over plain values: no vault, repository, clock or model
client (the shell is ``learnloop.daily_plan.lesson_suggestion``).

**The candidate** is ``instruct(lesson)`` on one learning object, proposed for
one of the spec's three reasons (``new_goal``: an LO on an active goal the
learner has not started; ``cold_failing``: its two latest cold checks were not
right (from instruct hand-off's mvp-0.55, with the owner's decision 4, ``cold_missed``: any cold check
since its last lesson was not fully right, with no threshold on its size, count or error type);
``below_band``: adaptive difficulty's posterior predicts the learner
below its practice band, by AD's own out-of-band rule on ``P_band``). Declining costs nothing, so it is
reversible and drawn.

**The acceptance model** ``P(accept | context, candidate) = σ(h · θ)`` is a
logistic model with latent effects: a Gaussian over ``θ`` (the intercept, the
time of day as a sine and cosine pair, the share of a lesson that fits in the
minutes left, re-entry, the reason given, the days since the last suggestion
(:func:`spacing_feature`), and the decline depth ``D``), one Gaussian per point of the per-learner
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
be taken. The staged rule's pick is the top value. The card's target is drawn
the router's way (spec §15.1, codex re-review F5): in ``router.mode =
"mixture"`` by the router's own ``model_mixture`` over the top ``router.k``
(:func:`mixture_target`: :mod:`learnloop.router.mixture`, the configured
``router.weights`` and the ``router.epsilon_min`` floor each; the Decider and
the router LLM are not asked about lesson candidates, so their weight goes to
the staged rule as for any model not set up, G7, and the record says so), and
in ``staged`` mode by ``epsilon_tiebreak`` among the near-tied top values
(:func:`tiebreak_target`; the shell runs the randomization layer's tie-break).
The target is then shown with probability ``P(accept)`` of the drawn candidate:
shown and not-shown days are both logged, each with the exact joint
probability of its drawn target and its arm (``π(c) · P(c)`` shown,
``π(c) · (1 − P(c))`` not shown: the outcome is the drawn target's, so the
propensity is too; codex review F3), so the policy is evaluated
intention-to-treat on ``R_cold`` (``router.outcomes``). No per-day quota and no fixed mute length: the seeded
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
from learnloop.router import mixture as mx

#: The decision row's shape (its candidates and detail JSON).
SUGGESTION_VERSION = "lesson_suggestion_v1"
#: The prior set's identity: a changed prior is a successor (the playbook).
PRIORS_VERSION = "suggestion_priors_v1"
DECISION_KIND = "lesson_suggestion"
#: The assignment mechanism (registered in ``db.stores.router.ROUTER_DESIGNS``): the target by the
#: router's design (:data:`TARGET_DESIGNS`), then the show coin.
DESIGN = "lesson_suggestion_draw"
#: The target's design per ``router.mode`` (spec §15.1): the router's mixture, or the staged tie-break.
TARGET_MIXTURE = mx.DESIGN
TARGET_TIEBREAK = "epsilon_tiebreak"
TARGET_DESIGNS: tuple[str, ...] = (TARGET_MIXTURE, TARGET_TIEBREAK)
#: The router's models are not asked about lesson candidates (their status on the target's record).
MODELS_NOT_ASKED = "not_asked"
POLICY = "lesson_suggestion_v1"
SURFACE = "today_card"
CANDIDATE_KIND = "instruct_lesson"
#: The day's draw showed no card.
NO_SUGGESTION = "no_suggestion"
REASONS: tuple[str, ...] = ("new_goal", "cold_failing", "below_band", "cold_missed")
#: The reasons that say a cold check on the topic didn't come out right, read by one effect, ``reason_cold_failing``
#: (the owner's decision 4, spec_instruct_handoff_v1 §8). ``cold_missed`` replaced ``cold_failing``'s candidacy rule (any
#: missed check since the last lesson, not the two latest) and its wording (the miss's date: "On Nov 3, a check on it wasn't
#: fully right."),
#: but it tells the learner the same thing, so a response to either card teaches the same effect: every earlier answer
#: to a ``cold_failing`` card keeps informing it, and no new effect starts from a prior of its own. No prior changed, so
#: the set keeps its name; a vault that never draws a ``cold_missed`` card computes TE1b's numbers bit for bit.
COLD_MISS_REASONS: frozenset[str] = frozenset({"cold_failing", "cold_missed"})
RESPONSES: tuple[str, ...] = ("accepted", "chose_alternative", "declined", "ignored")

#: The state vector, in order (``decline`` is ``D``, entered as ``−g_R(d)``).
#: Every context feature is 0 at the reference context (a lesson fits in the minutes left, or no plan
#: says otherwise; not a re-entry; a goal LO not started; the last suggestion a day ago, at the seeded
#: cadence, or none yet; no "Not now"), so the seeded centres below are the reference context's
#: (structural: bounded features).
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
#: Revision 3's cadence of about one suggestion a day (basis legacy): the days-since-last-suggestion
#: feature is 0 at this gap, so the seeded centres are the one-a-day context's (codex review F7).
LEGACY_CADENCE_DAYS = 1.0
#: Every effect's prior width (the LP spec's rule for legacy priors: >= 1 logit).
PRIOR_SD = 1.0
#: IH4 (spec_instruct_handoff_v1 §7 item 1): the offset of an unprompted request (the learner asked for a lesson with no
#: offer on screen) from a response to an offer, one more effect of the same width (:data:`PRIOR_SD`, centre 0: no prior
#: claim that the two differ). It exists only once a request is on record (:meth:`AcceptanceState.observe`), and a
#: prediction for an offer never sets it, so how far a request moves ``P(accept)`` is the posterior's split between this
#: offset and the effects an offer reads: no hand-set weight. A changed prior set is a successor (the playbook), so the
#: set with the offset has its own name.
UNPROMPTED_TERM = "unprompted"
UNPROMPTED_PRIORS_VERSION = "suggestion_priors_v1+unprompted_v1"
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
    #: ``below_band``: adaptive difficulty's prediction that put it there (``P_band``, ``p̄``, the band).
    band: Mapping[str, Any] | None = None
    #: ``cold_missed``: when the latest missed cold check since the topic's last lesson was made (its ``created_at``), so
    #: the reason's words can say what happened and when. Read only for the words, never by the model.
    missed_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out = {"ref": self.ref, "kind": CANDIDATE_KIND, "learning_object_ids": list(self.learning_object_ids),
               "reason": self.reason, "title": self.title,
               "predicted_success": None if self.predicted_success is None else round(float(self.predicted_success), 6),
               "days_since_decline": (None if self.days_since_decline is None
                                      else round(float(self.days_since_decline), 6))}
        if self.band is not None:
            out["band"] = dict(self.band)
        if self.missed_at is not None:
            out["missed_at"] = str(self.missed_at)
        return out

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Candidate":
        p = value.get("predicted_success")
        d = value.get("days_since_decline")
        band = value.get("band")
        return cls(ref=str(value["ref"]), learning_object_ids=tuple(str(x) for x in value.get("learning_object_ids") or ()),
                   reason=str(value.get("reason") or "new_goal"),
                   predicted_success=None if p is None else float(p),
                   days_since_decline=None if d is None else float(d), title=str(value.get("title") or ""),
                   band=dict(band) if isinstance(band, Mapping) else None,
                   missed_at=None if value.get("missed_at") is None else str(value["missed_at"]))


def lesson_ref(learning_object_id: str) -> str:
    return f"lesson:{learning_object_id}"


def decline_shape(days: float | None, recovery_days: float) -> float:
    """``g_R(d)``: 1 at the "Not now", 0 from ``R`` days on (``log(1 + d)`` against ``log(1 + R)``)."""

    if days is None:
        return 0.0
    return max(0.0, 1.0 - math.log1p(max(float(days), 0.0)) / math.log1p(float(recovery_days)))


def spacing_feature(days: float | None) -> float:
    """The days-since-the-last-suggestion feature (codex review F7): ``1/(1 + c) − 1/(1 + d)``.

    0 at the seeded cadence ``c`` (:data:`LEGACY_CADENCE_DAYS`, one day) and with no earlier
    suggestion, −1/2 for a suggestion moments ago, rising toward +1/2 as the gap grows: every
    gap keeps its own value (1, 7 and 30 days are 0, 0.375 and 0.468), so the learned
    coefficient can tell daily prompts from a card after several days. Bounded (structural:
    a logistic input whose prior variance stays within a quarter of one effect's), so the seeded
    prior predictive stays at about one a day whatever the gap."""

    if days is None:
        return 0.0
    return 1.0 / (1.0 + LEGACY_CADENCE_DAYS) - 1.0 / (1.0 + max(float(days), 0.0))


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
    h[TERMS.index("reason_cold_failing")] = 1.0 if candidate.reason in COLD_MISS_REASONS else 0.0
    h[TERMS.index("reason_below_band")] = 1.0 if candidate.reason == "below_band" else 0.0
    h[TERMS.index("recent_suggestion")] = spacing_feature(context.days_since_last)
    h[TERMS.index("decline")] = -decline_shape(candidate.days_since_decline, recovery_days)
    return h


@dataclass
class AcceptanceState:
    """The acceptance model's posterior as of some instant."""

    banks: list[_Bank] = field(default_factory=lambda: [
        _Bank(recovery_days=r, mean=_prior_mean(), cov=np.eye(len(TERMS)) * PRIOR_SD ** 2)
        for r in RECOVERY_DAYS_GRID])
    updates: int = 0
    #: IH4: how many of ``updates`` were unprompted requests (0: the banks hold :data:`TERMS` alone, as before IH4).
    unprompted_updates: int = 0

    def weights(self) -> np.ndarray:
        return normalized_log_weights(np.array([bank.log_w for bank in self.banks]))

    def design(self, bank: _Bank, context: Context, candidate: Candidate, *, unprompted: bool = False) -> np.ndarray:
        """``h`` in ``bank``'s terms. The unprompted offset's slot exists only once a request is on record; an offer's
        ``h`` holds 0 there, so with none on record every array and number is the one TE1b computed, bit for bit."""

        h = design_vector(context, candidate, bank.recovery_days)
        return np.append(h, 1.0 if unprompted else 0.0) if bank.mean.shape[0] > h.shape[0] else h

    def p_accept(self, context: Context, candidate: Candidate) -> float:
        """The posterior predictive ``P(accept)`` of an offer: the grid mixture of ``E[σ(h · θ)]``."""

        total = 0.0
        for weight, bank in zip(self.weights(), self.banks):
            h = self.design(bank, context, candidate)
            total += float(weight) * gaussian_sigmoid_mean(float(h @ bank.mean), float(h @ bank.cov @ h))
        return min(max(total, 0.0), 1.0)

    def _open_unprompted(self) -> None:
        """The offset's prior, independent of the rest: earlier responses never set its slot, so adding it now is the
        same posterior as having held it from the start."""

        for bank in self.banks:
            size = bank.mean.shape[0]
            cov = np.zeros((size + 1, size + 1), dtype=np.float64)
            cov[:size, :size] = bank.cov
            cov[size, size] = PRIOR_SD ** 2
            bank.mean, bank.cov = np.append(bank.mean, 0.0), cov

    def observe(self, context: Context, candidate: Candidate, accepted: bool, *, unprompted: bool = False) -> None:
        """One response: AD's assumed-density step in every bank, the grid weights by ``log Z``. ``unprompted`` (IH4): a
        request with no offer on screen, read through its own offset (:data:`UNPROMPTED_TERM`)."""

        y = 1.0 if accepted else 0.0
        if unprompted and self.unprompted_updates == 0:
            self._open_unprompted()

        def log_lik(eta: np.ndarray) -> np.ndarray:
            p = np.clip(sigmoid(eta), 1e-12, 1.0 - 1e-12)
            return y * np.log(p) + (1.0 - y) * np.log(1.0 - p)

        for bank in self.banks:
            h = self.design(bank, context, candidate, unprompted=unprompted)
            bank.mean, bank.cov, record = adf_update(bank.mean, bank.cov, h, log_lik)
            bank.log_w += record.log_z
        self.updates += 1
        if unprompted:
            self.unprompted_updates += 1

    def summary(self) -> dict[str, Any]:
        """Posterior means (grid-weighted) and the recovery grid's weights, for the decision row."""

        weights = self.weights()
        mean = sum(float(w) * bank.mean for w, bank in zip(weights, self.banks))
        extra = {"unprompted_updates": self.unprompted_updates} if self.unprompted_updates else {}
        terms = (*TERMS, UNPROMPTED_TERM) if self.unprompted_updates else TERMS
        return {"priors_version": self.priors_version, "updates": self.updates, **extra,
                "means": {term: round(float(value), 6) for term, value in zip(terms, mean)},
                "recovery_days": [round(bank.recovery_days, 6) for bank in self.banks],
                "recovery_weights": [round(float(w), 6) for w in weights]}

    @property
    def priors_version(self) -> str:
        return UNPROMPTED_PRIORS_VERSION if self.unprompted_updates else PRIORS_VERSION


# =============================================================================
# Replay: the observations a response ledger gives
# =============================================================================


@dataclass(frozen=True)
class Observation:
    context: Context
    candidate: Candidate
    accepted: bool
    at: str
    #: IH4: a request with no offer on screen (:func:`unprompted_observations`), never a response to one
    unprompted: bool = False


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


#: The ``router_learner_preferences`` kind that names a lesson (``learner_action.LESSON``), and the key its row froze the
#: acceptance model's replay inputs under (``learner_action.Options.offered``).
LESSON_KIND = "lesson"
LESSON_INPUTS = "lesson_inputs"
#: The surfaces with no offer on them (``learner_action.PHONE_SURFACES``; a test pins the two).
PHONE_SURFACES = ("phone_feedback", "phone_today")
#: What the learner themselves said to an offer. ``ignored`` is not one: it is the plan reading a moved-on card.
_ANSWERS = frozenset({"accepted", "chose_alternative", "declined"})


def unprompted_observations(preferences: Iterable[Mapping[str, Any]], *, at: str | None = None,
                            responses: Iterable[Mapping[str, Any]] = ()) -> list[Observation]:
    """IH4 (spec_instruct_handoff_v1 §7 item 1): the learner's requests for a lesson as acceptance observations, oldest
    first, as of ``at``. Each is a preference of the lesson kind with the replay inputs its row froze, so a replay never
    depends on today's state, as for a response.

    Left out: a choice on the desktop of the lesson the plan had itself drawn (an agreement, ``served_decision_id`` the
    parent: an offer was on screen, and its own Start or "Not now" is the response, so counting this too would count it
    twice) and a row with no frozen inputs (written with the switch off). A phone shows no offer, so an agreement there
    was asked for with nothing on screen and counts as a request, until the learner answers that offer on the desktop:
    from then on the answer is the one observation of that offer (``responses``, as of ``at``). A request is only ever
    ``accepted``: nothing records the moments the learner could have asked and didn't, and they are not read as refusals."""

    answered = {str(row["decision_id"]) for row in responses
                if str(row["response"]) in _ANSWERS and (at is None or str(row["responded_at"]) <= at)}
    out: list[Observation] = []
    for row in sorted(preferences, key=lambda found: (str(found["created_at"]), str(found["id"]))):
        created = str(row["created_at"])
        if str(row.get("chosen_kind")) != LESSON_KIND or (at is not None and created > at):
            continue
        parent = row.get("decision_id")
        if parent is not None and row.get("served_decision_id") == parent and (
                str(row.get("surface")) not in PHONE_SURFACES or str(parent) in answered):
            continue
        inputs = json.loads(row.get("offered_json") or "{}").get(LESSON_INPUTS)
        if not isinstance(inputs, Mapping) or not isinstance(inputs.get("candidate"), Mapping):
            continue
        out.append(Observation(Context.from_dict(inputs.get("context") or {}), Candidate.from_dict(inputs["candidate"]),
                               True, created, unprompted=True))
    return out


def with_unprompted(observed: Sequence[Observation], requests: Sequence[Observation]) -> list[Observation]:
    """The responses and the requests in one order (by time; a tie keeps a response first). No request: ``observed``,
    untouched."""

    return sorted([*observed, *requests], key=lambda row: row.at) if requests else list(observed)


def replay(observed: Iterable[Observation]) -> AcceptanceState:
    state = AcceptanceState()
    for observation in observed:
        state.observe(observation.context, observation.candidate, observation.accepted,
                      unprompted=observation.unprompted)
    return state


def declines_by_learning_object(decisions: Mapping[str, Mapping[str, Any]],
                                responses: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Per LO, the time of its latest "Not now" not followed by an acceptance of a lesson on it.

    A ``released`` row (the learner's "Not now" on a pending card, letting a Start's unopened lesson go)
    is a "Not now" on its LOs too; an ``expired`` one (the lesson could no longer open) is not.

    Only the rows of ``decisions`` count, as in :func:`observations` (TE3b, Codex re-review F3: with lesson offers off,
    the daily draw passes TE1b's own decisions, so an offer's "Not now" never dates a switch-off candidate; every
    response below TE3b is on a daily decision, so its ledger reads as before)."""

    latest: dict[str, str] = {}
    for response in sorted(responses, key=lambda row: (str(row["responded_at"]), str(row["id"]))):
        if str(response["decision_id"]) not in decisions:
            continue
        los = json.loads(response.get("learning_object_ids_json") or "[]") if isinstance(
            response.get("learning_object_ids_json"), str) else list(response.get("learning_object_ids") or ())
        kind = str(response["response"])
        for lo in los:
            if kind in ("declined", "released"):
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
class Target:
    """The drawn target: the router's design, its exact distribution over the scored candidates (0 off
    the support) and what it logs (``record``: enough to recompute ``pi``)."""

    design: str
    chosen_ref: str
    pi: Mapping[str, float]
    record: Mapping[str, Any]


def mixture_target(scored: Sequence[ScoredCandidate], *, weights: Mapping[str, float], epsilon: float,
                   seed: str) -> Target:
    """``router.mode = "mixture"``: the router's ``model_mixture`` over ``scored`` (the top ``k``).

    The staged component puts its mass on the staged rule's pick (the top value); the Decider and the
    router LLM are not asked about lesson candidates, so each gives its configured weight to the staged
    rule (``mixture.effective_weights``, G7), and ``epsilon`` floors every candidate. The two-stage draw
    and ``pi`` are :mod:`learnloop.router.mixture`'s; ``mixture.recompute(record)`` gives the target's
    propensity back."""

    if not scored:
        raise ValueError("a draw needs a candidate")
    support = [s.candidate.ref for s in scored]
    staged_ref = support[0]
    distributions: dict[str, Mapping[str, float] | None] = {name: None for name in mx.MODEL_COMPONENTS}
    effective = mx.effective_weights(weights, set(mx.MODEL_COMPONENTS))
    components = mx.component_distributions(support, staged_ref, distributions)
    u1, u2, _ = _uniforms(seed)
    result = mx.draw_with_uniforms(support, components, effective, float(epsilon), u1, u2)
    record = {
        "design": TARGET_MIXTURE, "support": support, "staged_ref": staged_ref, "chosen": result.chosen,
        "epsilon": float(epsilon),
        "configured_weights": {name: float(weights.get(name, 0.0) or 0.0) for name in mx.COMPONENTS},
        "effective_weights": dict(effective), "distributions": {},
        "models": {name: {"status": MODELS_NOT_ASKED} for name in mx.MODEL_COMPONENTS},
        "component": result.component, "u1": round(u1, 12), "u2": round(u2, 12),
    }
    return Target(TARGET_MIXTURE, result.chosen, dict(result.pi), record)


def tiebreak_target(scored: Sequence[ScoredCandidate], *, chosen_ref: str, tied: Sequence[str],
                    margin: float) -> Target:
    """``router.mode = "staged"``: the randomization layer's ``epsilon_tiebreak`` (the shell runs it).

    Near-tied top values (within ``margin`` of the top, the layer's own rule): uniform over the tied
    set; otherwise the staged rule's pick with probability 1."""

    if not scored:
        raise ValueError("a draw needs a candidate")
    refs = [s.candidate.ref for s in scored]
    support = [ref for ref in tied if ref in refs] if len(tied) > 1 else [chosen_ref]
    if chosen_ref not in support:
        raise ValueError("the tie-break chose outside its tied set")
    pi = {ref: (1.0 / len(support) if ref in support else 0.0) for ref in refs}
    record = {"design": TARGET_TIEBREAK, "support": refs, "staged_ref": refs[0], "chosen": chosen_ref,
              "tied": sorted(support), "near_equivalent": len(support) > 1, "margin": float(margin),
              "values": {s.candidate.ref: round(math.exp(s.value), 12) for s in scored}}
    return Target(TARGET_TIEBREAK, chosen_ref, pi, record)


@dataclass(frozen=True)
class Draw:
    """The day's draw. The target is drawn first (``π``, :class:`Target`), then the arm (the show coin at
    the target's ``P(accept)``); ``propensity`` is the joint probability of that target and that arm, so a
    shown and an unshown day are weighted on the same target-specific outcome (codex review F3).

    ``scope`` is the predeclared outcome scope, fixed before the arm: the target and the up-to-two
    candidates the card would offer beside it (the alternatives when shown), so an accepted
    alternative's delayed checks join the decision in both arms (codex review F4)."""

    scored: tuple[ScoredCandidate, ...]
    drawn: ScoredCandidate
    shown: bool
    alternatives: tuple[ScoredCandidate, ...]
    propensity: float
    propensity_kind: str
    p_no_card: float
    seed: str
    ceiling_bound: bool = False
    scope: tuple[ScoredCandidate, ...] = ()
    target: Target | None = None

    @property
    def arm_propensity(self) -> float:
        """The arm's probability given the drawn target (1 when the ceiling binds)."""

        if self.ceiling_bound:
            return 1.0
        return self.drawn.p_accept if self.shown else 1.0 - self.drawn.p_accept

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


def _uniforms(seed: str) -> tuple[float, float, float]:
    """The draw's three uniforms from its seed: the mixture's two stages, then the show coin."""

    return mx.uniform(seed, "component"), mx.uniform(seed, "candidate"), mx.uniform(seed, "show")


def _propensity(p: float) -> tuple[float, str]:
    if p >= 1.0 - 1e-12:
        return 1.0, "deterministic"
    return p, "exact"


def draw(scored: Sequence[ScoredCandidate], *, target: Target, seed: str, ceiling_bound: bool = False) -> Draw:
    """The day's draw over ``scored`` (non-empty): the drawn ``target`` (its ``π``), then the show coin.

    ``ceiling_bound``: the anti-nagging ceiling binds (``keep``), so no card is
    shown whatever the draw (logged with a deterministic arm)."""

    if not scored:
        raise ValueError("a draw needs a candidate")
    pi = {ref: float(target.pi.get(ref, 0.0)) for ref in (s.candidate.ref for s in scored)}
    if abs(sum(pi.values()) - 1.0) > 1e-9 or pi.get(target.chosen_ref, 0.0) <= 0.0:
        raise ValueError("the target's distribution must sum to one and support its pick")
    with_pi = tuple(ScoredCandidate(s.candidate, s.p_accept, s.room, s.value, pi[s.candidate.ref]) for s in scored)
    drawn = next(s for s in with_pi if s.candidate.ref == target.chosen_ref)
    u_show = _uniforms(seed)[2]
    # The aggregate chance of no card (any target), kept for the report; never the row's propensity.
    p_no_card = float(sum(s.pi * (1.0 - s.p_accept) for s in with_pi))
    others = sorted((s for s in with_pi if s.candidate.ref != drawn.candidate.ref),
                    key=lambda s: (-s.pi, -s.value, s.candidate.ref))
    scope = (drawn, *others[:MAX_ALTERNATIVES])
    if ceiling_bound:
        # The ceiling decides the arm, but the target was still drawn: P(target) · 1.
        propensity, kind = _propensity(drawn.pi)
        return Draw(with_pi, drawn, False, (), propensity, kind, 1.0, seed, ceiling_bound=True, scope=scope,
                    target=target)
    shown = u_show < drawn.p_accept
    if shown:
        propensity, kind = _propensity(drawn.pi * drawn.p_accept)
        alternatives = tuple(others[:MAX_ALTERNATIVES])
    else:
        propensity, kind = _propensity(drawn.pi * (1.0 - drawn.p_accept))
        alternatives = ()
    return Draw(with_pi, drawn, shown, alternatives, propensity, kind, p_no_card, seed, scope=scope, target=target)


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
    "MODELS_NOT_ASKED",
    "NO_SUGGESTION",
    "Observation",
    "POLICY",
    "PRIORS_VERSION",
    "REASONS",
    "COLD_MISS_REASONS",
    "RECOVERY_DAYS_GRID",
    "RESPONSES",
    "SURFACE",
    "SUGGESTION_VERSION",
    "ScoredCandidate",
    "TARGET_DESIGNS",
    "TARGET_MIXTURE",
    "TARGET_TIEBREAK",
    "Target",
    "canonical_hash",
    "days_between",
    "decline_shape",
    "declines_by_learning_object",
    "design_vector",
    "draw",
    "lesson_ref",
    "mixture_target",
    "observations",
    "replay",
    "score",
    "seed_for",
    "spacing_feature",
    "tiebreak_target",
]

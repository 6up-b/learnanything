"""The plain types the router's objective, its rollouts and its callers share: the action kinds, a candidate
(:class:`Action`), and the frozen belief one decision values its candidates on (:class:`Inputs` with its
:class:`Topic`, :class:`DatedUse`, :class:`Learning`, :class:`CauseSplit`, :class:`EffectSlope` and :class:`Price`).

``daily_plan/objective_inputs.py`` builds them from the vault; :mod:`rollouts` simulates on them. They live here,
not beside their builder, because ``router_objective`` may not import ``daily_plan`` (the package-level cycle
contract), and the builder sits in the chooser's import cycle. This module imports :mod:`memory` (the combiner a
default :class:`Inputs` holds), :mod:`ad_link` (two field types), :mod:`diagnostic_payload` (a probe's payload type)
and :mod:`learnloop.plan_refs` (the offer and stop names it re-exports); nothing it imports reads it back.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop.plan_refs import LESSON_OFFER_PREFIX, LESSON_OFFER_SUBTYPE, STOP_FOR_TODAY, is_offer_subtype
from learnloop.router_objective.ad_link import AdLink, LessonCurve
from learnloop.router_objective.diagnostic_payload import DiagnosticProbe
from learnloop.router_objective.memory import Combiner

#: Action kinds (§8.1's table).
REVIEW = "review"
NEW_PRACTICE = "new_practice"
READING = "reading"
PROBE = "probe"
REPAIR = "repair"
TEACH_BACK = "teach_back"
LESSON = "lesson"
STOP = "stop"
#: An ordered sequence of sub-actions (a mid-block alternative, §8.3): each step keeps its own kind, duration,
#: observation and effect, valued one after another on the one clock (Codex review F5).
SEQUENCE = "sequence"
PRACTICE_KINDS = frozenset({REVIEW, NEW_PRACTICE, REPAIR, TEACH_BACK})
KINDS = frozenset({REVIEW, NEW_PRACTICE, READING, PROBE, REPAIR, TEACH_BACK, LESSON, STOP, SEQUENCE})
# The lesson offer's subtype and ref prefix and the stop ref are ``plan_refs``'s (imported above and re-exported):
# one definition that ``router``, ``db`` and ``followup_serve`` read too.


@dataclass(frozen=True)
class Topic:
    """One valued topic (an LO) as the decision believed it."""

    lo: str
    #: AD's predictive on the logit scale and its posterior variance (θ draws from it).
    eta_mean: float
    eta_var: float
    #: FSRS state of the LO's practiced items (aggregate); ``practiced`` False: no memory yet.
    practiced: bool = False
    difficulty: float = 5.0
    stability: float = 0.0
    elapsed_days: float = 0.0
    #: ``c_L`` per day (§8.5): 0 for a topic not enrolled in any undated use.
    undated_density: float = 0.0
    #: AD's reading-dose count on the LO (the dose curve's position).
    reading_count: float = 0.0
    #: Landing ruling R10: AD's latent posterior of ``η`` at the LO's top point, ``(mean, variance)``, read only with
    #: R9's link (``Inputs.ad_link``); None: reconstructed from ``eta_mean`` (``logit p̄``) and ``eta_var``.
    eta_latent: tuple[float, float] | None = None


@dataclass(frozen=True)
class DatedUse:
    goal_id: str
    lo: str
    #: days from the decision to the goal's date
    at_days: float
    #: ``ω_{g,L}`` (§8.5)
    weight: float


@dataclass(frozen=True)
class CauseSplit:
    """Slip or gap SG2 (``docs/specs/spec_slip_vs_gap_v1.md`` §3): on a topic whose latest miss has a diagnosis, a
    lesson's and a repair's effect slope is the mixture over the miss's cause, ``p_gap·γ_gap + p_slip·γ_slip +
    p_unknown·γ``, instead of ``γ``.

    ``gap`` and ``slip`` are ``γ_gap``'s and ``γ_slip``'s posterior (mean, variance), ``cov`` their covariance; ``weights``
    each diagnosed topic's calibrated ``(p_gap, p_slip, p_unknown)``. A topic not in ``weights`` keeps ``γ`` exactly. The
    joint posterior is drawn (Codex F7): ``γ_gap`` along ``γ``'s own stream (common random numbers), so where its
    posterior is ``γ``'s a pure gap is the predecessor's value draw for draw; ``γ_slip`` as its regression on that draw
    plus its residual on a stream of its own (at the seeded priors, independent of ``γ_gap``)."""

    gap: tuple[float, float]
    slip: tuple[float, float]
    weights: Mapping[str, tuple[float, float, float]] = field(default_factory=dict)
    cov: float = 0.0
    version: str = "miss_cause_slopes_v1"

    def at_mean(self) -> "CauseSplit":
        """The believed parameters (each posterior's mean, no parameter draw), as the belief's own world reads γ."""

        return replace(self, gap=(self.gap[0], 0.0), slip=(self.slip[0], 0.0), cov=0.0)


@dataclass(frozen=True)
class Learning:
    """AD's learning parameters (posterior mean, variance): ``γ`` per practice opportunity, the reading dose
    curve's ``ḡ_1, ḡ_2`` on scales ``h_1, h_2``; from TE3a, AD's lesson curve (None: RO4's placeholder); from slip or
    gap SG2, the lesson's and the repair's slope by the miss's cause (None: ``γ`` on every topic, the predecessor)."""

    gamma: tuple[float, float] = (0.2, 0.01)
    gbar: tuple[tuple[float, float], tuple[float, float]] = ((0.10, 0.0049), (0.20, 0.01))
    dose_scales: tuple[float, float] = (1.0, 4.0)
    source: str = "adaptive_difficulty.priors"
    lesson: LessonCurve | None = None
    causes: CauseSplit | None = None


@dataclass(frozen=True)
class EffectSlope:
    """``ΔG = α_v + β_v·f(a)`` (§8.4): each coefficient's posterior mean and variance."""

    alpha: tuple[float, float] = (0.0, 0.04)
    beta: tuple[float, float] = (0.2, 0.04)
    n: int = 0
    version: str = "effect_slope_v1:prior"


@dataclass(frozen=True)
class Price:
    """The attention price at this decision (§8.6): ``κ(x) = κ0·x/m̄`` on session minutes."""

    kappa0: float
    remembered: float
    remembered_source: str = "unknown"
    regime: str = "seed"


@dataclass(frozen=True)
class Action:
    """One candidate as the value estimator sees it."""

    ref: str
    kind: str
    #: one LO per practice opportunity (or per reading dose, or the probe's topic)
    item_los: tuple[str, ...] = ()
    #: the predicted active minutes (the duration distribution's median)
    minutes: float = 0.0
    #: the duration's spread on the log scale (0: fixed)
    minutes_log_sd: float = 0.0
    #: evidence mass on ``γ`` (teach-back, lesson)
    mass: float = 1.0
    #: an offer-type action's uptake ``Beta(a, b)`` (None: not an offer)
    accept: tuple[float, float] | None = None
    #: a probe's repair branch (a practice block on the same topic)
    repair: "Action | None" = None
    #: the LLM policy's forecast for this option (a probability), the effect correction's input
    forecast: float | None = None
    choosable: bool = True
    #: a :data:`SEQUENCE`'s ordered sub-actions (none of them a sequence, a stop or an offer)
    steps: tuple["Action", ...] = ()
    #: Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the delayed checks a lesson commits, ``(LO, days after the
    #: action's end)``: each is a graded attempt on its LO at the first session day at or past its date, so its
    #: information enters through ``E[V(x′)]`` (empty for every other action: the rollouts are unchanged)
    commitments: tuple[tuple[str, float], ...] = ()
    #: IH2 (spec_instruct_handoff_v1 §5): an offer's declined branch when the decision says what follows a "Not now": the
    #: follow-up it competes with, which stays available. None: the tail's next non-offer block, as RO4's interface.
    declined: "Action | None" = None
    #: G2: a probe's diagnostic payload (locked hypotheses, channel, repair per hypothesis), priced only by
    #: ``diagnostic_value.evaluate_probe``; the rollouts refuse it. None: the probe as before.
    diagnostic: DiagnosticProbe | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown action kind {self.kind!r}")
        if self.diagnostic is not None and self.kind != PROBE:
            raise ValueError("only a probe carries a diagnostic payload")
        if (self.kind == SEQUENCE) != bool(self.steps):
            raise ValueError("a sequence (and only a sequence) has steps")
        if any(step.kind in (SEQUENCE, STOP) or step.accept is not None for step in self.steps):
            raise ValueError("a sequence's steps are plain actions")


@dataclass(frozen=True)
class Inputs:
    """The frozen belief one decision values its candidates on (every number the trace reports)."""

    topics: tuple[Topic, ...]
    dated: tuple[DatedUse, ...]
    session_minutes: float
    price: Price
    #: the tail's block: minutes and practice opportunities (the support's means)
    tail_block_minutes: float
    tail_block_items: int
    horizon_days: float
    fsrs_weights: tuple[float, ...]
    return_gaps_days: tuple[float, ...] = ()
    stop_accept: tuple[float, float] = (1.0, 1.0)
    #: RO5 §9 item 1: the return model's slope ``b`` (posterior mean, variance): the gap after a session that
    #: ended at ``x`` active minutes is the learner's own gap times ``exp(b·(x − m̄)/m̄)``. None: no return model
    #: (RO4's: the same gaps after every session's end, the return effect zero by construction).
    return_slope: tuple[float, float] | None = None
    combiner: Combiner = field(default_factory=Combiner)
    learning: Learning = field(default_factory=Learning)
    #: None: the effect correction is off by hand, or a forecast is missing
    effect: EffectSlope | None = None
    reference_forecast: float | None = None
    #: the trace's sources (where each number came from)
    sources: Mapping[str, Any] = field(default_factory=dict)
    #: Landing ruling R9: AD's own predictive (:class:`AdLink`). None: mvp-0.49's ``σ(η)`` on ``logit p̄``.
    ad_link: AdLink | None = None

    @property
    def cutoff(self) -> float:
        """``C`` in days from the decision (§3.2): carried through every rollout."""

        latest = max((use.at_days for use in self.dated), default=0.0)
        return max(float(self.horizon_days), latest)


def cutoff_for(horizon_days: float, dated: Sequence[DatedUse]) -> float:
    return max(float(horizon_days), max((use.at_days for use in dated), default=0.0))


__all__ = [
    "Action", "CauseSplit", "DatedUse", "EffectSlope", "Inputs", "KINDS", "LESSON", "Learning", "NEW_PRACTICE",
    "PRACTICE_KINDS", "PROBE", "Price", "READING", "REPAIR", "REVIEW", "SEQUENCE", "STOP", "TEACH_BACK", "Topic",
    "LESSON_OFFER_PREFIX", "LESSON_OFFER_SUBTYPE", "STOP_FOR_TODAY", "cutoff_for", "is_offer_subtype",
]

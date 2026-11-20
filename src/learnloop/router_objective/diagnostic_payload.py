"""What the diagnostic layer hands the router about one possible post-miss probe: the locked hypotheses, the probe's
channel ``P(result | hypothesis)`` or its explicit absence, the repair each hypothesis needs, the probe's duration,
whether its answer is already exposed, and the hard stops that keep it out of the support. Plain values only.

The diagnostic shell builds it (it may read the vault; this module reads nothing and imports nothing of LearnLoop but
the cause-class names of :mod:`miss_cause`), and :mod:`diagnostic_value` prices it. Nothing here judges whether the
probe is worth asking: there is no threshold, no margin and no score. A hypothesis is never dropped here or after a
result: narrowing reweights it.

The owner's open decisions that change how a payload is priced are :class:`OwnerDecisions`, an explicit input of the
evaluator, never a constant inside it. :data:`DESIGN_RECOMMENDATIONS` holds the values the G2 design recommends,
each marked pending the owner in the evaluator's record.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any

from learnloop.router_objective.miss_cause import CLASSES, GAP, SLIP, UNKNOWN

#: The cause classes in the order of a topic's ``(p_gap, p_slip, p_unknown)`` split (``types.CauseSplit.weights``,
#: which the rollouts' ``_cause_gain`` reads by position).
CLASSES_ORDER: tuple[str, ...] = (GAP, SLIP, UNKNOWN)
#: The hypothesis the diagnosis keeps for "none of the named causes" (the locked set's open arm).
OPEN_HYPOTHESIS = "other_or_unknown"
#: A rows' sum may differ from one by this much (float rounding of a stored channel), never more.
_ROW_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Hypothesis:
    """One locked hypothesis: its id, its prior (or effective posterior) mass, and its cause class (one of
    :data:`miss_cause.CLASSES`: a gap, a slip, or unknown; the open hypothesis is unknown)."""

    id: str
    prior: float
    cause_class: str = UNKNOWN

    def __post_init__(self) -> None:
        if self.cause_class not in CLASSES:
            raise ValueError(f"unknown cause class {self.cause_class!r}")
        if not (math.isfinite(self.prior) and self.prior >= 0.0):
            raise ValueError(f"hypothesis {self.id!r}: a prior is a finite mass at or above zero")


@dataclass(frozen=True)
class Channel:
    """A complete channel: for each hypothesis id, in ``rows``' order, ``P(result | hypothesis)`` over ``results``.

    Every locked hypothesis needs its row (the open one too): a channel that cannot say how a hypothesis answers is
    a :class:`MissingChannel`, never a row filled in by the builder."""

    results: tuple[str, ...]
    rows: tuple[tuple[str, tuple[float, ...]], ...]
    version: str
    source: str

    def __post_init__(self) -> None:
        if not self.results or len(set(self.results)) != len(self.results):
            raise ValueError("a channel names each result once")
        for hypothesis, row in self.rows:
            if len(row) != len(self.results):
                raise ValueError(f"channel row {hypothesis!r} has {len(row)} entries for {len(self.results)} results")
            if any(not (math.isfinite(p) and p >= 0.0) for p in row) or abs(sum(row) - 1.0) > _ROW_TOLERANCE:
                raise ValueError(f"channel row {hypothesis!r} is not a distribution over the results")

    def row(self, hypothesis: str) -> tuple[float, ...]:
        for name, row in self.rows:
            if name == hypothesis:
                return row
        raise KeyError(hypothesis)


@dataclass(frozen=True)
class MissingChannel:
    """No channel exists at the decision, and why (an unauthored probe, an instrument with no likelihood, ...)."""

    reason: str


@dataclass(frozen=True)
class RepairOption:
    """One executable repair the policy may choose after the probe's result (or now, without it): the repair block
    (an :class:`types.Action` of kind repair on the factor's topic) and the hypotheses it covers."""

    ref: str
    action: Any
    covers: frozenset[str]
    #: where the repair's coverage came from (the repair-class mapping's source), for the record
    source: str = ""


@dataclass(frozen=True)
class DiagnosticProbe:
    """The diagnostic payload of one probe candidate (design §2a's table), as plain values.

    ``source`` identifies the decision (attempt, factor, workflow or episode, candidate or item, origin, as-of time) as
    ``(name, value)`` pairs, for the record only. ``topic`` is the factor's learning object, the topic whose repair
    effect each hypothesis conditions. ``exposed``: the answer would be given after the miss's feedback, causes or a
    reveal were shown, so it separates no cause (an exposed answer updates no belief). ``hard_stops``: the reasons the
    probe may not be asked now (a learner refusal, pending machine checks, a measured foreign episode, an
    unexecutable contract); any one keeps it out of the support. ``routing_weights``: a separately versioned positive
    weight per hypothesis that reweights the branches (the learner's own narrowing); it can never remove one.
    ``facts``: the repair lane's facts (``ProbeFacts``) as plain values, for the record and the card; they are not a
    likelihood and the evaluator never prices them."""

    topic: str
    hypotheses: tuple[Hypothesis, ...]
    prior_basis: str
    channel: Channel | MissingChannel
    repairs: tuple[RepairOption, ...]
    exposed: bool = False
    hard_stops: tuple[str, ...] = ()
    routing_weights: tuple[tuple[str, float], ...] = ()
    routing_version: str | None = None
    source: tuple[tuple[str, str], ...] = ()
    facts: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        ids = [h.id for h in self.hypotheses]
        if len(ids) < 1 or len(set(ids)) != len(ids):
            raise ValueError("a payload locks at least one hypothesis, each once")
        if sum(h.prior for h in self.hypotheses) <= 0.0:
            raise ValueError("the locked prior has no mass")
        if isinstance(self.channel, Channel) and sorted(name for name, _row in self.channel.rows) != sorted(ids):
            raise ValueError("a channel needs exactly one row per locked hypothesis (a missing row is a MissingChannel)")
        weights = dict(self.routing_weights)
        if set(weights) - set(ids):
            raise ValueError("a routing weight names a hypothesis outside the locked set")
        if any(not (math.isfinite(w) and w > 0.0) for w in weights.values()):
            raise ValueError("a routing weight is positive: narrowing reweights a hypothesis, it never removes one")
        refs = [option.ref for option in self.repairs]
        if len(set(refs)) != len(refs) or "none" in refs:
            raise ValueError("each repair option has its own ref, and 'none' is the no-repair option's")
        for option in self.repairs:
            if set(option.covers) - set(ids):
                raise ValueError(f"repair {option.ref!r} covers a hypothesis outside the locked set")

    def effective_prior(self) -> dict[str, float]:
        """Each hypothesis's mass after the routing weights, normalized; every locked hypothesis keeps its entry."""

        weights = dict(self.routing_weights)
        raw = {h.id: h.prior * weights.get(h.id, 1.0) for h in self.hypotheses}
        total = sum(raw.values())
        return {name: value / total for name, value in raw.items()}

    def summary(self) -> dict[str, Any]:
        """The payload as plain JSON values (what the evaluator was given)."""

        channel: dict[str, Any]
        if isinstance(self.channel, Channel):
            channel = {"status": "complete", "results": list(self.channel.results),
                       "rows": {name: list(row) for name, row in self.channel.rows},
                       "version": self.channel.version, "source": self.channel.source}
        else:
            channel = {"status": "missing", "reason": self.channel.reason}
        return {
            "topic": self.topic,
            "hypotheses": [{"id": h.id, "prior": h.prior, "cause_class": h.cause_class} for h in self.hypotheses],
            "prior_basis": self.prior_basis,
            "routing_weights": dict(self.routing_weights), "routing_version": self.routing_version,
            "effective_prior": self.effective_prior(),
            "channel": channel,
            "repairs": [{"ref": o.ref, "covers": sorted(o.covers), "source": o.source,
                         "minutes": getattr(o.action, "minutes", None),
                         "minutes_log_sd": getattr(o.action, "minutes_log_sd", None)} for o in self.repairs],
            "exposed": self.exposed, "hard_stops": list(self.hard_stops),
            "source": dict(self.source), "facts": dict(self.facts),
        }


# -- the owner's open decisions ---------------------------------------------------------------------------------------

#: Decision 1: a probe whose channel is missing (an unauthored FG1 probe) earns no diagnostic information credit; its
#: burden and the repair it leads to are still priced. The alternative, a versioned generation-channel prior, does not
#: exist in the code, so it is not an implementable value yet.
NO_INFORMATION_CREDIT = "no_information_credit"
#: Decision 2, a repair that covers the true hypothesis: the slip-or-gap slopes by that hypothesis's cause class
#: (``CauseSplit``: ``γ_gap``, ``γ_slip``, and ``γ`` for unknown), the same seeded priors and fits the lesson and repair
#: values already read.
CAUSE_CLASS_SLOPES = "cause_class_slopes"
#: Decision 2, a repair that does not cover the true hypothesis: priced as an ordinary practice opportunity on the
#: topic, AD's ``γ`` (what the rollouts give every untargeted graded attempt: a review, new practice, the tail's own
#: blocks). This asserts only that the repair teaches like practice; it claims neither zero nor a measured effect.
PRACTICE_GAMMA = "practice_gamma"
PENDING = "pending the owner"


@dataclass(frozen=True)
class OwnerDecisions:
    """The G2 design's owner decisions 1 to 3 as the evaluator's named inputs (decision 4, the launch tradeoff, is
    decided from the comparison report and changes no pricing)."""

    unauthored_channel: str
    covered_repair_effect: str
    uncovered_repair_effect: str
    #: Decision 3: when WAIT is infeasible (no room to wait), acting now without a repair (no intervention) stays an
    #: arm. False is the predecessor's shape: no room removes it and the probe is asked.
    no_intervention_without_wait: bool
    status: str = PENDING

    def __post_init__(self) -> None:
        if self.unauthored_channel != NO_INFORMATION_CREDIT:
            raise ValueError("decision 1: no generation-channel prior exists in the code; a missing channel earns no "
                             "information credit until the owner approves one")
        if self.covered_repair_effect != CAUSE_CLASS_SLOPES:
            raise ValueError("decision 2: the cause-class slopes are the only covered-repair effect in the code")
        if self.uncovered_repair_effect != PRACTICE_GAMMA:
            raise ValueError("decision 2: practice's gamma is the only uncovered-repair seed the code can supply")

    def record(self) -> dict[str, Any]:
        return {
            "1_unauthored_channel": {"value": self.unauthored_channel, "status": self.status},
            "2_covered_repair_effect": {"value": self.covered_repair_effect, "status": self.status},
            "2_uncovered_repair_effect": {"value": self.uncovered_repair_effect, "status": self.status,
                                          "seed": "AD's practice slope gamma (types.Learning.gamma)"},
            "3_no_intervention_without_wait": {"value": self.no_intervention_without_wait, "status": self.status},
            "4_launch_tradeoff": {"value": "decided from the comparison report", "status": self.status},
        }


#: The G2 design's recommendations (docs/reviews/refactor-g2-design.md §7), the values the tests and the comparison
#: report use until the owner answers.
DESIGN_RECOMMENDATIONS = OwnerDecisions(
    unauthored_channel=NO_INFORMATION_CREDIT,
    covered_repair_effect=CAUSE_CLASS_SLOPES,
    uncovered_repair_effect=PRACTICE_GAMMA,
    no_intervention_without_wait=True,
)


def posterior_table(probe: DiagnosticProbe) -> tuple[str, list[dict[str, Any]]]:
    """The results the policy can see and the posterior after each: ``(channel use, rows)``, each row
    ``{"result", "p", "posterior", "joint"}`` with ``joint[h] = p(h)·L(r|h)``.

    Without information (the answer exposed, or no channel) there is one row, the prior itself: the policy then sees
    nothing it did not know. With a channel, ``p(h | r) = p(h)·L(r|h) / p(r)``, every locked hypothesis kept (at zero
    where the result rules it out); a result no hypothesis can give (``p(r) = 0``) is dropped, because no branch
    reaches it."""

    prior = probe.effective_prior()
    if probe.exposed:
        return "exposed", [{"result": "exposed", "p": 1.0, "posterior": dict(prior), "joint": dict(prior)}]
    if not isinstance(probe.channel, Channel):
        return f"missing:{probe.channel.reason}", [
            {"result": "unobserved", "p": 1.0, "posterior": dict(prior), "joint": dict(prior)}]
    rows = []
    for index, result in enumerate(probe.channel.results):
        joint = {h: prior[h] * probe.channel.row(h)[index] for h in prior}
        p = sum(joint.values())
        if p <= 0.0:
            continue
        rows.append({"result": result, "p": p, "posterior": {h: value / p for h, value in joint.items()},
                     "joint": joint})
    return "channel", rows


def effect_key(option: RepairOption | None, hypothesis: Hypothesis) -> str:
    """Which effect a repair has when ``hypothesis`` is true: its cause class's slope when the repair covers it,
    ``uncovered`` when it does not, ``none`` for no repair."""

    if option is None:
        return "none"
    return hypothesis.cause_class if hypothesis.id in option.covers else "uncovered"


def weights_from(mapping: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted((str(k), float(v)) for k, v in mapping.items()))


__all__ = [
    "CAUSE_CLASS_SLOPES", "CLASSES_ORDER", "Channel", "DESIGN_RECOMMENDATIONS", "DiagnosticProbe", "GAP", "Hypothesis", "MissingChannel",
    "NO_INFORMATION_CREDIT", "OPEN_HYPOTHESIS", "OwnerDecisions", "PENDING", "PRACTICE_GAMMA", "RepairOption", "SLIP",
    "UNKNOWN", "effect_key", "posterior_table", "weights_from",
]

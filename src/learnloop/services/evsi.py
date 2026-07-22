"""P4 step 3 -- robust expected value of sample information (EVSI), spec §6.

EVSI is the minutes-denominated decision value of a diagnostic question. Because the
loss table (:mod:`action_loss`) is already in wasted learner-minutes, EVSI comes out in
minutes directly -- no nats->minutes conversion is needed (contrast the EIG path in
:mod:`robust_composition`, which this module deliberately does NOT reuse for the value
itself). For a candidate question ``q`` and belief ``p(h)`` (spec §6.3)::

    current_loss  = min_a  sum_h p(h)      L(h, a)
    future_loss(q)= sum_e P(e|q) min_a sum_h p(h|e,q) L(h, a)
    EVSI(q)       = current_loss - future_loss(q)   (>= 0)

The emission integration is over the calibrated generative chain
``H -> Z -> E=(G, conf)``: ``P(E|H) = sum_z P(E|Z) P(Z|H)`` (composed via
:func:`robust_composition.compose_emission_over_hypotheses`). We NEVER substitute a
stored ``P(Z|E)`` as a likelihood and never multiply correlated regrades (spec §6.1,
§16.3 "no P(Z|E) double-count").

Robustness (spec §6.5): EVSI is evaluated over a **credible set** of grader/instrument
likelihood matrices (the deterministic ensemble from
:func:`robust_composition.build_ensemble`) and a bounded ±0.15 per-row perturbation
stress test. The point estimate is the mean member; the robust value is the lower
quantile (:func:`robust_composition.robust_quantile`). If the ranking winner or the
downstream argmin action flips across the credible/stress matrices, the selector
**abstains** (§6.5) -- the flip is logged, never hidden behind a mean.

Ranking vs stopping are different (invariant 5, §6.4):

    rank(q) = robust_value(q) / (expected_minutes(q) + burden_minutes(q))   # ordering
    stop when  LCB(EVSI(q)) <= lambda_time * expected_minutes(q) + burden_cost   # halting

``lambda_time`` is fixed at 1 (the minutes numeraire, U-023). A positive EVSI cannot by
itself force another question; only a robust net value above the minutes cost does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.services import action_loss as AL
from learnloop.services.robust_composition import (
    BURDEN_COST,
    LAMBDA_TIME,
    ROBUST_QUANTILE,
    robust_quantile,
)

# Structural schema version of the EVSI persistence body (enum, not a decision knob).
EVSI_SCHEMA_VERSION = 1

# Bounded per-row probability perturbation for the robustness stress test (spec §6.5,
# §16.3). Reuses the standing ±0.15 robustness axis; heuristic decision parameter.
PERTURBATION_DELTA = 0.15


# ---------------------------------------------------------------------------
# Core EVSI over one conditional table (one credible-set member).
# ---------------------------------------------------------------------------


def _normalized_prior(prior: Mapping[str, float], hypotheses: Sequence[str]) -> dict[str, float]:
    p = {h: max(float(prior.get(h, 0.0)), 0.0) for h in hypotheses}
    total = sum(p.values())
    if total <= 0:
        n = len(hypotheses) or 1
        return {h: 1.0 / n for h in hypotheses}
    return {h: v / total for h, v in p.items()}


def shared_optimal_action(loss_table: AL.LossTable, *, tol: float = 1e-9) -> str | None:
    """The action that is argmin loss for EVERY hypothesis individually (§6.2). When it
    exists, every plausible hypothesis maps to the same optimal action, so measurement
    has no action value and the controller uses that common action (EVSI = 0)."""

    shared: frozenset[str] | None = None
    for h in loss_table.hypotheses:
        losses = {a: loss_table.loss(h, a) for a in loss_table.actions}
        if not losses:
            return None
        floor = min(losses.values())
        argmins = frozenset(a for a, v in losses.items() if v - floor <= tol)
        shared = argmins if shared is None else (shared & argmins)
    if not shared:
        return None
    return sorted(shared)[0]


@dataclass(frozen=True)
class MemberEVSI:
    evsi: float
    current_action: str
    argmin_by_emission: dict[str, str]


def evsi_for_conditionals(
    conditionals: Mapping[str, Mapping[str, float]],
    prior: Mapping[str, float],
    loss_table: AL.LossTable,
) -> MemberEVSI:
    """EVSI over one ``P(E|H)`` table (spec §6.3). ``conditionals`` is ``{H: {E: p}}``;
    it is the composed emission likelihood, NOT a stored ``P(Z|E)`` (§6.1)."""

    hyps = [h for h in loss_table.hypotheses if h in conditionals]
    p = _normalized_prior(prior, hyps)
    current_action = loss_table.argmin_action(p)
    current_loss = loss_table.expected_loss(current_action, p)

    emissions = sorted({e for h in hyps for e in conditionals[h]})
    future = 0.0
    argmin_by_e: dict[str, str] = {}
    for e in emissions:
        pe = sum(p[h] * float(conditionals[h].get(e, 0.0)) for h in hyps)
        if pe <= 0.0:
            continue
        posterior = {h: p[h] * float(conditionals[h].get(e, 0.0)) / pe for h in hyps}
        a = loss_table.argmin_action(posterior)
        argmin_by_e[e] = a
        future += pe * loss_table.expected_loss(a, posterior)

    evsi = max(current_loss - future, 0.0)
    return MemberEVSI(evsi=evsi, current_action=current_action, argmin_by_emission=argmin_by_e)


# ---------------------------------------------------------------------------
# Robust EVSI over the credible set (the ensemble members).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RobustEVSI:
    """Robust EVSI products for one candidate question (spec §6.3/§6.5), persistable."""

    point: float          # mean-member EVSI (minutes)
    lcb: float            # lower-quantile (robust) EVSI (minutes)
    ucb: float            # upper-quantile EVSI (minutes)
    current_action: str   # argmin action under the mean member
    action_flipped: bool  # does the downstream argmin action differ across members?
    common_action: str | None  # a shared argmin action across every member, else None
    member_count: int
    quantile: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVSI_SCHEMA_VERSION,
            "point": round(self.point, 6),
            "lcb": round(self.lcb, 6),
            "ucb": round(self.ucb, 6),
            "current_action": self.current_action,
            "action_flipped": self.action_flipped,
            "common_action": self.common_action,
            "member_count": self.member_count,
            "quantile": self.quantile,
        }


def robust_evsi(
    members: Sequence[Mapping[str, Mapping[str, float]]],
    prior: Mapping[str, float],
    loss_table: AL.LossTable,
    *,
    quantile: float = ROBUST_QUANTILE,
) -> RobustEVSI:
    """Robust EVSI over a credible set of ``P(E|H)`` matrices. Member 0 is the
    posterior-mean (the point estimate); the LCB is the lower ``quantile`` (spec §6.5).
    ``common_action`` is defined in DECISION SPACE (§6.2): an action in the argmin set
    of every member under the current belief -- never closeness of loss values."""

    if not members:
        return RobustEVSI(0.0, 0.0, 0.0, "", False, None, 0, quantile)

    per_member = [evsi_for_conditionals(m, prior, loss_table) for m in members]
    evsis = [r.evsi for r in per_member]
    point = evsis[0]
    lcb = robust_quantile(evsis, quantile)
    ucb = -robust_quantile([-v for v in evsis], quantile)

    # Downstream-action flip (§6.5). ``current_action`` is the argmin under the PRIOR
    # only -- it is the same loss table and prior for every credible-set member, so it can
    # never disagree and is useless as a flip signal (audit H2/F1). The member-dependent
    # decision quantity is the per-emission recommended action ``argmin_by_emission``:
    # members differ in P(E|H), so the action you would take AFTER observing an emission
    # can disagree across the credible set. Any emission whose recommended action differs
    # between members is a genuine downstream-action flip -> abstain.
    per_emission_actions: dict[str, set[str]] = {}
    for r in per_member:
        for emission, action in r.argmin_by_emission.items():
            per_emission_actions.setdefault(emission, set()).add(action)
    action_flipped = (
        len({r.current_action for r in per_member}) > 1
        or any(len(actions) > 1 for actions in per_emission_actions.values())
    )

    # Common optimal action across HYPOTHESES (§6.2): the action that is argmin loss for
    # EVERY hypothesis individually. When one exists, measurement has no action value and
    # the controller uses that common action (EVSI is 0). Defined in decision space (the
    # argmin action set), never closeness of loss values.
    common_action = shared_optimal_action(loss_table)

    return RobustEVSI(
        point=point, lcb=lcb, ucb=ucb, current_action=per_member[0].current_action,
        action_flipped=action_flipped, common_action=common_action,
        member_count=len(members), quantile=quantile,
    )


# ---------------------------------------------------------------------------
# ±0.15 per-row perturbation stress (spec §6.5).
# ---------------------------------------------------------------------------


def _perturb_row(row: Mapping[str, float], delta: float, *, toward_mode: bool) -> dict[str, float]:
    """Move ``delta`` probability mass between the modal and the least-likely emission
    of a row, then renormalize (bounded ±0.15, renormalized per row, §6.5)."""

    keys = sorted(row.keys())
    if len(keys) < 2:
        return {k: float(row[k]) for k in keys}
    hi = max(keys, key=lambda k: (row[k], k))
    lo = min(keys, key=lambda k: (row[k], k))
    out = {k: float(row[k]) for k in keys}
    if toward_mode:
        moved = min(delta, out[lo])
        out[hi] += moved
        out[lo] -= moved
    else:
        moved = min(delta, out[hi])
        out[hi] -= moved
        out[lo] += moved
    total = sum(out.values()) or 1.0
    return {k: max(0.0, v) / total for k, v in out.items()}


def stress_matrices(
    conditionals: Mapping[str, Mapping[str, float]], delta: float = PERTURBATION_DELTA
) -> list[dict[str, dict[str, float]]]:
    """Two deterministic ±``delta`` per-row perturbations of a ``P(E|H)`` table (§6.5)."""

    toward = {h: _perturb_row(row, delta, toward_mode=True) for h, row in conditionals.items()}
    away = {h: _perturb_row(row, delta, toward_mode=False) for h, row in conditionals.items()}
    return [toward, away]


# ---------------------------------------------------------------------------
# Feasible-set ranking + stop (spec §6.4). Ranking orders WITHIN the feasible set;
# the constraint engine already defined feasibility.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosticCandidate:
    """One feasible diagnostic question, already admitted by the constraint engine.
    ``members`` are the credible-set ``P(E|H)`` matrices (member 0 = mean)."""

    ref: str
    members: tuple[dict[str, dict[str, float]], ...]
    prior: Mapping[str, float]
    expected_minutes: float
    burden_minutes: float = 0.0


@dataclass(frozen=True)
class RankedCandidate:
    ref: str
    evsi: RobustEVSI
    rank_value: float          # robust EVSI per minute
    expected_minutes: float
    stop_threshold: float
    ordinal: int


@dataclass(frozen=True)
class RankResult:
    ranked: tuple[RankedCandidate, ...]
    best_ref: str | None
    should_stop: bool
    abstained: bool
    verdict: str  # 'measure' | 'stop' | 'abstain'
    reason: str
    stress_winner_flipped: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVSI_SCHEMA_VERSION,
            "best_ref": self.best_ref,
            "should_stop": self.should_stop,
            "abstained": self.abstained,
            "verdict": self.verdict,
            "reason": self.reason,
            "stress_winner_flipped": self.stress_winner_flipped,
            "ranked": [
                {"ref": r.ref, "rank_value": round(r.rank_value, 6),
                 "evsi": r.evsi.as_dict(), "expected_minutes": r.expected_minutes,
                 "stop_threshold": round(r.stop_threshold, 6), "ordinal": r.ordinal}
                for r in self.ranked
            ],
        }


def _rank_value(ev: RobustEVSI, expected_minutes: float, burden_minutes: float) -> float:
    denom = max(expected_minutes + burden_minutes, 1e-6)
    return ev.lcb / denom


def _stop_threshold(c: "DiagnosticCandidate", lambda_time: float, burden_cost: float) -> float:
    """Minutes the robust EVSI must clear to be worth measuring (spec §6.4): the
    minutes-numeraire time cost PLUS this candidate's own administration burden (matching
    the ranking denominator), plus the global burden floor."""

    return lambda_time * c.expected_minutes + c.burden_minutes + burden_cost


def rank_feasible(
    candidates: Sequence[DiagnosticCandidate],
    loss_table: AL.LossTable,
    *,
    quantile: float = ROBUST_QUANTILE,
    lambda_time: float = LAMBDA_TIME,
    burden_cost: float = BURDEN_COST,
    perturbation_delta: float = PERTURBATION_DELTA,
) -> RankResult:
    """Rank feasible diagnostic questions by robust EVSI per minute and apply the LCB
    stop rule (spec §6.4). Abstains when the ranking winner or the downstream action
    flips across the credible set or the ±0.15 stress (spec §6.5)."""

    if not candidates:
        return RankResult((), None, True, False, "stop", "no_feasible_question", False)

    scored: list[tuple[DiagnosticCandidate, RobustEVSI, float]] = []
    for c in candidates:
        ev = robust_evsi(c.members, c.prior, loss_table, quantile=quantile)
        scored.append((c, ev, _rank_value(ev, c.expected_minutes, c.burden_minutes)))
    scored.sort(key=lambda t: (t[2], t[0].ref), reverse=True)

    ranked = tuple(
        RankedCandidate(
            ref=c.ref, evsi=ev, rank_value=rv, expected_minutes=c.expected_minutes,
            stop_threshold=_stop_threshold(c, lambda_time, burden_cost), ordinal=i + 1,
        )
        for i, (c, ev, rv) in enumerate(scored)
    )
    best_cand, best_ev, _ = scored[0]
    # The stop threshold carries the SAME per-candidate burden the ranking denominator uses
    # (audit M1/F3): a costly-to-administer question must clear its own burden to be worth
    # measuring, not just a shared constant. Pre-fix the stop rule used only the global
    # burden_cost (0.0), so a high per-candidate burden could not force a stop.
    stop_threshold = _stop_threshold(best_cand, lambda_time, burden_cost)

    # Stop rule (§6.4): halt when the best robust EVSI does not clear the minutes cost.
    should_stop = best_ev.lcb <= stop_threshold

    # Winner-flip under the ±0.15 stress (§6.5): re-rank on the mean member's stressed
    # matrices and see whether the top ref changes.
    stress_winner_flipped = _winner_flips_under_stress(scored, loss_table, quantile,
                                                       perturbation_delta, lambda_time, burden_cost)
    # Action-flip under the ±0.15 stress (§6.5, audit H2/F2): the winner's per-emission
    # recommended action must be stable across the stress, not just its rank. Compares the
    # stressed argmin actions against the nominal ones for the winning candidate -- the
    # decision quantity the ranking would otherwise hide.
    stress_action_flipped = _action_flips_under_stress(
        best_cand, loss_table, perturbation_delta
    )
    abstain = (not should_stop) and (
        best_ev.action_flipped or stress_winner_flipped or stress_action_flipped
    )

    if should_stop:
        return RankResult(ranked, best_cand.ref, True, False, "stop",
                          "lcb_evsi_below_minutes_cost", stress_winner_flipped)
    if abstain:
        if best_ev.action_flipped:
            reason = "downstream_action_flip"
        elif stress_action_flipped:
            reason = "stress_action_flip"
        else:
            reason = "stress_winner_flip"
        return RankResult(ranked, best_cand.ref, False, True, "abstain", reason,
                          stress_winner_flipped)
    return RankResult(ranked, best_cand.ref, False, False, "measure",
                      "positive_robust_net_value", stress_winner_flipped)


def _action_flips_under_stress(
    best: DiagnosticCandidate,
    loss_table: AL.LossTable,
    delta: float,
) -> bool:
    """Does the winning candidate's per-emission recommended action flip between its
    nominal mean-member table and either ±``delta`` stressed table? (§6.5). Compares the
    member-dependent decision quantity (``argmin_by_emission`` and the prior-argmin
    ``current_action``) rather than the EVSI magnitude, so a stress that reverses which
    action you would take -- without changing the ranking -- still forces an abstain."""

    if not best.members:
        return False
    nominal = evsi_for_conditionals(best.members[0], best.prior, loss_table)
    for idx in (0, 1):
        stressed_member = stress_matrices(best.members[0], delta)[idx]
        stressed = evsi_for_conditionals(stressed_member, best.prior, loss_table)
        if stressed.current_action != nominal.current_action:
            return True
        for emission, action in stressed.argmin_by_emission.items():
            nominal_action = nominal.argmin_by_emission.get(emission)
            if nominal_action is not None and nominal_action != action:
                return True
    return False


def _winner_flips_under_stress(
    scored: Sequence[tuple[DiagnosticCandidate, RobustEVSI, float]],
    loss_table: AL.LossTable,
    quantile: float,
    delta: float,
    lambda_time: float,
    burden_cost: float,
) -> bool:
    nominal_best = scored[0][0].ref
    for stressed in ("toward", "away"):
        idx = 0 if stressed == "toward" else 1
        re_scored: list[tuple[str, float]] = []
        for c, _ev, _rv in scored:
            stressed_members = tuple(stress_matrices(m, delta)[idx] for m in c.members)
            ev = robust_evsi(stressed_members, c.prior, loss_table, quantile=quantile)
            re_scored.append((c.ref, _rank_value(ev, c.expected_minutes, c.burden_minutes)))
        re_scored.sort(key=lambda t: (t[1], t[0]), reverse=True)
        if re_scored and re_scored[0][0] != nominal_best:
            return True
    return False

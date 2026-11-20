"""The successor's value of a post-miss probe (G2 design §2b): ask the probe, then act on its result, priced against
acting now without it, over the locked hypotheses, in the router objective's own terms. Unserved: nothing under
``src`` calls :func:`evaluate_probe`; the comparison report and the tests do, until the behaviour step wires it.

**What is computed.** For the effective prior ``p(h)`` and the channel ``L(r | h)`` (:mod:`diagnostic_payload`)::

    a*(r)     = argmax over {no repair, each repair} of Σh p(h | r)·Q̄_belief(probe, a | h)
    Q(probe)  = Σh p(h) Σr L(r | h)·Qpath(probe, a*(r) | h)

The repair policy sees the result, never the hypothesis, so ``Q(probe)`` is at most ``Σh p(h)·max_a Qpath(probe, a |
h)`` (the record's ``clairvoyant``), reached only by a channel that separates every cause. ``a*(r)`` is chosen on
each option's ``Q̄`` in the belief's own world (the rollouts' :meth:`_Model._belief_model`: believed parameters,
noise of its own), as the predecessor's probe chooses its repair, so the choice never sees the true path's noise.
Each acting-now arm is ``Σh p(h)·Qpath(a | h)``, the same option with no probe before it.

**Where each piece lives.** A path (:class:`objective._Ledger`) is the objective's terms, accrued by the rollouts'
own segment and tail (:meth:`_Model._segment`, :meth:`_Model.run_tail`): the probe's minutes are its segment's κ
integral and the undated uses during it; a repair's effect is AD's practice update with its slope by the true
hypothesis (:meth:`_Model._cause_gain` over ``CauseSplit``, through :func:`_world`); the tail and ``T_C`` follow once.
Nothing here adds a term: no information bonus, no avoided-teaching minutes, no EIG. The probe segment observes
nothing on the binary-ability scale (its topic is dropped for the segment), because its one answer is this
channel's result and a second, independent observation of the same answer would count it twice.

**Effects by hypothesis** (owner decision 2, :class:`diagnostic_payload.OwnerDecisions`): a repair covering the true
hypothesis learns at that hypothesis's cause-class slope (``γ_gap``, ``γ_slip``, or ``γ`` for unknown); one that does
not is ordinary practice at ``γ``. Without cause slopes in the inputs every repair is practice at ``γ``. **No
information** (an exposed answer, a missing channel under decision 1) is one posterior, the prior: the policy then
picks the prior's repair after the probe, and the probe is priced at its time alone.

Paths whose effect is the same are computed once: a repair's path depends on the hypothesis only through its effect
key (:func:`diagnostic_payload.effect_key`), so an option has at most four paths, whatever the number of hypotheses.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
import time
from typing import Any

import numpy as np

from learnloop.router_objective import diagnostic_payload as DP
from learnloop.router_objective.objective import _LEDGER_FIELDS, Evaluation, Valued, _Ledger, _terms, numeric_choice
from learnloop.router_objective.rollouts import _beta_draw, _Model, _State
from learnloop.router_objective.types import PROBE, SEQUENCE, Action, Inputs

#: This policy's version (a scoped probe-policy version: the objective's own versions do not move for it).
POLICY_VERSION = "diagnostic_probe_value_v1"
#: The acting-now arms' refs: ``act_now:none`` and ``act_now:<repair ref>``.
ACT_NOW = "act_now:"
NONE = "none"
#: A repair's noise stream, the predecessor's probe repair's (rollouts ``_probe``): the same stream with and without
#: the probe before it, so the two arms differ by the probe and not by the repair's duration draw.
REPAIR_STREAM = 2
#: The offer's declined branch's stream, the rollouts' (``_Model.value``).
DECLINED_STREAM = 1


@dataclass(frozen=True)
class ProbeValuation:
    """The candidate's row (the probe's policy, a sequence holding it, or an offer declining into it) and each
    acting-now arm's, in the objective's :class:`Valued` terms; the choice among them (``π_Q``'s rule, acting now first
    in the support order, so a probe that only ties acting now is not chosen); and the record."""

    valued: tuple[Valued, ...]
    choice: str | None
    record: Mapping[str, Any]

    def by_ref(self) -> dict[str, Valued]:
        return {row.ref: row for row in self.valued}


def _weighted(parts: Sequence[tuple[float, _Ledger]]) -> _Ledger:
    """``Σ w·ledger``, term by term, per draw (each branch's path weighted by its probability)."""

    return _Ledger(*(sum(w * getattr(ledger, name) for w, ledger in parts) for name in _LEDGER_FIELDS))


@contextmanager
def _world(model: _Model, lo: int | None, key: str) -> Iterator[None]:
    """While a repair runs, its topic learns as it would if the hypothesis behind ``key`` were true: the cause-class
    slope through the rollouts' own ``_cause_gain`` (a one-hot split), or practice's ``γ`` (no split) when the repair
    does not cover it or the inputs carry no cause slopes. The topic's own split is restored after, so no other path
    and no tail sees it."""

    if lo is None or key == NONE:
        yield
        return
    absent = object()
    saved = model.cause_weights.get(lo, absent)
    if key in DP.CLASSES_ORDER and model.inputs.learning.causes is not None:
        model.cause_weights[lo] = tuple(1.0 if name == key else 0.0 for name in DP.CLASSES_ORDER)
    else:
        model.cause_weights.pop(lo, None)
    try:
        yield
    finally:
        if saved is absent:
            model.cause_weights.pop(lo, None)
        else:
            model.cause_weights[lo] = saved  # type: ignore[assignment]


@dataclass(frozen=True)
class _Place:
    """Where the probe sits: the steps before it and after it (each with its stream), the probe's own stream, the
    offer wrapping it (None: none), and the record's words for the position."""

    probe: Action
    #: the probe itself or the sequence holding it (whose delayed checks, if any, follow the tail as ``_do``'s do)
    inner: Action
    before: tuple[tuple[Action, int], ...]
    after: tuple[tuple[Action, int], ...]
    stream: int
    offer: Action | None
    position: str


def _place(model: _Model, action: Action, base_stream: int) -> _Place:
    offer = None
    if action.accept is not None:
        if action.declined is None:
            raise ValueError("an offer carries a diagnostic probe only in its declined branch")
        offer, action, base_stream = action, action.declined, DECLINED_STREAM
    if action.kind == PROBE and action.diagnostic is not None:
        return _Place(action, action, (), (), base_stream, offer,
                      "declined branch of an offer" if offer is not None else "standalone")
    if action.kind == SEQUENCE:
        steps = model._steps(action, base_stream)
        at = [i for i, (step, _stream) in enumerate(steps) if step.diagnostic is not None]
        if len(at) != 1:
            raise ValueError("a sequence holds exactly one diagnostic probe for this evaluator")
        i = at[0]
        position = f"step {i} of a sequence" + (" in the declined branch of an offer" if offer is not None else "")
        return _Place(steps[i][0], action, tuple(steps[:i]), tuple(steps[i + 1:]), steps[i][1], offer, position)
    raise ValueError("no diagnostic payload: the action is valued by the rollouts, not this evaluator")


class _Paths:
    """Every path one model needs: the steps before the probe once, then per option and effect key a copy that runs
    the probe (or not), the option, the steps after and the tail. Counts the tails it runs."""

    def __init__(self, model: _Model, place: _Place, lo: int | None, commitments: Sequence[tuple[str, float]]):
        self.model, self.place, self.lo, self.commitments = model, place, lo, tuple(commitments)
        self.tails = 0

    def _run(self, state: _State, ledger: _Ledger, steps: Sequence[tuple[Action, int]], at: np.ndarray,
             spent: np.ndarray, done: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        for step, stream in steps:
            at, spent, _good = self.model._segment(state, ledger, step, start=at, spent=spent,
                                                   minutes=self.model._durations(step, stream), dated_done=done,
                                                   stream=stream)
        return at, spent

    def build(self, options: Sequence[tuple[str, DP.RepairOption | None]], keys: Mapping[str, Sequence[str]], *,
              with_probe: bool) -> dict[tuple[str, str], _Ledger]:
        model, k = self.model, self.model.k
        state, ledger = model.initial(), _Ledger.zeros(k)
        done = np.zeros((k, len(model.dated)), dtype=bool)
        at, spent = self._run(state, ledger, self.place.before, np.zeros(k), np.zeros(k), done)
        if with_probe:
            # The probe's time on the one clock, observing nothing on the ability scale (its result is the channel's).
            silent = replace(self.place.probe, item_los=(), diagnostic=None)
            at, spent, _good = model._segment(state, ledger, silent, start=at, spent=spent,
                                              minutes=model._durations(self.place.probe, self.place.stream),
                                              dated_done=done, stream=self.place.stream)
        out: dict[tuple[str, str], _Ledger] = {}
        for ref, option in options:
            for key in keys[ref]:
                path, terms, path_done = state.copy(), ledger.copy(), done.copy()
                end, used = at, spent
                if option is not None:
                    with _world(model, self.lo, key):
                        end, used = self._run(path, terms, ((option.action, REPAIR_STREAM),), end, used, path_done)
                end, used = self._run(path, terms, self.place.after, end, used, path_done)
                commitments = [(model.index[lo], end + float(days)) for lo, days in self.commitments
                               if lo in model.index]
                model.run_tail(path, terms, today_minutes=float(model.inputs.session_minutes) + used, after=end,
                               dated_done=path_done, commitments=commitments)
                self.tails += 1
                out[(ref, key)] = terms
        return out


def _choose(options: Sequence[tuple[str, DP.RepairOption | None]], hypotheses: Sequence[DP.Hypothesis],
            q: Mapping[tuple[str, str], float], posterior: Mapping[str, float]) -> tuple[str, dict[str, float]]:
    """The option with the highest posterior-expected ``Q̄`` (the first in option order on a tie: no repair first)."""

    expected = {ref: sum(posterior[h.id] * q[(ref, DP.effect_key(option, h))] for h in hypotheses)
                for ref, option in options}
    best = options[0][0]
    for ref, _option in options:
        if expected[ref] > expected[best]:
            best = ref
    return best, expected


def evaluate_probe(inputs: Inputs, action: Action, *, decisions: DP.OwnerDecisions, draws: int, seed: str,
                   wait_feasible: bool = True, base_stream: int = 0, merged_sessions: bool = False,
                   consistent_review_draw: bool = False, held_ad_link: bool = False,
                   clock: Callable[[], float] = time.perf_counter) -> ProbeValuation:
    """The value of the diagnostic probe ``action`` carries (alone, as one step of a sequence, or in an offer's
    declined branch) against acting now, with its record. It runs every acting-now path, then (unless a hard stop
    keeps the probe out) every path with the probe in the true world and in the belief's, picks each result's repair
    on the belief's paths, and weights the true paths by ``p(h)·L(r | h)`` into one ledger; an offer mixes that
    ledger with its accepted branch. ``decisions``: the owner's open decisions, explicitly.
    ``wait_feasible``: whether the boundary has room to wait (decision 3 reads it). The switches are the rollouts'
    (:func:`rollouts.evaluate`'s), so a comparison runs at the boundary's own settings. ``clock`` times the record's
    cost only; no value depends on it."""

    started = clock()
    model = _Model(inputs, int(draws), seed, merged_sessions=merged_sessions,
                   consistent_review_draw=consistent_review_draw, held_ad_link=held_ad_link)
    place = _place(model, action, base_stream)
    payload: DP.DiagnosticProbe = place.probe.diagnostic
    exposed_by = None
    if place.offer is not None and not payload.exposed:
        # The offer's win released the feedback; a probe after its "Not now" answers exposed.
        payload, exposed_by = replace(payload, exposed=True), "the offer released the miss's feedback"
    hypotheses = payload.hypotheses
    prior = payload.effective_prior()
    options: list[tuple[str, DP.RepairOption | None]] = [(NONE, None), *((o.ref, o) for o in payload.repairs)]
    keys = {ref: sorted({DP.effect_key(option, h) for h in hypotheses}) for ref, option in options}
    lo = model.index.get(payload.topic)
    commitments = place.inner.commitments
    excluded: dict[str, Any] = {}
    now_options = list(options)
    if not wait_feasible and not decisions.no_intervention_without_wait:
        now_options = [(ref, option) for ref, option in options if option is not None]
        excluded[f"{ACT_NOW}{NONE}"] = "decision 3: no room to wait removes no intervention"

    true_paths = _Paths(model, place, lo, commitments)
    belief_paths = _Paths(model._belief_model(), place, model._belief_model().index.get(payload.topic), commitments)
    now = true_paths.build(now_options, keys, with_probe=False)
    now_tails, now_done = true_paths.tails, clock()
    rows: list[Valued] = []
    branch_terms: dict[str, Any] = {"act_now": {ref: {key: _terms(now[(ref, key)], model) for key in keys[ref]}
                                                for ref, _option in now_options}}
    record: dict[str, Any] = {
        "version": POLICY_VERSION,
        "decisions": decisions.record(),
        "given": {"payload": payload.summary(), "position": place.position, "exposed_by": exposed_by,
                  "draws": model.k, "seed": seed, "wait_feasible": bool(wait_feasible),
                  "topic_valued": lo is not None},
        "excluded": excluded,
    }
    for ref, option in now_options:
        ledger = _weighted([(prior[h.id], now[(ref, DP.effect_key(option, h))]) for h in hypotheses])
        rows.append(Valued(ref=f"{ACT_NOW}{ref}", kind="act_now", q_draws=tuple(float(v) for v in ledger.q),
                           terms=_terms(ledger, model), extra={"option": ref}, choosable=True))
    values: dict[str, Any] = {"act_now": {row.ref: row.q for row in rows}}

    if payload.hard_stops:
        excluded["probe"] = list(payload.hard_stops)
    else:
        probed = true_paths.build(options, keys, with_probe=True)
        believed = belief_paths.build(options, keys, with_probe=True)
        probe_done = clock()
        q_belief = {key: float(ledger.q.mean()) for key, ledger in believed.items()}
        use, table = DP.posterior_table(payload)
        prior_choice, prior_expected = _choose(options, hypotheses, q_belief, prior)
        results = []
        weights: dict[tuple[str, str], float] = {}
        for row in table:
            choice, expected = _choose(options, hypotheses, q_belief, row["posterior"])
            results.append({"result": row["result"], "p": row["p"], "posterior": row["posterior"], "choice": choice,
                            "q_belief": expected})
            for h in hypotheses:
                key = (choice, DP.effect_key(dict(options)[choice], h))
                weights[key] = weights.get(key, 0.0) + row["joint"][h.id]
        prior_ledger = _weighted([(prior[h.id], probed[(prior_choice, DP.effect_key(dict(options)[prior_choice], h))])
                                  for h in hypotheses])
        changes = any(row["choice"] != prior_choice for row in results)
        # Every result choosing the prior's repair is the prior's path exactly: no information, by construction.
        policy = _weighted([(w, probed[key]) for key, w in sorted(weights.items())]) if changes else prior_ledger
        clairvoyant = sum(prior[h.id] * max(float(probed[(ref, DP.effect_key(option, h))].q.mean())
                                            for ref, option in options) for h in hypotheses)
        branch_terms["probe"] = {ref: {key: _terms(probed[(ref, key)], model) for key in keys[ref]}
                                 for ref, _option in options}
        record.update(channel_use=use, results=results, prior_choice=prior_choice, prior_q_belief=prior_expected,
                      policy_changes_with_result=changes)
        values.update(probe_policy=float(policy.q.mean()), probe_then_prior_choice=float(prior_ledger.q.mean()),
                      information=float(policy.q.mean()) - float(prior_ledger.q.mean()) if changes else 0.0,
                      clairvoyant=clairvoyant)
        candidate, extra = policy, {"policy": {row["result"]: row["choice"] for row in results}}
        if place.offer is not None:
            a, b = place.offer.accept or (1.0, 1.0)
            p = _beta_draw(model.streams.offer_u, float(a), float(b))
            accepted, _state, _minutes = model._do(replace(place.offer, accept=None))
            true_paths.tails += 1
            candidate = _Ledger.mix(p, accepted, policy)
            record["offer"] = {"p_accept": float(p.mean()), "accepted": float(accepted.q.mean()),
                               "declined": float(policy.q.mean()),
                               "declined_q_draws": [float(v) for v in policy.q]}
        rows.insert(0, Valued(ref=action.ref, kind=action.kind, q_draws=tuple(float(v) for v in candidate.q),
                              terms=_terms(candidate, model), extra=extra, choosable=action.choosable))
    record["branch_terms"] = branch_terms
    record["values"] = values
    support = [row.ref for row in rows if row.ref.startswith(ACT_NOW)] + [row.ref for row in rows
                                                                           if not row.ref.startswith(ACT_NOW)]
    choice, rule = (numeric_choice(Evaluation(valued=tuple(rows), draws=model.k, cutoff=model.cutoff, seed=seed,
                                              elapsed_ms=0, complete=True), support) if rows else (None, {}))
    record["choice"] = rule
    finished = clock()
    # Split, so a reader can tell the acting-now arms' cost from what the probe's own paths (true and believed) add.
    record["cost"] = {"ms": (finished - started) * 1000.0, "rollouts": true_paths.tails + belief_paths.tails,
                      "ms_act_now": (now_done - started) * 1000.0, "rollouts_act_now": now_tails,
                      "ms_probe": ((probe_done - now_done) * 1000.0) if not payload.hard_stops else 0.0,
                      "hypotheses": len(hypotheses), "results": len(record.get("results", ())),
                      "repairs": len(payload.repairs), "effect_paths": sum(len(v) for v in keys.values())}
    return ProbeValuation(valued=tuple(rows), choice=choice, record=record)


__all__ = ["ACT_NOW", "DECLINED_STREAM", "NONE", "POLICY_VERSION", "REPAIR_STREAM", "ProbeValuation", "evaluate_probe"]

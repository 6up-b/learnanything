"""RO6 (spec_router_objective_v1 §10): the learned tail at a decision. ``Ṽ = V_tail + ŵ·V_residual`` inside the numeric
policy's value.

At a ``plan_block`` decision at the tag with ``[router_objective] learned_tail`` on, before the rollouts:

1. each candidate's features from the decision's frozen inputs and RO0's snapshot readers (the pending reports and
   the candidates' mastery, read by ``decision_state``'s own functions, so the trace's frozen features and a rebuild
   from RO0's receipt are the same function of the same numbers);
2. the fitted Q evaluation as of now (:func:`learnloop.router_objective.tail_data.fits`): the current generator
   version's own fit, or with none of its transitions yet the latest earlier version's ("version k+1 uses the
   result"), else none (the residual zero). It is refit at every decision, so every mixture change is followed by a
   refit;
3. ``ŵ`` as of now from the randomized stop-coin contrasts whose windows closed (:func:`learned_tail.residual_weight`);
4. ``V_residual(a) = ρ̂(x, a)`` per candidate; the numeric policy's argmax and its tie rule run on ``Ṽ``.

Everything is frozen into the decision's trace (``residual``: ``ŵ`` with its slope and rank, the fit's
coefficients, standardization, version and size, and per candidate the features, ``V_tail``, ``V_residual`` and
``Ṽ``), so the trace's terms recompute. No model request; a failure leaves the residual out (the trace says why)
and the numeric policy as mvp-0.48's.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import logging
import time
from typing import Any

from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import tail_data as TD

LOG = logging.getLogger(__name__)

VERSION = "ro6_learned_tail_v1"


def features(connection: Any, inputs: Any, actions: Sequence[Any], *, now_iso: str) -> tuple[dict[str, tuple[float, ...]],
                                                                                            dict[str, Any]]:
    """Each candidate's features at serve time (the module docstring's step 1)."""

    from learnloop.router_objective import decision_state as DS

    topic_by_lo = {topic.lo: topic for topic in inputs.topics}
    los = list(dict.fromkeys(lo for action in actions for lo in action.item_los if lo in topic_by_lo))
    pending = DS._pending_reports(connection, now_iso)
    total = sum(value for value in pending.values() if value is not None)
    snapshot = DS._lo_rows(connection, los, {})
    numbers = {lo: LT.TopicNumbers(eta=float(topic_by_lo[lo].eta_mean), eta_var=float(topic_by_lo[lo].eta_var),
                                   practiced=bool(topic_by_lo[lo].practiced),
                                   stability=float(topic_by_lo[lo].stability),
                                   elapsed_days=float(topic_by_lo[lo].elapsed_days)) for lo in los}
    nearest = min((float(use.at_days) for use in inputs.dated), default=None)
    remembered = float(inputs.price.remembered)
    belief = LT.belief(session_minutes=float(inputs.session_minutes), remembered=remembered,
                       nearest_goal_days=nearest, horizon_days=float(inputs.horizon_days), pending_reports=total,
                       mastery=TD.snapshot_mastery(snapshot, los), topics=list(numbers.values()))
    out = {}
    for action in actions:
        own = tuple(numbers[lo] for lo in dict.fromkeys(action.item_los) if lo in numbers)
        out[action.ref] = LT.vector(belief, LT.ActionView(ref=action.ref, kind=action.kind,
                                                          minutes=float(action.minutes or 0.0), topics=own),
                                    remembered=remembered)
    return out, {"pending_reports": total, "candidate_los": len(los),
                 "mastery_recorded": len(TD.snapshot_mastery(snapshot, los)), "belief": belief.as_tuple()}


def residual(repository: Any, config: Any, *, inputs: Any, actions: Sequence[Any], now_iso: str,
             generator_now: str, clock: Any = time.monotonic) -> dict[str, Any]:
    """The decision's residual record (module docstring), or its failure: ``{"status": ...}``."""

    started = clock()
    try:
        with repository.connection() as connection:
            phi, basis = features(connection, inputs, actions, now_iso=now_iso)
            rows = TD.logged(connection, config, at=now_iso)
            fitted = TD.fits(connection, config, at=now_iso, rows=rows)
            fit_ms = int(round((clock() - started) * 1000))
            contrasts, censored_contrasts = TD.contrasts(connection, config, rows, at=now_iso)
        weight = LT.residual_weight(contrasts, prior_sd=float(config.router_objective.residual_weight_prior_sd),
                                    at=now_iso)
        model, basis_of_fit = fitted.for_serving(generator_now)
        if model is None:
            model = LT.prior_fit(float(config.router_objective.residual_prior_sd), generator_now)
        values = {ref: model.value(vector) for ref, vector in phi.items()}
        fit_record = model.as_dict()
        for key in ("mean", "sd", "coef"):
            fit_record[key] = [_exact(value) for value in fit_record[key]]
        return {
            "status": "applied", "version": VERSION, "w_hat": weight.w_hat, "weight": weight.as_dict(),
            "contrasts": {"n": len(contrasts), "censored": censored_contrasts},
            "generator": generator_now, "fit_basis": basis_of_fit, "fit": fit_record,
            "transitions": {"n": len(fitted.steps.transitions), "censored": dict(fitted.steps.censored),
                            "change_points": len(fitted.steps.change_points), "decisions": fitted.decisions,
                            "versions": len(fitted.order)},
            "basis": basis, "fit_ms": fit_ms, "elapsed_ms": int(round((clock() - started) * 1000)),
            "candidates": {ref: {"features": [_exact(v) for v in phi[ref]], "v_residual": values[ref]} for ref in phi},
            "claim": "the logger's value plus one small improvement step; no improvement guarantee",
        }
    except Exception as exc:  # noqa: BLE001 - the residual never blocks the numeric policy
        LOG.warning("router objective: the learned tail was not computed", exc_info=True)
        return {"status": "failed", "version": VERSION, "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                "elapsed_ms": int(round((clock() - started) * 1000))}


def _exact(value: float) -> str:
    """A number the trace keeps exactly (its ``repr``): the trace rounds every float to six places, and the fit's
    standardized coefficients and the features must recompute ``V_residual`` to float precision."""

    return repr(float(value))


def applied(record: Mapping[str, Any] | None) -> bool:
    return isinstance(record, Mapping) and record.get("status") == "applied"


def shifted(evaluation: Any, record: Mapping[str, Any]) -> Any:
    """The evaluation the numeric policy's argmax reads: each candidate's draws moved by ``ŵ·V_residual`` (a
    constant per candidate, so the paired precision is the tail's)."""

    from dataclasses import replace

    w_hat = float(record.get("w_hat") or 0.0)
    values = record.get("candidates") or {}
    rows = tuple(replace(row, q_draws=tuple(float(q) + w_hat * float((values.get(row.ref) or {}).get("v_residual") or 0.0)
                                            for q in row.q_draws)) for row in evaluation.valued)
    return replace(evaluation, valued=rows)


def candidate_terms(record: Mapping[str, Any], ref: str, v_tail: float | None) -> dict[str, Any]:
    """§10's per-candidate trace terms: ``ŵ``, ``V_tail``, ``V_residual`` and ``Ṽ``."""

    w_hat = float(record.get("w_hat") or 0.0)
    v_residual = (record.get("candidates") or {}).get(ref, {}).get("v_residual")
    return {"w_hat": w_hat, "v_tail": v_tail, "v_residual": v_residual,
            "v_tilde": (v_tail + w_hat * float(v_residual)) if v_tail is not None and v_residual is not None else None}


__all__ = ["VERSION", "applied", "candidate_terms", "features", "residual", "shifted"]

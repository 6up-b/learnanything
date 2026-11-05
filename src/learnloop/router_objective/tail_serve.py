"""RO6 (spec_router_objective_v1 §10): the learned tail at a decision. ``Ṽ = V_tail + ŵ·V_residual`` inside the numeric
policy's value.

At a ``plan_block`` decision at the tag with ``[router_objective] learned_tail`` on, before the rollouts:

1. each candidate's features from the decision's frozen inputs and its :func:`snapshot` (the pending reports and
   the LOs' mastery, read by ``decision_state``'s own readers in the decision's own thread at its moment, before the
   prefetch job runs: Codex review F4), so the trace's frozen features and a rebuild from RO0's receipt are the same
   function of numbers read at the decision;
2. the fitted Q evaluation as of now (:func:`learnloop.router_objective.tail_data.fits`): the current generator
   version's own fit, or with none of its transitions yet the latest earlier version's ("version k+1 uses the
   result"), else none (the residual zero). It is refit at every decision, so every mixture change is followed by a
   refit;
3. ``ŵ`` as of now from the randomized stop-coin contrasts whose windows closed (:func:`learned_tail.residual_weight`);
4. ``V_residual(a) = ρ̂(x, a)`` per candidate; the numeric policy's argmax and its tie rule run on ``Ṽ``;
5. the latest earlier decision's cutoff (:func:`previous_cutoff`): after the rollouts at this decision's own
   cutoff, the candidates are valued again with every rollout run at ``C_prev`` (``residual.previous.q``) and their
   features taken at ``C_prev``'s span (``residual.previous.features``), so that decision's backup reads this state's
   value at its own cutoff exactly (Codex re-review F3); this decision's ``Q̄`` and choice are unchanged by it. It
   runs in the numeric policy's prefetch job after the answer is published, never on the learner's serving path:
   with no prefetch job (the no-model branch) it is not run, and the transition into this decision is censored
   ``cutoff_unmatched`` (:func:`not_on_the_serving_path`, RO6's landing ruling R3).

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


SNAPSHOT_VERSION = "ro6_tail_snapshot_v2"


def snapshot(repository: Any, *, now_iso: str) -> dict[str, Any]:
    """The decision's own reads of the residual's mutable inputs, taken **at the decision's moment** (Codex review of
    RO6, F4): the pending reports (``decision_state``'s reader) and every LO's mastery numbers (RO0 row 9's), so a
    diagnosis queued or a projection moved after ``now_iso`` while the prefetch job waits for its turn never enters
    the decision's features. The caller takes it in the decision's own thread, before any asynchronous work, and
    hands it to :func:`residual`."""

    from learnloop.router_objective import checks as C
    from learnloop.router_objective import decision_state as DS

    with repository.connection() as connection:
        # RO6's landing ruling R7: each topic's check support as of the decision (the coin's draw), so the terms no
        # check could measure are left out of both the realized and the predicted contrast.
        support, support_basis = C.support_at(connection, now_iso)
        pending = DS._pending_reports(connection, now_iso)
        mastery: dict[str, dict[str, Any]] = {}
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'learning_object_mastery'"
                              ).fetchone() is not None:
            for lo, mean, variance in connection.execute(
                    "SELECT learning_object_id, logit_mean, logit_variance FROM learning_object_mastery"):
                mastery[str(lo)] = {"logit_mean": DS._round(mean), "logit_variance": DS._round(variance)}
    return {"version": SNAPSHOT_VERSION, "at": now_iso, "pending_reports": dict(pending), "los": mastery,
            "support": {str(lo): float(r) for lo, r in sorted(support.items())}, "support_basis": support_basis}


def measurable(frozen: Mapping[str, Any] | None, inputs: Any, *, now_iso: str) -> dict[str, Any] | None:
    """RO6's landing ruling R7: the decision's measurable terms, from its :func:`snapshot`: each topic's check
    support as of the draw, and the valued topics with none (``unmeasured``: their undated uses are outside the
    measurable target, left out of the realized return and, through ``value.evaluate``'s ``unmeasured``, out of the
    tail's predicted contrast). None with no decision-time snapshot holding the support."""

    if not isinstance(frozen, Mapping) or frozen.get("at") != now_iso or not isinstance(frozen.get("support"), Mapping):
        return None
    support = {str(lo): float(r) for lo, r in frozen["support"].items()}
    unmeasured = sorted(topic.lo for topic in inputs.topics if support.get(topic.lo, 0.0) <= 0.0)
    return {"support": support, "basis": frozen.get("support_basis"), "unmeasured": unmeasured,
            "label": "w^ is calibrated on the measurable part of the return only (terms a check could measure as of "
                     "the draw)"}


def features(inputs: Any, actions: Sequence[Any], *, frozen: Mapping[str, Any],
             cutoff_days: float | None = None) -> tuple[dict[str, tuple[float, ...]], dict[str, Any]]:
    """Each candidate's features at serve time (the module docstring's step 1), from the decision's ``frozen``
    :func:`snapshot` and its frozen inputs only: nothing here reads the vault. ``cutoff_days``: the cutoff the
    features are taken at (None: the decision's own; an earlier decision's carried cutoff for its backup)."""

    topic_by_lo = {topic.lo: topic for topic in inputs.topics}
    los = list(dict.fromkeys(lo for action in actions for lo in action.item_los if lo in topic_by_lo))
    pending = frozen.get("pending_reports") or {}
    total = sum(value for value in pending.values() if value is not None)
    snapshot = {lo: (frozen.get("los") or {}).get(lo) or {} for lo in los}
    numbers = {lo: LT.TopicNumbers(eta=float(topic_by_lo[lo].eta_mean), eta_var=float(topic_by_lo[lo].eta_var),
                                   practiced=bool(topic_by_lo[lo].practiced),
                                   stability=float(topic_by_lo[lo].stability),
                                   elapsed_days=float(topic_by_lo[lo].elapsed_days)) for lo in los}
    nearest = min((float(use.at_days) for use in inputs.dated), default=None)
    remembered = float(inputs.price.remembered)
    belief = LT.belief(session_minutes=float(inputs.session_minutes), remembered=remembered,
                       nearest_goal_days=nearest, horizon_days=float(inputs.horizon_days), pending_reports=total,
                       mastery=TD.snapshot_mastery(snapshot, los), topics=list(numbers.values()),
                       cutoff_days=float(inputs.cutoff) if cutoff_days is None else float(cutoff_days))
    out = {}
    for action in actions:
        own = tuple(numbers[lo] for lo in dict.fromkeys(action.item_los) if lo in numbers)
        out[action.ref] = LT.vector(belief, LT.ActionView(ref=action.ref, kind=action.kind,
                                                          minutes=float(action.minutes or 0.0), topics=own),
                                    remembered=remembered)
    return out, {"pending_reports": total, "candidate_los": len(los),
                 "mastery_recorded": len(TD.snapshot_mastery(snapshot, los)), "belief": belief.as_tuple()}


def residual(repository: Any, config: Any, *, inputs: Any, actions: Sequence[Any], now_iso: str,
             generator_now: str, frozen: Mapping[str, Any] | None, clock: Any = time.monotonic) -> dict[str, Any]:
    """The decision's residual record (module docstring), or its failure: ``{"status": ...}``. ``frozen``: the
    decision's :func:`snapshot`, taken at its moment; with none the residual is left out (``no_snapshot``), never
    computed from a later read."""

    started = clock()
    if not isinstance(frozen, Mapping) or frozen.get("at") != now_iso:
        return {"status": "no_snapshot", "version": VERSION,
                "error": "no decision-time snapshot of the residual's inputs", "elapsed_ms": 0}
    try:
        phi, basis = features(inputs, actions, frozen=frozen)
        basis["snapshot"] = {"version": frozen.get("version"), "at": frozen.get("at")}
        with repository.connection() as connection:
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
        previous = previous_cutoff(rows, inputs, now_iso=now_iso)
        if previous is not None and previous["status"] == CARRIED:
            # The next state's features at the carried cutoff (Codex re-review F3), the same function.
            at_previous, _ = features(inputs, actions, frozen=frozen, cutoff_days=float(previous["cutoff_days"]))
            previous["features"] = {ref: [_exact(v) for v in vector] for ref, vector in at_previous.items()}
        return {
            "status": "applied", "version": VERSION, "features_version": LT.FEATURES_VERSION,
            "w_hat": weight.w_hat, "weight": weight.as_dict(), "previous": previous,
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


CARRIED = "carried"
SAME_CUTOFF = "same_cutoff"
PAST_CUTOFF = "past_cutoff"


def previous_cutoff(rows: Sequence[Any], inputs: Any, *, now_iso: str) -> dict[str, Any] | None:
    """§3.2 for the backup (Codex re-review F3): the latest earlier logged decision (``tail_data.Logged``) and its
    cutoff ``C_prev`` in days from now. Status ``carried``: this decision's candidates are valued a second time with
    every rollout run at ``C_prev`` (:func:`value.evaluate`'s ``cutoff``: the continuation's ranking, a probe's branch
    choice, the quadrature's boundaries and the end ``C_prev + H``), and their features with ``C_prev``'s span, so
    that decision's backup reads ``Q_tail(x′, a′; C_prev)`` itself, never this cutoff's value trimmed.
    ``same_cutoff`` (within ``tail_data``'s numerical tolerance): this decision's own ``Q̄`` is that value.
    ``past_cutoff``: ``C_prev`` already passed (that transition is censored ``past_cutoff``)."""

    earlier = [row for row in rows if str(row.created_at) < now_iso and row.cutoff_at is not None]
    if not earlier:
        return None
    prev = max(earlier, key=lambda row: (row.created_at, row.decision_id))
    now = TD._parse(now_iso)
    cutoff_days = (prev.cutoff_at - now).total_seconds() / 86400.0
    if cutoff_days <= 0:
        status = PAST_CUTOFF
    elif abs(cutoff_days - float(inputs.cutoff)) * 86400.0 <= TD._SAME_CUTOFF_SECONDS:
        status = SAME_CUTOFF
    else:
        status = CARRIED
    return {"decision_id": prev.decision_id, "cutoff_at": prev.cutoff_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "cutoff_days": _exact(cutoff_days), "horizon_days": float(prev.horizon_days), "status": status}


def carried_cutoff(record: Mapping[str, Any] | None) -> float | None:
    """The cutoff (days from now) the candidates are valued at a second time, for an applied record whose previous
    decision's cutoff is ``carried`` (:func:`previous_cutoff`); else None (no second valuation)."""

    if not applied(record):
        return None
    previous = record.get("previous") if isinstance(record, Mapping) else None  # type: ignore[union-attr]
    if not isinstance(previous, Mapping) or previous.get("status") != CARRIED:
        return None
    return float(previous["cutoff_days"])


def with_carried_values(record: Mapping[str, Any], evaluation: Any) -> dict[str, Any]:
    """The record with each candidate's ``Q̄`` at the carried cutoff (``previous.q``, from the evaluation run at it,
    with its draws and time), or with why there is none (``previous.q_status``): a transition into this decision then
    has no value at the earlier cutoff and is censored ``cutoff_unmatched``."""

    previous = dict(record.get("previous") or {})
    if evaluation is None or not getattr(evaluation, "complete", False):
        previous["q_status"] = "not_valued_within_the_budget"
    else:
        previous["q"] = {row.ref: float(row.q) for row in evaluation.valued}
        previous["q_status"] = "valued"
        previous["draws"] = int(evaluation.draws)
        previous["elapsed_ms"] = int(evaluation.elapsed_ms)
    return {**dict(record), "previous": previous}


#: ``previous.q_status`` of a decision whose second valuation would have run on the learner's serving path (RO6's
#: landing ruling R3): not run; a transition into the decision is censored ``cutoff_unmatched``
NOT_ON_THE_SERVING_PATH = "not_valued_on_the_serving_path"


def not_on_the_serving_path(record: Mapping[str, Any]) -> dict[str, Any]:
    """The record of a decision served with no prefetch job (the no-model branch, RO6's landing ruling R3): its
    answer is published and served at once and its trace written with it, so a second valuation at the carried
    cutoff has nowhere to run but the learner's serving path. It is not run; the transition into this decision is
    censored ``cutoff_unmatched``."""

    previous = dict(record.get("previous") or {})
    previous["q_status"] = NOT_ON_THE_SERVING_PATH
    return {**dict(record), "previous": previous}


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


__all__ = ["CARRIED", "NOT_ON_THE_SERVING_PATH", "PAST_CUTOFF", "SAME_CUTOFF", "SNAPSHOT_VERSION", "VERSION",
           "applied", "candidate_terms", "carried_cutoff", "features", "measurable", "not_on_the_serving_path",
           "previous_cutoff",
           "residual", "shifted", "snapshot", "with_carried_values"]

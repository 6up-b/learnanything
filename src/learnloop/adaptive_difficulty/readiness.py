"""Readiness numbers from the subject view, and the router card's AD fields (spec §9.5, §10.1, §12).

**Ready for the top level (predicted).** Per cell of an LO, ``p̄`` at the
goal ladder's top rung ``t`` (the default target of the cell's capability in
AD2+AD3: no goal ladders or exam targets until AD4), labelled as a prediction
(KM §9.6). "likely ready" when ``p̄(t) >= ready_threshold``. It reads the subject
view, so it needs ``promoted_predictor``: with it off the line reads "exam level:
not yet predicted" and the card carries no AD fields.

**Untested stays untested** (field F4, §4.3; A4): a cell with no eligible answer
of its own shows "untested" in place of the prediction, whatever the shared
terms, couplings or reading predict, so none of them alone ever shows "likely
ready".

**The router card's AD fields**, per LO (§10.1): ``P_band`` of the next
point (the best point of the cell's ``X_c``), ``p̄`` at the target, and the
untested mark, labelled as predictions. Demonstrated level / K is AD4's.

Nothing here is evidence or a level (A2, A9): numbers beside the map, never a
second depth.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.successor import subject_view_live

READINESS_VERSION = "ad_readiness_v1"
NOT_PREDICTED = "exam level: not yet predicted"
UNTESTED = "untested"
LIKELY = "likely ready"
NOT_YET = "not yet likely"


def _cells(view: Any, learning_object_id: str) -> list[tuple[str, str, str]]:
    """``(facet, capability, subject)`` of every cell the LO's visible active items measure, read
    through the material view: a protected item (held-out material, an exam reservation) never
    shapes a readiness line or the router card (A8); with the predicate unavailable there are none."""

    vault = view.vault
    cells: set[tuple[str, str, str]] = set()
    for item in view.items(learning_object_id=learning_object_id, active=True):
        subject = PR.item_subject(vault, item)
        for facet in PR.facet_weights(vault, item):
            cells.add((facet, PR.capability(item), subject))
    return sorted(cells)


@entry(read_only=True)
def lo_readiness(vault: Any, repository: Any, learning_object_id: str, *,
                 snapshot: RP.Snapshot | None = None, view: Any = None) -> dict[str, Any]:
    """The LO's readiness lines (labelled predictions), or the not-predicted line."""

    if not subject_view_live(vault.config):
        return {"version": READINESS_VERSION, "predicted": False, "line": NOT_PREDICTED, "cells": []}
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    snapshot = snapshot or RP.snapshot(vault, repository, view=view)
    constants = S.constants_from_config(vault.config)
    threshold = float(getattr(vault.config.adaptive_difficulty, "ready_threshold", 0.8))
    rows = []
    for facet, capability, subject in _cells(view, learning_object_id):
        target = S.default_target(capability)
        if target is None:
            continue
        untested = (facet, capability) not in snapshot.observed_cells
        spec = PR.point_spec(target, learning_object_id=learning_object_id, subject=subject, facet=facet,
                             capability_name=capability)
        prediction = PR.predict(snapshot.subject, spec, band=constants.band)
        label = UNTESTED if untested else (LIKELY if prediction.p_bar >= threshold else NOT_YET)
        rows.append({"facet": facet, "capability": capability, "untested": untested,
                     "p_bar_at_top": None if untested else round(prediction.p_bar, 4),
                     "label": label, "kind": "prediction", "ladder": S.ladder_id(capability, target)})
    return {"version": READINESS_VERSION, "predicted": True, "line": aggregate_line(rows), "cells": rows}


def aggregate_line(rows: list[Mapping[str, Any]]) -> str:
    """The LO's one visible line (Codex review F9): "likely ready" only when **every** cell is
    tested and likely ready; a partly untested LO says so in the line itself, since the desktop
    shows this line alone, and is never "likely ready" on its tested cells."""

    if not rows:
        return UNTESTED
    untested = sum(1 for row in rows if row["untested"])
    if untested == len(rows):
        return f"Top level for this goal: {UNTESTED}"
    if untested:
        return (f"Top level for this goal: not yet shown · {NOT_YET} (a prediction; "
                f"{untested} of {len(rows)} parts {UNTESTED})")
    if all(row["label"] == LIKELY for row in rows):
        return f"Top level for this goal: not yet shown · {LIKELY} (a prediction)"
    return f"Top level for this goal: not yet shown · {NOT_YET} (a prediction)"


@entry(read_only=True)
def card_fields(vault: Any, repository: Any, learning_object_id: str, *,
                snapshot: RP.Snapshot | None = None, view: Any = None) -> dict[str, Any] | None:
    """The router card's AD fields for one LO (None with ``promoted_predictor`` off)."""

    if not subject_view_live(vault.config):
        return None
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    snapshot = snapshot or RP.snapshot(vault, repository, view=view)
    fields = _lo_fields(vault, view, snapshot, learning_object_id)
    if fields is None:
        return None
    return {key: value for key, value in fields.items() if key != "p_bar_at_top_raw"}


@entry(read_only=True)
def decision_state_fields(vault: Any, repository: Any, learning_object_ids: Sequence[str], *,
                          snapshot: RP.Snapshot | None = None, view: Any = None,
                          reading_doses: bool = False, learning_moments: bool = False,
                          eta_moments: bool = False) -> dict[str, Any]:
    """RO0 row 9 (spec_router_objective_v1 §4): the card's numbers for each candidate LO at one decision, and the state
    they were read from. A receipt, not a claim: an untested cell keeps its mark beside its raw prediction, which no
    display reads. Through the material view, so a protected item never shapes it (A8).

    ``reading_doses`` (router objective RO4, Codex review F8): each LO also carries ``reading_dose``, its main facet's
    position on AD's ``reading`` dose curve (the subject view's open window, averaged over the bank's rows: reading
    since the facet's last graded attempt), so a rollout's next dose takes AD's diminishing increment. Off for every
    other caller, whose rows stay as they were.

    ``learning_moments`` (router objective RO5, §9 item 7): also the subject view's fitted ``γ`` and reading curve
    (``learning``: each parameter's posterior mean and variance), so the rollouts read the posterior and not the
    prior means. Off for every other caller.

    ``eta_moments`` (the router objective follow-up batch's landing ruling R10): each LO also carries
    ``eta_at_top``, the posterior moments of the latent ``η`` its ``p_bar_at_top_raw`` integrates (the mixture's
    mean and variance over the bank's rows, the target point's epistemic variance, before the item residual) and the
    point's guess, so the rollouts start from AD's own latent distribution. Off for every other caller.

    Teacher TE3a (spec_teacher_v1 rev 5 §14.2): with ``learning_moments`` and the lesson switch live, also
    ``lesson_curve``: the ``landed`` dose curve's posterior moments (both coefficients' means and their 2x2
    covariance, the mixture's over the bank's first group; the seeded prior while no lesson has reached the bank)
    and each LO's position on it (its main facet's lesson window), the one learned lesson effect the objective's
    lesson interface reads (``router_objective.value``). Absent with the switch off or below its tag."""

    if not subject_view_live(vault.config):
        return {"status": "not_live"}
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    snapshot = snapshot or RP.snapshot(vault, repository, view=view)
    los: dict[str, Any] = {}
    positions: dict[str, float] = {}
    for learning_object_id in learning_object_ids:
        fields = _lo_fields(vault, view, snapshot, learning_object_id, moments=eta_moments)
        if fields is not None:
            los[learning_object_id] = {key: fields[key] for key in ("p_band_next", "p_bar_at_top_raw", "untested", "cell")}
            if eta_moments:
                los[learning_object_id]["eta_at_top"] = fields.get("eta_at_top")
            if reading_doses:
                window = snapshot.subject.windows.get(("reading", fields["cell"][0]))
                los[learning_object_id]["reading_dose"] = float(window.mean()) if window is not None else 0.0
            lesson_window = snapshot.subject.windows.get((P.LESSON_KIND, fields["cell"][0]))
            positions[learning_object_id] = float(lesson_window.mean()) if lesson_window is not None else 0.0
    out: dict[str, Any] = {"status": "live", "state_hash": snapshot.state_hash(), "los": los}
    if learning_moments:
        out["learning"] = _learning_moments(snapshot.subject)
        from learnloop.adaptive_difficulty.successor import lesson_opportunities_on

        if lesson_opportunities_on(vault.config):
            out["lesson_curve"] = {**lesson_curve_moments(snapshot.subject), "positions": positions}
    return out


def lesson_curve_moments(subject: Any, subkind: str = "landed") -> dict[str, Any]:
    """Teacher TE3a: a lesson subkind's dose-curve coefficients ``(c_1, c_2)``: the mixture's mean and covariance over
    the bank's first group (as :func:`_learning_moments`), a read, never a write; the seeded prior
    (``ad_lesson_priors_v1``) while the bank has no lesson coordinate (no lesson opportunity applied yet), and the
    seeded prior's moments beside them (``prior_mean``, ``prior_cov``)."""

    names = [P.lesson_coordinate(subkind, m) for m in (1, 2)]
    bank = subject.bank
    seeded = {name: (mean, var) for name, mean, var in P.LESSON_PRIORS}
    prior_mean = [float(seeded[name][0]) for name in names]
    prior_cov = [[float(seeded[names[0]][1]), 0.0], [0.0, float(seeded[names[1]][1])]]
    # Codex review F2: the prior beside the posterior, so the objective values only what lessons taught the curve.
    out = {"version": P.LESSON_PRIORS_VERSION, "subkind": subkind, "prior_mean": prior_mean, "prior_cov": prior_cov}
    if not all(name in bank.index for name in names):
        return {**out, "source": "prior", "mean": list(prior_mean), "cov": [list(row) for row in prior_cov]}
    import numpy as np

    weights = bank.weights()[0]
    rows = len(weights)
    index = [bank.index[name] for name in names]
    mu = bank.mu[:rows][:, index]
    cov = bank.S[:rows][:, index][:, :, index]
    if np.array_equal(mu, np.broadcast_to(prior_mean, mu.shape)) and np.array_equal(
            cov, np.broadcast_to(prior_cov, cov.shape)):
        # Every component still at the seeded prior (a lesson applied, no later answer informed it): the mixture is
        # the prior exactly (the moment arithmetic below would round it by an ulp).
        return {**out, "source": "posterior", "mean": list(prior_mean), "cov": [list(row) for row in prior_cov]}
    mean = weights @ mu
    second = np.einsum("b,bij->ij", weights, cov + np.einsum("bi,bj->bij", mu, mu))
    covariance = second - np.outer(mean, mean)
    return {**out, "source": "posterior", "mean": [float(value) for value in mean],
            "cov": [[float(covariance[0, 0]), float(covariance[0, 1])], [float(covariance[1, 0]), float(covariance[1, 1])]]}


#: Router objective RO5 (§9 item 7): the learning parameters whose fitted moments the rollouts read.
LEARNING_PARAMETERS: tuple[str, ...] = ("gamma", "gbar:1", "gbar:2")


def _learning_moments(subject: Any) -> dict[str, list[float]]:
    """The subject view's posterior mean and variance of ``γ`` and the reading curve's ``γ̄_1, γ̄_2``: the mixture's
    moments over the bank's first group (``dose_report.coefficient_draws``'s rows), a read, never a write."""

    bank = subject.bank
    weights = bank.weights()[0]
    rows = len(weights)
    out: dict[str, list[float]] = {}
    for name in LEARNING_PARAMETERS:
        index = bank.index.get(name)
        if index is None:
            continue
        mu = bank.mu[:rows, index]
        var = bank.S[:rows, index, index]
        mean = float((weights * mu).sum())
        second = float((weights * (var + mu * mu)).sum())
        out[name] = [mean, max(second - mean * mean, 0.0)]
    return out


def _lo_fields(vault: Any, view: Any, snapshot: RP.Snapshot, learning_object_id: str, *,
               moments: bool = False) -> dict[str, Any] | None:
    """One LO's AD numbers in its main cell, or None with no visible cell. ``moments`` (R10, see
    :func:`decision_state_fields`): also ``eta_at_top``."""

    cells = _cells(view, learning_object_id)
    if not cells:
        return None
    constants = S.constants_from_config(vault.config)
    facet, capability, subject = cells[0]
    weights = {f: 0.0 for f, _c, _s in cells}
    for item in view.items(learning_object_id=learning_object_id):
        for f, w in PR.facet_weights(vault, item).items():
            if f in weights:
                weights[f] += w
    facet = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    capability = next(c for f, c, _s in cells if f == facet)
    subject = next(s for f, _c, s in cells if f == facet)
    points = S.commission_candidates(capability)
    specs = [PR.point_spec(point, learning_object_id=learning_object_id, subject=subject, facet=facet,
                           capability_name=capability) for point in points]
    scored = PR.score(snapshot.subject, specs, constants=constants, information=False)
    target = S.default_target(capability)
    untested = (facet, capability) not in snapshot.observed_cells
    target_spec = PR.point_spec(target, learning_object_id=learning_object_id, subject=subject, facet=facet,
                                capability_name=capability) if target is not None else None
    prediction = PR.predict(snapshot.subject, target_spec, band=constants.band) if target_spec is not None else None
    at_target = prediction.p_bar if prediction is not None else None
    out = {
        "kind": "prediction", "cell": [facet, capability],
        "p_band_next": round(max((s.p_band for s in scored), default=0.0), 4),
        "p_bar_at_top": None if untested or at_target is None else round(at_target, 4),
        "p_bar_at_top_raw": None if at_target is None else round(at_target, 4),
        "untested": untested,
    }
    if moments:
        out["eta_at_top"] = (_latent_moments(snapshot.subject, prediction, target_spec)
                             if prediction is not None else None)
    return out


def _latent_moments(subject: Any, prediction: PR.Prediction, spec: Any) -> dict[str, float]:
    """R10: the latent ``η`` the prediction integrates, as a mixture's mean and variance over the bank's rows (each
    row's ``(m, v_e)``, weighted as ``predict`` weights them), and the spec's guess. A read, never a write."""

    weights = PR.mixture_weights(subject)
    rows = prediction.rows
    w = [float(x) for x in weights[:len(rows)]]
    total = sum(w) or 1.0
    mean = sum(wi * m for wi, (m, _v) in zip(w, rows, strict=True)) / total
    second = sum(wi * (v + m * m) for wi, (m, v) in zip(w, rows, strict=True)) / total
    return {"mean": float(mean), "variance": float(max(second - mean * mean, 0.0)), "guess": float(spec.guess),
            "rows": len(rows)}


@entry(read_only=True)
def band_positions(vault: Any, repository: Any, learning_object_ids: Sequence[str], *,
                   snapshot: RP.Snapshot | None = None, view: Any = None) -> dict[str, dict[str, Any]]:
    """Per LO, where adaptive difficulty predicts the learner stands against its practice band
    (teacher TE1b's ``below_band`` lesson reason; codex review F6). Empty with ``promoted_predictor``
    off; an LO with no visible cell is left out.

    Over the LO's commission points ``X_c`` in its main cell (the cell :func:`card_fields` reads):
    ``p_band`` the highest ``P_band`` (a probability of being in the band, the quantity
    ``calibrate_below`` thresholds, selection §6.2) and ``p_bar`` the highest expected success (the
    easiest point). ``below``: the cell is tested (an untested cell's prediction is never a claim,
    A4), AD's own out-of-band rule holds (no point has ``P_band`` at ``calibrate_below`` or more) and
    even the easiest point's expected success is under the band's lower edge, so the learner is
    predicted below the band, not above it or merely uncertain. No new number: the band and
    ``calibrate_below`` are AD's."""

    if not subject_view_live(vault.config):
        return {}
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    snapshot = snapshot or RP.snapshot(vault, repository, view=view)
    constants = S.constants_from_config(vault.config)
    out: dict[str, dict[str, Any]] = {}
    for learning_object_id in learning_object_ids:
        cell = _main_cell(view, vault, learning_object_id)
        if cell is None:
            continue
        facet, capability, subject = cell
        specs = [PR.point_spec(point, learning_object_id=learning_object_id, subject=subject, facet=facet,
                               capability_name=capability) for point in S.commission_candidates(capability)]
        scored = PR.score(snapshot.subject, specs, constants=constants, information=False)
        if not scored:
            continue
        best_band = max(s.p_band for s in scored)
        easiest = max(s.p_bar for s in scored)
        untested = (facet, capability) not in snapshot.observed_cells
        out[learning_object_id] = {
            "kind": "prediction", "cell": [facet, capability],
            "p_band": round(best_band, 6), "p_bar": round(easiest, 6),
            "band": [float(constants.band[0]), float(constants.band[1])],
            "calibrate_below": float(constants.calibrate_below),
            "untested": untested,
            "below": (not untested) and best_band < constants.calibrate_below and easiest < constants.band[0],
        }
    return out


def _main_cell(view: Any, vault: Any, learning_object_id: str) -> tuple[str, str, str] | None:
    """The LO's main cell: the facet its visible items weigh most (as :func:`card_fields` picks)."""

    cells = _cells(view, learning_object_id)
    if not cells:
        return None
    weights = {f: 0.0 for f, _c, _s in cells}
    for item in view.items(learning_object_id=learning_object_id):
        for f, w in PR.facet_weights(vault, item).items():
            if f in weights:
                weights[f] += w
    facet = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    capability = next(c for f, c, _s in cells if f == facet)
    subject = next(s for f, _c, s in cells if f == facet)
    return facet, capability, subject


def card_line(fields: Mapping[str, Any]) -> str:
    if fields.get("untested"):
        return f"AD (prediction): {fields.get('p_band_next', 0):.2f} chance the next point lands in the band; untested"
    return (f"AD (prediction): {fields.get('p_band_next', 0):.2f} chance the next point lands in the band; "
            f"{fields.get('p_bar_at_top') or 0:.2f} predicted at the top level")


__all__ = ["LIKELY", "NOT_PREDICTED", "NOT_YET", "READINESS_VERSION", "UNTESTED", "aggregate_line", "band_positions",
           "card_fields", "card_line", "decision_state_fields", "lesson_curve_moments", "lo_readiness"]

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

from collections.abc import Mapping
from typing import Any

from learnloop.adaptive_difficulty import predict as PR
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


@entry
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


@entry
def card_fields(vault: Any, repository: Any, learning_object_id: str, *,
                snapshot: RP.Snapshot | None = None, view: Any = None) -> dict[str, Any] | None:
    """The router card's AD fields for one LO (None with ``promoted_predictor`` off)."""

    if not subject_view_live(vault.config):
        return None
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    snapshot = snapshot or RP.snapshot(vault, repository, view=view)
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
    at_target = PR.predict(snapshot.subject, PR.point_spec(
        target, learning_object_id=learning_object_id, subject=subject, facet=facet, capability_name=capability),
        band=constants.band).p_bar if target is not None else None
    return {
        "kind": "prediction", "cell": [facet, capability],
        "p_band_next": round(max((s.p_band for s in scored), default=0.0), 4),
        "p_bar_at_top": None if untested or at_target is None else round(at_target, 4),
        "untested": untested,
    }


def card_line(fields: Mapping[str, Any]) -> str:
    if fields.get("untested"):
        return f"AD (prediction): {fields.get('p_band_next', 0):.2f} chance the next point lands in the band; untested"
    return (f"AD (prediction): {fields.get('p_band_next', 0):.2f} chance the next point lands in the band; "
            f"{fields.get('p_bar_at_top') or 0:.2f} predicted at the top level")


__all__ = ["LIKELY", "NOT_PREDICTED", "NOT_YET", "READINESS_VERSION", "UNTESTED", "aggregate_line", "card_fields", "card_line",
           "lo_readiness"]

"""Predictive quantities for decisions and receipts (spec_adaptive_difficulty_v1 §5.7).

``p̄``, ``P_band`` and ``I_c`` for an item or a not-yet-written feature point,
in the view a decision reads: the subject view's mixture over the grid (a
probability under a mixture is the weighted sum of the component
probabilities, so propensities built from them stay exact), its
uniform-sharing restriction (``@subject_uniform``), or one LO's view.

Also the item specs a decision reads now: a current item's features (the audit
where it had answered, else the stamped value), its signals (the same
functions that freeze them in the serve-input receipt) and, in the subject
view, the loadings in force; a feature point's spec carries no signal
(``z = 0``) and only the cell's own facet (§5.7).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty.selection import Scored, SelectionConstants, point_key
from learnloop.adaptive_difficulty.state import ItemSpec, View, normalized_weights

VIEW_SUBJECT = "subject"


def mixture_weights(view: View, *, uniform: bool = False) -> np.ndarray:
    bank = view.bank
    if not view.subject_view or bank.P == 1:
        return np.ones(bank.P)
    if uniform:
        mask = np.array([p.uniform for p in bank.points])
        return bank.restricted_weights(mask)[0]
    return bank.weights()[0]


@dataclass(frozen=True)
class Prediction:
    p_bar: float
    p_band: float
    rows: tuple[tuple[float, float], ...]  # (m, v_e) per grid point

    def as_dict(self) -> dict[str, Any]:
        return {"p_bar": round(self.p_bar, 12), "p_band": round(self.p_band, 12)}


def predict(view: View, spec: ItemSpec, *, warmth: float = 0.0, weights: np.ndarray | None = None,
            band: tuple[float, float] = (0.70, 0.80)) -> Prediction:
    """``p̄(x)`` and ``P_band(x)`` (mixtures in the subject view)."""

    m, v = view.prediction(spec, warmth)
    w = mixture_weights(view) if weights is None else weights
    p_bars = M.expected_success(m, v, spec.guess)
    p_bands = M.band_probability(m, v, spec.guess, band)
    return Prediction(float(np.dot(w, p_bars)), float(np.dot(w, p_bands)),
                      tuple((float(a), float(b)) for a, b in zip(m, v)))


def score(view: View, specs: Sequence[ItemSpec], *, warmth: float = 0.0,
          constants: SelectionConstants = SelectionConstants(), weights: np.ndarray | None = None,
          information: bool = True) -> list[Scored]:
    """Each candidate's ``Scored`` (``P_band``, ``p̄`` and the cell information ``I_c``)."""

    if not specs:
        return []
    w = mixture_weights(view) if weights is None else weights
    scored: list[Scored] = []
    infos: dict[str, float] = {}
    if information:
        cell_view_cache: dict[tuple[str, str, str], View] = {}
        for spec in specs:
            facet, capability = spec.cell()
            key = (spec.subject, facet, capability)
            if key not in cell_view_cache:
                cell_view_cache[key] = view.with_cell(spec.subject, facet, capability)
            cell_view = cell_view_cache[key]
            m, v, cov, var_c = cell_view.cell_moments(spec)
            info = M.cell_information(m, v, cov, var_c, spec.guess)
            infos[spec.item_id] = float(np.dot(w, info))
    for spec in specs:
        prediction = predict(view, spec, warmth=warmth, weights=w, band=constants.band)
        scored.append(Scored(spec.item_id, prediction.p_band, prediction.p_bar, infos.get(spec.item_id, 0.0)))
    return scored


# -- item specs at decision time ----------------------------------------------------------------

def item_subject(vault: Any, item: Any) -> str:
    subjects = vault.subjects_for_item(item)
    return str(subjects[0]) if subjects else "default"


def facet_weights(vault: Any, item: Any) -> dict[str, float]:
    weights: dict[str, float] = {}
    for facet, weight in normalized_weights(getattr(item, "evidence_weights", None),
                                            getattr(item, "evidence_facets", None) or ()).items():
        canonical = vault.canonical_facet_id(facet)
        weights[canonical] = weights.get(canonical, 0.0) + weight
    return weights


def capability(item: Any) -> str:
    value = getattr(item, "capability", None)
    if value in P.CAPABILITIES:
        return str(value)
    try:
        from learnloop.learner.capability_mapping import default_capability_for

        mapped = default_capability_for(str(getattr(item, "practice_mode", "") or ""))
        return mapped if mapped in P.CAPABILITIES else "retrieval"
    except Exception:  # noqa: BLE001
        return "retrieval"


def guess(vault: Any, item: Any) -> float:
    try:
        from learnloop.learner.blueprint_projection import guess_floor_for_item

        return float(guess_floor_for_item(item, vault.config))
    except Exception:  # noqa: BLE001
        return 0.0


def current_spec(vault: Any, connection: Any, item: Any, *, at: str, view: Any,
                 loadings: Mapping[str, float] | None = None, outside: bool = False) -> ItemSpec:
    """The item as a decision now reads it: the audit where answered, else the stamped
    features; the signals the serve-input receipt would freeze (their calibration history read
    through ``view``, the operation's material view); the loadings in force."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.serve_inputs import feature_inputs, signal_vector

    content_hash, _json = item_revision(item)
    features = feature_inputs(connection, item, content_hash, at)["resolved_features"]
    vector, _version = signal_vector(connection, item, content_hash, at, view=view)
    signals = {name: float(entry["value"]) for name, entry in vector.items()
               if isinstance(entry, Mapping) and entry.get("available") and entry.get("value") is not None}
    if not outside:
        signals.pop("z_v1", None)
    return ItemSpec(str(item.id), str(item.learning_object_id), item_subject(vault, item), capability(item),
                    facet_weights(vault, item), features=features, signals=signals,
                    loadings={vault.canonical_facet_id(g): float(q) for g, q in (loadings or {}).items()},
                    guess=guess(vault, item))


def point_spec(point: Mapping[str, Any], *, learning_object_id: str, subject: str, facet: str,
               capability_name: str) -> ItemSpec:
    """A not-yet-written feature point (``z = 0``, the cell's own facet only)."""

    return ItemSpec(f"point:{point_key(point)}", learning_object_id, subject, capability_name, {facet: 1.0},
                    features=dict(point))


__all__ = [
    "Prediction",
    "VIEW_SUBJECT",
    "capability",
    "current_spec",
    "facet_weights",
    "guess",
    "item_subject",
    "mixture_weights",
    "point_spec",
    "predict",
    "score",
]

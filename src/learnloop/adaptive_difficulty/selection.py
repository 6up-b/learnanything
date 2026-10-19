"""The draws: practice in the band, calibration within acceptable difficulty (spec §6.1-6.2).

``ad_select_v1``, a pure rule over scored candidates:

0. an empty support makes no draw;
1. ``P_band`` and ``p̄`` for every candidate (mixtures over the grid in the
   subject view: a probability under a mixture is the weighted sum of the
   component probabilities, so the propensities stay exact, §5.7);
2. **calibrate** instead when ``max P_band < calibrate_below`` (0.25; 0.35 as
   pre-registered, lowered by the owner on 2026-10-19 after the gates, amendment A17): choose
   by the cell information ``I_c`` among the overlap set (near-ties within 5%
   of the maximum, relative, broken uniformly), or, with the overlap set
   empty, the candidate whose ``p̄`` is nearest ``[0.55, 0.90]``, ties by id;
3. the near-tie set ``T`` (``P_band >= max - 0.05``) and the overlap set ``O``
   (``p̄ ∈ [0.55, 0.90]``);
4. ``π(i) = (1 - q)·1[i∈T]/|T| + q·1[i∈O]/|O|`` with ``q = 0.10`` (``q = 0``
   when ``O`` is empty); the seed is ``sha256(design:key)``, and the draw
   inverts the propensities' CDF over the candidates in id order.

A propensity is a deterministic function of the logged scores, so it
recomputes exactly from the logged row (G-AD2-19). The ``feature_overlap``
design is registered in the randomization layer with its own floor.

The ladders (``ad_ladder_v1``, §9.1) and the commission candidates ``X_c``
(§6.1) are deterministic functions of a capability and a target point.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

SELECT_VERSION = "ad_select_v1"
COMMISSION_VERSION = "ad_commission_v1"
LADDER_VERSION = "ad_ladder_v1"
DESIGN = "feature_overlap"

MODE_BAND = "band"
MODE_CALIBRATE = "calibrate"
MODE_PREDECESSOR = "predecessor"


@dataclass(frozen=True)
class SelectionConstants:
    band: tuple[float, float] = (0.70, 0.80)
    overlap: tuple[float, float] = (0.55, 0.90)
    overlap_share: float = 0.10
    near_tie: float = 0.05
    calibrate_below: float = 0.25
    info_near_tie: float = 0.05

    def as_dict(self) -> dict[str, Any]:
        return {"band": list(self.band), "overlap": list(self.overlap), "overlap_share": self.overlap_share,
                "near_tie": self.near_tie, "calibrate_below": self.calibrate_below,
                "info_near_tie": self.info_near_tie}


def constants_from_config(config: Any) -> SelectionConstants:
    section = getattr(config, "adaptive_difficulty", None)
    if section is None:
        return SelectionConstants()
    return SelectionConstants(
        band=tuple(float(v) for v in getattr(section, "practice_band", (0.70, 0.80))),  # type: ignore[arg-type]
        overlap=tuple(float(v) for v in getattr(section, "overlap_band", (0.55, 0.90))),  # type: ignore[arg-type]
        overlap_share=float(getattr(section, "overlap_share", 0.10)),
        near_tie=float(getattr(section, "near_tie_margin", 0.05)),
        calibrate_below=float(getattr(section, "calibrate_below", 0.25)),
    )


@dataclass(frozen=True)
class Scored:
    """One candidate's scores, as logged."""

    ref: str
    p_band: float
    p_bar: float
    info: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {"ref": self.ref, "p_band": round(self.p_band, 12), "p_bar": round(self.p_bar, 12),
                "info": round(self.info, 12)}


@dataclass(frozen=True)
class Draw:
    mode: str
    chosen: str | None
    propensities: Mapping[str, float]
    seed: str
    u: float | None
    near_tie: tuple[str, ...] = ()
    overlap: tuple[str, ...] = ()
    q: float = 0.0
    empty_support: bool = False

    @property
    def propensity(self) -> float:
        return float(self.propensities.get(self.chosen or "", 0.0))

    def as_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "chosen": self.chosen, "propensity": self.propensity,
                "propensities": {k: v for k, v in sorted(self.propensities.items())}, "seed": self.seed,
                "u": self.u, "near_tie": list(self.near_tie), "overlap": list(self.overlap), "q": self.q,
                "empty_support": self.empty_support}


def seed_for(design: str, key: str) -> str:
    return hashlib.sha256(f"{design}:{key}".encode("utf-8")).hexdigest()


def uniform(seed: str) -> float:
    """A uniform in [0, 1) from the seed (53 bits of a SHA-256)."""

    digest = hashlib.sha256(f"{seed}:u".encode("utf-8")).digest()
    return (int.from_bytes(digest[:8], "big") >> 11) / float(1 << 53)


def _invert(propensities: Mapping[str, float], u: float) -> str:
    cumulative = 0.0
    refs = sorted(propensities)
    for ref in refs:
        cumulative += propensities[ref]
        if u < cumulative:
            return ref
    return refs[-1]


def _within(value: float, interval: tuple[float, float]) -> bool:
    return interval[0] <= value <= interval[1]


def _distance(value: float, interval: tuple[float, float]) -> float:
    if value < interval[0]:
        return interval[0] - value
    if value > interval[1]:
        return value - interval[1]
    return 0.0


def propensities(scored: Sequence[Scored], constants: SelectionConstants = SelectionConstants()
                 ) -> tuple[str, dict[str, float], tuple[str, ...], tuple[str, ...], float]:
    """``(mode, π, T, O, q)``: the exact propensities of §6.1 step 4 (or §6.2's calibrate rule)."""

    if not scored:
        return MODE_BAND, {}, (), (), 0.0
    refs = sorted(s.ref for s in scored)
    by_ref = {s.ref: s for s in scored}
    overlap = tuple(ref for ref in refs if _within(by_ref[ref].p_bar, constants.overlap))
    best = max(s.p_band for s in scored)
    if best < constants.calibrate_below:
        mode = MODE_CALIBRATE
        if overlap:
            top_info = max(by_ref[ref].info for ref in overlap)
            threshold = top_info * (1.0 - constants.info_near_tie) if top_info > 0 else top_info
            tied = tuple(ref for ref in overlap if by_ref[ref].info >= threshold)
        else:
            nearest = min(_distance(by_ref[ref].p_bar, constants.overlap) for ref in refs)
            tied = (min(ref for ref in refs if _distance(by_ref[ref].p_bar, constants.overlap) == nearest),)
    else:
        mode = MODE_BAND
        tied = tuple(ref for ref in refs if by_ref[ref].p_band >= best - constants.near_tie)
    q = constants.overlap_share if overlap else 0.0
    # The randomization layer's ``feature_overlap`` design owns the formula (spec §10.1).
    from learnloop.scheduling.randomization_layer import feature_overlap_propensities

    pi = feature_overlap_propensities(refs, tied, overlap, q)
    return mode, pi, tied, overlap, q


def draw(scored: Sequence[Scored], *, key: str, design: str = SELECT_VERSION,
         constants: SelectionConstants = SelectionConstants()) -> Draw:
    """The draw, with its propensities logged before it is used (A7)."""

    seed = seed_for(design, key)
    if not scored:
        return Draw(MODE_BAND, None, {}, seed, None, empty_support=True)
    mode, pi, tied, overlap, q = propensities(scored, constants)
    u = uniform(seed)
    chosen = _invert({ref: p for ref, p in pi.items() if p > 0}, u)
    return Draw(mode, chosen, pi, seed, u, near_tie=tied, overlap=overlap, q=q)


def recompute(row: Mapping[str, Any], constants: SelectionConstants | None = None) -> Draw:
    """Recompute a draw from its logged row (G-AD2-19): the scores, the constants and the seed."""

    scored = [Scored(str(entry["ref"]), float(entry["p_band"]), float(entry["p_bar"]), float(entry.get("info", 0.0)))
              for entry in row.get("support") or ()]
    raw = row.get("constants") or {}
    constants = constants or SelectionConstants(
        band=tuple(raw.get("band", (0.70, 0.80))), overlap=tuple(raw.get("overlap", (0.55, 0.90))),  # type: ignore[arg-type]
        overlap_share=float(raw.get("overlap_share", 0.10)), near_tie=float(raw.get("near_tie", 0.05)),
        calibrate_below=float(raw.get("calibrate_below", 0.25)), info_near_tie=float(raw.get("info_near_tie", 0.05)),
    )
    mode, pi, tied, overlap, q = propensities(scored, constants)
    seed = str(row["seed"])
    if not scored:
        return Draw(MODE_BAND, None, {}, seed, None, empty_support=True)
    u = uniform(seed)
    chosen = _invert({ref: p for ref, p in pi.items() if p > 0}, u)
    return Draw(mode, chosen, pi, seed, u, near_tie=tied, overlap=overlap, q=q)


# -- ladders and commission candidates (§9.1, §6.1) ----------------------------------------

#: The ordered dimensions, hardest last (scaffolding: worked < partial < cue < none).
LADDER_ORDER = ("scaffolding", "transfer", "complexity", "span", "response", "tools")
_SCAFFOLDING = ("worked", "partial", "cue", "none")
_TRANSFER = ("same_context", "near", "far", "novel_combination")
_SPAN = ("atomic", "single_step", "multi_step", "whole_task")
_RESPONSE_CLASS = {"recognize": 0, "short_constructed": 1, "long_constructed": 1, "structured_steps": 1,
                   "performance": 2}


def _level(dimension: str, value: Any) -> int:
    if dimension == "scaffolding":
        return _SCAFFOLDING.index(value) if value in _SCAFFOLDING else 2
    if dimension == "transfer":
        return _TRANSFER.index(value) if value in _TRANSFER else 0
    if dimension == "complexity":
        try:
            return min(max(int(value), 0), 4)
        except (TypeError, ValueError):
            return 0
    if dimension == "span":
        return _SPAN.index(value) if value in _SPAN else 0
    if dimension == "response":
        return _RESPONSE_CLASS.get(str(value), 1)
    if dimension == "tools":
        tools = {value} if isinstance(value, str) else set(value or ())
        return 0 if tools & {"open_book", "references"} else 1
    raise ValueError(dimension)


def _value(dimension: str, level: int, template: Mapping[str, Any]) -> Any:
    if dimension == "scaffolding":
        return _SCAFFOLDING[level]
    if dimension == "transfer":
        return _TRANSFER[level]
    if dimension == "complexity":
        return int(level)
    if dimension == "span":
        return _SPAN[level]
    if dimension == "response":
        current = template.get("response")
        if _RESPONSE_CLASS.get(str(current), 1) == level:
            return current
        return {0: "recognize", 1: "short_constructed", 2: "performance"}[level]
    if dimension == "tools":
        return ["open_book"] if level == 0 else ["closed_book"]
    raise ValueError(dimension)


def feature_level(dimension: str, value: Any) -> int:
    """The ordinal level of a feature value on a ladder dimension (§9.1's order)."""

    return _level(dimension, value)


_LEVELS = {"scaffolding": 4, "transfer": 4, "complexity": 5, "span": 4, "response": 3, "tools": 2}


def point_key(point: Mapping[str, Any]) -> str:
    def canonical(value: Any) -> Any:
        if isinstance(value, (list, tuple, set, frozenset)):
            return sorted(str(v) for v in value)
        return value

    import json

    return json.dumps({k: canonical(point[k]) for k in sorted(point) if k in LADDER_ORDER}, sort_keys=True,
                      separators=(",", ":"))


def entry_point(capability: str) -> dict[str, Any] | None:
    """``e_k``: the default-trajectory waypoint for the capability (§9.1); None for coordination."""

    from learnloop.curriculum.depth_rungs import DEFAULT_TRAJECTORY

    for waypoint in DEFAULT_TRAJECTORY:
        if waypoint.capability == capability:
            return {**dict(waypoint.features), "tools": ["closed_book"]}
    return None


def default_target(capability: str) -> dict[str, Any] | None:
    """``e_k`` stepped one level up in complexity and in transfer, bounded by the default trajectory."""

    entry = entry_point(capability)
    if entry is None:
        return None
    target = dict(entry)
    target["complexity"] = min(_level("complexity", entry.get("complexity")) + 1, envelope_max()["complexity"])
    transfer = min(_level("transfer", entry.get("transfer")) + 1, envelope_max()["transfer"])
    target["transfer"] = _TRANSFER[transfer]
    return target


def envelope_max() -> dict[str, int]:
    """The default trajectory's depth envelope: the hardest level it reaches on each dimension."""

    from learnloop.curriculum.depth_rungs import DEFAULT_TRAJECTORY

    levels = {dimension: 0 for dimension in LADDER_ORDER}
    for waypoint in DEFAULT_TRAJECTORY:
        point = {**dict(waypoint.features), "tools": ["closed_book"]}
        for dimension in LADDER_ORDER:
            levels[dimension] = max(levels[dimension], _level(dimension, point.get(dimension)))
    return levels


def within_envelope(point: Mapping[str, Any] | None) -> bool:
    if not point:
        return True
    limits = envelope_max()
    return all(_level(dimension, point.get(dimension)) <= limits[dimension]
               for dimension in LADDER_ORDER if point.get(dimension) is not None)


def ladder(capability: str, target: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """A ladder instance ``L(k, t)`` (§9.1): from ``e_k`` to ``t``, one dimension one level per rung
    in the fixed order, cycling until every dimension reaches ``t``. Rung 1 is ``e_k``."""

    entry = entry_point(capability)
    if entry is None:
        return []
    goal = dict(target or default_target(capability) or entry)
    for dimension in LADDER_ORDER:
        if _level(dimension, goal.get(dimension, entry.get(dimension))) < _level(dimension, entry.get(dimension)):
            goal[dimension] = entry.get(dimension)
    current = dict(entry)
    rungs = [dict(current)]
    for _ in range(64):
        moved = False
        for dimension in LADDER_ORDER:
            here = _level(dimension, current.get(dimension))
            there = _level(dimension, goal.get(dimension, current.get(dimension)))
            if here < there:
                current[dimension] = _value(dimension, here + 1, goal)
                rungs.append(dict(current))
                moved = True
        if not moved:
            break
    return rungs


def ladder_id(capability: str, target: Mapping[str, Any] | None) -> str:
    import json

    payload = {"capability": capability, "target": point_key(target or default_target(capability) or {}),
               "schema": "p1_launch@1", "version": LADDER_VERSION}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def commission_candidates(capability: str, targets: Sequence[Mapping[str, Any] | None] = (None,)) -> list[dict[str, Any]]:
    """``X_c``: the rungs of every applicable ladder and their one-step neighbours on a single
    ordinal dimension, clipped to the depth envelope (§6.1)."""

    points: dict[str, dict[str, Any]] = {}
    for target in targets:
        for rung in ladder(capability, target):
            for candidate in [rung, *_neighbours(rung)]:
                if within_envelope(candidate):
                    points.setdefault(point_key(candidate), candidate)
    return [points[key] for key in sorted(points)]


def _neighbours(point: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for dimension in LADDER_ORDER:
        level = _level(dimension, point.get(dimension))
        for step in (-1, 1):
            target = level + step
            if 0 <= target < _LEVELS[dimension]:
                moved = dict(point)
                moved[dimension] = _value(dimension, target, point)
                out.append(moved)
    return out


__all__ = [
    "COMMISSION_VERSION",
    "DESIGN",
    "Draw",
    "LADDER_ORDER",
    "LADDER_VERSION",
    "MODE_BAND",
    "MODE_CALIBRATE",
    "MODE_PREDECESSOR",
    "SELECT_VERSION",
    "Scored",
    "SelectionConstants",
    "commission_candidates",
    "constants_from_config",
    "default_target",
    "draw",
    "entry_point",
    "envelope_max",
    "feature_level",
    "ladder",
    "ladder_id",
    "point_key",
    "propensities",
    "recompute",
    "seed_for",
    "uniform",
    "within_envelope",
]

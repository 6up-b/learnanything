"""AD's draw at a planned new-material slot, and the serve-time AD2+AD3 receipts (spec §6.1, §10.1-10.2, §8.2).

The daily plan's adapter (``daily_plan.ad_slot``) builds the slot's support
and calls :func:`decide_slot` inside the serve transaction; this module scores
the support in the view live decisions read, draws with exact propensities,
and writes the ``ad_selections`` row before the item is served (A7). It never
builds, reorders or chooses blocks (§6.4).

0. **Empty support.** No draw. The row records ``empty_support`` and each
   candidate's failed checks. A slot item that failed only the pre-exposure
   check is served as the predecessor serves it (mode ``predecessor``,
   ``π_AD = 1``); otherwise the slot is displaced (``ad_ineligible``) and its
   item deferred by the plan until its blocking condition clears.
1-4. **The draw** (:mod:`.selection`): band, or calibrate when the posterior
   is too wide; the overlap share; the seed from the block and slot position.
5. **Substitution**: a drawn item that is not the slot item replaces it
   (``item_substituted``, written by the plan in the same transaction).

**Commission** (§6.1): at a serve draw, when the cell pool has no item with
``P_band >= calibrate_below``, a commission draw over the cell's ``X_c`` (at
most one open commission per cell). It changes only what can be served later.

**Which view** (A6, D3): the subject view while ``promoted_predictor`` is on,
else the slot LO's own view, exactly.

**Receipts** (§8.2): at every serve of a never-attempted item, the in-process
``ad_threshold@subject``, ``@subject_uniform`` and ``@lo`` forecasts, as
``item_unassisted_success`` rows in ``forecast_receipts``.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.logs import warn_failure
from learnloop.adaptive_difficulty.operation import entry

import logging
import math
from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.clock import parse_utc
from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.successor import (
    coupling_on,
    selection_on,
    subject_view_live,
    successor_active,
)

LOG = logging.getLogger(__name__)

SUBSTITUTED = "item_substituted"
DISPLACED = "item_displaced"
AD_INELIGIBLE = "ad_ineligible"
PRE_EXPOSED = "pre_exposed"
THRESHOLD_FORECASTERS = ("ad_threshold@subject", "ad_threshold@subject_uniform", "ad_threshold@lo")
THRESHOLD_VERSION = "ad-threshold-v1"

WHY = {
    "band": "Picked to be challenging but doable for you (about a 3 in 4 chance)",
    "overlap": "A different kind of question, to keep LearnLoop's picture of you accurate",
    "calibrate": "A question to find your level here",
}


@dataclass(frozen=True)
class SlotCandidate:
    practice_item_id: str
    failed: tuple[str, ...] = ()
    est_minutes: float = 0.0


@dataclass(frozen=True)
class SlotRequest:
    plan_id: str
    block_id: str
    slot_position: int
    slot_item_id: str
    learning_object_id: str
    candidates: tuple[SlotCandidate, ...]
    cell_pool: tuple[str, ...] = ()
    router_decision_id: str | None = None
    router_propensity: float | None = None
    now: str = ""

    @property
    def decision_key(self) -> str:
        return f"serve:{self.block_id}:{self.slot_position}"


@dataclass
class SlotDecision:
    action: str  # "serve" | "substitute" | "predecessor" | "displace"
    chosen_item_id: str | None
    selection_id: str | None
    mode: str
    propensity: float | None
    why: str | None = None
    why_kind: str | None = None
    slot_failed: tuple[str, ...] = ()
    commission_id: str | None = None
    view: str = PR.VIEW_SUBJECT

    def step_detail(self) -> dict[str, Any] | None:
        if self.why is None:
            return None
        return {"mode": self.why_kind, "why": self.why, "selection_id": self.selection_id}


def slot_applies(config: Any, item: Any) -> bool:
    """A new-material slot AD's draw serves (§6.1): a planned, never-served item with
    ``new_admitted`` (an ordinary new-lane item the chooser planned)."""

    return bool(
        selection_on(config) and getattr(item, "served_at", None) is None and getattr(item, "new_admitted", False)
        and getattr(item, "origin", None) == "chooser" and getattr(item, "check_kind", None) is None
    )


def view_for(snapshot: RP.Snapshot, config: Any, learning_object_id: str) -> tuple[Any, str]:
    if subject_view_live(config):
        return snapshot.subject, PR.VIEW_SUBJECT
    return snapshot.lo_view(learning_object_id), RP.lo_view_name(learning_object_id)


def _warmth(connection: Any, view: Any, learning_object_id: str, now: str) -> float:
    """``w_t`` at a decision: hours since the LO's last exposure (an attempt, a reveal, a reading
    opportunity) before ``now``, read through the material view (Codex verify F20: an attempt
    on a withheld item, or a receipt whose source is withheld now, warms nothing)."""

    served = RP.days(now)
    latest = None
    stamps = [row.get("created_at") for row in view.attempts(connection)
              if str(row.get("learning_object_id")) == str(learning_object_id)]
    stamps += [row.get("created_at") for row in view.reveals(connection)
               if str(row.get("learning_object_id")) == str(learning_object_id)]
    stamps += [row.get("source_written_at") for row in view.reading_opportunities(
        connection, learning_object_ids=[learning_object_id])]
    for created_at in stamps:
        try:
            value = RP.days(created_at)
        except (TypeError, ValueError):
            continue
        if value < served and (latest is None or value > latest):
            latest = value
    if latest is None:
        return 0.0
    return float(math.exp(-((served - latest) * 24.0) / P.WARMTH_HOURS))


def _loadings(snapshot: RP.Snapshot, config: Any, content_hash: str, now: str) -> dict[str, float]:
    if not coupling_on(config):
        return {}
    return snapshot.events.structure.loadings(content_hash, RP.days(now))


def _spec(vault: Any, connection: Any, snapshot: RP.Snapshot, item: Any, now: str, view: Any) -> Any:
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    content_hash, _json = item_revision(item)
    return PR.current_spec(vault, connection, item, at=now, view=view,
                           loadings=_loadings(snapshot, vault.config, content_hash, now))


def _versions(vault: Any, snapshot: RP.Snapshot, view_name: str) -> dict[str, Any]:
    return {**P.versions(), "select": S.SELECT_VERSION, "replay": RP.REPLAY_VERSION, "view": view_name,
            "coupling": dict(snapshot.events.structure.versions),
            "algorithm_version": vault.config.algorithms.algorithm_version}


@entry(savepoint=True)
def decide_slot(vault: Any, repository: Any, request: SlotRequest, *, view: Any = None) -> SlotDecision:
    """Score the slot's support and draw (§6.1), writing the ``ad_selections`` row first.

    Runs in the caller's (the serve's) transaction. The reading-opportunity sweep runs first,
    through the decision's instant (Codex review F4): a section read or a self-check since the
    last serve enters the state the support is scored on, and the serve hook's own sweep (at the
    same instant, in the same transaction) then finds nothing new, so the draw, the selection row
    and the serve receipts read one state."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.reading import sweep

    # The slot's material view (the plan side built it for the support's checks; A8).
    view = material_view(vault, repository, view)
    connection = repository.connection()
    if request.now:
        try:
            sweep(vault, repository, as_of=request.now, sweep_kind="serve", sweep_ref=request.decision_key,
                  view=view)
        except Exception as exc:  # noqa: BLE001 - as at the serve hook: a failed sweep never blocks the draw
            from learnloop.adaptive_difficulty.operation import is_denial

            if is_denial(exc):
                raise  # the guard's refusal: AD is unavailable for the slot (owner Q3)
            warn_failure(LOG, "AD reading sweep before draw %s failed", request.decision_key)
    constants = S.constants_from_config(vault.config)
    support = [c for c in request.candidates if not c.failed]
    excluded = [{"ref": c.practice_item_id, "failed": list(c.failed)} for c in request.candidates if c.failed]
    slot = next((c for c in request.candidates if c.practice_item_id == request.slot_item_id), None)
    slot_failed = tuple(slot.failed) if slot is not None else ("not_a_candidate",)
    snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
    state_view, view_name = view_for(snapshot, vault.config, request.learning_object_id)
    slot_item = view.item(request.slot_item_id)
    cell = (PR.facet_weights(vault, slot_item) and
            sorted(PR.facet_weights(vault, slot_item).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]) \
        if slot_item is not None else None
    cell_capability = PR.capability(slot_item) if slot_item is not None else None
    base = {
        "decision_key": request.decision_key, "kind": "serve", "view": view_name,
        "learning_object_id": request.learning_object_id, "cell_facet": cell, "cell_capability": cell_capability,
        "daily_plan_id": request.plan_id, "block_id": request.block_id, "slot_position": request.slot_position,
        "slot_item_id": request.slot_item_id, "constants": constants.as_dict(),
        "router_decision_id": request.router_decision_id, "router_propensity": request.router_propensity,
        "state_hash": snapshot.state_hash(), "versions": _versions(vault, snapshot, view_name),
        "algorithm_version": vault.config.algorithms.algorithm_version, "created_at": request.now,
        # The protection epoch the draw was computed under (round 2, class 3b).
        "protection_epoch": view.epoch,
    }
    status, existing = view.stored_status(connection, store.SELECTIONS, store.selection_by_key, request.decision_key)
    if status == "withheld":
        # The slot's logged draw is withheld now: it stands (never redrawn) and AD reads nothing of it,
        # so AD is unavailable for the slot and the plan serves its planned item.
        from learnloop.adaptive_difficulty.operation import GuardDenied

        raise GuardDenied(f"the logged draw of slot {request.decision_key} is withheld")
    if existing is not None:
        # A reopened slot: the logged draw stands (a propensity is never recomputed after the draw).
        chosen = existing.get("chosen_item_id")
        action = ("predecessor" if existing["mode"] == S.MODE_PREDECESSOR else
                  "displace" if existing["empty_support"] else
                  "serve" if chosen == request.slot_item_id else "substitute")
        return SlotDecision(action, chosen, str(existing["id"]), existing["mode"], existing.get("propensity"),
                            view=view_name)
    if not support:
        seed = S.seed_for(S.SELECT_VERSION, f"{request.block_id}:{request.slot_position}")
        if slot is not None and slot_failed == (PRE_EXPOSED,):
            selection_id = store.insert_selection(connection, {
                **base, "mode": S.MODE_PREDECESSOR, "support": [], "excluded": excluded, "seed": seed, "u": None,
                "chosen_item_id": request.slot_item_id, "propensity": 1.0,
                "pair_propensity": request.router_propensity, "empty_support": True,
            })
            return SlotDecision("predecessor", request.slot_item_id, selection_id, S.MODE_PREDECESSOR, 1.0,
                                slot_failed=slot_failed, view=view_name)
        selection_id = store.insert_selection(connection, {
            **base, "mode": "empty_support", "support": [], "excluded": excluded, "seed": seed, "u": None,
            "chosen_item_id": None, "propensity": None, "pair_propensity": None, "empty_support": True,
        })
        return SlotDecision("displace", None, selection_id, "empty_support", None,
                            slot_failed=tuple(f for f in slot_failed if f != PRE_EXPOSED), view=view_name)
    warmth = _warmth(connection, view, request.learning_object_id, request.now)
    specs = []
    for candidate in support:
        item = view.item(candidate.practice_item_id)
        if item is not None:
            specs.append(_spec(vault, connection, snapshot, item, request.now, view))
    scored = PR.score(state_view, specs, warmth=warmth, constants=constants)
    draw = S.draw(scored, key=f"{request.block_id}:{request.slot_position}", constants=constants)
    support_rows = [{**s.as_dict(), "propensity": round(draw.propensities.get(s.ref, 0.0), 12)} for s in scored]
    pair = None if request.router_propensity is None else request.router_propensity * draw.propensity
    selection_id = store.insert_selection(connection, {
        **base, "mode": draw.mode, "support": support_rows, "excluded": excluded, "seed": draw.seed, "u": draw.u,
        "chosen_item_id": draw.chosen, "propensity": draw.propensity, "pair_propensity": pair,
        "empty_support": False,
    })
    commission_id = _maybe_commission(vault, repository, snapshot, state_view, view_name, request, constants,
                                      cell=cell, capability_name=cell_capability, warmth=warmth, material=view)
    why_kind = ("calibrate" if draw.mode == S.MODE_CALIBRATE else
                "band" if draw.chosen in draw.near_tie else "overlap")
    action = "serve" if draw.chosen == request.slot_item_id else "substitute"
    return SlotDecision(action, draw.chosen, selection_id, draw.mode, draw.propensity, why=WHY[why_kind],
                        why_kind=why_kind, commission_id=commission_id, view=view_name)


def _maybe_commission(vault: Any, repository: Any, snapshot: RP.Snapshot, view: Any, view_name: str,
                      request: SlotRequest, constants: S.SelectionConstants, *, cell: str | None,
                      capability_name: str | None, warmth: float, material: Any) -> str | None:
    """§6.1: a commission draw when the cell pool has no item with ``P_band >= calibrate_below``."""

    if cell is None or capability_name is None:
        return None
    connection = repository.connection()
    if any(row.get("cell_facet") == cell and row.get("cell_capability") == capability_name
           for row in material.open_commissions(connection, now=request.now)):
        return None
    specs = []
    for item_id in request.cell_pool:
        item = material.item(item_id)
        if item is not None:
            specs.append(_spec(vault, connection, snapshot, item, request.now, material))
    if specs:
        scored = PR.score(view, specs, warmth=warmth, constants=constants, information=False)
        if max(s.p_band for s in scored) >= constants.calibrate_below:
            return None
    lo = vault.learning_objects.get(request.learning_object_id)
    subject = (list(getattr(lo, "subjects", None) or []) or ["default"])[0] if lo is not None else "default"
    return commission_draw(vault, repository, snapshot, view, view_name, learning_object_id=request.learning_object_id,
                           subject=subject, facet=cell, capability_name=capability_name,
                           key=f"{request.decision_key}", now=request.now, constants=constants)


def commission_draw(vault: Any, repository: Any, snapshot: RP.Snapshot, view: Any, view_name: str, *,
                    learning_object_id: str, subject: str, facet: str, capability_name: str, key: str, now: str,
                    constants: S.SelectionConstants | None = None,
                    targets: Sequence[Mapping[str, Any] | None] = (None,),
                    generating_job_id: str | None = None) -> str | None:
    """A commission draw over ``X_c`` (§6.1): the same rule over feature points with ``z = 0``,
    its own seed and ``ad_selections`` row (``kind = commission``). ``generating_job_id``: the
    durable job the generation path drew it in, whose finish starts its expiry (Codex verify F14)."""

    constants = constants or S.constants_from_config(vault.config)
    connection = repository.connection()
    points = S.commission_candidates(capability_name, targets)
    if not points:
        return None
    specs = [PR.point_spec(point, learning_object_id=learning_object_id, subject=subject, facet=facet,
                           capability_name=capability_name) for point in points]
    scored = PR.score(view, specs, constants=constants)
    decision_key = f"commission:{facet}:{capability_name}:{key}"
    from learnloop.adaptive_difficulty.material_view import current_view

    # (``view`` here is the state view: the material view is the operation's.)
    if current_view().lookup(connection, store.SELECTIONS, "decision_key = ?", (decision_key,))[0] != "missing":
        return None
    draw = S.draw(scored, key=f"{facet}:{capability_name}:{key}", design=S.COMMISSION_VERSION, constants=constants)
    chosen = next((point for point, spec in zip(points, specs) if spec.item_id == draw.chosen), None)
    return store.insert_selection(connection, {
        "protection_epoch": current_view().epoch,
        "decision_key": decision_key, "kind": "commission", "view": view_name,
        "learning_object_id": learning_object_id, "cell_facet": facet, "cell_capability": capability_name,
        "mode": draw.mode, "constants": constants.as_dict(),
        "support": [{**s.as_dict(), "propensity": round(draw.propensities.get(s.ref, 0.0), 12)} for s in scored],
        "excluded": [], "seed": draw.seed, "u": draw.u, "chosen_item_id": None, "chosen_point": chosen,
        "propensity": draw.propensity, "empty_support": False, "state_hash": snapshot.state_hash(),
        "versions": {**_versions(vault, snapshot, view_name), "commission": S.COMMISSION_VERSION},
        "algorithm_version": vault.config.algorithms.algorithm_version, "generating_job_id": generating_job_id,
        "created_at": now,
    })


def why_for_presentation(connection: Any, presentation_id: str, *, view: Any) -> dict[str, Any] | None:
    """"Why this item" for a served plan item (§12): the one line of the draw that chose it, or
    None when no AD draw chose it (below the tag, ``selection`` off, a predecessor serve) or its
    item is withheld now (``view``, the material view)."""

    if not store.has_table(connection, store.SELECTIONS):
        return None
    found = view.presentation(connection, presentation_id)
    if found is None:
        return None
    block_id, item_id = str(found["block_id"]), str(found["practice_item_id"])
    for row in reversed(view.selections(connection, kind="serve")):
        if str(row.get("block_id")) != block_id or row.get("chosen_item_id") != item_id:
            continue
        if row["mode"] not in (S.MODE_BAND, S.MODE_CALIBRATE) or not row.get("support"):
            return None
        draw = S.recompute(row)
        kind = "calibrate" if row["mode"] == S.MODE_CALIBRATE else ("band" if item_id in draw.near_tie else "overlap")
        return {"mode": kind, "why": WHY[kind], "selection_id": row["id"]}
    return None


# -- serve-time receipts (§8.2) and the loadings in force (§7.5) ------------------------------------

def frozen_loadings(vault: Any, repository: Any, connection: Any, content_hash: str, served_at: str, *,
                    view: Any) -> tuple[dict[str, Any] | None, str | None]:
    """The item revision's loadings in force at the serve and the coupling version (AD2/AD3)."""

    if not successor_active(vault.config) or not coupling_on(vault.config):
        return None, None
    snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
    structure = snapshot.events.structure
    loadings = structure.loadings(content_hash, RP.days(served_at))
    # The judgments behind the loadings in force only (fix round 11): a judgment onto a facet only
    # withheld material names has no loading in force, so it is not named here either.
    # Only a judgment of a run in force at this epoch (E2).
    from learnloop.adaptive_difficulty import relatedness as R

    in_force = {vault.canonical_facet_id(str(facet)) for facet in loadings}
    live = R.live_judgments(connection, view=view) if loadings else set()
    ids = [row["id"] for row in view.rows(
        connection, "judgment_ledger", "task = 'ad_relatedness' AND left_kind = 'practice_item_revision' AND "
        "left_id = ?", (content_hash,), order="created_at, rowid")
        if vault.canonical_facet_id(str(row["right_id"])) in in_force and str(row["id"]) in live] \
        if loadings else []
    version = ",".join(f"{subject}={value}" for subject, value in sorted(structure.versions.items())) or None
    return {"loadings": {f: round(float(q), 12) for f, q in sorted(loadings.items())}, "judgment_ids": ids}, version


def threshold_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str,
                       presentation_id: str, served_at: str, view: Any) -> list[Any]:
    """The in-process ``ad_threshold@*`` forecasts of one presentation (AD2/AD3)."""

    from learnloop.scheduling.forecast_receipts import ITEM_UNASSISTED_SUCCESS, ForecastReceipt
    from learnloop.scheduling.voi_forecasts import parameter

    from learnloop.adaptive_difficulty.forecasters import EVENT, receipt_key

    if not successor_active(vault.config):
        return []
    snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
    spec = _spec(vault, connection, snapshot, item, served_at, view)
    warmth = _warmth(connection, view, str(item.learning_object_id), served_at)
    constants = S.constants_from_config(vault.config)
    out = []
    for name, state, weights in (
        ("ad_threshold@subject", snapshot.subject, None),
        ("ad_threshold@subject_uniform", snapshot.subject, PR.mixture_weights(snapshot.subject, uniform=True)),
        ("ad_threshold@lo", snapshot.lo_view(str(item.learning_object_id)), None),
    ):
        prediction = PR.predict(state, spec if state.subject_view else _no_loadings(spec), warmth=warmth,
                                weights=weights, band=constants.band)
        out.append(ForecastReceipt(
            receipt_key=receipt_key(presentation_kind, presentation_id, name), kind=ITEM_UNASSISTED_SUCCESS,
            forecaster=name, forecaster_version=f"{THRESHOLD_VERSION}:{P.PRIORS_VERSION}:{P.HYPER_VERSION}",
            scope="presentation", decision_kind="serve", binding_kind=presentation_kind, event=EVENT,
            forecast={"p": round(prediction.p_bar, 8), "event": EVENT, "p_categories": None,
                      "p_band": round(prediction.p_band, 8)},
            inputs={"practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
                    "state_hash": snapshot.state_hash(), "warmth": round(warmth, 8),
                    "features": dict(spec.features or {}), "signals": dict(spec.signals),
                    "loadings": dict(spec.loadings) if state.subject_view else {}},
            parameters=[parameter("priors", P.PRIORS_VERSION, "structural", source="code")],
            versions={"forecaster": THRESHOLD_VERSION, **P.versions()},
            inputs_as_of=served_at, p=prediction.p_bar,
            columns={"decision_ref": presentation_id, "practice_item_id": str(item.id),
                     "learning_object_id": item.learning_object_id, f"{presentation_kind}_id": presentation_id},
        ))
    return out


def _no_loadings(spec: Any) -> Any:
    from dataclasses import replace

    return replace(spec, loadings={})


__all__ = [
    "AD_INELIGIBLE",
    "DISPLACED",
    "PRE_EXPOSED",
    "SUBSTITUTED",
    "SlotCandidate",
    "SlotDecision",
    "SlotRequest",
    "THRESHOLD_FORECASTERS",
    "WHY",
    "commission_draw",
    "decide_slot",
    "frozen_loadings",
    "slot_applies",
    "threshold_receipts",
    "view_for",
    "why_for_presentation",
]

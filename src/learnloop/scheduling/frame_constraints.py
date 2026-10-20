"""The staged frame's mandatory constraint evaluation, as one function both
Today's staged frame and the "Check once" gate call.

Router R2a (``daily_plan.staged_frame``) runs the P4 constraint engine
(``constraint_engine.evaluate``) on every laned item of Today's pool against
one bounded :class:`~learnloop.scheduling.controller_snapshot.ControllerSnapshot`.
DL2 fix round 6 (verify F19, orchestrator ruling): a due "Check once" passes
the same evaluation under every plan policy, DL1's pair included, purely as a
check gate (:mod:`learnloop.scheduling.intent.feasibility`). So the evaluation
lives here, below the daily plan (the import contract keeps scheduling off
``learnloop.daily_plan``), and the frame delegates to it unchanged.

What it decides, per item (fail closed, R2a review F2):

* The hard constraints' inputs (item states, surfaces, reservations).
  Unreadable: no item's constraints can be established, so every item is
  refused (``constraints_unavailable``).
* The controller snapshot (the exposure ledger). Unreadable: a fresh-evidence
  item is refused (``freshness_unknown``); ordinary items are evaluated against
  a snapshot of the reservations alone, which gives them their full verdict.
* Each item's evaluation. A failure refuses that item alone.

An item is anything with ``practice_item_id``, ``learning_object_id``,
``est_minutes``, ``lane`` and ``check_kind`` (the plan's ``PoolItem``, or the
gate's :class:`GateItem`); ``block_for(item, role)`` gives the attention block
it is evaluated in (the frame's lane action; the gate's ``maintain``, the lane
a check is planned in).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.learner.assessment_contracts import compile_assessment_contract
from learnloop.substrate.activities import fingerprint_of
from learnloop.substrate.activities import surface_hash as hash_surface
from learnloop.substrate.instrument_serving import unservable_reason

_LOG = logging.getLogger(__name__)

#: Practice modes whose serve is a fresh-evidence administration (an unseen
#: surface is required): the scheduler's own single-use probe modes.
FRESH_EVIDENCE_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "probe"})
#: Plan checks that are fresh-evidence administrations.
FRESH_EVIDENCE_CHECKS = frozenset({"project_probe"})

ROLE_FRESH_EVIDENCE = "fresh_evidence"
ROLE_PRACTICE = "practice"

#: The named refusal of an item whose hard constraints could not be
#: established because their inputs could not be read (fail closed: an item is
#: never served unchecked; R2a review F2).
CONSTRAINTS_UNAVAILABLE_KEY = "constraints_unavailable"


def item_role(item: Any, practice_mode: str | None) -> str:
    """An item's role in the plan: a fresh-evidence check, or ordinary practice."""

    if getattr(item, "check_kind", None) in FRESH_EVIDENCE_CHECKS or (practice_mode or "") in FRESH_EVIDENCE_MODES:
        return ROLE_FRESH_EVIDENCE
    return ROLE_PRACTICE


def unavailable(part: str, exc: BaseException) -> dict[str, Any]:
    return {
        "constraint_key": CONSTRAINTS_UNAVAILABLE_KEY, "constraint_version": 1,
        "reason": f"{part}_unreadable", "detail": {"error": type(exc).__name__}, "kind": "exclude",
    }


def freshness_unknown(exc: BaseException) -> dict[str, Any]:
    """P4's own fail-closed refusal of a fresh-evidence item whose surface's
    freshness cannot be established (here: the exposure ledger could not be read)."""

    return {
        "constraint_key": "hard_exposure_collision", "constraint_version": 1, "reason": "freshness_unknown",
        "detail": {"note": "the exposure ledger could not be read", "error": type(exc).__name__},
        "kind": "exclude",
    }


@dataclass(frozen=True)
class GateItem:
    """A "Check once" candidate as the gate evaluates it: planned in the
    maintain lane, as a check (``lanes.classify``)."""

    practice_item_id: str
    learning_object_id: str
    est_minutes: float
    lane: str = "maintain"
    check_kind: str = "check_once"


@dataclass
class FrameEvaluation:
    """The mandatory verdicts over the items evaluated, and what the frame's
    annotations read after them (the snapshot, the reservations, the roles)."""

    manifest_hash: str
    refusals: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)
    reserved_items: frozenset[str] = frozenset()
    snapshot: Any = None
    snapshot_hash: str | None = None
    errors: list[str] = field(default_factory=list)
    #: The inputs could not be read: every item refused, nothing else read.
    inputs_error: str | None = None


def surfaces_by_item(repository: Any) -> dict[str, list[dict[str, Any]]]:
    by_item: dict[str, list[dict[str, Any]]] = {}
    with repository.connection() as connection:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'activity_surfaces'"
        ).fetchone()
        if present is None:
            return by_item
        for row in connection.execute(
            "SELECT id, surface_hash, fingerprint, legacy_practice_item_id FROM activity_surfaces "
            "WHERE legacy_practice_item_id IS NOT NULL ORDER BY created_at, id"
        ):
            by_item.setdefault(str(row["legacy_practice_item_id"]), []).append(dict(row))
    return by_item


def frame_candidate(vault: Any, item: Any, role: str, states: Mapping[str, Any], surfaces: Mapping[str, Any],
                    reserved_surface_ids: frozenset[str]) -> Any:
    from learnloop.scheduling import controller_snapshot as cs

    practice_item = vault.practice_items[item.practice_item_id]
    state = states.get(item.practice_item_id)
    rows = surfaces.get(item.practice_item_id, [])
    reserved = next((row for row in rows if row["id"] in reserved_surface_ids), None)
    surface_id = (reserved or (rows[0] if rows else {})).get("id")
    surface_hash = fingerprint = None
    if role == ROLE_FRESH_EVIDENCE:
        # The surface the serve would render, from the item's own contract
        # (resolve_legacy_item's identity), so an item never resolved before
        # is checked against the ledger too. Unknown -> the engine fails
        # closed (freshness_unknown).
        try:
            contract = compile_assessment_contract(vault, practice_item)
            surface_hash, fingerprint = hash_surface(contract), fingerprint_of(contract)
        except Exception:  # noqa: BLE001 - unknown freshness, refused by the engine
            surface_hash = fingerprint = None
    facets = list(getattr(practice_item, "evidence_facets", []) or [])
    return cs.Candidate(
        candidate_ref=item.practice_item_id,
        learning_object_id=item.learning_object_id,
        active=True if state is None else bool(getattr(state, "active", True)),
        quarantined=False,
        purpose="diagnostic" if role == ROLE_FRESH_EVIDENCE else "practice",
        facet_id=facets[0] if facets else None,
        surface_id=surface_id,
        surface_hash=surface_hash,
        fingerprint=fingerprint,
        expected_minutes=round(float(item.est_minutes), 4),
        practice_mode=getattr(practice_item, "practice_mode", None),
        due_at=getattr(state, "due_at", None) if state is not None else None,
        unservable_reason=unservable_reason(practice_item),
    )


def attention_block(action: str, subtype: str | None, *, budget_minutes: float, source: str, lane: Any) -> Any:
    from learnloop.scheduling import staged_policy as sp

    return sp.AttentionBlock(
        action=action, subtype=subtype, commitment_id=None, budget_minutes=float(budget_minutes),
        compatible_purposes=sp._ACTION_PURPOSES.get(action, ()),
        neighborhood={"source": source, "lane": lane},
    )


def fallback_snapshot(candidates: Mapping[str, Any], reserved_surface_ids: frozenset[str]) -> Any:
    """A snapshot without the exposure ledger, for when the controller
    snapshot cannot be built. It carries what the practice-role constraints
    read (the reservations; each candidate's own active and renderable
    flags), so an ordinary item's verdict is the one the full snapshot gives:
    hard exposure and dispersion apply only to fresh-evidence blocks, which
    are refused instead (their freshness cannot be established)."""

    from learnloop.scheduling import controller_snapshot as cs

    return cs.ControllerSnapshot(
        snapshot_hash="", session_id=None, available_minutes=None, energy=None, remaining_minutes=None,
        conservative_duration_minutes=None,
        candidates=tuple(sorted(candidates.values(), key=lambda c: c.candidate_ref)),
        exposure_by_hash={}, exposure_by_fingerprint={}, reserved_assessment_surface_ids=reserved_surface_ids,
        commitments=(), affect_by_commitment={}, param_manifest_hash="", projection_versions={},
    )


def evaluate_mandatory(
    vault: Any,
    repository: Any,
    items: Sequence[Any],
    *,
    clock: Any = None,
    block_for: Callable[[Any, str], Any],
    log_prefix: str = "router R2a: the staged frame",
) -> FrameEvaluation:
    """The mandatory verdicts of ``items`` (those the vault knows), fail closed."""

    from learnloop.scheduling import constraint_engine as ce
    from learnloop.scheduling import controller_snapshot as cs

    known = [item for item in items if item.practice_item_id in vault.practice_items]
    manifest_hash = ce.manifest()["manifest_hash"]
    errors: list[str] = []
    try:
        states = repository.practice_item_states()
        surfaces = surfaces_by_item(repository)
        reserved_rows = repository.reserved_assessment_surfaces()
    except Exception as exc:  # noqa: BLE001 - fail closed: nothing can be established
        _LOG.warning("%s's constraint inputs could not be read; every item is refused", log_prefix, exc_info=True)
        refusal = (unavailable("constraint_inputs", exc),)
        return FrameEvaluation(
            manifest_hash=manifest_hash,
            refusals={item.practice_item_id: refusal for item in known},
            inputs_error=f"constraint_inputs:{type(exc).__name__}",
        )
    reserved_surface_ids = frozenset(str(row["id"]) for row in reserved_rows)
    reserved_items = frozenset(
        str(row["legacy_practice_item_id"]) for row in reserved_rows if row.get("legacy_practice_item_id")
    )
    roles = {
        item.practice_item_id: item_role(item, getattr(vault.practice_items[item.practice_item_id], "practice_mode", None))
        for item in known
    }
    refusals: dict[str, tuple[dict[str, Any], ...]] = {}
    candidates: dict[str, Any] = {}
    for item in known:
        try:
            candidates[item.practice_item_id] = frame_candidate(
                vault, item, roles[item.practice_item_id], states, surfaces, reserved_surface_ids,
            )
        except Exception as exc:  # noqa: BLE001 - fail closed for this item alone
            _LOG.warning("%s: item %s could not be evaluated; refused", log_prefix, item.practice_item_id, exc_info=True)
            refusals[item.practice_item_id] = (unavailable("candidate", exc),)
            errors.append(f"candidate:{type(exc).__name__}")
    ledger_error: BaseException | None = None
    snapshot_hash: str | None = None
    try:
        snapshot = cs.build_snapshot(vault, repository, None, candidates=list(candidates.values()), clock=clock)
        snapshot_hash = snapshot.snapshot_hash
    except Exception as exc:  # noqa: BLE001 - fail closed where the ledger is needed
        _LOG.warning("%s: the controller snapshot could not be built; quick checks are refused", log_prefix,
                     exc_info=True)
        ledger_error = exc
        errors.append(f"snapshot:{type(exc).__name__}")
        snapshot = fallback_snapshot(candidates, reserved_surface_ids)
    for item in sorted(known, key=lambda entry: entry.practice_item_id):
        item_id = item.practice_item_id
        if item_id in refusals:
            continue
        if ledger_error is not None and roles[item_id] == ROLE_FRESH_EVIDENCE:
            refusals[item_id] = (freshness_unknown(ledger_error),)
            continue
        try:
            feasibility = ce.evaluate(candidates[item_id], snapshot, block_for(item, roles[item_id]))
        except Exception as exc:  # noqa: BLE001 - fail closed for this item alone
            _LOG.warning("%s: item %s could not be evaluated; refused", log_prefix, item_id, exc_info=True)
            refusals[item_id] = (unavailable("evaluation", exc),)
            errors.append(f"evaluation:{type(exc).__name__}")
            continue
        if not feasibility.eligible:
            refusals[item_id] = tuple(reason.as_dict() for reason in feasibility.exclusions)
    return FrameEvaluation(
        manifest_hash=manifest_hash,
        refusals=refusals,
        roles=roles,
        reserved_items=reserved_items,
        snapshot=snapshot,
        snapshot_hash=snapshot_hash,
        errors=errors,
    )


__all__ = [
    "CONSTRAINTS_UNAVAILABLE_KEY",
    "FRESH_EVIDENCE_CHECKS",
    "FRESH_EVIDENCE_MODES",
    "FrameEvaluation",
    "GateItem",
    "ROLE_FRESH_EVIDENCE",
    "ROLE_PRACTICE",
    "attention_block",
    "evaluate_mandatory",
    "fallback_snapshot",
    "frame_candidate",
    "freshness_unknown",
    "item_role",
    "surfaces_by_item",
    "unavailable",
]

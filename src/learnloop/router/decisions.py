"""Router R1: decision rows for today's serving paths (spec_action_router_v1 §9).

Three decisions are logged, each as one append-only ``router_decisions`` row:

* **A Today offer** (``today_offer``): the legacy scheduler's composed offer. Its
  chosen candidate is the item Today focuses first and "Next" opens (the head of
  the first non-empty section). Its propensity is exact: the scheduler's seeded
  exploration (design ``scheduler_seeded_exploration``) is the offer's only
  draw, and the scheduler recomposes the offer under every outcome of that draw
  (``OfferTrace.outcomes``), so the probability that each candidate heads the
  offer is a sum over that support. Everything after the draw (goal quota,
  requested floor, forced follow-ups, contrast-pair order, the committed
  presentation pin, ``limit``, the teach-back readiness filter) is inside the
  propensity, not around it. The contrast-pair coin is seeded per session and
  pair, so it is context the decision is conditioned on, not part of its draw.
  When no head is served (the full list while the daily plan serves Today),
  the row records the candidates with ``propensity_kind = 'not_served'`` and no
  chosen candidate, and every bind from it is a learner pick.
* **A staged P2 decision** (``staged_p2``): the P4 staged policy deciding a
  staged-owned golden-path run's next action.
* **A learner pick** (``learner_pick``): the learner started an offered
  candidate other than the offer's head; written with no propensity inside the
  bind's transaction (``db.stores.router.record_learner_pick``).

"Continue" is a candidate wherever a block or item is in progress, and
"stop for today" is always a candidate. Builders are pure; callers commit the
row (an offer's with its receipt, in one transaction).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
import hashlib
import json
import logging
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

CONTINUE_REF = "continue_current"
STOP_REF = "stop_for_today"
#: The Today queue's own exploration (see ``db.stores.router.ROUTER_DESIGNS``).
DESIGN_SCHEDULER_EXPLORATION = "scheduler_seeded_exploration"
#: ``randomization_layer.epsilon_tiebreak`` (the staged within-block draw).
DESIGN_EPSILON_TIEBREAK = "epsilon_tiebreak"
#: An offer that served no head: the learner chooses from the list.
NOT_SERVED = "not_served"
MODE_LEGACY_QUEUE = "legacy_queue"
MODE_STAGED = "staged"
STAGED_POLICY = "staged_policy_v1"

#: A head probability within this of 1 is the deterministic choice.
DETERMINISTIC_TOLERANCE = 1e-12

#: Exclusion reasons logged as counts, not ids: they withhold most of a vault
#: on every build (nothing due, retired, put away) and carry no decision content.
COUNTED_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "retired",
        "inactive_state",
        "diagnostic_microprobe",
        "diagnostic_probe_administered",
        "unservable_stimulus",
        "no_learning_object",
        "lifecycle_put_away",
        "diagnostic_freshness_reserve",
        "cold_start_unattempted",
        "zero_priority",
        # Staged path: items another controller owns, and inactive ones.
        "controller_ownership",
        "active",
    }
)

#: Planner signals carried per Today candidate when non-zero (the rest of each
#: candidate's components stay on its scheduler slate row).
_PLANNER_SIGNALS: tuple[str, ...] = (
    "forgetting_risk",
    "goal_frontier",
    "recent_error",
    "probe_eig",
    "boundary_target",
    "predicted_correctness",
    "new_material",
    "assumed_check",
    "taught_first",
    "placement_layer",
    "placement_predicted_success",
    "intervention_followup",
    "negative_surprise_followup",
    "exploration_selected",
    "probe_committed",
    "cold_followup_deferred_reveal",
)


class OfferHeadMismatch(RuntimeError):
    """The recomposed realized outcome does not reproduce the served head.

    Raised instead of logging a propensity that would not be the probability of
    what was served; the caller logs a warning and publishes the offer unlogged.
    """


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def _exact(probability: float) -> float:
    """A candidate's head probability, to 12 decimals (the row keeps the chosen
    candidate's at full precision)."""

    return round(float(probability), 12)


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _propensity(probability: float) -> tuple[float, str]:
    if probability >= 1.0 - DETERMINISTIC_TOLERANCE:
        return 1.0, "deterministic"
    return probability, "exact"


def split_exclusions(exclusions: Mapping[str, Iterable[str]]) -> dict[str, dict[str, Any]]:
    """``{"named": {reason: [ids]}, "counts": {reason: n}}``, sorted and deduplicated."""

    named: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    for reason, ids in sorted(exclusions.items()):
        unique = sorted(set(ids))
        if not unique:
            continue
        if reason in COUNTED_EXCLUSIONS:
            counts[reason] = len(unique)
        else:
            named[reason] = unique
    return {"named": named, "counts": counts}


# ---------------------------------------------------------------------------
# Today offers
# ---------------------------------------------------------------------------


def head_distribution(
    outcomes: Sequence[Any], head_of: Callable[[Sequence[Any]], str | None]
) -> dict[str | None, float]:
    """P(each item heads the offer) over the exploration's whole support.

    ``outcomes`` are ``ExplorationOutcome``s (probability + composed order);
    ``head_of`` maps a composed order to the item the offer would show first
    (``None`` for an empty offer).
    """

    distribution: dict[str | None, float] = {}
    for outcome in outcomes:
        head = head_of(outcome.composed)
        distribution[head] = distribution.get(head, 0.0) + float(outcome.probability)
    return distribution


def build_today_offer_decision(
    trace: Any,
    *,
    offered: Sequence[Any],
    head_of: Callable[[Sequence[Any]], str | None],
    section_of: Callable[[Any], str],
    served_head: str | None,
    surface: str,
    policy: str,
    in_progress: Mapping[str, Any] | None = None,
    removed: Mapping[str, Iterable[str]] | None = None,
    inputs: Mapping[str, Any] | None = None,
    head_served: bool = True,
    created_at: str | None = None,
) -> dict[str, Any]:
    """The ``router_decisions`` row for one published Today offer.

    ``trace`` is the scheduler's filled ``OfferTrace``; ``offered`` is the
    published list (after ``limit``, the readiness filter and any skip);
    ``served_head`` the item Today shows first. ``head_of`` must apply exactly
    the steps between the trace and that list. ``removed`` names items the
    caller dropped after the build (``teach_back_provider_unready``,
    ``skipped_by_learner``). ``in_progress`` describes an item the session
    already has under way (a committed probe presentation or a saved draft).
    ``inputs`` are the caller's own decision inputs (teach-back readiness),
    hashed with the trace's. ``head_served=False`` logs a list the learner
    picks from: candidates and the queue's head distribution, no chosen
    candidate and no propensity (``not_served``).
    """

    if not trace.outcomes:
        raise ValueError("the offer trace has no exploration outcomes; was it passed to build_due_queue?")
    distribution = head_distribution(trace.outcomes, head_of)
    realized_head = head_of(trace.outcomes[trace.realized].composed)
    if realized_head != served_head:
        raise OfferHeadMismatch(
            f"recomposed head {realized_head!r} != served head {served_head!r} (slate {trace.slate_id})"
        )
    offered_rank = {item.practice_item_id: rank for rank, item in enumerate(offered, start=1)}
    realized_rank = {
        item.practice_item_id: rank
        for rank, item in enumerate(trace.outcomes[trace.realized].composed, start=1)
    }

    # Every candidate any outcome composes (membership can differ only by the
    # teach-back cap), realized order first. Planner values come from the
    # realized offer, else from the greedy order (never from a counterfactual
    # draw's marks).
    by_id: dict[str, Any] = {}
    sources = (trace.outcomes[trace.realized].composed, getattr(trace, "greedy", ()), *(
        outcome.composed for outcome in trace.outcomes
    ))
    for composed in sources:
        for item in composed:
            by_id.setdefault(item.practice_item_id, item)
    composed_ids = {item.practice_item_id for outcome in trace.outcomes for item in outcome.composed}
    by_id = {item_id: item for item_id, item in by_id.items() if item_id in composed_ids}
    ordered_ids = sorted(by_id, key=lambda item_id: (realized_rank.get(item_id, 10**9), item_id))

    candidates: list[dict[str, Any]] = []
    for item_id in ordered_ids:
        item = by_id[item_id]
        components = item.components or {}
        reward = (item.reward_debug or {}) if getattr(item, "reward_debug", None) else {}
        signals = {
            key: _round(float(components[key]))
            for key in _PLANNER_SIGNALS
            if isinstance(components.get(key), (int, float)) and float(components[key]) != 0.0
        }
        entry = {
            "ref": item_id,
            "kind": "item",
            "learning_object_id": item.learning_object_id,
            "practice_mode": item.selected_mode,
            "feasible": True,
            "planner": {
                "priority": _round(float(item.priority)),
                "selection_reward": _round(components.get("selection_reward")),
                "legacy_priority": _round(components.get("legacy_priority")),
                "intent": reward.get("intent"),
                "signals": signals,
            },
            "followup_kind": getattr(item, "followup_kind", None),
            "section": section_of(item),
            "considered_rank": realized_rank.get(item_id),
            "offered_rank": offered_rank.get(item_id),
            "exploration_propensity": _round(trace.base_propensity.get(item_id, 0.0)),
            "propensity": _exact(distribution.get(item_id, 0.0)),
            "scheduler_candidate_id": trace.candidate_ids.get(item_id),
        }
        # Absent means none: a candidate the offer did not show has no
        # offered_rank, an ordinary pick no followup_kind.
        candidates.append({key: value for key, value in entry.items() if value is not None})

    pinned = trace.pinned_item_id
    continuation = None
    if pinned is not None:
        continuation = {"source": "probe_presentation", "practice_item_id": pinned}
    elif in_progress is not None:
        continuation = dict(in_progress)
    if continuation is not None:
        item_id = continuation.get("practice_item_id")
        # One distribution over the refs, "continue" counted once. The pin is
        # the legacy queue's only continuation: whenever the pinned item heads
        # the offer it is served as "continue", so that mass is continue's and
        # the item's own entry carries 0 (``served_as``). A draft is never
        # resumed by the queue itself: its item heads as an ordinary item, and
        # "continue" carries 0.
        continue_probability = 0.0
        if pinned is not None:
            continue_probability = _exact(distribution.get(pinned, 0.0))
            for entry in candidates:
                if entry["ref"] == pinned:
                    entry["propensity"] = 0.0
                    entry["served_as"] = CONTINUE_REF
        candidates.append(
            {
                "ref": CONTINUE_REF,
                "kind": "continue",
                "practice_item_id": item_id,
                "source": continuation.get("source"),
                "feasible": True,
                "propensity": continue_probability,
            }
        )
    candidates.append(
        {
            "ref": STOP_REF,
            "kind": "stop",
            "feasible": True,
            # The legacy queue stops only when it has nothing to offer.
            "propensity": _exact(distribution.get(None, 0.0)),
        }
    )

    if served_head is None:
        chosen_ref = STOP_REF
        chosen_item = None
    elif pinned is not None and served_head == pinned:
        chosen_ref = CONTINUE_REF
        chosen_item = by_id.get(served_head)
    else:
        chosen_ref = served_head
        chosen_item = by_id.get(served_head)
    propensity, propensity_kind = _propensity(distribution.get(served_head, 0.0))
    design = DESIGN_SCHEDULER_EXPLORATION if propensity_kind == "exact" else None
    if not head_served:
        # The learner chooses from this list: nothing was served, so nothing
        # was chosen and no propensity applies (every bind is a learner pick).
        chosen_ref, chosen_item = None, None
        propensity, propensity_kind, design = None, NOT_SERVED, None

    exclusions: dict[str, list[str]] = {
        reason: list(ids) for reason, ids in trace.exclusions.items()
    }
    realized_ids = set(realized_rank)
    capped = [item_id for item_id in trace.greedy_item_ids if item_id not in realized_ids]
    if capped:
        # mvp-0.21 names the value rule that dropped them; below it, the cap.
        exclusions[getattr(trace, "teach_back_exclusion_reason", None) or "teach_back_session_cap"] = capped
    if trace.limit is not None:
        beyond = [
            item.practice_item_id
            for item in trace.outcomes[trace.realized].composed[trace.limit:]
        ]
        if beyond:
            exclusions["beyond_limit"] = beyond
    for reason, ids in (removed or {}).items():
        ids = list(ids)
        if ids:
            exclusions[reason] = ids
    deferred = [str(row.get("practice_item_id")) for row in trace.cold_deferrals if row.get("practice_item_id")]
    if deferred:
        exclusions["cold_followup_deferred"] = deferred
    exclusion_json = split_exclusions(exclusions)

    exploration = dict(trace.exploration)
    detail = {
        "exploration": exploration,
        "head_distribution": {
            (ref if ref is not None else STOP_REF): probability
            for ref, probability in sorted(distribution.items(), key=lambda pair: (pair[0] is None, pair[0] or ""))
            if probability > 0
        },
        "outcome_count": len(trace.outcomes),
        "limit": trace.limit,
        "pinned_item_id": pinned,
        "in_progress": continuation,
        "probe_block_reason": trace.probe_block_reason,
        "placement_active": trace.placement_active,
        "offered_count": len(offered),
        "built_at": trace.now_iso,
        "head_served": head_served,
        "session_context": dict(getattr(trace, "session_context", None) or {}),
        "inputs": dict(inputs or {}),
        # The staged policy does not run on Today's legacy queue (spec §2): no
        # candidate here has a staged eligibility to log.
        "staged_eligibility": "not_evaluated_on_legacy_queue",
    }
    voi_decisions = list(getattr(trace, "voi_decisions", None) or ())
    if voi_decisions:
        # mvp-0.21 (voi_stopping): every value-of-information stop/continue
        # decision the build made, each with its forecast; absent below it.
        detail["voi_decisions"] = voi_decisions
    # The decision's inputs (P4 §3.3): candidates with their planner values,
    # exclusions, the draw's design, the session context (budget, energy), the
    # configuration that shaped the build, and the caller's own inputs. Not the
    # build time: the same inputs at another instant hash alike.
    snapshot_hash = _canonical_hash(
        {
            "algorithm_version": trace.algorithm_version,
            "session_id": trace.session_id,
            "candidates": [
                {key: entry.get(key) for key in ("ref", "kind", "planner", "section", "propensity", "served_as")}
                for entry in candidates
            ],
            "exclusions": exclusion_json,
            "exploration": exploration,
            "limit": trace.limit,
            "pinned_item_id": pinned,
            "in_progress": continuation,
            "head_served": head_served,
            "session_context": getattr(trace, "session_context", None) or {},
            "config": getattr(trace, "config_snapshot", None) or {},
            "inputs": dict(inputs or {}),
        }
    )
    return {
        "id": new_ulid(),
        "receipt_key": f"today_offer:{trace.slate_id}",
        "decision_kind": "today_offer",
        "surface": surface,
        "mode": MODE_LEGACY_QUEUE,
        "policy": policy,
        "algorithm_version": trace.algorithm_version,
        "log_version": ROUTER_LOG_VERSION,
        "session_id": trace.session_id,
        "parent_decision_id": None,
        "scheduler_slate_id": trace.slate_id,
        "controller_decision_id": None,
        "snapshot_hash": snapshot_hash,
        "design": design,
        "seed": exploration.get("seed") if design else None,
        "candidates_json": _dumps(candidates),
        "exclusions_json": _dumps(exclusion_json),
        "candidate_count": len(candidates),
        "chosen_ref": chosen_ref,
        "chosen_practice_item_id": chosen_item.practice_item_id if chosen_item is not None else None,
        "chosen_learning_object_id": chosen_item.learning_object_id if chosen_item is not None else None,
        "chosen_scheduler_candidate_id": (
            trace.candidate_ids.get(chosen_item.practice_item_id) if chosen_item is not None else None
        ),
        "propensity": propensity,
        "propensity_kind": propensity_kind,
        "learner_pick": 0,
        "latency_ms": None,
        "cost_usd": 0.0,
        "detail_json": _dumps(detail),
        "created_at": created_at or utc_now_iso(),
    }


# ---------------------------------------------------------------------------
# Staged P2 decisions
# ---------------------------------------------------------------------------


def _block_ref(action: str | None, subtype: str | None) -> str:
    if not action:
        return "block:none"
    return f"block:{action}" + (f"/{subtype}" if subtype else "")


def build_staged_p2_decision(
    result: Any,
    *,
    ladder: Sequence[Mapping[str, Any]],
    canonical: Mapping[str, Any] | None,
    authority: str,
    veto_reason: str | None,
    run_id: str,
    commitment_id: str | None,
    algorithm_version: str,
    session_id: str | None,
    chosen_learning_object_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """The ``router_decisions`` row for one live staged decision on a P2 run.

    ``result`` is the staged policy's ``DecisionResult``; ``ladder`` the §4.2
    rungs with their eligibility (``staged_policy.ladder_eligibility``);
    ``canonical`` the run's pre-cutover successor (the "continue" candidate);
    ``authority``/``veto_reason`` what the bridge served.

    The chosen candidate is what the bridge served, never a pick it did not
    serve. The bridge (``controller_cutover.advance_live``) serves the run's
    canonical successor when one stands (``continue_current``, deterministic:
    no item of the staged policy's block is served), and nothing on a veto or
    when the run has no successor (``stop_for_today``: the run defers). The
    staged policy's within-block pick, and its ``epsilon_tiebreak`` assignment
    when that pick was randomized, stay on the item candidate it concerns
    (``within_block_assignment``). ``canonical=None`` (no bridge) logs the
    staged decision itself as served: its block, with the within-block item and
    that assignment's propensity.
    """

    trace = result.trace or {}
    block = trace.get("attention_block") or {}
    short_circuit = block.get("short_circuit_reason")
    ranking = trace.get("ranking_inputs") or {}
    ranks = {row["candidate_ref"]: row["rank"] for row in ranking.get("ranked") or []}
    assignment = ranking.get("evsi_assignment") or None
    comparator_scores = ((trace.get("comparator") or {}).get("scores") or {}) if trace.get("comparator") else {}

    candidates: list[dict[str, Any]] = []
    continue_available = bool(canonical and canonical.get("to_state")) or short_circuit == "continuation"
    if continue_available:
        candidates.append(
            {
                "ref": CONTINUE_REF,
                "kind": "continue",
                "source": "continuation" if short_circuit == "continuation" else "p2_run",
                "to_state": (canonical or {}).get("to_state"),
                "reason": (canonical or {}).get("reason"),
                "feasible": True,
            }
        )
    for rung in ladder:
        candidates.append(
            {
                "ref": _block_ref(rung.get("action"), rung.get("subtype")),
                "kind": "block",
                "rung": rung.get("rung"),
                "staged_rule": rung.get("staged_rule"),
                "staged_eligible": bool(rung.get("eligible")),
                "fired": bool(rung.get("fired")),
                "reversible": bool(rung.get("reversible", True)),
                "planner": {key: _round(value) for key, value in (rung.get("planner") or {}).items()},
            }
        )
    randomized = bool(assignment and assignment.get("randomized"))
    feasible_refs = list(trace.get("feasible_set") or [])
    for ref in feasible_refs:
        comparator = comparator_scores.get(ref) if isinstance(comparator_scores, Mapping) else None
        entry: dict[str, Any] = {
            "ref": ref,
            "kind": "item",
            "feasible": True,
            "rank": ranks.get(ref),
            "selector": ranking.get("selector"),
            "legacy_priority": _round(comparator.get("priority")) if isinstance(comparator, Mapping) else None,
        }
        if randomized and ref == result.chosen_candidate_ref:
            # The randomization layer's assignment belongs to the item it drew
            # inside the block, whatever the bridge then served.
            entry["within_block_assignment"] = {
                "design": assignment.get("design") or DESIGN_EPSILON_TIEBREAK,
                "propensity": float(assignment.get("propensity") or 1.0),
                "seed": assignment.get("seed"),
                "assignment_id": assignment.get("assignment_id"),
            }
        candidates.append(entry)
    candidates.append({"ref": STOP_REF, "kind": "stop", "feasible": True})

    exclusions: dict[str, list[str]] = {}
    for ref, reasons in (trace.get("exclusions") or {}).items():
        for reason in reasons or []:
            key = str(reason.get("constraint_key") or reason.get("reason") or "unknown")
            exclusions.setdefault(key, []).append(ref)
    exclusion_json = split_exclusions(exclusions)

    learner_pick = short_circuit == "explicit_learner_choice"
    chosen_item = result.chosen_candidate_ref
    bridged = canonical is not None
    # What the bridge served: the canonical successor, or nothing (a veto, or
    # a run with no successor defers).
    if learner_pick:
        chosen_ref = _block_ref(result.action, result.subtype)
        served = "learner_choice"
    elif authority == "staged_veto":
        chosen_ref, chosen_item, served = STOP_REF, None, "staged_veto"
    elif bridged and not canonical.get("to_state"):
        chosen_ref, chosen_item, served = STOP_REF, None, "no_transition"
    elif bridged:
        # The successor is a run-state transition, served deterministically;
        # it serves none of the staged block's items.
        chosen_ref, chosen_item, served = CONTINUE_REF, None, "canonical_successor"
    elif continue_available:
        chosen_ref, served = CONTINUE_REF, "staged_continuation"
    else:
        chosen_ref, served = _block_ref(result.action, result.subtype), "staged_block"
    for entry in candidates:
        entry["chosen"] = entry["ref"] == chosen_ref

    design = None
    seed = None
    if learner_pick:
        propensity: float | None = None
        propensity_kind = "none"
    else:
        probability = 1.0
        if randomized and chosen_item is not None and served == "staged_block":
            # Only a served staged block's item was drawn by the assignment.
            probability = float(assignment.get("propensity") or 1.0)
            seed = assignment.get("seed")
        propensity, propensity_kind = _propensity(probability)
        if propensity_kind == "exact":
            design = assignment.get("design") or DESIGN_EPSILON_TIEBREAK
        else:
            seed = None
    chosen_lo = chosen_learning_object_id if chosen_item is not None else None
    detail = {
        "run_id": run_id,
        "commitment_id": commitment_id,
        "authority": authority,
        "veto_reason": veto_reason,
        "served": served,
        "staged_rule": result.staged_rule,
        "action": result.action,
        "subtype": result.subtype,
        "stop_reason": result.stop_reason,
        "short_circuit_reason": short_circuit,
        "within_block_assignment": assignment,
        "snapshot_hash": result.snapshot_hash,
        "constraint_manifest_hash": trace.get("constraint_manifest_hash"),
        "why": result.why,
        "already": bool(getattr(result, "already", False)),
    }
    snapshot_hash = _canonical_hash(
        {
            "snapshot_hash": result.snapshot_hash,
            "candidates": candidates,
            "exclusions": exclusion_json,
            "authority": authority,
        }
    )
    return {
        "id": new_ulid(),
        "receipt_key": f"staged_p2:{result.decision_id}",
        "decision_kind": "staged_p2",
        "surface": "p2_bridge",
        "mode": MODE_STAGED,
        "policy": STAGED_POLICY,
        "algorithm_version": algorithm_version,
        "log_version": ROUTER_LOG_VERSION,
        "session_id": session_id,
        "parent_decision_id": None,
        "scheduler_slate_id": None,
        "controller_decision_id": result.decision_id,
        "snapshot_hash": snapshot_hash,
        "design": design,
        "seed": seed,
        "candidates_json": _dumps(candidates),
        "exclusions_json": _dumps(exclusion_json),
        "candidate_count": len(candidates),
        "chosen_ref": chosen_ref,
        "chosen_practice_item_id": chosen_item,
        "chosen_learning_object_id": chosen_lo,
        "chosen_scheduler_candidate_id": None,
        "propensity": propensity,
        "propensity_kind": propensity_kind,
        "learner_pick": 1 if learner_pick else 0,
        "latency_ms": None,
        "cost_usd": 0.0,
        "detail_json": _dumps(detail),
        "created_at": created_at or utc_now_iso(),
    }


def record_decision(repository: Any, row: Mapping[str, Any]) -> bool:
    """Append one decision row in its own transaction; idempotent on its key."""

    with repository.atomic(), repository.connection() as connection:
        return insert_router_decision(connection, row)


def logging_enabled(config: Any) -> bool:
    router = getattr(config, "router", None)
    return bool(getattr(router, "log_decisions", False))


__all__ = [
    "CONTINUE_REF",
    "DESIGN_EPSILON_TIEBREAK",
    "DESIGN_SCHEDULER_EXPLORATION",
    "MODE_LEGACY_QUEUE",
    "MODE_STAGED",
    "NOT_SERVED",
    "OfferHeadMismatch",
    "STOP_REF",
    "build_staged_p2_decision",
    "build_today_offer_decision",
    "head_distribution",
    "logging_enabled",
    "record_decision",
    "split_exclusions",
]

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import timedelta
from math import log
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import FacetRecallState, FacetUncertaintyState, MasteryState, Repository
from learnloop.learner.facet_state_reader import (
    facet_recall_states_for_lo,
    facet_uncertainty_states_for_lo,
    is_canonical_state_vault,
)
from learnloop.learner.mastery import display_mastery
from learnloop.diagnosis.probes import apply_facet_observation
from learnloop.numeric import clamp
from learnloop.learner.recall_coverage import criterion_facet_weights_for_item
from learnloop.vault.models import (
    LoadedVault,
    PracticeItem,
    Rubric,
    learning_object_facet_union,
)


def entropy(distribution: Mapping[str, float]) -> float:
    return -sum(float(p) * log(float(p)) for p in distribution.values() if float(p) > 0)


def normalize_distribution(distribution: Mapping[str, float]) -> dict[str, float]:
    cleaned = {str(label): max(float(probability), 0.0) for label, probability in distribution.items()}
    total = sum(cleaned.values())
    if total <= 0:
        return {}
    return {label: probability / total for label, probability in cleaned.items()}


def candidate_facet_support(item: PracticeItem) -> set[str]:
    return {str(facet) for facet in (item.repair_targets or item.evidence_facets)}


def required_facets(
    vault: LoadedVault,
    learning_object_id: str,
    repository: Repository | None = None,
) -> set[str]:
    """Facets the LO's ACTIVE authored practice items actually measure.

    This is a statement about instruments, not about curriculum: an LO with no
    items measures nothing, and callers doing coverage / probe-target / tutor-
    context math genuinely want that reading. Callers asking "what is this LO
    responsible for" want :func:`scope_facets` instead.
    """

    facets: set[str] = set()
    item_states = repository.practice_item_states() if repository is not None else {}
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object_id:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        facets.update(str(facet) for facet in item.evidence_facets)
    return facets


def scope_facets(
    vault: LoadedVault,
    learning_object_id: str,
    repository: Repository | None = None,
) -> set[str]:
    """Facets an LO is RESPONSIBLE for: blueprint declarations ∪ measured facets.

    ``required_facets`` derives everything from authored practice items, so an
    LO whose items have not been generated yet reports the empty set and
    disappears from any consumer that treats "no facets" as "not real" — most
    consequentially ``resolve_goal_scope``, which drops it outright. The
    blueprints (§7.2 requirement recipes) already declare those facets; nothing
    was reading them here, so a goal over freshly synthesized material resolved
    to nothing and was created inert.

    The union is deliberate and makes this strictly additive: every LO that
    resolved before still resolves (items keep contributing), legacy LOs with no
    blueprints keep their item-derived facets, and item drift outside the
    blueprint is not silently dropped. Nothing loses scope by this change.
    """

    facets = required_facets(vault, learning_object_id, repository)
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is not None:
        facets = facets | {
            str(facet) for facet in learning_object_facet_union(learning_object)
        }
    return facets


#: How much of a cell's measurement debt an INFERRED value relieves
#: (spec_measurement_efficiency_v1 §5.2: "the floor is relieved by inference as
#: well as direct touch, at the Part II discount").  An inferred cell is not a
#: measured cell, but it is also not an unexamined one, and the variance floor
#: should say so.  Part II's inference rules (B1 dominance, B3 entailment) are
#: Stage 8; until one supplies inferred cells this term is inert, which is
#: deliberate — the seam exists so the discount is decided once, in the open,
#: rather than invented by whichever inference rule ships first.
INFERRED_CELL_COVERAGE_DISCOUNT = 0.5

#: The coverage denominator's SEMANTICS version (migration 138).  Bump it when the
#: denominator's meaning changes — never for a bug fix that leaves the meaning
#: intact.  On its own it is not what gets recorded: see
#: :func:`coverage_denominator_version`.
COVERAGE_DENOMINATOR_SEMANTICS = "coverage_contract_frontier_v1"

#: Back-compat alias. Readers that only need the semantics tag keep working.
COVERAGE_DENOMINATOR_VERSION = COVERAGE_DENOMINATOR_SEMANTICS


def coverage_denominator_version(
    vault: LoadedVault, repository: Repository | None = None
) -> str:
    """The version stamped on a rebuild: semantics tag + effective-frontier hash.

    Recorded on every derived-state rebuild so a change in the coverage
    denominator surfaces as exactly ONE honest recalibration entry — "estimates
    recomputed, your evidence unchanged" — instead of a silent jump in displayed
    mastery.

    **Why the hash is over the effective frontier and not over the YAML.**  What
    moves displayed mastery is the set of `(LO, facet, capability)` cells the
    denominator actually counts.  Hashing the authored files instead would be
    wrong in both directions: a comment or `updated_at` touch would mint a
    phantom boundary and narrate a recalibration that did not happen, while a
    facet alias/merge that changes which canonical cells resolve would move the
    denominator without changing any file.  Hashing the resolved cell set makes
    the version a function of the thing being versioned.

    Two properties this buys, both load-bearing (§5.2 / A6):

    * **Idempotence.** Re-running a backfill, or any later ordinary rebuild,
      recomputes the same frontier and therefore the same version, so no second
      recalibration entry is emitted for one change.
    * **One entry per real change.** A vault-content edit that genuinely adds or
      removes cells changes the hash exactly once.

    Legacy vaults with no authored blueprint components contribute no cells and
    hash to the empty frontier, which is correct: their denominator is the
    unchanged legacy item-derived one, so they must never emit a boundary.
    """

    cells: set[tuple[str, str]] = set()
    frontier_by_lo: list[tuple[str, str, str]] = []
    for learning_object_id in sorted(vault.learning_objects):
        cells, authored = contract_frontier(vault, learning_object_id, repository)
        if not (cells and authored):
            # Only LOs whose denominator IS the frontier can move it.
            continue
        frontier_by_lo.extend(
            (learning_object_id, facet, capability)
            for facet, capability in sorted(cells)
        )
    digest = hashlib.sha256(
        json.dumps(sorted(frontier_by_lo), separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"{COVERAGE_DENOMINATOR_SEMANTICS}:{digest}"


def contract_frontier(
    vault: LoadedVault,
    learning_object_id: str,
    repository: Repository | None = None,
) -> tuple[set[tuple[str, str]], bool]:
    """The ``(facet, capability)`` cells this LO's contract actually requires.

    Returns ``(cells, authored)``.  ``authored`` is False when the cells were
    derived from the legacy item-mode fallback rather than from blueprint recipe
    components, which is what lets callers keep legacy vaults on their existing
    behaviour instead of silently re-basing them onto a denominator their content
    never declared.

    §5.2: the coverage denominator becomes the contract frontier instead of the
    union of active items' ``evidence_facets``.  The variance floor is right in
    principle — you should be less certain about what you have not measured — but
    an item-derived denominator is an artifact of AUTHORING HISTORY, not an
    obligation, so the floor was punishing the learner for the system's authoring
    activity.  A cell nobody's goal requires is not a measurement debt.

    The frontier is the UNION over the LO's blueprint recipes, not the
    best-covered single recipe.  That deliberately overstates debt where recipes
    are genuine alternatives, and it is the conservative direction for a variance
    floor (it errs toward less confidence).  It also keeps one definition of
    "required cell" in the vault: ``goal_certification.required_capabilities_for_facet``
    already reads the same components, and a second, subtly different frontier
    would be a worse defect than a slightly wide one.  Per-recipe routing belongs
    with the certification substitution rule (§5.3), which owns "for SOME
    blueprint".
    """

    from learnloop.goals.goal_certification import required_capabilities_for_facet

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return set(), False
    cells: set[tuple[str, str]] = set()
    authored_any = False
    legacy_any = False
    for facet in learning_object_facet_union(learning_object) or sorted(
        required_facets(vault, learning_object_id, repository)
    ):
        canonical = vault.canonical_facet_id(str(facet))
        capabilities, from_legacy_default = required_capabilities_for_facet(
            vault, learning_object, canonical
        )
        if not capabilities:
            continue
        if from_legacy_default:
            legacy_any = True
        else:
            authored_any = True
        for capability in capabilities:
            cells.add((canonical, str(capability)))
    return cells, (authored_any and not legacy_any)


def lo_relative_coverage(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    normalized_facet_weights: Mapping[str, float],
    effective_item_coverage: float,
) -> tuple[float, dict[str, Any]]:
    required = required_facets(vault, learning_object_id, repository)
    open_uncertainties = {
        state.facet_id: state
        for state in facet_uncertainty_states_for_lo(
            vault, repository, learning_object_id, statuses=("open", "resolving")
        )
    }
    measured_required = set(open_uncertainties) if open_uncertainties else required
    if not measured_required:
        return 1.0, {
            "required_facets": [],
            "open_facet_restriction": False,
            "measured_facets": [],
            "facet_importance": {},
            "per_facet_coverage": {},
            "lo_relative_coverage": 1.0,
        }
    config = vault.config.recall_coverage
    importance = {
        facet: 1.0 + config.kappa_uncertain * max(open_uncertainties.get(facet).uncertainty, 0.0)
        if facet in open_uncertainties
        else 1.0
        for facet in measured_required
    }
    per_facet = {
        facet: clamp(effective_item_coverage)
        if float(normalized_facet_weights.get(facet, 0.0)) >= config.tau_facet_share
        else 0.0
        for facet in measured_required
    }
    denominator = sum(importance.values())
    value = 0.0 if denominator <= 0 else sum(importance[f] * per_facet[f] for f in measured_required) / denominator
    trace = {
        "required_facets": sorted(required),
        "open_facet_restriction": bool(open_uncertainties),
        "measured_facets": sorted(measured_required),
        "facet_importance": {facet: importance[facet] for facet in sorted(importance)},
        "per_facet_coverage": {facet: per_facet[facet] for facet in sorted(per_facet)},
        "tau_facet_share": config.tau_facet_share,
        "lo_relative_coverage": clamp(value),
    }
    return clamp(value), trace


def covered_required_fraction(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    aggregate_facet_recall: Mapping[str, FacetRecallState | Mapping[str, Any] | None] | None = None,
    inferred_cells: Mapping[tuple[str, str], float] | None = None,
) -> tuple[float, dict[str, Any]]:
    """Fraction of the contract frontier that carries evidence (§5.2).

    Two denominators live here, and which one applies is a property of the vault:

    * **Contract frontier** — the ``(facet, capability)`` cells the LO's blueprint
      recipes require. This is the §5.2 denominator, and it is per-CELL: a facet
      measured at ``retrieval`` when the contract requires ``transfer`` is not a
      covered obligation, which is the 72%-of-attempts mismatch Step 0 measured.
    * **Legacy item-derived facets** — vaults with no authored blueprint
      components keep the previous behaviour exactly, including its "nothing
      required ⇒ 1.0". §5.2 is strictly additive.

    The vacuous case §5.2 names is the first branch's: an LO that DECLARES a
    frontier but has no instruments used to report 1.0 — full coverage from zero
    measurement — because the item-derived ``required`` set was empty. It now
    reports 0.0, which is the honest reading and (correctly) raises the variance
    floor rather than lowering it.

    ``inferred_cells`` maps a cell to its inference confidence and relieves the
    denominator at :data:`INFERRED_CELL_COVERAGE_DISCOUNT`. No caller supplies it
    yet (Part II is Stage 8); the parameter exists so the discount is decided in
    one place rather than by whichever inference rule ships first.
    """

    frontier, authored = contract_frontier(vault, learning_object_id, repository)
    if frontier and authored:
        return _covered_frontier_fraction(
            vault,
            repository,
            learning_object_id=learning_object_id,
            frontier=frontier,
            aggregate_facet_recall=aggregate_facet_recall,
            inferred_cells=inferred_cells,
        )
    required = required_facets(vault, learning_object_id, repository)
    if not required:
        return 1.0, {
            "required_facets": [],
            "covered_required_facets": [],
            "min_facet_evidence_mass": vault.config.recall_coverage.min_facet_evidence_mass,
            "covered_required_fraction": 1.0,
            "denominator_basis": "legacy_item_facets",
        }
    state_by_facet: dict[str, Any] = {
        state.facet_id: state
        for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
        if state.practice_item_id is None
    }
    for facet, state in dict(aggregate_facet_recall or {}).items():
        if state is not None:
            state_by_facet[str(facet)] = state
    threshold = vault.config.recall_coverage.min_facet_evidence_mass

    def mass(state: Any) -> float:
        if isinstance(state, Mapping):
            return float(state.get("independent_evidence_mass", 0.0))
        return float(getattr(state, "independent_evidence_mass", 0.0))

    covered = sorted(
        facet
        for facet in required
        if mass(state_by_facet.get(facet)) > threshold
    )
    value = len(covered) / len(required)
    return value, {
        "required_facets": sorted(required),
        "covered_required_facets": covered,
        "min_facet_evidence_mass": threshold,
        "covered_required_fraction": value,
        "denominator_basis": "legacy_item_facets",
    }


def _covered_frontier_fraction(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    frontier: set[tuple[str, str]],
    aggregate_facet_recall: Mapping[str, FacetRecallState | Mapping[str, Any] | None] | None,
    inferred_cells: Mapping[tuple[str, str], float] | None,
) -> tuple[float, dict[str, Any]]:
    """Per-cell coverage over the contract frontier."""

    threshold = vault.config.recall_coverage.min_facet_evidence_mass
    facets = sorted({facet for facet, _capability in frontier})

    # Per-cell direct evidence, from the capability ledger. A facet whose only
    # evidence sits at another capability leaves this cell untouched — that
    # distinction is the entire point of the capability axis, and it is invisible
    # to the facet-level `independent_evidence_mass` the legacy branch reads.
    cell_mass: dict[tuple[str, str], float] = {}
    for facet in facets:
        for cell in repository.facet_capability_evidence_for_facet(facet):
            key = (facet, str(cell.capability))
            cell_mass[key] = max(0.0, float(cell.direct_positive_mass)) + max(
                0.0, float(cell.direct_negative_mass)
            )

    # A vault that predates the capability ledger cannot answer per-cell, and
    # answering per-facet while CLAIMING per-cell would be the fabrication this
    # item exists to remove. Fall back to the facet-level mass, recorded as such.
    #
    # The fallback is gated on whether the vault SUPPORTS the ledger, not on
    # whether these facets happen to have rows in it. Keying on row presence
    # would silently credit a `transfer` cell from facet-level mass earned at
    # `retrieval` on any canonical vault that simply has no evidence for this LO
    # yet — the precise error the capability axis exists to stop.
    ledger_available = is_canonical_state_vault(vault)
    facet_mass: dict[str, float] = {}
    for state in facet_recall_states_for_lo(vault, repository, learning_object_id):
        if state.practice_item_id is not None:
            continue
        facet_mass[vault.canonical_facet_id(state.facet_id)] = float(
            state.independent_evidence_mass
        )
    for facet, state in dict(aggregate_facet_recall or {}).items():
        if state is None:
            continue
        value = (
            float(state.get("independent_evidence_mass", 0.0))
            if isinstance(state, Mapping)
            else float(getattr(state, "independent_evidence_mass", 0.0))
        )
        facet_mass[vault.canonical_facet_id(str(facet))] = value

    inferred = {
        (str(key[0]), str(key[1])): float(value)
        for key, value in dict(inferred_cells or {}).items()
    }
    measured: list[dict[str, str]] = []
    inferred_covered: list[dict[str, str]] = []
    uncovered: list[dict[str, str]] = []
    credit = 0.0
    for facet, capability in sorted(frontier):
        cell = {"facet": facet, "capability": capability}
        observed = (
            cell_mass.get((facet, capability), 0.0)
            if ledger_available
            else facet_mass.get(facet, 0.0)
        )
        if observed > threshold:
            measured.append(cell)
            credit += 1.0
        elif (facet, capability) in inferred:
            inferred_covered.append(cell)
            credit += INFERRED_CELL_COVERAGE_DISCOUNT
        else:
            uncovered.append(cell)
    value = clamp(credit / len(frontier))
    return value, {
        "denominator_basis": (
            "contract_frontier" if ledger_available else "contract_frontier_facet_mass"
        ),
        "frontier_cells": [
            {"facet": facet, "capability": capability}
            for facet, capability in sorted(frontier)
        ],
        "measured_cells": measured,
        "inferred_cells": inferred_covered,
        "uncovered_cells": uncovered,
        "inferred_discount": INFERRED_CELL_COVERAGE_DISCOUNT,
        "min_facet_evidence_mass": threshold,
        # Kept for readers written against the legacy trace shape.
        "required_facets": facets,
        "covered_required_facets": sorted(
            {entry["facet"] for entry in measured}
        ),
        "covered_required_fraction": value,
    }


def variance_floor(config: LearnLoopConfig, covered_fraction: float) -> float:
    recall = config.recall_coverage
    c = clamp(covered_fraction)
    return recall.variance_floor_at_full_coverage + (
        recall.variance_floor_at_zero_coverage - recall.variance_floor_at_full_coverage
    ) * (1.0 - c)


def apply_mastery_variance_floor(
    state: MasteryState,
    config: LearnLoopConfig,
    *,
    covered_fraction: float,
) -> tuple[MasteryState, float]:
    floor = variance_floor(config, covered_fraction)
    if state.logit_variance >= floor:
        return state, floor
    return replace(state, logit_variance=floor), floor


def build_facet_uncertainty_updates(
    vault: LoadedVault,
    *,
    item: PracticeItem,
    rubric: Rubric,
    learning_object_id: str,
    attempt_id: str,
    facet_outcomes: Mapping[str, float],
    normalized_facet_weights: Mapping[str, float],
    evidence_rows: Iterable[Mapping[str, Any] | Any],
    error_attributions: Iterable[Any],
    prior_uncertainties: Mapping[str, FacetUncertaintyState | None],
    prior_facet_recall: Mapping[str, FacetRecallState | None],
    observed_error_type: str | None,
    algorithm_version: str,
    now_iso: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = vault.config.facet_diagnostic
    support = candidate_facet_support(item)
    fatal_error_ids = {fatal_error.id for fatal_error in rubric.fatal_errors}
    criterion_facets = criterion_facet_weights_for_item(item, rubric)
    hedged_facets = _hedged_facets(evidence_rows, criterion_facets, item.evidence_facets)
    updates: list[dict[str, Any]] = []
    update_trace: dict[str, Any] = {"updates": {}, "hedged_facets": sorted(hedged_facets)}
    observed_buckets = {
        facet: _facet_outcome_bucket(float(outcome))
        for facet, outcome in facet_outcomes.items()
    }
    for facet in sorted(set(facet_outcomes) | hedged_facets):
        if float(normalized_facet_weights.get(facet, 0.0)) < vault.config.recall_coverage.tau_facet_share:
            continue
        outcome = clamp(float(facet_outcomes.get(facet, 0.5)))
        prior = prior_uncertainties.get(facet)
        prior_recall = prior_facet_recall.get(facet)
        reason = _open_reason(
            outcome,
            hedged=facet in hedged_facets,
            prior_recall=prior_recall,
            config=config,
        )
        if prior is None and reason is None:
            continue
        marginal_before = (
            dict(prior.hypothesis_marginal)
            if prior is not None
            else _initial_hypothesis_marginal(vault, learning_object_id, facet, error_attributions)
        )
        posterior = apply_facet_observation(
            marginal_before,
            facet_id=facet,
            candidate_facet_support=support,
            fatal_error_ids=fatal_error_ids,
            observed_bucket=observed_buckets.get(facet, "mid"),
            observed_error_type=observed_error_type if observed_error_type in fatal_error_ids else None,
        )
        if facet in hedged_facets:
            posterior = _raise_entropy_floor(posterior, config.hedge_uncertainty_floor)
        posterior = normalize_distribution(posterior)
        uncertainty = entropy(posterior)
        status = "resolved" if uncertainty <= config.facet_resolved_threshold else ("resolving" if prior is not None else "open")
        opened_reason = prior.opened_reason if prior is not None else str(reason or "low_facet_outcome")
        opened_by_attempt_id = prior.opened_by_attempt_id if prior is not None else attempt_id
        created_at = prior.created_at if prior is not None else now_iso
        updates.append(
            {
                "id": prior.id if prior is not None else _facet_uncertainty_id(learning_object_id, facet),
                "learning_object_id": learning_object_id,
                "facet_id": facet,
                "hypothesis_marginal": posterior,
                "uncertainty": uncertainty,
                "status": status,
                "opened_by_attempt_id": opened_by_attempt_id,
                "opened_reason": opened_reason,
                "last_evidence_at": now_iso,
                "algorithm_version": algorithm_version,
                "created_at": created_at,
                "updated_at": now_iso,
            }
        )
        update_trace["updates"][facet] = {
            "before": marginal_before,
            "after": posterior,
            "uncertainty_before": entropy(marginal_before),
            "uncertainty_after": uncertainty,
            "uncertainty_drop": entropy(marginal_before) - uncertainty,
            "status": status,
            "opened_reason": opened_reason,
        }
    return updates, update_trace


def facet_state_label(
    facet_id: str,
    uncertainty: FacetUncertaintyState | None,
    recall: FacetRecallState | None,
    min_evidence_mass: float,
) -> str:
    """Diagnostic bucket for one required facet.

    Returns one of ``unexamined`` / ``uncertain`` / ``known_gap`` / ``solid``,
    the same classification ``mastery_diagnostic_view`` renders. ``recall`` is
    the aggregate (``practice_item_id is None``) facet recall state.
    """

    if uncertainty is not None:
        top_label = max(uncertainty.hypothesis_marginal, key=uncertainty.hypothesis_marginal.get)
        if uncertainty.status in {"open", "resolving"}:
            return "uncertain"
        if top_label != f"facet_solid:{facet_id}":
            return "known_gap"
        if recall is not None and recall.independent_evidence_mass > min_evidence_mass:
            return "solid"
        return "unexamined"
    if recall is not None and recall.independent_evidence_mass > min_evidence_mass:
        return "solid"
    return "unexamined"


# Tutor Q&A read-side uncertainty adjustment (design decision, see the tutor_qa
# service): asking about a facet raises the *displayed* diagnostic uncertainty
# instead of writing a facet_uncertainty row. question_events persist, so this
# view is automatically replay-consistent — rebuilding derived state can never
# disagree with it — and the mastery mean is untouched by construction. The
# bump is bounded: at most _QUESTION_BUMP_MAX_COUNT recent unresolved questions
# count, each adding config.tutor_qa.uncertainty_evidence_mass nats.
_QUESTION_BUMP_WINDOW_DAYS = 7
_QUESTION_BUMP_MAX_COUNT = 3


def unresolved_question_facet_counts(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    recall_states: Mapping[str, FacetRecallState] | None = None,
    clock: Clock | None = None,
) -> dict[str, int]:
    """Recent unresolved tutor questions per facet for one LO.

    A question is *unresolved* while no attempt evidence on that facet has
    landed after it (aggregate recall's last_attempt_at). Question events map
    to the LO through their practice item (practice/feedback contexts) or the
    note's related_los (library context)."""

    now = parse_utc(utc_now_iso(clock))
    since = (now - timedelta(days=_QUESTION_BUMP_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if recall_states is None:
        recall_states = {
            state.facet_id: state
            for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
            if state.practice_item_id is None
        }
    counts: dict[str, int] = {}
    for event in repository.question_events(since=since):
        item_id = event.get("practice_item_id")
        note_id = event.get("note_id")
        if item_id is not None:
            item = vault.practice_items.get(item_id)
            if item is None or item.learning_object_id != learning_object_id:
                continue
        elif note_id is not None:
            note = vault.notes.get(note_id)
            if note is None or learning_object_id not in note.related_los:
                continue
        else:
            continue
        for facet in event.get("facets", []):
            facet_id = vault.canonical_facet_id(str(facet))
            recall = recall_states.get(facet_id)
            if (
                recall is not None
                and recall.last_attempt_at is not None
                and recall.last_attempt_at > event["created_at"]
            ):
                continue  # answered by later attempt evidence: resolved
            counts[facet_id] = counts.get(facet_id, 0) + 1
    return counts


def mastery_diagnostic_view(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    mastery = repository.mastery_state(learning_object_id)
    display = display_mastery(mastery) if mastery is not None else None
    recall_states = {
        state.facet_id: state
        for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
        if state.practice_item_id is None
    }
    uncertainty_states = {
        state.facet_id: state
        for state in facet_uncertainty_states_for_lo(vault, repository, learning_object_id)
    }
    required = required_facets(vault, learning_object_id, repository)
    question_counts: dict[str, int] = {}
    if vault.config.tutor_qa.apply_uncertainty_effect:
        question_counts = unresolved_question_facet_counts(
            vault,
            repository,
            learning_object_id,
            recall_states=recall_states,
            clock=clock,
        )
    facets: list[dict[str, Any]] = []
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    for facet in sorted(required | set(uncertainty_states)):
        uncertainty = uncertainty_states.get(facet)
        recall = recall_states.get(facet)
        state = facet_state_label(facet, uncertainty, recall, min_mass)
        known_gap_label = (
            max(uncertainty.hypothesis_marginal, key=uncertainty.hypothesis_marginal.get)
            if state == "known_gap" and uncertainty is not None
            else None
        )
        question_count = question_counts.get(facet, 0)
        question_bump = (
            min(question_count, _QUESTION_BUMP_MAX_COUNT)
            * vault.config.tutor_qa.uncertainty_evidence_mass
        )
        displayed_uncertainty = uncertainty.uncertainty if uncertainty is not None else None
        if question_bump > 0:
            displayed_uncertainty = (displayed_uncertainty or 0.0) + question_bump
            # Asking about a facet the diagnostics call solid/unexamined marks
            # it uncertain in the view; known gaps stay known gaps.
            if state in {"solid", "unexamined"}:
                state = "uncertain"
        facets.append(
            {
                "facet_id": facet,
                "state": state,
                "known_gap": known_gap_label,
                "independent_evidence_mass": recall.independent_evidence_mass if recall is not None else 0.0,
                "uncertainty": displayed_uncertainty,
                "question_uncertainty_bump": question_bump,
                "recent_question_count": question_count,
                "hypothesis_marginal": uncertainty.hypothesis_marginal if uncertainty is not None else None,
            }
        )
    return {
        "learning_object_id": learning_object_id,
        "mastery_mean": display.mastery_mean if display is not None else None,
        "mastery_variance": display.mastery_variance if display is not None else None,
        "required_facets": sorted(required),
        "facets": facets,
    }


def _open_reason(
    outcome: float,
    *,
    hedged: bool,
    prior_recall: FacetRecallState | None,
    config: Any,
) -> str | None:
    if outcome < config.tau_facet_failed:
        if prior_recall is not None and prior_recall.consecutive_failures >= 1:
            return "repeated_facet_failure"
        return "low_facet_outcome"
    if hedged:
        return "hedged_confidence"
    if prior_recall is not None and prior_recall.recall_variance > config.tau_facet_uncertain_variance:
        return "low_facet_outcome"
    return None


def _facet_uncertainty_id(learning_object_id: str, facet_id: str) -> str:
    safe_lo = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in learning_object_id)
    safe_facet = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in facet_id)
    return f"facet_uncertainty_{safe_lo}_{safe_facet}"


def _initial_hypothesis_marginal(
    vault: LoadedVault,
    learning_object_id: str,
    facet_id: str,
    error_attributions: Iterable[Any],
) -> dict[str, float]:
    labels = [f"facet_solid:{facet_id}", f"facet_absent:{facet_id}"]
    for attribution in error_attributions:
        if not _attribution_targets_facet(vault, learning_object_id, attribution, facet_id):
            continue
        label = f"misconception:{getattr(attribution, 'error_type', '')}"
        if label not in labels:
            labels.append(label)
    if len(labels) == 2:
        return {labels[0]: 0.35, labels[1]: 0.65}
    misconception_share = 0.30 / max(len(labels) - 2, 1)
    marginal = {labels[0]: 0.25, labels[1]: 0.45}
    for label in labels[2:]:
        marginal[label] = misconception_share
    return normalize_distribution(marginal)


def _attribution_targets_facet(
    vault: LoadedVault,
    learning_object_id: str,
    attribution: Any,
    facet_id: str,
) -> bool:
    targets = {str(facet) for facet in getattr(attribution, "target_evidence_families", [])}
    if facet_id in targets:
        return True
    error_type = vault.error_types.get(str(getattr(attribution, "error_type", "")))
    learning_object = vault.learning_objects.get(learning_object_id)
    if error_type is None or learning_object is None:
        return not targets
    return learning_object.concept in set(error_type.related_concepts) and not targets


def _hedged_facets(
    evidence_rows: Iterable[Mapping[str, Any] | Any],
    criterion_facets: Mapping[str, Mapping[str, float]],
    item_facets: Iterable[str],
) -> set[str]:
    fallback = set(str(facet) for facet in item_facets)
    hedged: set[str] = set()
    for row in evidence_rows:
        confidence = _row_value(row, "learner_confidence")
        if confidence != "hedged":
            continue
        criterion_id = _row_value(row, "criterion_id")
        mapped = criterion_facets.get(str(criterion_id), {})
        hedged.update(str(facet) for facet, weight in mapped.items() if float(weight) > 0)
        if not mapped:
            hedged.update(fallback)
    return hedged


def _row_value(row: Mapping[str, Any] | Any, key: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(key)
    return getattr(row, key, None)


def _facet_outcome_bucket(outcome: float) -> str:
    if outcome < 0.40:
        return "low"
    if outcome < 0.75:
        return "mid"
    return "high"


def _raise_entropy_floor(distribution: Mapping[str, float], floor: float) -> dict[str, float]:
    posterior = normalize_distribution(distribution)
    if entropy(posterior) >= floor or len(posterior) <= 1:
        return posterior
    uniform = {label: 1.0 / len(posterior) for label in posterior}
    for step in range(1, 21):
        alpha = step / 20
        mixed = {
            label: (1.0 - alpha) * posterior[label] + alpha * uniform[label]
            for label in posterior
        }
        if entropy(mixed) >= floor:
            return normalize_distribution(mixed)
    return uniform

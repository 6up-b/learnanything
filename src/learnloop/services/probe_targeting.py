"""Unresolved-cause-set probe targeting (knowledge-model §11.1).

Implements the §11.1 probe/episode priority order over the task graph, capability
ledger, and observation provenance, so a diagnostic targets what actually needs
discriminating instead of re-establishing settled facts. Priority (rough order):

1. an unresolved failure **cause set** whose candidates imply different repairs
   (distinct facets) -> select an instrument that DISCRIMINATES the candidate
   causes (KM4 contrast bindings / compositional records);
2. capability-direct-vs-prior disagreement -> stays SHADOW (§11.1 item 2;
   `episode_priority_disagreement` earns live authority only on held-out data);
3. the least-certain **bottleneck** requirement shared across at-risk blueprints;
4. the **integration condition** — components strong AND direct integrated
   performance weak -> probe coordination/selection, NOT the components again;
5. **transfer** to a new independent surface family.

Plus the suppression rule: if strong downstream `embedded` evidence already
demonstrates a prerequisite facet, early probes MUST NOT re-establish it.

This is the diagnostic instrument-choice path (already "diagnostic", not routine
scheduling); it is conservative and leaves the live EIG ranking untouched except
to prefer a discriminating instrument when an episode targets a cause set.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.goal_certification import (
    demonstrated_capabilities_for_facet,
    lo_certification,
)
from learnloop.vault.models import LearningObject, LoadedVault


# --- suppression (§11.1 final clause) ---------------------------------------


def prerequisite_already_demonstrated(
    vault: LoadedVault, repository: Repository, facet: str, capability: str
) -> bool:
    """True when a facet-capability already has direct/embedded certification.

    Reads the capability ledger (embedded evidence carries certification credit),
    so a prerequisite demonstrated downstream is not re-probed (§11.1)."""

    return capability in demonstrated_capabilities_for_facet(vault, repository, facet)


def should_suppress_prerequisite_probe(
    vault: LoadedVault, repository: Repository, prerequisite: dict[str, str]
) -> bool:
    facet = str(prerequisite.get("facet") or "")
    capability = str(prerequisite.get("capability") or "")
    if not facet or not capability:
        return False
    return prerequisite_already_demonstrated(vault, repository, facet, capability)


# --- cause-set discrimination (§11.1 priority 1) ----------------------------


def open_cause_sets_for_learning_object(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> list[list[dict[str, Any]]]:
    """Candidate-cause sets from open unresolved-cause factors on this LO.

    Only cause sets whose candidates imply *different repairs* (>= 2 distinct
    facets) qualify — a single-facet ambiguity is a repair, not a discrimination.
    """

    lo_attempts: set[str] = set()
    for attempt in repository.canonical_observation_ledger():
        item = vault.practice_items.get(attempt["practice_item_id"])
        if item is not None and item.learning_object_id == learning_object_id:
            lo_attempts.add(str(attempt["attempt_id"]))

    cause_sets: list[list[dict[str, Any]]] = []
    seen: set[tuple[str, ...]] = set()
    for attempt_id in sorted(lo_attempts):
        for factor in repository.unresolved_cause_factors_for_attempt(attempt_id, status="open"):
            causes = list(factor.get("candidate_causes") or [])
            # P0-era authored cause sets are not safe probe targets until they
            # carry the explicit open-world arm. Otherwise learner effort would
            # be spent discriminating between an accidentally closed pair.
            if not any(
                cause.get("hypothesis_id") == "H_OTHER" or cause.get("open_set") is True
                for cause in causes
                if isinstance(cause, dict)
            ):
                continue
            facets = {str(c.get("facet")) for c in causes if c.get("facet")}
            if len(facets) < 2:
                continue
            key = tuple(sorted(f"{c.get('facet')}#{c.get('capability')}" for c in causes))
            if key in seen:
                continue
            seen.add(key)
            cause_sets.append(causes)
    return cause_sets


def select_discriminating_instrument(
    candidate_causes: list[dict[str, Any]], eligible: list[Any]
) -> Any | None:
    """Pick the eligible instrument that best discriminates the candidate causes.

    A contrast instrument bound to the confused facets (``target_facets`` covering
    two or more candidate-cause facets) can tell them apart; among equally
    discriminating instruments the pre-ranked EIG order (predictive rate, then
    hypothesis EIG) breaks ties, so we never lose measurement efficiency.
    """

    if not eligible:
        return None
    cause_facets = {str(c.get("facet")) for c in candidate_causes if c.get("facet")}
    if len(cause_facets) < 2:
        return eligible[0]

    def coverage(instrument: Any) -> int:
        target_facets = set(getattr(instrument.instrument, "target_facets", ()) or ())
        return len(cause_facets & target_facets)

    ranked = sorted(
        eligible,
        key=lambda ei: (
            -coverage(ei),
            -ei.predictive_information_rate,
            -ei.expected_information_gain,
            ei.item.id,
        ),
    )
    return ranked[0]


def next_cause_set_instrument(
    vault: LoadedVault,
    repository: Repository,
    episode: Any,
    *,
    candidate_causes: list[dict[str, Any]] | None = None,
) -> Any | None:
    """Serve the discriminating instrument for a cause-set diagnostic episode.

    Entering a diagnostic for a cause set selects instruments that discriminate
    between the candidate causes (§11.1) rather than the plain top-EIG instrument.
    """

    from learnloop.services.probe_episodes import eligible_instruments

    if candidate_causes is None:
        cause_sets = open_cause_sets_for_learning_object(vault, repository, episode.learning_object_id)
        candidate_causes = cause_sets[0] if cause_sets else []
    eligible = eligible_instruments(vault, repository, episode)
    if not candidate_causes:
        return eligible[0] if eligible else None
    return select_discriminating_instrument(candidate_causes, eligible)


# --- integration condition (§11.1 priority 4) -------------------------------


def integration_condition_target(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> dict[str, Any] | None:
    """Components strong AND integration weak -> probe coordination, not components.

    Returns the integration (coordination) target when every component is
    demonstrated but an integration factor is not — never a component target.
    """

    cert = lo_certification(vault, repository, learning_object)
    if cert.integration_gaps and not cert.component_gaps:
        return {
            "facet": cert.integration_gaps[0],
            "capability": "coordination",
            "reason": "integration_condition",
            "integration_gaps": list(cert.integration_gaps),
        }
    return None


# --- §11.1 priority orchestrator --------------------------------------------


def probe_priority(
    vault: LoadedVault,
    repository: Repository,
    learning_object: LearningObject,
    *,
    bottleneck: dict[str, Any] | None = None,
    transfer_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the §11.1 priority order into one selected diagnostic target.

    Higher-priority signals win. Capability-direct-vs-prior disagreement (item 2)
    is reported under ``shadow`` only — it never becomes the live selected target
    until it earns held-out validation.
    """

    lo_id = learning_object.id
    considered: list[dict[str, Any]] = []

    cause_sets = open_cause_sets_for_learning_object(vault, repository, lo_id)
    # Drop candidate causes whose prerequisite is already demonstrated downstream.
    filtered_cause_sets: list[list[dict[str, Any]]] = []
    for causes in cause_sets:
        kept = [c for c in causes if not should_suppress_prerequisite_probe(vault, repository, c)]
        if len({str(c.get("facet")) for c in kept if c.get("facet")}) >= 2:
            filtered_cause_sets.append(kept)
    if filtered_cause_sets:
        considered.append(
            {"priority": 1, "kind": "cause_set_discrimination", "candidate_causes": filtered_cause_sets[0]}
        )

    if bottleneck is not None and not should_suppress_prerequisite_probe(vault, repository, bottleneck):
        considered.append({"priority": 3, "kind": "bottleneck", "target": bottleneck})

    integration = integration_condition_target(vault, repository, learning_object)
    if integration is not None:
        considered.append({"priority": 4, "kind": "integration_condition", "target": integration})

    if transfer_target is not None:
        considered.append({"priority": 5, "kind": "transfer", "target": transfer_target})

    considered.sort(key=lambda entry: entry["priority"])
    selected = considered[0] if considered else None
    return {
        "learning_object_id": lo_id,
        "selected": selected,
        "considered": considered,
        # §11.1 item 2 stays shadow; surfaced for logging, never selected live.
        "shadow": {"capability_disagreement": "shadow_only"},
    }

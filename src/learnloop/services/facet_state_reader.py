"""KM2b consumer re-key: canonical shared facet state read adapter (§7.1).

The thirteen legacy readers of the per-LO ``evidence_facet_recall_state`` table
were written against a per-``(learning_object_id, facet_id)`` grain. Under
mvp-0.7 the belief is a vault-level projection keyed on the canonical
(post-alias/post-merge) facet id and the observed capability. This module folds
those capability-sliced canonical rows back into the exact ``FacetRecallState``
shape the consumers already expect, so each read site becomes a one-line
version branch instead of a hand-rolled canonical query.

Design (§7.1):

* A facet's belief is shared vault-wide; each learning object "sees" the facets
  its practice items exercise. Membership is derived from the curriculum (the
  items' ``evidence_facets``), never from the state-table key — so the same
  shared parent surfaces under every LO that touches it.
* Capability rows for one facet are folded into a single facet-level belief:
  Beta pseudo-counts add, so ``alpha = 1 + Σ(alpha_c - 1)`` and likewise for
  beta. This is the canonical analogue of the legacy capability-free per-facet
  aggregate a non-capability-aware consumer read. A single-capability facet
  folds to itself (identity), keeping the common case exact.
* Per-item marginals (``practice_item_id IS NOT NULL``) exist canonically too;
  each maps to the LO that owns the item.

mvp-0.6 vaults never reach this module — the version branch calls the legacy
repository method directly — so legacy replay stays byte-identical.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from learnloop.db.repositories import (
    CanonicalFacetRecallState,
    FacetRecallState,
    FacetUncertaintyState,
    Repository,
)
from learnloop.services.assessment_contracts import KM_ALGORITHM_VERSION
from learnloop.vault.models import LoadedVault


def is_canonical_state_vault(vault: LoadedVault) -> bool:
    """True when this vault reads/writes canonical (mvp-0.7) facet state."""

    return vault.config.algorithms.algorithm_version == KM_ALGORITHM_VERSION


def resolve_canonical_facet(
    vault: LoadedVault, merge_map: dict[str, str], facet_id: str
) -> str:
    """Resolve a facet id to its terminal canonical survivor (§7.1).

    Aliases first (``vault.facet_aliases``), then transitive ``facet_merges``.
    A no-op under mvp-0.6 (aliases already applied at write, merge map empty),
    so callers may apply it unconditionally without disturbing legacy state.
    """

    current = vault.canonical_facet_id(facet_id)
    seen: set[str] = set()
    while current in merge_map and current not in seen:
        seen.add(current)
        current = merge_map[current]
    return current


def _max_iso(a: str | None, b: str | None) -> str | None:
    if a is None:
        return b
    if b is None:
        return a
    return a if a >= b else b


def _min_iso(a: str | None, b: str | None) -> str | None:
    if a is None:
        return b
    if b is None:
        return a
    return a if a <= b else b


def _capability_scope(rows: Iterable[CanonicalFacetRecallState]) -> str:
    caps = sorted({row.capability_key for row in rows})
    return "+".join(caps) if caps else "shared"


def _fold(
    rows: list[CanonicalFacetRecallState],
    *,
    learning_object_id: str,
    facet_id: str,
    practice_item_id: str | None,
) -> FacetRecallState:
    """Fold capability-sliced canonical rows into one legacy-shaped state."""

    alpha = 1.0
    beta = 1.0
    independent_mass = 0.0
    raw_mass = 0.0
    consecutive = 0
    last_observed_at: str | None = None
    last_error_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    for row in rows:
        alpha += row.recall_alpha - 1.0
        beta += row.recall_beta - 1.0
        independent_mass += row.independent_evidence_mass
        raw_mass += row.raw_coverage_mass
        consecutive = max(consecutive, row.consecutive_failures)
        last_observed_at = _max_iso(last_observed_at, row.last_observed_at)
        last_error_at = _max_iso(last_error_at, row.last_error_at)
        created_at = _min_iso(created_at, row.created_at)
        updated_at = _max_iso(updated_at, row.updated_at)
    total = alpha + beta
    mean = alpha / total
    variance = alpha * beta / (total**2 * (total + 1.0))
    return FacetRecallState(
        id=f"canonical:{facet_id}:{_capability_scope(rows)}:{practice_item_id or ''}",
        learning_object_id=learning_object_id,
        facet_id=facet_id,
        practice_item_id=practice_item_id,
        recall_alpha=alpha,
        recall_beta=beta,
        recall_mean=mean,
        recall_variance=variance,
        independent_evidence_mass=independent_mass,
        raw_coverage_mass=raw_mass,
        last_attempt_at=last_observed_at,
        last_error_at=last_error_at,
        consecutive_failures=consecutive,
        algorithm_version=KM_ALGORITHM_VERSION,
        created_at=created_at or (updated_at or ""),
        updated_at=updated_at or "",
    )


class CanonicalFacetStateReader:
    """Serves legacy-shaped per-LO facet states from canonical mvp-0.7 rows.

    Build once (loads the whole canonical cache and resolves the alias+merge map
    a single time), then query per learning object. Cheap to reuse across a
    scheduler/goal build that touches every LO.
    """

    def __init__(self, vault: LoadedVault, repository: Repository) -> None:
        self.vault = vault
        self._merge_map = repository.facet_merge_map()
        self._resolve_cache: dict[str, str] = {}

        aggregate: dict[str, list[CanonicalFacetRecallState]] = defaultdict(list)
        per_item: dict[tuple[str, str], list[CanonicalFacetRecallState]] = defaultdict(list)
        for row in repository.canonical_facet_recall_states():
            canonical = self._resolve(row.facet_id)
            if row.practice_item_id is None:
                aggregate[canonical].append(row)
            else:
                per_item[(canonical, row.practice_item_id)].append(row)
        self._aggregate = aggregate
        self._per_item = per_item

        lo_facets: dict[str, set[str]] = defaultdict(set)
        lo_items: dict[str, list[str]] = defaultdict(list)
        for item in vault.practice_items.values():
            lo_items[item.learning_object_id].append(item.id)
            for facet in item.evidence_facets:
                lo_facets[item.learning_object_id].add(self._resolve(facet))
        self._lo_facets = lo_facets
        self._lo_items = lo_items

    def _resolve(self, facet_id: str) -> str:
        cached = self._resolve_cache.get(facet_id)
        if cached is not None:
            return cached
        current = resolve_canonical_facet(self.vault, self._merge_map, facet_id)
        self._resolve_cache[facet_id] = current
        return current

    def states_for_lo(self, learning_object_id: str) -> list[FacetRecallState]:
        facets = sorted(self._lo_facets.get(learning_object_id, set()))
        states: list[FacetRecallState] = []
        for facet in facets:
            rows = self._aggregate.get(facet)
            if rows:
                states.append(
                    _fold(
                        rows,
                        learning_object_id=learning_object_id,
                        facet_id=facet,
                        practice_item_id=None,
                    )
                )
        for item_id in sorted(self._lo_items.get(learning_object_id, [])):
            for facet in facets:
                rows = self._per_item.get((facet, item_id))
                if rows:
                    states.append(
                        _fold(
                            rows,
                            learning_object_id=learning_object_id,
                            facet_id=facet,
                            practice_item_id=item_id,
                        )
                    )
        return states

    def state_for_facet(
        self,
        learning_object_id: str,
        facet_id: str,
        practice_item_id: str | None = None,
    ) -> FacetRecallState | None:
        canonical = self._resolve(facet_id)
        if practice_item_id is None:
            rows = self._aggregate.get(canonical)
        else:
            rows = self._per_item.get((canonical, practice_item_id))
        if not rows:
            return None
        return _fold(
            rows,
            learning_object_id=learning_object_id,
            facet_id=canonical,
            practice_item_id=practice_item_id,
        )


# -- Version-branched convenience wrappers (the read-site entry points) --------
# mvp-0.6 branches call the legacy repository method with the identical arguments
# and shape, so legacy vaults are byte-for-byte unchanged.


def facet_states_by_lo(
    vault: LoadedVault, repository: Repository
) -> dict[str, list[FacetRecallState]]:
    """``{learning_object_id: [FacetRecallState, ...]}`` for every LO in the vault."""

    if is_canonical_state_vault(vault):
        reader = CanonicalFacetStateReader(vault, repository)
        return {lo: reader.states_for_lo(lo) for lo in vault.learning_objects}
    return {lo: repository.facet_recall_states(lo) for lo in vault.learning_objects}


def facet_recall_states_for_lo(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    reader: CanonicalFacetStateReader | None = None,
) -> list[FacetRecallState]:
    if is_canonical_state_vault(vault):
        reader = reader or CanonicalFacetStateReader(vault, repository)
        return reader.states_for_lo(learning_object_id)
    return repository.facet_recall_states(learning_object_id)


def facet_recall_state_for_lo(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    facet_id: str,
    practice_item_id: str | None = None,
    *,
    reader: CanonicalFacetStateReader | None = None,
) -> FacetRecallState | None:
    if is_canonical_state_vault(vault):
        reader = reader or CanonicalFacetStateReader(vault, repository)
        return reader.state_for_facet(learning_object_id, facet_id, practice_item_id)
    return repository.facet_recall_state(learning_object_id, facet_id, practice_item_id)


def facet_uncertainty_states_for_lo(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    statuses: tuple[str, ...] | None = None,
) -> list[FacetUncertaintyState]:
    """Per-LO facet uncertainty states (KM §7.1).

    mvp-0.6: the legacy per-``(learning_object_id, facet_id)`` diagnostic state,
    byte-identical. mvp-0.7: the legacy per-LO write is retired, and the
    facet-only-keyed re-key is a compositional-misconception concern deferred to
    KM4 — so this returns the conservative empty read (a named KM4 seam) rather
    than reading the legacy table.
    """

    if is_canonical_state_vault(vault):
        return []
    return list(
        repository.facet_uncertainty_states(learning_object_id, statuses=statuses)
    )

"""Goal certification semantics (knowledge-model §9.5).

The dual-axis honesty rule: **attainment/readiness** MAY use expected-performance
projections and shared parent evidence, but **certification/demonstration**
requires direct/embedded, capability-matched, unassisted evidence meeting the
independent-surface and declared-integrated-blueprint requirements. Priors,
claims, calibration residuals, and graph projections never certify.

This module is read-side and pure over the persisted capability ledger
(``facet_capability_evidence``, derived by KM2's canonical projection). It never
writes evidence.

Legacy vaults (mvp-0.6) have no capability ledger; the helpers degrade to the
conservative empty answer there — the caller keeps the legacy mass-gate
``certified`` axis untouched (§15).
"""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.db.repositories import Repository
from learnloop.services.capability_mapping import default_capability_for
from learnloop.services.facet_state_reader import is_canonical_state_vault
from learnloop.vault.models import LearningObject, LoadedVault, recipe_components


@dataclass(frozen=True)
class FacetDemonstration:
    """Capability-matched demonstration state for one facet within an LO (§9.5)."""

    facet_id: str
    required_capabilities: tuple[str, ...]
    demonstrated_capabilities: tuple[str, ...]
    from_legacy_default: bool  # capabilities resolved from a mode default, not authored blueprints

    @property
    def demonstrated(self) -> bool:
        """Every required capability has capability-matched direct evidence.

        An empty requirement set is *not* demonstrated: with no declared
        capability we never silently certify (a facet with no blueprint or
        supporting item cannot be demonstrated on this LO)."""

        if not self.required_capabilities:
            return False
        demonstrated = set(self.demonstrated_capabilities)
        return all(cap in demonstrated for cap in self.required_capabilities)


def required_capabilities_for_facet(
    vault: LoadedVault, learning_object: LearningObject, facet_id: str
) -> tuple[tuple[str, ...], bool]:
    """Capabilities ``facet_id`` is required at within ``learning_object`` (§9.5).

    Prefers authored blueprint recipe components; falls back to the reviewed
    mode-default capability of the LO's items that exercise the facet (a legacy
    facet-only scope). Returns ``(capabilities, from_legacy_default)`` — the flag
    drives the migration warning so a facet-only scope never silently certifies
    every capability.
    """

    canonical = vault.canonical_facet_id(facet_id)
    authored: set[str] = set()
    for blueprint in learning_object.blueprints:
        for recipe in blueprint.recipes:
            for component in recipe_components(recipe):
                if vault.canonical_facet_id(component.facet) == canonical:
                    authored.add(component.capability)
    if authored:
        return tuple(sorted(authored)), False

    legacy: set[str] = set()
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object.id:
            continue
        item_facets = {vault.canonical_facet_id(str(f)) for f in item.evidence_facets}
        if canonical in item_facets:
            legacy.add(default_capability_for(item.practice_mode))
    return tuple(sorted(legacy)), True


def demonstrated_capabilities_for_facet(
    vault: LoadedVault, repository: Repository, facet_id: str
) -> set[str]:
    """Capabilities with capability-matched direct/embedded certification credit.

    Reads ``facet_capability_evidence``: a capability is demonstrated only when
    its ledger cell carries certification credit (> 0) — which by construction
    is direct/embedded, capability-matched, and unassisted (§5.4). Priors,
    claims, and projections have zero credit and never appear.
    """

    canonical = vault.canonical_facet_id(facet_id)
    demonstrated: set[str] = set()
    for cell in repository.facet_capability_evidence_for_facet(canonical):
        if cell.certification_credit > 0.0:
            demonstrated.add(cell.capability)
    return demonstrated


def facet_demonstration(
    vault: LoadedVault,
    repository: Repository,
    learning_object: LearningObject,
    facet_id: str,
) -> FacetDemonstration:
    """The §9.5 demonstration state of one facet within an LO."""

    required, from_legacy = required_capabilities_for_facet(vault, learning_object, facet_id)
    if is_canonical_state_vault(vault):
        demonstrated = demonstrated_capabilities_for_facet(vault, repository, facet_id)
    else:
        demonstrated = set()
    matched = tuple(sorted(set(required) & demonstrated))
    return FacetDemonstration(
        facet_id=vault.canonical_facet_id(facet_id),
        required_capabilities=required,
        demonstrated_capabilities=matched,
        from_legacy_default=from_legacy,
    )


@dataclass(frozen=True)
class LoCertification:
    """Composite-LO certification: component coverage + integration (§9.2/§9.5)."""

    learning_object_id: str
    demonstrated: bool
    component_gaps: tuple[str, ...]  # facets whose required capability is not yet demonstrated
    integration_gaps: tuple[str, ...]  # integration facets lacking direct evidence


def lo_certification(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> LoCertification:
    """Whether a composite LO is demonstrated (§9.2 last bullet, §9.5).

    Certification requires, for at least one declared blueprint: every hard
    component demonstrated at its capability **and** direct evidence on the
    blueprint's declared integration facet. Strong components alone cannot
    saturate it — a planted integration gap keeps the LO undemonstrated.

    Only meaningful on mvp-0.7 vaults with authored blueprints; returns
    ``demonstrated=False`` otherwise (nothing to certify against).
    """

    if not is_canonical_state_vault(vault) or not learning_object.blueprints:
        return LoCertification(
            learning_object_id=learning_object.id,
            demonstrated=False,
            component_gaps=(),
            integration_gaps=(),
        )

    demonstrated_cache: dict[str, set[str]] = {}

    def demo(facet_id: str) -> set[str]:
        canonical = vault.canonical_facet_id(facet_id)
        if canonical not in demonstrated_cache:
            demonstrated_cache[canonical] = demonstrated_capabilities_for_facet(
                vault, repository, canonical
            )
        return demonstrated_cache[canonical]

    any_blueprint_demonstrated = False
    all_component_gaps: set[str] = set()
    all_integration_gaps: set[str] = set()
    for blueprint in learning_object.blueprints:
        for recipe in blueprint.recipes:
            component_gaps: set[str] = set()
            integration_gaps: set[str] = set()
            for component in recipe.all_of:
                if component.modality not in ("hard", "path_specific"):
                    continue
                if component.capability not in demo(component.facet):
                    component_gaps.add(vault.canonical_facet_id(component.facet))
            if recipe.integration is not None:
                integ = recipe.integration
                if integ.capability not in demo(integ.facet):
                    integration_gaps.add(vault.canonical_facet_id(integ.facet))
            all_component_gaps |= component_gaps
            all_integration_gaps |= integration_gaps
            if not component_gaps and not integration_gaps:
                any_blueprint_demonstrated = True
    return LoCertification(
        learning_object_id=learning_object.id,
        demonstrated=any_blueprint_demonstrated,
        component_gaps=tuple(sorted(all_component_gaps)),
        integration_gaps=tuple(sorted(all_integration_gaps)),
    )

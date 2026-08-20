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
from learnloop.goals.certification import is_demonstrated_credit
from learnloop.learner.capability_mapping import default_capability_for
from learnloop.learner.contract_reachability import CONTRACT_MODALITIES
from learnloop.learner.facet_state_reader import is_canonical_state_vault
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
        if is_demonstrated_credit(cell.certification_credit):
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


@dataclass(frozen=True)
class RecipeGaps:
    """The unmet requirements of ONE recipe (§9.2 last bullet, §9.5).

    Extracted from :func:`lo_certification` so that a caller which needs to know
    *which* recipe a certificate rests on — the §5.7 delayed cold probe has to
    name the blueprint/recipe and the certified cells on its task record — runs
    the identical predicate rather than a second copy of it that can drift.
    ``satisfied`` is the per-recipe certification decision; the LO-level decision
    is "some recipe is satisfied".
    """

    blueprint_id: str
    recipe_id: str
    component_gaps: tuple[str, ...]
    integration_gaps: tuple[str, ...]
    #: One entry per unmet ``any_of`` group: the facets of the alternatives, none
    #: of which is demonstrated. A group is OR-joined — satisfying any single
    #: alternative clears the whole entry — so the facets are listed together
    #: rather than folded into ``component_gaps``, which is AND-joined.
    alternative_gaps: tuple[tuple[str, ...], ...] = ()
    #: The ``(facet, capability)`` cells of the ``any_of`` alternatives that are
    #: demonstrated. These are load-bearing for the certificate exactly as the
    #: ``all_of`` cells are, so the cold probe re-tests them (§5.7).
    satisfying_alternatives: tuple[tuple[str, str], ...] = ()
    #: How many contract-modality obligations this recipe declares at all
    #: (``all_of`` cells + one per ``any_of`` group + the integration cell). A
    #: recipe that declares none certifies nothing: with both loops empty every
    #: gap tuple is empty, which must not read as "all requirements met".
    contract_component_count: int = 0

    @property
    def satisfied(self) -> bool:
        if not self.contract_component_count:
            return False
        return not (
            self.component_gaps or self.integration_gaps or self.alternative_gaps
        )


def _demonstrated_resolver(vault: LoadedVault, repository: Repository):
    """Memoized ``facet -> demonstrated capabilities`` over the ledger."""

    cache: dict[str, set[str]] = {}

    def demo(facet_id: str) -> set[str]:
        canonical = vault.canonical_facet_id(facet_id)
        if canonical not in cache:
            cache[canonical] = demonstrated_capabilities_for_facet(
                vault, repository, canonical
            )
        return cache[canonical]

    return demo


def recipe_gaps(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> tuple[RecipeGaps, ...]:
    """Per-recipe gaps for every declared recipe, in declaration order.

    Every declared obligation is gated, at the same modality filter
    ``contract_reachability.CONTRACT_MODALITIES`` uses to build the commissioning
    queue: ``all_of`` conjunctively, ``any_of`` at-least-one (the semantics
    :func:`blueprint_projection.project_recipe` already projects with), and the
    integration cell. Certification and reachability must agree on which
    obligations exist, or a recipe can be blocked by a cell that never appears in
    the queue that exists to close it.

    Requires a canonical-state vault with authored blueprints; returns ``()``
    otherwise, exactly as :func:`lo_certification` returns ``demonstrated=False``
    there (nothing to certify against).
    """

    if not is_canonical_state_vault(vault) or not learning_object.blueprints:
        return ()
    demo = _demonstrated_resolver(vault, repository)
    rows: list[RecipeGaps] = []
    for blueprint in learning_object.blueprints:
        for recipe in blueprint.recipes:
            component_gaps: set[str] = set()
            integration_gaps: set[str] = set()
            contract_components = 0
            for component in recipe.all_of:
                if component.modality not in CONTRACT_MODALITIES:
                    continue
                contract_components += 1
                if component.capability not in demo(component.facet):
                    component_gaps.add(vault.canonical_facet_id(component.facet))
            alternatives = [
                component
                for component in recipe.any_of
                if component.modality in CONTRACT_MODALITIES
            ]
            alternative_gaps: tuple[tuple[str, ...], ...] = ()
            satisfying: set[tuple[str, str]] = set()
            if alternatives:
                contract_components += 1
                for component in alternatives:
                    if component.capability in demo(component.facet):
                        satisfying.add(
                            (
                                vault.canonical_facet_id(component.facet),
                                component.capability,
                            )
                        )
                if not satisfying:
                    alternative_gaps = (
                        tuple(
                            sorted(
                                {
                                    vault.canonical_facet_id(component.facet)
                                    for component in alternatives
                                }
                            )
                        ),
                    )
            if (
                recipe.integration is not None
                and recipe.integration.modality in CONTRACT_MODALITIES
            ):
                integ = recipe.integration
                contract_components += 1
                if integ.capability not in demo(integ.facet):
                    integration_gaps.add(vault.canonical_facet_id(integ.facet))
            rows.append(
                RecipeGaps(
                    blueprint_id=blueprint.id,
                    recipe_id=recipe.id,
                    component_gaps=tuple(sorted(component_gaps)),
                    integration_gaps=tuple(sorted(integration_gaps)),
                    alternative_gaps=alternative_gaps,
                    satisfying_alternatives=tuple(sorted(satisfying)),
                    contract_component_count=contract_components,
                )
            )
    return tuple(rows)


def lo_certification(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> LoCertification:
    """Whether a composite LO is demonstrated (§9.2 last bullet, §9.5).

    Certification requires, for at least one declared blueprint: every hard
    component demonstrated at its capability, at least one alternative of each
    declared ``any_of`` group, **and** direct evidence on the blueprint's
    declared integration facet. Strong components alone cannot saturate it — a
    planted integration gap keeps the LO undemonstrated, and a recipe that
    declares no contract-modality obligation at all certifies nothing.

    Only meaningful on mvp-0.7 vaults with authored blueprints; returns
    ``demonstrated=False`` otherwise (nothing to certify against).

    Delegates the per-recipe predicate to :func:`recipe_gaps` — one copy, so the
    §5.7 cold probe (which needs to name the satisfying recipe) and this
    decision can never disagree about what a certificate is.
    """

    any_blueprint_demonstrated = False
    all_component_gaps: set[str] = set()
    all_integration_gaps: set[str] = set()
    for gaps in recipe_gaps(vault, repository, learning_object):
        all_component_gaps |= set(gaps.component_gaps)
        # An unmet ``any_of`` group contributes every alternative: each is
        # undemonstrated today, and the flat LO-level list has no OR to express.
        # Only one of them has to close for the recipe to clear.
        for group in gaps.alternative_gaps:
            all_component_gaps |= set(group)
        all_integration_gaps |= set(gaps.integration_gaps)
        if gaps.satisfied:
            any_blueprint_demonstrated = True
    return LoCertification(
        learning_object_id=learning_object.id,
        demonstrated=any_blueprint_demonstrated,
        component_gaps=tuple(sorted(all_component_gaps)),
        integration_gaps=tuple(sorted(all_integration_gaps)),
    )

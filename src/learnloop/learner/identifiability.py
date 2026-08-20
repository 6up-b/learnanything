"""Assessment identifiability doctor (knowledge-model §11.3).

This is the real check the M5 synthesis-gate stubbed. It analyzes a criterion /
facet-capability / recipe / planted-profile neighborhood for the SEVEN §11.3
non-identifiability warnings and, per §11.3, emits a **generate-discriminator
need FIRST** (anchor/contrast probe or item, through the existing generation-
needs machinery). A coarsening recommendation is produced only when no
distinguishing assessment exists AND the instructional repairs are identical —
while everything is still pre-lock and cheap to change (§3.4).

The same :func:`analyze_identifiability` runs against two views (§11.3):

1. a **synthesis-time** proposal view (:func:`build_proposal_view`), the
   discriminator-first quality gate;
2. a **pre-first-practice** registry view (:func:`build_registry_view`), run over
   a subject's persisted registry neighborhood so distinctions are coarsened
   before evidence starts accruing against them.

The seven §11.3 warnings, mapped to :attr:`IdentifiabilityFinding.check`:

1. duplicate target signatures that always co-occur;
2. missing anchor/contrast criteria for a facet-capability;
3. different planted profiles with equivalent ideal outcomes;
4. capability confounding (capabilities only ever observed jointly);
5. alternative recipes that grading cannot distinguish;
6. component weakness vs integration weakness with identical signatures;
7. all evidence from one representation / source example / testlet.

The analysis is deterministic and adds zero provider tokens (§12.9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ProposalView:
    """Normalized identifiability inputs extracted from a proposal or registry."""

    # facet id -> normalized sorted instructional-repairs tuple
    facet_repairs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # {criterion_id, correlation_group, facet, capability, role, recipe_ids}
    criterion_targets: list[dict[str, Any]] = field(default_factory=list)
    # {facet, capability, blueprint_id?, recipe_id?, integration?} required by recipes
    recipe_components: list[dict[str, Any]] = field(default_factory=list)
    # KM5 §11.3 checks 3/5/6/7 (all optional; empty on legacy/minimal views):
    # {blueprint_id, recipe_id, integration_facet?, integration_capability?}
    recipes: list[dict[str, Any]] = field(default_factory=list)
    # {id, facets: tuple[str,...], outcome_signature: tuple[str,...]}
    planted_profiles: list[dict[str, Any]] = field(default_factory=list)
    # criterion_id -> representation/source-example/testlet fingerprint signature
    criterion_fingerprints: dict[str, str] = field(default_factory=dict)
    # Meas §D1 measurement_rank only: practice item id -> canonical facet ids that
    # item observes (its ``evidence_facets``). Empty on the synthesis-time
    # proposal view, which has no item pool yet — rank then reads criteria alone.
    # Deliberately NOT read by the seven checks: they judge whether *grading*
    # discriminates two facets, which is a criterion-level question.
    item_observations: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class IdentifiabilityFinding:
    """A structured non-identifiability finding routed to the gate + gen-needs."""

    kind: str  # generate_discriminator | coarsen_distinction
    facet_ids: tuple[str, ...]
    capability: str
    target_key: str
    message: str
    suggested_action: str
    detail: str = ""
    check: int = 0  # 1..7 — which §11.3 warning fired

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "facet_ids": list(self.facet_ids),
            "capability": self.capability,
            "target_key": self.target_key,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "detail": self.detail,
            "check": self.check,
        }


def _criteria_by_facet(view: ProposalView) -> dict[str, set[str]]:
    """facet id -> set of observation signatures (correlation group or criterion id)."""

    signatures: dict[str, set[str]] = {}
    for target in view.criterion_targets:
        facet = str(target.get("facet") or "")
        if not facet:
            continue
        signature = str(target.get("correlation_group") or target.get("criterion_id") or "")
        signatures.setdefault(facet, set()).add(signature)
    return signatures


# --- Meas §D1: measurement_rank ---------------------------------------------
#
# "The number of independent dimensions the item pool can actually resolve,
# against the number of facets declared. If 40 facets resolve to 12 dimensions,
# the system is charging the learner 40 facets' worth of questions for 12 facets'
# worth of information, and that number should be visible rather than inferred
# from frustration."
#
# INDEPENDENCE, as implemented: a facet's *measurement signature* is the set of
# observation units that can see it — every criterion signature (correlation
# group, else criterion id, exactly what ``_criteria_by_facet`` builds and what
# check 1 compares) plus every practice item whose ``evidence_facets`` names it.
# Two facets are the SAME dimension iff those sets are identical: nothing in the
# pool ever moves one without moving the other, so no evidence can separate them
# — this is check 1's behavioural criterion (standing constraint 11), counted
# instead of reported pairwise. Identical signatures therefore contribute ONE
# dimension, not two. A facet with an EMPTY signature contributes ZERO: nothing
# observes it, so it is not a resolvable dimension at all.
#
# The deficit therefore has two distinguishable causes, and §5.8.2 measured them
# to be very different sizes on the real vault — 25 of 39 facets uninstrumented,
# zero synonymous pairs — so the report names both rather than one total:
#   * ``deficit_from_unobserved`` — declared, never observed (D2's problem);
#   * ``deficit_from_collapse``  — observed, but indistinguishable from another
#     facet (D1's problem, the merge candidates).
#
# Analysis only. Computing or publishing the rank proposes nothing and merges
# nothing: collapse candidates surface for review (§D1 "review, never
# auto-merge"), and only ``schedule_discriminating_probes`` — driven by the seven
# checks, never by the rank — persists anything.


def _measurement_signatures(view: ProposalView) -> dict[str, frozenset[str]]:
    """facet id -> the set of observation units that can see it (§D1).

    Union of criterion signatures and observing items. Keys cover every facet
    named by an observer, whether or not the facet is also declared.
    """

    signatures: dict[str, set[str]] = {}
    for facet, criteria in _criteria_by_facet(view).items():
        signatures.setdefault(facet, set()).update(f"criterion:{sig}" for sig in criteria if sig)
    for item_id, facets in view.item_observations.items():
        for facet in facets:
            if facet:
                signatures.setdefault(str(facet), set()).add(f"item:{item_id}")
    return {facet: frozenset(units) for facet, units in signatures.items()}


def declared_facets(view: ProposalView) -> set[str]:
    """Every facet this neighborhood declares — the standing measurement obligations.

    Union of registry entries (``facet_repairs``), facets named by recipe
    components, facets named by criterion targets, and facets observed by items:
    each of those is an assertion that the facet exists and will be measured.
    The registry keys alone under-count, because a subject-scoped registry view
    only keeps facets its blueprints reference.
    """

    facets: set[str] = set(view.facet_repairs)
    for component in view.recipe_components:
        facet = str(component.get("facet") or "")
        if facet:
            facets.add(facet)
    for target in view.criterion_targets:
        facet = str(target.get("facet") or "")
        if facet:
            facets.add(facet)
    for observed in view.item_observations.values():
        facets.update(str(facet) for facet in observed if facet)
    return facets


@dataclass(frozen=True)
class MeasurementRank:
    """§D1's published ratio: resolvable dimensions vs facets declared.

    ``deficit`` is stated outright (``facets_declared - independent_dimensions``)
    rather than left to the reader to subtract, and split by cause. Report-only:
    no field of this is read by a threshold, a merge, or a certification.
    """

    facets_declared: int
    independent_dimensions: int
    deficit: int
    deficit_from_unobserved: int
    deficit_from_collapse: int
    # Declared but observed by nothing — uninstrumented, not synonymous (§D2).
    unobserved_facets: tuple[str, ...] = ()
    # Groups of ≥2 declared facets sharing one measurement signature: the D1
    # collapse candidates, offered to review and never merged from here.
    collapsed_groups: tuple[tuple[str, ...], ...] = ()

    @property
    def rank_ratio(self) -> float | None:
        """``measurement_rank / facets_declared`` (§5.8.2 reports 14/39 = 0.36)."""

        if self.facets_declared <= 0:
            return None
        return self.independent_dimensions / self.facets_declared

    def as_dict(self) -> dict[str, Any]:
        ratio = self.rank_ratio
        return {
            "facets_declared": self.facets_declared,
            "independent_dimensions": self.independent_dimensions,
            "measurement_rank": self.independent_dimensions,
            "rank_ratio": round(ratio, 6) if ratio is not None else None,
            "deficit": self.deficit,
            "deficit_from_unobserved": self.deficit_from_unobserved,
            "deficit_from_collapse": self.deficit_from_collapse,
            "unobserved_facets": list(self.unobserved_facets),
            "collapsed_groups": [list(group) for group in self.collapsed_groups],
        }


def measurement_rank(view: ProposalView) -> MeasurementRank:
    """Count independent measurement dimensions against facets declared (§D1).

    See the block comment above for what "independent" means as implemented.
    Deterministic, read-only, and merge-free.
    """

    declared = declared_facets(view)
    signatures = _measurement_signatures(view)
    groups: dict[frozenset[str], list[str]] = {}
    unobserved: list[str] = []
    for facet in sorted(declared):
        signature = signatures.get(facet) or frozenset()
        if not signature:
            unobserved.append(facet)
            continue
        groups.setdefault(signature, []).append(facet)
    dimensions = len(groups)
    collapsed = tuple(
        tuple(facets) for _signature, facets in sorted(groups.items(), key=lambda kv: sorted(kv[1]))
        if len(facets) > 1
    )
    # Every collapsed group of n facets costs n-1 dimensions; every unobserved
    # facet costs 1. The two add up to the whole deficit by construction.
    collapse_deficit = sum(len(group) - 1 for group in collapsed)
    return MeasurementRank(
        facets_declared=len(declared),
        independent_dimensions=dimensions,
        deficit=len(declared) - dimensions,
        deficit_from_unobserved=len(unobserved),
        deficit_from_collapse=collapse_deficit,
        unobserved_facets=tuple(unobserved),
        collapsed_groups=collapsed,
    )


def _primary_anchor_pairs(view: ProposalView) -> set[tuple[str, str]]:
    """(facet, capability) pairs that at least one criterion PRIMARILY observes."""

    anchors: set[tuple[str, str]] = set()
    for target in view.criterion_targets:
        if str(target.get("role") or "primary") != "primary":
            continue
        facet = str(target.get("facet") or "")
        capability = str(target.get("capability") or "")
        if facet and capability:
            anchors.add((facet, capability))
    return anchors


def _anchor_groups(view: ProposalView) -> dict[tuple[str, str], set[str]]:
    """(facet, capability) -> correlation groups that PRIMARILY observe it."""

    groups: dict[tuple[str, str], set[str]] = {}
    for target in view.criterion_targets:
        if str(target.get("role") or "primary") != "primary":
            continue
        facet = str(target.get("facet") or "")
        capability = str(target.get("capability") or "")
        if not facet or not capability:
            continue
        signature = str(target.get("correlation_group") or target.get("criterion_id") or "")
        groups.setdefault((facet, capability), set()).add(signature)
    return groups


def analyze_identifiability(view: ProposalView) -> list[IdentifiabilityFinding]:
    findings: list[IdentifiabilityFinding] = []
    seen_pairs: set[tuple[str, ...]] = set()

    # Check 2 — missing anchor/contrast for a required (facet, capability).
    anchors = _primary_anchor_pairs(view)
    required_pairs: set[tuple[str, str]] = set()
    for component in view.recipe_components:
        facet = str(component.get("facet") or "")
        capability = str(component.get("capability") or "")
        if facet and capability:
            required_pairs.add((facet, capability))
    for facet, capability in sorted(required_pairs):
        if (facet, capability) not in anchors:
            findings.append(
                IdentifiabilityFinding(
                    kind="generate_discriminator",
                    facet_ids=(facet,),
                    capability=capability,
                    target_key=f"{facet}#{capability}",
                    message=(
                        f"recipe requires ({facet}, {capability}) but no criterion "
                        "primarily observes it — the distinction is not identifiable"
                    ),
                    suggested_action="generate a discriminator (anchor/contrast probe or item)",
                    detail="missing_anchor",
                    check=2,
                )
            )

    # Check 1 — duplicate target signatures that always co-occur.
    signatures = _criteria_by_facet(view)
    facets = sorted(signatures)
    for i in range(len(facets)):
        for j in range(i + 1, len(facets)):
            a, b = facets[i], facets[j]
            sig_a, sig_b = signatures[a], signatures[b]
            if not sig_a or sig_a != sig_b:
                continue
            # a and b are observed by exactly the same criteria and never apart.
            pair = tuple(sorted((a, b)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            repairs_a = view.facet_repairs.get(a, ())
            repairs_b = view.facet_repairs.get(b, ())
            identical_repairs = bool(repairs_a) and repairs_a == repairs_b
            if identical_repairs:
                findings.append(
                    IdentifiabilityFinding(
                        kind="coarsen_distinction",
                        facet_ids=pair,
                        capability="",
                        target_key="|".join(pair),
                        message=(
                            f"facets {a} and {b} are observed by identical criteria and share "
                            "instructional repairs; no assessment can distinguish them"
                        ),
                        suggested_action="coarsen to one facet (no distinguishing assessment, identical repairs)",
                        detail="duplicate_signature_identical_repairs",
                        check=1,
                    )
                )
            else:
                findings.append(
                    IdentifiabilityFinding(
                        kind="generate_discriminator",
                        facet_ids=pair,
                        capability="",
                        target_key="|".join(pair),
                        message=(
                            f"facets {a} and {b} always co-occur under the same criteria; "
                            "no criterion distinguishes them"
                        ),
                        suggested_action="generate a discriminator (anchor/contrast probe or item)",
                        detail="duplicate_signature",
                        check=1,
                    )
                )

    # Check 4 — capability confounding within a single facet.
    caps_by_facet_criterion: dict[str, dict[str, set[str]]] = {}
    for target in view.criterion_targets:
        facet = str(target.get("facet") or "")
        capability = str(target.get("capability") or "")
        criterion = str(target.get("criterion_id") or target.get("correlation_group") or "")
        if not facet or not capability:
            continue
        caps_by_facet_criterion.setdefault(facet, {}).setdefault(criterion, set()).add(capability)
    for facet, per_criterion in sorted(caps_by_facet_criterion.items()):
        all_caps: set[str] = set()
        for caps in per_criterion.values():
            all_caps |= caps
        if len(all_caps) < 2:
            continue
        # A capability is isolable if some criterion observes it alone.
        isolable = {cap for caps in per_criterion.values() if len(caps) == 1 for cap in caps}
        confounded = sorted(all_caps - isolable)
        if len(confounded) >= 2:
            pair = tuple(f"{facet}#{cap}" for cap in confounded)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            findings.append(
                IdentifiabilityFinding(
                    kind="generate_discriminator",
                    facet_ids=(facet,),
                    capability=",".join(confounded),
                    target_key=f"{facet}#capability_confound#{'+'.join(confounded)}",
                    message=(
                        f"facet {facet} capabilities {confounded} are only ever observed "
                        "together; no criterion isolates them (capability confounding)"
                    ),
                    suggested_action="generate a discriminator that isolates each capability",
                    detail="capability_confounding",
                    check=4,
                )
            )

    findings.extend(_check_planted_profiles(view, seen_pairs))
    findings.extend(_check_alternative_recipes(view, seen_pairs))
    findings.extend(_check_component_vs_integration(view, seen_pairs))
    findings.extend(_check_single_representation(view, seen_pairs))
    return findings


def _check_planted_profiles(
    view: ProposalView, seen_pairs: set[tuple[str, ...]]
) -> list[IdentifiabilityFinding]:
    """Check 3 — different planted profiles with equivalent ideal outcomes.

    Two distinct planted misconception/cause profiles whose ideal observable
    outcome signature is identical cannot be told apart by grading: emit a
    contrast-probe discriminator (KM4 target/confused_with parameterization).
    """

    findings: list[IdentifiabilityFinding] = []
    by_outcome: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for profile in view.planted_profiles:
        outcome = tuple(sorted(str(s).strip().lower() for s in (profile.get("outcome_signature") or []) if str(s).strip()))
        if not outcome:
            continue
        by_outcome.setdefault(outcome, []).append(profile)
    for outcome, group in sorted(by_outcome.items()):
        identities = {str(p.get("id") or "") for p in group}
        if len(group) < 2 or len(identities) < 2:
            continue
        facet_ids: list[str] = []
        for profile in group:
            for facet in profile.get("facets") or ():
                if facet and str(facet) not in facet_ids:
                    facet_ids.append(str(facet))
        key = ("planted", *sorted(identities))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        findings.append(
            IdentifiabilityFinding(
                kind="generate_discriminator",
                facet_ids=tuple(facet_ids),
                capability="",
                target_key="planted#" + "|".join(sorted(identities)),
                message=(
                    f"planted profiles {sorted(identities)} produce identical ideal "
                    "outcomes; no assessment distinguishes which cause is present"
                ),
                suggested_action="generate a contrast probe that separates the planted profiles",
                detail="equivalent_planted_profiles",
                check=3,
            )
        )
    return findings


def _recipe_observable_signatures(view: ProposalView) -> dict[str, dict[str, frozenset[str]]]:
    """blueprint_id -> {recipe_id -> frozenset of discriminating criterion signatures}.

    A criterion discriminates recipe ``r`` when its ``recipe_ids`` names ``r``.
    Criteria with no ``recipe_ids`` apply to every recipe and cannot discriminate.
    """

    # blueprint -> set of recipe ids
    recipes_by_blueprint: dict[str, set[str]] = {}
    for recipe in view.recipes:
        blueprint = str(recipe.get("blueprint_id") or "")
        recipe_id = str(recipe.get("recipe_id") or "")
        if blueprint and recipe_id:
            recipes_by_blueprint.setdefault(blueprint, set()).add(recipe_id)

    # recipe_id -> set of criterion signatures observing it
    obs_by_recipe: dict[str, set[str]] = {}
    for target in view.criterion_targets:
        recipe_ids = target.get("recipe_ids") or []
        signature = str(target.get("correlation_group") or target.get("criterion_id") or "")
        if not signature:
            continue
        for recipe_id in recipe_ids:
            obs_by_recipe.setdefault(str(recipe_id), set()).add(signature)

    out: dict[str, dict[str, frozenset[str]]] = {}
    for blueprint, recipe_ids in recipes_by_blueprint.items():
        out[blueprint] = {r: frozenset(obs_by_recipe.get(r, set())) for r in recipe_ids}
    return out


def _check_alternative_recipes(
    view: ProposalView, seen_pairs: set[tuple[str, ...]]
) -> list[IdentifiabilityFinding]:
    """Check 5 — alternative recipes grading cannot distinguish.

    Two recipes under the same blueprint whose observable criterion signatures
    are identical (including both empty) cannot be told apart by grading.
    """

    findings: list[IdentifiabilityFinding] = []
    signatures = _recipe_observable_signatures(view)
    for blueprint, recipe_sigs in sorted(signatures.items()):
        recipe_ids = sorted(recipe_sigs)
        if len(recipe_ids) < 2:
            continue
        for i in range(len(recipe_ids)):
            for j in range(i + 1, len(recipe_ids)):
                a, b = recipe_ids[i], recipe_ids[j]
                if recipe_sigs[a] != recipe_sigs[b]:
                    continue
                key = ("recipe", blueprint, a, b)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                findings.append(
                    IdentifiabilityFinding(
                        kind="generate_discriminator",
                        facet_ids=(),
                        capability="",
                        target_key=f"recipe#{blueprint}#{a}|{b}",
                        message=(
                            f"blueprint {blueprint} recipes {a} and {b} have identical "
                            "observable signatures; grading cannot tell which method was used"
                        ),
                        suggested_action="add a recipe-discriminating criterion or method-selection probe",
                        detail="indistinguishable_recipes",
                        check=5,
                    )
                )
    return findings


def _check_component_vs_integration(
    view: ProposalView, seen_pairs: set[tuple[str, ...]]
) -> list[IdentifiabilityFinding]:
    """Check 6 — component weakness vs integration weakness, identical signatures.

    A recipe with an explicit integration component, but no criterion primarily
    observes that integration factor in a correlation group distinct from its
    component criteria: component failure and integration failure produce the
    same signature. Probe coordination/selection, not the components again.
    """

    findings: list[IdentifiabilityFinding] = []
    anchor_groups = _anchor_groups(view)
    # component (facet, capability) groups per recipe.
    comp_groups_by_recipe: dict[tuple[str, str], set[str]] = {}
    for component in view.recipe_components:
        if component.get("integration"):
            continue
        blueprint = str(component.get("blueprint_id") or "")
        recipe_id = str(component.get("recipe_id") or "")
        facet = str(component.get("facet") or "")
        capability = str(component.get("capability") or "")
        if not (blueprint and recipe_id):
            continue
        groups = anchor_groups.get((facet, capability), set())
        comp_groups_by_recipe.setdefault((blueprint, recipe_id), set()).update(groups)

    for recipe in view.recipes:
        integration_facet = str(recipe.get("integration_facet") or "")
        integration_capability = str(recipe.get("integration_capability") or "")
        if not integration_facet or not integration_capability:
            continue
        blueprint = str(recipe.get("blueprint_id") or "")
        recipe_id = str(recipe.get("recipe_id") or "")
        integ_groups = anchor_groups.get((integration_facet, integration_capability), set())
        comp_groups = comp_groups_by_recipe.get((blueprint, recipe_id), set())
        # Identifiable only if the integration factor has a primary anchor in a
        # correlation group NOT shared with any component observation.
        distinct = integ_groups - comp_groups
        if distinct:
            continue
        key = ("integration", blueprint, recipe_id)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        findings.append(
            IdentifiabilityFinding(
                kind="generate_discriminator",
                facet_ids=(integration_facet,),
                capability=integration_capability,
                target_key=f"integration#{blueprint}#{recipe_id}",
                message=(
                    f"recipe {recipe_id} integration factor ({integration_facet}, "
                    f"{integration_capability}) has no signature distinct from its "
                    "components; component and integration weakness are indistinguishable"
                ),
                suggested_action="probe coordination/selection with a dedicated integration criterion",
                detail="component_vs_integration",
                check=6,
            )
        )
    return findings


def _check_single_representation(
    view: ProposalView, seen_pairs: set[tuple[str, ...]]
) -> list[IdentifiabilityFinding]:
    """Check 7 — all evidence from one representation / source example / testlet.

    When every criterion observing a (facet, capability) shares a single
    representation/source/testlet fingerprint, success may reflect the surface,
    not the facet. Emit an independent-surface discriminator need.
    """

    findings: list[IdentifiabilityFinding] = []
    if not view.criterion_fingerprints:
        return findings
    fingerprints_by_pair: dict[tuple[str, str], set[str]] = {}
    for target in view.criterion_targets:
        facet = str(target.get("facet") or "")
        capability = str(target.get("capability") or "")
        criterion = str(target.get("criterion_id") or "")
        if not facet or not capability:
            continue
        fingerprint = view.criterion_fingerprints.get(criterion)
        if not fingerprint:
            continue
        fingerprints_by_pair.setdefault((facet, capability), set()).add(fingerprint)
    for (facet, capability), fingerprints in sorted(fingerprints_by_pair.items()):
        if len(fingerprints) != 1:
            continue
        key = ("single_rep", facet, capability)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        only = next(iter(fingerprints))
        findings.append(
            IdentifiabilityFinding(
                kind="generate_discriminator",
                facet_ids=(facet,),
                capability=capability,
                target_key=f"single_representation#{facet}#{capability}",
                message=(
                    f"all evidence for ({facet}, {capability}) comes from one "
                    f"representation/source/testlet ({only}); success may reflect the surface"
                ),
                suggested_action="add an independent surface family / representation / testlet",
                detail="single_representation",
                check=7,
            )
        )
    return findings


def build_proposal_view(
    *,
    facets: list[dict[str, Any]],
    criterion_targets: list[dict[str, Any]],
    recipe_components: list[dict[str, Any]],
    recipes: list[dict[str, Any]] | None = None,
    planted_profiles: list[dict[str, Any]] | None = None,
    criterion_fingerprints: dict[str, str] | None = None,
) -> ProposalView:
    """Build the normalized identifiability view from synthesis proposal parts."""

    facet_repairs: dict[str, tuple[str, ...]] = {}
    for facet in facets:
        facet_id = str(facet.get("id") or facet.get("client_item_id") or "")
        if not facet_id:
            continue
        repairs = tuple(sorted(str(r).strip().lower() for r in (facet.get("instructional_repairs") or []) if str(r).strip()))
        facet_repairs[facet_id] = repairs
    fingerprints = dict(criterion_fingerprints or {})
    if not fingerprints:
        for target in criterion_targets:
            criterion = str(target.get("criterion_id") or "")
            fingerprint = target.get("fingerprint") or target.get("representation") or target.get("source_example")
            if criterion and fingerprint:
                fingerprints[criterion] = str(fingerprint)
    return ProposalView(
        facet_repairs=facet_repairs,
        criterion_targets=list(criterion_targets),
        recipe_components=list(recipe_components),
        recipes=list(recipes or []),
        planted_profiles=list(planted_profiles or []),
        criterion_fingerprints=fingerprints,
    )


# --- registry (pre-first-practice) view -------------------------------------


def build_registry_view(
    vault: "LoadedVault",
    subject_id: str | None = None,
    *,
    misconception_records: list[Any] | None = None,
) -> ProposalView:
    """Build the identifiability view from a subject's persisted registry (§11.3).

    This is the pre-first-practice doctor input: the same seven checks run over
    the locked-in facets, blueprints/recipes, rubric criterion targets, and
    compositional misconception records so distinctions are coarsened before
    evidence accrues. Deterministic; reads only the vault registry (plus any
    ``misconception_records`` the caller loaded from the repository for check 3).
    """

    from learnloop.vault.models import recipe_components as _recipe_components

    def _in_subject(subjects: list[str] | None) -> bool:
        if subject_id is None:
            return True
        return bool(subjects) and subject_id in subjects

    # Facets in scope (union of registry entries and blueprint-referenced facets).
    facet_repairs: dict[str, tuple[str, ...]] = {}
    scoped_facets: set[str] = set()
    los = [lo for lo in vault.learning_objects.values() if _in_subject(lo.subjects)]
    for lo in los:
        for blueprint in lo.blueprints:
            for recipe in blueprint.recipes:
                for component in _recipe_components(recipe):
                    scoped_facets.add(component.facet)
    for facet_id, facet in vault.evidence_facets.items():
        if subject_id is not None and facet_id not in scoped_facets:
            continue
        repairs = tuple(
            sorted(str(r).strip().lower() for r in (facet.instructional_repairs or []) if str(r).strip())
        )
        facet_repairs[facet_id] = repairs

    # Recipes + components + integration factors.
    recipes: list[dict[str, Any]] = []
    recipe_component_rows: list[dict[str, Any]] = []
    for lo in los:
        for blueprint in lo.blueprints:
            for recipe in blueprint.recipes:
                integration = recipe.integration
                recipes.append(
                    {
                        "blueprint_id": blueprint.id,
                        "recipe_id": recipe.id,
                        "integration_facet": integration.facet if integration else "",
                        "integration_capability": integration.capability if integration else "",
                    }
                )
                for component in list(recipe.all_of) + list(recipe.any_of):
                    recipe_component_rows.append(
                        {
                            "facet": component.facet,
                            "capability": component.capability,
                            "blueprint_id": blueprint.id,
                            "recipe_id": recipe.id,
                            "integration": False,
                        }
                    )
                if integration is not None:
                    recipe_component_rows.append(
                        {
                            "facet": integration.facet,
                            "capability": integration.capability,
                            "blueprint_id": blueprint.id,
                            "recipe_id": recipe.id,
                            "integration": True,
                        }
                    )

    # Criterion targets (from default rubrics + per-item rubrics) and fingerprints.
    criterion_targets: list[dict[str, Any]] = []
    criterion_fingerprints: dict[str, str] = {}
    scoped_los = {lo.id for lo in los}
    rubrics: list[tuple[str, Any, Any]] = [
        (f"rubric:{mode}", rubric, None) for mode, rubric in vault.default_rubrics.items()
    ]
    # Meas §D1 measurement_rank input (item pool observations), gathered in the
    # same scoped pass. Canonical facet ids so an alias-named item lands on the
    # declared facet it actually observes.
    item_observations: dict[str, tuple[str, ...]] = {}
    for item in vault.practice_items.values():
        if subject_id is not None and item.learning_object_id not in scoped_los:
            continue
        observed = tuple(
            sorted({vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets if facet})
        )
        if observed:
            item_observations[item.id] = observed
        if item.grading_rubric is not None:
            rubrics.append((item.id, item.grading_rubric, item))
    for owner_id, rubric, item in rubrics:
        for criterion in rubric.criteria:
            key = f"{owner_id}:{criterion.id}"
            fingerprint = _item_fingerprint(item) if item is not None else None
            if fingerprint:
                criterion_fingerprints[key] = fingerprint
            for target in criterion.targets:
                criterion_targets.append(
                    {
                        "criterion_id": key,
                        "correlation_group": criterion.correlation_group,
                        "facet": target.facet,
                        "capability": target.capability,
                        "role": target.role,
                        "recipe_ids": list(criterion.recipe_ids),
                    }
                )

    planted_profiles = _planted_profiles_from_registry(
        vault, subject_id, scoped_los, misconception_records=misconception_records
    )

    return ProposalView(
        facet_repairs=facet_repairs,
        criterion_targets=criterion_targets,
        recipe_components=recipe_component_rows,
        recipes=recipes,
        planted_profiles=planted_profiles,
        criterion_fingerprints=criterion_fingerprints,
        item_observations=item_observations,
    )


def _item_fingerprint(item: Any) -> str | None:
    """A representation/source/testlet signature for check 7 (§6 fingerprint)."""

    fp = getattr(item, "evidence_fingerprint", None)
    if fp is not None:
        for attr in ("shared_stimulus_id", "source_family", "solution_recipe_family"):
            value = getattr(fp, attr, None)
            if value:
                return f"{attr}:{value}"
    surface = getattr(item, "surface_family", None)
    if surface:
        return f"surface_family:{surface}"
    return None


def _planted_profiles_from_registry(
    vault: "LoadedVault",
    subject_id: str | None,
    scoped_los: set[str],
    *,
    misconception_records: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """Compositional misconception records as planted profiles for check 3.

    A compositional record's ideal outcome signature is its expected error
    signatures (§10.2); two records over the same confusion with identical
    signatures cannot be discriminated.
    """

    profiles: list[dict[str, Any]] = []
    if misconception_records is not None:
        values: Any = misconception_records
    else:
        records = getattr(vault, "misconceptions", None) or {}
        values = records.values() if hasattr(records, "values") else records
    for record in values:
        lo_id = getattr(record, "learning_object_id", None)
        if subject_id is not None and lo_id is not None and lo_id not in scoped_los:
            continue
        target = getattr(record, "target_facet", None)
        confused = getattr(record, "confused_with_facet", None)
        signatures = getattr(record, "expected_signatures", None) or getattr(record, "error_signatures", None) or []
        facets = tuple(f for f in (target, confused) if f)
        profiles.append(
            {
                "id": getattr(record, "id", None) or getattr(record, "misconception_id", None) or "",
                "facets": facets,
                "outcome_signature": list(signatures),
            }
        )
    return profiles


# --- graph-identifiability report + probe scheduling (§11.3) -----------------


def calculate_registry_hash(view: ProposalView) -> str:
    """A stable hash of the identifiability-relevant registry neighborhood.

    Changes iff a facet's repairs, a criterion target, a recipe, an integration
    factor, a fingerprint, or a planted profile changed — exactly the inputs the
    seven checks read. Drives the pre-first-practice watermark (§11.3).
    """

    import hashlib
    import json

    payload = {
        "facet_repairs": {k: list(v) for k, v in sorted(view.facet_repairs.items())},
        "criterion_targets": sorted(
            (
                str(t.get("criterion_id") or ""),
                str(t.get("correlation_group") or ""),
                str(t.get("facet") or ""),
                str(t.get("capability") or ""),
                str(t.get("role") or ""),
                tuple(sorted(str(r) for r in (t.get("recipe_ids") or []))),
            )
            for t in view.criterion_targets
        ),
        "recipe_components": sorted(
            (str(c.get("facet") or ""), str(c.get("capability") or ""), str(c.get("blueprint_id") or ""),
             str(c.get("recipe_id") or ""), bool(c.get("integration")))
            for c in view.recipe_components
        ),
        "recipes": sorted(
            (str(r.get("blueprint_id") or ""), str(r.get("recipe_id") or ""),
             str(r.get("integration_facet") or ""), str(r.get("integration_capability") or ""))
            for r in view.recipes
        ),
        "planted_profiles": sorted(
            (str(p.get("id") or ""), tuple(sorted(str(f) for f in (p.get("facets") or ()))),
             tuple(sorted(str(s) for s in (p.get("outcome_signature") or []))))
            for p in view.planted_profiles
        ),
        "criterion_fingerprints": sorted(view.criterion_fingerprints.items()),
    }
    encoded = json.dumps(payload, sort_keys=True, default=list).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_misconception_records(vault: "LoadedVault", repository: Any, scoped_los: set[str]) -> list[Any]:
    records: list[Any] = []
    reader = getattr(repository, "misconceptions_for_learning_object", None)
    if reader is None:
        return records
    lo_ids = scoped_los or set(vault.learning_objects)
    for lo_id in sorted(lo_ids):
        try:
            records.extend(reader(lo_id))
        except Exception:  # pragma: no cover - defensive; a missing LO yields nothing
            continue
    return records


def _bundle_findings(findings: list[IdentifiabilityFinding]) -> list[dict[str, Any]]:
    """Group findings into unresolved bundles (never false facet-specific precision)."""

    bundles: list[dict[str, Any]] = []
    for finding in findings:
        bundles.append(
            {
                "target_key": finding.target_key,
                "check": finding.check,
                "kind": finding.kind,
                "facet_ids": list(finding.facet_ids),
                "capability": finding.capability,
                "detail": finding.detail,
                "message": finding.message,
                "suggested_action": finding.suggested_action,
            }
        )
    return bundles


def graph_identifiability_report(
    vault: "LoadedVault",
    repository: Any,
    *,
    subject_id: str | None = None,
    schedule_probes: bool = False,
    clock: Any = None,
) -> dict[str, Any]:
    """Run the §11.3 doctor over each subject's registry neighborhood.

    Reports non-identifiable distinctions as unresolved bundles (never false
    facet-specific precision) and, when ``schedule_probes`` is set, schedules a
    discriminating probe per finding through the synthesis generation-needs
    machinery (a coarsen need only when repairs are identical and no distinguishing
    assessment exists).

    Also publishes Meas §D1's ``measurement_rank`` per subject — analysis only,
    computed off the same view, and never a reason to schedule or apply anything.
    """

    subject_ids = [subject_id] if subject_id else sorted(vault.subjects) or [None]
    subjects_out: list[dict[str, Any]] = []
    total_findings = 0
    total_scheduled = 0
    total_declared = 0
    total_dimensions = 0
    for sid in subject_ids:
        scoped_los = {
            lo.id
            for lo in vault.learning_objects.values()
            if sid is None or (lo.subjects and sid in lo.subjects)
        }
        records = load_misconception_records(vault, repository, scoped_los)
        view = build_registry_view(vault, sid, misconception_records=records)
        findings = analyze_identifiability(view)
        total_findings += len(findings)
        rank = measurement_rank(view)
        total_declared += rank.facets_declared
        total_dimensions += rank.independent_dimensions
        scheduled: list[dict[str, Any]] = []
        if schedule_probes and repository is not None and sid is not None:
            # Findings schedule probes; the rank never does (§D1 review-only).
            scheduled = schedule_discriminating_probes(repository, sid, findings, clock=clock)
            total_scheduled += len(scheduled)
        subjects_out.append(
            {
                "subject_id": sid,
                "registry_hash": calculate_registry_hash(view),
                "findings": [f.as_dict() for f in findings],
                "unresolved_bundles": _bundle_findings(findings),
                "scheduled_probes": scheduled,
                # Meas §D1, plan 3.4. Published even when there are no findings:
                # an uninstrumented facet trips no check yet still costs a
                # dimension, which is the §5.8.2 result on the real vault.
                "measurement_rank": rank.as_dict(),
                "counts": {
                    "findings": len(findings),
                    "by_check": _count_by_check(findings),
                },
            }
        )
    return {
        "version": 1,
        "subject": subject_id,
        "subjects": subjects_out,
        "totals": {
            "findings": total_findings,
            "scheduled_probes": total_scheduled,
            # Sums over the per-subject views, so a facet shared by two subjects
            # counts in both — read the per-subject ranks for exact figures.
            "measurement_rank": {
                "facets_declared": total_declared,
                "independent_dimensions": total_dimensions,
                "deficit": total_declared - total_dimensions,
            },
        },
    }


def _count_by_check(findings: list[IdentifiabilityFinding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        key = str(finding.check)
        counts[key] = counts.get(key, 0) + 1
    return counts


def schedule_discriminating_probes(
    repository: Any,
    subject_id: str,
    findings: list[IdentifiabilityFinding],
    *,
    clock: Any = None,
) -> list[dict[str, Any]]:
    """Persist a discriminating probe / coarsen need per finding (§11.3).

    Reuses the synthesis generation-needs machinery (deduped on
    ``(subject_id, need_kind, target_key)``), so re-running the doctor over an
    unchanged registry does not duplicate needs.
    """

    scheduled: list[dict[str, Any]] = []
    for finding in findings:
        repository.upsert_synthesis_generation_need(
            subject_id=subject_id,
            need_kind=finding.kind,
            target_key=finding.target_key,
            missing_capability=finding.capability or "unresolved",
            facet_ids=list(finding.facet_ids),
            detail=finding.detail,
            clock=clock,
        )
        scheduled.append(
            {"kind": finding.kind, "target_key": finding.target_key, "check": finding.check}
        )
    return scheduled

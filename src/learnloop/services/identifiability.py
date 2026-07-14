"""Synthesis-time assessment identifiability analysis (knowledge-model §11.3).

This is the real check the M5 synthesis-gate stubbed. It analyzes a bootstrap
proposal's criterion / facet-capability targets and blueprint recipes for
non-identifiable distinctions and, per §11.3, emits a **generate-discriminator
need FIRST** (anchor/contrast probe or item, through the existing generation-
needs machinery). A coarsening recommendation is produced only when no
distinguishing assessment exists AND the instructional repairs are identical —
while everything is still pre-lock and cheap to change (§3.4).

Implemented checks (§11.3 items 1, 2, 4 minimum):

1. duplicate target signatures that always co-occur — two facets observed by
   exactly the same criteria (same correlation groups), never apart;
2. missing anchor/contrast criteria — a (facet, capability) a recipe requires
   that no criterion primarily observes;
4. capability confounding — a facet whose capabilities are only ever observed
   jointly in one criterion, with no criterion isolating either.

The analysis is deterministic and adds zero provider tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProposalView:
    """Normalized identifiability inputs extracted from a synthesis proposal."""

    # facet id -> normalized sorted instructional-repairs tuple
    facet_repairs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # {criterion_id, correlation_group, facet, capability, role}
    criterion_targets: list[dict[str, Any]] = field(default_factory=list)
    # {facet, capability} required by blueprint recipes
    recipe_components: list[dict[str, Any]] = field(default_factory=list)


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
                )
            )

    return findings


def build_proposal_view(
    *,
    facets: list[dict[str, Any]],
    criterion_targets: list[dict[str, Any]],
    recipe_components: list[dict[str, Any]],
) -> ProposalView:
    """Build the normalized identifiability view from synthesis proposal parts."""

    facet_repairs: dict[str, tuple[str, ...]] = {}
    for facet in facets:
        facet_id = str(facet.get("id") or facet.get("client_item_id") or "")
        if not facet_id:
            continue
        repairs = tuple(sorted(str(r).strip().lower() for r in (facet.get("instructional_repairs") or []) if str(r).strip()))
        facet_repairs[facet_id] = repairs
    return ProposalView(
        facet_repairs=facet_repairs,
        criterion_targets=list(criterion_targets),
        recipe_components=list(recipe_components),
    )

"""Deterministic, reviewable affected-neighborhood selection for append (ING M7).

Append MUST be linear in newly selected/changed material plus a *bounded* relevant
neighborhood of the existing map — it must never resend the accumulated curriculum
(source-ingestion §3.2 scaling invariant, §10.1). This module builds that
neighborhood deterministically from the new/changed inventories:

- concept names/aliases mentioned in new inventories -> existing concepts/facets;
- cited prerequisite hints -> existing concepts/facets/LOs;
- current provenance (``entity_source_links``) for the appended source/revision;
- source scope (entities already linked to the appended source);
- candidate facet contracts (lexical fingerprint overlap of new claims vs existing
  facet claims / aliases / error signatures).

The result is capped by ``[ingest.budgets].append_neighborhood_input_tokens``; the
selection records *why* every entity matched so the manifest and the review UI can
show it. One additional bounded round is allowed for an unresolved candidate: a new
concept mention that matched nothing on the first pass gets a looser lexical pass so
a genuinely-related-but-differently-worded neighbor is still pulled in (§3.2), still
under the same cap.

Nothing here calls an LLM: it is pure, deterministic, and unit-testable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterable

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "for",
        "with", "that", "this", "when", "every", "each", "if", "then", "on",
        "as", "by", "at", "be", "it", "its", "we", "you", "which", "such",
    }
)


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(str(text).lower()) if t not in _STOPWORDS and len(t) > 1}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _estimate_tokens(obj: Any) -> int:
    return max(1, len(json.dumps(obj, default=str, sort_keys=True)) // 4)


# --- match reasons ----------------------------------------------------------


@dataclass(frozen=True)
class MatchReason:
    kind: str  # concept_name | alias | prerequisite_hint | provenance | source_scope | fingerprint
    detail: str
    score: float


@dataclass
class Neighborhood:
    """The bounded existing-map neighborhood sent to append reconciliation."""

    concepts: list[dict[str, Any]] = field(default_factory=list)
    facets: list[dict[str, Any]] = field(default_factory=list)
    learning_objects: list[dict[str, Any]] = field(default_factory=list)
    blueprints: list[dict[str, Any]] = field(default_factory=list)
    recipes: list[dict[str, Any]] = field(default_factory=list)
    criterion_summaries: list[dict[str, Any]] = field(default_factory=list)
    notation: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    lock_reasons: list[dict[str, Any]] = field(default_factory=list)
    # entity_ref -> [{kind, detail, score}] — why each entity was pulled in.
    match_reasons: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    # neighborhood ids/hashes for the manifest + audit.
    entity_hashes: dict[str, str] = field(default_factory=dict)
    input_token_estimate: int = 0
    budget_tokens: int = 0
    capped: bool = False
    rounds: int = 1

    def as_context(self) -> dict[str, Any]:
        """The compact dict placed in the reconciliation prompt context."""

        return {
            "concepts": self.concepts,
            "facets": self.facets,
            "learning_objects": self.learning_objects,
            "blueprints": self.blueprints,
            "recipes": self.recipes,
            "criterion_summaries": self.criterion_summaries,
            "notation": self.notation,
            "conflicts": self.conflicts,
            "provenance": self.provenance,
            "lock_reasons": self.lock_reasons,
        }

    def as_manifest_record(self) -> dict[str, Any]:
        return {
            "entity_hashes": dict(self.entity_hashes),
            "match_reasons": {k: list(v) for k, v in self.match_reasons.items()},
            "input_token_estimate": self.input_token_estimate,
            "budget_tokens": self.budget_tokens,
            "capped": self.capped,
            "rounds": self.rounds,
        }

    def entity_refs(self) -> set[str]:
        return set(self.entity_hashes.keys())


# --- inventory signal extraction --------------------------------------------


@dataclass
class _NewSignals:
    concept_names: set[str]
    aliases: set[str]
    prerequisite_hints: set[str]
    claim_token_sets: list[set[str]]
    source_ids: set[str]
    revision_ids: set[str]

    def all_name_tokens(self) -> set[str]:
        out: set[str] = set()
        for name in self.concept_names | self.aliases | self.prerequisite_hints:
            out |= _tokens(name)
        return out


def extract_new_signals(
    new_inventories: list[dict[str, Any]],
    *,
    source_ids: Iterable[str] = (),
    revision_ids: Iterable[str] = (),
) -> _NewSignals:
    """Pull the deterministic match signals out of the new/changed inventories."""

    concept_names: set[str] = set()
    aliases: set[str] = set()
    prerequisite_hints: set[str] = set()
    claim_token_sets: list[set[str]] = []
    for entry in new_inventories:
        inventory = entry.get("inventory") if "inventory" in entry else entry
        if not isinstance(inventory, dict):
            continue
        for mention in inventory.get("concept_mentions", []) or []:
            name = str(mention.get("name") or "").strip()
            if name:
                concept_names.add(name)
            for alias in mention.get("aliases", []) or []:
                if str(alias).strip():
                    aliases.add(str(alias).strip())
        for claim in inventory.get("claims", []) or []:
            statement = str(claim.get("statement") or "")
            if statement:
                claim_token_sets.append(_tokens(statement))
            for hint in claim.get("prerequisite_hints", []) or []:
                if str(hint).strip():
                    prerequisite_hints.add(str(hint).strip())
        for procedure in inventory.get("procedure_signals", []) or []:
            contract = str(procedure.get("contract") or "")
            if contract:
                claim_token_sets.append(_tokens(contract))
    return _NewSignals(
        concept_names=concept_names,
        aliases=aliases,
        prerequisite_hints=prerequisite_hints,
        claim_token_sets=claim_token_sets,
        source_ids=set(str(s) for s in source_ids),
        revision_ids=set(str(r) for r in revision_ids),
    )


# --- selection --------------------------------------------------------------


def _hash_entity(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + sha256(encoded.encode("utf-8")).hexdigest()[:16]


def select_neighborhood(
    vault: LoadedVault,
    repository: Repository,
    new_inventories: list[dict[str, Any]],
    *,
    budget_tokens: int,
    source_ids: Iterable[str] = (),
    revision_ids: Iterable[str] = (),
    fingerprint_threshold: float = 0.25,
    loose_threshold: float = 0.12,
) -> Neighborhood:
    """Select the bounded affected-map neighborhood (deterministic, §10.1/§3.2)."""

    signals = extract_new_signals(new_inventories, source_ids=source_ids, revision_ids=revision_ids)
    provenance_entities = _provenance_matched_entities(repository, signals)

    # Score every existing facet + concept deterministically.
    scored: dict[str, tuple[float, list[MatchReason]]] = {}

    def add_reason(ref: str, reason: MatchReason) -> None:
        score, reasons = scored.get(ref, (0.0, []))
        scored[ref] = (score + reason.score, [*reasons, reason])

    name_tokensets = {name: _tokens(name) for name in signals.concept_names | signals.aliases}
    hint_tokensets = {h: _tokens(h) for h in signals.prerequisite_hints}

    for facet_id, facet in vault.evidence_facets.items():
        ref = f"facet:{facet_id}"
        claim_tokens = _tokens(facet.claim or "")
        title_tokens = _tokens((facet.title or "") + " " + " ".join(facet.aliases or []))
        # concept-name / alias match
        for name, ntoks in name_tokensets.items():
            if ntoks and (ntoks <= (claim_tokens | title_tokens) or _jaccard(ntoks, title_tokens) >= 0.5):
                add_reason(ref, MatchReason("concept_name", f"mentions '{name}'", 1.0))
                break
        # fingerprint / lexical overlap of claims
        best_fp = 0.0
        for cts in signals.claim_token_sets:
            best_fp = max(best_fp, _jaccard(cts, claim_tokens))
        if best_fp >= fingerprint_threshold:
            add_reason(ref, MatchReason("fingerprint", f"claim overlap {best_fp:.2f}", best_fp))
        # prerequisite hints
        for hint, htoks in hint_tokensets.items():
            if htoks and _jaccard(htoks, claim_tokens | title_tokens) >= 0.4:
                add_reason(ref, MatchReason("prerequisite_hint", f"cited prerequisite '{hint}'", 0.6))
                break

    for concept_id, concept in vault.concepts.items():
        ref = f"concept:{concept_id}"
        title_tokens = _tokens((concept.title or "") + " " + " ".join(concept.aliases or []))
        for name, ntoks in name_tokensets.items():
            if ntoks and _jaccard(ntoks, title_tokens) >= 0.5:
                add_reason(ref, MatchReason("concept_name", f"matches concept '{name}'", 1.0))
                break

    # Provenance / source-scope always match (the appended source already touches
    # these entities): they are the highest-signal neighbors.
    for ref, reason in provenance_entities.items():
        add_reason(ref, reason)

    unresolved = _unresolved_candidates(signals, scored)
    rounds = 1
    if unresolved:
        rounds = 2
        # One additional bounded round: looser lexical pass for still-unmatched
        # concept mentions, so a differently-worded neighbor is not missed (§3.2).
        for facet_id, facet in vault.evidence_facets.items():
            ref = f"facet:{facet_id}"
            claim_tokens = _tokens(facet.claim or "") | _tokens(facet.title or "")
            for name in unresolved:
                ntoks = _tokens(name)
                if ntoks and _jaccard(ntoks, claim_tokens) >= loose_threshold:
                    add_reason(ref, MatchReason("concept_name", f"loose match '{name}'", loose_threshold))
                    break

    ordered = sorted(scored.items(), key=lambda kv: (-kv[1][0], kv[0]))
    return _materialize(vault, repository, ordered, budget_tokens=budget_tokens, rounds=rounds)


def _provenance_matched_entities(
    repository: Repository, signals: _NewSignals
) -> dict[str, MatchReason]:
    matched: dict[str, MatchReason] = {}
    for revision_id in sorted(signals.revision_ids):
        for link in repository.entity_source_links_for_revision(revision_id):
            ref = f"{link['entity_type']}:{link['entity_id']}"
            matched.setdefault(
                ref, MatchReason("provenance", f"already linked to revision {revision_id}", 2.0)
            )
    # source-scope: any link whose source_id is being appended.
    if signals.source_ids:
        for link in repository.entity_source_links_for_sources(sorted(signals.source_ids)):
            ref = f"{link['entity_type']}:{link['entity_id']}"
            matched.setdefault(
                ref, MatchReason("source_scope", f"linked to source {link['source_id']}", 1.5)
            )
    return matched


def _unresolved_candidates(
    signals: _NewSignals, scored: dict[str, tuple[float, list[MatchReason]]]
) -> list[str]:
    """Concept names in the new inventory that matched no existing entity yet."""

    if scored:
        return []  # a candidate is "unresolved" only when the whole first pass found nothing
    return sorted(signals.concept_names)


def _materialize(
    vault: LoadedVault,
    repository: Repository,
    ordered: list[tuple[str, tuple[float, list[MatchReason]]]],
    *,
    budget_tokens: int,
    rounds: int,
) -> Neighborhood:
    from learnloop.services.curriculum_locks import identity_locks

    locks = identity_locks(vault, repository)
    neighborhood = Neighborhood(budget_tokens=budget_tokens, rounds=rounds)
    used = 0
    included_facets: set[str] = set()
    included_concepts: set[str] = set()
    included_los: set[str] = set()

    for ref, (score, reasons) in ordered:
        kind, _, entity_id = ref.partition(":")
        payload: dict[str, Any] | None = None
        if kind == "facet":
            facet = vault.evidence_facets.get(entity_id)
            if facet is None:
                continue
            payload = _facet_contract(facet)
        elif kind == "concept":
            concept = vault.concepts.get(entity_id)
            if concept is None:
                continue
            payload = {
                "id": concept.id,
                "title": concept.title,
                "type": concept.type,
                "aliases": list(concept.aliases or []),
            }
        if payload is None:
            continue
        cost = _estimate_tokens(payload)
        if used + cost > budget_tokens and neighborhood.entity_hashes:
            neighborhood.capped = True
            break
        used += cost
        neighborhood.entity_hashes[ref] = _hash_entity(payload)
        neighborhood.match_reasons[ref] = [
            {"kind": r.kind, "detail": r.detail, "score": round(r.score, 3)} for r in reasons
        ]
        if kind == "facet":
            neighborhood.facets.append(payload)
            included_facets.add(entity_id)
            if facet.concept_id:
                included_concepts.add(facet.concept_id)
        elif kind == "concept":
            neighborhood.concepts.append(payload)
            included_concepts.add(entity_id)

    # Pull in the concepts, LOs, blueprints, recipes, criteria that anchor the
    # matched facets (bounded by what already matched — no fan-out).
    for concept_id in sorted(included_concepts):
        if any(c["id"] == concept_id for c in neighborhood.concepts):
            continue
        concept = vault.concepts.get(concept_id)
        if concept is None:
            continue
        neighborhood.concepts.append(
            {"id": concept.id, "title": concept.title, "type": concept.type, "aliases": list(concept.aliases or [])}
        )
        neighborhood.entity_hashes[f"concept:{concept_id}"] = _hash_entity({"id": concept.id})

    for lo_id, lo in sorted(vault.learning_objects.items()):
        if lo.concept not in included_concepts:
            continue
        included_los.add(lo_id)
        neighborhood.learning_objects.append(
            {
                "id": lo.id,
                "title": lo.title,
                "concept_id": lo.concept,
                "prerequisites": list(lo.prerequisites or []),
                "blueprint_ids": [bp.id for bp in (lo.blueprints or [])],
            }
        )
        for bp in lo.blueprints or []:
            recipe_refs: list[str] = []
            for recipe in bp.recipes or []:
                comps = [
                    {"facet": c.facet, "capability": c.capability}
                    for c in [*(recipe.all_of or []), *(recipe.any_of or [])]
                ]
                if recipe.integration is not None:
                    comps.append({"facet": recipe.integration.facet, "capability": recipe.integration.capability})
                neighborhood.recipes.append({"id": recipe.id, "blueprint_id": bp.id, "components": comps})
                recipe_refs.append(recipe.id)
            neighborhood.blueprints.append(
                {"id": bp.id, "learning_object_id": lo.id, "weight": bp.weight, "recipe_ids": recipe_refs}
            )

    # Criterion summaries: rubric criteria that target a matched facet.
    for pi in vault.practice_items.values():
        rubric = pi.grading_rubric
        if rubric is None:
            continue
        for criterion in rubric.criteria or []:
            targets = [t.facet for t in (criterion.targets or [])]
            if any(f in included_facets for f in targets):
                neighborhood.criterion_summaries.append(
                    {
                        "practice_item_id": pi.id,
                        "criterion_id": criterion.id,
                        "targets": [{"facet": t.facet, "capability": t.capability, "role": t.role} for t in criterion.targets or []],
                        "correlation_group": criterion.correlation_group,
                    }
                )

    # Notation, conflicts, provenance, lock reasons for the matched entities.
    for facet_id in sorted(included_facets):
        for mapping in repository.notation_mappings_for_entity("facet", facet_id):
            neighborhood.notation.append(
                {
                    "entity_id": facet_id,
                    "canonical": mapping["canonical_notation"],
                    "alternate": mapping["alternate_notation"],
                    "context": mapping.get("context"),
                    "status": mapping.get("status"),
                }
            )
        for conflict in repository.source_conflicts_for_entity("facet", facet_id):
            neighborhood.conflicts.append(
                {
                    "id": conflict["id"],
                    "entity_id": facet_id,
                    "statement": conflict["statement"],
                    "status": conflict["status"],
                }
            )
        for link in repository.entity_source_links("facet", facet_id):
            neighborhood.provenance.append(
                {
                    "entity_type": "facet",
                    "entity_id": facet_id,
                    "relation": link["relation"],
                    "revision_id": link.get("revision_id"),
                    "locator": link.get("locator"),
                    "status": link.get("status"),
                }
            )
        for reason in locks.get(facet_id, []):
            neighborhood.lock_reasons.append(
                {"facet_id": facet_id, "source": reason.source, "detail": reason.detail}
            )

    neighborhood.input_token_estimate = _estimate_tokens(neighborhood.as_context())
    if neighborhood.input_token_estimate > budget_tokens:
        neighborhood.capped = True
    return neighborhood


def _facet_contract(facet: Any) -> dict[str, Any]:
    return {
        "id": facet.id,
        "concept_id": facet.concept_id,
        "kind": facet.kind,
        "claim": facet.claim,
        "preconditions": list(facet.preconditions or []),
        "postconditions": list(facet.postconditions or []),
        "error_signatures": list(facet.error_signatures or []),
        "instructional_repairs": list(facet.instructional_repairs or []),
        "aliases": list(facet.aliases or []),
        "semantic_fingerprint": facet.semantic_fingerprint,
    }

"""Synthesis quality eval harness (ING M6, spec §14 / §15 M6).

Deterministic gates check structure and the sim harness checks evidence math;
this is the ONLY instrument that checks whether synthesis mints *good facets* —
the highest-leverage LLM judgment in the system. It scores a synthesized study
map against a hand-authored GOLD registry + blueprint set for one fixture
chapter, keyed per prompt version.

Metrics (all in [0, 1] unless a count):
- facet precision / recall — match on semantic fingerprint OR fuzzy claim;
- over-fragmentation rate — candidate facets that split one gold facet;
- duplicate rate — candidate facets duplicating another candidate;
- missing-conditions count — gold pre/postconditions absent on a matched facet;
- recipe validity — recipes whose referenced facets all resolve;
- criterion-target accuracy — candidate (facet, capability) targets that match
  a gold target after facet alignment;
- provenance accuracy — candidate facets with an in-scope, role-allowed span;
- repair-distinctness — do facets mapped to DIFFERENT gold facets carry
  different instructional repairs? (a synthesized distinction that implies no
  different repair is a false distinction).

Given a canned candidate the report is fully deterministic (tests). Live runs
feed the provider's synthesized map through the same extractor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.vault.facet_fingerprint import semantic_fingerprint
from learnloop.vault.models import LoadedVault

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SEMANTIC_ROLES = frozenset({"primary_textbook", "lecture", "paper", "reference", "alternate_explanation"})
_FUZZY_THRESHOLD = 0.6


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


@dataclass
class EvalReport:
    prompt_version: str
    subject: str
    gold_facet_count: int
    candidate_facet_count: int
    matched_facet_count: int
    facet_precision: float
    facet_recall: float
    over_fragmentation_rate: float
    duplicate_rate: float
    missing_conditions_count: int
    recipe_validity: float
    criterion_target_accuracy: float
    provenance_accuracy: float
    repair_distinctness: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "prompt_version": self.prompt_version,
            "subject": self.subject,
            "gold_facet_count": self.gold_facet_count,
            "candidate_facet_count": self.candidate_facet_count,
            "matched_facet_count": self.matched_facet_count,
            "facet_precision": round(self.facet_precision, 4),
            "facet_recall": round(self.facet_recall, 4),
            "over_fragmentation_rate": round(self.over_fragmentation_rate, 4),
            "duplicate_rate": round(self.duplicate_rate, 4),
            "missing_conditions_count": self.missing_conditions_count,
            "recipe_validity": round(self.recipe_validity, 4),
            "criterion_target_accuracy": round(self.criterion_target_accuracy, 4),
            "provenance_accuracy": round(self.provenance_accuracy, 4),
            "repair_distinctness": round(self.repair_distinctness, 4),
            "notes": list(self.notes),
        }

    def format_text(self) -> str:
        d = self.as_dict()
        lines = [
            f"synthesis-eval  subject={self.subject}  prompt_version={self.prompt_version}",
            f"  facets: gold={self.gold_facet_count} candidate={self.candidate_facet_count} matched={self.matched_facet_count}",
            f"  precision={d['facet_precision']}  recall={d['facet_recall']}",
            f"  over_fragmentation={d['over_fragmentation_rate']}  duplicate={d['duplicate_rate']}",
            f"  missing_conditions={d['missing_conditions_count']}  recipe_validity={d['recipe_validity']}",
            f"  criterion_target_accuracy={d['criterion_target_accuracy']}  provenance_accuracy={d['provenance_accuracy']}",
            f"  repair_distinctness={d['repair_distinctness']}",
        ]
        for note in self.notes:
            lines.append(f"  note: {note}")
        return "\n".join(lines)


def _fingerprint(facet: dict[str, Any]) -> str:
    fp = facet.get("semantic_fingerprint")
    if fp:
        return str(fp)
    return semantic_fingerprint(facet)


def _match_facets(candidate: list[dict[str, Any]], gold: list[dict[str, Any]]) -> dict[int, int]:
    """Greedy candidate-index -> gold-index alignment by fingerprint then fuzzy claim."""

    gold_fp = {_fingerprint(g): i for i, g in enumerate(gold)}
    gold_tokens = [_tokens(g.get("claim", "")) for g in gold]
    matches: dict[int, int] = {}
    used_gold: set[int] = set()
    # pass 1: exact fingerprint
    for ci, cand in enumerate(candidate):
        gi = gold_fp.get(_fingerprint(cand))
        if gi is not None and gi not in used_gold:
            matches[ci] = gi
            used_gold.add(gi)
    # pass 2: fuzzy claim for the rest
    for ci, cand in enumerate(candidate):
        if ci in matches:
            continue
        ct = _tokens(cand.get("claim", ""))
        best_gi, best_sim = None, _FUZZY_THRESHOLD
        for gi, gt in enumerate(gold_tokens):
            if gi in used_gold:
                continue
            sim = _jaccard(ct, gt)
            if sim >= best_sim:
                best_gi, best_sim = gi, sim
        if best_gi is not None:
            matches[ci] = best_gi
            used_gold.add(best_gi)
    return matches


def evaluate(gold: dict[str, Any], candidate: dict[str, Any]) -> EvalReport:
    gold_facets = gold.get("facets", []) or []
    cand_facets = candidate.get("facets", []) or []
    matches = _match_facets(cand_facets, gold_facets)

    matched = len(matches)
    precision = matched / len(cand_facets) if cand_facets else 0.0
    recall = matched / len(gold_facets) if gold_facets else 0.0

    # over-fragmentation: >1 candidate facet mapped to the same gold facet.
    gold_hits: dict[int, int] = {}
    for gi in matches.values():
        gold_hits[gi] = gold_hits.get(gi, 0) + 1
    fragmented = sum(count - 1 for count in gold_hits.values() if count > 1)
    over_fragmentation = fragmented / len(cand_facets) if cand_facets else 0.0

    # duplicate rate: candidate facets sharing a fingerprint with another candidate.
    fp_counts: dict[str, int] = {}
    for cand in cand_facets:
        fp_counts[_fingerprint(cand)] = fp_counts.get(_fingerprint(cand), 0) + 1
    duplicates = sum(count - 1 for count in fp_counts.values() if count > 1)
    duplicate_rate = duplicates / len(cand_facets) if cand_facets else 0.0

    # missing conditions on matched facets.
    missing_conditions = 0
    for ci, gi in matches.items():
        gold_conds = {str(c).strip().lower() for key in ("preconditions", "postconditions")
                      for c in (gold_facets[gi].get(key) or [])}
        cand_conds = {str(c).strip().lower() for key in ("preconditions", "postconditions")
                      for c in (cand_facets[ci].get(key) or [])}
        missing_conditions += len(gold_conds - cand_conds)

    # candidate facet id -> whether it matched a gold facet (for recipe/criterion checks)
    cand_ids = {str(f.get("id") or "") for f in cand_facets}

    # recipe validity: every referenced facet resolves to a candidate facet.
    recipes = candidate.get("recipes", []) or []
    valid_recipes = 0
    for recipe in recipes:
        facets = [str(x) for x in (recipe.get("facets") or [])]
        if facets and all(f in cand_ids for f in facets):
            valid_recipes += 1
    recipe_validity = valid_recipes / len(recipes) if recipes else 1.0

    # criterion-target accuracy: candidate (facet-claim, capability) matches a gold target.
    gold_targets = set()
    cand_claim_by_id = {str(f.get("id") or ""): _tokens(f.get("claim", "")) for f in cand_facets}
    gold_claim_by_id = {str(f.get("id") or ""): _tokens(f.get("claim", "")) for f in gold_facets}
    for target in gold.get("criterion_targets", []) or []:
        gold_targets.add((str(target.get("facet")), str(target.get("capability"))))
    cand_targets = candidate.get("criterion_targets", []) or []
    target_hits = 0
    for target in cand_targets:
        cap = str(target.get("capability"))
        cfacet = str(target.get("facet"))
        ctok = cand_claim_by_id.get(cfacet, _tokens(cfacet))
        ok = False
        for gfacet, gcap in gold_targets:
            if gcap != cap:
                continue
            gtok = gold_claim_by_id.get(gfacet, _tokens(gfacet))
            if gfacet == cfacet or _jaccard(ctok, gtok) >= _FUZZY_THRESHOLD:
                ok = True
                break
        target_hits += 1 if ok else 0
    criterion_target_accuracy = target_hits / len(cand_targets) if cand_targets else 1.0

    # provenance accuracy: matched facets carry an in-scope, role-allowed span.
    prov_ok = 0
    for cand in cand_facets:
        refs = cand.get("provenance") or []
        if isinstance(refs, dict):
            refs = refs.get("source_refs", [])
        if any(str(r.get("role")) in _SEMANTIC_ROLES and (r.get("span_id") or r.get("locator")) for r in refs):
            prov_ok += 1
    provenance_accuracy = prov_ok / len(cand_facets) if cand_facets else 0.0

    # repair-distinctness: facets mapped to DIFFERENT gold facets should differ in repairs.
    distinct_pairs = 0
    distinct_ok = 0
    matched_items = list(matches.items())
    for i in range(len(matched_items)):
        for j in range(i + 1, len(matched_items)):
            (ci, gi), (cj, gj) = matched_items[i], matched_items[j]
            if gi == gj:
                continue
            distinct_pairs += 1
            ri = {str(r).strip().lower() for r in (cand_facets[ci].get("instructional_repairs") or [])}
            rj = {str(r).strip().lower() for r in (cand_facets[cj].get("instructional_repairs") or [])}
            if ri != rj:
                distinct_ok += 1
    repair_distinctness = distinct_ok / distinct_pairs if distinct_pairs else 1.0

    notes: list[str] = []
    if over_fragmentation > 0:
        notes.append(f"{fragmented} candidate facet(s) over-fragment a gold facet")
    if duplicate_rate > 0:
        notes.append(f"{duplicates} duplicate candidate facet(s)")
    missing_gold = len(gold_facets) - len(set(matches.values()))
    if missing_gold > 0:
        notes.append(f"{missing_gold} gold facet(s) unmatched by any candidate")

    return EvalReport(
        prompt_version=str(candidate.get("prompt_version") or gold.get("prompt_version") or ""),
        subject=str(gold.get("subject") or ""),
        gold_facet_count=len(gold_facets),
        candidate_facet_count=len(cand_facets),
        matched_facet_count=matched,
        facet_precision=precision,
        facet_recall=recall,
        over_fragmentation_rate=over_fragmentation,
        duplicate_rate=duplicate_rate,
        missing_conditions_count=missing_conditions,
        recipe_validity=recipe_validity,
        criterion_target_accuracy=criterion_target_accuracy,
        provenance_accuracy=provenance_accuracy,
        repair_distinctness=repair_distinctness,
        notes=notes,
    )


def extract_candidate_from_vault(vault: LoadedVault, *, prompt_version: str = "") -> dict[str, Any]:
    """Build the eval candidate summary from an applied study map."""

    facets = []
    for facet in vault.evidence_facets.values():
        payload = facet.model_dump(mode="json") if hasattr(facet, "model_dump") else dict(facet)
        facets.append(payload)
    recipes: list[dict[str, Any]] = []
    criterion_targets: list[dict[str, Any]] = []
    for lo in vault.learning_objects.values():
        for blueprint in getattr(lo, "blueprints", []) or []:
            for recipe in blueprint.recipes:
                flat = [c.facet for c in (recipe.all_of + recipe.any_of)]
                if recipe.integration:
                    flat.append(recipe.integration.facet)
                recipes.append({"id": recipe.id, "facets": flat})
    for item in vault.practice_items.values():
        rubric = getattr(item, "grading_rubric", None)
        if rubric is None:
            continue
        for criterion in rubric.criteria:
            for target in criterion.targets:
                criterion_targets.append({"facet": target.facet, "capability": target.capability, "role": target.role})
    return {
        "prompt_version": prompt_version,
        "facets": facets,
        "recipes": recipes,
        "criterion_targets": criterion_targets,
    }


def load_gold(path: Path) -> dict[str, Any]:
    from learnloop.vault.yaml_io import read_yaml

    return read_yaml(path)


def default_gold_path() -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "synthesis_eval_gold" / "linear_algebra_symmetry.yaml"

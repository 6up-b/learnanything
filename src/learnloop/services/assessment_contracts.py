"""Immutable assessment-contract snapshots (knowledge-model §5.2).

Every presented item resolves to a content-addressed assessment contract that
freezes item/rubric content, criterion maxima, the dependency DAG, correlation
groups, facet x capability targets/roles, valid recipes, budgets, and the
evidence fingerprint. Grading (and replay) resolve historical attribution
against the stored snapshot, so mutating the live rubric after an attempt cannot
change what that attempt demonstrated.

This module is deterministic and writes no belief state. It is only exercised on
mvp-0.7 vaults; legacy (mvp-0.6) replay never calls it, keeping derived state
byte-identical.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from learnloop.clock import Clock
from learnloop.services.capability_mapping import compile_criterion_targets
from learnloop.services.grading import resolved_rubric
from learnloop.vault.models import LearningObject, LoadedVault, PracticeItem, Rubric, recipe_components

# Activation gate: the snapshot path only runs on vaults upgraded to the new
# knowledge model. Legacy vaults never compute or read snapshots.
KM_ALGORITHM_VERSION = "mvp-0.7"

CONTRACT_SCHEMA_VERSION = 1


def _content_hash(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def _blueprint_recipes(lo: LearningObject | None) -> list[dict[str, Any]]:
    if lo is None:
        return []
    recipes: list[dict[str, Any]] = []
    for blueprint in lo.blueprints:
        for recipe in blueprint.recipes:
            recipes.append(
                {
                    "blueprint_id": blueprint.id,
                    "recipe_id": recipe.id,
                    "composition": recipe.composition,
                    "components": [
                        {
                            "facet": component.facet,
                            "capability": component.capability,
                            "modality": component.modality,
                        }
                        for component in recipe_components(recipe)
                    ],
                }
            )
    return recipes


def compile_assessment_contract(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    rubric: Rubric | None = None,
) -> dict[str, Any]:
    """Deterministic assessment-contract content for an item (§5.2).

    Criterion targets are authored-or-compiled from the mode->capability defaults
    (capability_mapping), so legacy items still snapshot a capability-aware
    contract without belief writes.
    """

    resolved = rubric if rubric is not None else resolved_rubric(vault, item)
    lo = vault.learning_objects.get(item.learning_object_id)
    rubric_total = sum(criterion.points for criterion in resolved.criteria) or float(resolved.max_points)

    criteria: list[dict[str, Any]] = []
    for criterion in resolved.criteria:
        targets = compile_criterion_targets(item, criterion, resolved_rubric=resolved)
        criteria.append(
            {
                "id": criterion.id,
                "max_points": criterion.points,
                "tier": getattr(criterion, "tier", "core"),
                "depends_on": sorted(criterion.depends_on),
                "correlation_group": criterion.correlation_group,
                "recipe_ids": sorted(criterion.recipe_ids),
                "targets": [
                    {"facet": target.facet, "capability": target.capability, "role": target.role}
                    for target in targets
                ],
            }
        )

    fingerprint = getattr(item, "evidence_fingerprint", None)
    contract = {
        "practice_item_id": item.id,
        "learning_object_id": item.learning_object_id,
        "practice_mode": item.practice_mode,
        "item_content_hash": _content_hash(
            {"prompt": item.prompt, "expected_answer": item.expected_answer}
        ),
        "rubric_content_hash": _content_hash(resolved.model_dump(mode="json")),
        "rubric_total": rubric_total,
        "rubric_max_points": resolved.max_points,
        "criteria": criteria,
        "fatal_errors": [
            {"id": fatal.id, "max_grade": fatal.max_grade, "misconception_id": fatal.misconception_id}
            for fatal in resolved.fatal_errors
        ],
        "recipes": _blueprint_recipes(lo),
        "evidence_fingerprint": fingerprint if isinstance(fingerprint, dict) else None,
        "surface_family": item.surface_family,
        "assistance": {"max_useful_hints": item.hint_policy.max_useful_hints},
    }
    return contract


def contract_hash(contract: dict[str, Any]) -> str:
    """Content-addressed hash of a compiled contract (attribution-affecting only)."""

    return _content_hash(contract)


def snapshot_for_presentation(
    repository,
    vault: LoadedVault,
    item: PracticeItem,
    *,
    rubric: Rubric | None = None,
    clock: Clock | None = None,
) -> str:
    """Ensure an assessment-contract snapshot exists for a presented item (§5.2).

    Idempotent (content-addressed): identical item versions reuse one snapshot.
    Returns the snapshot version id.
    """

    contract = compile_assessment_contract(vault, item, rubric=rubric)
    digest = contract_hash(contract)
    return repository.ensure_assessment_contract_version(
        practice_item_id=item.id,
        contract_hash=digest,
        contract_json=json.dumps(contract, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        schema_version=CONTRACT_SCHEMA_VERSION,
        clock=clock,
    )

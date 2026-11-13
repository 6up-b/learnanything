"""Immutable synthesis manifests (source-ingestion §8.4, knowledge-model §12.4).

The manifest is the complete, immutable record of *why the curriculum changed*:
which revisions, assets, extractors and inventory rows (by id and content) a run
read, under which resolved brief, scope and role overrides, against which
curriculum (its concept edges included), facet and task snapshot, assessment
schema and learner-model contract, with which token budget. It is persisted
BEFORE model execution.

It is a record and nothing else. No run is looked up by it to be reused: a
rebuild runs the orchestration again, each paid call answering from its
checkpoint (keyed on the rendered request, ``ai/execution.request_key``), and a
proposal equal to an earlier one is that one (``proposal_match``). So a field
here costs nothing when it moves, and an input missing here makes the record
incomplete, never a reuse wrong.

``manifest_hash`` names the record (``synthesis_manifests`` is unique on it, and
``agent_runs.input_context_hash`` carries it, :func:`agent_run_input_context_hash`).
Records written before the manifest stopped being a reuse key keep their bytes
and are read as they are.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from pydantic import BaseModel

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.vault.models import (
    Blueprint,
    BlueprintRecipe,
    LoadedVault,
    RecipeComponent,
    learning_object_facet_union,
)

MANIFEST_SCHEMA_VERSION = 1

# Fields that participate in the manifest identity hash. `id`, `created_at`,
# `manifest_hash`, and the derived `estimated_usage` preview are excluded: the
# first three are assigned, the last is a non-authorizing preview.
_HASHED_FIELDS: tuple[str, ...] = (
    "source_set_id",
    "membership",
    "revision_ids",
    "asset_hashes",
    "extraction_ids",
    "unit_inventory_versions",
    "scope",
    "brief",
    "prompt_version",
    "schema_version",
    "provider",
    "model",
    "extractor_versions",
    "curriculum_snapshot_hash",
    "facet_registry_hash",
    "task_graph_hash",
    "assessment_schema_version",
    "learner_model_contract_version",
    "token_budget",
)


def _sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def content_hash(value: Any) -> str:
    """A stable hash of a JSON-shaped value (an inventory row's content, a revision diff)."""

    return _sha256(value)


def compute_manifest_hash(manifest: Mapping[str, Any]) -> str:
    """Deterministic hash over the identity-bearing manifest fields (§8.4)."""

    identity = {field: manifest.get(field) for field in _HASHED_FIELDS}
    return _sha256(identity)


def facet_registry_hash(vault: LoadedVault) -> str:
    """Stable hash of the canonical facet registry (§12.4).

    Keyed on id + semantic fingerprint + version + status, so the record shows any
    registry change that could alter synthesis meaning.
    """

    entries = []
    for facet_id in sorted(vault.evidence_facets):
        facet = vault.evidence_facets[facet_id]
        entries.append(
            {
                "id": facet_id,
                "fingerprint": getattr(facet, "semantic_fingerprint", None),
                "version": getattr(facet, "version", None),
                "status": getattr(facet, "status", None),
            }
        )
    return _sha256({"facets": entries, "aliases": dict(sorted(vault.facet_aliases.items()))})


def curriculum_snapshot_hash(vault: LoadedVault) -> str:
    """Stable hash of the concept/LO curriculum snapshot (§12.4), with the concept
    edges as the structuring pass shows them to the model (source, target, relation)."""

    concepts = sorted(vault.concepts)
    learning_objects = []
    for lo_id in sorted(vault.learning_objects):
        lo = vault.learning_objects[lo_id]
        learning_objects.append(
            {
                "id": lo_id,
                "concept": lo.concept,
                "status": lo.status,
                "prerequisites": sorted(lo.prerequisites),
                "facets": sorted(learning_object_facet_union(lo)),
            }
        )
    edges = sorted([edge.source, edge.target, edge.relation_type] for edge in vault.edges)
    return _sha256({"concepts": concepts, "learning_objects": learning_objects, "edges": edges})


#: The blueprint fields :func:`task_graph_hash` reads, by model: every field each had when the hash was first
#: recorded, so a field added later stays out of the record until it is named here on purpose, and a named field
#: removed fails loudly instead of moving the hash (``tests/test_identity_pins.py``).
_BLUEPRINT_IDENTITY_FIELDS: dict[type[BaseModel], tuple[str, ...]] = {
    Blueprint: ("id", "weight", "recipes"),
    BlueprintRecipe: ("id", "composition", "all_of", "any_of", "integration"),
    RecipeComponent: ("facet", "capability", "modality"),
}


def _blueprint_identity(value: Any) -> Any:
    """``model_dump(mode="json", exclude_none=True)`` of a blueprint, through the named fields only.

    Keys the vault's YAML wrote that no model declares (vault models keep them) are what the owner authored, so
    they stay in, dumped exactly as before."""

    if isinstance(value, list):
        return [_blueprint_identity(child) for child in value]
    if not isinstance(value, BaseModel):
        return value
    out = {name: _blueprint_identity(child) for name in _BLUEPRINT_IDENTITY_FIELDS[type(value)]
           if (child := getattr(value, name)) is not None}
    if value.model_extra:
        out.update(value.model_dump(mode="json", exclude_none=True, include=set(value.model_extra)))
    return out


def task_graph_hash(vault: LoadedVault) -> str:
    """Stable hash of the task graph — blueprints/recipes and item task shape (§12.4)."""

    learning_objects = []
    for lo_id in sorted(vault.learning_objects):
        lo = vault.learning_objects[lo_id]
        blueprints = [_blueprint_identity(bp) for bp in getattr(lo, "blueprints", []) or []]
        learning_objects.append({"id": lo_id, "blueprints": blueprints})
    items = []
    for item_id in sorted(vault.practice_items):
        item = vault.practice_items[item_id]
        items.append(
            {
                "id": item_id,
                "learning_object_id": item.learning_object_id,
                "evidence_facets": sorted(item.evidence_facets),
            }
        )
    return _sha256({"learning_objects": learning_objects, "practice_items": items})


def learner_model_contract_version(vault: LoadedVault) -> str:
    """The learner-model contract version — the vault-global algorithm_version
    (§12.4)."""

    return vault.config.algorithms.algorithm_version


def build_manifest(
    vault: LoadedVault,
    *,
    source_set_id: str | None = None,
    membership: Any = None,
    revision_ids: Any = None,
    asset_hashes: Any = None,
    extraction_ids: Any = None,
    unit_inventory_versions: Any = None,
    scope: Any = None,
    brief: Any = None,
    prompt_version: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    extractor_versions: Any = None,
    assessment_schema_version: str | None = None,
    token_budget: Any = None,
    estimated_usage: Any = None,
    schema_version: int = MANIFEST_SCHEMA_VERSION,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Build the complete synthesis manifest with the derived completeness hashes.

    The caller supplies the source-side inputs (membership, revisions, scope,
    brief, budget); the curriculum/facet/task snapshot hashes and the
    learner-model contract version are derived from ``vault`` so they always
    describe the state synthesis actually ran against.
    """

    manifest: dict[str, Any] = {
        "source_set_id": source_set_id,
        "membership": membership,
        "revision_ids": revision_ids,
        "asset_hashes": asset_hashes,
        "extraction_ids": extraction_ids,
        "unit_inventory_versions": unit_inventory_versions,
        "scope": scope,
        "brief": brief,
        "prompt_version": prompt_version,
        "schema_version": schema_version,
        "provider": provider,
        "model": model,
        "extractor_versions": extractor_versions,
        "curriculum_snapshot_hash": curriculum_snapshot_hash(vault),
        "facet_registry_hash": facet_registry_hash(vault),
        "task_graph_hash": task_graph_hash(vault),
        "assessment_schema_version": assessment_schema_version,
        "learner_model_contract_version": learner_model_contract_version(vault),
        "token_budget": token_budget,
        "estimated_usage": estimated_usage,
        "created_at": utc_now_iso(clock),
    }
    manifest["manifest_hash"] = compute_manifest_hash(manifest)
    return manifest


def persist_manifest(repository: Repository, manifest: Mapping[str, Any]) -> str:
    """Persist an immutable manifest before model execution (idempotent on hash)."""

    return repository.insert_synthesis_manifest(manifest)


def agent_run_input_context_hash(manifest: Mapping[str, Any]) -> str:
    """What a synthesis agent run records as its ``input_context_hash``: the hash of
    the manifest it read. A record; no synthesis looks a run up by it."""

    return str(manifest["manifest_hash"])

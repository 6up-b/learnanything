"""Immutable synthesis manifests (source-ingestion §8.4, knowledge-model §12.4).

The manifest is the complete, immutable record of *why the curriculum changed*:
which revisions/assets/units, under which brief and scope, against which
curriculum/facet/task snapshot, assessment schema, and learner-model contract,
with which token budget. It is persisted BEFORE model execution.

``manifest_hash`` is deterministic over every identity-bearing input, so an
identical manifest reuses the completed agent run and any changed input mints a
new manifest/run. This hash IS the cache seam:

    agent_runs.input_context_hash = manifest_hash          (§8.4)

Use :func:`agent_run_input_context_hash` when creating the agent run so the seam
is explicit and never diverges. A lock fingerprint alone is insufficient for
append (output depends on existing-map content), which is exactly why the
completeness hashes (§12.4) are part of the manifest identity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault, learning_object_facet_union

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
    "lock_fingerprint",
    "token_budget",
)


def _sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compute_manifest_hash(manifest: Mapping[str, Any]) -> str:
    """Deterministic hash over the identity-bearing manifest fields (§8.4)."""

    identity = {field: manifest.get(field) for field in _HASHED_FIELDS}
    return _sha256(identity)


def facet_registry_hash(vault: LoadedVault) -> str:
    """Stable hash of the canonical facet registry (§12.4).

    Keyed on id + semantic fingerprint + version + status so any registry change
    that could alter synthesis meaning invalidates cached synthesis.
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
    """Stable hash of the concept/LO curriculum snapshot (§12.4)."""

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
    return _sha256({"concepts": concepts, "learning_objects": learning_objects})


def task_graph_hash(vault: LoadedVault) -> str:
    """Stable hash of the task graph — blueprints/recipes and item task shape (§12.4)."""

    learning_objects = []
    for lo_id in sorted(vault.learning_objects):
        lo = vault.learning_objects[lo_id]
        blueprints = [
            bp.model_dump(mode="json", exclude_none=True)
            for bp in getattr(lo, "blueprints", []) or []
        ]
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
    (§12.4). Cached synthesis is never reused across a contract change."""

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
    lock_fingerprint: str | None = None,
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
        "lock_fingerprint": lock_fingerprint,
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
    """The documented cache seam: ``agent_runs.input_context_hash = manifest_hash``.

    Always set an agent run's ``input_context_hash`` to this value when the run is
    a synthesis pass, so identical manifests hit the completed-run cache.
    """

    return str(manifest["manifest_hash"])

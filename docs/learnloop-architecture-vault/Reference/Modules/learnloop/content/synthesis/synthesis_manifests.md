---
title: "learnloop.content.synthesis.synthesis_manifests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/synthesis_manifests.py"
source_paths:
  - "src/learnloop/content/synthesis/synthesis_manifests.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.synthesis_manifests module"
  - "src/learnloop/content/synthesis/synthesis_manifests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.synthesis_manifests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.synthesis_manifests` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Immutable synthesis manifests (source-ingestion §8.4, knowledge-model §12.4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/synthesis_manifests.py](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `compute_manifest_hash(manifest: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 64) — Deterministic hash over the identity-bearing manifest fields (§8.4).
- `facet_registry_hash(vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 71) — Stable hash of the canonical facet registry (§12.4).
- `curriculum_snapshot_hash(vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 92) — Stable hash of the concept/LO curriculum snapshot (§12.4).
- `task_graph_hash(vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 111) — Stable hash of the task graph — blueprints/recipes and item task shape (§12.4).
- `learner_model_contract_version(vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 135) — The learner-model contract version — the vault-global algorithm_version (§12.4).
- `build_manifest(vault: LoadedVault, *, source_set_id: str | None=None, membership: Any=None, revision_ids: Any=None, asset_hashes: Any=None, extraction_ids: Any=None, unit_inventory_versions: Any=None, scope: Any=None, brief: Any=None, prompt_version: str | None=None, provider: str | None=None, model: str | None=None, extractor_versions: Any=None, assessment_schema_version: str | None=None, lock_fingerprint: str | None=None, token_budget: Any=None, estimated_usage: Any=None, schema_version: int=MANIFEST_SCHEMA_VERSION, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 142) — Build the complete synthesis manifest with the derived completeness hashes.
- `persist_manifest(repository: Repository, manifest: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 200) — Persist an immutable manifest before model execution (idempotent on hash).
- `agent_run_input_context_hash(manifest: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 206) — The documented cache seam: ``agent_runs.input_context_hash = manifest_hash``.

### Module constants

- `MANIFEST_SCHEMA_VERSION` ([src/learnloop/content/synthesis/synthesis_manifests.py](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 30)
- `_HASHED_FIELDS` ([src/learnloop/content/synthesis/synthesis_manifests.py](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 35)

## Internal implementation anchors

- `_sha256(payload: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py), line 59)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`; statically calls `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`; statically calls `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_synthesis_manifests.py](../../../../../../../tests/test_synthesis_manifests.py) — direct import
  - `test_persist_manifest_is_idempotent_and_seam_documented`
- [tests/test_synthesis_runs_repo.py](../../../../../../../tests/test_synthesis_runs_repo.py) — direct import
  - `test_finalize_stale_synthesis_runs_spares_recent_rows`
  - `test_synthesis_run_introducing_entity_lineage`
  - `test_synthesis_run_lifecycle`

## Modification guidance

- Change synthesis manifests policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/synthesis_manifests.py](../../../../../../../src/learnloop/content/synthesis/synthesis_manifests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

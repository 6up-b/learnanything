---
title: "learnloop.content.sources.source_deletion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_deletion.py"
source_paths:
  - "src/learnloop/content/sources/source_deletion.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.source_deletion module"
  - "src/learnloop/content/sources/source_deletion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.source_deletion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_deletion` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Delete an imported source and everything derived from it (§4.1).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_deletion.py](../../../../../../../src/learnloop/content/sources/source_deletion.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SourceDeletionError(ValueError)` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 33) — Deletion refused.
  - `__init__(self, code: str, message: str, *, details: dict[str, Any] | None=None) -> None` (line 36; internal)
- `class CollectionImpact` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 43)
  - `as_dict(self) -> dict[str, Any]` (line 52; public)
- `class SourceDeletionPlan` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 62)
  - `deletable(self) -> bool` (line 83; public)
  - `as_dict(self) -> dict[str, Any]` (line 86; public)
- `class SourceDeletionResult` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 106)
  - `as_dict(self) -> dict[str, Any]` (line 113; public)
- `plan_source_deletion(vault, repo: Repository, source_id: str) -> SourceDeletionPlan` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 211) — Report what deleting ``source_id`` would remove, cost, and currently block.
- `delete_source(vault, repo: Repository, source_id: str, *, vault_root: Path | None=None, clock: Clock | None=None) -> SourceDeletionResult` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 264) — Delete the source: SQLite cascade, collection membership, stored bytes.

### Module constants

- `_CITED_ENTITY_LIMIT` ([src/learnloop/content/sources/source_deletion.py](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 125)

## Internal implementation anchors

- `_artifact_or_error(repo: Repository, source_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 128)
- `_display_title(artifact: dict[str, Any], revisions: list[dict[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 135) — Same fallback chain the Source library uses, so the confirmation dialog names the source exactly as the row the learner clicked.
- `_active_job_blockers(repo: Repository, *, canonical_uri: str | None, revision_ids: set[str], extraction_ids: set[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 149) — Jobs still running against this source, matched on their payload.
- `_collections_for_source(vault, source_id: str) -> list[CollectionImpact]` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 172)
- `_shared_asset_hashes(repo: Repository, source_id: str, revisions: list[dict[str, Any]]) -> set[str]` ([source](../../../../../../../src/learnloop/content/sources/source_deletion.py), line 190) — Asset hashes of this source's revisions that another source also stores.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SourceDeletionError`, `delete_source`, `plan_source_deletion`; statically calls `delete_source`, `plan_source_deletion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `canonical_source_raw_path`; calls `canonical_source_raw_path`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_deletion.py](../../../../../../../tests/test_source_deletion.py) — direct import
  - `test_delete_detaches_learner_records_instead_of_destroying_them`
  - `test_delete_drops_the_source_from_its_collections`
  - `test_delete_is_refused_while_an_ingest_job_is_active`
  - `test_delete_keeps_stored_bytes_another_source_still_shares`
  - `test_delete_removes_every_derived_row_and_leaves_other_sources_intact`
  - `test_plan_rejects_an_unknown_source`
  - `test_plan_reports_study_map_citations_without_deleting`

## Modification guidance

- Change source deletion policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_deletion.py](../../../../../../../src/learnloop/content/sources/source_deletion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

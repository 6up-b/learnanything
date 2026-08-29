---
title: "learnloop.ops.maintenance_feed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/maintenance_feed.py"
source_paths:
  - "src/learnloop/ops/maintenance_feed.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.maintenance_feed module"
  - "src/learnloop/ops/maintenance_feed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.maintenance_feed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.maintenance_feed` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Maintenance feed (source-ingestion §11).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py) |
| Source lines | 368 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class NoticeType` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 34)
- `generate_maintenance_feed(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 79) — Regenerate the feed deterministically; return the live notices (§11).
- `dismiss_notice(repository: Repository, notice_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 341)
- `snooze_notice(repository: Repository, notice_id: str, *, until: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 345) — Snooze a notice; escalation-policy notices raise severity after N snoozes.

### Module constants

- `ESCALATION_SNOOZE_THRESHOLD` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 30)
- `NOTICE_TYPES` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 41)
- `_COLLECTORS` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 326)

## Internal implementation anchors

- `class _Notice` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 68)
- `_collect(vault: LoadedVault, repository: Repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 135)
- `_stale_link_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 142)
- `_open_conflict_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 167)
- `_partial_append_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 183)
- `_lo_without_practice_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 197)
- `_taught_blueprint_without_assessment_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 219) — A taught blueprint with no assessment_alignment provenance (§11).
- `_source_outcome_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 238) — Provenance-outcome associations as additive suggestions (§11, ING M8).
- `_graph_edit_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 266) — Graph-editor notices (§8/§12): ambiguous edge direction + queued restructure-intent for locked facets.
- `_probe_pool_empty_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 296) — Empty diagnostic-probe pools (owner decision: never silent).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; statically calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; statically calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `analyze_source_outcomes`, `source_outcome_notices`; calls `analyze_source_outcomes`, `source_outcome_notices`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `ambiguous_edge_direction_notices`, `restructure_request_notices`; calls `ambiguous_edge_direction_notices`, `restructure_request_notices`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`; calls `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_ambiguous_edge_direction_notice_carries_evidence`
  - `test_ambiguous_edge_direction_omits_sparse_evidence`
  - `test_queue_restructure_request_records_and_surfaces_in_feed`
  - `test_resolve_edge_direction_flip_files_proposal_and_resolves_notice`
  - `test_resolve_edge_direction_keep_resolves_without_filing`
  - `test_resolve_edge_direction_retire_removes_and_can_restore`
- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — direct import
  - `test_dismiss_and_snooze_do_not_change_curriculum`
  - `test_maintenance_notice_aging_policies`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_maintenance_feed_sustains_and_auto_resolves_the_notice`
- [tests/test_source_outcome_analytics.py](../../../../../../tests/test_source_outcome_analytics.py) — direct import
  - `test_actionable_associations_flow_into_maintenance_feed`

## Modification guidance

- Make changes here when the responsibility remains maintenance feed within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

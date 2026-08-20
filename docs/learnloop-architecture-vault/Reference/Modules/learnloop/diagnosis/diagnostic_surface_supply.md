---
title: "learnloop.diagnosis.diagnostic_surface_supply"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/diagnostic_surface_supply.py"
source_paths:
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.diagnostic_surface_supply module"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.diagnostic_surface_supply`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.diagnostic_surface_supply` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Replenish diagnostic-probe surface supply after consumption.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/diagnostic_surface_supply.py](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py) |
| Source lines | 456 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `reconcile_diagnostic_surface_needs(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 67) — Enqueue needs for consumed diagnostic surfaces; resolve satisfied ones.
- `class EmptyPoolCondition` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 138) — One learning object whose diagnostic surface pool is currently empty.
- `probe_pool_empty_conditions(vault: LoadedVault, repository: Repository) -> list[EmptyPoolCondition]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 155) — Learning objects whose eligible diagnostic pool is empty right now.
- `probe_pool_empty_notice_payload(vault: LoadedVault, condition: EmptyPoolCondition) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 259) — The one notice shape both writers use (sweep upsert + feed collector).
- `authoring_provider_available(vault: LoadedVault) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 305) — The routed authoring provider when its runtime is ready, else None.
- `reconcile_empty_probe_pools(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, provider_available: bool | None=None, ai_client: object | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 324) — Detect empty pools; queue generation (provider-gated); raise/clear notices.

### Module constants

- `DIAGNOSTIC_SURFACE_CAPABILITY` ([src/learnloop/diagnosis/diagnostic_surface_supply.py](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 40)
- `PROBE_POOL_EMPTY_NOTICE_TYPE` ([src/learnloop/diagnosis/diagnostic_surface_supply.py](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 48)
- `EMPTY_POOL_REASONS` ([src/learnloop/diagnosis/diagnostic_surface_supply.py](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 54)

## Internal implementation anchors

- `_facet_target_key(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 57)
- `_misconception_ids(vault: LoadedVault, item: PracticeItem) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 62)
- `_queue_episode_generation_need(vault: LoadedVault, repository: Repository, episode_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py), line 425) — Ensure the starved episode has one pending generation need.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`; statically calls `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`; statically calls `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`; calls `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `mint_single_use_probe_surface`; calls `mint_single_use_probe_surface`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; calls `discriminates`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_a_fresh_replacement_surface_resolves_the_pending_need`
  - `test_consuming_a_diagnostic_administration_enqueues_one_deduplicated_need`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_empty_pool_raises_exactly_one_urgent_deduplicated_notice`
  - `test_maintenance_feed_sustains_and_auto_resolves_the_notice`
  - `test_never_authored_pool_is_distinguished_from_excluded_as_seen`
  - `test_no_provider_skips_queueing_but_still_raises_the_notice`
  - `test_notice_clears_when_a_fresh_surface_appears`
  - `test_pending_diagnostic_need_with_no_fresh_surface_raises_and_clears`
  - `test_pending_items_episode_with_fresh_surfaces_is_not_an_empty_pool`
  - `test_provider_routed_queues_one_deduplicated_generation_need`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_does_not_resolve_the_diagnostic_supply_need`

## Modification guidance

- Change diagnostic surface supply policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/diagnostic_surface_supply.py](../../../../../../src/learnloop/diagnosis/diagnostic_surface_supply.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

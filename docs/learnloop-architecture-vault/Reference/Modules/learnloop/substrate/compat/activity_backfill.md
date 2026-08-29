---
title: "learnloop.substrate.compat.activity_backfill"
type: "module-reference"
status: "current"
refactor_status: "COMPAT"
version: "1.0.0"
source_path: "src/learnloop/substrate/compat/activity_backfill.py"
source_paths:
  - "src/learnloop/substrate/compat/activity_backfill.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate.compat"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.compat.activity_backfill module"
  - "src/learnloop/substrate/compat/activity_backfill.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/compat"
  - "layer/domain"
  - "package/learnloop-substrate-compat"
---

# `learnloop.substrate.compat.activity_backfill`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.compat.activity_backfill` exists within [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] to own the behavior summarized by its module contract: Deterministic, idempotent backfill of the activity lineage substrate (§7.1).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/compat/activity_backfill.py](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py) |
| Source lines | 387 |
| Owning package | [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] |
| Architecture layer | `domain` |
| Refactor status | `COMPAT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Frozen compatibility boundary
> This live module is retained for old vaults. It is green but not a target for new feature growth.

## Public API

- `class BackfillReport` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 46)
  - `as_dict(self) -> dict[str, Any]` (line 60; public)
- `backfill_activity_substrate(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> BackfillReport` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 84) — Backfill migration-065 tables from the vault + legacy SQL (§7.1 steps 1-4).

## Internal implementation anchors

- `_purpose_for_attempt_type(attempt_type: str) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 69)
- `_clock_at(iso: str | None) -> Clock` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 77)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `backfill_activity_substrate`; statically calls `backfill_activity_substrate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`; calls `FrozenClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`; calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `_CONSUMING_PURPOSES`, `_PURPOSE_TO_LEGACY_KIND`, `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`; calls `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_backfill.py](../../../../../../../tests/test_activity_backfill.py) — direct import
  - `test_backfill_is_idempotent_on_fixture_copy`
  - `test_backfill_logs_attempt_duration_interaction_events`
  - `test_backfill_marks_unverifiable_for_missing_item`
  - `test_backfill_populates_substrate_from_fixture`
  - `test_backfill_render_once_per_shared_surface`
  - `test_diagnostic_probe_attempts_reuse_shared_surface_hash`
- [tests/test_grade_resolution_pipeline.py](../../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_backfill_converts_probe_presentations_idempotently`

## Modification guidance

- Change activity backfill policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/compat/activity_backfill.py](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

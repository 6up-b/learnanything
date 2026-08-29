---
title: "learnloop.attempts.measurement_corrections"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/measurement_corrections.py"
source_paths:
  - "src/learnloop/attempts/measurement_corrections.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.measurement_corrections module"
  - "src/learnloop/attempts/measurement_corrections.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.measurement_corrections`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.measurement_corrections` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Append-only authoring corrections for attempted assessment contracts (§5.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/measurement_corrections.py](../../../../../../src/learnloop/attempts/measurement_corrections.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MeasurementCorrectionError(ValueError)` ([source](../../../../../../src/learnloop/attempts/measurement_corrections.py), line 29) — The requested change cannot be represented as an honest correction.
- `class MeasurementCorrectionResult` ([source](../../../../../../src/learnloop/attempts/measurement_corrections.py), line 34)
- `create_measurement_correction(root: Path, repository: Repository, *, source_practice_item_id: str, corrected_fields: Mapping[str, Any], reason: str, consuming_projection_version: str, reinterpret_historical_evidence: bool=False, corrected_practice_item_id: str | None=None, clock: Clock | None=None) -> MeasurementCorrectionResult` ([source](../../../../../../src/learnloop/attempts/measurement_corrections.py), line 104) — Mint a corrected item/version and append projection-versioned receipts.

## Internal implementation anchors

- `_criterion_signature(contract: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/measurement_corrections.py), line 46)
- `_assert_reinterpretable(source_contract: Mapping[str, Any], corrected_contract: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/attempts/measurement_corrections.py), line 53) — Ensure the correction changes measurement, not the historical task.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `create_measurement_correction`; statically calls `create_measurement_correction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`, `snapshot_for_presentation`; calls `compile_assessment_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `PracticeItem`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_measurement_corrections.py](../../../../../../tests/test_measurement_corrections.py) — direct import
  - `test_attempted_item_correction_is_append_only_and_projection_versioned`
  - `test_historical_reinterpretation_rejects_a_changed_task`

## Modification guidance

- Change measurement corrections policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/measurement_corrections.py](../../../../../../src/learnloop/attempts/measurement_corrections.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

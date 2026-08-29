---
title: "learnloop.diagnosis.probe_outcome_mapping"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_outcome_mapping.py"
source_paths:
  - "src/learnloop/diagnosis/probe_outcome_mapping.py"
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
  - "learnloop.diagnosis.probe_outcome_mapping module"
  - "src/learnloop/diagnosis/probe_outcome_mapping.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_outcome_mapping`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_outcome_mapping` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Versioned probe-outcome -> coarse-class mapping (spec_p0_measurement_correctness §3.1 + Change log 2026-07-18 entry (a)).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_outcome_mapping.py](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py) |
| Source lines | 178 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `coarse_schema_slug(instrument: CompiledInstrument) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 72) — The card-declared coarse outcome schema this instrument maps onto (§3.1).
- `coarse_class_for_outcome(instrument: CompiledInstrument, outcome: str, *, schema_true_classes: Mapping[str, object] | tuple[str, ...] | frozenset[str] | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 100) — Deterministically coarsen one fine probe outcome (§3.1).
- `probe_outcome_mapping(instrument: CompiledInstrument) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 120) — The full deterministic fine-outcome -> coarse-class table for this card.
- `mapping_snapshot(instrument: CompiledInstrument) -> dict[str, object]` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 142) — The administration-snapshotted mapping identity (deliverable 1).
- `coarse_instrument_rows(instrument: CompiledInstrument, slot_map: Mapping[str, str], schema_true_classes: tuple[str, ...]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 156) — Aggregate the fine ``P(fine_outcome | H_slot)`` instrument rows into coarse ``P(Z_coarse | H_label)`` rows over the schema's true classes (§4.2 P(Z|H,card)).

### Module constants

- `PROBE_COARSE_MAPPING_VERSION` ([src/learnloop/diagnosis/probe_outcome_mapping.py](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 36)
- `_CORRECT_OUTCOMES` ([src/learnloop/diagnosis/probe_outcome_mapping.py](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 41)
- `_PARTIAL_OUTCOMES` ([src/learnloop/diagnosis/probe_outcome_mapping.py](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 56)

## Internal implementation anchors

- `_base_coarse_class(instrument: CompiledInstrument, outcome: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`; statically calls `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `PROBE_COARSE_MAPPING_VERSION`, `coarse_class_for_outcome`, `coarse_instrument_rows`; statically calls `coarse_class_for_outcome`, `coarse_instrument_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`, `COARSE_RESPONSE_UNANSWERED_SLUG`, `SIGNATURE_ERROR_SLUG`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_administration_snapshots_probe_coarse_mapping`
  - `test_episode_pins_channel_and_products_are_deterministic`
  - `test_probe_outcome_mapping_is_deterministic_and_versioned`

## Modification guidance

- Change probe outcome mapping policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_outcome_mapping.py](../../../../../../src/learnloop/diagnosis/probe_outcome_mapping.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

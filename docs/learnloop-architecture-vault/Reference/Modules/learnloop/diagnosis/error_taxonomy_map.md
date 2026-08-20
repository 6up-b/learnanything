---
title: "learnloop.diagnosis.error_taxonomy_map"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/error_taxonomy_map.py"
source_paths:
  - "src/learnloop/diagnosis/error_taxonomy_map.py"
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
  - "learnloop.diagnosis.error_taxonomy_map module"
  - "src/learnloop/diagnosis/error_taxonomy_map.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.error_taxonomy_map`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.error_taxonomy_map` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Stable mechanism taxonomy and the single legacy → canonical error-type map.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py) |
| Source lines | 266 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `map_legacy_error_type(error_type: str | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 118) — Resolve any legacy error-type name onto the canonical mechanism space.
- `project_mechanism(*, declared: str | None=None, error_type: str | None=None) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 154) — Project a free-text candidate cause onto the mechanism space, post hoc.

### Module constants

- `MECHANISM_TAXONOMY` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 49)
- `MECHANISM_TAXONOMY_SET` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 61)
- `ASSESSMENT_SIDE_ERROR_TYPES` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 67)
- `MECHANISM_IS_MISCONCEPTION` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 72)
- `MECHANISM_SEVERITY_DEFAULT` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 85)
- `LEGACY_ERROR_TYPE_MAP` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 99)
- `MISCONCEPTION_CLASS_MECHANISMS` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 140)
- `MECHANISM_PROJECTION_OPEN_SET` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 151)
- `MECHANISM_TAXONOMY_CARD` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 192)
- `MECHANISM_TAXONOMY_CARD_JSON` ([src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py), line 259)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `MECHANISM_SEVERITY_DEFAULT`, `MECHANISM_TAXONOMY_CARD_JSON`, `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `MECHANISM_PROJECTION_OPEN_SET`, `map_legacy_error_type`, `project_mechanism`; statically calls `map_legacy_error_type`, `project_mechanism`
- [[Reference/Modules/learnloop/diagnosis/causal_migration|learnloop.diagnosis.causal_migration]] — imports `MECHANISM_TAXONOMY_SET`, `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `MECHANISM_IS_MISCONCEPTION`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `map_legacy_error_type`; statically calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; statically calls `map_legacy_error_type`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/diagnosis/causal_migration|learnloop.diagnosis.causal_migration]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_mechanism_projection_prefers_the_model_label_then_falls_open_set`
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_resolves_legacy_error_event_through_causal_taxonomy`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_arithmetic_slip_and_scaffold_failure_mapping_decision`
  - `test_legacy_error_types_map_per_spec`
  - `test_mvp07_grader_taxonomy_emits_mechanism_vocabulary`
  - `test_retrieval_boundary_is_mechanism_based_and_domain_neutral`

## Modification guidance

- Change error taxonomy map policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/error_taxonomy_map.py](../../../../../../src/learnloop/diagnosis/error_taxonomy_map.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.diagnosis.gate_fit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/gate_fit.py"
source_paths:
  - "src/learnloop/diagnosis/gate_fit.py"
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
  - "learnloop.diagnosis.gate_fit module"
  - "src/learnloop/diagnosis/gate_fit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.gate_fit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.gate_fit` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Offline follow-up gate fitting from override + usefulness labels.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/gate_fit.py](../../../../../../src/learnloop/diagnosis/gate_fit.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GateExample` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 30)
- `class GateFitResult` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 39)
- `class GateFitError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 52) — Raised when the label stream cannot support a fit.
- `assemble_gate_training_set(repository: Repository, config: LearnLoopConfig) -> list[GateExample]` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 56)
- `fit_gate_weights(examples: list[GateExample], *, l2: float=0.1, epochs: int=500, learning_rate: float=0.5) -> GateFitResult` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 98)

### Module constants

- `_UNINFORMATIVE_SILENT_REASONS` ([src/learnloop/diagnosis/gate_fit.py](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 23)
- `_SILENT_NEGATIVE_WEIGHT` ([src/learnloop/diagnosis/gate_fit.py](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 24)
- `STRONG_LABEL_SOURCES` ([src/learnloop/diagnosis/gate_fit.py](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 26)

## Internal implementation anchors

- `_rank_auc(predictions: list[tuple[float, GateExample]]) -> float` ([source](../../../../../../src/learnloop/diagnosis/gate_fit.py), line 166) — Exact Mann-Whitney AUC with midrank tie handling.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `GateFitError`, `assemble_gate_training_set`, `fit_gate_weights`; statically calls `assemble_gate_training_set`, `fit_gate_weights`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `GATE_FEATURES`, `GATE_FEATURE_VERSION`, `subscores_from_diagnostics`; calls `subscores_from_diagnostics`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `sigmoid`; calls `sigmoid`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_gate_fit.py](../../../../../../tests/test_gate_fit.py) — direct import
  - `test_auc_handles_ties`
  - `test_fitter_recovers_separating_weights`
  - `test_fitter_requires_both_classes`
  - `test_l2_shrinks_weights`
  - `test_label_assembly`
  - `test_label_assembly_excludes_old_feature_semantics`

## Modification guidance

- Change gate fit policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/gate_fit.py](../../../../../../src/learnloop/diagnosis/gate_fit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

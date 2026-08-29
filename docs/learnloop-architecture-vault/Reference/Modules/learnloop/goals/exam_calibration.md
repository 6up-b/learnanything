---
title: "learnloop.goals.exam_calibration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/exam_calibration.py"
source_paths:
  - "src/learnloop/goals/exam_calibration.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.exam_calibration module"
  - "src/learnloop/goals/exam_calibration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.exam_calibration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.exam_calibration` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Exam calibration: did the model's pre-exam predictions come true?

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py) |
| Source lines | 147 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `calibration_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_calibration.py), line 74) — Pooled prediction-outcome calibration across all completed exam sessions.

### Module constants

- `_EPS` ([src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py), line 26)
- `_BIN_COUNT` ([src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py), line 27)
- `MINIMUM_CURVE_N` ([src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py), line 28)
- `_ANSWER_CONFIDENCE_PROBABILITY` ([src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py), line 29)

## Internal implementation anchors

- `_reliability_table(pairs: list[tuple[float, float]], *, bins: int=_BIN_COUNT) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_calibration.py), line 32) — n / Brier / log loss / equal-width reliability table for (predicted, observed) pairs.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `calibration_report`
- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `calibration_report`; statically calls `calibration_report`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `calibration_report`; statically calls `calibration_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — direct import
  - `test_duel_excludes_assisted_primed_and_unmatched_attempts`
  - `test_duel_is_empty_when_no_matched_attempt_exists`
- [tests/test_exam_calibration.py](../../../../../../tests/test_exam_calibration.py) — direct import
  - `test_empty_calibration_is_defined`
  - `test_facet_projection_calibration`
  - `test_known_pairs_produce_known_brier_and_bins`

## Modification guidance

- Change exam calibration policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/exam_calibration.py](../../../../../../src/learnloop/goals/exam_calibration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

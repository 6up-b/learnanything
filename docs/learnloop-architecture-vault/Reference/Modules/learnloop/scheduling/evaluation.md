---
title: "learnloop.scheduling.evaluation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/evaluation.py"
source_paths:
  - "src/learnloop/scheduling/evaluation.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.evaluation module"
  - "src/learnloop/scheduling/evaluation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.evaluation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.evaluation` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: `learnloop eval` — calibration report over logged decisions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/evaluation.py](../../../../../../src/learnloop/scheduling/evaluation.py) |
| Source lines | 520 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `brier_score(pairs: list[tuple[float, float]]) -> float` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 29)
- `log_loss(pairs: list[tuple[float, float]], *, clip: float=_CLIP) -> float` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 35) — Cross-entropy with soft targets in [0, 1].
- `class CalibrationBin` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 48)
  - `as_dict(self) -> dict[str, Any]` (line 55; public)
- `ece_equal_width(pairs: list[tuple[float, float]], *, bins: int=10) -> tuple[float, list[CalibrationBin]]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 65)
- `class EvalReport` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 90)
  - `as_dict(self) -> dict[str, Any]` (line 97; public)
  - `format_text(self) -> str` (line 106; public)
- `build_eval_report(vault: LoadedVault, repository: Repository, *, sections: set[str], bins: int=10) -> EvalReport` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 121)

### Module constants

- `_CLIP` ([src/learnloop/scheduling/evaluation.py](../../../../../../src/learnloop/scheduling/evaluation.py), line 23)
- `_COVERAGE_Z80` ([src/learnloop/scheduling/evaluation.py](../../../../../../src/learnloop/scheduling/evaluation.py), line 169)
- `_COLD_ATTEMPT_COUNT` ([src/learnloop/scheduling/evaluation.py](../../../../../../src/learnloop/scheduling/evaluation.py), line 170)

## Internal implementation anchors

- `_predictions_section(repository: Repository, *, bins: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 137)
- `_coverage_section(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 173) — Prospective 80% predictive-interval coverage, sliced cold vs warm.
- `_gates_section(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 239)
- `_retention_section(vault: LoadedVault, repository: Repository, *, bins: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 307)
- `_propensity_section(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 383)
- `_format_predictions(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 413)
- `_format_coverage(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 436)
- `_format_gates(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 455)
- `_format_retention(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 484)
- `_format_propensity(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/evaluation.py), line 505)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `build_eval_report`; statically calls `build_eval_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `fsrs_rating_for_attempt`; calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `percentiles`; calls `percentiles`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `MemoryState`, `apply_review`, `forgetting_curve`; calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_brier_hand_computed`
  - `test_ece_empty`
  - `test_ece_two_known_bins`
  - `test_gate_section_counts_manual_false_negatives`
  - `test_log_loss_hand_computed_and_clipped`
  - `test_report_on_real_session_flow`

## Modification guidance

- Change evaluation policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/evaluation.py](../../../../../../src/learnloop/scheduling/evaluation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

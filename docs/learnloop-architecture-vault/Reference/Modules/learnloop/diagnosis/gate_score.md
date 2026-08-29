---
title: "learnloop.diagnosis.gate_score"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/gate_score.py"
source_paths:
  - "src/learnloop/diagnosis/gate_score.py"
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
  - "learnloop.diagnosis.gate_score module"
  - "src/learnloop/diagnosis/gate_score.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.gate_score`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.gate_score` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Continuous follow-up gate score (Fable's-take items 2 + 7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GateSignalValues` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 83) — Raw gate inputs, bundled once so cascade and score modes read the same values.
- `class GateSubscore` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 98)
  - `as_dict(self) -> dict[str, Any]` (line 106; public)
- `class GateScoreResult` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 122)
  - `subscore(self, name: str) -> GateSubscore` (line 130; public)
  - `triggered_reasons(self) -> list[str]` (line 136; public) — Cascade-vocabulary reasons for trigger features scoring >= 0.5.
  - `as_dict(self) -> dict[str, Any]` (line 145; public)
- `compute_gate_score(*, signals: GateSignalValues, thresholds: dict[str, ResolvedThreshold], weights: dict[str, float], bias: float, gate_score_threshold: float, steepness: float, weights_provenance: str) -> GateScoreResult` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 155)
- `resolve_gate_weights(repository: Repository) -> tuple[dict[str, float], float, str]` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 194) — Fitted logistic weights from the fitted-parameters store, else defaults.
- `subscores_from_diagnostics(gate: dict[str, Any], config: Any) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 222) — Reconstruct the seven subscores from a persisted gate_diagnostics dict.

### Module constants

- `GATE_FEATURES` ([src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py), line 43)
- `GATE_FEATURE_VERSION` ([src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py), line 58)
- `TRIGGER_FEATURE_REASONS` ([src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py), line 62)
- `DEFAULT_GATE_WEIGHTS` ([src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py), line 70)
- `DEFAULT_GATE_BIAS` ([src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py), line 79)

## Internal implementation anchors

- `_subscores(signals: GateSignalValues, thresholds: dict[str, ResolvedThreshold], steepness: float) -> dict[str, tuple[float, float | None, ResolvedThreshold | None]]` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 276) — name -> (subscore, raw_value, threshold used).
- `_margin_subscore(value: float, threshold: float, steepness: float, *, bounded: bool=False) -> float` ([source](../../../../../../src/learnloop/diagnosis/gate_score.py), line 324) — Steep sigmoid of the margin over the threshold, normalized by its scale.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `GATE_FEATURE_VERSION`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `GATE_FEATURE_VERSION`, `GateScoreResult`, `GateSignalValues`, `compute_gate_score`, `resolve_gate_weights`; statically calls `GateSignalValues`, `compute_gate_score`, `resolve_gate_weights`
- [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] — imports `GATE_FEATURES`, `GATE_FEATURE_VERSION`, `subscores_from_diagnostics`; statically calls `subscores_from_diagnostics`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/signal_quantiles|learnloop.diagnosis.signal_quantiles]] — imports `ResolvedThreshold`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `FOLLOWUP_GATE_SCOPE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_gate_fit.py](../../../../../../tests/test_gate_fit.py) — direct import
  - `test_label_assembly`
  - `test_label_assembly_excludes_old_feature_semantics`
- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
  - `test_as_dict_carries_all_subscores`
  - `test_resolve_gate_weights_defaults_and_fitted`
  - `test_score_mode_fires_on_surprising_failure_and_logs_scores`
  - `test_subscores_from_cascade_era_diagnostics`
  - `test_subscores_from_score_mode_diagnostics`
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_success_resets_repeat_failure_gate_and_coverage_is_not_failed`

## Modification guidance

- Change gate score policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/gate_score.py](../../../../../../src/learnloop/diagnosis/gate_score.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

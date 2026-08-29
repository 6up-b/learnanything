---
title: "learnloop.diagnosis.signal_quantiles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/signal_quantiles.py"
source_paths:
  - "src/learnloop/diagnosis/signal_quantiles.py"
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
  - "learnloop.diagnosis.signal_quantiles module"
  - "src/learnloop/diagnosis/signal_quantiles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.signal_quantiles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.signal_quantiles` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Data-relative follow-up gate thresholds (Fable's-take item 1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/signal_quantiles.py](../../../../../../src/learnloop/diagnosis/signal_quantiles.py) |
| Source lines | 141 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ResolvedThreshold` ([source](../../../../../../src/learnloop/diagnosis/signal_quantiles.py), line 27)
  - `as_dict(self) -> dict[str, Any]` (line 35; public)
- `resolve_followup_thresholds(repository: Repository, config: SchedulerFollowupConfig, *, exclude_attempt_id: str | None=None) -> dict[str, ResolvedThreshold]` ([source](../../../../../../src/learnloop/diagnosis/signal_quantiles.py), line 45) — Resolve every gate threshold, quantile-relative where configured.

## Internal implementation anchors

- `_resolve(name: str, *, samples: list[float], quantile: float, absolute: float, config: SchedulerFollowupConfig) -> ResolvedThreshold` ([source](../../../../../../src/learnloop/diagnosis/signal_quantiles.py), line 103)
- `_absolute(name: str, value: float) -> ResolvedThreshold` ([source](../../../../../../src/learnloop/diagnosis/signal_quantiles.py), line 133)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `ResolvedThreshold`, `resolve_followup_thresholds`; statically calls `resolve_followup_thresholds`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `ResolvedThreshold`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `SchedulerFollowupConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `empirical_quantile`; calls `empirical_quantile`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
- [tests/test_signal_quantiles.py](../../../../../../tests/test_signal_quantiles.py) — direct import
  - `test_absolute_fallback_below_min_samples`
  - `test_absolute_mode_disables_quantiles`
  - `test_current_attempt_excluded`
  - `test_positive_direction_rows_do_not_count`
  - `test_quantile_resolution_with_enough_samples`
  - `test_severity_quantile_reads_gate_diagnostics`
  - `test_window_limits_history`

## Modification guidance

- Change signal quantiles policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/signal_quantiles.py](../../../../../../src/learnloop/diagnosis/signal_quantiles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

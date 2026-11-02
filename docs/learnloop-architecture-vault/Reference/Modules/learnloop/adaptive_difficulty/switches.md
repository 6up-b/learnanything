---
title: "learnloop.adaptive_difficulty.switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/switches.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/switches.py"
source_commit: "88e6e75b69fe4a2be20e016b9a3d5480f772547d"
source_commit_timestamp: "2026-10-18T15:39:39-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.switches module"
  - "src/learnloop/adaptive_difficulty/switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.switches` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's switches, read from config only (``[adaptive_difficulty]``, spec §11.1, §11.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py) |
| Source lines | 74 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `88e6e75b69fe4a2be20e016b9a3d5480f772547d` |
| Commit timestamp | `2026-10-18T15:39:39-04:00` |

## Public API

- `ad_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 24) — The master switch (``adaptive_difficulty.enabled``).
- `receipts_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 31) — ``forecast_receipts``: the serve-time sweep, serve inputs, in-process forecasts and the marker.
- `outside_forecasters(config: Any) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 37) — The outside forecasters that run; () with the switch off.
- `rating_tap_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 48)
- `feature_audit_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 52)
- `any_background_work(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 56) — Whether a serve or a plan build may start a background AD job.

### Module constants

- `IN_PROCESS_FORECASTERS` ([src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 13)
- `LLM_V1` ([src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 14)
- `LLM_V3_LLM` ([src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 15)
- `LLM_V3_DECIDER` ([src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 16)
- `OUTSIDE_FORECASTERS` ([src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 17)

### Explicit exports

`__all__` declares:

- `IN_PROCESS_FORECASTERS`
- `LLM_V1`
- `LLM_V3_DECIDER`
- `LLM_V3_LLM`
- `OUTSIDE_FORECASTERS`
- `ad_enabled`
- `any_background_work`
- `feature_audit_enabled`
- `outside_forecasters`
- `rating_tap_enabled`
- `receipts_enabled`

## Internal implementation anchors

- `_section(config: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/switches.py), line 20)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `LLM_V1`, `feature_audit_enabled`, `outside_forecasters`, `receipts_enabled`; statically calls `feature_audit_enabled`, `outside_forecasters`, `receipts_enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `LLM_V1`, `LLM_V3_DECIDER`, `LLM_V3_LLM`, `any_background_work`, `feature_audit_enabled`, `outside_forecasters`; statically calls `any_background_work`, `feature_audit_enabled`, `outside_forecasters`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `feature_audit_enabled`; statically calls `feature_audit_enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `IN_PROCESS_FORECASTERS`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `ad_enabled`; statically calls `ad_enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `LLM_V1`, `LLM_V3_DECIDER`, `LLM_V3_LLM`, `outside_forecasters`; statically calls `outside_forecasters`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `receipts_enabled`; statically calls `receipts_enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `receipts_enabled`; statically calls `receipts_enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `LLM_V1`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `ad_enabled`; statically calls `ad_enabled`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `feature_audit_enabled`, `outside_forecasters`; statically calls `feature_audit_enabled`, `outside_forecasters`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `rating_tap_enabled`, `receipts_enabled`; statically calls `rating_tap_enabled`, `receipts_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `any_background_work`; statically calls `any_background_work`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `receipts_enabled`; statically calls `receipts_enabled`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_z_v1_calibration_never_reads_a_withheld_items_forecast`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`

## Modification guidance

- Make changes here when the responsibility remains switches within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/switches.py](../../../../../../src/learnloop/adaptive_difficulty/switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

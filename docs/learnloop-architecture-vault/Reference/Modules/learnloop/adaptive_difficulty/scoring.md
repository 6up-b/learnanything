---
title: "learnloop.adaptive_difficulty.scoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/scoring.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/scoring.py"
source_commit: "fc54039ec677f81905caccc24c1c70b7a2a13bdf"
source_commit_timestamp: "2026-10-21T13:03:22-04:00"
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
  - "learnloop.adaptive_difficulty.scoring module"
  - "src/learnloop/adaptive_difficulty/scoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.scoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.scoring` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The forecast-score replayer (spec_adaptive_difficulty_v1 §8.3; DERIVED ``item_forecast_scores``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py) |
| Source lines | 132 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fc54039ec677f81905caccc24c1c70b7a2a13bdf` |
| Commit timestamp | `2026-10-21T13:03:22-04:00` |

## Public API

- `log_loss(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 33)
- `brier(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 38)
- `score_rows(connection: Any, vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 43) — The scores of every item forecast receipt (pure reads; zero model calls).
- `rebuild(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 114) — Clear and rebuild ``item_forecast_scores`` (zero model calls).

### Module constants

- `SCORE_VERSION` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 29)
- `CLIP` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 30)

### Explicit exports

`__all__` declares:

- `CLIP`
- `SCORE_VERSION`
- `brier`
- `log_loss`
- `rebuild`
- `score_rows`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `rebuild`; statically calls `rebuild`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild`; statically calls `rebuild`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `unassisted_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `successor_active`; calls `successor_active`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `clear_derived`, `has_table`, `write_scores`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `valid_for_serve`; calls `valid_for_serve`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_ad_never_writes_evidence`
  - `test_pre_exposed_presentation_excluded_from_update_and_scoring`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`

## Modification guidance

- Make changes here when the responsibility remains scoring within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

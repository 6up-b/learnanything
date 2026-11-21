---
title: "learnloop.adaptive_difficulty.snapshot_parts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/snapshot_parts.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/snapshot_parts.py"
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
  - "learnloop.adaptive_difficulty.snapshot_parts module"
  - "src/learnloop/adaptive_difficulty/snapshot_parts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.snapshot_parts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.snapshot_parts` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: What adaptive difficulty's serve-time forecasts state in their prediction snapshots (EP spec §7.7.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py) |
| Source lines | 186 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ServedItem` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 48) — The served revision's identity, as the serve read it: the item, its content hash, its learning object, its canonical facets and its surface group with the field that key came from.
- `surface_source(item: Any, key: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 60) — The field :func:`~learnloop.adaptive_difficulty.replay.surface_group`'s ``key`` came from (``item`` when the item is its own group).
- `item_target(served: ServedItem, *, unit: str, presentation_kind: str, presentation_id: str) -> PredictionTarget` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 73) — A serve-time forecast's target: the item at its served revision, its learning object, its facets and its surface group, conditional on serving it at this presentation, resolved by AD's scorer.
- `threshold_parts(served: ServedItem, *, name: str, categories: tuple[float, float, float], state_hash: str, mixture: str, presentation_kind: str, presentation_id: str, served_at: str, epoch: Any, threshold_version: str, replay_version: str) -> SnapshotParts` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 89) — An ``ad_threshold@*`` receipt's snapshot: the replayed state it read (every readable event at the serve, through the serve's material view), the three category probabilities, and its artifacts.
- `threshold_snapshot(served: ServedItem | None, *, name: str, categories_of: Callable[[], tuple[float, float, float]], mixture: str, state_hash: str, presentation_kind: str, presentation_id: str, served_at: str, epoch: Any, threshold_version: str, replay_version: str) -> tuple[dict[str, float] | None, SnapshotParts | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 118) — A threshold forecast's ``p_categories`` (by category, ``categories_of()``: the caller's :func:`~learnloop.adaptive_difficulty.predict.category_mixture` at the view, spec, warmth and weights its ``p̄`` was computed with) and its snapshot parts.
- `in_process_snapshot(served: ServedItem | None, **kwargs: Any) -> SnapshotParts | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 146) — :func:`in_process_parts`, or None (the writer derives what it can) when the serve passed no identity or it cannot be built.
- `in_process_parts(served: ServedItem, *, incumbent: bool, version_hash: str, inputs: Mapping[str, Any], presentation_kind: str, presentation_id: str, served_at: str) -> SnapshotParts` ([source](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 160) — ``mastery_ekf``'s and ``lo_general+composite``'s snapshot: the incumbent reads the mastery states as they stand (current); the challenger refits on attempt rows completed by the serve (the field's ``completed_by``).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 30)
- `UNIT_CATEGORIES` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 33)
- `CATEGORIES` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 34)
- `EVENT_CATEGORIES` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 35)
- `RESOLVER_VERSION` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 39)
- `_SURFACE_SOURCES` ([src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py), line 42)

### Explicit exports

`__all__` declares:

- `CATEGORIES`
- `EVENT_CATEGORIES`
- `RESOLVER_VERSION`
- `ServedItem`
- `UNIT_CATEGORIES`
- `in_process_parts`
- `in_process_snapshot`
- `item_target`
- `surface_source`
- `threshold_parts`
- `threshold_snapshot`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `in_process_snapshot`; statically calls `in_process_snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/repeat_receipts|learnloop.adaptive_difficulty.repeat_receipts]] — imports `threshold_snapshot`; statically calls `threshold_snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `ServedItem`, `surface_source`, `threshold_snapshot`; statically calls `ServedItem`, `surface_source`, `threshold_snapshot`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/db/evidence_cutoff|learnloop.db.evidence_cutoff]] — imports `Cutoff`
- [[Reference/Modules/learnloop/db/prediction_target|learnloop.db.prediction_target]] — imports `MEMBER_FACET`, `MEMBER_ITEM`, `MEMBER_LEARNING_OBJECT`, `MEMBER_SURFACE_GROUP`, `PredictionTarget`, `TargetMember`; calls `PredictionTarget`, `TargetMember`
- [[Reference/Modules/learnloop/scheduling/prediction_snapshots|learnloop.scheduling.prediction_snapshots]] — imports `SnapshotParts`, `UNIT_BINARY`, `categorical_distribution`; calls `SnapshotParts`, `categorical_distribution`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/adaptive_difficulty/repeat_receipts|learnloop.adaptive_difficulty.repeat_receipts]], [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_epp_prediction_snapshots.py](../../../../../../tests/test_epp_prediction_snapshots.py) — direct import
  - `test_the_snapshot_names_the_resolver_that_scores_it`
- [tests/test_epp_repeat_receipts.py](../../../../../../tests/test_epp_repeat_receipts.py) — direct import
  - `test_the_memory_context_tells_the_cases_apart`

## Modification guidance

- Make changes here when the responsibility remains snapshot parts within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/snapshot_parts.py](../../../../../../src/learnloop/adaptive_difficulty/snapshot_parts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

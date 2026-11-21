---
title: "learnloop.scheduling.prediction_snapshots"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/prediction_snapshots.py"
source_paths:
  - "src/learnloop/scheduling/prediction_snapshots.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.prediction_snapshots module"
  - "src/learnloop/scheduling/prediction_snapshots.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.prediction_snapshots`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.prediction_snapshots` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Prediction snapshots: what a forecast receipt needs to be scored later without reconstruction (EP spec §7.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py) |
| Source lines | 313 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SnapshotParts` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 65) — What a producer knows that the receipt's own fields do not say.
- `as_of_status(value: Any, issued: str) -> str` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 84) — The validity of a receipt's original ``inputs_as_of`` against its issue time.
- `binary_distribution(p: float, *, event: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 99) — A binary forecast as named outcomes: ``p`` itself for the event, its complement for the rest.
- `categorical_distribution(probabilities: Mapping[str, float], *, unit: str, event: str, event_outcomes: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 106) — A forecast over named categories; the binary ``p`` is the sum over ``event_outcomes``.
- `not_issued_distribution(reason: str, *, unit: str=UNIT_BINARY, event: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 114)
- `receipt_target(receipt: Any) -> tuple[PredictionTarget | None, list[str], str | None]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 127) — The target the writer can read off the receipt's columns: ``(target, unversioned fields, absent reason)``.
- `snapshot(receipt: Any, issued: str, recorded_as_of: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 196) — ``versions_json.snapshot`` of one receipt (module docstring).
- `distribution(receipt: Any) -> tuple[dict[str, Any], str | None]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 209) — ``forecast_json.distribution`` and the reason no forecast was issued (None when one was).
- `receipt_bodies(receipt: Any, issued: str, recorded_as_of: str) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 222) — The receipt's ``forecast`` and ``versions`` bodies with the snapshot added.
- `voi_snapshot(*, site: str, forecast: Mapping[str, Any], columns: Mapping[str, Any], forecast_version: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 245) — ``versions_json.snapshot`` of a native ``voi_forecasts`` body (it has no ``inputs_as_of``).

### Module constants

- `SNAPSHOT_SCHEMA` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 44)
- `AS_OF_EXACT` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 48)
- `AS_OF_UNKNOWN` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 49)
- `AS_OF_INVALID` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 50)
- `UNVERSIONED` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 53)
- `UNIT_BINARY` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 56)
- `EVENT_OUTCOME` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 57)
- `NOT_EVENT_OUTCOME` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 58)
- `_BOUND_COLUMNS` ([src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 60)

### Explicit exports

`__all__` declares:

- `AS_OF_EXACT`
- `AS_OF_INVALID`
- `AS_OF_UNKNOWN`
- `SNAPSHOT_SCHEMA`
- `SnapshotParts`
- `UNIT_BINARY`
- `UNVERSIONED`
- `as_of_status`
- `binary_distribution`
- `categorical_distribution`
- `distribution`
- `not_issued_distribution`
- `receipt_bodies`
- `receipt_target`
- `snapshot`
- `voi_snapshot`

## Internal implementation anchors

- `_not_issued_reason(receipt: Any) -> str | None` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 118)
- `_target_block(receipt: Any, parts: SnapshotParts) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 158)
- `_cutoff_block(receipt: Any, parts: SnapshotParts, issued: str, recorded_as_of: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 171)
- `_provenance_block(receipt: Any, parts: SnapshotParts) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prediction_snapshots.py), line 183)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]] — imports `SnapshotParts`, `UNIT_BINARY`, `categorical_distribution`; statically calls `SnapshotParts`, `categorical_distribution`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `SnapshotParts`, `module`; statically calls `receipt_bodies`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; statically calls `voi_snapshot`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/evidence_cutoff|learnloop.db.evidence_cutoff]] — imports `Cutoff`
- [[Reference/Modules/learnloop/db/prediction_target|learnloop.db.prediction_target]] — imports `MEMBER_FACET`, `MEMBER_ITEM`, `MEMBER_LEARNING_OBJECT`, `PredictionTarget`, `TargetMember`; calls `PredictionTarget`, `TargetMember`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]], [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]], [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/epp_snapshot_helpers.py](../../../../../../tests/epp_snapshot_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_epp_prediction_snapshots.py](../../../../../../tests/test_epp_prediction_snapshots.py) — direct import
  - `test_a_receipt_round_trips_its_cutoff_target_distribution_and_provenance`
  - `test_a_snapshot_that_cannot_be_built_never_costs_the_receipt`
  - `test_the_status_check_of_the_unreadable_time`
  - `test_writes_are_idempotent_and_roll_back_with_their_transaction`

## Modification guidance

- Change prediction snapshots policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/prediction_snapshots.py](../../../../../../src/learnloop/scheduling/prediction_snapshots.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

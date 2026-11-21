---
title: "learnloop.adaptive_difficulty.repeat_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/repeat_receipts.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/repeat_receipts.py"
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
  - "learnloop.adaptive_difficulty.repeat_receipts module"
  - "src/learnloop/adaptive_difficulty/repeat_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.repeat_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.repeat_receipts` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The predecessor's prediction on a repeat presentation (evidence packets spec §7.7.3 item 1, §7.7.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py) |
| Source lines | 403 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `new_receipt_id() -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 77) — A repeat receipt's id, from this module's own stream (never ``ids.new_ulid``: module docstring).
- `memory_context(connection: Any, view: Any, item: Any, served: Any, served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 105) — The item's and its surface group's earlier attempts, read through the serve's material view.
- `last_exposure(connection: Any, view: Any, learning_object_id: str, served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 159) — The exposure warmth is computed from: the learning object's latest attempt, reveal or reading opportunity strictly before the serve, in ``serving._warmth``'s order and comparison (the first of equal times wins).
- `delay_context(connection: Any, view: Any, presentation_id: str, memory: Mapping[str, Any], served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 184) — Whether the repeat's delay was chosen by the plan's policy (natural) or by a randomized check, and what is known at the serve of the probability of its assignment.
- `shared_inputs(item: Any, *, content_hash: str, state_hash: str, features: Mapping[str, Any], recalibration: str, warmth: float, exposure: Mapping[str, Any], pre_exposed: bool, memory: Mapping[str, Any], delay: Mapping[str, Any], coupling: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 226) — The part of a repeat receipt's ``inputs_json`` both views share, from values already read (no read, no write): the assembly is apart from every read so the shape is testable, and pinned, with plain values.
- `view_inputs(shared: Mapping[str, Any], *, view: str, mixture: str, vector: Mapping[str, Any], spec: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 254) — One view's ``inputs_json``: the shared part, every signal with its availability and whether this view's prediction read it, the values it read, and the loadings it used (none in a learning-object view).
- `build_receipt(name: str, *, item: Any, presentation_kind: str, presentation_id: str, served_at: str, forecast: Mapping[str, Any], inputs: Mapping[str, Any], p: float | None, status: str, parts: Any) -> ForecastReceipt` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 263) — One repeat receipt: kind ``item_unassisted_success``, bound to the presentation, keyed as AD's other serve-time receipts are (``forecasters.receipt_key``), so a second write of it is ignored.
- `repeat_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str, served_at: str, view: Any) -> tuple[list[ForecastReceipt], str | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 362) — The two repeat receipts of one presentation, and why none when there are none.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 50)
- `REPEAT_SUBJECT` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 52)
- `REPEAT_LO` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 53)
- `REPEAT_FORECASTERS` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 54)
- `REPEAT_VERSION` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 55)
- `INPUTS_SCHEMA` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 56)
- `RANDOMIZED_CHECK_ORIGIN` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 58)
- `PREDECESSOR_MEMORY` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 62)
- `_RECEIPT_IDS` ([src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 74)

### Explicit exports

`__all__` declares:

- `INPUTS_SCHEMA`
- `PREDECESSOR_MEMORY`
- `RANDOMIZED_CHECK_ORIGIN`
- `REPEAT_FORECASTERS`
- `REPEAT_LO`
- `REPEAT_SUBJECT`
- `REPEAT_VERSION`
- `build_receipt`
- `delay_context`
- `last_exposure`
- `memory_context`
- `new_receipt_id`
- `repeat_receipts`
- `shared_inputs`
- `view_inputs`

## Internal implementation anchors

- `_at_or_before(value: Any, served_at: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 83)
- `_hours(earlier: Any, served_at: str) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 91)
- `_attempt_entry(row: Mapping[str, Any], served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 98)
- `_signals(vector: Mapping[str, Any], read: Mapping[str, float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 214)
- `_repeat_parts(parts: Any, *, inputs_ref: str, epoch: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 287)
- `_computed(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str, served_at: str, view: Any) -> list[ForecastReceipt]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 296)
- `_failed(item: Any, error: BaseException, *, presentation_kind: str, presentation_id: str, served_at: str, epoch: Any) -> list[ForecastReceipt]` ([source](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py), line 343) — The two receipts as failed forecasts: issued at the serve, no ``p``, the error's type as the reason.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `new_receipt_id`, `repeat_receipts`; statically calls `repeat_receipts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `EVENT`, `receipt_key`; calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `is_denial`; calls `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `category_mixture`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `days`, `lo_view_name`, `snapshot`, `surface_group`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `constants_from_config`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `RESOLUTION_VERSION`, `feature_inputs`, `pre_exposed`, `signal_vector`; calls `feature_inputs`, `pre_exposed`, `signal_vector`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `THRESHOLD_VERSION`, `_no_loadings`, `_spec`, `_warmth`, `served_item`; calls `_no_loadings`, `_spec`, `_warmth`, `served_item`
- [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]] — imports `threshold_snapshot`; calls `threshold_snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `successor_active`; calls `successor_active`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/evidence_cutoff|learnloop.db.evidence_cutoff]] — imports `Cutoff`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `UlidStream`; calls `UlidStream`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`; calls `ForecastReceipt`
- [[Reference/Modules/learnloop/scheduling/prediction_snapshots|learnloop.scheduling.prediction_snapshots]] — imports `SnapshotParts`; calls `SnapshotParts`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `parameter`; calls `parameter`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/epp_repeat_helpers.py](../../../../../../tests/epp_repeat_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_epp_repeat_receipts.py](../../../../../../tests/test_epp_repeat_receipts.py) — direct import
  - `test_a_computation_that_fails_is_recorded_as_failed_with_its_reason`
  - `test_a_protected_item_gets_no_repeat_receipt`
  - `test_a_repeat_gets_the_two_receipts_and_a_fresh_item_keeps_its_own`
  - `test_a_write_that_fails_rolls_back_alone`
  - `test_answered_unanswered_and_scored_like_the_in_process_receipts`
  - `test_repeat_receipt_ids_come_from_their_own_stream`
  - `test_repeat_receipts_move_no_id_seed_receipt_score_or_state_under_a_frozen_clock`
  - `test_repeat_receipts_roll_back_with_the_serve_transaction`
  - `test_the_categories_sum_to_one_and_category_two_is_the_binary_value`
  - `test_the_delay_names_its_kind_and_what_is_unknown_of_its_assignment`
  - `test_the_inputs_state_signals_with_availability_and_the_memory_context`
  - `test_the_last_exposure_is_the_one_warmth_reads`
  - `test_the_memory_context_tells_the_cases_apart`
  - `test_the_snapshot_names_the_repeat_target_and_no_frozen_serve_inputs`
  - `test_the_subject_receipt_is_the_predecessors_own_prediction_at_the_serve`
  - `test_the_surface_group_is_recorded_as_served_after_a_later_edit`

## Modification guidance

- Make changes here when the responsibility remains repeat receipts within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/repeat_receipts.py](../../../../../../src/learnloop/adaptive_difficulty/repeat_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

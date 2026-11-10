---
title: "learnloop.adaptive_difficulty.serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/serving.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/serving.py"
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
  - "learnloop.adaptive_difficulty.serving module"
  - "src/learnloop/adaptive_difficulty/serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.serving` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD's draw at a planned new-material slot, and the serve-time AD2+AD3 receipts (spec §6.1, §10.1-10.2, §8.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py) |
| Source lines | 461 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SlotCandidate` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 73)
- `class SlotRequest` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 80)
  - `decision_key(self) -> str` (line 93; public)
- `class SlotDecision` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 98)
  - `step_detail(self) -> dict[str, Any] | None` (line 110; public)
- `slot_applies(config: Any, item: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 116) — A new-material slot AD's draw serves (§6.1): a planned, never-served item with ``new_admitted`` (an ordinary new-lane item the chooser planned).
- `view_for(snapshot: RP.Snapshot, config: Any, learning_object_id: str) -> tuple[Any, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 126)
- `decide_slot(vault: Any, repository: Any, request: SlotRequest, *, view: Any=None) -> SlotDecision` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 178) — Score the slot's support and draw (§6.1), writing the ``ad_selections`` row first.
- `commission_draw(vault: Any, repository: Any, snapshot: RP.Snapshot, view: Any, view_name: str, *, learning_object_id: str, subject: str, facet: str, capability_name: str, key: str, now: str, constants: S.SelectionConstants | None=None, targets: Sequence[Mapping[str, Any] | None]=(None,), generating_job_id: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 308) — A commission draw over ``X_c`` (§6.1): the same rule over feature points with ``z = 0``, its own seed and ``ad_selections`` row (``kind = commission``).
- `why_for_presentation(connection: Any, presentation_id: str, *, view: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 347) — "Why this item" for a served plan item (§12): the one line of the draw that chose it, or None when no AD draw chose it (below the tag, ``selection`` off, a predecessor serve) or its item is withheld now (``view``, the material view).
- `frozen_loadings(vault: Any, repository: Any, connection: Any, content_hash: str, served_at: str, *, view: Any) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 371) — The item revision's loadings in force at the serve and the coupling version (AD2/AD3).
- `threshold_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str, served_at: str, view: Any) -> list[Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 396) — The in-process ``ad_threshold@*`` forecasts of one presentation (AD2/AD3).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 56)
- `SUBSTITUTED` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 58)
- `DISPLACED` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 59)
- `AD_INELIGIBLE` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 60)
- `PRE_EXPOSED` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 61)
- `THRESHOLD_FORECASTERS` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 62)
- `THRESHOLD_VERSION` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 63)
- `WHY` ([src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 65)

### Explicit exports

`__all__` declares:

- `AD_INELIGIBLE`
- `DISPLACED`
- `PRE_EXPOSED`
- `SUBSTITUTED`
- `SlotCandidate`
- `SlotDecision`
- `SlotRequest`
- `THRESHOLD_FORECASTERS`
- `WHY`
- `commission_draw`
- `decide_slot`
- `frozen_loadings`
- `slot_applies`
- `threshold_receipts`
- `view_for`
- `why_for_presentation`

## Internal implementation anchors

- `_warmth(connection: Any, view: Any, learning_object_id: str, now: str) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 132) — ``w_t`` at a decision: hours since the LO's last exposure (an attempt, a reveal, a reading opportunity) before ``now``, read through the material view (Codex verify F20: an attempt on a withheld item, or a receipt whose source is withheld now, warms nothing).
- `_loadings(snapshot: RP.Snapshot, config: Any, content_hash: str, now: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 157)
- `_spec(vault: Any, connection: Any, snapshot: RP.Snapshot, item: Any, now: str, view: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 163)
- `_versions(vault: Any, snapshot: RP.Snapshot, view_name: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 171)
- `_maybe_commission(vault: Any, repository: Any, snapshot: RP.Snapshot, view: Any, view_name: str, request: SlotRequest, constants: S.SelectionConstants, *, cell: str | None, capability_name: str | None, warmth: float, material: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 281) — §6.1: a commission draw when the cell pool has no item with ``P_band >= calibrate_below``.
- `_no_loadings(spec: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/serving.py), line 438)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `commission_draw`, `view_for`; statically calls `commission_draw`, `view_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `frozen_loadings`, `threshold_receipts`; statically calls `frozen_loadings`, `threshold_receipts`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `SlotCandidate`, `SlotRequest`, `decide_slot`; statically calls `SlotCandidate`, `SlotRequest`, `decide_slot`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `slot_applies`; statically calls `slot_applies`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `why_for_presentation`; statically calls `why_for_presentation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `EVENT`, `receipt_key`; calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`, `material_view`; calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `GuardDenied`, `entry`, `is_denial`; calls `GuardDenied`, `entry`, `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `capability`, `current_spec`, `facet_weights`, `mixture_weights`, `point_spec`, `predict`, `score`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `sweep`; calls `sweep`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; calls `live_judgments`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `days`, `lo_view_name`, `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `commission_candidates`, `constants_from_config`, `draw`, `recompute`, `seed_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `coupling_on`, `selection_on`, `subject_view_live`, `successor_active`; calls `coupling_on`, `selection_on`, `subject_view_live`, `successor_active`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `has_table`, `insert_selection`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`; calls `ForecastReceipt`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `parameter`; calls `parameter`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]], [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_property_a_buggy_deciders_pick_outside_the_facts_is_rolled_back`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_why_this_item_names_the_draw_that_chose_it`

## Modification guidance

- Make changes here when the responsibility remains serving within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/serving.py](../../../../../../src/learnloop/adaptive_difficulty/serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

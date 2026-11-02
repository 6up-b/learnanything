---
title: "learnloop.adaptive_difficulty.dose"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/dose.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/dose.py"
source_commit: "9adf8fc4802c6db8b4c80ddd04ba3160c5772360"
source_commit_timestamp: "2026-10-23T15:29:18-04:00"
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
  - "learnloop.adaptive_difficulty.dose module"
  - "src/learnloop/adaptive_difficulty/dose.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.dose`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.dose` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: How many: randomized dose offers in the Reader (spec_adaptive_difficulty_v1 §5.12, D21; switch ``reading_dose_offers``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py) |
| Source lines | 392 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9adf8fc4802c6db8b4c80ddd04ba3160c5772360` |
| Commit timestamp | `2026-10-23T15:29:18-04:00` |

## Public API

- `class Boundary` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 64) — What the Reader knows at the section boundary (no magnitude: no dwell, scroll or time).
- `class DoseDecision` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 78)
  - `as_dict(self) -> dict[str, Any]` (line 86; public)
- `budget(connection: Any, *, extraction_id: str, section_id: str, now: str, daily: int, view: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 99) — Why the friction budget has no room (None when it has): one extra per section, ``daily`` a day.
- `feasible_variants(vault: Any, repository: Any, connection: Any, boundary: Boundary, learning_object_ids: Sequence[str], *, reading_map: Any=None, view: Any=None) -> tuple[list[str], dict[str, str], dict[str, dict[str, Any]]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 130) — ``(feasible, infeasible with why, each extra's content)``.
- `dose_taken(connection: Any, learning_object_ids: Sequence[str], *, view: Any) -> dict[str, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 181) — The dose of each offered kind already taken in the window at the decision (the moderator of the randomized dose-response, §5.12): recorded opportunities on the section's LOs since their last graded attempt.
- `decide(vault: Any, repository: Any, boundary: Boundary, *, clock: Clock | None=None, reading_map: Any=None, view: Any=None) -> DoseDecision` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 232) — At a section boundary: eligibility, the budget, the draw, and its row before anything is shown.
- `offer_withheld(connection: Any, view: Any, variant: Any, content: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 317) — Whether a drawn extra's content is withheld now (revalidated before it is shown again).
- `record_uptake(vault: Any, repository: Any, draw_id: str, kind: str, *, clock: Clock | None=None, view: Any=None) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 324) — Append ``delivered``, ``not_delivered``, ``taken`` or ``dismissed`` (never changing the draw).
- `taken_offers(connection: Any, *, view: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 355) — Each taken extra's content key -> its draw id (a reading opportunity carries the id), from the material view's dose cohort (a withheld extra's draw is not one; fix round 10's self-audit).

### Module constants

- `DOSE_VERSION` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 49)
- `BASE_VERSION` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 50)
- `NONE` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 51)
- `EXTRA_EXAMPLE` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 52)
- `EXTRA_QUESTION` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 53)
- `VARIANTS` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 54)
- `UPTAKE` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 55)
- `OFFER_TEXT` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 56)
- `WHY_TEXT` ([src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 60)

### Explicit exports

`__all__` declares:

- `BASE_VERSION`
- `Boundary`
- `DOSE_VERSION`
- `DoseDecision`
- `EXTRA_EXAMPLE`
- `EXTRA_QUESTION`
- `NONE`
- `OFFER_TEXT`
- `UPTAKE`
- `VARIANTS`
- `WHY_TEXT`
- `budget`
- `decide`
- `dose_taken`
- `feasible_variants`
- `offer_withheld`
- `record_uptake`
- `taken_offers`

## Internal implementation anchors

- `_day(stamp: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 94)
- `_studied_examples(connection: Any, view: Any, learning_object_ids: Sequence[str]) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 117)
- `_forecast(vault: Any, repository: Any, connection: Any, learning_object_id: str, *, view: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose.py), line 204) — The AD forecast fixed before the draw (a precision covariate, never an input of the draw).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `taken_offers`; statically calls `taken_offers`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `Boundary`, `UPTAKE`, `decide`, `record_uptake`; statically calls `Boundary`, `decide`, `record_uptake`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `lo_cell_facet`; calls `lo_cell_facet`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`, `is_denial`; calls `entry`, `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `point_spec`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `VaultReadingMap`; calls `VaultReadingMap`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `entry_point`, `seed_for`, `uniform`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `dose_offers_on`; calls `dose_offers_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `dose_rows`, `has_table`, `insert_dose_row`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `READING_DOSE`, `draw_from`, `reading_dose_propensities`; calls `draw_from`, `reading_dose_propensities`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_dose_draw_at_a_protected_origin_is_a_draw_never_made`
  - `test_a_late_uptake_callback_writes_nothing_when_ad_cannot_record_it`
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_the_dose_arm_never_offers_or_returns_a_held_out_question`
  - `test_the_dose_moderator_window_closes_only_at_a_visible_graded_attempt`
  - `test_with_the_predicate_unavailable_the_dose_arm_draws_nothing`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_a_taken_extra_becomes_a_reading_opportunity_with_the_offer_id`
  - `test_dose_offer_propensities_exact`
  - `test_draw_frequencies_match_propensities`
  - `test_infeasible_variant_has_no_mass_and_its_reason_is_logged`
  - `test_recommendations_never_act`
  - `test_switch_off_is_todays_reader_exactly`
  - `test_the_friction_budget_holds`
  - `test_uptake_appends_rows_and_never_changes_the_draw`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
  - `test_a_planted_read_swallowed_in_the_dose_decision_yields_no_decision_and_no_rows`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_marking_and_release_flip_the_epoch_and_the_reading_with_it`
  - `test_probe_candidates_are_taken_in_reading_order_not_span_id_order`
  - `test_probe_raw_section_membership_in_the_dose_arm`

## Modification guidance

- Make changes here when the responsibility remains dose within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/dose.py](../../../../../../src/learnloop/adaptive_difficulty/dose.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

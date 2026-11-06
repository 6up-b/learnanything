---
title: "learnloop.adaptive_difficulty.reading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/reading.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/reading.py"
source_commit: "04d1b40e19aa935b9233c007868ca3c58d217e99"
source_commit_timestamp: "2026-11-06T04:58:47-05:00"
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
  - "learnloop.adaptive_difficulty.reading module"
  - "src/learnloop/adaptive_difficulty/reading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.reading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.reading` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Reading and other learning opportunities, frozen in a receipt (spec §5.11, D20, D22; AD1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py) |
| Source lines | 410 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `04d1b40e19aa935b9233c007868ca3c58d217e99` |
| Commit timestamp | `2026-11-06T04:58:47-05:00` |

## Public API

- `class VaultReadingMap` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 98) — The default map: ``reader.reader_progression``'s section/span -> LO rule, worked examples by role (``source_retrieval.corpus.role_keys``), facets by the LO's facet union.
  - `__init__(self, vault: Any, repository: Any, view: Any=None) -> None` (line 105; internal)
  - `_document_ir(self, extraction_id: str) -> Any` (line 122; internal) — The extraction's IR through the reading chokepoint (RO2 landing ruling R6): the material view's ``document_ir`` (none for a reading the withheld material touches, or while the view is unavailable).
  - `los_for_section(self, extraction_id: str, section_id: str) -> list[str]` (line 136; public)
  - `los_for_span(self, extraction_id: str, span_id: str) -> list[str]` (line 150; public)
  - `section_spans(self, extraction_id: str, section_id: str) -> list[str]` (line 163; public)
  - `worked_example_spans(self, extraction_id: str) -> set[str]` (line 166; public)
  - `reading_order(self, extraction_id: str) -> dict[str, int]` (line 178; public)
  - `withheld(self, extraction_id: str, span_id: str | None) -> bool` (line 181; public)
  - `note_withheld(self, note_id: str) -> bool` (line 186; public) — Whether a note is withheld (a held-out source's canonical note; fix round 13, F43).
  - `los_for_note(self, note_id: str) -> list[str]` (line 194; public)
  - `lo_for_item(self, practice_item_id: str) -> str | None` (line 201; public)
  - `facets_for_lo(self, learning_object_id: str) -> list[str]` (line 205; public)
- `section_learning_objects(vault: Any, repository: Any, extraction_id: str, section_id: str, *, view: Any=None) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 214) — Router objective RO4 (landing, after RO2's ruling R6): a reading section's LOs as AD maps them, for the rollouts' reading action, so its doses land on the LOs AD's reading curve (``reading_dose``) counts: through the map's ``MaterialView.document_ir`` after the sweep's withheld…
- `class SweepResult` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 225)
  - `as_dict(self) -> dict[str, Any]` (line 230; public)
- `occupancy(connection: Any, view: Any) -> dict[tuple[str, str, str], int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 255) — Each capped bucket's occupancy, ``(bucket, LO, day) -> receipts``, counted over the receipts AD's material view sees (Codex verify F44, fix round 13): a receipt from withheld material is, for AD, a receipt never written, so it occupies no slot of a daily cap.
- `sweep(vault: Any, repository: Any, *, as_of: str, sweep_kind: str='serve', sweep_ref: str | None=None, reading_map: ReadingMap | None=None, clock: Clock | None=None, view: Any=None) -> SweepResult` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 317) — Record every listed opportunity written no later than ``as_of``.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 86)
- `MAPPING_VERSION` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 88)
- `KINDS` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 89)
- `PASSAGES_PER_LO_PER_DAY` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 90)
- `TUTOR_EXCHANGES_PER_LO_PER_DAY` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 91)
- `SOURCES` ([src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 95)

### Explicit exports

`__all__` declares:

- `EXPOSURE_CONTEXTS`
- `IN_PASSAGE_STYLES`
- `TUTOR_ANSWER_MODES`
- `UNKNOWN_ANSWER_MODE`
- `KINDS`
- `MAPPING_VERSION`
- `ReadingMap`
- `SOURCES`
- `SweepResult`
- `VaultReadingMap`
- `listed_events`
- `section_learning_objects`
- `sweep`

## Internal implementation anchors

- `_doses(reading_map: ReadingMap, lo_id: str, named: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 234)
- `_capped(kind: str, subkind: str) -> tuple[str, int] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 245) — A capped kind's occupancy bucket and its cap per LO and day (§5.11), or None.
- `_keys(connection: Any, event: _Event, lo_id: str, occupied: dict[tuple[str, str, str], int]) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 269) — The opportunity's key inside its cap, or None when the cap is full.
- `_taken_offers(connection: Any, view: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 296)
- `_offer_for(offers: Mapping[str, str], event: '_Event') -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading.py), line 306)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `sweep`; statically calls `sweep`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `VaultReadingMap`; statically calls `VaultReadingMap`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `VaultReadingMap`; statically calls `VaultReadingMap`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `VaultReadingMap`; statically calls `VaultReadingMap`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `sweep`; statically calls `sweep`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `sweep`; statically calls `sweep`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `section_learning_objects`; statically calls `section_learning_objects`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `taken_offers`; calls `taken_offers`
- [[Reference/Modules/learnloop/adaptive_difficulty/lessons|learnloop.adaptive_difficulty.lessons]] — imports `lesson_events`; calls `lesson_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/projection|learnloop.adaptive_difficulty.projection]] — imports `project_repository`; calls `project_repository`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `lesson_opportunities_on`; calls `lesson_opportunities_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `receipts_enabled`; calls `receipts_enabled`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `LEARNING_OPPORTUNITY_KINDS`, `LEARNING_OPPORTUNITY_SOURCES`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `has_table`, `insert_reading_opportunity`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `has_table`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `EXPOSURE_CONTEXTS`, `IN_PASSAGE_STYLES`, `ListedEvent`, `ReadingMap`, `SWEEP_OVERLAP`, `TUTOR_ANSWER_MODES`, `UNKNOWN_ANSWER_MODE`, `listed_events`, `source_stamp`; calls `listed_events`, `source_stamp`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `learning_objects_for_section_in_ir`, `learning_objects_for_span_in_ir`; calls `learning_objects_for_section_in_ir`, `learning_objects_for_span_in_ir`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_a_reader_tutor_exchange_is_recorded_under_its_answer_mode`
- [tests/test_ad1_reading_opportunities.py](../../../../../../tests/test_ad1_reading_opportunities.py) — direct import
  - `test_the_vault_map_reads_the_readers_own_section_rule`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_protected_receipt_occupies_no_daily_cap_slot`
  - `test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction`
  - `test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_withheld_items_facet_never_enters_the_facet_maps_or_the_reading_map`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_draw_reads_reading_recorded_since_the_last_serve`
  - `test_the_offer_names_the_sections_other_question_and_its_answer_is_the_extra`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_a_taken_extra_becomes_a_reading_opportunity_with_the_offer_id`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_reading_receipt_recorded_under_other_protection_is_mapped_again`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — direct import
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_marking_and_release_flip_the_epoch_and_the_reading_with_it`
  - `test_probe_candidates_are_taken_in_reading_order_not_span_id_order`
- [tests/test_ro2_ad_document_ir.py](../../../../../../tests/test_ro2_ad_document_ir.py) — direct import
  - `test_the_reading_map_answers_inside_the_operation_what_the_incumbent_answers_outside`
- [tests/test_ro2_ad_raw_document_reads.py](../../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_at_run_time_ad_loads_a_reading_only_through_its_chokepoint`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_an_anchor_mapped_inquiry_behind_the_recent_limit_is_missing_and_the_card_says_so`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_a_reread_past_ads_daily_dose_cap_is_an_intervening_exposure`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_carve_out_allowlist_is_the_sweeps_list_and_the_only_typed_value_is_the_verdict`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains reading within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/reading.py](../../../../../../src/learnloop/adaptive_difficulty/reading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

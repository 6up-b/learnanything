---
title: "learnloop.reading_sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reading_sources.py"
source_paths:
  - "src/learnloop/reading_sources.py"
source_commit: "2d4520e1fe11db97835f80cc5f280b51602c6954"
source_commit_timestamp: "2026-11-03T19:28:17-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.reading_sources module"
  - "src/learnloop/reading_sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.reading_sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reading_sources` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The list of Reader sources: every learning opportunity a source row records, and how to read it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py) |
| Source lines | 335 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d4520e1fe11db97835f80cc5f280b51602c6954` |
| Commit timestamp | `2026-11-03T19:28:17-05:00` |

## Public API

- `source_stamp(value: Any) -> str | None` ([source](../../../../../src/learnloop/reading_sources.py), line 43) — A source time in one sortable form (microseconds, ``Z``); None when unreadable.
- `class ReadingMap(Protocol)` ([source](../../../../../src/learnloop/reading_sources.py), line 55) — How a source row maps to LOs and facets (the Reader's own mapping).
  - `los_for_section(self, extraction_id: str, section_id: str) -> list[str]` (line 58; public)
  - `los_for_span(self, extraction_id: str, span_id: str) -> list[str]` (line 59; public)
  - `section_spans(self, extraction_id: str, section_id: str) -> list[str]` (line 60; public)
  - `worked_example_spans(self, extraction_id: str) -> set[str]` (line 61; public)
  - `withheld(self, extraction_id: str, span_id: str | None) -> bool` (line 62; public)
  - `los_for_note(self, note_id: str) -> list[str]` (line 63; public)
  - `lo_for_item(self, practice_item_id: str) -> str | None` (line 64; public)
  - `facets_for_lo(self, learning_object_id: str) -> list[str]` (line 65; public)
- `class ListedEvent` ([source](../../../../../src/learnloop/reading_sources.py), line 69)
- `listed_events(connection: Any, reading_map: Any, lower: str | None, upper: str, *, view: Any) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 312) — Every listed learning opportunity in the window, as ``reading_map`` and ``view`` see them: this list and its reading, with no receipt, no cap and no write.

### Module constants

- `TUTOR_ANSWER_MODES` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 22)
- `UNKNOWN_ANSWER_MODE` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 23)
- `IN_PASSAGE_STYLES` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 26)
- `SWEEP_OVERLAP` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 30)
- `SELF_CHECK_TASK` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 32)
- `SELF_CHECK_CLASSES` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 33)
- `EXPOSURE_CONTEXTS` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 38)
- `TUTOR_CONTEXTS` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 40)
- `_COLLECTORS` ([src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py), line 307)

### Explicit exports

`__all__` declares:

- `EXPOSURE_CONTEXTS`
- `IN_PASSAGE_STYLES`
- `ListedEvent`
- `ReadingMap`
- `SELF_CHECK_CLASSES`
- `SELF_CHECK_TASK`
- `SWEEP_OVERLAP`
- `TUTOR_ANSWER_MODES`
- `TUTOR_CONTEXTS`
- `UNKNOWN_ANSWER_MODE`
- `listed_events`
- `source_stamp`

## Internal implementation anchors

- `_in_window(stamp: str | None, lower: str | None, upper: str) -> bool` ([source](../../../../../src/learnloop/reading_sources.py), line 82)
- `_recorded(connection: Any, kind: str, subkind: str, table: str, source_id: str, *, view: Any) -> bool` ([source](../../../../../src/learnloop/reading_sources.py), line 86) — An earlier sweep recorded this source row: it is not mapped again (a serve's sweep re-reads its overlap window, never re-resolves it).
- `_section_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 96)
- `_exposure_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 128)
- `_named_facets(raw: Any) -> tuple[str, ...]` ([source](../../../../../src/learnloop/reading_sources.py), line 156)
- `_note_withheld(connection: Any, reading_map: Any, view: Any, note_id: str) -> bool` ([source](../../../../../src/learnloop/reading_sources.py), line 166) — A note's protection for the sweep: the map's own rule when it has one, else the view's (every note while the view is unavailable).
- `_tutor_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 175)
- `_question_los(reading_map: ReadingMap, extraction_id: str, section_id: str, anchors: Any) -> tuple[str, ...]` ([source](../../../../../src/learnloop/reading_sources.py), line 222)
- `_question_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 236)
- `_owner_placed_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 257)
- `_verdict_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str, view: Any=None) -> list[ListedEvent]` ([source](../../../../../src/learnloop/reading_sources.py), line 275)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `listed_events`, `source_stamp`; statically calls `listed_events`, `source_stamp`
- [[Reference/Modules/learnloop/adaptive_difficulty/lessons|learnloop.adaptive_difficulty.lessons]] — imports `ListedEvent`, `ReadingMap`, `source_stamp`; statically calls `ListedEvent`, `source_stamp`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `EXPOSURE_CONTEXTS`, `IN_PASSAGE_STYLES`, `ListedEvent`, `ReadingMap`, `SWEEP_OVERLAP`, `TUTOR_ANSWER_MODES`, `UNKNOWN_ANSWER_MODE`, `listed_events`, `source_stamp`; statically calls `listed_events`, `source_stamp`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `IN_PASSAGE_STYLES`, `TUTOR_ANSWER_MODES`, `UNKNOWN_ANSWER_MODE`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `SWEEP_OVERLAP`, `listed_events`, `source_stamp`; statically calls `listed_events`, `source_stamp`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/lessons|learnloop.adaptive_difficulty.lessons]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]], [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ro2_history_resolve.py](../../../../../tests/test_ro2_history_resolve.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]]
- [tests/test_ro4_codex_review.py](../../../../../tests/test_ro4_codex_review.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]]
- [tests/test_ad1_fix_round4.py](../../../../../tests/test_ad1_fix_round4.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad1_reading_opportunities.py](../../../../../tests/test_ad1_reading_opportunities.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_contract.py](../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_fix_r8.py](../../../../../tests/test_ad23_fix_r8.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_fix_review.py](../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad3_dose_arm.py](../../../../../tests/test_ad3_dose_arm.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_epoch.py](../../../../../tests/test_ad_epoch.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_guard.py](../../../../../tests/test_ad_guard.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_projection.py](../../../../../tests/test_ad_projection.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_protected_readings.py](../../../../../tests/test_ad_protected_readings.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]

## Modification guidance

- Make changes here when the responsibility remains reading sources within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reading_sources.py](../../../../../src/learnloop/reading_sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

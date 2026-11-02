---
title: "learnloop.db.stores.reader_cue_links"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/reader_cue_links.py"
source_paths:
  - "src/learnloop/db/stores/reader_cue_links.py"
source_commit: "758fec8241d0befbc095f69220952611b05e419b"
source_commit_timestamp: "2026-10-20T15:05:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.db.stores.reader_cue_links module"
  - "src/learnloop/db/stores/reader_cue_links.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.reader_cue_links`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.reader_cue_links` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW3b: ``passage_links`` and ``reader_cue_impressions`` (migration 215).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/reader_cue_links.py](../../../../../../../src/learnloop/db/stores/reader_cue_links.py) |
| Source lines | 196 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `758fec8241d0befbc095f69220952611b05e419b` |
| Commit timestamp | `2026-10-20T15:05:02-04:00` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 26)
- `insert_link(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 40) — Insert one pick; an identical (extraction, target, state, span) row already there is kept (the same paid answer recorded twice) and its id returned.
- `links_for_extraction(connection: sqlite3.Connection, extraction_id: str, state_keys: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 63) — The links on one extraction, optionally only those of these target states.
- `link_by_id(connection: sqlite3.Connection, link_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 79)
- `links_with_roles(connection: sqlite3.Connection, extraction_ids: Iterable[str], roles: Iterable[str]) -> set[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 85) — Spans RW3b's own judge proposed one of ``roles`` for (positive use only).
- `judged_left_ids(connection: sqlite3.Connection, task: str, left_kind: str, left_ids: Iterable[str]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 104) — Which target states the cue judge already judged (a verdict row exists, picks or not), so a source open never pays for them twice.
- `insert_impression(connection: sqlite3.Connection, row: Mapping[str, Any]) -> tuple[dict[str, Any], bool]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 124) — Record one (visit, cue) impression; the first one of a visit stands.
- `impression_for(connection: sqlite3.Connection, visit_id: str, cue_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 142)
- `record_response(connection: sqlite3.Connection, impression_id: str, *, response: str, text_hash: str | None, at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 149) — Write the learner's first response; a later one changes nothing.
- `shown_impressions(connection: sqlite3.Connection, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 159) — The cues shown on one extraction (every visit), each with its link's target when it has one: what "already shown this visit" is read from.
- `impressions(connection: sqlite3.Connection, *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 170)

### Module constants

- `LINK_COLUMNS` ([src/learnloop/db/stores/reader_cue_links.py](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 17)
- `IMPRESSION_COLUMNS` ([src/learnloop/db/stores/reader_cue_links.py](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 20)

### Explicit exports

`__all__` declares:

- `IMPRESSION_COLUMNS`
- `LINK_COLUMNS`
- `impression_for`
- `impressions`
- `insert_impression`
- `insert_link`
- `judged_left_ids`
- `link_by_id`
- `links_for_extraction`
- `links_with_roles`
- `record_response`
- `shown_impressions`
- `tables_present`

## Internal implementation anchors

- `_link(row: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 32)
- `_impression(row: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/reader_cue_links.py), line 118)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `module`; statically calls `insert_link`, `judged_left_ids`, `links_for_extraction`, `links_with_roles`, `shown_impressions`, `tables_present`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `impression_for`, `insert_impression`, `record_response`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/passage_cue_fakes.py](../../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/test_passage_links.py](../../../../../../../tests/test_passage_links.py) — direct import
  - `test_a_lost_link_write_is_recovered_from_the_paid_answer_without_paying_again`
- [tests/test_reader_cue_holdout.py](../../../../../../../tests/test_reader_cue_holdout.py) — direct import
- [tests/test_reader_cue_value.py](../../../../../../../tests/test_reader_cue_value.py) — direct import
- [tests/test_reader_rw3b_fix_round4.py](../../../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
- [tests/test_reader_rw3b_fix_round5.py](../../../../../../../tests/test_reader_rw3b_fix_round5.py) — direct import
- [tests/test_reader_rw3b_protection.py](../../../../../../../tests/test_reader_rw3b_protection.py) — direct import
  - `test_a_held_out_passage_never_reaches_the_judge_a_quote_or_a_cue`
  - `test_not_relevant_text_is_judge_feedback_never_learner_text`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_a_cached_try_first_tap_is_refused_once_try_first_is_switched_off_and_reloaded`
  - `test_a_held_out_cue_the_reader_would_have_spaced_out_is_recorded_as_spacing`
  - `test_a_tap_on_a_drawn_mark_does_not_rebuild_the_plan`
- [tests/test_reader_try_first.py](../../../../../../../tests/test_reader_try_first.py) — direct import
  - `test_pressing_try_first_is_a_learner_pick_that_opens_the_next_step_at_that_line`
- [tests/test_roles_switch_off.py](../../../../../../../tests/test_roles_switch_off.py) — direct import
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/reader_cue_links.py](../../../../../../../src/learnloop/db/stores/reader_cue_links.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

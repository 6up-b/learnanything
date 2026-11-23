---
title: "learnloop.companion.history"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/companion/history.py"
source_paths:
  - "src/learnloop/companion/history.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.companion"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.companion.history module"
  - "src/learnloop/companion/history.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-companion"
---

# `learnloop.companion.history`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.companion.history` exists within [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] to own the behavior summarized by its module contract: ``companion.history`` (spec §8.5, owner decision 2): every tutor exchange, by day and then desk, newest first, each with where it happened and the passage it was about.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py) |
| Source lines | 155 |
| Owning package | [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_exchange_context(repository: Any, *, question_event_id: str, surface: str, desk_id: str | None=None, window_spec: Mapping[str, Any] | None=None, pad_block_ids: list[str] | None=None, goal_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/companion/history.py), line 37) — Record where one exchange was asked (origin ``live``); a second record of it is ignored.
- `companion_history(repository: Any, *, date_from: str | None=None, date_to: str | None=None, desk_id: str | None=None, query: str | None=None, cursor: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/history.py), line 86)

### Module constants

- `PAGE_SIZE` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 27)
- `LIVE` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 28)
- `BACKFILL` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 29)
- `SURFACE_BY_CONTEXT` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 31)
- `WHERE` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 32)
- `_SENTENCE` ([src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py), line 34)

### Explicit exports

`__all__` declares:

- `BACKFILL`
- `LIVE`
- `PAGE_SIZE`
- `companion_history`
- `record_exchange_context`

## Internal implementation anchors

- `_first_sentence(text: str | None) -> str` ([source](../../../../../../src/learnloop/companion/history.py), line 51)
- `_local_day(stamp: str) -> str` ([source](../../../../../../src/learnloop/companion/history.py), line 59)
- `_day_start(day: str, *, days_after: int=0) -> str` ([source](../../../../../../src/learnloop/companion/history.py), line 64) — A local calendar day's first instant (or that of a day after it), in UTC, as stored stamps are.
- `_anchors(connection: Any, ids: list[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/companion/history.py), line 71) — Each exchange's passage: its selection if it has one, else its first citation, else its context.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/companion|learnloop_sidecar.handlers.companion]] — imports `companion_history`; statically calls `companion_history`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/span_projection_reads|learnloop.db.stores.span_projection_reads]] — imports `module`; calls `exchange_contexts`, `rows_for`
- [[Reference/Modules/learnloop/db/stores/span_projections|learnloop.db.stores.span_projections]] — imports `module`; calls `insert_exchange_context`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `delivered_answer_md`; calls `delivered_answer_md`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/companion|learnloop_sidecar.handlers.companion]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_reads.py](../../../../../../tests/test_reader_rd0_reads.py) — direct import
  - `test_history_groups_by_day_then_desk_newest_first_with_an_honest_origin`
  - `test_history_pages_by_cursor_and_reaches_every_exchange`

## Modification guidance

- Make changes here when the responsibility remains history within learnloop.companion; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/companion/history.py](../../../../../../src/learnloop/companion/history.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

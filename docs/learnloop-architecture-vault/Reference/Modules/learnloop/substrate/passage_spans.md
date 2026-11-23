---
title: "learnloop.substrate.passage_spans"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/passage_spans.py"
source_paths:
  - "src/learnloop/substrate/passage_spans.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.passage_spans module"
  - "src/learnloop/substrate/passage_spans.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.passage_spans`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.passage_spans` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: The two DERIVED span projections (spec §7.6): which passages each tutor exchange (``question_event_spans``) and each read learner text (``learner_text_gap_spans``) are tied to.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py) |
| Source lines | 373 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `located(value: Any, extraction_id: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 50) — The ``(reading, span)`` a citation-like value names, or None.
- `exchange_places(payload: Mapping[str, Any], *, subject_id: str, extraction_id: str) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 63) — Every ``(reading, span, role)`` one exchange names, in the order ``ask_provenance`` lists them.
- `question_event_rows(vault: Any, event: Mapping[str, Any], payloads: list[tuple[str, dict]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 180) — One exchange's rows.
- `project_question_event(connection: Any, vault: Any, question_event_id: str) -> int` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 219) — Write (or rewrite) one exchange's rows; returns how many were written.
- `rebuild_question_event_spans(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 230) — The replayer: clear the table, then project every exchange through the live recipe.
- `gap_rows(connection: Any, vault: Any, gap: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 258) — One read learner text's rows, by its source kind's recipe (spec §7.6's table).
- `project_gap(connection: Any, vault: Any, gap_id: str) -> int` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 312) — Write (or rewrite) one read learner text's rows; returns how many were written.
- `rebuild_learner_text_gap_spans(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 321) — The replayer: clear the table, then project every gap through the live recipe.
- `write_through_question_events(repository: Any, vault: Any, question_event_ids: Iterable[str]) -> None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 340) — Project new or answered exchanges at once.
- `write_through_gap(connection: Any, vault: Any, gap_id: str | None) -> None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 355) — Project a gap just written, in its writer's transaction (a savepoint of it: ``connection`` is the repository's atomic connection), so a failure leaves the gap row and is only logged.

### Module constants

- `LOG` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 37)
- `SELECTION` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 45)
- `CITED` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 46)
- `GIVEN` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 47)
- `EXACT_SELECTION` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 86)
- `CITATION` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 87)
- `SOURCE_CONTEXT` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 88)
- `UNANCHORED` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 89)
- `CONTEXT` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 90)
- `QUESTION_EVENT_SPANS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 92)
- `LEARNER_TEXT_GAP_SPANS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 93)
- `_ITEM_PLACED_GAP_KINDS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 96)
- `_GAP_COLUMNS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 309)

### Explicit exports

`__all__` declares:

- `CITED`
- `GIVEN`
- `SELECTION`
- `exchange_places`
- `located`
- `CITATION`
- `EXACT_SELECTION`
- `LEARNER_TEXT_GAP_SPANS`
- `QUESTION_EVENT_SPANS`
- `SOURCE_CONTEXT`
- `UNANCHORED`
- `gap_rows`
- `project_gap`
- `project_question_event`
- `question_event_rows`
- `rebuild_learner_text_gap_spans`
- `rebuild_question_event_spans`
- `write_through_gap`
- `write_through_question_events`

## Internal implementation anchors

- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 99)
- `_row(extraction_id: str | None, span_id: str | None, role: str, quality: str, learning_object_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 110)
- `_dedupe(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 116)
- `_span_key(note_id: Any) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 127)
- `_item_passages(vault: Any, item_id: str | None) -> tuple[list[tuple[str, str]], str | None]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 135) — An item's source passages (its canonical exercise and source refs) and its learning object.
- `_context_rows(places: list[tuple[str, str]], learning_object_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 151)
- `_reader_payloads(connection: Any, question_event_ids: Iterable[str] | None) -> dict[str, list[tuple[str, dict]]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 160) — Each exchange's ``reader_answer_submitted`` events, as (subject, payload), by question event id.
- `_question_events(connection: Any, ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 205)
- `_one(connection: Any, sql: str, params: Iterable[Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 248)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 254)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `write_through_gap`; statically calls `write_through_gap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `write_through_gap`; statically calls `write_through_gap`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `exchange_places`, `write_through_question_events`; statically calls `exchange_places`, `write_through_question_events`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_learner_text_gap_spans`, `rebuild_question_event_spans`; statically calls `rebuild_learner_text_gap_spans`, `rebuild_question_event_spans`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `write_through_question_events`; statically calls `write_through_question_events`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/span_projections|learnloop.db.stores.span_projections]] — imports `module`; calls `replace_rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_reads.py](../../../../../../tests/test_reader_rd0_reads.py) — direct import
  - `test_a_same_place_alias_is_flagged_never_shown_as_the_cited_text`
- [tests/test_reader_rd0_spans.py](../../../../../../tests/test_reader_rd0_spans.py) — direct import
  - `test_a_hidden_note_link_places_nothing`
  - `test_a_practice_question_is_projected_as_the_tutor_records_it`
  - `test_a_rebuild_from_empty_tables_reproduces_the_live_rows_and_is_idempotent`
  - `test_the_live_projection_equals_a_rebuild_for_every_adapter`

## Modification guidance

- Change passage spans policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

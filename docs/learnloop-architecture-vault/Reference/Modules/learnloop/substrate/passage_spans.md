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
| Source lines | 434 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `located(value: Any, extraction_id: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 50) — The ``(reading, span)`` a citation-like value names, or None.
- `exchange_places(payload: Mapping[str, Any], *, subject_id: str, extraction_id: str) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 63) — Every ``(reading, span, role)`` one exchange names, in the order ``ask_provenance`` lists them.
- `question_event_rows(vault: Any, event: Mapping[str, Any], payloads: list[tuple[str, dict]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 189) — One exchange's rows.
- `project_question_event(connection: Any, vault: Any, question_event_id: str) -> int` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 236) — Write (or rewrite) one exchange's rows; returns how many were written.
- `rebuild_question_event_spans(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 247) — The replayer: clear the table, then project every exchange through the live recipe.
- `gap_rows(connection: Any, vault: Any, gap: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 275) — One read learner text's rows, by its source kind's recipe (spec §7.6's table).
- `project_gap(connection: Any, vault: Any, gap_id: str) -> int` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 340) — Write (or rewrite) one read learner text's rows; returns how many were written.
- `rebuild_learner_text_gap_spans(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 349) — The replayer: clear the table, then project every gap through the live recipe.
- `initialize_on_open(vault: Any, repository: Any, *, clock: Any=None) -> dict[str, int] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 368) — Project every exchange and gap once, the first time a vault opens with these tables.
- `write_through_question_events(repository: Any, vault: Any, question_event_ids: Iterable[str]) -> None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 400) — Project new or answered exchanges at once.
- `write_through_gap(connection: Any, vault: Any, gap_id: str | None) -> None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 415) — Project a gap just written, in its writer's transaction (a savepoint of it: ``connection`` is the repository's atomic connection), so a failure leaves the gap row and is only logged.

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
- `READER_ANSWER_QUESTION_KEY` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 93)
- `FIGURE_EXPLANATION_SUFFIX` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 95)
- `QUESTION_EVENT_SPANS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 97)
- `LEARNER_TEXT_GAP_SPANS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 98)
- `_ITEM_PLACED_GAP_KINDS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 101)
- `_GAP_COLUMNS` ([src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py), line 337)

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
- `FIGURE_EXPLANATION_SUFFIX`
- `READER_ANSWER_QUESTION_KEY`
- `initialize_on_open`
- `gap_rows`
- `project_gap`
- `project_question_event`
- `question_event_rows`
- `rebuild_learner_text_gap_spans`
- `rebuild_question_event_spans`
- `write_through_gap`
- `write_through_question_events`

## Internal implementation anchors

- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 104)
- `_row(extraction_id: str | None, span_id: str | None, role: str, quality: str, learning_object_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 115)
- `_dedupe(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 121)
- `_span_key(note_id: Any) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 132)
- `_item_passages(vault: Any, item_id: str | None) -> tuple[list[tuple[str, str]], str | None]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 140) — An item's source passages (its canonical exercise and source refs) and its learning object.
- `_context_rows(places: list[tuple[str, str]], learning_object_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 156)
- `_reader_payloads(connection: Any, question_event_ids: Iterable[str] | None) -> dict[str, list[tuple[str, dict]]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 165) — Each exchange's ``reader_answer_submitted`` events, as (subject, payload), by question event id.
- `_question_events(connection: Any, ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 214)
- `_payloads_of(connection: Any, event: Mapping[str, Any]) -> list[tuple[str, dict]]` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 228) — A Reader exchange's answer events; any other exchange has none, so none is looked up.
- `_one(connection: Any, sql: str, params: Iterable[Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 265)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/substrate/passage_spans.py), line 271)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]] — imports `READER_ANSWER_QUESTION_KEY`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `write_through_gap`; statically calls `write_through_gap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `write_through_gap`; statically calls `write_through_gap`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `exchange_places`, `write_through_question_events`; statically calls `exchange_places`, `write_through_question_events`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_learner_text_gap_spans`, `rebuild_question_event_spans`; statically calls `rebuild_learner_text_gap_spans`, `rebuild_question_event_spans`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `write_through_question_events`; statically calls `write_through_question_events`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `initialize_on_open`; statically calls `initialize_on_open`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/span_projections|learnloop.db.stores.span_projections]] — imports `module`; calls `initialized`, `record_initialization`, `replace_rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_guards_migration.py](../../../../../../tests/test_reader_rd0_guards_migration.py) — direct import
  - `test_one_exchanges_answer_lookup_uses_the_index`
- [tests/test_reader_rd0_reads.py](../../../../../../tests/test_reader_rd0_reads.py) — direct import
  - `test_a_same_place_alias_is_flagged_never_shown_as_the_cited_text`
- [tests/test_reader_rd0_spans.py](../../../../../../tests/test_reader_rd0_spans.py) — direct import
  - `test_a_figure_prediction_gap_is_placed_on_its_figures_passages`
  - `test_a_note_link_changed_after_the_gap_was_read_keeps_live_equal_to_rebuild`
  - `test_a_note_link_hidden_before_the_gap_was_read_places_nothing`
  - `test_a_practice_question_is_projected_as_the_tutor_records_it`
  - `test_a_rebuild_from_empty_tables_reproduces_the_live_rows_and_is_idempotent`
  - `test_projecting_a_practice_question_reads_no_reader_answer`
  - `test_the_explanation_suffix_is_the_gap_pipelines`
  - `test_the_live_projection_equals_a_rebuild_for_every_adapter`
- [tests/test_reader_rd3a_companion_ask.py](../../../../../../tests/test_reader_rd3a_companion_ask.py) — direct import
  - `test_the_exchange_context_is_recorded_and_its_passages_equal_a_rebuild`

## Modification guidance

- Change passage spans policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/passage_spans.py](../../../../../../src/learnloop/substrate/passage_spans.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.source_retrieval.reader_tutor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/reader_tutor.py"
source_paths:
  - "src/learnloop/source_retrieval/reader_tutor.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.source_retrieval.reader_tutor module"
  - "src/learnloop/source_retrieval/reader_tutor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.reader_tutor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.reader_tutor` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader workbench RW1c: the Reader context's span provider (spec_reader_workbench_v1 §4.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py) |
| Source lines | 605 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `learner_query(question_md: str, *, ancestors: Sequence[Mapping[str, Any]]=()) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 87) — The learner's own part of the tutor's query: the question and its latest ancestors' questions, whitespace-normalized (never withheld; cut at the query's limit as before).
- `reader_query(question_md: str, *, ancestors: Sequence[Mapping[str, Any]]=(), gaps: Sequence[Mapping[str, Any]]=()) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 100) — The tutor's own query: the question, its latest ancestors' questions and (personalized) the open-gap statements, within ``QUERY_CHARS``.
- `another_way_label(hits: Sequence[Mapping[str, Any]], shown_sources: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 130) — How "another way"'s passages differ from what the inquiry showed.
- `class ReaderLookup` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 144) — One Reader question's retrieval, bound by the adapter (``ReaderTutorRequest.retrieve``).
  - `query(self, gaps: Sequence[Mapping[str, Any]] | None=None) -> str` (line 176; public) — The tutor's own query, from these gap statements (default: as read).
  - `learner_query(self) -> str` (line 182; public) — The learner's own part of the query (the plan fits the rest to it when bound).
  - `__call__(self, inputs: Mapping[str, Any] | None=None) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]` (line 187; internal)
  - `_admitted(self, hits: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]` (line 245; internal) — The hits that may reach the tutor: never held-out material; item-bound, never an exercise or solution lead nor a passage reproducing the item's answer (``find_sources`` already applied the policy's scope; this is the second guard).
- `class ItemBoundGuard` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 274) — T6's item-bound exclusions over every span the tutor would be given (Codex review F3): the passages linked to the item (``item_exclusions``: its own worked answer, whatever the relation), every exercise and solution block (by lead and by effective role) and every passage that re…
  - `__call__(self, spans: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]` (line 286; internal)
  - `text_leaks(self, text: str) -> bool` (line 313; public) — The guard's check for one model-written or source text that is not a block (fix round 5, R2: an earlier answer in the thread, a line of the learner-work context): it leads as a solution or reproduces the item's answer.
  - `text_overlap(self, text: str) -> float` (line 329; public) — The same matcher's score for one text (fix round 6, R1): how much of the item's answer it exposes, a solution lead counting as all of it.
- `inquiry_exchanges(exchanges: Sequence[Mapping[str, Any]], exchange_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 352) — Every exchange of the inquiry ``exchange_id`` belongs to (its root's tree), oldest first.
- `shown_span_keys(exchanges: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 376) — Every passage an inquiry has shown: each exchange's selection, citations, excerpt and the passages its tutor retrieved.
- `offer_shown_span_keys(repository: Repository, exchanges: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 403) — The passages the inquiry's offers showed (Codex review F7): the exposure rows a pressed passage or comparison offer wrote (``record_source_offer_shown``: entity ``source_tool_call``, a request the tutor made from one of these questions) and the excerpts' own rows (entity ``quest…
- `shown_source_ids(repository: Repository, keys: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 432) — The sources the shown passages belong to (for "from a different book").
- `named_gap_hypotheses(repository: Repository, exchanges: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 445) — The gaps learner-text gaps named from the inquiry's questions, as ``target_hypotheses`` (``named_gap`` refs the sources service resolves).
- `passage_learning_objects(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_ids: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 466) — The passage's learning objects: its section's provenance-linked LOs (RW4a's anchor), else the LOs whose current source links name one of its blocks (``entity_source_links``, ``primary`` or ``support``).
- `learner_work(vault: LoadedVault, repository: Repository, learning_object_ids: Sequence[str], *, gaps: Sequence[Mapping[str, Any]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 490) — The learner's open questions (statements, labelled LearnLoop's reading) and most recent workbench steps (their own words) on these LOs: the same class of data the hint writer already sends (spec §5.8).
- `next_step_buttons(repository: Repository, *, extraction_id: str, cited: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 541) — "Try the next step first" on each cited block of the open source that is a derivation or a worked example (RW1b's next-step question at that line).
- `explorable_buttons(repository: Repository, *, extraction_id: str, explorable: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 560) — RW5b: "make this explorable" on each block of the open source the tutor judged explorable (the answer view's ``explorable``) that is an equation or a figure.
- `citation_dicts(raw: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 573) — Citations as plain dicts whatever their stored shape.

### Module constants

- `READER_INTENTS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 62)
- `QUERY_ANCESTORS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 64)
- `QUERY_GAPS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 67)
- `QUERY_CHARS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 68)
- `BOUND_QUERY_CHARS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 73)
- `NEXT_STEP_ROLES` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 76)
- `FROM_ANOTHER_BOOK` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 78)
- `WORKED_EXAMPLE_INSTEAD` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 79)
- `SAME_BOOK_OTHER_PASSAGE` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 80)
- `VERIFIED` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 82)
- `WORK_STEPS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 84)
- `SELECTION_RELATIONS` ([src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 270)

### Explicit exports

`__all__` declares:

- `FROM_ANOTHER_BOOK`
- `ItemBoundGuard`
- `NEXT_STEP_ROLES`
- `READER_INTENTS`
- `ReaderLookup`
- `SAME_BOOK_OTHER_PASSAGE`
- `WORKED_EXAMPLE_INSTEAD`
- `another_way_label`
- `citation_dicts`
- `inquiry_exchanges`
- `learner_work`
- `named_gap_hypotheses`
- `explorable_buttons`
- `next_step_buttons`
- `offerable_blocks`
- `offer_shown_span_keys`
- `passage_learning_objects`
- `reader_query`
- `shown_source_ids`
- `shown_span_keys`

## Internal implementation anchors

- `_span(hit: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 119)
- `_delivered(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 340) — ``text`` unchanged, after checking it is the canonical, delivered form.
- `_latest_session(repository: Repository, item_ids: Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/reader_tutor.py), line 516)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `passage_learning_objects`; statically calls `passage_learning_objects`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `passage_learning_objects`; statically calls `passage_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `shown_span_keys`; statically calls `shown_span_keys`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `NEXT_STEP_ROLES`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `module`; statically calls `ItemBoundGuard`, `ReaderLookup`, `explorable_buttons`, `inquiry_exchanges`, `learner_work`, `named_gap_hypotheses`, `next_step_buttons`, `offer_shown_span_keys`, `passage_learning_objects`, `shown_source_ids`, `shown_span_keys`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_material`; calls `held_out_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `offerable_blocks`; calls `offerable_blocks`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `lead_role`; calls `lead_role`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]] — imports `named_gaps`; calls `named_gaps`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `live_steps`; calls `live_steps`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `block_roles`, `item_exclusions`; calls `block_roles`, `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `QUESTION_CHARS`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `anchor_learning_objects`, `open_questions`; calls `anchor_learning_objects`, `open_questions`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `MAX_QUERY_CHARS`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `ITEM_BOUND_LEAD_ROLES`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `verification_route`; calls `verification_route`
- [[Reference/Modules/learnloop/text_canon|learnloop.text_canon]] — imports `canonical`; calls `canonical`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `module`; calls `open_question_work`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`, `span_leaks_expected`; calls `span_answer_overlap`, `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_placeholder_the_key_matches_is_replaced_by_nothing`
  - `test_every_sent_model_written_fragment_was_checked`
  - `test_the_guard_reads_only_delivered_text`
  - `test_the_learners_question_is_truncated_as_before`
  - `test_unbound_queries_are_built_as_before`

## Modification guidance

- Make changes here when the responsibility remains reader tutor within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/reader_tutor.py](../../../../../../src/learnloop/source_retrieval/reader_tutor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

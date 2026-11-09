---
title: "learnloop.reader.source_objects"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_objects.py"
source_paths:
  - "src/learnloop/reader/source_objects.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.source_objects module"
  - "src/learnloop/reader/source_objects.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_objects`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_objects` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Source-object layer + relations + canonical mapping proposals (spec §7, design B step 7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py) |
| Source lines | 529 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SourceObjectError(ValueError)` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 41) — Domain error for the source-object service.
- `author_source_object(repository: Repository, *, source_id: str, revision_id: str, object_type: str, exact_text: str='', content: Mapping[str, Any] | None=None, citations: list[Mapping[str, Any]] | None=None, authorship: str='ai', status: str='proposed', authorial_role: str | None=None, salience_proposal: float | None=None, model_provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 45) — Author a new source object (version 1).
- `append_proposal_version(repository: Repository, *, source_object_id: str, revision_id: str, object_type: str, content: Mapping[str, Any], citations: list[Mapping[str, Any]], authorial_role: str | None=None, exact_text: str='', model_provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 86) — Append a further AI proposal version to a ``proposed`` object (Reader RW4e: a second judge proposing the same instructional role on the same passage, so agreement between judges is visible).
- `review_source_object(repository: Repository, *, source_object_id: str, status: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 128) — Append a review status successor (``reviewed`` / ``rejected`` / ``superseded``).
- `link_relation(repository: Repository, *, source_object_id: str, related_object_id: str | None=None, relation_type: str=CONNECT_IT_RELATION, learner_text: str | None=None, authorship: str='learner', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 144) — Create a versioned relation between source objects.
- `supersede_relation(repository: Repository, *, relation_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 167) — Mark a relation ``superseded`` by appending its successor version (the same endpoints, type, wording and authorship; ``version_ordinal + 1``): relations are versioned and append-only, so nothing is updated or deleted (Reader RW4d's *remove*, spec_reader_workbench_v1 §7.8).
- `propose_mapping(repository: Repository, *, target_kind: str, source_object_id: str | None=None, annotation_id: str | None=None, target_ref: str | None=None, confidence: float | None=None, rationale: str | None=None, provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 184) — Append a canonical mapping proposal (§7.3).
- `accept_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 209)
- `reject_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 216) — Rejecting a mapping never deletes the annotation or suppresses alternatives (§7.3).
- `withheld_source_objects(vault: Any, repository: Repository, heads: Sequence[Mapping[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 225) — The ids among ``heads`` whose material is exam or held out **now** (exam protection's one predicate, ``exam_material``), read from each object's own provenance: every citation's span on the reading it was made on, on its book's current reading and on every reading of its revisio…
- `comparison_passages(repository: Repository, comparison_id: str, *, ask_id: str | None=None, question_event_id: str | None=None, ask_ids: Sequence[str]=(), question_event_ids: Sequence[str]=(), passages: Sequence[Any]=()) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 318) — Every passage that contributed to a stored comparison, as the **union across its reuse** (Codex verify of RW4d fix round 4, F1): * the stored comparison: its compared sources, counterparts, unverified sources and dropped pins, its own ``caller_ref`` (a tutor question; for the Re…
- `withheld_comparisons(vault: Any, repository: Repository, comparisons: Sequence[tuple[str, str | None]], *, question_event_ids: Sequence[str]=(), passages: Sequence[Any]=()) -> frozenset[tuple[str, str | None]]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 440) — The ``(comparison id, ask id)`` pairs with **any** contributing passage (:func:`comparison_passages`) that is exam or held out now.
- `hidden_source_objects(vault: Any, repository: Repository, heads: Sequence[Mapping[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 491) — The ids among ``heads`` no reader returns: an object whose own material is withheld (:func:`withheld_source_objects`), and every object kept from a comparison that is withheld whole (:func:`withheld_comparisons`).
- `source_objects_for_source(vault: Any, repository: Repository, *, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 505) — A book's source objects (each head version with its citations), without any whose material is exam or held out now, or that was kept from a comparison withheld whole (:func:`hidden_source_objects`): their exact text, content, lines, quotes and citations are never returned.
- `proposal_inbox(vault: Any, repository: Repository, *, status: str='proposed', source_object_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 517) — Non-modal review inbox (§6.4): accumulated proposals reviewed without losing reading position.

### Module constants

- `OBJECT_TYPES` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 26)
- `RELATION_TYPES` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 30)
- `MAPPING_TARGET_KINDS` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 34)
- `CONNECT_IT_RELATION` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 38)

## Internal implementation anchors

- `_span_key(value: Any) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 285)
- `_question_passages(repository: Repository, question_event_id: str) -> list[Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 297) — The passages a tutor question was asked from: its passage and the spans it was given.
- `_comparison_of(head: Mapping[str, Any]) -> tuple[str, str | None] | None` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 476) — The comparison an object was kept from, ``("", None)`` when it claims one it does not name (unresolvable), None for any other object.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `module`; statically calls `withheld_comparisons`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; statically calls `author_source_object`, `propose_mapping`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; statically calls `append_proposal_version`, `author_source_object`, `hidden_source_objects`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; statically calls `author_source_object`, `comparison_passages`, `link_relation`, `review_source_object`, `supersede_relation`, `withheld_comparisons`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `withheld_comparisons`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `accept_mapping`, `link_relation`, `proposal_inbox`, `reject_mapping`, `review_source_object`, `source_objects_for_source`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `CitationResolver`; calls `CitationResolver`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/library_asks|learnloop.db.stores.library_asks]] — imports `module`; calls `ask_row`, `asks_referencing_comparison`, `kept_row`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `existing_spans`, `source_extraction_ids`; calls `existing_spans`, `source_extraction_ids`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `REUSE_QUESTIONS_KEY`, `comparison_row`, `tool_requests_for_result`; calls `comparison_row`, `tool_requests_for_result`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]], [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]], [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]], [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_an_unreadable_comparison_is_withheld_whole`
  - `test_source_objects_fail_closed`
- [tests/test_find_sources_intents.py](../../../../../../tests/test_find_sources_intents.py) — direct import
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_f3_a_reviewed_copy_keeps_its_citations_origin`
  - `test_f3_reviewing_a_legacy_citation_after_a_reread_keeps_what_it_cites`
- [tests/test_roles_concurrency.py](../../../../../../tests/test_roles_concurrency.py) — direct import
  - `test_a_review_between_a_judges_read_and_its_write_stands`
  - `test_a_review_that_won_the_lock_first_takes_no_further_proposal`
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import
- [tests/test_source_objects.py](../../../../../../tests/test_source_objects.py) — direct import
  - `test_author_begins_proposed_and_review_is_append_only`
  - `test_connect_it_relation_defaults_to_learner_connects_proposal`
  - `test_mapping_proposal_accept_and_reject_are_non_destructive`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_a_proposal_held_out_later_is_never_returned`
  - `test_a_reviewed_or_rejected_proposal_takes_no_further_version`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
  - `test_rw4d_followup_an_agent_callers_comparison_is_not_withheld_as_unresolvable`
  - `test_rw4d_followup_find_sources_compare_intent_applies_the_rule`
  - `test_rw4d_followup_the_rule_fails_closed_on_the_direct_rpc`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_a_cached_tutor_comparison_checks_the_current_questions_passage`
  - `test_f1_a_reuses_pin_naming_no_passage_is_not_persisted`
  - `test_f1_rereview_a_direct_tutor_reuse_persists_its_question_for_later_readers`
  - `test_f1_rereview_a_reuse_for_an_unknown_question_is_not_persisted`
  - `test_f1_the_reuses_dropped_pin_is_persisted_for_later_reads`
  - `test_nov1_open_item_3_a_fresh_comparisons_pin_naming_no_passage_is_not_persisted`

## Modification guidance

- Change source objects policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

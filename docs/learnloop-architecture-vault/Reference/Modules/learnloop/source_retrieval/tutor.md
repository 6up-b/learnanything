---
title: "learnloop.source_retrieval.tutor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/tutor.py"
source_paths:
  - "src/learnloop/source_retrieval/tutor.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.source_retrieval.tutor module"
  - "src/learnloop/source_retrieval/tutor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.tutor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.tutor` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Question-dependent tutor spans (Slice 2 T6), injected into ``tutor_qa``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py) |
| Source lines | 556 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `step_timings(search_timings: dict[str, int], *, verification_ms: int, total_ms: int) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 83) — Per-step wall times: retrieval is the search minus its paid steps.
- `over_soft_deadline(timings: dict[str, int], seconds: float) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 96) — The steps (``total`` included) whose wall time exceeded the soft deadline.
- `span_context(hit: SpanHit, *, complete: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 107) — A verified span in the tutor's ``source_spans`` shape: the complete canonical block (``tutor_qa.context_token_budget`` is the only bound), or with ``complete`` false (``tutor_qa.expanded_delivery``, the kill switch) the predecessor's ``SPAN_TEXT_CAP`` characters of its collapsed…
- `reference_filter(vault: LoadedVault, repository: Repository, scope: Scope, *, item: PracticeItem | None) -> BlockFilter` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 130) — The rules a cited numbered block passes to join a retrieved, pinned or linked span: inside the span's scope (an item-bound scope already leaves out the item's passages and the exercise and solution blocks its role hints name), never exam material, and with an ``item`` (practice,…
- `linked_reference_filter(vault: LoadedVault, repository: Repository, *, context: str, learning_object_ids: Sequence[str], item: PracticeItem | None) -> BlockFilter` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 162) — The rules a numbered block cited by a learning object's linked span passes (the tutor's fallback when retrieval keeps the linked spans; injected by the adapter as ``ask_question(linked_reference_filter=...)``).
- `with_references(vault: LoadedVault, repository: Repository, spans: list[dict[str, Any]], scope: Scope, *, item: PracticeItem | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 193) — ``spans`` and the numbered blocks they cite (``referenced``), with what was followed for the manifest (None when nothing was cited or the ``tutor_qa.resolve_references`` kill switch is off).
- `class TutorPool` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 216) — The candidates the tutor's verification judges, and how they were found.
- `tutor_scope(vault: LoadedVault, repository: Repository, *, context: str, learning_object_ids: Sequence[str], item: PracticeItem | None) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 228) — The scope the tutor's pool searches for one question: the teaching scope of its LOs, with the item's exclusions in a practice or feedback context.
- `tutor_pool(vault: LoadedVault, repository: Repository, *, context: str, question_md: str, learning_object_ids: Sequence[str], item: PracticeItem | None, embedder: Any | None=None, rewrite_client: Any | None=None, owner_id: str='', deadline: float | None=None, query_vectors: Mapping[str, Any] | None=None, rewrite: bool | None=None, rewritten: Rewrite | None=None, pool: str | None=None, pool_extras: int | None=None, extra_lists: Mapping[str, Sequence[SpanKey]] | None=None, scope: Scope | None=None) -> TutorPool` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 240) — The tutor's candidate pool for one question (steps 1 and its withholding).
- `class TutorSpanProvider` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 320) — ``(vault, repository, *, context, question_md, learning_object_ids, item)`` -> ``(spans or None, manifest or None)``.
  - `__init__(self, *, embedder: Any | None=None, rewrite_client: Any | None=None, rerank_client: Any | None=None, clock: Clock | None=None, intent_for: Any | None=None) -> None` (line 325; internal)
  - `__call__(self, vault: LoadedVault, repository: Repository, *, context: str, question_md: str, learning_object_ids: Sequence[str], item: PracticeItem | None) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]` (line 337; internal)
  - `_remediate(self, vault: LoadedVault, repository: Repository, *, question_md: str, pool: list[SpanHit], intent: dict[str, Any], item: PracticeItem | None, search: SpanSearch, withheld: list[str], owner_id: str, ready: Any, deadline: float | None, started: float, scope: Scope) -> tuple[Any, dict[str, Any]]` (line 416; internal) — The remediate intent: same retrieval, the intent's verification prompt (no extra call).
- `class PinnedSpanProvider` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 479) — "Explain this with my work" (canonical sources S4, §10.3): the tutor is grounded in the passages the learner chose, through the same filters any retrieved span passes (an item-bound question never receives an exercise, a solution, a span linked to its item or one that reproduces…
  - `__init__(self, span_keys: Sequence[Any], *, cold: bool=False) -> None` (line 487; internal)
  - `__call__(self, vault: LoadedVault, repository: Repository, *, context: str, question_md: str, learning_object_ids: Sequence[str], item: PracticeItem | None) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]` (line 491; internal)

### Module constants

- `PROVENANCE_SPANS_PER_LO` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 73)
- `ITEM_BOUND_CONTEXTS` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 75)
- `WITHHOLD_SPARE` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 78)
- `TIMED_STEPS` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 80)
- `SPAN_TEXT_CAP` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 104)
- `ITEM_BOUND_LEAD_ROLES` ([src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py), line 127)

### Explicit exports

`__all__` declares:

- `ITEM_BOUND_CONTEXTS`
- `ITEM_BOUND_LEAD_ROLES`
- `PROVENANCE_SPANS_PER_LO`
- `PinnedSpanProvider`
- `SPAN_TEXT_CAP`
- `TIMED_STEPS`
- `TutorPool`
- `TutorSpanProvider`
- `WITHHOLD_SPARE`
- `linked_reference_filter`
- `over_soft_deadline`
- `reference_filter`
- `span_context`
- `step_timings`
- `tutor_pool`
- `tutor_scope`
- `with_references`

## Internal implementation anchors

- `_delivered(vault: LoadedVault, repository: Repository, search: SpanSearch, picks: list[SpanHit]) -> list[SpanHit]` ([source](../../../../../../src/learnloop/source_retrieval/tutor.py), line 469) — The verified spans the tutor is given, recorded as this consumer's delivery in their final order (local contextual retrieval P1, Codex review F9; nothing is logged while no new embedding space is on).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `tutor_pool`; statically calls `tutor_pool`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `ITEM_BOUND_CONTEXTS`, `TutorPool`, `tutor_pool`, `tutor_scope`; statically calls `tutor_pool`, `tutor_scope`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `ITEM_BOUND_LEAD_ROLES`
- [[Reference/Modules/learnloop/source_retrieval/timing|learnloop.source_retrieval.timing]] — imports `TIMED_STEPS`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `TutorSpanProvider`; statically calls `TutorSpanProvider`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `PinnedSpanProvider`; statically calls `PinnedSpanProvider`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `PinnedSpanProvider`, `TutorSpanProvider`, `linked_reference_filter`; statically calls `PinnedSpanProvider`, `TutorSpanProvider`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `lead_role`; calls `lead_role`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `exam_withheld`, `teaching_scope`; calls `exam_withheld`, `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `deliver`; calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `_verify`, `correction_lists`, `scope_for`, `span_keys`; calls `_verify`, `correction_lists`, `scope_for`, `span_keys`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `Rewrite`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `SpanHit`, `SpanKey`, `SpanSearch`, `search_spans`; calls `SpanHit`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `practice_question`, `verification_route`, `verify_spans`; calls `practice_question`, `verification_route`, `verify_spans`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockFilter`, `BlockSource`, `SPAN_CHARS`, `follow_references`, `predecessor_cut`; calls `BlockSource`, `follow_references`, `predecessor_cut`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]], [[Reference/Modules/learnloop/source_retrieval/timing|learnloop.source_retrieval.timing]], [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_locks_landing.py](../../../../../../tests/test_facet_locks_landing.py) — direct import
  - `test_a_pinned_passage_in_a_held_out_textbook_unit_never_grounds_the_tutor`
- [tests/test_pinned_span_bridge.py](../../../../../../tests/test_pinned_span_bridge.py) — direct import
  - `test_pinned_spans_pass_the_policys_filters`
  - `test_the_bridge_is_a_normal_tutor_question_with_the_draft`
- [tests/test_prescription_passages.py](../../../../../../tests/test_prescription_passages.py) — direct import
  - `test_the_tutor_provider_verifies_with_the_remediate_prompt`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_a_workbench_session_asks_as_its_items_practice`
- [tests/test_sidecar_source_retrieval.py](../../../../../../tests/test_sidecar_source_retrieval.py) — direct import
  - `test_ask_tutor_question_injects_the_source_span_provider`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
  - `test_a_codex_that_is_not_ready_buys_no_retrieval_for_the_tutor`
  - `test_an_exhausted_codex_leaves_the_tutor_on_its_linked_spans`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_every_tutor_step_is_timed_and_a_slow_step_is_flagged_not_cancelled`
  - `test_sources_report_gives_p50_and_p90_per_step_and_counts_truncations`
  - `test_the_hybrid_pool_option_keeps_todays_tutor_pool`
  - `test_the_live_rewrite_and_verification_ask_for_low_reasoning_effort`
  - `test_the_tutor_verifies_the_dense_pool_widened_by_bm25_and_linked_spans`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_nothing_is_paid_for_when_verification_cannot_run`
  - `test_the_practice_question_is_never_the_retrieval_query`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_a_slow_verification_runs_out_of_time_when_the_time_box_is_restored`
  - `test_no_paid_step_starts_after_the_time_box`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_pinned_exam_passage_never_grounds_the_tutor`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_the_report_verifies_the_tutors_own_pool_with_its_item_in_context`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_pinned_passage_arrives_whole_with_the_theorem_it_cites`
  - `test_a_retrieved_spans_reference_to_an_exercise_caption_is_refused_while_practising`
  - `test_an_exercise_continuing_a_cited_theorem_is_cut_while_practising`
  - `test_the_sidecar_injects_the_linked_reference_rules`

## Modification guidance

- Make changes here when the responsibility remains tutor within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/tutor.py](../../../../../../src/learnloop/source_retrieval/tutor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

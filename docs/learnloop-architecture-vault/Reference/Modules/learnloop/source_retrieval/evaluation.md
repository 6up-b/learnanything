---
title: "learnloop.source_retrieval.evaluation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/evaluation.py"
source_paths:
  - "src/learnloop/source_retrieval/evaluation.py"
source_commit: "29919610d941c1159450a6d4b064171c42551f4f"
source_commit_timestamp: "2026-10-14T01:06:20-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.evaluation module"
  - "src/learnloop/source_retrieval/evaluation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.evaluation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.evaluation` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The T6 report: source retrieval vs today's substring search (suite ``source_retrieval``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py) |
| Source lines | 1086 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `29919610d941c1159450a6d4b064171c42551f4f` |
| Commit timestamp | `2026-10-14T01:06:20-04:00` |

## Public API

- `class Seed` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 166)
  - `seed_id(self) -> str` (line 174; public)
  - `keys(self) -> list[tuple[str, str]]` (line 179; public)
  - `writer_text(self) -> str | tuple[str, str]` (line 183; public)
- `class LoggedQuestion` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 188)
- `class TutorQuestion` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 197) — How the tutor would be asked one benchmark question (review F5).
  - `describe(self) -> dict[str, Any]` (line 212; public)
- `class EvalData` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 218)
  - `seeds_of(self, qtype: str) -> list[Seed]` (line 227; public)
- `type_counts(generated: int) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 252) — Generated questions per type: an even split, the remainder to the first types.
- `verification_metrics(pool: Sequence[str], picks: Sequence[str], pick_at_most: int, labels: Mapping[str, Sequence[str | None]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 348) — How good the picked spans are, against the labels of the whole pool.
- `summarize_verification(per_question: Sequence[Mapping[str, Any]], systems: Sequence[str], comparisons: Sequence[tuple[str, str]]=VERIFY_COMPARISONS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 381) — Per verification system: what the tutor would get, and paired differences.
- `class SourceRetrievalSuite` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 419)
  - `load(self, vault: LoadedVault, request: Any) -> EvalData` (line 425; public)
  - `passage_bound(vault: LoadedVault, scope: Scope) -> int` (line 450; public) — The most characters one judged passage can have here: the passage budget, or the scope's longest block when that is shorter.
  - `plan(self, vault: LoadedVault, data: EvalData, request: Any) -> dict[str, Any]` (line 468; public)
  - `verify_pool_bound(system: str, config: Any) -> int` (line 521; public) — Most candidates a verification system's tutor pool can hold: the dense (or fused) top ``tutor_candidate_pool``, and for ``pool_verify`` at most ``pool_keyword_extras`` more from each widening list (BM25 and the LOs' linked spans; a spare dense hit that stays counts as its list's…
  - `label_pool_bound(cls, systems: Sequence[str], config: Any) -> int` (line 531; public) — Upper bound on one question's labelled candidates: each display system's top 10, plus the tutor pools (the teaching scope's, so no overlap with the library's lists is assumed; dense_verify's pool is the dense part of pool_verify's).
  - `run(self, data: EvalData, request: Any, ctx: Any) -> dict[str, Any]` (line 547; public)
  - `_rankings(self, vault: LoadedVault, repository: Repository, scope: Scope, text: str, systems: Iterable[str], index: Any, vectors: dict[str, Any], rewrite: Rewrite | None) -> dict[str, list[str]]` (line 802; internal)
  - `_passage_question(self, vault: LoadedVault, repository: Repository, keys: Sequence[tuple[str, str]]) -> TutorQuestion` (line 839; internal) — A generated (or reader) question: a library question about its passages' LOs.
  - `_logged_question(self, vault: LoadedVault, repository: Repository, entry: LoggedQuestion) -> TutorQuestion` (line 852; internal) — A logged question in the context the learner asked it (review F5).
  - `_tutor_scope(self, vault: LoadedVault, repository: Repository, question: Mapping[str, Any]) -> Scope` (line 863; internal) — The teaching scope this question's tutor pools search (review F8).
  - `_verify_pools(self, vault: LoadedVault, repository: Repository, question: Mapping[str, Any], systems: Sequence[str], vectors: Mapping[str, Any], rewrites: Mapping[str, Rewrite], pool_modes: dict[str, dict[str, int]]) -> dict[str, TutorPool]` (line 871; internal) — The pools each verification system judges: the tutor's own construction (``tutor_pool``) for this question's context, on vectors already paid for.
  - `_verify(self, ctx: Any, vault: LoadedVault, text: str, hits: Sequence[SpanHit], context: str | None=None) -> tuple[Any, float]` (line 901; internal) — The production verification under the harness's budget, price and receipts.
  - `_blocks(self, repository: Repository, keys: list[str], *, complete: bool=True) -> dict[str, str]` (line 927; internal)
  - `markdown_lines(self, results: dict[str, Any]) -> list[str]` (line 938; public)
- `verdict_blocks(comparisons: Sequence[tuple[str, str]], coverage: Mapping[str, Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 1047) — Comparisons whose verdict is blocked: a verification system with a verification that did not run (review F4), or a dense-only system whose pool fell back on some question (review F8).

### Module constants

- `DISPLAY_SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 118)
- `VERIFY_SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 119)
- `SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 120)
- `DENSE_SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 121)
- `DENSE_ONLY_SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 123)
- `REWRITE_SYSTEMS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 124)
- `QUERY_TYPES` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 125)
- `LOGGED_TYPE` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 126)
- `DEFAULT_QUESTIONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 127)
- `QUESTION_PROMPT_VERSION` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 128)
- `TYPE_PROMPT_VERSIONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 129)
- `LABEL_PROMPT_VERSIONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 135)
- `QUESTION_BATCH` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 136)
- `LABEL_BATCH` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 137)
- `SEED_MIN_CHARS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 138)
- `SEED_CHARS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 139)
- `PAIR_MIN_DISTANCE` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 141)
- `EMBED_BATCH` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 142)
- `COMPARISONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 143)
- `TYPE_COMPARISONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 150)
- `VERIFY_COMPARISONS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 153)
- `VERIFY_METRICS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 155)
- `VERIFY_POOLS` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 158)
- `GENERATED_CONTEXT` ([src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 162)

### Explicit exports

`__all__` declares:

- `COMPARISONS`
- `DISPLAY_SYSTEMS`
- `LABEL_PROMPT_VERSIONS`
- `QUERY_TYPES`
- `QUESTION_PROMPT_VERSION`
- `SYSTEMS`
- `SourceRetrievalSuite`
- `TYPE_PROMPT_VERSIONS`
- `VERIFY_SYSTEMS`
- `summarize_verification`
- `type_counts`
- `verdict_blocks`
- `verification_metrics`

## Internal implementation anchors

- `class _Block` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 232)
- `_candidate_blocks(repository: Repository, scope: Scope) -> list[_Block]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 239)
- `_seeds(repository: Repository, scope: Scope, counts: Mapping[str, int]) -> list[Seed]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 259) — Disjoint seeds per type.
- `_logged(repository: Repository, scope: Scope, count: int | None=None) -> list[LoggedQuestion]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 308) — Every distinct logged learner question (``count`` None: all of them).
- `_dcg(gains: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 332)
- `_gains(labels: Mapping[str, Sequence[str | None]]) -> tuple[dict[str, float], set[str]] | None` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 336)
- `_stats(values: Sequence[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 372)
- `_fmt(value: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 1011)
- `_count(values: Iterable[str]) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 1015)
- `_split(per_question: list[dict[str, Any]], systems: list[str], key: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 1022)
- `_by_type(per_question: list[dict[str, Any]], systems: list[str], verifying: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/evaluation.py), line 1030) — Every metric within each query type (generated types, then logged).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/suites|learnloop.source_retrieval.suites]] — imports `SourceRetrievalSuite`; statically calls `SourceRetrievalSuite`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`; calls `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`; calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`, `extraction_blocks`, `search_blocks`, `section_header_titles`; calls `blocks_by_key`, `extraction_blocks`, `search_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `estimate_tokens`; calls `estimate_tokens`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `paired_bootstrap`; calls `paired_bootstrap`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `MAX_HITS`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `module`; calls `beats`, `clip`, `label_agreement`, `label_pool`, `plan_label_calls`, `plan_question_calls`, `read_only_repository`, `role_budget`, `score_question`, `stable_key`, `summarize`, `write_questions`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `QueryRewrite`, `SpanVerification`, `VERDICT_SCORE`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `library_scope`; calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `dense_coverage`, `load_dense_index`; calls `dense_coverage`, `load_dense_index`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `REWRITE_PROMPT_VERSION`, `Rewrite`, `is_conceptual`, `rewrite_prompt`, `rewritten_text`; calls `Rewrite`, `is_conceptual`, `rewrite_prompt`, `rewritten_text`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`, `embeddable`, `source_block_passage`, `source_block_text`, `split_record_id`; calls `block_record_id`, `embeddable`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `POOL_DENSE_PLUS_BM25`, `POOL_HYBRID_RRF`, `SpanHit`, `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `ITEM_BOUND_CONTEXTS`, `TutorPool`, `tutor_pool`, `tutor_scope`; calls `tutor_pool`, `tutor_scope`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `judged_passage`, `passage_limit`, `verify_prompt`, `verify_spans`; calls `judged_passage`, `passage_limit`, `verify_prompt`, `verify_spans`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `math`, `statistics`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/suites|learnloop.source_retrieval.suites]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_every_logged_learner_question_is_included`
  - `test_generated_questions_split_evenly_across_the_four_types`
  - `test_the_label_pool_bound_counts_what_each_verification_pool_can_add`
  - `test_the_report_runs_the_production_verification_by_query_type`
  - `test_verification_metrics_score_the_picks_against_the_whole_pool`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_cached_verification_is_served_even_when_the_caps_are_spent`
  - `test_a_failed_verification_is_never_scored_and_blocks_its_verdicts`
  - `test_every_verification_attempt_is_admitted_under_the_shared_caps`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_trim_between_the_recipe_cap_and_the_block_length_is_counted`
  - `test_the_t6_labeller_counts_a_trim_at_the_passage_budget`

## Modification guidance

- Make changes here when the responsibility remains evaluation within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/evaluation.py](../../../../../../src/learnloop/source_retrieval/evaluation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

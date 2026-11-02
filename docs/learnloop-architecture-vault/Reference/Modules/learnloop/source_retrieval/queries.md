---
title: "learnloop.source_retrieval.queries"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/queries.py"
source_paths:
  - "src/learnloop/source_retrieval/queries.py"
source_commit: "944cae2748d7f9d5a4a085f398084586615b50fa"
source_commit_timestamp: "2026-10-24T20:56:30-04:00"
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
  - "learnloop.source_retrieval.queries module"
  - "src/learnloop/source_retrieval/queries.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.queries`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.queries` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Queries: the conceptual-question gate, cached query embeddings, the LLM rewrite.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py) |
| Source lines | 243 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `944cae2748d7f9d5a4a085f398084586615b50fa` |
| Commit timestamp | `2026-10-24T20:56:30-04:00` |

## Public API

- `query_id(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 71)
- `is_conceptual(text: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 75) — A question worth rewriting: a question word or mark, or five content terms.
- `class Rewrite` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 86)
  - `ok(self) -> bool` (line 95; public)
  - `describe(self) -> dict[str, Any]` (line 98; public)
- `rewrite_output_tokens(vault: LoadedVault, client: Any | None=None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 103) — The rewrite's output budget: the route's under the shared policy.
- `rewrite_caps(vault: LoadedVault, output_tokens: int | None=None) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 109) — One call and one retry; a truncation retry asks for twice the budget.
- `route_skip(route: Any, price: float | None, *, injected: bool) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 118) — Why a live paid step is skipped before any client is built, or None (Phase 5b's skip check, naming T6's price setting).
- `rewrite_prompt(question: str, context: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 126)
- `rewrite_query(vault: LoadedVault, repository: Repository, question: str, *, context: str | None=None, client: Any | None=None, owner_kind: str='source_query_rewrite', owner_id: str='', deadline: float | None=None, budget: SpendBudget | None=None) -> Rewrite` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 142) — The live rewrite of one conceptual question (never raises).
- `rewritten_text(rewrite: Rewrite) -> str` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 195) — The rewrite as one query text: the passage, then the keywords.
- `embed_query_texts(vault: LoadedVault, repository: Repository, texts: Mapping[str, str], *, embedder: Any | None=None, owner_id: str='', budget: SpendBudget | None=None, deadline: float | None=None) -> tuple[dict[str, np.ndarray], dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 201) — Query vectors by key (cached by text; one capped request for the rest).

### Module constants

- `QUERY_RECORD_KIND` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 40)
- `REWRITE_PROMPT_VERSION` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 41)
- `REWRITE_INPUT_TOKENS_BOUND` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 44)
- `MAX_QUERY_CHARS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 45)
- `LARGEST_QUERY_TEXT` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 50)
- `MAX_CONTEXT_CHARS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 51)
- `MAX_KEYWORDS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 52)
- `QUERY_EMBEDDING_CAPS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 54)
- `_QUESTION_WORDS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 56)
- `_REWRITE_INSTRUCTIONS` ([src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py), line 60)

### Explicit exports

`__all__` declares:

- `LARGEST_QUERY_TEXT`
- `MAX_QUERY_CHARS`
- `QUERY_EMBEDDING_CAPS`
- `QUERY_RECORD_KIND`
- `REWRITE_INPUT_TOKENS_BOUND`
- `REWRITE_PROMPT_VERSION`
- `Rewrite`
- `embed_query_texts`
- `is_conceptual`
- `query_id`
- `rewrite_caps`
- `rewrite_output_tokens`
- `rewrite_prompt`
- `rewrite_query`
- `rewritten_text`
- `route_skip`

## Internal implementation anchors

- `_validate(result: QueryRewrite) -> QueryRewrite` ([source](../../../../../../src/learnloop/source_retrieval/queries.py), line 136)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `query_id`; statically calls `query_id`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `embed_query_texts`; statically calls `embed_query_texts`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `REWRITE_PROMPT_VERSION`, `Rewrite`, `is_conceptual`, `rewrite_prompt`, `rewritten_text`; statically calls `Rewrite`, `is_conceptual`, `rewrite_prompt`, `rewritten_text`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `LARGEST_QUERY_TEXT`, `QUERY_EMBEDDING_CAPS`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `query_id`; statically calls `query_id`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `LARGEST_QUERY_TEXT`, `MAX_QUERY_CHARS`, `QUERY_EMBEDDING_CAPS`, `QUERY_RECORD_KIND`, `is_conceptual`, `query_id`, `rewrite_caps`, `rewrite_prompt`, `route_skip`; statically calls `is_conceptual`, `query_id`, `rewrite_caps`, `rewrite_prompt`, `route_skip`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `QUERY_EMBEDDING_CAPS`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `MAX_QUERY_CHARS`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `MAX_QUERY_CHARS`, `Rewrite`, `embed_query_texts`, `is_conceptual`, `rewrite_query`, `rewritten_text`; statically calls `embed_query_texts`, `is_conceptual`, `rewrite_query`, `rewritten_text`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `MAX_QUERY_CHARS`, `QUERY_RECORD_KIND`, `embed_query_texts`, `query_id`; statically calls `embed_query_texts`, `query_id`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `Rewrite`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `embed_query_texts`; statically calls `embed_query_texts`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `MAX_QUERY_CHARS`, `query_id`; statically calls `query_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `query_terms`; calls `query_terms`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `route_skip`; calls `route_skip`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `embed_queries`, `normalize_query`; calls `embed_queries`, `normalize_query`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `QueryRewrite`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `re`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]], [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]], [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_t6_rewrite_runs_on_the_plan_with_receipts`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_leaking_gap_statement_never_reaches_the_lookup`
  - `test_a_length_limit_never_cuts_a_statement_into_the_key`
  - `test_a_statement_that_fits_whole_is_still_delivered`
  - `test_the_learners_question_is_truncated_as_before`
  - `test_unbound_queries_are_built_as_before`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_only_conceptual_questions_are_rewritten`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_an_unknown_rewrite_is_planned_at_its_largest_encoding_and_never_found_cached`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains queries within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/queries.py](../../../../../../src/learnloop/source_retrieval/queries.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

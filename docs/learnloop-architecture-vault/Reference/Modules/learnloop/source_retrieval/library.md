---
title: "learnloop.source_retrieval.library"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/library.py"
source_paths:
  - "src/learnloop/source_retrieval/library.py"
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
  - "learnloop.source_retrieval.library module"
  - "src/learnloop/source_retrieval/library.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.library`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.library` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Library search ("where did I read that?") beyond ``instr()`` (Slice 2 T6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/library.py](../../../../../../src/learnloop/source_retrieval/library.py) |
| Source lines | 283 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `944cae2748d7f9d5a4a085f398084586615b50fa` |
| Commit timestamp | `2026-10-24T20:56:30-04:00` |

## Public API

- `embedding_route_problem(vault: LoadedVault) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 69) — Why the ``embedding`` route cannot embed a query now, or None (no call).
- `meaning_search_state(vault: LoadedVault, repository: Repository, scope: Scope, *, embedder: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 86) — Whether a deep search would rank by meaning, and over how much of the scope.
- `search_library(vault: LoadedVault, repository: Repository, *, query: str, limit: int=MAX_HITS, deep: bool=False, embedder: Any | None=None, rewrite_client: Any | None=None, budget: SpendBudget | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 117) — The library search response: today's shape plus ``basis``, ``meaning_search`` and ``retrieval``.
- `deep_search_caps(*, max_calls: int, max_tokens: int, max_cost_usd: float) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 173) — One budget for a deep search's paid steps: the rewrite (and its retry) and each paid query encoder's embedding of the question and its rewrite.
- `plan_library_search(vault: LoadedVault, repository: Repository, *, query: str, deep: bool, caps: SpendCaps | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 188) — Dry run of :func:`search_library`: what a search would call, and at what cost.

### Module constants

- `_SNIPPET_RADIUS` ([src/learnloop/source_retrieval/library.py](../../../../../../src/learnloop/source_retrieval/library.py), line 51)
- `QUERY_TEXTS` ([src/learnloop/source_retrieval/library.py](../../../../../../src/learnloop/source_retrieval/library.py), line 170)

### Explicit exports

`__all__` declares:

- `deep_search_caps`
- `embedding_route_problem`
- `meaning_search_state`
- `plan_library_search`
- `search_library`

## Internal implementation anchors

- `_snippet(text: str, query: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library.py), line 54) — Around the first query term the block contains; else its opening.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `deep_search_caps`, `plan_library_search`, `search_library`; statically calls `deep_search_caps`, `plan_library_search`, `search_library`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `plan_library_search`; statically calls `plan_library_search`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `search_library`; statically calls `search_library`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `MANUAL_PROVIDER`, `provider_for_task`, `runtime_for_provider`; calls `provider_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `query_terms`; calls `query_terms`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `estimated_tokens`; calls `estimated_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `cached_query_vectors`, `normalize_query`, `query_embedding_price`; calls `cached_query_vectors`, `normalize_query`, `query_embedding_price`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `MAX_HITS`, `search_sources`; calls `search_sources`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `QueryRewrite`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `library_scope`; calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `dense_coverage`; calls `dense_coverage`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `plan_query`; calls `plan_query`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `deliver`; calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `LARGEST_QUERY_TEXT`, `MAX_QUERY_CHARS`, `QUERY_EMBEDDING_CAPS`, `QUERY_RECORD_KIND`, `is_conceptual`, `query_id`, `rewrite_caps`, `rewrite_prompt`, `route_skip`; calls `is_conceptual`, `query_id`, `rewrite_caps`, `rewrite_prompt`, `route_skip`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `PAID_QUERY_SPACES`, `resolver_active`; calls `resolver_active`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_cli.py](../../../../../../tests/test_source_retrieval_cli.py) — direct import
  - `test_deep_search_caps_bound_the_paid_steps`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
  - `test_the_deep_library_search_keeps_keyword_and_meaning_hits_without_codex`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_the_library_deep_search_reports_its_pool`
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
  - `test_a_query_embedding_that_runs_out_of_time_is_labelled_timed_out`
  - `test_meaning_search_is_unavailable_when_the_embedding_route_is_not_ready`
  - `test_the_deep_library_search_query_embedding_carries_the_time_left`
  - `test_typing_searches_reuse_the_coverage_until_the_library_changes`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_a_new_import_leaves_meaning_search_on_for_the_embedded_sources`
  - `test_deep_search_fuses_keyword_and_meaning_with_one_cached_query_embedding`
  - `test_the_kill_switch_restores_todays_search_exactly`
  - `test_the_typing_search_says_whether_enter_would_search_by_meaning`
  - `test_typing_search_beats_instr_on_stems_and_prefixes_and_keeps_substring_hits`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_an_unknown_rewrite_is_planned_at_its_largest_encoding_and_never_found_cached`
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`

## Modification guidance

- Make changes here when the responsibility remains library within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/library.py](../../../../../../src/learnloop/source_retrieval/library.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

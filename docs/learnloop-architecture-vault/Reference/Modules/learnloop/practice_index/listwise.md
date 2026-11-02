---
title: "learnloop.practice_index.listwise"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/listwise.py"
source_paths:
  - "src/learnloop/practice_index/listwise.py"
source_commit: "28c697869e348eba290381ac6155c5704df2e707"
source_commit_timestamp: "2026-10-25T17:16:18-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.listwise module"
  - "src/learnloop/practice_index/listwise.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.listwise`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.listwise` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: One listwise LLM judge for every live rerank (Phase 5b; shared with Slice 2 T6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/listwise.py](../../../../../../src/learnloop/practice_index/listwise.py) |
| Source lines | 298 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `28c697869e348eba290381ac6155c5704df2e707` |
| Commit timestamp | `2026-10-25T17:16:18-04:00` |

## Public API

- `class ListwiseTask` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 50) — What one kind of listwise rerank writes and how it is routed and priced.
- `class ListwiseOutcome(Generic[Key])` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 79) — ``status``: ``empty_pool``, a skip label, ``unavailable``, ``cached``, ``judged``, ``cancelled``, ``over_budget`` or ``failed`` (``reason`` says why).
  - `judged(self) -> bool` (line 91; public)
- `route_skip(route: PaidRoute, price: float | None, *, injected: bool, price_setting: str, route_label: str='') -> str | None` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 95) — Why a live paid step is skipped before any client is built, or None.
- `listwise_caps(pool_size: int, *, max_total_tokens: int, max_estimated_usd: float | None) -> SpendCaps` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 106) — One request and at most one retry, every candidate judged once.
- `task_output_tokens(task: ListwiseTask, route: PaidRoute) -> int` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 113) — The rerank's output budget: the task's pinned one, else the route's policy budget.
- `request_input_hash(task: ListwiseTask, route: PaidRoute, prompt: str) -> str` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 119)
- `ledger_ids(task: ListwiseTask, input_hash: str, keys: Sequence[Key], id_parts: Callable[[Key], Sequence[str]]) -> dict[Key, str]` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 128) — One ``judgment_ledger`` id per candidate, derived from the exact request.
- `validate_all_judged(result: Any, refs: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 135)
- `from_ledger(task: ListwiseTask, keys: Sequence[Key], ids: Mapping[Key, str], rows: Mapping[str, Mapping[str, Any]], status: str, pick_at_most: int) -> ListwiseOutcome[Key]` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 144) — The outcome a set of ledger rows describes: verdict rows and picks by rank.
- `judge_listwise(vault: LoadedVault, repository: Repository, task: ListwiseTask, *, prompt: str, refs: Mapping[str, Key], left_id: str, right_id: Callable[[Key], str], id_parts: Callable[[Key], Sequence[str]], pick_at_most: int, caps: SpendCaps, price: float | None, owner_id: str, client: Any | None=None, route: PaidRoute | None=None, deadline: float | None=None, validate: Callable[[Any], Any] | None=None, clock: Clock | None=None, budget: SpendBudget | None=None, admit: Callable[[SpendEstimate], None] | None=None, context: Mapping[str, Any] | None=None) -> ListwiseOutcome[Key]` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 175) — Judge the pool ``refs`` (prompt ref -> candidate key) and pick at most ``pick_at_most``.

### Explicit exports

`__all__` declares:

- `ListwiseOutcome`
- `ListwiseTask`
- `from_ledger`
- `judge_listwise`
- `ledger_ids`
- `listwise_caps`
- `request_input_hash`
- `route_skip`
- `task_output_tokens`
- `validate_all_judged`

## Internal implementation anchors

- `_jsonable(value: Any) -> Any` ([source](../../../../../../src/learnloop/practice_index/listwise.py), line 165) — A recorded judgment field as JSON (a nested model, or a list of them, dumped).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`; statically calls `ListwiseTask`, `judge_listwise`, `listwise_caps`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`; statically calls `ListwiseTask`, `judge_listwise`, `listwise_caps`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `route_skip`; statically calls `route_skip`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `ListwiseTask`, `judge_listwise`, `ledger_ids`, `listwise_caps`, `request_input_hash`, `route_skip`; statically calls `ListwiseTask`, `judge_listwise`, `ledger_ids`, `listwise_caps`, `request_input_hash`, `route_skip`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `route_skip`, `task_output_tokens`; statically calls `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `route_skip`; statically calls `route_skip`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `ListwiseTask`, `judge_listwise`; statically calls `ListwiseTask`, `judge_listwise`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `task_output_tokens`; statically calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `task_output_tokens`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`; statically calls `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `route_skip`; statically calls `route_skip`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`; statically calls `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`, `task_output_tokens`; statically calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`; statically calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AITask`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]], [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_the_dry_run_bounds_the_live_verification`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_tutor_verification_and_the_practice_rerank_share_one_listwise_judge`

## Modification guidance

- Make changes here when the responsibility remains listwise within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/listwise.py](../../../../../../src/learnloop/practice_index/listwise.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

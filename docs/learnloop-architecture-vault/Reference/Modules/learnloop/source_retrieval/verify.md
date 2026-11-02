---
title: "learnloop.source_retrieval.verify"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/verify.py"
source_paths:
  - "src/learnloop/source_retrieval/verify.py"
source_commit: "ddbdb51df610516f4ebd27b64b60505c8a0190ab"
source_commit_timestamp: "2026-10-15T02:25:24-04:00"
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
  - "learnloop.source_retrieval.verify module"
  - "src/learnloop/source_retrieval/verify.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.verify`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.verify` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The listwise LLM verification of retrieved spans (consequential paths only).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py) |
| Source lines | 329 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ddbdb51df610516f4ebd27b64b60505c8a0190ab` |
| Commit timestamp | `2026-10-15T02:25:24-04:00` |

## Public API

- `class Verification` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 89)
  - `ran(self) -> bool` (line 100; public)
  - `describe(self) -> dict[str, Any]` (line 103; public)
- `class VerificationRoute` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 116) — The verification's route and client, resolved before anything is paid for.
  - `ready(self) -> bool` (line 125; public)
- `verification_route(vault: LoadedVault, client: Any | None=None) -> VerificationRoute` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 129) — Whether verification can run (route, price, provider readiness), with no call.
- `practice_question(item: Any, *, ellipsis: bool=False) -> str` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 159) — An item-bound verification's practice question: the question as presented, within :data:`PRACTICE_QUESTION_CHARS`.
- `passage_chars(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 175) — The most characters of one judged passage (``passage_token_budget``).
- `passage_limit(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 181) — The most characters of one judged passage under the vault's switch: the passage budget, or the predecessor's 900 with complete passages off.
- `judged_passage(vault: LoadedVault, text: str | None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 188) — A candidate's passage as the vault's judges read it, and whether it was cut: :func:`judge_passage` at the budget, or with ``source_retrieval.complete_passages`` off the predecessor's clip (900 characters of the collapsed text, "…" at the cut).
- `judge_passage(text: str | None, max_chars: int) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 200) — A candidate's passage for a relevance judge: the complete block with its whitespace collapsed, trimmed only past ``max_chars`` (a word boundary when one is near, then "…").
- `verify_caps(vault: LoadedVault, pool_size: int, output_tokens: int | None=None, input_tokens: int | None=None) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 215) — One call and one retry (a truncation retry asks for twice the budget).
- `verify_prompt(question: str, context: str | None, pick_at_most: int, candidates: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 229)
- `verify_spans(vault: LoadedVault, repository: Repository, *, question: str, pool: Sequence[SpanHit], pick_at_most: int, context: str | None=None, client: Any | None=None, owner_id: str='', clock: Clock | None=None, ready: VerificationRoute | None=None, deadline: float | None=None, budget: SpendBudget | None=None, price_per_million: float | None=None, admit: Callable[[SpendEstimate], None] | None=None) -> Verification` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 259) — Judge ``pool`` for ``question`` and pick at most ``pick_at_most`` spans.

### Module constants

- `VERIFY_PROMPT_VERSION` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 54)
- `PRACTICE_QUESTION_CHARS` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 56)
- `VERIFY_INPUT_TOKENS_BOUND` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 59)
- `CHARS_PER_TOKEN` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 61)
- `PREDECESSOR_PASSAGE_CHARS` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 63)
- `TASK` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 64)
- `PRICE_SETTING` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 65)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 66)
- `VERIFY_TASK` ([src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py), line 78)

### Explicit exports

`__all__` declares:

- `CHARS_PER_TOKEN`
- `PRACTICE_QUESTION_CHARS`
- `PREDECESSOR_PASSAGE_CHARS`
- `PRICE_SETTING`
- `TASK`
- `VERIFY_PROMPT_VERSION`
- `VERIFY_TASK`
- `Verification`
- `VerificationRoute`
- `judge_passage`
- `judged_passage`
- `passage_chars`
- `passage_limit`
- `practice_question`
- `verification_route`
- `verify_caps`
- `verify_prompt`
- `verify_spans`

## Internal implementation anchors

- `_clip(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 150)
- `_cut(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 155)
- `_candidates(pool: Sequence[SpanHit], vault: LoadedVault) -> tuple[list[dict[str, Any]], dict[str, SpanHit], int]` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 239)
- `_validate(result: SpanVerification, refs: Mapping[str, Any]) -> SpanVerification` ([source](../../../../../../src/learnloop/source_retrieval/verify.py), line 253)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `verify_spans`; statically calls `verify_spans`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `PRICE_SETTING`, `verify_caps`; statically calls `verify_caps`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `judged_passage`, `passage_limit`, `verify_prompt`, `verify_spans`; statically calls `judged_passage`, `passage_limit`, `verify_prompt`, `verify_spans`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `PRICE_SETTING`, `judged_passage`, `passage_limit`, `practice_question`, `verify_caps`; statically calls `judged_passage`, `passage_limit`, `practice_question`, `verify_caps`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `verification_route`; statically calls `verification_route`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `practice_question`, `verification_route`, `verify_spans`; statically calls `practice_question`, `verification_route`, `verify_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `PRACTICE_QUESTION_CHARS`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidRoute`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`; calls `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `normalize_query`; calls `normalize_query`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `SpanVerification`, `VERDICT_SCORE`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `MAX_QUERY_CHARS`, `query_id`; calls `query_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `SpanHit`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_no_bound_model_call_receives_item_text_from_outside_the_plan`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_tutor_verification_and_the_practice_rerank_share_one_listwise_judge`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_judge_passages_are_complete_blocks_trimmed_only_past_the_budget`

## Modification guidance

- Make changes here when the responsibility remains verify within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/verify.py](../../../../../../src/learnloop/source_retrieval/verify.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

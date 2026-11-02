---
title: "learnloop.source_retrieval.contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/contracts.py"
source_paths:
  - "src/learnloop/source_retrieval/contracts.py"
source_commit: "7ee17730cc8fb532f5e438aeda915444cf9609f2"
source_commit_timestamp: "2026-10-12T17:19:54-04:00"
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
  - "learnloop.source_retrieval.contracts module"
  - "src/learnloop/source_retrieval/contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.contracts` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Strict wire contracts for T6's paid LLM roles.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/contracts.py](../../../../../../src/learnloop/source_retrieval/contracts.py) |
| Source lines | 59 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7ee17730cc8fb532f5e438aeda915444cf9609f2` |
| Commit timestamp | `2026-10-12T17:19:54-04:00` |

## Public API

- `class QueryRewrite(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 17) — A retrieval rewrite: what a relevant passage would say, and search terms.
- `class SpanJudgment(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 24)
- `class SpanVerification(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 30) — Judge every candidate passage, then pick and order the best few.
- `class SpanLabels(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 37)
- `class WrittenQuestion(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 41)
- `class WrittenQuestions(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/contracts.py), line 46)

### Module constants

- `VERDICT_SCORE` ([src/learnloop/source_retrieval/contracts.py](../../../../../../src/learnloop/source_retrieval/contracts.py), line 14)

### Explicit exports

`__all__` declares:

- `QueryRewrite`
- `SpanJudgment`
- `SpanLabels`
- `SpanVerdict`
- `SpanVerification`
- `VERDICT_SCORE`
- `WrittenQuestion`
- `WrittenQuestions`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `SpanLabels`, `VERDICT_SCORE`, `WrittenQuestions`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `QueryRewrite`, `SpanVerification`, `VERDICT_SCORE`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `QueryRewrite`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `QueryRewrite`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `SpanVerification`, `VERDICT_SCORE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]], [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_a_profile_maximum_is_never_exceeded_by_the_retry`
  - `test_a_route_effort_reaches_openrouter_as_reasoning_effort`
  - `test_a_second_truncation_fails_and_is_never_accepted`
  - `test_an_admitting_caller_lets_the_transport_retry_a_truncation_at_double`
  - `test_an_owner_set_budget_is_never_exceeded_and_its_truncation_is_logged`
  - `test_inside_a_caller_budget_the_transport_leaves_the_retry_to_the_caller`
  - `test_paid_calls_fail_on_a_second_truncation`
  - `test_paid_calls_retry_a_truncation_once_at_double_the_admitted_budget`
  - `test_slice1_review_spend_admits_the_transports_truncation_retry_at_double`
  - `test_the_compare_harness_uses_the_policy_budget_and_retries_a_truncation`
  - `test_the_route_effort_wins_over_a_profile_that_disables_thinking`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_pf_caller_prices_a_truncation_retry_at_its_doubled_output_budget`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request`
  - `test_paid_calls_reserve_and_record_the_real_increased_limit`
  - `test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance`
  - `test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance`
  - `test_the_compare_harness_never_resends_a_profile_maximum`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains contracts within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/contracts.py](../../../../../../src/learnloop/source_retrieval/contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

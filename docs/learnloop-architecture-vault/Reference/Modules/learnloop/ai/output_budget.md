---
title: "learnloop.ai.output_budget"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/output_budget.py"
source_paths:
  - "src/learnloop/ai/output_budget.py"
source_commit: "98ebeafcd685cc1a358506d793dca6bec1b08930"
source_commit_timestamp: "2026-10-13T00:40:36-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.output_budget module"
  - "src/learnloop/ai/output_budget.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.output_budget`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.output_budget` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: One output-budget policy for every LLM role (owner, 2026-10-12).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/output_budget.py](../../../../../../src/learnloop/ai/output_budget.py) |
| Source lines | 237 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `98ebeafcd685cc1a358506d793dca6bec1b08930` |
| Commit timestamp | `2026-10-13T00:40:36-04:00` |

## Public API

- `output_budget(config: Any | None, route: str | None=None, *, provider: str | None=None) -> int` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 70) — The output-token budget for one LLM call on ``route``.
- `output_ceiling(client: Any) -> int | None` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 99) — The most output tokens ``client``'s transport will ever send, or None.
- `reasoning_effort(config: Any | None, route: str | None) -> str | None` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 111) — The reasoning effort ``route`` asks for, or None to keep the profile's.
- `record_truncation(*, role: str | None, provider: str | None, model: str | None, budget: int | None, retry_budget: int | None, owner_kind: str | None=None, owner_id: str | None=None, next_step: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 124) — Log one truncation as an event; returns its fields (for receipts and reports).
- `class TruncationRetry` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 149) — One logical call's output budget: increased once after a truncation.
  - `initial_budget(self) -> int` (line 186; public)
  - `after_truncation(self, *, allowed: bool=True) -> bool` (line 189; public) — Record a truncation; True when the call should retry with a larger budget.
  - `receipts(self) -> Iterator[None]` (line 215; public) — Tag the root receipt of a truncation retry (its ``budget_json``).

### Module constants

- `TRUNCATION_RETRY_FACTOR` ([src/learnloop/ai/output_budget.py](../../../../../../src/learnloop/ai/output_budget.py), line 50)
- `PROFILE_EFFORT` ([src/learnloop/ai/output_budget.py](../../../../../../src/learnloop/ai/output_budget.py), line 52)

### Explicit exports

`__all__` declares:

- `DEFAULT_OUTPUT_TOKENS`
- `PROFILE_EFFORT`
- `TRUNCATION_RETRY_FACTOR`
- `TruncationRetry`
- `output_budget`
- `output_ceiling`
- `reasoning_effort`
- `record_truncation`

## Internal implementation anchors

- `_profile_for(config: Any, route: str | None, provider: str | None) -> Any` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 55)
- `_positive(value: Any) -> int | None` ([source](../../../../../../src/learnloop/ai/output_budget.py), line 95)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `TRUNCATION_RETRY_FACTOR`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `TRUNCATION_RETRY_FACTOR`, `record_truncation`; statically calls `record_truncation`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `output_budget`, `record_truncation`; statically calls `output_budget`, `record_truncation`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `DEFAULT_OUTPUT_TOKENS`, `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `DEFAULT_OUTPUT_TOKENS`, `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `TruncationRetry`, `output_ceiling`; statically calls `TruncationRetry`, `output_ceiling`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `TRUNCATION_RETRY_FACTOR`, `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; statically calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `output_budget`; statically calls `output_budget`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `output_budget`; statically calls `output_budget`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `annotate_calls`; calls `annotate_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_OUTPUT_TOKENS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] and 20 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_hardcase_harness_plans_the_grader_at_its_routes_policy_budget`
  - `test_the_hardcase_harness_retries_a_truncated_grade_once_at_double`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_a_truncation_retry_obeys_the_retry_cap`
  - `test_t6_rewrite_and_verification_default_to_low_effort_and_an_owner_table_merges`
  - `test_the_default_budget_is_generous_and_the_profile_or_route_can_replace_it`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b1_writer_output_budget_defaults_to_the_policy_budget_and_is_planned`
  - `test_the_openrouter_writer_carries_its_effort_and_budget_and_the_bill_is_the_headline`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap`
  - `test_a_truncated_facet_judgment_is_retried_once_at_double_the_budget`
  - `test_b1_local_runner_never_lets_the_transport_retry_a_truncated_writer`
  - `test_b1_writer_budget_follows_the_policy_and_the_flag`
  - `test_text_gap_routes_follow_the_vaults_output_budget_policy`
  - `test_the_facet_judge_asks_for_and_reserves_the_policy_budget`
  - `test_the_latency_probe_asks_for_each_profiles_policy_budget`
  - `test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_route_override_cannot_exceed_the_profile_maximum`
  - `test_a_truncation_retry_stops_at_the_transport_ceiling`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/output_budget.py](../../../../../../src/learnloop/ai/output_budget.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

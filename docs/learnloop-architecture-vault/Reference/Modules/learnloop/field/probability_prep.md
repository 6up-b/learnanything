---
title: "learnloop.field.probability_prep"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/probability_prep.py"
source_paths:
  - "src/learnloop/field/probability_prep.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.probability_prep module"
  - "src/learnloop/field/probability_prep.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.probability_prep`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.probability_prep` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Paid preparation and cache loading for the ``llm_probability`` V1-V3 arms.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py) |
| Source lines | 675 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbabilityJudgment(WireModel)` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 90)
- `prediction_points(rows: Iterable[Any], *, incumbent: Mapping[str, Any] | None=None, start_of: Callable[[str], datetime | None] | None=None) -> list[PredictionPoint]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 128) — Every prediction the harness will ask an attempt arm for, in order.
- `class RenderedRequest` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 177)
- `class RenderedPlan` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 185) — Per variant: every position's request digest, and each distinct state.
  - `for_variant(self, variant: str) -> list[RenderedRequest]` (line 191; public)
- `render_plan(points: Sequence[PredictionPoint], variants: Iterable[str], renderer: StateRenderer) -> RenderedPlan` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 196)
- `class JudgeRoute` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 215) — A resolved judge route; ``settings`` is non-secret and hashed into the cache.
  - `version(self) -> str` (line 228; public)
  - `settings_hash(self) -> str` (line 232; public)
- `llm_prompt(state: Any) -> str` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 236)
- `request_estimate(route: JudgeRoute, request: RenderedRequest) -> SpendEstimate` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 242) — A conservative per-request estimate, before any call.
- `committed_judgments(connection: Any) -> dict[tuple[str, ...], dict[str, Any]]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 314) — Valid verdicts already committed to ``judgment_ledger``, by request identity.
- `check_cache_location(cache_dir: Path, vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 348)
- `load_arms(plan: RenderedPlan, *, cache_dir: Path, routes: Mapping[str, JudgeRoute], selection: Sequence[tuple[str, str]]) -> tuple[list[CachedProbabilityArm], dict[str, Any]]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 355) — Cache-only: no client, no repository, no call.
- `prepare_judge(plan: RenderedPlan, *, route: JudgeRoute, variants: Sequence[str], cache_dir: Path, repository: Any, caps: SpendCaps, dry_run: bool=False, cancelled: Callable[[], bool] | None=None, sleep: Callable[[float], None]=time.sleep, committed: Mapping[tuple[str, ...], Mapping[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 432) — Prepare one judge's uncached requests; returns an aggregate-only report.

### Module constants

- `TASK` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 62)
- `QUESTION_NAME` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 63)
- `QUESTION_TEXT` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 64)
- `QUESTION_SET_VERSION` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 66)
- `LLM_PROMPT_VERSION` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 68)
- `DECIDER_QUESTIONS` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 69)
- `LLM_INSTRUCTIONS` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 79)
- `DECIDER_OUTPUT_TOKENS` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 85)
- `MAX_RETRY_AFTER_SECONDS` ([src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py), line 87)

### Explicit exports

`__all__` declares:

- `DECIDER_QUESTIONS`
- `JudgeRoute`
- `LLM_PROMPT_VERSION`
- `ProbabilityJudgment`
- `QUESTION_NAME`
- `QUESTION_SET_VERSION`
- `QUESTION_TEXT`
- `RenderedPlan`
- `RenderedRequest`
- `TASK`
- `check_cache_location`
- `committed_judgments`
- `llm_prompt`
- `load_arms`
- `prediction_points`
- `prepare_judge`
- `render_plan`
- `request_estimate`

## Internal implementation anchors

- `_digest(value: Any) -> str` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 95)
- `_observes(row: Any) -> bool` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 102) — What the incumbent folds: every signal and every scored attempt.
- `_incumbent_numbers(ekf: Any, row: AttemptRow, observations: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 108)
- `_sum(estimates: Iterable[SpendEstimate]) -> SpendEstimate` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 262)
- `_cache_path(directory: Path, route: JudgeRoute, digest: str) -> Path` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 275)
- `_read_cached(directory: Path, route: JudgeRoute, request: RenderedRequest) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 280)
- `_write_checkpoint(path: Path, checkpoint: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 295) — One completed prediction per file; an interruption never corrupts a finished entry.
- `_valid_probability(value: Any) -> bool` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 304)
- `_identity(judge: str, version: str, settings_hash: str, request_digest: str, state_hash_: str, state_version: str=STATE_VERSION) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 309)
- `class _Attempt` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 401)
- `_call_decider(client: Any, request: RenderedRequest) -> tuple[float | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 406)
- `_call_llm(client: Any, route: JudgeRoute, request: RenderedRequest, output_tokens: int | None=None) -> tuple[float | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/field/probability_prep.py), line 414)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `DECIDER_OUTPUT_TOKENS`, `JudgeRoute`, `check_cache_location`, `committed_judgments`, `load_arms`, `prediction_points`, `prepare_judge`, `render_plan`; statically calls `JudgeRoute`, `check_cache_location`, `committed_judgments`, `load_arms`, `prediction_points`, `prepare_judge`, `render_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `DecisionResponseInvalid`, `NoulQuestion`, `request_body`; calls `NoulQuestion`, `request_body`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `generation_limit`, `observe_model_calls`, `single_request`; calls `call_labels`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_ceiling`; calls `TruncationRetry`, `output_ceiling`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `_eligible`, `_groups`; calls `_eligible`, `_groups`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `create_predictor`; calls `create_predictor`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `CachedProbabilityArm`, `VARIANTS`, `position_key`; calls `CachedProbabilityArm`, `position_key`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `PredictionPoint`, `STATE_VERSION`, `StateRenderer`, `canonical_json`, `history_pairs`, `start_index`, `state_hash`; calls `PredictionPoint`, `canonical_json`, `history_pairs`, `start_index`, `state_hash`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`, `SignalRow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `pathlib`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_an_early_offer_moves_the_window_and_the_incumbent_back`
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_prediction_points_are_exactly_the_harness_positions`
  - `test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed`
  - `test_resume_recovers_a_committed_verdict_instead_of_paying_again`
  - `test_rich_state_carries_hypothesis_evidence_and_help_timing_to_both_judges`
  - `test_scripted_decider_sees_identical_states_for_both_judges`
  - `test_subscription_llm_estimates_cost_ledgers_invalid_verdicts_and_resumes`
- [tests/test_recurrence_merge_composition.py](../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_t1_ledger_rows_fit_r0s_check_and_r0s_recovery_never_reads_them`

## Modification guidance

- Make changes here when the responsibility remains probability prep within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/probability_prep.py](../../../../../../src/learnloop/field/probability_prep.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

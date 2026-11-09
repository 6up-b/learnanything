---
title: "learnloop.content.facet_identity.judge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/judge.py"
source_paths:
  - "src/learnloop/content/facet_identity/judge.py"
source_commit: "workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.judge module"
  - "src/learnloop/content/facet_identity/judge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.judge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.judge` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: The facet-identity judge: one concept neighbourhood in, a partition out.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py) |
| Source lines | 1264 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65` |
| Commit timestamp | `2026-11-09T12:16:08-05:00` |

## Public API

- `class FacetSetVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 153)
- `class FacetPartitionVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 161)
- `class Member` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 166)
- `class GroupRequest` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 180)
  - `member(self, label: str) -> Member | None` (line 191; public)
  - `by_key(self, key: str) -> Member | None` (line 194; public)
  - `pairs(self) -> list[tuple[Member, Member]]` (line 197; public) — Pairs the judge decides (registered pairs are not decided in attach mode).
  - `new_count(self) -> int` (line 208; public)
- `class DecidedSet` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 213)
  - `as_dict(self) -> dict[str, Any]` (line 220; public)
- `class GroupOutcome` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 225)
  - `judgments_for(self, keys: Sequence[str]) -> list[str]` (line 236; public)
  - `summary(self) -> dict[str, Any]` (line 243; public)
- `build_request(members: Sequence[Member], *, mode: str, shortlisted: Iterable[Iterable[str]]=()) -> GroupRequest` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 260) — Label members (E*/N* in attach mode, F* otherwise) and render the prompt.
- `judge_output_tokens(config: Any | None, provider: str | None=None) -> int` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 307) — The LLM judge's output budget: the shared policy's for its route.
- `estimate_tokens(request: GroupRequest, output_tokens: int=DEFAULT_OUTPUT_TOKENS) -> int` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 319)
- `validate_partition(request: GroupRequest, verdict: FacetPartitionVerdict) -> tuple[list[DecidedSet], list[str]]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 327) — The merge/absorb sets a verdict decides, repaired conservatively.
- `same_set(sets: Sequence[DecidedSet]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 384)
- `existing_judgments(connection: Any, request: GroupRequest, *, judge: str, judge_model: str, prompt_version: str) -> dict[tuple[str, str], str]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 399) — Ledger rows already written for exactly this question (pair keys -> id).
- `raw_pair_verdicts(request: GroupRequest, verdict: FacetPartitionVerdict) -> Callable[[Member, Member], tuple[bool, dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 419) — The judge's own verdict on a pair, from its raw partition (before repair).
- `append_partition_judgments(connection: Any, request: GroupRequest, sets: Sequence[DecidedSet], *, judge: str, judge_model: str, prompt_version: str, judged: Callable[[Member, Member], tuple[bool, Mapping[str, Any]]] | None=None, repair_reason: str='kept apart when the partition was validated', pair_detail: Callable[[Member, Member], Mapping[str, Any]] | None=None, pair_score: Callable[[Member, Member], float | None] | None=None) -> dict[tuple[str, str], str]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 450) — The judge's verdict on its merged and shortlisted pairs; returns pair keys -> id.
- `owner_vetoes(connection: Any, request: GroupRequest) -> set[frozenset[str]]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 520) — Member-key pairs of ``request`` the owner currently says are ``different``.
- `apply_owner_vetoes(request: GroupRequest, sets: Sequence[DecidedSet], vetoes: set[frozenset[str]]) -> tuple[list[DecidedSet], list[str]]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 547) — Drop from each set every member the owner said differs from a kept one.
- `class Pricing` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 576)
  - `known(self) -> bool` (line 582; public)
  - `usd(self, input_tokens: int, output_tokens: int) -> float | None` (line 585; public)
- `pricing_for(model: str | None, *, input_override: float | None=None, output_override: float | None=None) -> Pricing` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 591)
- `request_estimate(request: GroupRequest, pricing: Pricing, *, retry: bool=False, new_facets: int | None=None, new_pairs: int | None=None, output_tokens: int=DEFAULT_OUTPUT_TOKENS) -> SpendEstimate` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 601)
- `plan_estimate(requests: Sequence[GroupRequest], pricing: Pricing, *, decider: bool=False, output_tokens: int=DEFAULT_OUTPUT_TOKENS) -> SpendEstimate` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 614) — The whole plan, for a dry run and the up-front cap check.
- `class LLMGroupJudge` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 650) — One structured call per group, under the Slice A spend controls.
  - `__init__(self, *, client: Any, provider: str, model: str | None, caps: SpendCaps, pricing: Pricing, repository: Any, owner_id: str, cancelled: Callable[[], bool] | None=None, output_tokens: int | None=None, reasoning_effort: str | None=None) -> None` (line 669; internal)
  - `declared(self) -> dict[str, Any]` (line 699; public)
  - `checkpoint_key(self, request: GroupRequest) -> str` (line 710; public)
  - `run(self, requests: Sequence[GroupRequest]) -> list[GroupOutcome]` (line 723; public)
  - `_finish(self, request: GroupRequest, verdict: FacetPartitionVerdict, model: str, *, status: str) -> GroupOutcome` (line 844; internal)
  - `charged(self) -> dict[str, Any]` (line 862; public)
- `choice_question(instructions: str, options: Mapping[str, str | None]) -> ChoiceQuestion` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 869) — Router R0's typed choice question (the Decider client accepts nothing else).
- `partition_from_pairs(request: GroupRequest, choices: Mapping[tuple[str, str], tuple[str, Mapping[str, float]]]) -> list[DecidedSet]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 875) — Same-skill sets from per-pair choices, with the no-chaining refusal.
- `class DeciderGroupJudge` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 948) — The Decider: one typed ``choice`` question per pair (router spec §6).
  - `__init__(self, *, client: Any, model: str | None, caps: SpendCaps, pricing: Pricing, repository: Any, owner_id: str, cancelled: Callable[[], bool] | None=None) -> None` (line 960; internal)
  - `declared(self) -> dict[str, Any]` (line 970; public)
  - `checkpoint_key(self, request: GroupRequest) -> str` (line 974; public)
  - `_stored_choices(self, request: GroupRequest) -> tuple[dict[tuple[str, str], tuple[str, Mapping[str, float]]], str] | None` (line 981; internal)
  - `_observer(self, request: GroupRequest, tokens: int) -> Callable[[str, dict[str, Any]], None]` (line 1000; internal) — Receipts for the Decider's paid calls, owned like the LLM judge's.
  - `run(self, requests: Sequence[GroupRequest]) -> list[GroupOutcome]` (line 1016; public)
  - `_finish(self, request: GroupRequest, choices: Mapping[tuple[str, str], tuple[str, Mapping[str, float]]], model: str, *, status: str) -> GroupOutcome` (line 1079; internal)
  - `charged(self) -> dict[str, Any]` (line 1110; public)
- `class JudgeRoute` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 1118) — The resolved judge route, before any client exists (dry runs stop here).
  - `as_dict(self) -> dict[str, Any]` (line 1133; public)
- `resolve_route(config: Any, *, client: Any=None, input_price: float | None=None, output_price: float | None=None) -> JudgeRoute` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 1144)
- `build_judge(vault: Any, repository: Any, *, owner_id: str, caps: SpendCaps, client: Any=None, cancelled: Callable[[], bool] | None=None, input_price: float | None=None, output_price: float | None=None) -> tuple[LLMGroupJudge | DeciderGroupJudge | None, JudgeRoute]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 1180) — A ready judge for the route, or ``None`` with the route's problem set.
- `caps_from_config(settings: Any, **overrides: Any) -> SpendCaps` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 1220)

### Module constants

- `TASK` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 88)
- `PROMPT_VERSION` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 89)
- `DECIDER_QUESTION_SET_VERSION` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 90)
- `OWNER_KIND` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 91)
- `PURPOSE` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 92)
- `ROUTE` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 93)
- `METERED_JUDGE_TYPES` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 94)
- `DECIDER_MAX_QUESTIONS` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 96)
- `KNOWN_PRICES_PER_MILLION` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 101)
- `RULES` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 107)
- `ATTACH_RULES` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 134)
- `DECIDER_INSTRUCTIONS` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 139)
- `DECIDER_OPTIONS` ([src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 145)

### Explicit exports

`__all__` declares:

- `DECIDER_QUESTION_SET_VERSION`
- `DeciderGroupJudge`
- `DecidedSet`
- `FacetPartitionVerdict`
- `FacetSetVerdict`
- `GroupOutcome`
- `GroupRequest`
- `JudgeRoute`
- `KNOWN_PRICES_PER_MILLION`
- `LLMGroupJudge`
- `Member`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `PURPOSE`
- `Pricing`
- `ROUTE`
- `TASK`
- `append_partition_judgments`
- `apply_owner_vetoes`
- `build_judge`
- `build_request`
- `caps_from_config`
- `judge_output_tokens`
- `choice_question`
- `partition_from_pairs`
- `owner_vetoes`
- `plan_estimate`
- `pricing_for`
- `resolve_route`
- `validate_partition`

## Internal implementation anchors

- `_ordered_pair(left: Member, right: Member) -> tuple[Member, Member]` ([source](../../../../../../../src/learnloop/content/facet_identity/judge.py), line 395)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `TASK`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `Member`, `build_judge`, `build_request`, `caps_from_config`, `plan_estimate`, `resolve_route`; statically calls `Member`, `build_judge`, `build_request`, `caps_from_config`, `plan_estimate`, `resolve_route`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `GroupOutcome`, `Member`, `build_judge`, `build_request`, `caps_from_config`, `resolve_route`; statically calls `Member`, `build_judge`, `build_request`, `caps_from_config`, `resolve_route`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `PROMPT_VERSION`, `resolve_route`; statically calls `resolve_route`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `PROMPT_VERSION`, `resolve_route`; statically calls `resolve_route`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `TASK`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; calls `call_labels`, `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `DEFAULT_OUTPUT_TOKENS`, `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `module`, `ready_client_for_task`; calls `is_decider_profile`, `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/matching/union|learnloop.matching.union]] — imports `module`; calls `UnionEdge`, `union_with_refusals`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `math`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]], [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_fakes.py](../../../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_a_failing_judge_is_retried_within_the_cap_then_gives_up`
  - `test_a_rerun_of_the_decider_reuses_its_answers_and_ledger_rows`
  - `test_attach_keeps_registered_facets_apart_and_makes_one_survive`
  - `test_judge_writes_one_ledger_row_per_pair_and_never_pays_twice`
  - `test_partition_validation_is_conservative`
  - `test_spend_caps_stop_the_judge_before_a_call`
  - `test_the_decider_answers_per_pair_choices_and_partitions`
  - `test_the_decider_asks_one_choice_question_per_pair`
  - `test_the_decider_partition_never_chains_against_a_distinct_verdict`
  - `test_the_ledger_keeps_the_judges_verdict_and_marks_repaired_and_omitted_pairs`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_a_configured_decider_route_builds_the_decider_judge_without_a_call`
  - `test_dedupe_through_a_decider_route_merges_and_writes_labelled_receipts`
  - `test_the_decider_partition_is_matchings_no_chaining_union`
  - `test_the_structured_judge_labels_its_receipts_llm`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import

## Modification guidance

- Change judge policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/judge.py](../../../../../../../src/learnloop/content/facet_identity/judge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

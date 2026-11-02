---
title: "learnloop.content.proposals.method_phrasing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/method_phrasing.py"
source_paths:
  - "src/learnloop/content/proposals/method_phrasing.py"
source_commit: "eb3be2bfb8ff61fc25e4ca0b492de25822ae7ac5"
source_commit_timestamp: "2026-10-23T12:29:53-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.method_phrasing module"
  - "src/learnloop/content/proposals/method_phrasing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.method_phrasing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.method_phrasing` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: ``learnloop grading method-phrasing``: criteria phrased by method, and their repairs.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py) |
| Source lines | 1231 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `eb3be2bfb8ff61fc25e4ca0b492de25822ae7ac5` |
| Commit timestamp | `2026-10-23T12:29:53-04:00` |

## Public API

- `default_caps(items: int) -> SpendCaps` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 141) — Two requests per item at most (a reading and a rewrite), and $0.50.
- `class CriterionPhrasingReading(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 167)
- `class RubricPhrasingReading(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 178)
- `judge_prompt(item: PracticeItem, rubric: Any, targets: Sequence[MethodTarget]) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 196)
- `decider_state(item: PracticeItem, rubric: Any) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 211) — What the Decider reads: the item and its criteria.
- `decider_question(criterion: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 225)
- `class JudgeRoute` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 241)
  - `as_dict(self) -> dict[str, Any]` (line 253; public)
- `writer_name(vault: LoadedVault) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 282) — The chat profile that judges as the LLM judge and writes fact phrasings.
- `writer_names(vault: LoadedVault) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 302) — Every chat profile a run may write with, in the order it tries them (re-review F11): :func:`writer_name`, then ``ai.fallback_provider`` exactly where :func:`_ready_writer` falls back to it (an unset route without an environment override and with a serving provider, as the task r…
- `can_write(client: Any) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 334) — Can ``client`` serve the writer's call (an isolated structured completion)?
- `decider_profile_name(vault: LoadedVault) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 389) — The decider profile ``ai.routing.rubric_phrasing_judge`` names, or the Tier-1 Decider's (``ai.routing.tier1_decider``, else the code default) when the route is unset; None when it names a chat profile.
- `ready_profile_client(vault: LoadedVault, name: str | None) -> Any | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 397) — A ready client for the profile ``name`` on the judge route, or None.
- `ready_writer(vault: LoadedVault, injected: Mapping[str, Any] | None=None) -> tuple[Any | None, str | None]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 403) — The LLM judge (and writer) on the judge route: (client, profile), or (None, profile) when none can serve an isolated structured completion.
- `resolve_judge(vault: LoadedVault, requested: str='auto', *, clients: Mapping[str, Any] | None=None) -> JudgeRoute` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 410) — Decider, else the LLM judge, else the heuristic (or the one ``requested``).
- `class CriterionReading` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 451)
  - `as_dict(self) -> dict[str, Any]` (line 477; public)
  - `judgment_ids(self) -> list[str]` (line 480; public)
- `class IncompleteJudgment(ValueError)` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 484) — A judge's reading that does not cover exactly the item's criteria, once each.
- `candidate_items(vault: LoadedVault, item_ids: Sequence[str] | None=None) -> list[PracticeItem]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 488) — Active items with their own rubric (the default rubrics are doctor's), sorted.
- `heuristic_readings(item: PracticeItem) -> list[CriterionReading]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 506)
- `deterministic_fact_draft(description: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 533) — A DRAFT fact phrasing: the criterion with its method clause removed.
- `llm_readings(item: PracticeItem, targets: Sequence[MethodTarget], client: Any, budget: _Budget, *, only: set[str] | None=None) -> tuple[list[CriterionReading], str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 632) — One structured call: every criterion's phrasing (and the rewrites).
- `decider_readings(item: PracticeItem, client: Any, budget: _Budget) -> tuple[list[CriterionReading], str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 671) — One Decider request: a choice question per criterion (a required method's own criteria are not asked: fact by design).
- `repair_plan(vault: LoadedVault, item: PracticeItem, readings: Sequence[CriterionReading]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 743) — One item's repair: the updated rubric (and required method).
- `persist_repairs(vault: LoadedVault, repository: Repository, plans: Sequence[Mapping[str, Any]], *, judge: JudgeRoute, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 855) — One pending proposal batch (never auto-applied): an update per item.
- `plan_dry_run(vault: LoadedVault, items: Sequence[PracticeItem], *, judge: str, caps: SpendCaps, price_per_million: float | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 919) — What a run would send and cost, from configuration alone (review F7).
- `run_method_phrasing(vault: LoadedVault, *, judge: str='auto', item_ids: Sequence[str] | None=None, propose: bool=False, dry_run: bool=False, caps: SpendCaps | None=None, price_per_million: float | None=None, clients: Mapping[str, Any] | None=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 1064) — Read the items' criteria, report the method-phrased ones, optionally propose repairs.
- `write_report(report: Mapping[str, Any], output_dir: Path) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 1193)

### Module constants

- `REPORT_VERSION` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 117)
- `JUDGE_PROMPT_VERSION` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 120)
- `DECIDER_QUESTION_SET` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 121)
- `LEDGER_TASK` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 122)
- `LEDGER_LEFT_KIND` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 123)
- `PROPOSAL_PURPOSE` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 124)
- `RECEIPT_OWNER_KIND` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 125)
- `ROUTE` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 126)
- `DECIDER_ROUTE` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 127)
- `LLM_PURPOSE` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 128)
- `JUDGE_CHOICES` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 130)
- `DECIDER_OPTIONS` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 132)
- `DECIDER_METHOD_THRESHOLD` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 137)
- `LLM_OUTPUT_TOKENS` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 138)
- `_JUDGE_TASK` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 182)
- `_THIRD` ([src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 517)

### Explicit exports

`__all__` declares:

- `CriterionPhrasingReading`
- `CriterionReading`
- `IncompleteJudgment`
- `DECIDER_QUESTION_SET`
- `JUDGE_PROMPT_VERSION`
- `JudgeRoute`
- `LEDGER_TASK`
- `PROPOSAL_PURPOSE`
- `REPORT_VERSION`
- `RubricPhrasingReading`
- `candidate_items`
- `decider_readings`
- `decider_profile_name`
- `default_caps`
- `deterministic_fact_draft`
- `heuristic_readings`
- `judge_prompt`
- `llm_readings`
- `persist_repairs`
- `plan_dry_run`
- `ready_profile_client`
- `ready_writer`
- `repair_plan`
- `resolve_judge`
- `run_method_phrasing`
- `can_write`
- `write_report`
- `writer_name`
- `writer_names`

## Internal implementation anchors

- `_estimate_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 149) — An upper bound on the input tokens of ``text``: its UTF-8 bytes (the PF convention, ``learnloop.ops.pf_calls.estimate_tokens``).
- `_route_names(vault: LoadedVault) -> tuple[str | None, str | None]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 263) — (decider profile, chat profile) the judge route names, or would default to.
- `_ready(vault: LoadedVault, name: str | None) -> Any | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 347)
- `_ready_writer(vault: LoadedVault, injected: Mapping[str, Any]) -> tuple[Any | None, str | None]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 356) — (the writer client, its profile), or (None, profile) when none can write.
- `_required_ids(item: PracticeItem) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 502)
- `_third_person(verb: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 520)
- `class _Budget` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 563) — Route registration and admission over one review spend.
- `_input_hash(payload: Any) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 583)
- `_ledger(repository: Repository, readings: Sequence[CriterionReading], *, judge: str, judge_model: Any, prompt_version: str, input_hash: str, now: str, writer: bool=False) -> None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 587) — Append each JUDGED reading's verdict and keep its id (a required method's own criterion, fact by design, is not a verdict).
- `_check_coverage(item: PracticeItem, returned: Sequence[str]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 616) — Exactly the item's criteria, once each (review F5): a missing, duplicated or unknown id is an incomplete judgment, never a verdict.
- `_judged_criteria(item: PracticeItem) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 707)
- `_decider_tokens(item: PracticeItem) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 711) — The input tokens one Decider request for ``item`` is admitted with (an upper bound: the state and every question's instructions and options).
- `_llm_tokens(prompt: str) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 722) — The input tokens one LLM judge or writer request is admitted with (an upper bound: the prompt and the result schema the transport sends).
- `_source_statement(item: PracticeItem) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 732) — A source-authored statement: never rewritten, and its required method is decided once at import (or by the owner), never by a repair.
- `_teach_back(item: PracticeItem) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 739)
- `_attempted_items(repository: Repository, item_ids: Sequence[str]) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 904)
- `_profile(vault: LoadedVault, name: str | None) -> Any | None` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 915)
- `_priced_step(spend: ReviewSpend, info: RouteInfo, step: str, count_key: str, count: int, input_tokens: int, output_tokens: int, owner_price: float | None, refused: list[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/method_phrasing.py), line 1037)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `candidate_items`, `default_caps`, `run_method_phrasing`, `write_report`; statically calls `candidate_items`, `default_caps`, `run_method_phrasing`, `write_report`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `ROUTE`, `decider_profile_name`, `ready_profile_client`, `ready_writer`; statically calls `decider_profile_name`, `ready_profile_client`, `ready_writer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `MANUAL_PROVIDER`, `configured_fallback`, `is_decider_profile`, `is_generation_profile`, `ready_client_for_task`; calls `configured_fallback`, `is_decider_profile`, `is_generation_profile`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `ISOLATED_TURN`, `STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DECIDER_PROFILE_TYPE`, `DEFAULT_DECIDER_PROVIDER`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `compute_target_hash`; calls `compute_target_hash`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `receipt_sink`; calls `receipt_sink`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `CRITERIA_BY_FACT_GUIDANCE`, `MethodTarget`, `advisory_statement_flag`, `best_target`, `is_source_statement`, `method_phrase`, `method_targets`, `names_match`; calls `advisory_statement_flag`, `best_target`, `is_source_statement`, `method_phrase`, `method_targets`, `names_match`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `os`, `pathlib`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]], [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_judges_decider_defaults_to_the_tier1_deciders_profile`
- [tests/test_method_phrasing_report.py](../../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_a_repair_adds_the_field_and_only_flags_a_statement_that_may_disagree`
  - `test_a_repair_never_rewrites_a_source_statement_or_gives_a_teach_back_a_method`
  - `test_auto_tries_the_decider_then_the_llm_judge_then_the_heuristic`
  - `test_f11_an_explicit_chat_route_or_an_env_override_has_no_fallback_writer`
  - `test_f11_an_unset_route_without_a_serving_provider_reaches_no_fallback`
  - `test_f11_the_dry_run_prices_the_configured_fallback_writer`
  - `test_f3_a_repair_refuses_a_rubric_edited_before_acceptance`
  - `test_f3_an_accepted_repair_writes_no_proposal_only_key`
  - `test_f4_a_decider_on_the_route_is_never_the_writer`
  - `test_f4_a_failed_rewrite_keeps_the_deciders_paid_flags_with_labelled_drafts`
  - `test_f5_an_incomplete_reading_is_a_failed_item_never_a_fact_verdict`
  - `test_f5_the_required_methods_own_criteria_are_never_ledgered_as_verdicts`
  - `test_f6_the_writers_verdicts_reach_the_ledger_linked_to_the_repair`
  - `test_f7_the_dry_run_plans_rewrites_and_their_cost`
  - `test_repairs_are_pending_proposals_applied_only_on_accept`
  - `test_t1_a_plan_writer_never_falls_back_silently_to_a_metered_writer`
  - `test_the_decider_flags_and_the_llm_route_writes_the_fact_phrasings`
  - `test_the_deterministic_draft`
  - `test_the_dry_run_plans_and_builds_no_client`
  - `test_the_heuristic_flags_explicit_method_phrasing_and_drafts_repairs`
  - `test_the_llm_contract_round_trips`
  - `test_the_llm_judge_reads_and_rewrites_and_its_verdicts_reach_the_ledger`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f6_codex_is_never_a_fallback_through_the_direct_readers_opt_in_or_not`
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`

## Modification guidance

- Change method phrasing policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/method_phrasing.py](../../../../../../../src/learnloop/content/proposals/method_phrasing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

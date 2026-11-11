---
title: "learnloop.decider_judgments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/decider_judgments.py"
source_paths:
  - "src/learnloop/decider_judgments.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.decider_judgments module"
  - "src/learnloop/decider_judgments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.decider_judgments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.decider_judgments` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Tier-1 small judgments decided by the Decider (owner decision 2026-10-13).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py) |
| Source lines | 517 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NoClearAnswer(ValueError)` ([source](../../../../../src/learnloop/decider_judgments.py), line 78) — The Decider's top probability is shared by two or more options: it decides nothing (review F8).
- `argmax(probabilities: Mapping[str, float]) -> str | None` ([source](../../../../../src/learnloop/decider_judgments.py), line 82) — The single option with the highest probability; None when the top is tied (or nothing is there).
- `enabled(config: Any, task: str) -> bool` ([source](../../../../../src/learnloop/decider_judgments.py), line 98) — Whether the Decider decides ``task`` for this vault's config (its switch and version).
- `connection_note(config: Any) -> str | None` ([source](../../../../../src/learnloop/decider_judgments.py), line 116) — The AI connection sheet's sentence about the Decider (UX Phase 1's one OK, Q4; D6), or None.
- `client_for(root: Any, config: Any) -> Any` ([source](../../../../../src/learnloop/decider_judgments.py), line 169) — The ready Decider client of ``ai.routing.tier1_decider``; raises when it is not ready.
- `class Decision` ([source](../../../../../src/learnloop/decider_judgments.py), line 181) — One Tier-1 check: ``choice`` is the argmax option, or None (``status`` says why).
  - `detail(self) -> dict[str, Any]` (line 197; public)
- `record_failure(repository: Any, decision: Decision, *, error: str | None=None) -> Decision` ([source](../../../../../src/learnloop/decider_judgments.py), line 215) — Ledger a check that gave no answer (``decision.status``), for a caller that asked the Decider itself.
- `route_rule(config: Any, route: str) -> tuple[str, str | None]` ([source](../../../../../src/learnloop/decider_judgments.py), line 252) — Why ``route`` had no ready Decider to ask (``no_decider_routed`` or ``decider_not_ready``) and the profile it names, read from the configuration: no client is built.
- `log_llm(repository: Any, decision: Decision, *, choice: str, model: str, rationale: str='') -> str` ([source](../../../../../src/learnloop/decider_judgments.py), line 281) — The fallback LLM's verdict on the Decider's input, as a real pair for the agreement report.
- `decide(*, root: Any, config: Any, repository: Any, task: str, state: Any, question: ChoiceQuestion, left_kind: str='input', left_id: str | None=None, right_kind: str | None=None, right_id: str | None=None, client_factory: Callable[[], Any] | None=None, spend: Any=None, input_hash: str | None=None, ledger_task: str | None=None, question_name: str='verdict', candidates: int=0, pairs: int=0, judgment_id: str | None=None, admit: Admit | None=None, rationale: Mapping[str, Any] | None=None, route: str=ROUTE, reuse: bool=False) -> Decision` ([source](../../../../../src/learnloop/decider_judgments.py), line 289) — Ask the Decider one typed question; a disabled judgment returns ``status='disabled'`` unasked.
- `ask_decider(client: Any, *, config: Any, repository: Any, task: str, state: Any, questions: dict[str, Any], owner_id: str, route: str, spend: Any=None, question_set_version: str=VERSION, timeout_seconds: float | None=None) -> Any` ([source](../../../../../src/learnloop/decider_judgments.py), line 420) — One admitted Decider request for a caller that keeps its own ledger rows (the Reader's intent box, ``learnloop.reader.reader_intent``; the hint chooser, ``learnloop.hints.chooser``): the same admission and receipts as :func:`decide` (owner kind ``task``), on ``route``'s listed p…
- `decide_many(*, root: Any, config: Any, repository: Any, task: str, state: Any, questions: dict[str, ChoiceQuestion], left_kind: str, left_id: str, spend: Any=None, candidates: int=0) -> dict[str, Decision]` ([source](../../../../../src/learnloop/decider_judgments.py), line 436) — One physical request for independent questions about one input; one ledger row per question.

### Module constants

- `ROUTE` ([src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py), line 54)
- `VERSION` ([src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py), line 56)
- `SERVING_TASKS` ([src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py), line 58)
- `CONTENT_TASKS` ([src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py), line 69)
- `FAILURE_VERDICTS` ([src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py), line 73)

### Explicit exports

`__all__` declares:

- `CONTENT_TASKS`
- `FAILURE_VERDICTS`
- `ROUTE`
- `SERVING_TASKS`
- `VERSION`
- `Decision`
- `NoClearAnswer`
- `argmax`
- `ask_decider`
- `client_for`
- `connection_note`
- `decide`
- `decide_many`
- `enabled`
- `log_llm`
- `record_failure`

## Internal implementation anchors

- `_append(repository: Any, decision: Decision, *, judge: str, choice: str, model: str, rationale: Mapping[str, Any], judgment_id: str | None=None, prompt_version: str=VERSION) -> str` ([source](../../../../../src/learnloop/decider_judgments.py), line 202)
- `_record_unanswered(repository: Any, config: Any, decision: Decision, *, task: str, route: str, outcome: Callable[[], tuple[str, str, dict[str, Any] | None]], error: BaseException | None=None) -> None` ([source](../../../../../src/learnloop/decider_judgments.py), line 230) — The decision record of a check that gave no answer (refactor B5): a disabled switch or a Decider never routed leaves no ledger row, and the ledger's ``unavailable``/``failed`` names neither the cause nor the limit.
- `_unanswered(config: Any, route: str, status: str, error: BaseException | None, *, client_ready: bool) -> tuple[str, str, dict[str, Any] | None]` ([source](../../../../../src/learnloop/decider_judgments.py), line 266) — A failed check's record status, rule and facts: which limit refused, or why no Decider was there to ask.
- `_recorded(repository: Any, decision: Decision, question: ChoiceQuestion) -> Decision | None` ([source](../../../../../src/learnloop/decider_judgments.py), line 357) — The latest answer (an option, never a failure) already ledgered for ``decision``'s input.
- `_ask(client: Any, *, config: Any, repository: Any, task: str, state: Any, questions: dict[str, Any], owner_id: str, spend: Any=None, candidates: int=0, pairs: int=0, admit: Admit | None=None, route: str=ROUTE, question_set_version: str=VERSION, timeout_seconds: float | None=None) -> Any` ([source](../../../../../src/learnloop/decider_judgments.py), line 383)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `module`; statically calls `enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `client_for`, `module`; statically calls `argmax`, `client_for`, `enabled`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ask_decider`; statically calls `ask_decider`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `VERSION`, `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `CONTENT_TASKS`, `SERVING_TASKS`, `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `decide`; statically calls `decide`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `FAILURE_VERDICTS`, `decide`, `enabled`, `log_llm`; statically calls `decide`, `enabled`, `log_llm`
- [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]] — imports `Admit`, `Decision`, `decide`, `log_llm`; statically calls `decide`, `log_llm`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `FAILURE_VERDICTS`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `Decision`, `FAILURE_VERDICTS`, `NoClearAnswer`, `VERSION`, `argmax`, `decide`, `record_failure`; statically calls `Decision`, `NoClearAnswer`, `argmax`, `decide`, `record_failure`
- [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]] — imports `Decision`, `decide_many`, `log_llm`; statically calls `decide_many`, `log_llm`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `ask_decider`, `route_rule`; statically calls `ask_decider`, `route_rule`
- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `decide`; statically calls `decide`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `enabled`; statically calls `enabled`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `ask_decider`; statically calls `ask_decider`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `ask_decider`; statically calls `ask_decider`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `connection_note`; statically calls `connection_note`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `MAX_QUESTIONS`, `choice_probabilities`; calls `choice_probabilities`
- [[Reference/Modules/learnloop/ai/disclosures|learnloop.ai.disclosures]] — imports `decider_destination`; calls `decider_destination`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`; calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendLimitExceeded`; calls `SpendCaps`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DECIDER_TIER1_VERSIONS`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `module`; calls `decider_record`, `disabled_rule`, `route_rule`, `spend_rule`, `write`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]], [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] and 17 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_fakes.py](../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/facet_span_support_helpers.py](../../../../../tests/facet_span_support_helpers.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_replay_reads_receipts_zero_model_calls`
- [tests/test_decider_agreement.py](../../../../../tests/test_decider_agreement.py) — direct import
  - `test_agreement_cli_is_read_only_and_reads_review_runs`
- [tests/test_decider_landing.py](../../../../../tests/test_decider_landing.py) — direct import
  - `test_a_tied_span_check_inside_an_automatic_build_waits_for_the_owner`
  - `test_an_automatic_builds_apply_asks_the_span_check_before_the_vault_lock`
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
  - `test_nothing_in_tier1_reads_the_deleted_route_check`
  - `test_the_tier1_disclosure_and_the_one_ok_use_one_recipient_for_a_direct_perplexity_route`
  - `test_tier1_judgments_move_only_at_mvp022`
  - `test_with_every_decider_route_off_the_one_ok_is_unchanged`
- [tests/test_facet_reword_confirm.py](../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_cited_reword_records_its_sources_on_the_facets_history`
  - `test_a_confirm_refuses_when_the_facets_wording_changed_since`
- [tests/test_facet_span_support.py](../../../../../tests/test_facet_span_support.py) — direct import
  - `test_exam_only_support_is_refused_before_the_decider_and_the_owner_edit_bypasses_it`
  - `test_keeping_a_card_that_went_stale_is_no_label`
  - `test_only_a_registered_facets_meaning_is_checked`
  - `test_the_span_check_is_asked_before_the_vault_lock_is_taken`
- [tests/test_method_explicit_landing.py](../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_statement_judgment_is_a_tier1_content_task_with_its_own_switch`
- [tests/test_mvp022_upgrade.py](../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_each_version_moves_the_judgments_only_at_the_successor`
  - `test_new_vaults_start_at_a_successor_with_the_deciders_judgments`
  - `test_upgrade_from_mvp021_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp023_upgrade.py](../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_the_routers_decider_route_is_never_a_tier1_judgment_at_the_successor`
- [tests/test_refusal_records.py](../../../../../tests/test_refusal_records.py) — direct import
- [tests/test_tier1_decider.py](../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_cancellation_is_never_a_fallback`
  - `test_a_decider_cancellation_in_misconception_matching_never_reaches_the_llm`
  - `test_a_review_resume_refuses_a_changed_decider_profile`
  - `test_a_tied_batch_question_has_no_choice`
  - `test_a_tied_top_option_is_no_answer_and_hands_over`
  - `test_contamination`
  - `test_contamination_one_routes_switch_restores_its_old_checkpoints_budget_check_and_ledger`
  - `test_decider_receipt_and_spend_ignore_llm_output_budget`
  - `test_field_question_classification`
  - `test_link_judgments`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`
  - `test_misconception_match`
  - `test_misconception_match_without_a_model_asks_no_decider`
  - `test_needed_is_the_deciders_and_its_refusal_falls_back`
  - `test_route_decision_fallback_and_switch`
  - `test_serving_judgments_wait_for_the_successor_and_the_router_is_never_tier1`
  - `test_settings_and_eval_judges_disclose_the_tier1_routes`
  - `test_text_gap_kind_is_reused_never_paid_for_twice`

## Modification guidance

- Make changes here when the responsibility remains decider judgments within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/decider_judgments.py](../../../../../src/learnloop/decider_judgments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

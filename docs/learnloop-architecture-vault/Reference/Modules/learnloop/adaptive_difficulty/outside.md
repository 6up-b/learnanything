---
title: "learnloop.adaptive_difficulty.outside"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/outside.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/outside.py"
source_commit: "a0516ec0ba817c588d166d0dab5c7ee89bc2bd63"
source_commit_timestamp: "2026-11-01T14:48:24-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.outside module"
  - "src/learnloop/adaptive_difficulty/outside.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.outside`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.outside` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The outside forecasters (spec_adaptive_difficulty_v1 §8.1-8.2, §7.3, D4; AD1, switch ``outside_forecasters``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py) |
| Source lines | 777 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a0516ec0ba817c588d166d0dab5c7ee89bc2bd63` |
| Commit timestamp | `2026-11-01T14:48:24-05:00` |

## Public API

- `class ItemForecastV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 125) — The LLM's answer: a probability strictly between 0 and 1.
- `item_view(vault: Any, item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 136) — V1's content: the stem, LO and facet names; no answer, rubric, hints or label.
- `source_identity(item: Any, practice_item_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 166) — A revision's protection identity: its item id and its own source references.
- `answer_excerpts_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 185) — ``adaptive_difficulty.history_answer_excerpts`` (learner-blindness relax; default on).
- `history_card(vault: Any, connection: Any, item: Any, *, served_at: str, view: Any, incumbent: Mapping[str, Any] | None, answers: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 192) — The learner's history on the item's LO and its prerequisites, as of the serve, read through the serve's material view (no withheld item's attempt is ever on the card).
- `class ForecastOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 242)
  - `as_dict(self) -> dict[str, Any]` (line 249; public)
- `class Clients` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 254) — Injected clients (tests, a sidecar's ``ad_clients``); None resolves the route.
- `item_prompt(vault: Any, item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 415) — ``llm_v1:item``'s prompt for one revision (the backfill's dry run plans it too).
- `forecast_item(vault: Any, repository: Any, item: Any, *, clients: Clients | None=None, clock: Clock | None=None, protected: Any=None, fence: Any=None, live_vault: Callable[[], Any] | None=None) -> ForecastOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 425) — ``llm_v1:item`` for one item revision (once per revision, under its durable claim).
- `frozen_state_key(presentation_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 542)
- `freeze_presentation_inputs(vault: Any, connection: Any, item: Any, *, presentation_id: str, served_at: str, protected: Any, view: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 546) — In the serve transaction: the exact ``llm_v3`` request inputs of one presentation.
- `forecast_presentation(vault: Any, repository: Any, presentation_id: str, *, clients: Clients | None=None, clock: Clock | None=None, fence: Any=None, live_vault: Callable[[], Any] | None=None) -> list[ForecastOutcome]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 607) — ``llm_v3:llm`` and ``llm_v3:decider`` for one plan presentation, from its frozen serve inputs.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 94)
- `STATE_VERSION` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 96)
- `STATE_VERSION_ANSWER_EXCERPTS` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 100)
- `HISTORY_ANSWER_LIMIT` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 102)
- `V1_PROMPT_VERSION` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 103)
- `V3_PROMPT_VERSION` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 104)
- `DECIDER_QUESTION_SET` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 105)
- `LLM_ROUTE` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 106)
- `DECIDER_ROUTE` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 107)
- `PURPOSE` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 108)
- `STEM_LIMIT` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 109)
- `HISTORY_STEM_LIMIT` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 110)
- `HISTORY_LIMIT` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 111)
- `V1_QUESTION` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 112)
- `V3_QUESTION` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 113)
- `DECIDER_QUESTIONS` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 114)
- `_CAPS` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 122)
- `FROZEN_STATE_PREFIX` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 538)
- `FROZEN_STATE_FORECASTER` ([src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 539)

### Explicit exports

`__all__` declares:

- `Clients`
- `DECIDER_QUESTIONS`
- `ForecastOutcome`
- `ItemForecastV1`
- `forecast_item`
- `forecast_presentation`
- `freeze_presentation_inputs`
- `frozen_state_key`
- `history_card`
- `item_prompt`
- `item_view`
- `source_identity`

## Internal implementation anchors

- `_excerpt(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 131)
- `_result(correctness: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 155)
- `_llm_client(vault: Any, injected: Any | None) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 261)
- `_decider_client(vault: Any, injected: Any | None) -> Any | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 271)
- `_store_payloads(repository: Any, owner_key: str, forecaster: str, request: Any, response: Any, now: str, retention_days: int) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 282)
- `_ask_llm(vault: Any, repository: Any, client: Any, *, prompt: str, owner_id: str, envelope: Any, send: SendGuard) -> tuple[float | None, dict[str, Any], str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 295)
- `_ask_decider(vault: Any, repository: Any, client: Any, *, state: Any, owner_id: str, envelope: Any, send: SendGuard) -> tuple[float, dict[str, Any], str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 316)
- `_receipt(*, key: str, forecaster: str, version: str, scope: str, decision_kind: str, binding_kind: str, inputs: Mapping[str, Any], inputs_as_of: str, p: float | None, status: str, received_at: str, columns: Mapping[str, Any], model: str | None, request_hash: str, state_version: str=STATE_VERSION) -> ForecastReceipt` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 326)
- `_existing(connection: Any, key: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 342)
- `_verdict_text(p: float) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 347)
- `_record_admission(send: SendGuard, outcome: ForecastOutcome) -> Callable[[], None] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 351) — The forecast's record admission, or None when its content is protected now.
- `_protected(outcome: ForecastOutcome, exc: Exception) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 370)
- `_write(repository: Any, vault: Any, receipt: ForecastReceipt, *, created_at: str, payload_key: str, request: Any, response: Any, received: str, judgment: Mapping[str, Any] | None, admit: Callable[[], None] | None=None) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 374) — The forecast's payloads, its receipt and (accepted) its judgment, in one transaction.
- `_forecast_item(vault: Any, worker: Any, item: Any, client: Any, *, content_hash: str, key: str, outcome: ForecastOutcome, clock: Clock | None, send: SendGuard) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 472)
- `_incumbent_inputs(connection: Any, presentation_id: str, view: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 524)
- `_frozen_inputs(connection: Any, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 590)
- `_forecast_one(vault: Any, worker: Any, name: str, presentation: Mapping[str, Any], frozen: Mapping[str, Any], *, clients: Clients, clock: Clock | None, send: SendGuard) -> ForecastOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/outside.py), line 683)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `Clients`, `ItemForecastV1`, `LLM_ROUTE`, `_CAPS`, `forecast_item`, `item_prompt`; statically calls `forecast_item`, `item_prompt`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `Clients`, `forecast_item`, `forecast_presentation`; statically calls `forecast_item`, `forecast_presentation`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `freeze_presentation_inputs`; statically calls `freeze_presentation_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`, `item_forecast_key`, `presentation_key`; calls `claimed`, `item_forecast_key`, `presentation_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `EVENT`, `INCUMBENT`, `receipt_key`; calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`, `material_view`; calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`, `epoch_of`; calls `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `guard`; calls `guard`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `SendGuard`, `module`, `refusal_status`; calls `SendGuard`, `ask_decider`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_V1`, `LLM_V3_DECIDER`, `LLM_V3_LLM`, `outside_forecasters`; calls `outside_forecasters`
- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `NoulQuestion`; calls `NoulQuestion`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`; calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `item_source_keys`; calls `item_source_keys`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `insert_payload`, `prune_payloads`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `module`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`, `resolve_client`; calls `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `FIRST_PRESENTATION`, `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`, `record_receipts`; calls `ForecastReceipt`, `record_receipts`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
  - `test_an_edit_during_a_preparation_prepares_the_new_revision_too`
  - `test_frozen_inputs_without_their_source_identities_are_never_sent`
  - `test_the_worst_case_plans_the_permitted_truncation_retry`
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_claim_held_by_another_process_is_skipped`
  - `test_a_presentation_without_frozen_inputs_is_never_forecast`
  - `test_a_refused_forecast_appends_no_judgment`
  - `test_a_reload_prepares_the_revisions_published_since_the_last_load`
  - `test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id`
  - `test_a_vault_switch_fences_the_outside_forecasters`
  - `test_accepted_outside_forecasts_append_one_judgment_each`
  - `test_historical_snapshots_of_held_out_material_are_never_audited`
  - `test_outside_forecasts_send_the_inputs_frozen_at_the_serve`
  - `test_overlapping_preparations_audit_a_revision_once`
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_a_same_vault_reload_adding_an_exam_scope_refuses_the_next_request_and_the_record`
  - `test_an_answer_after_a_vault_switch_writes_no_checkpoint_and_settles_its_spend`
  - `test_an_import_of_1000_revisions_prepares_at_most_20_per_run`
  - `test_two_watcher_batches_share_one_worker`
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_a_refused_spend_revision_is_retried_on_the_next_reload`
  - `test_an_exception_before_the_first_revision_keeps_the_whole_batch`
  - `test_an_exception_keeps_the_revision_that_raised_queued`
  - `test_busy_unavailable_and_incomplete_revisions_stay_queued`
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_harmless_reload_between_the_audits_check_and_its_record_is_retried`
  - `test_a_revision_that_keeps_raising_never_starves_the_rest`
  - `test_a_stale_refusal_reports_stale_and_held_out_content_reports_protected`
  - `test_four_interrupted_checks_are_stale_and_retried`
  - `test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt`
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — direct import
  - `test_a_refusal_at_the_deciders_start_receipt_stops_the_request`
- [tests/test_ad1_fix_round8.py](../../../../../../tests/test_ad1_fix_round8.py) — direct import
  - `test_a_cleanup_failure_after_a_refusal_is_logged_and_the_refusal_stands`
  - `test_any_failure_at_ads_start_receipt_stops_the_dispatch`
  - `test_the_item_forecasts_start_receipt_fails_closed_with_the_right_status`
- [tests/test_ad1_fix_round9.py](../../../../../../tests/test_ad1_fix_round9.py) — direct import
  - `test_the_backfill_records_a_stopped_audit_as_failed`
  - `test_the_queue_keeps_a_stopped_audit_for_a_retry`
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_a_metered_llm_route_without_a_price_is_refused_before_sending`
  - `test_background_jobs_run_off_the_request_path_once_each`
  - `test_the_daily_cap_refuses_a_metered_call_once_spent`
- [tests/test_ad1_send_guard.py](../../../../../../tests/test_ad1_send_guard.py) — direct import
  - `test_a_unit_held_out_while_the_backfill_runs_refuses_its_later_forecasts`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_z_v1_calibration_never_reads_a_withheld_items_forecast`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_revision_prepared_while_protected_is_prepared_once_it_is_public`
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
  - `test_the_synchronous_preparation_counts_visible_revisions_only`
  - `test_twenty_protected_revisions_queued_first_never_hold_back_the_public_one`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_ad1_switches_restore_predecessor`
  - `test_held_out_sentinel_never_reaches_ad_inputs`
  - `test_item_only_forecast_enters_inputs_only_if_received_before_serve`
  - `test_replay_reads_receipts_zero_model_calls`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_frozen_state_version_follows_the_switch`
  - `test_the_history_card_carries_bounded_answer_excerpts_only_while_on`

## Modification guidance

- Make changes here when the responsibility remains outside within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/outside.py](../../../../../../src/learnloop/adaptive_difficulty/outside.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

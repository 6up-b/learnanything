# Structured contracts, step 5

Status: **adopted**. The follow-up question's re-ask runs on the shared step; every baseline case sends the
same number of requests and ends the same way as before.

## Ruling and the bound

The orchestrator ruled that exact preservation wins. The owner's “one re-ask” means
one **contract** re-ask. A provider's schema repair addresses a different failure and
retains its existing allowance, independently for the first and corrective attempt.
Both still require explicit caller admission, remaining time and no cancellation.
`MAX_STRUCTURED_RECOVERIES = 1` now counts contract corrections only. Its registered
rationale and the step-0 amendment say so.

For the specified schema/contract sequences the tested bound is two authoring
attempts, each with at most one schema repair: four physical requests. Both providers
reach four today. Neither the job's two-lease limit nor its provider disables the
correction's repair. Failed repairs get no second schema repair; a second contract
failure gets no second contract correction.

Both providers also retain **transient transport retries**:
`chatgpt_plan._send` and `openai_chat._create_with_retry` allow three physical sends.
A socket-free scratch comparison executed the original `HEAD` jobs module in an
isolated namespace and the adopted jobs module, with identical provider doubles:

| Additional sequence, both providers | Unadopted | Adopted |
|---|---|---|
| Two transient failures; malformed; repair fails contract; valid correction | 5 requests, ready | 5 requests, ready |

The original jobs module passes no adapter, so shared hooks are inert in the before
run. Its source was read with `git show`; no file was restored, no second worktree
was created, and no private production seam was patched. No model or network call
was made. So the four-request bound is a bound on recovery, not on physical sends.

**Settled (the orchestrator, 2026-11-21):** the bound covers schema and contract recovery only: two authoring
attempts, each with at most one schema repair, so at most four requests from recovery. A provider's transient
transport retries (a throttled or dropped send) are a third, separate mechanism with its own existing limit and
are preserved unchanged, so a job can still reach five physical sends as it can today. Capping them would change
a measured success into a failure and is not part of this step.

## Baseline captured before production edits

The previous worker's baseline files were retained and extended first. With all
production code still unadopted, the added four-request case and the repair/contract/
correction-fails case passed on both providers: `25 passed in 3.04s`.
The baseline expectations and seven prompt digests were not moved.

Every row runs the real workflow, spend admission, transport and provider completion/
repair code, doubled only at the public network seam. Both plan and OpenRouter
have the following equal counts and outcomes:

| Answers / condition | Before requests | Before outcome | After requests | After outcome |
|---|---:|---|---:|---|
| Valid first | 1 | ready | 1 | ready |
| Contract failure, valid correction | 2 | ready | 2 | ready |
| Contract failure twice | 2 | failed | 2 | failed |
| Malformed, valid repair | 2 | ready | 2 | ready |
| Malformed, repair fails contract, valid correction | 3 | ready | 3 | ready |
| Contract failure, malformed correction, valid repair | 3 | ready | 3 | ready |
| Malformed, repair fails contract, malformed correction, valid repair | 4 | ready | 4 | ready |
| Malformed, repair fails contract, correction fails contract | 3 | failed | 3 | failed |
| Deadline passed before queued correction | 1 | failed | 1 | failed |
| Cancelled between requests | 1 | skipped | 1 | skipped |

Additional tests refuse each of the three recovery sends independently for missing
admission, deadline depletion or cancellation. Admission is not consulted when time
or cancellation refuses a send. Schema repairs do not increment contract recoveries.
Failed repairs and second contract failures leave a queued fifth valid answer unused.
These tests cover schema/contract recovery, not a changed transport-retry policy.

## Shared module and changed step-0 assertions

`_Ledger.admit` contains the common cancellation, deadline and admission checks.
`_Ledger.claim` additionally checks and records the contract credit.
`claim_schema_repair` admits without spending that credit, and refuses a second
repair claim in the same attempt. `_run` resets the repair marker per attempt.
The suffix, rejected-answer handling, `owed`/`defer`, recovery receipt linkage and
shared checkpoint implementation are unchanged.

Each changed assertion:

- Chat `test_the_chat_providers_repair_shares_the_one_recovery` was renamed to
  `test_the_chat_providers_repair_is_separate_from_the_contract_recovery`.
  Contract failure then malformed correction now returns `GOOD` after three requests,
  replacing `schema_failed` after two; its allowance explicitly admits two recoveries.
  Malformed then repaired contract failure now returns `GOOD` after three, replacing
  `contract_failed/empty_question_or_key` after two. Its no-admission assertion
  (one request/refused) and outside-checked repair assertion (two/success) are unchanged.
- Plan `test_malformed_then_repaired_then_contract_failing_stops` became
  `test_malformed_then_repaired_then_contract_failing_gets_one_correction`.
  It asserts an accepted third answer, three requests, one contract credit, the
  repair in the penultimate request and the exact correction prompt last, replacing
  `contract_failed/blank_note` after two requests.
- Plan `test_contract_failing_then_a_malformed_correction_gets_no_repair` became
  `test_contract_failing_then_a_malformed_correction_gets_one_repair`.
  It asserts three requests, an accepted answer, one contract credit and a final
  repair prompt, replacing the two-request `AIInvalidOutput` cause / `schema_failed`
  assertions. Both changed plan tests need the orchestrator's loopback sockets.
- The prior worker's four shared-credit conflict comparisons now expect three-request
  success; a two-provider four-request success comparison was added. These were
  pre-adoption measurements, not assertions in the unchanged UX-45 retry suite.
- The restored-spent-credit test only needed its outdated schema-repair comment
  corrected. Its assertions remain unchanged.

No assertion in `tests/test_followup_authoring_retry.py` changed. Step-0 inertness
assertions remain unchanged. Provider production files are unchanged, including
outside-checked request construction and repair behavior.

## Feature predicates and ordering

The six names, requirement lines and order remain in `authoring.py`.
`authoring_contract(refs)` declares them as `Predicate`s observing the first failure
of `check_structure`, the original validation pipeline extracted without reordering.
Terminal failures still raise `AuthoringRejected`. Protection remains after structure
validation in `check_output`, never becomes a predicate requirement, and never enters
a correction message.

Behavioral tests with simultaneous failures prove that `prompt_equals_key` precedes
criteria validation, `predictions_do_not_discriminate` precedes manipulation validation,
an earlier prediction's invalid criteria precede a later prediction's unknown
hypothesis, and an empty question precedes invalid criteria. No source-text assertion
or private production patch site was added.

The first prompt still uses the feature's existing prompt-builder seam. The seven
pre-adoption SHA-256 captures pin its bytes and all six correction suffixes. The
unchanged retry suite also checks initial timeout `None`, remaining-time correction
timeout, schema, receipts, event/state behavior and full deterministic first-success
rows. The blind grader's context is untouched.

## Durable adapter

`followup_run/contract_job.py` maps the job onto the shared mechanism:

| Existing authority/storage | Shared mapping |
|---|---|
| Current leased job, matching attempt count, at most two attempts | `admit`; the router envelope still admits each physical request |
| Initial provider timeout and retry event's persisted deadline | `remaining_seconds` |
| Inclusive one-second floor | `min_request_seconds` uses the adjacent float below 1 because the shared comparison is exclusive; exactly 1 second still sends with timeout 1 |
| Workflow no longer pending or worker cancellation | `cancelled` |
| Retry event JSON | `RecoveryState(0, owed)`, deadline, rejection/attempt numbers, original request key, first-prompt hash and provider settings |
| Existing checkpoint table, key `<job id>:recovery` | Write-once claimed `RecoveryState(1, owed)`, committed before send |
| Existing checkpoint table, original job id | Accepted correction, under the original logical job key |
| Next job lease | `defer=True`; `CorrectionDeferred` becomes existing `AuthoringContractRetry` |

Workflow events are append-only. A transaction checks for an existing claim and the
current lease, then stores the monotone claim in the existing write-once checkpoint
table. No event is updated, no event reason is added, and no migration is needed.
The normal retry retains exactly one `authoring_contract_retry` event. A transport
retry that already used the second lease cannot queue a contract correction.

First successes keep existing item persistence and orphan retirement, with no new
answer checkpoint: existing crash recovery retires an unbound first-success item
and authors a fresh question. Only corrected answers use the new slot.

Receipt recovery reads only this job's completed authoring root receipts with a
correction note naming its original key. It verifies prompt linkage, parses the
current model, reruns the contract and protection checks, and saves the correction.
It precedes the shared spent-state exit. A read-only saved-correction check precedes
the workflow's exhausted-lease exit; `admit` still forbids new requests there.
Rejected and unfinished receipts are never reused.

## Crash tests and development findings

Crash tests use the real workflow SQLite store and `BaseException` at public seams:

1. Queued owed correction survives restart, sends the correction, saves only the
   accepted answer and keeps the three-event sequence.
2. Crash after rejection note but before requeue preserves owed state, with no saved
   answer. The real 900-second lease exceeds the test's 40-second deadline; reclaim
   fails without another send, rather than restarting the deadline. With an original
   2000-second allowance, reclaim instead sends the owed correction within that same
   deadline and reaches ready.
3. Crash after durable claim but before correction send preserves the claim; reclaim
   sends nothing and uses the existing exhausted-attempt exit.
4. Crash after corrected receipt but before answer save recovers the correction under
   the original key on the next lease, even after deadline/cap exhaustion, and reaches
   ready without a third send. A further drain sends nothing. This also passes with
   the original four-field retry event queued before adoption, without a migration.
5. Exactly one second left preserves the original inclusive floor.

The first adapter attempted an event update and hit the append-only guard
(`22 failed, 64 passed`). The write-once claim slot fixed it (`86 passed`). The first
broad run exposed first-success cache reuse interfering with orphan retirement and
a bypassed prompt-builder test seam (`7 failed, 524 passed`). First-success caching
was removed and the seam restored. The identity audit rejected a new schema-derived
key (`1 failed, 385 passed`); the adapter now uses the job's existing identity and
stores prompt/settings guards. A targeted rerun of all those failures, the unchanged
retry suite, baseline, crash tests and identity pins passed: `561 passed in 33.99s`.
No pin, golden or existing preservation assertion was edited to resolve these findings.

The final full requested selection passed: 532, 363 and 26 tests in its three
name-filtered chunks, and 386 in the identity/structure/public-tip/layout/architecture
chunk. Because the structure scanner normally sees only tracked files, an additional
scratch check supplied the four new Python files to that scanner without touching
the index. All prospective ratchets passed, including 465 private patch sites and
23 source-text assertions, unchanged by the new files; the largest import component
remains 84 and modules in import cycles remain 220. The last added crash variants
were rerun separately as recorded below.

## Live-route walk and limits

A live walk should trigger a
follow-up after a miss, reject an empty answer and show one usable question or the
existing failure wording. Inspect first/correction bytes, all six suffixes, admission
and receipts, both three-request orders, the four-request case, deadlines,
cancellation and accepted correction recovery after an actual restart. Exercise
both providers and the chosen transport-retry policy.

Not verified: live models, billing, actual streaming deadlines/cancellation, real
process kills, desktop/phone surfaces, the full suite, arc-close or landing gates.
No network/model calls, secret configuration, owner vaults or local fixtures were
used. The untracked design reference was not edited. No prompt, schema, configuration
key, algorithm tag, kill switch, migration, identity pin or golden was changed.

## Commands and results

All Python tools used the supplied isolated wrappers. Pytest used explicit targets,
at most 30 files per chunk and at most `-n 2`; name-filtered chunks excluded arc-close.
Loopback tests were explicitly deselected, not weakened. Final commands and the
orchestrator's socket list follow below.

### Final requested selections

Selection 1:

```sh
t.sh \
  tests/test_chatgpt_plan_provider.py \
  tests/test_curriculum_c1_round5_followups.py \
  tests/test_e0_review_round4_followup.py \
  tests/test_followup_authoring_retry.py \
  tests/test_followup_codex_review.py \
  tests/test_followup_contract_baseline.py \
  tests/test_followup_contract_recovery.py \
  tests/test_followup_diagnostic_selection.py \
  tests/test_followup_fg1c_codex_review.py \
  tests/test_followup_fg1c_r1_exposure_independence.py \
  tests/test_followup_fg1d_panel_read.py \
  tests/test_followup_fg1d_probe_shadow.py \
  tests/test_followup_generate_e2e.py \
  tests/test_followup_journey.py \
  tests/test_followup_live_shape.py \
  tests/test_followup_migration.py \
  tests/test_followup_next_matrix.py \
  tests/test_followup_reserved_only.py \
  tests/test_followup_rival_factor.py \
  tests/test_followup_router.py \
  tests/test_followup_single_use.py \
  tests/test_followup_successor.py \
  tests/test_followup_workflow.py \
  tests/test_followups.py \
  tests/test_followups_batch5_c5_ledger.py \
  tests/test_followups_batch5_lesson.py \
  tests/test_followups_batch5_recap_dependencies.py \
  tests/test_followups_batch5_recap_protection.py \
  tests/test_followups_batch6_power_probe_cache.py \
  tests/test_followups_batch6_prefetch_decided_once.py \
  -q -n 2 -m 'not arc_close' \
  --deselect=tests/test_chatgpt_plan_provider.py::test_request_shape_follows_the_plan_route_rules \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_chunked_event_stream_is_reassembled \
  --deselect=tests/test_chatgpt_plan_provider.py::test_output_budget_rides_in_the_prompt_never_as_max_output_tokens \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_json_repair_is_sent_with_the_budget_of_the_request_it_repairs \
  --deselect=tests/test_chatgpt_plan_provider.py::test_receipts_name_the_provider_model_and_answering_model \
  --deselect=tests/test_chatgpt_plan_provider.py::test_capabilities_isolated_tool_free_and_bounded \
  --deselect=tests/test_chatgpt_plan_provider.py::test_json_object_mode_carries_the_schema_and_repairs_once \
  --deselect=tests/test_chatgpt_plan_provider.py::test_single_request_never_repairs_or_retries \
  --deselect=tests/test_chatgpt_plan_provider.py::test_transient_failures_retry_with_backoff \
  --deselect=tests/test_chatgpt_plan_provider.py::test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back \
  --deselect=tests/test_chatgpt_plan_provider.py::test_usage_limit_before_the_stream_and_not_eligible \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_401_refreshes_once_and_retries \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_401_under_single_request_fails_and_the_next_call_refreshes \
  --deselect=tests/test_chatgpt_plan_provider.py::test_rejected_structured_output_names_the_setting \
  --deselect=tests/test_chatgpt_plan_provider.py::test_incomplete_truncated_and_broken_streams \
  --deselect=tests/test_chatgpt_plan_provider.py::test_the_deadline_shuts_a_stalled_stream \
  --deselect=tests/test_chatgpt_plan_provider.py::test_an_interrupt_while_waiting_for_the_refresh_lock_sends_nothing \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_deadline_that_passes_while_waiting_for_the_refresh_lock_sends_nothing \
  --deselect=tests/test_chatgpt_plan_provider.py::test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing \
  --deselect=tests/test_chatgpt_plan_provider.py::test_an_expired_deadline_is_never_extended_into_a_send \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_success_that_overlaps_a_usage_limit_keeps_the_pause \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_success_clears_the_expired_pause_it_saw \
  --deselect=tests/test_chatgpt_plan_provider.py::test_signed_out_is_refused_before_any_request \
  --deselect=tests/test_chatgpt_plan_provider.py::test_model_list_keeps_listed_models_in_server_order \
  --deselect=tests/test_chatgpt_plan_provider.py::test_readiness_reads_local_state_only \
  --deselect=tests/test_chatgpt_plan_provider.py::test_billing_class_is_subscription \
  --deselect=tests/test_chatgpt_plan_provider.py::test_t6_rewrite_runs_on_the_plan_with_receipts \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_checked_call_sends_the_first_request_unchanged_and_one_correction \
  --deselect=tests/test_chatgpt_plan_provider.py::test_malformed_then_repaired_then_contract_failing_gets_one_correction \
  --deselect=tests/test_chatgpt_plan_provider.py::test_contract_failing_then_a_malformed_correction_gets_one_repair \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_checked_call_with_no_admitted_recovery_sends_no_plan_repair \
  --deselect=tests/test_chatgpt_plan_provider.py::test_a_background_request_gets_no_fresh_ceiling_past_the_checked_calls_deadline
```

Last result: `532 passed in 161.49s (0:02:41)`.

Selection 2:

```sh
t.sh \
  tests/test_followups_batch6_prefetch_next_section.py \
  tests/test_followups_batch6_prefetch_plan_wait.py \
  tests/test_followups_batch6_review_fixes.py \
  tests/test_followups_batch6_router_report.py \
  tests/test_followups_batch6_te1b_card.py \
  tests/test_followups_batch6_verify_fixes.py \
  tests/test_followups_batch7_note_titles.py \
  tests/test_followups_batch7_prefetch_capped_resume.py \
  tests/test_followups_batch7_prefetch_link_served.py \
  tests/test_followups_nov2_figure_provenance.py \
  tests/test_followups_nov2_help_fold.py \
  tests/test_followups_nov2_note_gap_unlinked.py \
  tests/test_mobile_v2_followup.py \
  tests/test_model_work_checkpoints.py \
  tests/test_openai_chat_client.py \
  tests/test_practice_index_paid.py \
  tests/test_reader_followup_valuation.py \
  tests/test_reader_followups.py \
  tests/test_reader_followups_rereview.py \
  tests/test_reader_followups_review.py \
  tests/test_reader_followups_round3.py \
  tests/test_reader_followups_round4.py \
  tests/test_reader_followups_round5.py \
  tests/test_reader_followups_round6.py \
  tests/test_reader_followups_round7.py \
  tests/test_reader_followups_round8.py \
  tests/test_reader_followups_successor.py \
  tests/test_registry_audit.py \
  tests/test_source_retrieval_followup.py \
  tests/test_structured_contracts.py \
  -q -n 2 -m 'not arc_close'
```

Last result: `363 passed in 66.78s (0:01:06)`.

Selection 3:

```sh
t.sh \
  tests/test_t6_followup_composition.py \
  tests/test_t6_followup_rereview.py \
  tests/test_t6_followup_review.py \
  -q -n 2 -m 'not arc_close' \
  --deselect=tests/test_t6_followup_composition.py::test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort \
  --deselect=tests/test_t6_followup_composition.py::test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap \
  --deselect=tests/test_t6_followup_composition.py::test_the_latency_probe_asks_for_each_profiles_policy_budget \
  --deselect=tests/test_t6_followup_composition.py::test_a_truncated_latency_call_is_logged_and_failed
```

Last result: `26 passed in 3.43s`.

Selection 4:

```sh
t.sh \
  tests/test_identity_pins.py \
  tests/test_structure_ratchets.py \
  tests/test_public_tip_guards.py \
  tests/test_test_layout.py \
  tests/test_architecture.py \
  -q -n 2
```

Last result: `386 passed in 39.20s`.

### Other commands

| Command | Last result line |
|---|---|
| `t.sh tests/test_followup_contract_baseline.py -q -n 2 (before production edits)` | `25 passed in 3.04s` |
| `t.sh tests/test_followup_contract_recovery.py -q -n 2 (final)` | `11 passed in 2.88s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` |
| `py.sh python <scratch>/sc5-transport-probe.py` | `openrouter after 5 ready (plan before/after and OpenRouter before also 5 ready)` |
| `py.sh python <scratch>/sc5-prospective-ratchets.py` | `Prospective ratchets passed, including all four new Python files; index untouched.` |
| `git diff --check` | `exit 0, no output` |

### Socket tests for the orchestrator

These 36 test functions were not run here. Run them through the wrapper with `-q -n 2 -m "not arc_close"` in a socket-capable sandbox.

```text
tests/test_chatgpt_plan_provider.py::test_request_shape_follows_the_plan_route_rules
tests/test_chatgpt_plan_provider.py::test_a_chunked_event_stream_is_reassembled
tests/test_chatgpt_plan_provider.py::test_output_budget_rides_in_the_prompt_never_as_max_output_tokens
tests/test_chatgpt_plan_provider.py::test_a_json_repair_is_sent_with_the_budget_of_the_request_it_repairs
tests/test_chatgpt_plan_provider.py::test_receipts_name_the_provider_model_and_answering_model
tests/test_chatgpt_plan_provider.py::test_capabilities_isolated_tool_free_and_bounded
tests/test_chatgpt_plan_provider.py::test_json_object_mode_carries_the_schema_and_repairs_once
tests/test_chatgpt_plan_provider.py::test_single_request_never_repairs_or_retries
tests/test_chatgpt_plan_provider.py::test_transient_failures_retry_with_backoff
tests/test_chatgpt_plan_provider.py::test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back
tests/test_chatgpt_plan_provider.py::test_usage_limit_before_the_stream_and_not_eligible
tests/test_chatgpt_plan_provider.py::test_a_401_refreshes_once_and_retries
tests/test_chatgpt_plan_provider.py::test_a_401_under_single_request_fails_and_the_next_call_refreshes
tests/test_chatgpt_plan_provider.py::test_rejected_structured_output_names_the_setting
tests/test_chatgpt_plan_provider.py::test_incomplete_truncated_and_broken_streams
tests/test_chatgpt_plan_provider.py::test_the_deadline_shuts_a_stalled_stream
tests/test_chatgpt_plan_provider.py::test_an_interrupt_while_waiting_for_the_refresh_lock_sends_nothing
tests/test_chatgpt_plan_provider.py::test_a_deadline_that_passes_while_waiting_for_the_refresh_lock_sends_nothing
tests/test_chatgpt_plan_provider.py::test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing
tests/test_chatgpt_plan_provider.py::test_an_expired_deadline_is_never_extended_into_a_send
tests/test_chatgpt_plan_provider.py::test_a_success_that_overlaps_a_usage_limit_keeps_the_pause
tests/test_chatgpt_plan_provider.py::test_a_success_clears_the_expired_pause_it_saw
tests/test_chatgpt_plan_provider.py::test_signed_out_is_refused_before_any_request
tests/test_chatgpt_plan_provider.py::test_model_list_keeps_listed_models_in_server_order
tests/test_chatgpt_plan_provider.py::test_readiness_reads_local_state_only
tests/test_chatgpt_plan_provider.py::test_billing_class_is_subscription
tests/test_chatgpt_plan_provider.py::test_t6_rewrite_runs_on_the_plan_with_receipts
tests/test_chatgpt_plan_provider.py::test_a_checked_call_sends_the_first_request_unchanged_and_one_correction
tests/test_chatgpt_plan_provider.py::test_malformed_then_repaired_then_contract_failing_gets_one_correction
tests/test_chatgpt_plan_provider.py::test_contract_failing_then_a_malformed_correction_gets_one_repair
tests/test_chatgpt_plan_provider.py::test_a_checked_call_with_no_admitted_recovery_sends_no_plan_repair
tests/test_chatgpt_plan_provider.py::test_a_background_request_gets_no_fresh_ceiling_past_the_checked_calls_deadline
tests/test_t6_followup_composition.py::test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort
tests/test_t6_followup_composition.py::test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap
tests/test_t6_followup_composition.py::test_the_latency_probe_asks_for_each_profiles_policy_budget
tests/test_t6_followup_composition.py::test_a_truncated_latency_call_is_logged_and_failed
```

## The socket tests, run by the orchestrator (2026-11-21)

The test files whose names contain followup, structured_contracts, model_work, chatgpt_plan, openai_chat,
registry_audit, practice_index_paid or t6_, with the identity pins, the structure ratchets and the test layout,
outside the sandbox: `1420 passed in 311.49s`.

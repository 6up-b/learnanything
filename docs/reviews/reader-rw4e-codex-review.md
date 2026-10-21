# Reader RW4e: Codex review and fix round

Stage: `reader-rw4e` (branch `reader/rw4e`, worktree `learnanything-rw4b`). Reviewed range `a12ba5ba9..008285cd1`
(Codex job `20261020-211935-LEnwZh`, by inspection; it ran no tests). This round: reproduce each finding, then fix it
or reject it. No migration, no new config key, no frontend change, no live or paid model call (fakes only).

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Concurrent role writes can override a rejected proposal; two judges can make two objects | fixed | `c5c62a2cc` | `tests/test_roles_concurrency.py` (durability lane, WAL asserted): `test_a_review_between_a_judges_read_and_its_write_stands`, `test_two_judges_at_once_make_one_object_with_their_agreement` (both failed before the fix: the judge's append raised `SourceObjectError ... is rejected` out of `propose_roles`, and two judges made 2 objects), `test_a_review_that_won_the_lock_first_takes_no_further_proposal` |
| F2 | Medium | Batch resume permanently skips judged-but-unapplied paid results | fixed | `0e1412f14` | `tests/test_label_roles_cli.py`: `…interruption_before_the_first_proposal_is_applied_on_resume_without_a_call`, `…interruption_midway_through_a_batch_leaves_nothing_half_written_and_resumes`, `…interruption_after_the_last_judgment_resumes_with_zero_calls`, `…judged_passage_whose_answer_is_gone_is_reported_incomplete_never_done`. Before the fix, the rerun reported `done` with zero calls and the stopped batch's passages had no proposal |
| F3 | Medium | Intent lists use low-confidence proposals alongside stronger matches | fixed | `d6389c3d3` | `tests/test_source_roles.py`: `…intent_list_takes_a_low_confidence_proposal_only_when_no_stronger_one_is_in_scope` and `…stronger_proposal_the_scope_excludes_never_blocks_the_low_confidence_one` (through `find_sources`, reading the search's extra lists; the stronger proposal excluded by the caller and by the teaching scope); `…intent_lists_read_proposals_by_role_and_by_their_mapped_type` now expects the strong entry alone (it had pinned the defect); `tests/test_roles_judges.py::test_rw3b_contrast_list_takes_a_low_confidence_proposal_only_when_none_better_is_on_target`. All failed before the fix |
| F4 | Medium | Subscription runs report zero estimated cost despite token usage | fixed | `0e1412f14` | `tests/test_label_roles_cli.py`: `…subscription_run_reports_the_estimate_from_reported_tokens` (the dollars equal the fake's reported tokens × the price; `marginal_usd` 0), `…metered_run_reports_its_charge_and_the_same_estimate`, `…subscription_run_with_no_price_keeps_its_estimate_unknown`. Before the fix `estimated_usd` was `0.0` and no token count was reported |

No finding was rejected.

### What changed

**F1.** `reader.source_roles.propose_roles` now runs the identity lookup (`_existing`, read on the repository's
connection), every status check and every object and version it writes inside one `repository.atomic()`
(`BEGIN IMMEDIATE`), so another judge or a learner's review lands wholly before or after it. On its own,
`source_objects.append_proposal_version` reads the head status and appends in one transaction too.
`Repository.set_source_object_status` (the review path, also used by RW4d's removal inside its own `atomic()`,
where it becomes a savepoint) reads the head and appends its successor in one transaction.
`append_source_object_version` opens `BEGIN IMMEDIATE`, so the next ordinal is read under the write lock. As a
result, a call's proposals are now all written or none, which F2 builds on. The tests open each race
deterministically: the first judge's lookup starts the competing writer on a thread and waits 1.5 s for it. A correct
writer stays blocked by the judge's lock for that whole time, so the test cannot pass by luck against fixed code.
Against the old code, heavy machine load could hide the race (the test might pass anyway), but it could not make a
fixed build fail.

**F2.** `practice_index.listwise.judge_listwise` takes an optional `context` and passes it to `PaidCalls.call`, which
already recorded context with the checkpoint and in the receipt's declared `practice_index` block; every other
caller passes nothing and is unchanged. The labeller records `{extraction_id, refs: {ref: "extraction/span"}}` for
each batch. A passage the labeller judged `roles` is *applied* once some proposal version (including a review
successor) carries one of its ledger ids. `_unapplied` finds passages that are judged but not applied. Before
sending anything, a run applies them from their receipts (`receipt_answers`, newest first): only receipts with this
reading's map and prompt version, an answer that parses and judges every passage of its batch, and an input hash
matching the ledger row. This needs no model call, and the passages are still never sent again. Any pending passage
left without an answer makes the run `incomplete` with a reason, never `done`. The report gains
`passages.pending_apply` (also shown in the dry run) and a `recovery` block: `pending`, `recovered_passages`,
`unrecovered`, written/versions/skipped. Applying is idempotent. So a passage whose answer named no usable role, or
whose every role was reviewed in the meantime, is just found again on a later run, with no call and nothing written.
The RW4e write-up's open question 6, which had accepted this window, now points here.

**F3.** `find_sources.source_object_lists` takes the caller's eligibility and decides the low-confidence fallback
*after* applying it. It returns the confident rows the caller may be given, and the low ones only when none of those
remain, instead of appending the low ones last. Eligibility means:

- for `find_sources`: the span scope, the caller's `exclude_span_ids`/`exclude_span_keys`, and exam material (the
  one predicate);
- for RW3b's `contrast_list`: the target's LOs and their confusables.

The `roles=` filter in `search_spans` had the same rule. Its fallback now asks whether any confident passage is
allowed by the scope, where before it only asked whether a confident passage existed anywhere in the scope's
extractions. The rule now also covers non-RW4e source objects carrying `confidence = "low"`, which also used to be
appended last.

**F4.** The labeller's `usage` is built by `_usage` from each batch outcome's paid-call usage:

- On a subscription: `estimated_tokens` is the sum of `estimated_only_tokens` (reported usage, or the call's estimate
  when a turn reports none). `estimated_usd` is those tokens × `source_retrieval.llm_price_per_million`, or `None`
  when there is no price. `marginal_usd` is 0.
- On a metered route: `estimated_tokens` is the reported tokens (the budget's charged tokens when nothing was
  reported), and `estimated_usd` equals `marginal_usd`, the budget's charge.

### Claims re-checked

- *One proposal per passage and role; a reviewed proposal takes no further version*: now holds under concurrent
  writers (F1).
- *Resumable batch labelling*: a stopped run's judged passages are applied on resume without a call, or the run says
  `incomplete` (F2). The "one write" window the RW4e write-up described was in fact several separately committed
  writes; a batch's proposals are now one transaction.
- *Low confidence only when nothing better exists*: now true for intent lists, for the `roles=` filter's scope
  check and for RW3b's contrast list (F3).
- *Subscription cost estimated from usage*: the final report carries the token-based estimate (F4).
- Not addressed here, as the review notes: `source_rerank`/`source_compare` (§18) stay deferred as the implementer
  recorded. Malformed-roles tolerance while the switches are off narrows the switch-off parity claim to "byte-identical
  except a malformed `roles` field no longer fails the judge"; `tests/test_roles_switch_off.py` still passes
  unchanged.

### Notes

- No live or paid call was made. No vault copy was used. Every model-backed path ran with fakes.
- One small text-edit script ran with plain `python3` before the isolation wrapper was in place. It imported nothing
  from LearnLoop and only rewrote two source files. Every later script ran under `env -i` with empty
  `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR` (`fixtures-local/tmp/isolated.sh`).
- No migration, config key, CLI help, RPC or frontend change, so no snapshots, references, CLI help or RPC pins were
  regenerated. The DB references cite no line in the changed code.

### Gate (this fix step; targeted per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile` then `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto <63 files below>`: **1,675 passed**.
- `uv run pytest -n auto -m durability <the same 63 files>`: **9 passed**.
- `uv run pytest -n auto --durable-sqlite tests/test_roles_concurrency.py tests/test_source_objects.py
  tests/test_source_roles.py tests/test_label_roles_cli.py tests/test_compare_sources_keep.py`: **123 passed**.
- `tests/test_roles_concurrency.py` run alone 3 times (timing-sensitive): 3 passed each time.
- Frontend, cargo, references, snapshots: not applicable (nothing under `apps/`, no schema or config change).

Test files run (63): `test_approach_maps`, `test_architecture`, `test_cli_help_snapshot`,
`test_compare_keep_switch_off`, `test_compare_sources_keep`, `test_coordinated_migrations`,
`test_desktop_rpc_contract`, `test_exam_protection_identity`, `test_exam_protection`, `test_exercise_arm`,
`test_facet_locks_landing`, `test_find_sources_intents`, `test_label_roles_cli`, `test_library_ask_expand`,
`test_library_ask`, `test_library_exercises`, `test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_cli`,
`test_mcp_tools`, `test_mobile_allowlist`, `test_output_budget`, `test_passage_links`, `test_practice_index_find`,
`test_practice_index_paid`, `test_prescription_passages`, `test_reader_compare_table`, `test_reader_cue_holdout`,
`test_reader_cue_value`, `test_reader_find_sources_callers`, `test_reader_rw1c_review`,
`test_reader_rw3b_fix_round4`, `test_reader_rw3b_fix_round5`, `test_reader_rw3b_fix_round6`,
`test_reader_rw3b_protection`, `test_reader_rw3b_review_fixes`, `test_reader_try_first`,
`test_reader_tutor_offers`, `test_reader_tutor_retrieval`, `test_required_method_round3_review`,
`test_reread_safety_landing`, `test_reread_safety`, `test_retrieval_interventions_write_points`,
`test_roles_concurrency`, `test_roles_judges`, `test_roles_switch_off`, `test_rw4d_rw3b_composition`,
`test_salience_firewall`, `test_source_objects`, `test_source_retrieval_followup`,
`test_source_retrieval_guards`, `test_source_retrieval_search`, `test_source_roles`,
`test_sources_merge_composition`, `test_sqlite_file_copies`, `test_t6_followup_review`, `test_table_roles`,
`test_tool_dispatch_policy`, `test_tool_registry`, `test_tool_results_withhold_answers`, `test_tools_cli`,
`test_tracked_fixture_databases`, `test_tutor_tool_requests` (all under `tests/`). They were chosen by `git grep`
for the changed modules and functions (source-object store and service, `judge_listwise`, `find_sources` /
`search_spans` / `source_object_lists`, `passage_cues` / `contrast_list`, the role labeller and `source_roles`),
plus the contract tests.

For the landing gate: the full suite, the whole durability lane and the whole vitest run, on the merged tree.

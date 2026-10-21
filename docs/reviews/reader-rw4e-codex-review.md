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

## Re-review

Codex re-review of `008285cd1..reader/rw4e` (job `20261020-214617-gckfJ8`, by inspection and isolated in-memory
probes; it ran no repository tests). Verdict REOPENED: F1 (High) confirmed fixed, two new findings. This round:
each one reproduced with a failing test first, then fixed. No migration, no config key, no frontend change, no live
or paid model call (fakes only).

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Concurrent role writes (first round) | confirmed fixed by the re-review | `c5c62a2cc` | nothing further |
| F5 | Medium | Role filtering can discard the stronger candidate after it suppresses the fallback | fixed | `e7fe1c039` | `tests/test_source_roles.py::test_a_stronger_proposal_the_roles_filter_rejects_never_blocks_the_low_confidence_one` (through `find_sources`, with the weak passage having no keyword match of its own). It failed before the fix: the `source_objects` list was the strong `intuition` passage `t2`, which the `alternative_treatment` filter then dropped, so the weak `t3` never reached the pool |
| F6 | Low | Mixed metered usage drops estimates for calls without reported tokens | fixed | `c257c0604` | `tests/test_label_roles_cli.py`: `…a_request_with_no_reported_usage_counts_its_estimate_beside_reported_ones[openrouter, codex_sdk]` (batch 1 reports, batch 2 does not) and `…a_retried_request_that_reported_nothing_counts_its_estimate[openrouter, codex_sdk]` (attempt 1 fails with no usage and is retried). Both metered cases failed before the fix (e.g. 1,402 reported tokens counted, the failed attempt's 19,859-token estimate dropped); the subscription cases already passed and pin that the rule is now the same on both billings |

No finding was rejected.

### What changed

**F5.** The `roles=` positive filter's rule (ingest's effective hints, RW4e's proposals, the low-confidence fallback
when no confident passage is in scope) moved out of `search_spans` into `source_retrieval.search.role_filter`, which
`search_spans` now calls; the rule itself is unchanged. `find_sources` computes it once for the effective roles
(`roles=`, or `worked_example` for that intent) and adds it to the eligibility it hands `source_object_lists`. So a
strong row the search would drop is no longer the "stronger candidate" that suppresses a weak one the search keeps.
With no `roles=` (and any intent but `worked_example`), nothing changes. With `roles=`, every strong row the filter
admits is kept exactly as before. The only rows that change are strong rows the search was going to drop anyway, and
the weak fallback that now appears in their place.

**F6.** `PaidCalls` keeps one more per-attempt tally, `UsageTotals.usage_tokens`: each attempt's reported tokens, or
its estimate when it reported none, whatever the billing. On a subscription it equals `estimated_only_tokens`. It is
an additive field in the `usage` report and is not what the budget charges (the budget keeps `max(estimate,
reported)`). The labeller's `_usage` sums it on both billings, so a metered run with mixed reported and missing
usage, retries included, counts every request. The dollar figures are unchanged: on a subscription, tokens × price;
metered, the budget's charge.

### Notes

- No live or paid call was made. No vault copy was used. Every model-backed path ran with fakes. Every script
  outside pytest (two text-edit scripts and the reference generator and validator) ran under `env -i` with empty
  `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`.
- References: F5 (and, before it, the first round's F3) moved lines that
  `Reference/Configuration/Fields/Config - source_retrieval.md` cites (`search.py` for `query_rewrite`, `pool`,
  `pool_keyword_extras`, `rrf_k`; `find_sources.py` for `llm_price_per_million`). `db_generate_reference.py` was
  rerun, and only that note's cited line numbers were kept. Its commit label and the other 403 notes'
  commit-label-only churn were reverted; the landing gate regenerates on the merged tree anyway.
  `db_validate_reference.py`: 0 errors.
- No CLI help, RPC, serializer or config-defaults change (the serializer snapshot test still passes).
- `/tmp/learnloop-fullsuite.lock` exists but is an empty file from Oct 13 with no holder and no full suite
  running (only other stages' targeted runs), so the targeted gate went ahead.

### Gate (this fix step; targeted per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile` then `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto <87 files below>`: **2,065 passed**.
- The first round's files not among the 87 (readers of `source_object_lists` through `contrast_list` / the cues):
  `test_passage_links`, `test_reader_cue_holdout`, `test_reader_cue_value`, `test_reader_rw3b_fix_round4`,
  `test_reader_rw3b_fix_round5`, `test_reader_rw3b_fix_round6`, `test_reader_rw3b_protection`,
  `test_reader_try_first`, `test_salience_firewall`: **130 passed**.
- Other consumers of the paid layer's `usage` report, plus the serializer snapshot: `test_sidecar_serializer_snapshot`,
  `test_approach_map_boundaries`, `test_approach_map_replay`, `test_hint_h2b_fix4`, `test_hint_h2b_rereview`,
  `test_hint_h2b_review`, `test_hint_kill_switch`, `test_hint_outcome`, `test_workbench_check`: **77 passed**.
- `uv run pytest -n auto --durable-sqlite tests/test_source_roles.py tests/test_label_roles_cli.py
  tests/test_find_sources_intents.py`: **68 passed**. No migration or DB/connection code changed, so the
  durability-marked lane does not apply.
- `db_generate_reference.py` / `db_validate_reference.py`: head 215, 0 errors.
- Frontend, cargo: not applicable (nothing under `apps/`).

Test files run (87, all under `tests/`, chosen by `git grep` for `practice_index.paid` / `PaidCalls` /
`UsageTotals`, `judge_listwise`, `role_filter` / `search_spans` / `find_sources` / `source_object_lists`, the role
labeller, the hint map builder and writer, `compare_sources`, `rewrite_query`, the dossiers and evaluation, plus the
contract tests): `test_ad1_codex_rereview_fixes`, `test_ad1_codex_review_fixes`, `test_ad1_fix_round4`,
`test_ad1_fix_round5`, `test_ad1_fix_round8`, `test_ad1_fix_round9`, `test_ad1_outside_and_cli`,
`test_ai_tool_isolation`, `test_approach_maps`, `test_architecture`, `test_auto_build_spend_report`,
`test_chatgpt_plan_provider`, `test_cli_help_snapshot`, `test_compare_keep_switch_off`, `test_compare_sources_keep`,
`test_compare_sources`, `test_coordinated_migrations`, `test_desktop_rpc_contract`, `test_embedding_backfill`,
`test_exam_protection_identity`, `test_exam_protection`, `test_exercise_arm`, `test_facet_locks_landing`,
`test_find_sources_intents`, `test_hint_contracts`, `test_hint_h2a_review`, `test_hint_h2a_review_round4`,
`test_hint_replies`, `test_hint_service`, `test_label_roles_cli`, `test_library_ask_expand`, `test_library_ask`,
`test_library_exercises`, `test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_cli`, `test_mcp_tools`,
`test_mobile_allowlist`, `test_output_budget`, `test_practice_index_adapters`, `test_practice_index_dossiers`,
`test_practice_index_evaluation`, `test_practice_index_find`, `test_practice_index_paid`,
`test_prescription_passages`, `test_project_atomicity`, `test_project_blindness`, `test_project_cli`,
`test_project_experiment_store`, `test_project_probes`, `test_project_report`, `test_reader_compare_table`,
`test_reader_find_sources_callers`, `test_reader_intentions`, `test_reader_intent`, `test_reader_rw1c_review`,
`test_reader_rw3b_review_fixes`, `test_reader_tutor_offers`, `test_reader_tutor_retrieval`,
`test_required_method_round3_review`, `test_reread_safety_landing`, `test_reread_safety`,
`test_retrieval_interventions_write_points`, `test_roles_concurrency`, `test_roles_judges`, `test_roles_switch_off`,
`test_rw4d_rw3b_composition`, `test_source_objects`, `test_source_retrieval_codex_unavailable`,
`test_source_retrieval_followup`, `test_source_retrieval_guards`, `test_source_retrieval_search`,
`test_source_roles`, `test_source_service_spend_accounting`, `test_source_service_spend_envelopes`,
`test_sources_merge_composition`, `test_sqlite_file_copies`, `test_t6_followup_composition`,
`test_t6_followup_review`, `test_table_roles`, `test_tool_dispatch_policy`, `test_tool_registry`,
`test_tool_results_withhold_answers`, `test_tools_cli`, `test_tracked_fixture_databases`,
`test_tutor_tool_requests`, `test_workbench_hint_service`.

For the landing gate: the full suite, the whole durability lane and the whole vitest run, on the merged tree.

## Fix round 3 (orchestrator)

Codex verify job `20261020-220340-vS2cMy` reopened F5 (Medium): the caller's exclusions were applied *after* the
"does a stronger candidate remain?" decision, so a strong passage the caller could not be given still suppressed
the low-confidence fallback. `search.role_filter` asked only `scope.allows`, and `find_sources` handed that set on to
its intent list. Reproduction: A has a high-confidence `alternative_treatment` proposal and B a low-confidence one,
both in library scope. `find_sources(intent="alternative", roles=["alternative_treatment"],
exclude_span_keys=[A])`, with B having no retrieval match of its own, gave `extra_lists={}`, zero hits and
`role_basis.low_confidence=0`. Binding ruling: one shared effective-eligibility function, used by the intent lists,
the search's role filter and the contrast list, so they can never disagree again. Rows a filter admits stay
otherwise unchanged.

### Finding

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F5 | Medium | Caller exclusions applied after the stronger-candidate decision | fixed | `a53cce97c` | `tests/test_source_roles.py::test_a_stronger_proposal_the_caller_excluded_never_blocks_the_low_confidence_one_under_roles` (the verify's reproduction, by `exclude_span_keys` and by `exclude_span_ids`), `tests/test_source_roles.py::test_the_roles_filter_falls_back_when_the_caller_excluded_every_stronger_passage` (the `roles=` search path alone: an `explain` call has no `intuition` intent list), `tests/test_roles_judges.py::test_rw3b_contrast_list_a_confident_contrast_the_judge_may_not_be_shown_never_blocks_the_low_one` (a confident counterexample on a solution block linked to the target's LO). All three failed on `c3b5c9484` (archive under `fixtures-local/tmp`, `-o pythonpath=<tmp>/src`). The failures: `{} == {'source_objects': [t3]}`; `[] == [t2]`; `[t12] == [t2]` |

### What changed

- **One rule.** `source_retrieval.corpus.Eligibility` (built by `effective_eligibility`) says what one caller may
  be given. A key is eligible when all of these hold:
  - the scope allows it;
  - it is not among the caller's `excluded` keys;
  - the caller's per-key `admits` rule accepts it;
  - it is not exam or held-out material (`exam_withheld`, the one predicate);
  - the caller's batch `withheld` rule does not name it.
- **The `roles=` filter.** `search.role_filter(..., eligible=)` asks this object, instead of `scope.allows`,
  whether any hinted or confident passage remains before it falls back to the low ones. `search_spans` takes
  `eligible=` and passes it through. Its default is the scope's eligibility with exam material withheld. That
  default changes only the fallback decision for a caller that passes none, and every such `roles=` caller
  (exercise import, the exercise arm) withholds exam material downstream anyway. The permitted set is still the
  hints and confident proposals, or the low ones alone, exactly as before.
- **`find_sources`.** It builds the eligibility once from:
  - the span scope;
  - `exclude_span_ids` + `exclude_span_keys`;
  - exam material;
  - under `assisted_practice` with an item, the answer-overlap filter, read from the same block text the pool
    filter reads (`_answer_overlap`).

  It passes the eligibility to `role_filter` and to `search_spans`. The intent lists use the same eligibility
  narrowed by the role filter's result. A cursor's judged passages are deliberately not exclusions here: they were
  candidates, and every page keeps the first page's role filter.
- **RW3b's `contrast_list`.** It takes the shortlist's `guard` (`protection`, read if absent) and builds its
  eligibility from:
  - the open source's `_scope`;
  - `admits`: the open extraction, `guard.allows` (exam, held-out and teaching exclusions) and the target's LOs or
    their confusables;
  - `withheld`: `model_reader_withheld` (solutions, assessment lanes).

  These are the filters the shortlist's pool applies, so a confident contrast the judge would never be shown no
  longer suppresses the low one. The judge's own earlier links (`own`) are unchanged.

### Notes

- No live or paid call. Fakes only, no vault copy. No migration, config key, CLI help, RPC, serializer or frontend
  change.
- Every script outside pytest (two test-edit scripts, one source-edit script, the reference generator and the
  validator) ran under `env -i PATH=$PATH` with empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR` under
  `fixtures-local/tmp`, and `python3 -I` for the edit scripts. One slip: a `python3 -` with an *empty* heredoc ran
  once without the wrapper. It executed no code and imported nothing.
- References: `db_generate_reference.py` was rerun. Only the cited line numbers in `Config - source_retrieval.md`
  (`search.py` for `query_rewrite`, `pool`, `pool_keyword_extras`, `rrf_k`; `find_sources.py` for
  `llm_price_per_million`) and in `Config - reader_active_reading.md` (`passage_cues.py` for `enabled`) were kept.
  The commit labels and the other 402 notes' churn were reverted, as in the last round.
  `db_validate_reference.py`: 0 errors.
- `/tmp/learnloop-fullsuite.lock` is still the empty Oct 13 file with no holder, and no pytest was running, so the
  targeted gate went ahead.

### Gate (targeted, per the owner's 2026-10-17 rule)

- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto <67 files below>`: **1,775 passed**.
- `uv run pytest -n auto --durable-sqlite tests/test_source_roles.py tests/test_roles_judges.py
  tests/test_find_sources_intents.py`: **64 passed**.
- References: generated, then validated with 0 errors.

Test files (67, all under `tests/`): `test_source_roles`, `test_roles_concurrency`, `test_roles_judges`,
`test_roles_switch_off`, `test_label_roles_cli`, `test_library_exercises`, `test_source_objects`; every file naming
`find_sources` / `search_spans` / `contrast_list` / `passage_cues` / `role_filter` / `source_object_lists`, plus the
search and cue files: `test_approach_maps`, `test_contrast_pairs`, `test_discriminating_search`,
`test_exam_protection_identity`, `test_exam_protection`, `test_exercise_arm`, `test_facet_locks_landing`,
`test_find_sources_intents`, `test_library_ask_expand`, `test_library_ask`, `test_mcp_c1a_narrow`,
`test_mcp_c1a_review`, `test_mcp_cli`, `test_mcp_tools`, `test_output_budget`, `test_passage_links`,
`test_prescription_passages`, `test_reader_cue_holdout`, `test_reader_cues_cli_report`, `test_reader_cues`,
`test_reader_cue_value`, `test_reader_find_sources_callers`, `test_reader_rw1c_review`,
`test_reader_rw3b_fix_round4`, `test_reader_rw3b_fix_round5`, `test_reader_rw3b_fix_round6`,
`test_reader_rw3b_protection`, `test_reader_rw3b_review_fixes`, `test_reader_try_first`,
`test_reader_tutor_offers`, `test_reader_tutor_retrieval`, `test_required_method_round3_review`,
`test_reread_safety_landing`, `test_reread_safety`, `test_retrieval_interventions_write_points`,
`test_salience_firewall`, `test_source_retrieval_followup`, `test_source_retrieval_guards`,
`test_source_retrieval_search`, `test_source_search`, `test_sources_merge_composition`, `test_t6_followup_review`,
`test_tool_dispatch_policy`, `test_tool_registry`, `test_tool_results_withhold_answers`, `test_tools_cli`,
`test_tutor_tool_requests`; the RW4d files: `test_compare_keep_switch_off`, `test_compare_sources_keep`,
`test_reader_compare_table`, `test_reader_intent`, `test_reader_tutor_switch_off`, `test_rw4_kill_switches`,
`test_rw4d_rw3b_composition`; the contract pins: `test_architecture`, `test_cli_help_snapshot`,
`test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_table_roles`, `test_sidecar_serializer_snapshot`.

For the landing gate: the full suite, the whole durability lane and the whole vitest run, on the merged tree.

## Fix round 4 (orchestrator)

The whole-stage verify, Codex job `20261020-222324-zO2vAN` on `a12ba5ba9..9b1a7271b`, reopened the stage with two
Highs and one Medium. It confirmed that item-bound exclusions hold, that exam protection holds through
`hidden_source_objects`, that agreement and review writes are atomic, that the dry run and the cap come in the right
order, and that no learning-state writes are made. The orchestrator's rulings bind this round.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F7 | High | With the switch off, legacy retrieval changes, including requests without `roles=` | fixed | `b4f707c78` | `tests/test_roles_switch_off_legacy_parity.py::test_legacy_source_objects_with_the_positive_filter_off_are_a12ba5ba9s`, golden `tests/fixtures/roles_switch_off_legacy_a12ba5ba9.json` recorded on an `a12ba5ba9` export. Legacy strong and weak `claim` objects (`intuition` on t2 and t3; a strong `counterexample` on solution t12 and a weak `contrast` on t2, both on the target's LO). `explain` and `alternative`, with and without `roles=`, with and without `exclude_span_keys`, plus `remediate` and RW3b's contrast list. On `9b1a7271b`, 9 of the 9 recorded answers differed from the golden (e.g. `explain`'s list `[t2, t12]` where the base gives `[t2, t12, t3]`) |
| F8 | High | Cue tolerance changes well-formed answers that the base accepted | fixed | `b4f707c78` | `…legacy_parity.py::test_a_valid_cue_answer_with_a_duplicate_role_is_parsed_and_stored_as_a12ba5ba9_did[switches_off, switches_on]`: `roles=[contrast low, contrast high]`, parsed (`model_validate_json`) and through `discover` (links, ledger, prompts, result) against the base golden, under both switch states. With the switches on, the proposals alone are deduplicated (one `contrast` per passage, its first entry). On `9b1a7271b` both failed on `parsed` and `links`. `tests/test_roles_judges.py::…malformed_roles_field…[entries]` now expects no proposal: a field the base would reject reads as `[]` as a whole, with no partial salvage. It failed on `9b1a7271b` |
| F9 | Medium | Labeller recovery can lose an accepted result and report `done` | fixed | `b4f707c78` | `tests/test_label_roles_cli.py`: `…answer_judging_a_passage_twice_is_the_batchs_failed_attempt_retried_within_the_caps` (request 1 names p1 twice; its retry is clean; one ledger row per passage), `…answer_that_always_judges_a_passage_twice_commits_nothing_and_never_reports_done` (status `failed`, no ledger row, no proposal), `…recovery_takes_a_refs_first_judgment_as_the_live_path_did` (the verify's p1 sequence: receipts naming p1 again as `none`/`[]` after its `explanation`; resume writes p1's `explanation`). All three failed on `9b1a7271b`: `done` where the fix gives `failed`, and p1 lost (6 proposals where 7 were expected) |

No finding was rejected.

### What changed

- **F7.** While `roles.positive_filter_enabled` is off, each of the following takes `a12ba5ba9`'s path:
  - `find_sources.source_object_lists`: every matching legacy row, with the low ones appended after the rest;
    `eligible` is not read.
  - `search.role_filter`, and so `search_spans`: the low ones only when no hint or confident row exists at all;
    `eligible` is not read.
  - `find_sources`: builds no effective eligibility and runs no role-filter precomputation.
  - RW3b's `contrast_list`: the legacy `remediate` rows and its own links, filtered by the target's LOs only. That
    filter is factored into `_on_target`/`_own_contrasts`, shared with the switch-on path.

  RW4e proposals stay unread while the switch is off, as before. Fix round 3's eligibility and fallback apply only
  while the switch is on.
- **F8.** The cue judge's before-validator is now `source_roles.tolerate_malformed_roles`. Any `roles` value that
  `list[RoleProposal]` (RW3b's field) accepts passes through unchanged, duplicates and order kept. Only a missing
  or malformed field becomes `[]`: one the base would have rejected, failing the whole answer. Stored links read
  `judgment.roles` as the base did. Deduplication stays in `claims_from_judgments` (`clean_roles`), which runs only
  under `on_demand_enabled`. The organizer's RW4e roles request and the batch labeller have no base counterpart, so
  they keep `tolerate_roles`.
- **F9.**
  - **Live path.** The labeller's `capture` (its `validate`) raises `AIInvalidOutput` for an answer that names a
    ref twice. The paid layer then treats it as the batch's failed attempt, retried within the run's caps, before
    any judgment is committed.
  - **Recovery.** It reads each receipt's judgments with `first_judgments`: a ref's first judgment, the one live
    capture and the ledger kept. This matters for a receipt accepted before this round.

### Notes

- No live or paid call, no vault copy; fakes only. No migration, config key, CLI help, RPC, serializer or frontend
  change.
- Every Python run outside pytest went through `env -i PATH=$PATH` with empty `HOME`/`CODEX_HOME`/
  `LEARNLOOP_CONFIG_DIR` under `fixtures-local/tmp` (`python3 -I` for the six edit scripts). That covers the edit
  scripts, the reference generator and the validator.
- The golden was recorded with `RW4E_WRITE_LEGACY_GOLDEN=1` and
  `-o pythonpath=fixtures-local/tmp/base-a12-r4/src` (a fresh `git archive a12ba5ba9 src migrations pyproject.toml`).
  The recorder asserts that it ran on that export.
- Fail-before: `git archive 9b1a7271b` under `fixtures-local/tmp`, run with `-o pythonpath=<tmp>/src`. 7 of the 7
  new or changed tests failed there, and all pass on `b4f707c78`.
- References: `db_generate_reference.py` was rerun. Only the cited line numbers in `Config - source_retrieval.md`
  (`search.py` and `find_sources.py`) were kept. The commit labels and the test- and module-list churn in five other
  notes were reverted, as in the last rounds; the landing gate regenerates. `db_validate_reference.py`: 0 errors.

### Gate (targeted, per the owner's 2026-10-17 rule)

- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto <round 3's 67 files + tests/test_roles_switch_off_legacy_parity.py>`:
  **1,781 passed, 1 skipped**. The skipped test is the golden recorder, which runs only on the base.
- `uv run pytest -n auto --durable-sqlite tests/test_source_roles.py tests/test_roles_judges.py
  tests/test_find_sources_intents.py tests/test_label_roles_cli.py tests/test_roles_switch_off.py
  tests/test_roles_switch_off_legacy_parity.py`: **93 passed, 1 skipped**.
- References: generated, then validated with 0 errors.

For the landing gate: the full suite, the whole durability lane and the whole vitest run, on the merged tree.

## Fix round 5

Codex verify job `20261020-224735-XWC66K` (on `a12ba5ba9..57d02d3f0`) confirmed everything else: 480 legacy
parity comparisons with the positive filter off, cue and organizer requests matching the base, and duplicates
handled. One Medium remained.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F10 | Medium | A labeller answer with `verdict: "none"` and non-empty roles is applied live but ignored by recovery | fixed | `e5d1ab4dd` | `tests/test_label_roles_cli.py::test_a_none_verdict_beside_roles_is_recorded_as_roles_and_recovered_after_the_last_batch` (interrupted after the last batch's ledger commit, then resumed: the role is proposed and the run reports `done`); `…::test_an_older_none_row_whose_saved_answer_has_roles_is_recovered` (a ledger written the old way, `none` beside an accepted role). Both failed on `57d02d3f0`: the ledger said `none`, and the first test's resume recovered 0 of 1 passages; the second's recovered none either |

**What changed.**
- **At capture.** The validator returns the answer with each verdict set from its cleaned roles (`agreed_verdicts`):
  `roles` when they are non-empty, `none` when they are empty. It runs after the duplicate check and before the
  ledger commits, so the ledger and the live writer agree.
- **On recovery.** `_unapplied` also takes a `none` row when its saved answer gave the passage roles
  (`_answers_with_roles`), which covers older receipts. Recovery and this check share one receipt reader,
  `_receipt_batches`: the same filters as before, each ref's first judgment, and every passage of the batch
  judged.

**Gate.**
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto`: **437 passed, 1 skipped** (the base-only golden recorder).
  The 15 files run:
  - the labeller: `test_label_roles_cli`;
  - roles: `test_roles_concurrency`, `test_roles_judges`, `test_roles_switch_off`,
    `test_roles_switch_off_legacy_parity`, `test_source_roles`;
  - RW4d: `test_compare_keep_switch_off`, `test_compare_sources_keep`, `test_reader_intent`,
    `test_reader_tutor_switch_off`, `test_rw4_kill_switches`, `test_rw4d_rw3b_composition`, `test_source_objects`,
    `test_reader_compare_table`, `test_mobile_allowlist`.

**Notes.**
- No model call; fakes only.
- The two Python edit scripts ran under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- No reference cites `role_labeller.py` lines, so no reference was regenerated.

For the landing gate: the full suite, the whole durability lane and the whole vitest run, on the merged tree.

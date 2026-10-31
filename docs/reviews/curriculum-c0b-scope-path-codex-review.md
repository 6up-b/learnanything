# Curriculum C0b: Codex review and fixes

**Stage:** `curriculum-c0b-scope-path`, branch `curriculum/c0b-scope-path` (worktree `learnanything-docs`).
**Reviewed:** `5b3f66059..b69e03225` (Codex on gpt-6.1-sol, job `20261031-152708-4s5P03`; source tracing only, its
test run was refused by the sandbox). **Fixed on:** `247b54b22` (backend), `3fedc82a9` (tests), `7c6d96da0`
(frontend), `aa1c5e21f` (CLI help snapshot, stage record), plus this record. Stage record:
`docs/reviews/curriculum-c0b-scope-path.md`.

**No paid or live call was made.** Every model is a fake. The one ad-hoc script (the CLI help snapshot `--write`)
ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault was opened,
`~/.config/learnloop` was not read, and nothing touched `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`. No migration and no schema change.

**Reproduction.** Every finding has a test in `tests/test_deliverable_codex_review.py` (26 tests). Run against the
reviewed head's source (`git archive b69e03225 src migrations` into the scratchpad, with
`pytest -o pythonpath=<that>/src`), **all 26 fail**. On the fixed tree, all 26 pass. (The message of `3fedc82a9` says 25 of 26. It was written before the F6 readmit test was tightened; the committed file fails 26 of 26.) Some of them fail on the old
head because a new function is missing (`coverage_key`, `bounded_prompt`, `ready_parameters`,
`recover_publications`). Each test still asserts the behaviour the finding describes, not only that the name
exists.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | New model calls lack protection revalidation | fixed | `247b54b22` | `test_f1_the_path_keeps_nothing_when_a_section_is_held_out_during_its_call`, `test_f1_a_path_retry_after_protection_changed_is_never_sent`, `test_f1_the_resolver_keeps_nothing_when_its_passage_is_held_out_during_the_call`, `test_f1_the_path_worker_reads_the_live_vault_and_checks_against_it` |
| F2 | High | An older resolution can overwrite a newer learner correction | fixed | `247b54b22` | `test_f2_a_resolution_overtaken_by_a_newer_input_is_kept_but_never_activated` |
| F3 | High | Queued extraction refreshes ignore both kill switches | fixed | `247b54b22` | `test_f3_a_switch_turned_off_after_queueing_stops_the_job[enabled\|coverage_on_extract]`, `test_f3_a_switch_turned_off_between_los_stops_the_rest`, `test_f3_judge_itself_refuses_with_the_curriculum_off` |
| F4 | High | The deliverable workflow has no usable app entry point | fixed | `7c6d96da0` | vitest `DeliverableSliceCard.test.tsx`: "makes a deliverable from the learner's words and a topic list…", "a phrase not in the library is added only on the learner's yes…", "the slice opens its scope for review…" |
| F5 | Medium | Previously judged coverage is treated as permanently current | fixed | `247b54b22` | `test_f5_a_changed_statement_owes_coverage_again` |
| F6 | Medium | Initial coverage failure leaves the Guide stuck without recovery | fixed | `247b54b22` | `test_f6_a_failed_coverage_shows_failed_and_try_again_recovers`, `test_f6_a_lifted_coverage_admission_refusal_starts_the_coverage_again` |
| F7 | Medium | Coalescing can discard a completed extraction | fixed | `247b54b22` | `test_f7_a_running_job_does_not_swallow_a_new_extraction` |
| F8 | Medium | A crash can split canonical scope from its resolution receipt | fixed | `247b54b22` | `test_f8_a_stop_after_the_receipt_is_finished_forward`, `test_f8_a_stop_before_the_receipt_publishes_nothing`, `test_f8_a_goal_whose_first_input_committed_is_recovered_by_the_next_rpc` |
| F9 | Medium | A successful scope correction can leave new topics invisible | fixed | `247b54b22`, `7c6d96da0` | `test_f9_a_topic_added_since_the_judgment_has_a_line_until_the_next`; vitest "not what I need goes to the scope resolver…" (now reads with `judge: true`), "not what I need: an unavailable resolution says so, and new phrases open the scope" |
| F10 | Medium | Display-time labels do not enforce primary eligibility | fixed | `247b54b22`, `7c6d96da0` | `test_f10_a_primary_no_longer_eligible_is_replaced_by_codes_choice`, `test_f10_use_instead_refuses_a_section_that_only_mentions_the_topic`, `test_f10_a_stored_swap_to_a_section_no_longer_eligible_is_not_shown_as_core`; vitest "use this one instead is offered only on a section that introduces or develops the topic" |
| F11 | Medium | Required learner context never reaches the path judge | fixed | `247b54b22` | `test_f11_didnt_help_kept_comparisons_and_minutes_reach_the_judge`, `test_f11_minutes_available_are_dl1s_daily_budget_times_the_days_left` |
| F12 | Medium | The path judge ignores the configured prompt bound | fixed | `247b54b22` | `test_f12_an_oversized_prompt_is_never_sent`, `test_f12_a_prompt_over_the_bound_drops_notation_before_anything_else` |
| F13 | Medium | Readiness decision parameters are fixed constants disguised as priors | fixed | `247b54b22` | `test_f13_the_check_dates_follow_the_vaults_dl2_parameters`; `test_check_due_is_bounded_by_tomorrow_fourteen_days_and_the_deadline` updated |
| F14 | Medium | The time report does not measure the specified signal | fixed | `247b54b22` | `test_f14_the_time_row_counts_each_section_once_and_minutes_read_are_recorded`; `test_the_report_rows_are_aggregates_only` updated |

14 findings: 14 fixed, 0 rejected. Four were High (F1–F4), and all four are fixed.

## What changed, per finding

- **F1.** Both C0b routes now use C0a's `SC.CoverageGuard`. `ChatRoute.ask(..., guard=)` installs it as the
  request gate and as `PaidCalls`' per-attempt admission, so it checks before each attempt, each physical request
  and each retry. `ProtectionChanged` is a `BaseException`, so nothing retries it or relabels it as a provider
  failure.
  - **Path judge:** guarded over every section named in the prompt, then checked again inside the write
    transaction. A change keeps nothing (`stale`, `protection_changed`).
  - **Resolver:** guarded over the sections its passage inputs read, then checked again under the publication lock
    before the receipt (`passage_guard`).
  - **"also about…":** guarded over its section, and checked again before the ledger row and the correction.
  - **Sidecar path worker:** reads the live vault when it runs (a vault switch fails it) and passes
    `ctx.loaded_vault` as the generation-bound provider. The in-request resolver and also-about pass it too.
- **F2.** `resolve` publishes only over the head it read. Under the vault mutation lock, after the call, it reads
  the goal's scope inputs and newest resolution again.
  - An input added meanwhile makes this answer obsolete. Its paid answer is kept as a `superseded` ledger verdict
    and is never activated; the RPC returns `superseded` with a plain message.
  - A resolution of the same state published meanwhile stands (`fresh`).
  - `decide_unmatched` does all of its work under the same lock, re-reading the newest resolution there.
- **F3.**
  - `rejudge_on_extract` checks both switches when the job starts. Before each LO it loads the vault's files
    (`vault_on_disk`), checks `on_extract_reason`, and reads protection from that same load. Off means
    `switched_off`, with nothing searched, called or written after.
  - `SC.judge` refuses while `curriculum.enabled` is off (`unavailable`, `curriculum_disabled`), whoever calls it.
- **F4.** A new component, `screens/reader/DeliverableScope.tsx`, provides two pieces.
  - **`DeliverableEntry`** sits under RW7a's card while no deliverable names the open book (it is hidden when the
    switch is off, so RW7a's card shows exactly as today).
    - *learning this for something?* opens a form: the learner's sentence, an optional pasted topic list (a
      `topic_list` input), a deadline and *it's an exam*.
    - *your deliverables* lists the ones already made.
  - **`DeliverableScopePanel`** follows §5.3's "what the learner sees":
    - the summary line, then one line per topic with the phrase it answers;
    - phrases not in the library with *add it* / *no* (`scope_decide`; a topic is created only on the yes);
    - *not this…* and *add…* text boxes;
    - the receipt on demand, and "How deep for this?" while it is unanswered.
  - The slice gains *what it covers*, which opens the same panel.
- **F5.**
  - `coverage_owed` counts an LO as owed until some judgment of its *current* statement exists (every row's
    `lo_hash` equal to `SC.lo_hash` now).
  - The sidecar's "tried this session" memory is keyed by `(LO, coverage_key)`, so a changed LO is tried again.
- **F6.**
  - `_path_state` returns the coverage failure, and `path_view` / `guide_slice` show it as `failed`, with its
    reason, message and *try again*. They never show a quiet `no_sections` or `pending` instead.
  - `retry` drops the failure and starts coverage again.
  - A coverage admission refusal (capped, unpriced, unrouted, models off) is asked again on each read (RW7a's
    `_readmit` rule). Once lifted, coverage starts again on the same read.
- **F7.** `queue_coverage_on_extract` coalesces only with a job still `queued`, which reads the library when it
  starts. An extraction completed while a job is `running` queues one more pass. At most one job is queued and one
  running.
- **F8.** Each publication that touches both `goals.yaml` and SQLite is journalled, under the vault mutation lock,
  at `.learnloop/curriculum-journal/<id>.json`. This covers `create_deliverable`, `resolve` and `scope_decide`.
  - **Order:** journal entry (fsynced), then the SQLite commit (the point of no return), then `goals.yaml`, then
    the entry is removed.
  - **Recovery:** `recover_publications` runs first in every curriculum RPC (`_require`, which reloads when
    `goals.yaml` changed), in `resolve` and in `decide_unmatched`. It finishes forward an entry whose receipt
    committed: the goal is appended, or its scope set from the receipt if that receipt is still the newest. It
    drops an entry whose receipt did not commit.
  - A learner's own goal edit is never overwritten, because only an unfinished entry is replayed.
- **F9.**
  - **Backend:** while the shown judgment is from an older state, a scope LO with an eligible section but no line
    gets code's line on its first eligible section (`_unjudged_lines`, `reason_by: code`). The learner can override
    it at once, since `override` now finds its line through `effective_lines`.
  - **Frontend:** a scope change re-reads the slice with `judge: true`, so the judgment it owes starts and is
    polled. A `superseded` or `unavailable` answer shows its message. New unmatched phrases open the scope panel.
- **F10.**
  - **At display:** `effective_lines` re-applies §7.1's core rule. A stored primary that no longer introduces or
    develops the LO is replaced by code's first eligible section, with code's line and the old one as an
    alternate.
  - **Stored swaps:** a stored *use this one instead* pointing at a section that is no longer eligible is not
    shown (the judge's choice stands).
  - **New swaps:** `override(..., "use_instead")` refuses a section that only uses or mentions the topic, in plain
    words. Each section view carries `can_use_instead`, and the frontend offers the button only where it is true.
- **F11.** The path judge's context, which is part of the cache key, now also carries:
  - `didnt_help`: the path's sections among the passages an answer had shown when the learner followed it with
    RW1c's *that didn't help* (`remediate`), still-readable sections only;
  - `your_comparisons`: RW4d's kept comparisons on these LOs (books, relation labels, number of takes;
    protection-filtered by `kept_comparisons_for_card`);
  - `minutes_available`: DL1's remembered daily minutes times the days left.

  Section minutes now use DL1's pace (`plan.read_words_per_minute`), so they are comparable with the minutes
  available. The instructions name the new fields.
- **F12.** `bounded_prompt` holds the path prompt to `curriculum.max_prompt_tokens`, shrinking it by structural
  steps (`PROMPT_LEVELS`): full; then without roles and notation; then only primary-eligible sections, since code
  fills alternates from coverage. If it is still over the bound, nothing is sent (`unavailable`, `too_large`, with
  a plain message). That reason is not an admission reason, so it is not retried on every read.
- **F13.** "Am I ready?" introduces no new number. The retrievability target is DL2's
  `intent.recall_targets.keep_in_touch`, the recall target DL2 maintains the check's own depth preset at. The
  no-state delay is DL2's `capture.test_me_later_days`, the delay DL2 gives any Check once without a date.
  - Both are registered **decision** parameters (`parameter_registry`: `intent.recall_targets.*` and
    `capture.test_me_later_days`, class `threshold`). They are governed and owner-adjustable where they live, and
    read from the vault's configuration at each call (`ready_parameters`).
  - `READY_TARGET_RETRIEVABILITY`, `READY_FALLBACK_DAYS` and their unused `prior_basis` strings are gone.
  - The 14-day `keep` guardrail stays. RW6b's valuation replaces the picker when it lands (§8.5).
  - This reuses existing governed parameters instead of minting a learned resolver for a duplicate of them, which
    avoids two producers of the same value. The owner may prefer a dedicated learned target (open question 1).
- **F14.** `time_row` replaces the old estimate.
  - `minutes_read` is recorded: the Reader's active seconds (`reader_view_closed`) in the path's books since the
    deliverable was made. The Reader records time per book, not per section, and the label says so.
  - `path_minutes_left`: DL1's estimate for the path's unique sections (a section primary for two LOs counts
    once).
  - `left_out_minutes`: DL1's estimate for the sections book order would read up to each book's last path section
    that the path left out.
  - `book_order_minutes_left` is their sum. Estimates are words left at DL1's pace, using
    `reader_section_progress`'s share of spans seen, and are labelled as estimates.

## Gate (this step; targeted, memory-capped)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`, with pytest at `-n 6` and vitest at `--maxWorkers=4`, one run at a time. The full suite,
the whole durability lane and the whole vitest run were **not** run (owner rule 2026-10-17: once, at landing).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| Fail-first: `tests/test_deliverable_codex_review.py` against `b69e03225`'s `src` (and its `migrations`) | **26 failed** |
| Targeted batch 1, 34 files: the C0b and C0a files, the review file, and the contract tests (listed below) | **1,136 passed, 4 skipped** |
| Targeted batch 2, 35 files: consumers of `content/pipeline/jobs.py`, `section_coverage`, kept comparisons, source roles and RW7b (listed below) | **635 passed, 11 skipped** |
| `--durable-sqlite` on `test_deliverable_codex_review`, `test_deliverable_path`, `test_deliverable_rpcs`, `test_deliverable_scope`, `test_coverage_on_extract` | **74 passed** |
| CLI help snapshot regenerated (`curriculum report`'s docstring; only that entry changed) under `env -i` | ok |
| Frontend: `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4` on `DeliverableSliceCard.test.tsx`, `ReadingPathCard.test.tsx`, `readingPathsReader.test.tsx`, `readingPathsRefresh.test.tsx`, `readingPathsSwitchOff.test.tsx`, `figuresWithReadingPath.test.tsx` (all under `src/screens/reader/`) | **6 files, 36 passed** |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference generate and validate | not run: no schema change |
| `-m durability` | not run: no migration or DB/connection code changed (`--durable-sqlite` on the C0b files above instead) |

**Batch 1 files:** `test_deliverable_codex_review.py`, `test_deliverable_path.py`, `test_deliverable_rpcs.py`,
`test_deliverable_scope.py`, `test_coverage_on_extract.py`, `test_deliverable_curriculum_migration.py`,
`test_section_coverage.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`,
`test_section_coverage_migration.py`, `test_cli_help_snapshot.py`, `test_architecture.py`,
`test_mobile_allowlist.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`,
`test_judge_routes.py`, `test_registry_audit.py`, `test_config_refactor.py`, `test_ad_protected_tables.py`,
`test_ad_protected_readings.py`, `test_table_roles.py`, `test_reading_paths.py`, `test_plan_follows_path.py`,
`test_public_tip_guards.py`, `test_codex_tool_lockdown.py`, `test_tracked_fixture_databases.py`,
`test_coordinated_migrations.py`, `test_plan_first_transport.py`, `test_plan_first_transport_paid_roles.py`,
`test_plan_first_transport_today_quiet.py`, `test_plan_first_transport_offer_grants.py`,
`test_reader_tutor_retrieval.py`, `test_compare_sources_keep.py`, `test_provider_resolution_parity.py`.

**Batch 2 files:** `test_ingest_jobs.py`, `test_ingest_runner.py`, `test_local_index.py`,
`test_ingest_ownership.py`, `test_ingest_m3.py`, `test_ingest_latency_journey.py`, `test_ingest_transcripts.py`,
`test_library_exercises.py`, `test_source_exercise_rpcs.py`, `test_source_space_resolver.py`,
`test_quick_add.py`, `test_keep_local_retired.py`, `test_reader_progression.py`, `test_ux_phase1_auto_build.py`,
`test_ux_phase1_landing.py`, `test_ux_phase1_review_fixes.py`, `test_ux_phase1_connect_ai.py`,
`test_ad23_contract.py`, `test_glm_ocr.py`, `test_synthesis_sweep_primary_only.py`,
`test_reading_request_sweep.py`, `test_reading_hardening_2_fixes.py`, `test_reading_hardening_review_fixes.py`,
`test_reader_active_reading.py`, `test_reader_passage_check.py`, `test_reader_reconnect.py`,
`test_query_student.py`, `test_sidecar_animation.py`, `test_ad23_successor.py`, `test_voyage_fallback.py`,
`test_roles_switch_off.py`, `test_roles_judges.py`, `test_rw7b_codex_review_fixes.py`,
`test_reader_tutor_switch_off.py`, `test_compare_keep_switch_off.py`.

## Landing notes (in addition to the stage record's)

- **New frontend file** `apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx`. `DeliverableSliceCard.tsx`
  and `deliverableSlice.ts` changed, and `dto.ts` gained `DeliverableSectionDto.canUseInstead`. Expect merges only
  where the Reader stages touch `dto.ts`.
- **`section_coverage.judge` now refuses while `curriculum.enabled` is off** (C0a's function). Every C0a caller
  already refused while it was off.
- **Path section minutes moved to DL1's pace** (120 words a minute by default, instead of RW7a's 200). The path
  prompt changed, but its version stays `deliverable_path_judge.v1`: no row exists outside this branch.
- **`.learnloop/curriculum-journal/`** is a new vault-local directory. It is empty except while a publication is
  in flight, or after a stopped one until the next curriculum RPC.

## Open questions

1. **F13:** the readiness check reads DL2's `intent.recall_targets.keep_in_touch` (0.80) and
   `capture.test_me_later_days` (7) rather than a dedicated learned target. Is reusing DL2's governed parameters
   right until RW6b's valuation replaces the picker, or does the owner want a separate learned R\* now?
2. **F4:** creation and scope review live in the Guide, under the path card. Should the Goals screen get the same
   panel too?
3. **F14:** the Reader records active time per book, not per section. Should a per-section active-time record
   come before C1 reads the time row?

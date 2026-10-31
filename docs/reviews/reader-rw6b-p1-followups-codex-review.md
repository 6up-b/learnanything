# Reader RW6b part 1: Codex review fixes (`reader/rw6b-followups`)

The Codex review of the stage (`gpt-6.1-sol`, job `20261031-142011-eGzO0z`) reported 4 High and 8 Medium findings.
I reproduced each one first with a failing test, then fixed it, or rejected it with a reason.
The repro tests are `tests/test_reader_followups_review.py` and `tests/test_reader_followups_successor.py`.
Before the fixes, the repro run of `test_reader_followups_review.py` (20 tests) failed for every finding, each for
the reason the finding gives. Examples: an exposed item still in `eligible` (F1); a commitment created under Pause
or Master (F2); orphan commitments, and a unique-constraint failure (F3); the exposure judge reached during
re-valuation (F5); `planned` after a budget stop (F6); zero problems for a formative-only question (F9); empty
spans (F10); both retention questions suppressed (F11); no familiarity on the receipt (F12). The F4 gate did not
exist.

**Spend: $0.** No model or paid calls. Tests use fakes only. Every Python run outside pytest used `env -i` with
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` under `fixtures-local/rw6b-env/`: the reference
generator, the CLI help snapshot writer and the fingerprint computation. No owner vault, `~/learnloop-vaults`,
`~/learnloop-retired` or `~/learnloop-books` was opened.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Exposed follow-ups can still be served as cold checks | fixed | `4741c4f5e` | `test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks`, `test_f1_a_related_worked_example_is_only_a_label_for_a_discriminating_check` |
| F2 | High | Automatic commitments override explicit learner intent | fixed | `4741c4f5e` | `test_f2_an_automatic_follow_up_never_lands_in_a_scope_the_learner_chose[pause,master]`, `test_f2_creation_refuses_an_item_the_learner_committed_since_the_search` |
| F3 | High | Crashes can leave live checks outside the digest and revaluation machinery | fixed | `4741c4f5e` | `test_f3_a_failure_before_the_digest_is_written_leaves_no_orphan_commitment`, `test_f3_a_session_another_process_planned_meanwhile_is_not_published_twice` |
| F4 | High | The serving change has no algorithm successor | fixed (successor `mvp-0.39`) | `ea98440d8`, `6391805a6` | `tests/test_reader_followups_successor.py` (17 tests: the constant, the tag/switch gate, plan parity, the upgrade link, interrupted activations, shadow 0/0/0) |
| F5 | Medium | Daily revaluation makes paid calls outside its advertised controls | fixed | `4741c4f5e` | `test_f5_revaluation_never_reaches_the_exposure_judge`, `test_f5_with_the_source_switches_off_revaluation_values_nothing_and_keeps_the_check`, `test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes` |
| F6 | Medium | Partial success turns a budget interruption into permanent truncation | fixed | `4741c4f5e` | `test_f6_a_budget_stop_after_a_pick_stays_incomplete_and_resumes_with_the_pick` |
| F7 | Medium | Repair decisions never reach the EVSI path | fixed | `4741c4f5e` | `test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question`, `test_f7_revaluation_passes_the_stored_pending_decision` |
| F8 | Medium | Required candidate kinds cannot complete the follow-up pipeline | rejected (deferred to a follow-up stage) | — | See "F8" below: the instrument arm conflicts with the probe episode's own administration, and the import arm needs paid authoring and vault writes from a background job, with a generation cap that does not exist yet. |
| F9 | Medium | Formative-only questions are discarded by the retention adapter | fixed | `4741c4f5e` | `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`; `test_formative_records_add_questions_only_with_their_switch` (updated) |
| F10 | Medium | The way back disappears when there was no inquiry | fixed | `4741c4f5e` | `test_f10_the_workbench_session_carries_the_way_back_without_an_inquiry`, `test_f10_a_formative_record_and_the_studied_passage_are_the_fallbacks` |
| F11 | Medium | Repair ownership is too broad and is checked only during initial planning | fixed | `4741c4f5e` | `test_f11_a_retry_owns_only_the_facets_its_item_assesses`, `test_f11_a_repair_retry_scheduled_after_the_follow_up_takes_its_place` |
| F12 | Medium | Familiar siblings receive undiscounted value | fixed | `4741c4f5e` | `test_f12_a_familiar_sibling_counts_for_less_than_its_undiscounted_value`, `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount` |

## What changed, per finding

**F1 and F11: one serve-time gate.** The new module `scheduling/intent/followup_gate.py` re-checks a reader
follow-up before DL2 serves it cold. It makes no model call. It checks two things:

- Exposure since valuation, using the sources spec's full exposure rule at serve
  (`db.stores.source_service.serve_time_exposure`). The rule counts:
  - an attempt;
  - a reveal on the item or its family;
  - source text shown from the item's span;
  - an impression from any proposal;
  - a studied worked example the judge called equivalent or related, or that nobody judged.

  The window starts at whichever is later: the valuation, or the start of the cold delay
  (`serve_eligibility.COLD_RETRIEVAL_DELAY`). Studied worked examples are read in the question's teaching scope,
  recorded on the provenance as `exposure_scope_extraction_ids`. A related worked example only labels a
  `discriminate` check; it never excludes it, which is the valuation's own rule.
- Repair ownership (`owning_retry`). A repair `cold_retry` owns a facet only when the item it measures assesses
  that facet. It may do so on the claim's own attempt, or on an item of the claim's learning objects. A retry with
  no item yet owns what its source attempt touched.

`split_check` (DL2) consults the gate for `via: reader_followup` checks only. A gated candidate is held, with its
reasons recorded in `CheckState.gated`, and is never administered cold.

The daily re-valuation applies the same gate:

- An exposure retires the check (`exposed_since_valuation`) and marks its question incomplete with no
  continuation, so the next plan runs a fresh search.
- Repair ownership retires the check (`repair_retry_owns`).

Creation uses the same `owning_retry` rule. Neither retirement is shown as good news on the card.

**F2: explicit intent.** `committed_items` lists the items that some other commitment decides, using DL2 §5.3's
resolution: Pause, Master, Learn, Keep, reference-only, the learner's own "Check once", or another session's
follow-up. Those items go to `find_practice` as `exclude_item_ids`, so they are never valued, and the receipt keeps
them as `learner_intent_item_ids`. The publication transaction checks again. An item the learner committed during
the search is skipped with `learner_intent`. An automatic check therefore never becomes the newest choice over an
explicit one. Its eventual `satisfied` never replaces an ongoing learning commitment, because such an item is
never a candidate.

**F3: one publication.** `plan_session` runs every paid search first. One transaction (`_publish`) then does the
following:

1. Re-reads the digest. If another process has planned the session, or changed its row since, that row stands and
   nothing is published.
2. Re-checks the learner's intent.
3. Creates the commitments.
4. Writes the digest receipt and bumps the queue revision.

The process-local lock now only stops this process from starting two jobs.

**F4: the successor `mvp-0.39`** (`READER_FOLLOWUPS_ALGORITHM_VERSION`, after `mvp-0.38`). It is the spec's own
fallback.

- `followups_enabled` requires the tag and `followups.enabled`. Planning, re-valuation and the background job are
  gated on it.
- `learnloop.reader_followups_upgrade` is the chain's next journalled link. It accepts `mvp-0.38`, or `mvp-0.9`
  onwards through the chain. It is wired into `learnloop upgrade --to`, the CLI and sidecar completions,
  `activation_journal`, and the import-linter module list.
- The defaults snapshot for `mvp-0.39` is recorded. The `[followups]` comment and the registry rationale now name
  the switch as the successor's kill switch.
- Plan parity: with the switch off, `get_today_queue` at `mvp-0.39` serves exactly what `mvp-0.38` serves, and
  writes no digest or commitment.
- 30 chain-pin test files moved their latest from `mvp-0.38` to `mvp-0.39`. The CLI help snapshot was regenerated;
  only `upgrade` changed.

**F5: no paid call on the synchronous path.**

- `default_valuer` passes `eligibility=_applied_exposure` to `value_request`, so the worked-example judge is
  unreachable. The exposure rule has already run from persisted judgments (the gate).
- With `source_service.enabled` or `discriminating_search` off, re-valuation values nothing and keeps each check,
  recording the switch.
- A check whose only exposure is an unjudged studied worked example is kept as `exposure_refresh_needed`.
  `refresh_exposure` then asks the judge in the background job (`prepare_followups`), under both envelopes
  (`followup_spend`) and the switches.

**F6: early stops stay incomplete.** Any `budget` or `judge_unavailable` paging marks the question incomplete,
even when it already chose checks. Its `continue_from` (the proposal id) is kept. The next plan resumes through
`continuation_cursor`, whose cursor carries the relevant candidates found so far, so the earlier picks take part in
conditional valuation. A mismatched or missing cursor falls back to a fresh search. Picks are published as they are
chosen and never duplicated.

**F7: decision questions.** For each session attempt with an open causal factor, `pending_causal_decision` (S2b's
reader) gives the locked hypothesis set and its repair classes. Each set becomes its own `decide:<set>` question, so
spaces are never merged. Its `pending_decision` goes to `find_practice`, which passes it to the valuer, so
`rank_feasible`/`robust_evsi` runs. The decision is also stored on the provenance for re-valuation. An unavailable
decision is a typed note.

**F9: formative-only retention.** A retention question that only formative records raised names itself with a
`retention` ref. `open_hypotheses` then passes `formative=True`, and `retention_problem` poses it on
`formative_anchor`: the most recently attempted item of the LO and facet, or else its first active item carrying
the facet. The prior is the active predictor's P(success). The record changes which question is asked, never a
number.

**F10: the way back.** `_session_spans` now adds three sources:

- the spans of the workbench sessions that worked an item of the question's learning objects;
- the spans of formative records whose spans or facets touch those learning objects;
- with neither, the session's other workbench and formative spans, or else the first span of the section read
  last.

**F12: familiarity.** `valuation.discount_members` composes `recall_coverage.familiarity_discount` into each item's
members as d·P(E|H) + (1−d)·P(E). Under d, the observation carries d of an independent one's evidence. d = 1 leaves
the item unchanged, and the composition adds no new number. `value_request(familiarity=True)` applies it and puts
the discount on the receipt: the candidate entry, the chosen check and the chosen line. RW6b's search and
re-valuation turn it on. Other callers of `find_practice` are unchanged.

### F8 (rejected for this stage; deferred)

- **Instruments.** A `diagnostic_probe` instrument is administered by its open probe episode. DL2's admission
  refuses a fresh diagnostic surface outside the episode's own administration (the freshness and probe gates in
  `serving_exclusions.admission_reason`). The episode already serves its eligible instruments the same day.
  Turning one into a dated `test_me_later` would double-schedule a single-use surface. The episode's rival question
  is still a `discriminate` question here (`episode_label`), valued over ordinary items, and closing the episode
  answers it.
- **Unimported textbook exercises.** Making one a check needs three things:
  - a paid authoring call;
  - the key verifier ladder;
  - a vault YAML write and reload, run from the sidecar's background job.

  It also needs the generation spend cap (`followups.generation_max_daily_cost_usd`), which, like §9.3 item 8's
  generation, has no source-anchored request API to build on. Exercises still reach the valuation as unvalued,
  `not_imported` candidates, and never as checks. This is a stage of its own, not a fix.

## Claims corrected

- "DL2 re-checks independence at serve": it now does, through `followup_gate` with the full rule.
- "Re-valuation makes no model call": it now holds. The judge runs only in the background refresh, inside both
  envelopes.
- "A budget stop leaves the digest incomplete": it now holds even after a pick.
- "The provenance carries the way back": it now holds with or without an inquiry.
- "Formative records add questions": those questions are now valued.
- "No successor": `mvp-0.39`. The stage record carries a pointer to this file.
- G35 reuse: the familiarity discount is composed into the valuation.

## Gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, with
pytest at `-n 6`. The full suite, the whole durability lane and the whole vitest run were not run; they belong to
the landing gate.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (run after the fixes and again at the end) |
| repro run before the fixes: `pytest -n 6 tests/test_reader_followups_review.py` | failed for every finding (see the top of this file) |
| `pytest -n 6` over the 121 files listed below (first full targeted run) | 7 failed, 2525 passed, 15 skipped, 5 xfailed. Six were chain-pin sets my bulk edit got wrong, and one was `test_intent_checks.py` (the gate counted an attempt made before the valuation). Both were fixed in `6391805a6`. |
| `pytest -n 6` over the 9 files with those failures, plus the follow-up tests | 206 passed, 6 skipped, 1 xfailed |
| confirmation run, `pytest -n 6` over 31 files: the 5 follow-up files, the 16 intent/DL2 files and 10 contract files | 749 passed, 3 skipped |
| `tests/test_cli_help_snapshot.py --write` (env -i) | only `upgrade` changed |
| `db_generate_reference.py`, `db_validate_reference.py` (env -i) | 355 table notes; `errors: []` (no schema change; stamps and line citations only) |

Not applicable:
- Frontend: no change. The new retirement reasons are never rendered by the card, which reads only
  `no_longer_needed`, and "Coming up" shows pending checks only.
- `src-tauri`: no change.
- Migrations and DB connection code: no change, so no durability run.

**The 121 files of the targeted run:** `test_reader_followups.py`, `test_reader_followups_review.py`, `test_reader_followups_successor.py`, `test_reader_followup_valuation.py`, `test_reader_session_digests_migration.py`, `test_ad23_successor.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_cold_retry_reschedule.py`, `test_field_workbench_signals.py`, `test_intent_codex_rereview.py`, `test_learner_report_superseded.py`, `test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_plan_follows_path.py`, `test_pr4_superseded_claims_landing.py`, `test_reader_ca2_one_ask.py`, `test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_regrade_contract_successor.py`, `test_required_method_grading.py`, `test_route_rules_in_grader.py`, `test_serve_eligibility_review.py`, `test_ad23_intent_compose.py`, `test_ad23_inversion.py`, `test_ad23_pool_membership.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_discriminating_search.py`, `test_evsi_multisim.py`, `test_facet_locks_landing.py`, `test_hint_feedback_texts.py`, `test_hypothesis_reference_contract.py`, `test_intent_fix_round4.py`, `test_intent_fix_round6.py`, `test_intent_fix_round7.py`, `test_intent_recall_targets.py`, `test_intent_resolution.py`, `test_library_exercises.py`, `test_mcp_c1a_landing.py`, `test_mcp_c1a_narrow.py`, `test_mcp_c1a_review.py`, `test_mcp_tools.py`, `test_probability_prep.py`, `test_reader_find_sources_callers.py`, `test_router_card.py`, `test_router_r2a_landing.py`, `test_router_r2c_retrieval.py`, `test_sources_merge_composition.py`, `test_tool_dispatch_policy.py`, `test_value_candidates.py`, `test_voi_merge_composition.py`, `test_voi_stopping.py`, `test_voi_v2.py`, `test_exam_protection.py`, `test_exam_protection_review.py`, `test_exercise_arm.py`, `test_practice_index_evaluation.py`, `test_practice_index_find.py`, `test_practice_proposal_caller_columns.py`, `test_proposal_impressions.py`, `test_retrieval_interventions_write_points.py`, `test_source_exercise_rpcs.py`, `test_source_service_spend_envelopes.py`, `test_tutor_practice_request.py`, `test_valuation_calibration_fields.py`, `test_dl2_rw4b_keyed_pick_check.py`, `test_intent_checks.py`, `test_intent_codex_review.py`, `test_intent_exclusion.py`, `test_intent_fix_round5.py`, `test_intent_goal_deadline.py`, `test_intent_orchestrator_rulings.py`, `test_intent_planner.py`, `test_intent_plan.py`, `test_intent_rpc.py`, `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_reader_wrap_up.py`, `test_reader_observation_records.py`, `test_daily_loop_reader_authored_practice.py`, `test_daily_loop_reader_retire.py`, `test_daily_plan_reading.py`, `test_reader_rw3a_landing.py`, `test_reading_paths.py`, `test_rw7b_codex_review_fixes.py`, `test_daily_plan_build.py`, `test_followups.py`, `test_commitments.py`, `test_config_refactor.py`, `test_registry_audit.py`, `test_table_roles.py`, `test_architecture.py`, `test_cli_help_snapshot.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`, `test_coordinated_migrations.py`, `test_migration_coordinator.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_mobile_allowlist.py`, `test_instructional_layering.py`, `test_reference_gate_imports.py`, `test_lp_claim_fixes_rereview.py`, `test_ad_denial_log.py`, `test_rbeq_pr2_landing.py`.

**The confirmation run's 31 files:** `test_reader_followups.py`, `test_reader_followups_review.py`,
`test_reader_followups_successor.py`, `test_reader_followup_valuation.py`, `test_reader_session_digests_migration.py`,
`test_dl2_rw4b_keyed_pick_check.py`, `test_intent_checks.py`, `test_intent_codex_review.py`,
`test_intent_codex_rereview.py`, `test_intent_exclusion.py`, `test_intent_fix_round4.py`, `test_intent_fix_round5.py`,
`test_intent_fix_round6.py`, `test_intent_fix_round7.py`, `test_intent_goal_deadline.py`,
`test_intent_orchestrator_rulings.py`, `test_intent_planner.py`, `test_intent_plan.py`, `test_intent_recall_targets.py`,
`test_intent_resolution.py`, `test_intent_rpc.py`, `test_config_refactor.py`, `test_registry_audit.py`,
`test_architecture.py`, `test_cli_help_snapshot.py`, `test_desktop_rpc_contract.py`,
`test_sidecar_serializer_snapshot.py`, `test_mobile_allowlist.py`, `test_table_roles.py`,
`test_tracked_fixture_databases.py`, `test_instructional_layering.py`.

## Notes for the landing

- **Successor at landing.** `mvp-0.39` and its defaults snapshot sit after `mvp-0.38`. If another successor lands
  first, renumber the one constant (`READER_FOLLOWUPS_ALGORITHM_VERSION`) and recompute the snapshot. Then move the
  chain pins: 31 test files plus `test_reader_followups_successor.py`.
- **Owner upgrade.** `learnloop upgrade` (default target) from `mvp-0.38`, or through the chain. The first Today
  build after that plans ended reader sessions from the last 14 days in the background, inside both daily caps.
- **Open question.** The F8 deferral: instruments stay with their probe episode, and unimported exercises need an
  import stage with its own generation cap.

## Re-review (Codex job `20261031-154122-obQbTN`, range `18536e876..reader/rw6b-followups`)

The re-review confirmed F2 and F4 as fixed. It reopened F1 and F3 and added two Medium findings, F13 and F14.
I reproduced each one first in `tests/test_reader_followups_rereview.py`, where all 5 failing tests failed before
the fixes, each for the reason the finding gives:
- `None` from the gate after the printed solution was read (F1a).
- `None` with a related example and an unjudged one (F1b).
- A live commitment outside the digest's ids after two resumptions in the same second (F3).
- The check `stopped` while the digest still read `planned` after an injected failure (F13).
- Both A and B pending after the resumed search selected only B, using perfect-information tables as Codex's
  probe did (F14).

The 6th test, `test_f14_..._keeps_it`, is a guard that passes on both sides. **Spend: $0.** No model or paid calls.
The one probe outside pytest checked which picks the real valuation makes for the F14 tables. It ran under `env -i`
with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High (reopened) | The gate omits book-solution spans; a `related` example masks an unjudged one | fixed | `31c24cbad` | `test_f1_reading_the_imported_exercises_book_solution_since_valuation_holds_the_check`, `test_f1_a_related_example_does_not_mask_another_unjudged_one_for_a_discriminating_check` |
| F2 | High | Explicit learner intent | confirmed fixed by the re-review | `4741c4f5e` | (unchanged) |
| F3 | High (reopened) | The publication guard compares second-resolution `updated_at` | fixed | `31c24cbad` | `test_f3_two_resumptions_publishing_in_the_same_second_never_orphan_a_commitment` |
| F4 | High | Successor | confirmed fixed by the re-review | `ea98440d8`, `6391805a6` | (unchanged) |
| F13 | Medium | An interrupted retirement permanently loses the replacement search | fixed | `31c24cbad` | `test_f13_a_failure_after_the_exposure_retirement_loses_neither_the_check_nor_the_re_ask` |
| F14 | Medium | Resuming a partial search accumulates redundant checks | fixed | `31c24cbad` | `test_f14_a_resumed_search_that_prefers_a_cheaper_equal_check_retires_the_earlier_one`, `test_f14_a_resumed_search_that_still_selects_the_earlier_check_keeps_it` |

### What changed

- **F1.** `followup_gate` now passes the imported exercise's book-solution spans to `serve_time_exposure`, using the
  new `db.stores.source_service.book_solution_span_ids`. This is the latest import's
  `verification.book_solution`, the same row `instructional.exposure._solution_spans` reads at valuation. It also
  passes the exercise's pre-import key (`exercise_key`) as a candidate key, as the diagnosis follow-up's serve-time
  check does.
  The exposure rule reports only the strongest worked-example reason. So `independent_reasons` now takes the rule's
  `studied_worked_examples`: when it drops a `related` label for a `discriminate` check while another studied
  example was never judged, it reports `worked_example_unjudged`. Re-valuation then keeps the check for the
  background refresh, as before.
- **F3.** The publication compares the whole digest row it read before the searches with the row inside the
  transaction, instead of the `updated_at` stamp. Any change since then supersedes the plan, whether another
  resumption or a re-valuation wrote it. Nothing is created, and the digest stays as the other writer left it.
- **F13.** `_revaluation_line` no longer retires an exposed check itself. `revalue_pending` does it inside the same
  `repository.atomic()` block that writes the question's re-ask marker (`incomplete`, `exposed_since_valuation`),
  the re-valuation lines and the queue revision. It re-reads the digest's valuation inside that block. If the
  learner undid, restored or answered the check meanwhile, it is kept with `changed_meanwhile` and its question is
  not re-asked.
- **F14.** A question can be re-asked after a resumed search (the earlier pick carried) or after a fresh one.
  If its search valued an earlier check of the same question (the check is in a section's `valued` group) and did
  not select it, the publication transaction retires that check. The new reason is `superseded_by_resumed_search`,
  and the `chosen` line gets `superseded_by`. The question's receipt entry lists `superseded`.
  A check the learner restored, undid or answered meanwhile is left alone. "Coming up" shows the retirement as
  "No longer needed: another check coming up tells you the same in less time".
  I chose reconciliation over conditioning the valuation on the scheduled checks because it stays inside RW6b.
  Conditioning would change the shared `value_candidates` API that other callers use.

### Re-review gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, at
`-n 6` (the repro runs serial). The full suite, the whole durability lane and the whole vitest run were not run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| repro, before the fixes: `pytest tests/test_reader_followups_rereview.py` | 5 failed, 1 passed (the guard) |
| `pytest -n 6` over the 5 follow-up files, after the fixes | 84 passed |
| `pytest -n 6` over the 30 files of the targeted run (below) | 1041 passed, 3 skipped |
| `pytest -n 6` over 14 more intent, DL2 and contract files (below) | 156 passed |

Not applicable:
- Frontend: no change. The new text comes from the backend through `coming_up`.
- `src-tauri`: no change.
- Migrations, DB connection code and schema: no change, so no durability run and no DB reference regeneration.

**The 30 files of the targeted run:** `test_ad23_intent_compose.py`, `test_ad23_inversion.py`,
`test_ad23_pool_membership.py`, `test_architecture.py`, `test_cli_attempt.py`, `test_followups.py`,
`test_gate_score.py`, `test_intent_codex_rereview.py`, `test_intent_fix_round4.py`, `test_intent_fix_round6.py`,
`test_intent_fix_round7.py`, `test_intent_recall_targets.py`, `test_intent_resolution.py`, `test_mobile_allowlist.py`,
`test_reader_followups.py`, `test_reader_followups_rereview.py`, `test_reader_followups_review.py`,
`test_reader_followups_successor.py`, `test_reader_followup_valuation.py`, `test_reader_session_digests_migration.py`,
`test_source_first_needs.py`, `test_ux_phase4_feedback.py`, `test_reader_recap.py`, `test_reader_recap_review.py`,
`test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_desktop_rpc_contract.py`,
`test_sidecar_serializer_snapshot.py`, `test_discriminating_search.py`, `test_exercise_arm.py`.

**The 14 more files:** `test_dl2_rw4b_keyed_pick_check.py`, `test_intent_checks.py`, `test_intent_codex_review.py`,
`test_intent_exclusion.py`, `test_intent_fix_round5.py`, `test_intent_goal_deadline.py`,
`test_intent_orchestrator_rulings.py`, `test_intent_planner.py`, `test_intent_plan.py`, `test_intent_rpc.py`,
`test_reader_wrap_up.py`, `test_commitments.py`, `test_instructional_layering.py`, `test_table_roles.py`.

## Round 3 (Sol verify job `20261031-160105-nYxfHs`)

The final verify confirmed F1, F2, F3, F4 and F13 as fixed. It reopened F14 and added F15, both Medium. Both came
from round 2's F14 design: a resumed search retired the earlier check it valued and no longer selected
(`superseded_by_resumed_search`).

- **F14 (reopened): reconciliation can lose the selected check.** Three budgeted or resumed searches with
  identical perfect-information candidates: search 1 (A = 3 min) selects A; search 2 (A = 3, B = 2) selects B and
  retires A; search 3 (A = 1, B = 2) selects A, but the historical `chosen_refs` blocked rescheduling A, and
  reconciliation retired B. Nothing was left live, the digest read `planned` and "Coming up" was empty.
- **F15: replacing a shared check abandons another question.** Q1 (recall) and Q2 (procedure) both selected A; the
  one commitment was associated with Q1. Resuming Q1 selected a cheaper B (recall only), and reconciliation retired
  A while Q2 stayed complete with nothing to check it.

**Orchestrator direction, followed exactly.** Round 2's reconciliation is removed, not iterated on. In its place is
the spec's own rule (§9.3 item 3: "Checks are added greedily, each valued conditionally on those already chosen").

### What changed

- **No retirement by reconciliation.** A resumed or re-asked search never retires a live check. Only the daily
  re-valuation's existing reasons (answered, below the stop), the exposure and repair gates, and the learner's undo
  retire checks. `RETIRE_SUPERSEDED`, its "Coming up" text, the `superseded_by` line field and the `superseded`
  receipt entry are gone from code, copy and tests.
- **The live checks seed the greedy selection.** `valuation.value_candidates` and `value_problem` take an optional
  `already_chosen` (refs). In information mode the greedy selection starts from those of them that are among the
  problem's competing candidates. A new check is added only if it still clears the stop given them, and seeded refs
  are never listed as new `checks`. With nothing new, the section reads `stop` / `already_chosen_suffice`. In decision
  mode (`rank_feasible`, at most one measurement) a seeded check in the pool is that measurement, so nothing is added.
  The section records `already_chosen: {conditioned_on, not_valued}`. `discriminating.value_request` values each
  seeded item alongside the request's items and applies the exposure rule to it again (one no longer independent is
  not conditioned on). `find_practice` passes `already_chosen` to the valuer only when given; it is not a filter and
  not part of the continuation binding. The default (empty) is byte-for-byte unchanged for every other caller: the
  test pins the sha256 of a two-problem receipt (information and decision modes, learner and system-initiated)
  computed from the code before round 3.
- **Rescheduling reads the live checks.** `plan_session` passes each question's live checks (pending commitments it
  licenses) as `already_chosen`. The historical `chosen_refs` is gone. An item whose earlier check was retired or
  satisfied can be scheduled again as a fresh generation: its `chosen` line carries `generation`, and the
  commitment's idempotency key is `reader_followup:{digest}:{question}:{item}:{generation}`, so a fresh generation
  never resolves to the retired commitment. An item the learner undid from this digest is excluded from the
  session's later searches (`exclude_item_ids`) and is never rescheduled over the undo.
- **Shared checks.** A check that several questions (or problems) select is created once. Its `chosen` line lists
  every licensing question (`questions`), and the receipt entry of each later question lists it under `shared`.
  "Coming up" and the receipt show it once. Re-valuation reads the licensing questions from the digest and keeps the
  check while any of them still needs it: it is retired as answered only when every licensing question is answered,
  as repair-owned only when a repair owns every open one, and below the stop only when it is below the stop for every
  open one. An exposure belongs to the item, so it retires the check and re-asks every licensing question.
- A question whose live checks already suffice reads `outcome: "checks"` with `search_outcome` (what the search alone
  found) and `already_chosen`.

### Tests (`tests/test_reader_followups_round3.py`), fail-first

All 9 tests failed on the base (`50f502ac0`, run from a `git archive` copy with the worktree's venv), each for the
finding's reason where there is one:

| test | before (50f502ac0) |
|---|---|
| `test_f14_the_exact_three_search_sequence_ends_with_exactly_one_live_check` (A = 3; A = 3, B = 2; A = 1, B = 2) | no live check at all (the finding) |
| `test_f15_resuming_one_question_never_abandons_the_check_another_question_shares` | the live check is B; A, which Q2 needs, retired (the finding) |
| `test_f15_revaluation_keeps_a_shared_check_while_any_licensing_question_needs_it` | retired as below the stop for Q1 while Q2's valuation still selects it |
| `test_a_re_ask_whose_live_check_already_suffices_adds_nothing` | no `already_chosen` on the search (nothing conditions on the live check) |
| `test_an_item_whose_check_was_retired_is_scheduled_again_as_a_fresh_generation` | no live check: the historical `chosen_refs` blocks the item |
| `test_an_item_the_learner_undid_is_never_scheduled_again_by_the_same_session` | the undone item is not in `exclude_item_ids` (a guard for the new rescheduling rule) |
| `test_value_candidates_without_already_chosen_is_byte_for_byte_the_previous_receipt` | `TypeError` on `already_chosen=()`; the default call matches the pinned hash on both sides |
| `test_a_live_check_seeds_the_greedy_selection_and_is_never_a_new_check` | `TypeError`: no `already_chosen` |
| `test_round_2s_reconciliation_reason_is_gone` | `RETIRE_SUPERSEDED` present |

Round 2's F14 test in `test_reader_followups_rereview.py` now asserts the round-3 behaviour (the earlier check stays
live, the cheaper equal one is not added, nothing retired). `FakeSearch` passes `already_chosen` to the real
`value_candidates`, as the real valuer does.

### Round 3 gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`,
behind `flock /tmp/learnloop-fullsuite.lock`, at `-n 6` (the repros serial). The full suite, the whole durability
lane and vitest were not run. **Spend: $0.** No model or paid calls. The one computation outside pytest (the pinned
receipt hash, on the base code) ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`.

| Command | Result |
|---|---|
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| repro on the base (`50f502ac0`): `pytest tests/test_reader_followups_round3.py` | 9 failed |
| `pytest -n 6` over the 58 files below, first run | 1404 passed, 1 failed, 3 skipped: `test_f6_..._resumes_with_the_pick` pinned the resume's kwargs, which now also carry `already_chosen`; the assertion was updated |
| `pytest -n 6` over the 58 files below, after that | 1405 passed, 3 skipped |

Kept green in that run: `test_rebuild_shadow_is_zero_with_follow_ups_present` (rebuild `--shadow` 0/0/0) and the
mvp-0.38 off-state parity and shadow tests in `test_reader_followups_successor.py` and `test_cold_retry_reschedule.py`.

Not applicable:
- Frontend: no change. The removed "Coming up" line was backend copy (`coming_up`), so no vitest, typecheck or build.
- `src-tauri`, migrations, DB connection code and schema: no change.

**The 58 files:** `test_ad23_intent_compose.py`, `test_ad23_inversion.py`, `test_ad23_pool_membership.py`, `test_architecture.py`, `test_cli_attempt.py`, `test_followups.py`, `test_gate_score.py`, `test_intent_codex_rereview.py`, `test_intent_fix_round4.py`, `test_intent_fix_round6.py`, `test_intent_fix_round7.py`, `test_intent_recall_targets.py`, `test_intent_resolution.py`, `test_mobile_allowlist.py`, `test_reader_followups.py`, `test_reader_followups_rereview.py`, `test_reader_followups_review.py`, `test_reader_followups_successor.py`, `test_reader_followups_round3.py`, `test_reader_followup_valuation.py`, `test_reader_session_digests_migration.py`, `test_source_first_needs.py`, `test_ux_phase4_feedback.py`, `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_discriminating_search.py`, `test_exercise_arm.py`, `test_dl2_rw4b_keyed_pick_check.py`, `test_intent_checks.py`, `test_intent_codex_review.py`, `test_intent_exclusion.py`, `test_intent_fix_round5.py`, `test_intent_goal_deadline.py`, `test_intent_orchestrator_rulings.py`, `test_intent_planner.py`, `test_intent_plan.py`, `test_intent_rpc.py`, `test_reader_wrap_up.py`, `test_commitments.py`, `test_instructional_layering.py`, `test_table_roles.py`, `test_value_candidates.py`, `test_valuation_calibration_fields.py`, `test_practice_index_evaluation.py`, `test_practice_index_find.py`, `test_source_exercise_rpcs.py`, `test_cold_retry_reschedule.py`, `test_voi_merge_composition.py`, `test_sources_merge_composition.py`, `test_tutor_practice_request.py`, `test_practice_proposal_caller_columns.py`, `test_cli_help_snapshot.py`, `test_config_refactor.py`, `test_registry_audit.py`.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F14 | Medium (reopened) | Reconciliation can permanently lose the selected check | fixed by replacing round 2's design | `test_f14_the_exact_three_search_sequence_ends_with_exactly_one_live_check` |
| F15 | Medium | Replacing a shared check abandons another completed question | fixed (same change) | `test_f15_resuming_one_question_never_abandons_the_check_another_question_shares`, `test_f15_revaluation_keeps_a_shared_check_while_any_licensing_question_needs_it` |

### Open questions (round 3)

- **Mixed-intent shared checks.** The serve-time gate and re-valuation's exposure step judge exposure on the first
  licensing question's intent (the provenance). A related worked example excludes a retention check but only labels
  a discriminating one, so a check shared by a retention and a discriminating question is judged as the first one
  was. Answered, repair-owned and below-the-stop do read every licensing question.
- **A seeded check that is no longer independent** is not conditioned on (`value_request` re-applies the exposure
  rule to it). A re-ask can then add a check beside it until the next re-valuation retires the exposed one.
- **Paging's perfect-information bound** still uses the prior's entropy, not the entropy left after the live
  checks. This is conservative: a search may page further, never stop early.

## Round 4 (F16; Sol verify job `20261031-174955-0DYSqv`)

The verify of `60a1a7e9f` confirmed F14 and F15 as fixed. It confirmed round 3's open question 1 as a real Medium:

- **F16: mixed-intent shared checks could bypass retention's exposure rule.** Sharing added licensing questions to
  the digest, but the serve-time gate and re-valuation's exposure step judged exposure on the first question's
  provenance only. The verifier's sequence used the real planner: retention's search budget-stops before choosing;
  discrimination chooses A; retention resumes and shares A; the learner studies a worked example judged `related`
  to A. The gate then allowed A (a `related` example is only a label for a discriminating check), while the same
  check judged for retention is excluded (`related_worked_example`). Re-valuation kept it.

### What changed

- **The strictest rule across the open licensing questions, at serve and at re-valuation.**
  `scheduling.intent.followup_gate.followup_gate` takes the open licensing questions: `questions` when the caller
  knows them (re-valuation passes the ones open now), otherwise it reads them from the digest by `commitment_id`
  (DL2's serving passes the check's commitment id). `licensing_questions` returns the provenance's question plus
  every other question on the check's `chosen` line, less those the last re-valuation found answered
  (`answered_for`).
  - Exposure: the reasons of every licensing intent together. A `related` worked example excludes the check when any
    open licensing question is a retention question.
  - Repair ownership: only when a repair owns every open licensing question (each a retention claim).
  - With one licensing question, both rules are the question's own, unchanged.
- **Re-valuation** now takes exposure and repair ownership from that one gate (`_gate_verdict`, with the open
  questions). Round 3's separate per-question repair loop is gone, so serve and re-valuation cannot disagree and
  leave a check held but never retired. An exposure retirement still re-asks every licensing question.
- The stage record's open items now say that decision-mode seeding enforces the mode's one-measurement behaviour,
  not general conditional EVSI (the verifier's nonblocking note).

### Tests (`tests/test_reader_followups_round4.py`), fail-first

| test | before (`60a1a7e9f`) |
|---|---|
| `test_f16_a_shared_check_is_held_and_retired_by_retentions_rule` (the verifier's exact sequence with the real planner; the serve path through `intent_serving`; then re-valuation retires it as exposed with `related_worked_example` and marks both questions incomplete) | fails: the gate lets A through (the finding) |
| `test_f16_a_question_found_answered_no_longer_tightens_the_gate` (the strictest rule is over OPEN questions) | passes (a guard) |
| `test_f16_one_licensing_question_keeps_its_own_rule` (discriminate alone: a label; retention alone: excluded) | passes (single-question rule unchanged) |

Round 3's tests and the earlier gate tests (`test_reader_followups_rereview.py` F1, `test_reader_followups_review.py`
F1 and F11) still pass unchanged.

### Round 4 gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`,
behind `flock /tmp/learnloop-fullsuite.lock`, at `-n 6` (the repro serial). The full suite, the durability lane and
vitest were not run. **Spend: $0.** No model or paid calls, and no Python outside pytest.

| Command | Result |
|---|---|
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| repro on the base (`60a1a7e9f`, a `git archive` copy with the worktree's venv): `pytest tests/test_reader_followups_round4.py` | 1 failed (the F16 sequence), 2 passed (the guards) |
| `pytest -n 6` over the 58 round-3 files plus `test_reader_followups_round4.py`, first run | 1407 passed, 1 failed, 3 skipped: `test_f5_..._both_envelopes` monkeypatched the renamed `_gate_reasons`; it now patches `_gate_verdict` |
| the same 59 files, after that | 1408 passed, 3 skipped |

Rebuild `--shadow` 0/0/0 and the mvp-0.38 off-state parity tests stay green. No frontend, `src-tauri`, migration or
schema change.

# Stage "sources-build": Codex review and fixes

**Branch:** `sources/canonical-practice` (worktree `learnanything-sources`).
**Reviewed:** the build recorded in `docs/reviews/source-practice.md` (through `c3179ebf`), against `docs/specs/spec_source_practice_and_probes_v1.md`.
**Codex job:** `~/.cache/codex-agent/jobs/20261013-034418-kgYGJR` (read-only review, synthetic checks; no files changed, no vault opened, no paid call).

## Review

Each finding was reproduced first: a test that fails on the code before its fix (checked by stashing the fix and re-running), then fixed. None was rejected. Tests use fakes only.

| ID | Severity | Title | Verdict | Commit | Test (or reason) |
|---|---|---|---|---|---|
| F1 | High | Reading tools return solution text to models | fixed | `4849ecd2` | `test_tool_results_withhold_answers.py::test_an_unbound_agent_never_reads_a_solution_block_or_an_exam` |
| F2 | High | Spend limits are accounting checks, not enforceable caps | fixed | `abfd39a7` | `test_source_service_spend_envelopes.py` (one import bounded across all its operations; daily cap refuses before sending; a harvest never passes `--max-cost-usd`; envelopes shared by concurrent workers; subscription estimated, never refused; dry runs report numbers; `spend_since` prices tokens) |
| F3 | High | Opening source offers does not record assessment exposure | fixed | `d6a6dad3` | `test_retrieval_interventions_write_points.py::test_an_opened_offer_records_exposure_that_independence_reads` (switch on and off) |
| F4 | High | Source-first needs lack the serve-time independence check | fixed | `72fc20c0` | `test_source_first_needs.py::test_the_follow_up_rechecks_independence_before_serving_a_need_import[source_read, impression, worked_example]`, `::test_a_worked_example_outside_the_items_teaching_scope_does_not_block_it` |
| F5 | High | Import recovery can permanently lose verification | fixed | `e98109ee` | `test_source_exercise_import.py::test_a_process_death_around_the_written_commit_never_loses_the_check[after_vault_write, inside_written_commit]`, `::test_a_retried_written_import_restores_a_missing_check`, `::test_a_background_check_lost_with_its_process_is_resumed_at_startup`, `::test_a_resumed_check_never_verifies_content_edited_since`, `::test_a_reader_imports_background_check_is_durable_too`, `::test_the_sidecar_resumes_pending_checks_at_startup` |
| F6 | High | "Practise from your book" never delivers the imported exercise | fixed | `be6ada17` | `SourceOffers.test.tsx`: followed until written then served with the import id; failed import shown with its reason and never served; plan off: item and imported exercise offer "open"; a refused pick is not announced as added |
| F7 | Medium | Final assembly restores exposure-rejected candidates | fixed | `05805c4d` | `test_discriminating_search.py::test_final_assembly_never_restores_a_hard_exclusion`, `::test_an_exposed_item_is_not_proposed_for_a_value_intent[discriminate, retention]` |
| F8 | Medium | Unverified imported keys remain eligible for value intents | fixed | `05805c4d` | `test_discriminating_search.py::test_an_unverified_import_is_excluded_from_value_intents_but_not_practice[model_answer, disputed, changed_since_check]` |
| F9 | Medium | Exercise pagination cannot advance beyond its initial pool | fixed | `9a16ac4a` | `test_exercise_arm.py::test_exercise_paging_reaches_every_region_through_exhaustion` (60 exercises, 20-span first depth) |
| F10 | Medium | Compiled probe instruments lose their licensing regime | fixed | `41ddf886` | `test_value_candidates.py::test_an_instrument_only_request_matches_robust_selection[one instrument (act), two (abstain)]`, `::test_below_the_robust_cutover_instruments_are_ordinary_items` |
| F11 | Medium | Verified PF variants become unverified after publication | fixed | `9c7ddd43` | `test_pf_generation.py::test_a_published_variant_of_a_textbook_exercise_keeps_its_own_verification` |
| F12 | Medium | Cold-outcome reports misclassify exposure and miss later independent attempts | fixed | `0a827eac` | `test_intervention_outcomes_replayer.py::test_an_assisted_attempt_no_longer_masks_a_later_independent_one`, `::test_an_attempt_right_after_another_exposure_is_not_cold[5 kinds]`, `::test_the_replayer_reads_persisted_exposure`, `::test_outcome_states` |
| F13 | Medium | Published hypothesis references do not match the adapters | fixed | `fe4440d3` | `test_hypothesis_reference_contract.py` (every published kind parses; schema-valid `facet`/`lo` refs run through the tool; named gaps map, reversals and holding-pen targets name nothing; remediation reads the gap's belief) |
| F14 | Medium | The promised Reader retrieval contract is incomplete | fixed | `75731bf7` | `test_find_sources_intents.py::test_roles_match_an_rw4e_proposal`, `::test_a_low_confidence_proposal_counts_only_when_nothing_better_exists`, `::test_a_proposal_never_admits_a_block_into_an_item_bound_scope`, `::test_facet_ids_target_retrieval_and_verification`, `::test_find_sources_compare_delegates_to_compare_sources` |
| F15 | Medium | Source-first needs bypass phase kill switches | fixed | `72fc20c0` | `test_source_first_needs.py::test_a_phase_switch_turns_the_need_step_off[exercise_arm, discriminating_search]`, `::test_batch_commands_honour_their_switches` |
| F16 | Medium | Pick interventions precede successful serving and the R1 decision | fixed | `73a26223` | `test_learner_pick_proposal.py::test_a_failed_pick_leaves_no_delivered_intervention`, `::test_the_delivery_carries_the_exact_decision_of_the_block_that_served_it`, `::test_without_a_logged_decision_none_is_recorded`, `::test_an_imported_exercise_is_delivered_when_its_item_is_served`, `::test_an_import_that_has_not_written_the_item_is_refused_before_serving` |
| F17 | Medium | Retention hypotheses are created without assisted-success evidence | fixed | `a84aede7` | `test_discriminating_search.py::test_retention_is_posed_only_after_an_assisted_only_success_with_the_active_predictor`, `::test_retention_needs_a_recent_assisted_success` |

### What each fix does

- **F1.** `find_sources` hits carry each span's effective role (a solution region's body included). The tool dispatcher's `find_sources` and `compare_sources` views drop solution regions and assessment-lane spans for every model reader, bound to an item or not.
- **F2.** `ai/spend.SpendEnvelope`: a thread-safe money bound that every `SpendBudget` admitted while it is active shares, including threads run in a copied context. Each metered request reserves its estimate in every active envelope before it is sent. The daily cap is an observed envelope: the service's receipts since UTC midnight plus this process's requests in flight. Subscription requests are tallied from tokens (`estimated_only`) and never refused; there is no request-count limit. One import's solution match, authoring, ladder, family judge and background check share the import cap and the daily cap. Harvest and verify share one `--max-cost-usd` envelope. Dry runs report calls, tokens and dollars.
- **F3.** `record_source_offer_shown` writes `source_exposure_events` for every span that became visible, whatever `source_service.interventions` says, and the intervention links those exposure ids.
- **F4.** Immediately before the follow-up chooser commits an item that a need was fulfilled with from the learner's textbook, it re-checks the exposure rule with no model call. The rule's facts at serving time are:
  - an attempt;
  - a reveal on the item or its family;
  - source text shown from its span or its book solution;
  - an impression from any proposal;
  - a worked example studied since, within the item's teaching scope, that the judge called `equivalent` or `related`, or never judged.

  The need step records its retrieval provenance on the import (intent, proposal, rule 4's scope). A contaminated item is filtered as `exposed_since_valuation` and the next candidate is chosen, or a need is recorded and the caller re-queries. §5.4 says a system-initiated check "is not served as one". The follow-up is a diagnostic check, so it is not served as practice in its place. §8.5 item 4 says "serves it as practice, labelled", which reads differently; §5.4's rule is the stricter one, and this fix follows it.
- **F5.** Write-ahead: before the vault write, the import row names its item and keeps the ladder's result, or a pending-check marker carrying this process's token. The `written` status and its check row commit in one transaction. A background check commits its row together with the import's completion (key status set, marker cleared). `resume_import` completes whatever a dead process left:
  - a write whose commit never happened (no model call);
  - a written import with no check row (restored from the persisted result);
  - another process's pending check. The ladder runs again against the content the import was written with. An item edited since gets no check and is marked `superseded_by_edit`.

  A retried job resumes instead of returning at once. The sidecar resumes pending checks at startup, off the request path. The Reader import's background checks carry the same marker, and `sources exercises verify` completes a pending import it re-checks.
- **F6.** `SourceOffers` polls a queued import until it is written, rejected or failed, and offers "check again" after six minutes. A failure is shown with its reason and a "try again". A written import is served through `plan_learner_pick` with the proposal and the import id, and the toast names the key's label. When the plan is off, the pick is no longer announced as added; the open-list path ("open") is offered instead, wired from `App` through `AskOverlay`.
- **F7.** The valuation receipt lists hard exclusions (`excluded`) separately from unvalued candidates. Final assembly drops them from the checks, the presentation order and the learner-initiated relevance tail, on both arms.
- **F8 (G6).** An imported item whose key for its current content is not verified is ineligible for `discriminate` and `retention` (`unverified_key`; its key status is on the eligibility record). Ordinary practice keeps it, labelled as before.
- **F9.** `find_practice` passes the cursor's judged exercise keys into the arm, which drops them (`judged_earlier`) before cutting its pool. The cursor's deeper list depths reach regions beyond the first retrieval depth.
- **F10.** For an open episode under the robust cutover, the episode's compiled instruments (`eligible_instruments`, on the channel `load_pinned_channel` rehydrates) are valued with `instrument_ensemble`: `pinned_channel` regime, `compiled_instrument` basis, and the instrument's own expected seconds. Same-shape requests go through `evaluate_selection` exactly as `robust_selection` does, so pinned instruments license a system-initiated check where the robust path can act. Below the cutover, or with no pinned channel, instruments stay ordinary items and the reason is recorded. The parity holds over the problem's prior (`H_OTHER` excluded and recorded, §8.3.1): given the same channel, instruments and posterior, the verdict, winner and robust EIG per second match.
- **F11.** Publication of a PF variant of a textbook exercise commits a `reference_key_checks` row with its published mark. The row is bound to the published content's hash and comes from PF's own verification of that candidate: `execution_cas` or panel+sympy gives `checked`, panel agreement on a non-symbolic answer gives `panel_agrees` (the import ladder's rule), and a quote-verified supported span gives `book_solution`. Any other verification writes nothing, so the label stays honest. Nothing is inherited from the parent, and a retried publication writes no second row.
- **F12.** The outcome replayer (`retrieval_outcomes.v2`) searches for the next independent attempt. It skips assisted attempts and any attempt contaminated in the cold delay before it, reading persisted rows only:
  - a reveal on the item or its LO;
  - the intervention's passage or the item's own source text shown;
  - another retrieval intervention on the same targets;
  - a final coldness receipt that failed `unassisted`, `answer_leakage` or `exposure_isolation`.

  When only contaminated attempts exist so far, the state is `contaminated_or_assisted`; a later independent attempt replaces it on rebuild. A submitted "don't know" is an unaided answer: `cold_dont_know`, counted as a measured failure. `learner_declined` is now the proposal's own `skipped` tap with no attempt.
- **F13.** One reference contract. `valuation.REFERENCE_KINDS` (the kinds plus the aliases `facet` → `facet_state` and `lo` → `learning_object`) is the tuple the tool schemas publish, and every adapter parses it; a `learning_object` ref is that LO's hypothesis set. Named gaps go through the learner-text gaps branch's `named_gaps_for_card()`, feature-detected by its module and table:
  - a `durable` target is that misconception;
  - a `learning_object` target (a missing prerequisite) is that LO's set;
  - a reversed gap names nothing (`named_gap_reversed`);
  - a holding-pen `candidate`, or no target, is `unmapped_named_gap`.

  The tool dispatcher, `propose_practice` and remediation's misconception resolution all read gaps through this mapping.
- **F14.**
  - The positive `roles` filter admits a span whose effective ingest hint, or whose RW4e role proposal (`source_object_versions.authorial_role`), is in the list. A low-confidence proposal counts only when nothing better exists. Scope, ingest exclusions and item links still apply (the Reader's G44), and the search receipt says what admitted each span.
  - `facet_ids` rank the facets' teaching source links as one more list, and verification is told what the passages should bear on. This holds in `find_sources` and `compare_sources`.
  - `find_sources(intent="compare")` delegates to `compare_sources` under the caller's policy.
- **F15.** The need step and the harvest and verify batches take the arm and the valuer from the same switch-aware wiring as the RPCs and the tutor. A switched-off phase sends the need to generation, and the batch reports `disabled`.
- **F16.**
  - `plan_learner_pick` records the learner's selection (the usage signal and the serve-time independence verdict) before serving, so a bad proposal is refused before anything is served.
  - The S5 intervention is written only after `learner_pick` succeeds. It carries the `decision_ref` of the block that served the item: R1's `plan_block` row once its logger is registered on merge, else null. The "latest matching row" lookup is removed.
  - A textbook exercise's import RPC records only its selection. Its delivery is recorded when the imported item is served (`sourceExerciseImportId`).
- **F17.** `retention_problem` poses "holds unaided" only when the most recent successful attempt on the LO or facet was assisted, with no unaided success since. "Assisted" and "successful" are S5's definitions, so the question and the outcome that answers it read the same. The prior is the active predictor's P(success) on the item of that success (`placement.predictor.active_predictor`), with `prior_basis = predictor:<name>` and its version. Otherwise the result is `no_recent_assisted_success` or `no_prior`.

### Build-record deviations now resolved

`docs/reviews/source-practice.md` §3 listed these as deviations. They no longer are:
- **1:** compiled-instrument parity is built (F10).
- **2:** retention's assisted-only condition and the active predictor's prior are enforced (F17).
- **7:** the background check is durable (F5).
- **11:** an imported exercise's delivery is recorded when the item is served (F16).

**Claims the review disputed:**
- Model readers no longer see solutions (F1).
- Paging is resumable for exercises (F9).
- The Reader's contract covers RW4e roles, facets and compare (F14).
- Interventions are written only on delivery, with the exact decision (F16).
- Paid commands are capped (F2).

Hypothesis movement in S5 stays references-only, for the calibration track (build open question 8).

### Paid calls

None in this fix step. All tests use fakes. The backup copies under `fixtures-local/sources-run/` were last written at 03:09, by the build stage's live run, before this review. The resumed stage's second live run on those copies (45 requests, $0.0328 reported) is recorded in `docs/reviews/source-practice.md` §4.

## Gate

This fix step was interrupted (the usage limit) after its last fix commit `a2da0362` and before its gate ran. The stage resumed on 2026-10-13 and ran the gate at `7e7ef832`. That commit adds the fixes recorded in `docs/reviews/source-practice.md` §2a: the spec stage's final-verify F13 (regrades and C3) and three defects from the second live run.

Python 3.12.14 and SQLite 3.53.1, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite, `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8919 passed, 0 failed (at `7e7ef832`) |
| Durability lane, `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 94 passed, 8825 deselected, 0 failed (at `7e7ef832`) |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | typecheck clean; vitest 33 files, 169 tests passed; build ok |
| `cargo check` | not required: nothing under `src-tauri` changed (the two new parameters go through the existing passthroughs) |
| DB references | no schema change in this fix step. The fixes moved source lines that 47 configuration citations named, so the references were regenerated (`1a3fe61d`); validator 0 errors |

## Re-review (second Codex pass, 2026-10-13)

**Codex job:** `~/.cache/codex-agent/jobs/20261013-085259-M5bPQS` (read-only review of the branch at `f104cd5d`; synthetic in-memory checks, no vault opened, no paid call).

Each finding was reproduced first: a test that fails on the code before its fix (checked by stashing the source change and re-running), then fixed. None was rejected. Tests use fakes only.

| ID | Severity | Title | Verdict | Commit | Test (or reason) |
|---|---|---|---|---|---|
| F1 | High | Crash recovery can certify an unchecked edit | fixed | `8b9bbad1` | `test_source_exercise_import.py::test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit[job_retry, startup]` (before: the edited key `6` was `book_solution`) |
| F2 | High | The daily spend cap does not cover ordinary retrieval | fixed | `8ac36a38` | `test_source_service_spend_envelopes.py::test_an_ordinary_practice_request_respects_the_daily_cap`, `::test_a_verified_passage_request_respects_the_daily_cap`, `::test_a_comparison_pays_for_nothing_once_the_daily_cap_is_spent`, `::test_the_daily_cap_is_shared_by_concurrent_processes` |
| F3 | High | Source-first diagnostic drafts cannot pass their admission gate | fixed | `d2f3f950` | `test_source_first_needs.py::test_a_discriminate_need_is_fulfilled_with_the_screens_profiles_and_rubric_links` (new end-to-end success case); `::test_discriminate_drafts_must_pass_the_choosers_own_gate` rewritten: it asserted the failure, it now checks that the gate reads the screen's links and a refused draft is never written |
| F4 | High | Unknown worked-example equivalence permits independent checks | fixed | `58c1b235` | `test_discriminating_search.py::test_an_unjudged_studied_worked_example_excludes_every_independent_intent`, `::test_a_pick_with_an_unjudged_worked_example_is_served_as_labelled_practice` |
| F5 | Medium | Value searches stop at a fixed candidate page | fixed | `5a5ba660` | `test_discriminating_search.py::test_a_value_search_pages_on_until_a_stop_inside_one_call`; `test_tool_dispatch_policy.py::test_a_find_practice_tool_result_can_be_continued`; `test_source_first_needs.py::test_a_need_resumes_its_search_before_it_goes_to_generation` |
| F6 | Medium | Budget refusal permanently skips unjudged candidates | fixed | `f9df005a` | `test_discriminating_search.py::test_a_refused_rerank_leaves_its_page_pending_and_a_resume_judges_it[over_budget, failed]` |
| F7 | Medium | Interactive imports lose the proposal's constraints and independence checks | fixed | `5b52ef1c` | `test_source_exercise_rpcs.py::test_an_interactive_import_is_validated_against_its_proposal_and_corrected`, `::test_an_imported_exercise_is_rechecked_for_independence_when_served`; `SourceOffers.test.tsx`: the import's correction is shown |
| F8 | Medium | The comparison kill switch has an alternate bypass | fixed | `3892a8c3` | `test_find_sources_intents.py::test_the_compare_switch_holds_on_every_entry_point` (`propose_sources`, `propose_comparison`, `find_sources_for_caller`, the `find_sources` RPC; before: the comparison's model was reached) |
| F9 | Medium | Recovery mistakes another process's live check for abandoned work | fixed | `45c62227` | `test_source_exercise_import.py::test_a_live_check_in_another_process_is_never_taken_over`, `::test_overlapping_recoveries_run_one_check`, `::test_a_late_check_whose_lease_was_taken_over_records_nothing` |
| F10 | Medium | Plan-off picks record delivery before the learner opens the item | fixed | `06d90dbe` | `test_learner_pick_proposal.py::test_with_the_plan_off_delivery_is_recorded_when_the_item_is_opened[item, imported_exercise]`; `SourceOffers.test.tsx` (open carries the proposal and import), `practiceOffer.test.ts`, `PracticeScreen.test.tsx` (the serve carries it) |
| F11 | Medium | Calibration records omit required decision and exposure data | fixed | `b424e0a6` | `test_valuation_calibration_fields.py::test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`, `::test_decision_fields_reach_the_record_and_the_outcome_derives_the_action_change`, `::test_a_studied_worked_example_records_the_seconds_since_exposure` |

References regenerated at schema head 191: `a565f617`.

### What each fix does

- **F1.** The import hashes the authored draft as it will be written (`draft_content_hash`, `reference_content_hash` over the prompt, key and rubric) before the ladder runs. The write-ahead record (the ladder's result, or the pending-check marker) and the import row carry that hash before the vault write. `_commit_written`, in one IMMEDIATE transaction, binds the check row to that hash only, never to the item as it is now. An item edited between the write and the commit is recorded `superseded_by_edit` and stays unverified until its own check. A record with no verified hash binds nothing (`unbound_verdict`).
- **F2.** The daily cap is a database-shared envelope (`SharedDailyEnvelope`, migration 191 `source_service_spend`, WORKFLOW). Each metered request reserves its estimate in one BEGIN IMMEDIATE transaction that checks the day's total (every process's reservations, never less than the service's own receipts) plus the estimate against the cap, so a sidecar and a CLI batch cannot both spend the same allowance. In flight a reservation counts its estimate, reconciled upward; once the request finished it counts the cost the provider reported (as the receipts-based cap did), else its estimate. A request another cap refused is removed. Envelope reservations now carry handles (`ai/spend.py`). Every complete service operation runs under it, not only its last call: `propose_practice` (the query embedding, every rerank page, the arm's search, the valuation's judges), `propose_sources` (search, rewrite, verification), `compare_sources` on every entry point, ranked remediation passages, a need's search, and the harvest and verify batches. Subscription requests are still never refused and are tallied `estimated_only`.
- **F3.** The valuation keeps each screened exercise's persisted screen (its `judgment_ledger` row, `screen_judgment_id`) on its receipt entry, and a `discriminate` need passes that screen to the import. Before validation, `screen_profiles` writes it onto the draft as §8.4 says: each misconception slot of a complete screen becomes a `DiscriminationProfile` (the screen's observable signature, `source = misconception_registry`) and a rubric fatal error linking the registry belief (`max_grade` 1, the convention of every misconception-linked fatal error the authoring paths write). It first checks that the screen is complete, each belief exists and is active, and each signature differs from the key; otherwise the draft fails validation and is not written. The follow-up chooser's unchanged gate then reads the linked fatal error (its bridge). The import's validation records the screen, the linked beliefs and the gate's verdict. Exercise screens are now cached per exercise and hypothesis space (F5), so this reads one row.
- **F4.** An unjudged studied worked example (the judge unavailable, over budget or failed) adds the typed reason `worked_example_unjudged` for every independent intent, `discriminate` included, until a verdict resolves it. Practice keeps the candidate. A learner's pick is served as practice with a label that names the actual reason (`practice_label`), not "you've seen this question". Spec §5.4 rule 4 now says so.
- **F5.** `find_practice` pages inside one call for `discriminate` and `retention`. Each page is one judge call over the next unjudged items and exercise regions. The valuation runs over every relevant candidate found so far, so it stays conditional across pages. Paging ends only at exhaustion, a refused budget or a caller's `deadline`, or the perfect-information stop; `candidate_pool` bounds a prompt, never the search. A stop before exhaustion stores its cursor on the proposal's receipt (`signals.paging`), carrying the relevant candidates (judgments, provisional metadata, exercise records), and a continuation values them again with the new pages. The `find_practice` tool returns `paging.continue_from` (the stored proposal, never an editable cursor) and accepts `continue_from` for the same caller, query and intent. A source-first need resumes its search from the cursor before it goes to generation.
- **F6.** Only completed, persisted judgments advance the cursor. A page refused by its budget, a failed call or an unavailable judge stays pending and is re-retrieved at the same list depths; paging reports `budget` or `judge_unavailable` with the judge's status. A judge switched off by configuration still advances its display page. A page that answered without judging anything new stops paging instead of looping.
- **F7.** The `import_source_exercise` RPC rehydrates what the exercise was proposed for from the proposal's receipt and passes it to the job as plain data: the constraints and intent, the plan estimator's minutes per practice mode when minutes were bounded, and a `discriminate` proposal's persisted screen. The job validates the authored draft against it (`content/authoring/draft_validation.py`, re-exported by `instructional.validation`, since the content layer may not import the service). A learner's pick is still written (learner authority) with the correction recorded, returned by `get_source_exercise_import` and shown on screen. Serving an imported exercise from a `discriminate` or `retention` proposal runs the same serve-time independence recheck as an existing item, with the originating proposal's impression exempt; a draft that failed its validation is served as practice with its correction.
- **F8.** `compare_sources` itself refuses with `source_service_disabled` when `source_service.enabled` or `source_service.compare` is off, so `find_sources(intent="compare")` can no longer reach a comparison, or pay for one, through its delegate.
- **F9.** Every key check runs under a durable claim on the existing `judgment_work_claims` machinery (task `source_key_check`, one claim per import): the import's own check, a background check, startup recovery, the Reader import's check, and `verify` of a pending import. The claim is acquired atomically before the ladder starts, its lease renewed while the ladder runs (`CHECK_LEASE_SECONDS` 120, heartbeat 30 s, process-liveness bounds), and the check row and the import's completion commit only while the claim holds (epoch fencing). Recovery takes over an expired lease only. Another process's live check is left alone, overlapping recoveries run one ladder (each claim has its own owner), and a check whose lease was taken over records nothing. The sidecar's startup waiter retries held checks once their lease lapses.
- **F10.** With the plan off, `plan_learner_pick` records only the selection (the usage signal and the serve-time verdict) and answers `delivery: on_open`. The open-list serve (`get_practice_item` with a session) takes the proposal and import identity and records S5's delivery there, after its own serve-time recheck. A pick's delivery is idempotent: one intervention per picked proposal candidate, however often the item is loaded. Frontend: `SourceOffers` keeps the proposal and import with its "open" action, `App` carries them as the practice offer's proposal origin, and `PracticeScreen` passes them on the item's serve; the Rust `get_practice_item` command forwards both.
- **F11.** The valuation receipt keeps each valued candidate's and check's member-0 `P(E|H)` table, and a decision-mode check keeps its expected minutes, predicted P(E), EVSI and the decision's action before the observation and after each outcome. The intervention record copies them with the problem's prior, prior basis and state hash. From persisted rows only, the outcome replayer (`retrieval_outcomes.v3`) derives two things: the action after the observed bucket and whether it flipped, and the posterior movement on the target hypotheses by Bayes over the record's own table, labelled `bayes_update_member0` and shown beside the predicted EIG. This is the model's implied movement, not the diagnoser's replayed posterior (build-record deviation 10 updated). The exposure rule records when each studied worked example was shown or read, and `seconds_since_related_exposure` is the time since the most recent related exposure (a related or unjudged example, or an earlier impression).

### Claims the re-review disputed

- "Every phase S0–S5 is built": diagnostic fulfilment (F3), value-search paging (F5, F6) and the calibration outputs (F11) are now built; the §17 evaluation extensions are not (below).
- "The daily cap is shared by every phase": now true, across processes too (F2).
- "Recovery never verifies edited content": now true at the pre-commit window as well (F1).
- "Interventions are written only on delivery": now true for the plan-off path (F10).
- "Phase switches restore prior behavior": the comparison switch now holds on every entry point (F8).

### Not done in this step

- **§17 evaluation extensions.** Not built. These are the practice evaluation's items-only versus both-kinds condition, the T6 harness's per-intent query set with verification as a condition, and the ladder's rung-agreement rates. The re-review listed them as a conformance gap, not a numbered finding. Each needs LLM-labelled held-out requests or paid rung-2 runs on fixture copies, which is evaluation work beyond a fix step. Open question for the owner.
- **Scope note** (from the re-review's conformance table): the general vault-writer change `73e5b721` stays as recorded in build deviation 16.

### Paid calls

None in this fix step. All tests use fakes; no vault copy was opened.

### Gate (re-review fixes)

Python 3.12.14 and SQLite 3.53.1, `TMPDIR` set to the worktree's `fixtures-local/tmp`.

The gate ran at `a565f617` (the last code and reference commit; this record and two documentation edits follow it).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite, `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8944 passed, 0 failed (was 8919; 25 new tests) |
| Durability lane, `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 94 passed, 8850 deselected, 0 failed |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | typecheck clean; vitest 33 files, 172 tests passed (was 169); build ok |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok (`get_practice_item` forwards the proposal and import ids, F10) |
| DB references (schema changed: migration 191) | head fixture renamed `migration_head_191` (191 applied in place, rollback journal, `integrity_check` ok, `foreign_key_check` clean; README and every hard-coded path follow); `db_generate_reference.py` at head 191 (`source_service_spend` described), `db_validate_reference.py` 0 errors (`a565f617`) |

## Third pass (Codex re-review of the fixes, 2026-10-13)

**Codex job:** `~/.cache/codex-agent/jobs/20261013-100441-ZodnI7`. A read-only review of the re-review fixes at `b967f3ad`, using source inspection and isolated in-memory reproductions. It opened no vault and made no paid call.

**Verdict:** REOPENED.
- **Confirmed fixed:** F1, F3 and F4.
- **Reopened:** F2 and F7.
- **New defects from the fix commits:** F12 and F13.

Each open finding was reproduced first with a test, which failed on the code before its fix, and then fixed. None was rejected. All tests use fakes.

| ID | Severity | Title | Verdict | Commit | Test (or reason) |
|---|---|---|---|---|---|
| F1 | High | Crash recovery can certify an unchecked edit | confirmed fixed (no change) | `8b9bbad1` | Codex confirmed. |
| F2 | High | The daily cap took `max(ledger, receipts)`: two concurrent reservations over prior spend were both admitted | fixed | `be57a8fe` | `test_source_service_spend_envelopes.py::test_prior_receipts_and_reservations_in_flight_add_up_under_the_cap`. Before the fix, the second $0.15 was admitted over $0.80 of prior receipts. `::test_a_settled_request_is_counted_once_not_by_its_receipt_and_its_reservation`. Before the fix, $0.99 + $0.02 was admitted under the $1 cap. |
| F3 | High | Source-first diagnostic drafts cannot pass their admission gate | confirmed fixed (no change) | `d2f3f950` | Codex confirmed. |
| F4 | High | Unknown worked-example equivalence permits independent checks | confirmed fixed (no change) | `58c1b235` | Codex confirmed. |
| F7 | Medium | The interactive import validated minutes estimated before authoring, ignoring the authored duration | fixed | `5cee8877` | `test_source_exercise_rpcs.py::test_an_interactive_import_bounds_the_authored_drafts_own_duration`. Before the fix, a 20-minute draft passed a 5-minute bound as `minutes=3.5`, while the plan's estimator gives 20.5. `::test_the_carried_duration_response_is_the_plan_estimate_of_the_authored_draft` checks parity with `daily_plan.estimates.Estimator` for 8 authored durations and 2 modes. |
| F12 | Medium | Continuations restore source exercises that fail current filters | fixed | `47f1d391` | `test_discriminating_search.py::test_a_continuation_with_other_constraints_is_refused`. Before the fix, narrower facets resumed the search. `::test_a_carried_exercise_imported_since_is_not_restored`. Before the fix, the imported exercise was proposed again. `test_tool_dispatch_policy.py::test_a_continuation_with_narrower_filters_is_refused`. Before the fix, `continue_from` with other facets was accepted. |
| F13 | Medium | Exposure age mixes valuation-time and delivery-time measurements | fixed | `9380a913` | `test_valuation_calibration_fields.py::test_exposure_age_is_measured_at_delivery_not_at_valuation`. Before the fix, 300 s was persisted for an example studied an hour and five minutes before delivery. The correct value is 3,900 s. |

The references were regenerated in `9489e676`. The table description for `source_service_spend` follows F2, and the source stamps and configuration citations follow the moved lines. The validator reports 0 errors. There is no schema change: no migration was added, and the head is still 191.

### What each fix does

- **F2.**
  - The day's total is now every reservation in `source_service_spend`, **plus** the service's receipts that no reservation covers. Those are spend from before the ledger existed, or spend by a path outside the envelope.
  - The total is never `max(ledger, receipts)`.
  - Settled receipts are not double-counted. A request's root receipt names its reservation: `SpendBudget.request` writes `budget_json.envelope_reservations` from `SpendEnvelope.reservation_ref`, which only the shared daily envelope implements. `spend_since(ledgered=...)` leaves a receipt out of `usd` when its reservation is in the ledger for that envelope and day, and counts it in `metered.ledgered_requests`.
  - The same total drives admission (`reserve_service_spend(unledgered_usd=...)`), the envelope's report and `service_spend_today`. `service_spend_today` reports `reserved_usd` and `unledgered_receipts_usd` separately.
  - A receipt from another day's reservation still counts on its own day, which is conservative.
  - This supersedes the re-review's description of F2 ("never less than the service's own receipts").
- **F7.**
  - The import RPC no longer computes minutes before authoring.
  - For each practice mode, it carries the injected plan estimator's response to the authored duration (`instructional.practice.duration_response`):
    - `minutes = at_zero + per_authored_minute × expected_minutes`;
    - `fallback_minutes` when the draft authors none.
  - The response is sampled through the estimator itself and never re-derived. DL1 §6.4's estimate is affine in the authored prior, and a third sample point checks this. A response that is not affine is not carried, so the bound is refused, never passed.
  - The job evaluates the response on the authored draft's practice mode and `expected_minutes` (`content.authoring.draft_validation.duration_estimator`). The content layer still imports neither the plan nor the service (SC12, and the plan's leaf-consumer rule).
  - Note on reachability: the import's authoring contract does not author `expected_minutes` today. The defect bites once a draft carries one, as Codex's synthetic draft did. The validator was already reading the field.
- **F12.**
  - **Request binding.**
    - Every cursor now carries `request`, a content key of the normalized query and every normalized constraint (`continuation_binding`, computed after the caller's constraints are applied).
    - `find_practice` refuses a cursor for another request (`ContinuationMismatch`, a `ValueError`). This covers every entry point: the tool's `continue_from` (answered `continuation_invalid`), the RPC's cursor (`validation_error`) and a need's resume. A changed filter is a new search.
  - **Readmitting carried exercises.**
    - Carried exercises are readmitted by the arm's own rules, with no search and no model call (`exercise_candidates(readmit=...)`).
    - An exercise is dropped, with a count, when:
      - it is now outside the teaching scope;
      - it is no longer an exercise region of its extraction;
      - it was imported since;
      - an ingest exclusion now covers it;
      - its region reads differently from the text the judge read (`changed`).
    - Carried exercises are also rechecked against the exact filters on their carried metadata.
    - With the arm off, or exercises not requested, nothing carried is restored.
    - The receipt records `signals.continuation` (carried count and drops).
    - A carried exercise now keeps the record the arm builds now, not the stored one. Carried items were already re-admitted against the current corpus.
- **F13.**
  - The exposure rule now persists when each related exposure happened: `worked_example.related_exposure_at`, and `inputs.impression_at`. The impression stamp is the latest earlier impression. Before, it was the last one listed, which could be an older item impression listed after span impressions.
  - `record_pick` measures `seconds_since_related_exposure` from the most recent of these, at the delivery instant. The intervention's `created_at` is pinned to that same instant.
  - A verdict stored before these stamps existed is carried forward as its `checked_at` minus the age it measured then.

### Paid calls

None in this fix step. All tests use fakes. No vault copy was opened.

### Gate (third-pass fixes)

Environment: Python 3.12.14 and SQLite 3.53.1, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

The gate ran at `9489e676`, the last code and reference commit. Only this record follows it.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite (`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`) | 8952 passed, 0 failed. Up from 8944; the 8 new tests are F2 2, F7 2, F12 3 and F13 1. |
| Durability lane (`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`) | 94 passed, 8858 deselected, 0 failed |
| Frontend: `npm install`, `typecheck`, `test`, `frontend:build` | Not required: nothing under `apps/learnloop-tauri` changed. |
| `cargo check` | Not required: nothing under `src-tauri` changed. |
| DB references | No schema change; the head is still 191. `db_generate_reference.py` was rerun because the `source_service_spend` description changed, and lines moved. `db_validate_reference.py` reports 0 errors (`9489e676`). |

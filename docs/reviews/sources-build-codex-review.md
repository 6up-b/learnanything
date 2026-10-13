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

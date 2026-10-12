# Slice 2 T1 (M3): Codex review fixes

Branch `slice-2/t1`, worktree `learnanything-t1`. The review (codex job
`20261012-140551-bXMu4Z`) read the stage at `a647b04d` and reported ten
defects, three High. All ten reproduced; all ten are fixed in `c5ae36a2`,
with the DB reference regenerated and this file in the commits after it.
None is rejected.

Owner decisions applied: the Slice A plan §5 rule 6 billing (Codex on the
subscription is counted in calls, cost `estimated_only`), frictionless
defaults (the new escalated-repair request is on by default behind a kill
switch), and the owner-directed shape: the shortlist + judge +
`judgment_ledger` step stays one component parameterized by kind. The new
claim, producer-reuse, model-activation and cutoff-provenance machinery all
live in `learnloop/matching/` and know nothing about misconceptions, so the
learner-text-gaps stage inherits them.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (or reason) |
|---|---|---|---|---|---|
| F1 | High | Live recurrence calls bypass the enclosing command's spend controls | fixed | `c5ae36a2` | `test_recurrence_live.py::test_an_exhausted_command_budget_stops_the_judge`, `::test_a_cancelled_command_stops_the_judge`, `::test_the_judge_runs_on_the_commands_budget_and_shows_in_its_summary`, `::test_the_dry_run_plans_the_recurrence_work_on_the_same_caps` |
| F2 | High | Prepared groups become authoritative before the successor is activated (and the kill switch waits for a refresh) | fixed | `c5ae36a2` | `test_recurrence_commands.py::test_a_failure_after_preparation_leaves_no_group_in_force` (two failure points), `::test_the_upgrade_activates_its_prepared_groups_after_the_switch`, `::test_the_kill_switch_takes_effect_at_vault_open_with_groups_already_populated` |
| F3 | High | Upgrade accepts an incomplete or failing guard | fixed | `c5ae36a2` | `test_recurrence_commands.py::test_an_m1_case_from_a_run_is_required_and_its_false_merge_blocks_the_switch`, `::test_a_registered_case_the_judge_never_saw_blocks_the_switch`, `::test_verdicts_split_across_two_models_do_not_pass_for_the_configured_one` |
| F4 | Medium | Changing judge models cannot rerun previously judged guard pairs | fixed | `c5ae36a2` | `test_matching.py::test_reuse_is_per_producer_and_a_rerun_supersedes_the_same_producer`, `test_recurrence_commands.py::test_a_false_merge_blocks_the_switch_and_a_fixed_judge_reruns_through_the_guard`, `::test_an_explicit_rerun_supersedes_the_same_models_false_merge` |
| F5 | Medium | Concurrent judging duplicates paid work and admits conflicting verdicts | fixed | `c5ae36a2` | `test_matching.py::test_a_concurrent_worker_skips_a_claimed_pair_and_never_pays_twice`, `::test_an_expired_lease_is_reclaimed_and_the_late_verdict_is_fenced_out`, `::test_a_failed_call_releases_its_claim` |
| F6 | Medium | B1/B3 do not implement Phase 5a's actual harness contract | fixed | `c5ae36a2` | `test_recurrence_benchmarks.py::test_b1_and_b3_run_through_phase_5as_harness_contract`; `::test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged` (skips until 5a merges); a manual run through 5a's actual code (below) |
| F7 | Medium | B3 recommends cutoffs for a different vector width than production | fixed | `c5ae36a2` | `test_recurrence_benchmarks.py::test_b3_recommends_only_at_the_serving_width_with_its_provenance`, `::test_b3_replays_the_vaults_labelled_pairs`; `test_matching.py::test_a_cutoff_applies_only_to_the_vectors_it_was_measured_on`; `test_recurrence_commands.py::test_a_blocking_cutoff_must_be_a_cosine_and_name_what_it_was_measured_on` |
| F8 | Medium | Retrieval switches to a partially embedded replacement model | fixed | `c5ae36a2` | `test_matching.py::test_a_partially_backfilled_replacement_model_never_ranks` |
| F9 | Medium | K=3 does not actually obtain an escalated repair | fixed | `c5ae36a2` | `test_recurrence_live.py::test_identical_repairs_three_times_obtain_a_different_one_at_escalation`, `::test_the_same_repair_again_is_labelled_honestly` (repeated operator, failed request, switch off); one live Codex call (below) |
| F10 | Medium | Benchmark dry-run omits the hypothesis writer's cost and token admission | fixed | `c5ae36a2` | `test_recurrence_benchmarks.py::test_the_b1_dry_run_prices_a_metered_writer_with_its_tokens`, `::test_b1_dry_run_then_run_with_fakes` |

## Reproduction (before fixing)

The new tests were run against the pre-fix tree (`git archive a647b04d`,
the new test files copied in, the worktree's interpreter): 12 failed, each on
the reviewed behaviour rather than on setup, for example F1 "no judge call
past the command's caps", F2 "prepared, not active" (the groups were in force
with the vault still at `mvp-0.10`), F4 `['already_judged'] == ['judged']`
(model B never asked), F5 `['judged'] == ['claimed_elsewhere']` (the second
worker paid again), F9 no escalated-repair request at all. Five behaviours
were also checked with a script that runs unchanged on both trees:

| Finding | Pre-fix (`a647b04d`) | Fixed (`c5ae36a2`) |
|---|---|---|
| F2 kill switch: groups in force after vault open with `recurrence.enabled = false` | yes | no |
| F6 B3 with Phase 5a's tuple `dims` | `TypeError: slice indices must be integers` | runs |
| F7 B3 default width vs `embedding.dimensions` (16 in the test vault) | 1024 vs 16 | 16 vs 16 |
| F8 pairs ranked when a replacement model holds 2 of the vectors | ranked by `new/model` (the partial index) | ranked by the previous complete model only |
| F10 B1 dry run, metered writer route, no price | `dry_run` (admitted) | `over_budget: Unknown price` |

## What changed, per finding

- **F1.** `apply_diagnosis` now takes the job's `spend`, `cancelled` and the
  diagnosis client (`writer_factory`) and passes them to `recurrence_step`
  and `record_escalation`. Inside `learnloop diagnose drain|retry` every
  hypothesis-embedding request, judge call and escalated-repair request is
  admitted on the COMMAND's `ReviewSpend` (its caps, its cancellation; it
  shows in the command's spend summary, receipted under the attempt) and
  only while every other queued diagnosis still fits after it
  (`_remaining_diagnoses_reserve`, the retrieval rule). A refusal sends
  nothing and leaves the pairs for the backlog. The per-job budgets
  (`live_judge_caps`, `ESCALATION_REPAIR_CAPS`) apply only outside a
  budgeted command (sidecar worker, inline CLI/TUI), and they now carry the
  worker's cancellation. The dry run (`plan_diagnosis_jobs`,
  `plan_unqueued_diagnosis`) adds a `recurrence` block: an upper bound per
  job of `judge_max_pairs_per_attempt` judge calls, one embedding request
  and one escalated-repair request, priced on the same caps, with `fits`.
- **F2.** The upgrade builds the groups as PREPARED
  (`hypothesis_recurrence_state.active = 0`) before the config rename and
  activates them after it (`activate_recurrence_groups`: a flip when the
  inputs are unchanged, else a rebuild). `recurrence_group_map` returns only
  ACTIVE groups, so a failure anywhere before the rename (p0 activation,
  registry refresh, the rename itself) leaves every consumer on exact keys;
  the next refresh at `mvp-0.10` clears the prepared rows. Consumers that
  hold the vault (normalization, durable promotion's promote step, error-hunt
  minting, the live step, the shortlist, the escalation) call `active_group_map(vault,
  repository)`, which also checks the effective algorithm version and kill
  switch, and `sync_vault_state` (vault open in the sidecar, TUI and CLI)
  re-syncs the projection, so `recurrence.enabled = false` takes effect at
  vault open.
- **F3.** Cases an M1 run adds with `recurrence guard --from-run` are
  registered in `recurrence_guard_cases` (RAW_LEDGER, append-only) the first
  time the guard runs them, and stay required. `guard_status` defaults to
  the built-in plus registered suite and, given `judge_model`, counts only
  that model's standing (not superseded) verdicts on the current prompt and
  input; any `same` among them is a false merge. The upgrade passes the
  configured judge model (it refuses when the route's profile names none)
  and names other models' verdicts as not counting.
- **F4.** `judge_pairs` needs the producer before any call
  (`executor.producer`, the judge model) and reuses a verdict only from that
  producer. A route change therefore asks the new model on the next run
  (the test follows the upgrade's own instruction: change the route, rerun
  the guard, upgrade). `recurrence guard --rerun` asks the same model again
  and each new verdict supersedes its previous one.
- **F5.** `judgment_work_claims` (WORKFLOW): before the call, a short write
  transaction claims the question (task, producer, prompt version, input)
  with a lease; the network call runs outside any transaction; a live lease
  held by another worker skips the pair (`claimed_elsewhere`, nothing paid);
  the verdict is appended, and the claim completed, only while the worker's
  lease epoch still holds, so an expired worker's late verdict is `fenced`
  and never lands beside the re-claimer's; a failed or refused call releases
  its claim. Lease 900 s by default (the Codex judge turn deadline is 180 s).
- **F6.** The suites read 5a's actual request and context: `dims` is a tuple
  of widths (an int still works; embedded once at the widest, MRL-truncated
  per width, results keyed `model@dims` when several), B1's `k` is its own
  constant (25), and B1's writer is a harness role,
  `recurrence_hypothesis_writer`, served by the `diagnosis` task.
  `register_suites(registry, role_tasks=...)` adds it to 5a's `ROLE_TASKS`,
  so 5a's whole-plan admission prices it and `ctx.role` resolves it. Calls go
  through `ctx.caller.call` under 5a, `ctx.complete` locally.
- **F7.** B3 defaults to the serving width (`embedding.dimensions`) and the
  production recipe and prefix (`hypothesis/statement@v1`,
  `retrieval-document`, now declared on the kind as `MatchKind.recipe`). Its
  recommendation is an entry bound to what it measured:
  `blocking_cutoffs = { "<model>" = { cutoff, dims, recipe, task_prefix,
  target_recall, confirmed_matches } }`; a bare `model = cosine` no longer
  validates. B3 recommends a config line only at the serving width. The
  shortlist applies an entry only when its width (the stored vectors'),
  recipe and prefix match, else reports `cutoff_basis: refused_incompatible`
  and blocks by top-k alone.
- **F8.** `matching.shortlist.active_model`: the configured model ranks once
  its current vectors cover every subject any other stored model covers (the
  rule T7's map neighbours already use); until then the previous model with
  the most current vectors keeps ranking and the replacement's partial index
  is never used. New hypotheses the old model never embedded then link only
  by exact statement and validated citation until the backlog embeds the
  rest (it embeds every missing vector before it shortlists). The shortlist
  summary reports `model_activation`.
- **F9.** `record_escalation` first prefers one of the diagnosis's own
  repairs with a new operator. When none differs, it asks the diagnosis
  route ONCE (`recurrence_escalation_repair`, prompt `escalated-repair-v1`,
  `diagnosis/recurrence/escalation.py`) for a repair of the same cause
  through a different operator and representation, given every repair shown
  for the group's earlier answers (their suggestions and earlier escalations'
  repairs) and the current diagnosis's. The answer is used only when its
  operator is new; it is stored on the receipt (`repair_source = generated`,
  `repair_json`) and shown by the card. When the model repeats an operator,
  the request fails or is refused, or `recurrence.escalation_repair_enabled
  = false`, the card keeps the honest "same kind of repair" label and the
  receipt's `generation_json` says why. A receipt already written returns
  before any request.
- **F10.** The bench dry run classifies the writer from its configured route
  (or the injected client): a subscription writer counts calls only
  (`estimated_only`); a metered writer's input-plus-output tokens are priced
  at `--price-per-million` (unknown fails closed) and admitted together with
  the embeddings against the token and dollar caps. The estimate reports
  `metered`, `subscription` and `billing` per role. Found on the way: B1
  planned one embedding request per model, but the corpus and each query
  view are separate requests; the plan now counts them.

## Phase 5a integration (F6)

5a's harness (`slice-a/phase-5a`, harness files unchanged between
`15634fb3` and its tip `60405345`) is still not on this branch. Besides the
contract test, B1 and B3 were run through 5a's ACTUAL code in-process: a
scratch pytest plugin loaded 5a's `ops/embedding_compare.py`,
`ops/pf_calls.py`, `content/authoring/pf_contracts.py`, `pf_sandbox.py`,
`substrate/item_fingerprints.py` and `db/stores/pf.py` from git onto this
tree (with 5a's `provider_list_for_task` and `skeleton_content_hash`), called
`register_suites(compare.SUITES, role_tasks=pf_calls.ROLE_TASKS)` and ran
`run_compare` with fakes. Both suites completed: B1 with `dims=(8, 16)`
(4 writer calls through 5a's `PFCaller`, its dry run billing the writer role
`subscription`), B3 at the serving width. Nothing of 5a is committed here.

At 5a's merge, in `cli/embeddings.py`'s `embeddings_compare`, call
`register_suites(SUITES, role_tasks=ROLE_TASKS)` (from
`learnloop.diagnosis.recurrence.benchmarks`, with 5a's
`ops.embedding_compare.SUITES` and `ops.pf_calls.ROLE_TASKS`) before
`run_compare`, extend `--suite` to `b1, b3`, and retire `learnloop recurrence
bench` (or keep it as an alias). The skipped real-harness test then runs.

## Paid calls

One, to check the new escalated-repair contract against the real route
(dry run first, `--dry-run`: 409 prompt tokens estimated, caps 1 call). On
`fixtures-local/t1fix-linear_algebra`, a fresh backup-API copy
(`copy_tree_with_databases`) of this worktree's `fixtures/linear_algebra`;
the tracked vaults were not written.

| What | Route | Calls | Tokens in / out | Cost |
|---|---|---|---|---|
| Escalated repair, after three `elicit_invariant_closure_gate` repairs | Codex `codex_low` (gpt-5.6-sol) | 1 | 10,392 / 224 | subscription, `estimated_only` |

It returned `elicit_minimal_counterexample` ("concrete counterexample",
practice mode `counterexample_construction`) with an eliciting question the
learner can answer unaided, so `status: used`. No metered call was made.

## The review's "claims that don't hold"

- "The map is empty unless the successor is active" now holds: prepared
  groups are never read, and vault open applies the kill switch (F2).
- Guard coverage is for the configured judge, and a route change is repaired
  by rerunning (F3, F4).
- Judgment reuse is idempotent under concurrency through the claims (F5).
- B1/B3 integrate through the role registry as well as the suite registry,
  and ran through 5a's actual harness (F6).
- B3's cutoff describes the vectors the shortlist ranks, or is refused (F7).
- The diagnose dry run and caps cover the recurrence work, and the bench dry
  run covers the writer (F1, F10).
- The escalation test now feeds three identical repairs and checks that a
  different one is requested and shown (F9).

## Test results (gate)

Run on `e4f8aa26` (the fixes in `c5ae36a2`, the regenerated DB reference and
this file); the commit that records these numbers changes only this file.

- `uv sync --extra dev`, `uv pip install pypdfium2`: done (no mobile extra:
  this stage does not touch `learnloop_mobile`).
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7356 passed,
  1 skipped**, 0 failed, 235 s. The skip is
  `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  (`importorskip` until Phase 5a's harness is on the branch).
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **78 passed**, 7279 deselected, 64 s.
- DB reference (`_scripts/db_generate_reference.py`, then
  `db_validate_reference.py`): `errors: []` (schema head 172, 283 table
  notes, 591 effective config leaves in 34 sections); `validate_vault.py`
  passed (1,050 notes).
- Frontend: not run; no file under `apps/learnloop-tauri` changed (the card
  reads the generated repair's `rationale` like any other repair).

Test count: 7331 before (`a647b04d`) to 7357 collected now. New or rewritten
tests: `test_matching.py` (+7), `test_recurrence_commands.py` (+8, two
rewritten), `test_recurrence_live.py` (+7 with the parametrized honest-label
cases), `test_recurrence_benchmarks.py` (+4, one of them skipped until 5a merges);
the CLI help snapshot (four commands' help changed) and the defaults
fingerprints of `mvp-0.9`, `mvp-0.10` and `mvp-0.11` (the new
`recurrence.escalation_repair_enabled` leaf and the cutoff entry type) were
regenerated.

## Notes for the owner

1. **Kill-switch reach.** Consumers that hold the vault check
   `recurrence.enabled` directly; repository-only reads (the candidate
   projection, the deferral sweep) follow the stored projection, which vault
   open and every normalization re-sync. A long-running process that edits
   `learnloop.toml` without reloading would see the old groups until then
   (the sidecar reloads on vault-file changes).
2. **The escalated-repair request is on by default** (one Codex call at a
   group's K-th answer, only when the diagnosis repeats an earlier repair).
   Kill switch: `[recurrence] escalation_repair_enabled = false`.
3. **The switch check uses the route in `learnloop.toml`.**
   `LEARNLOOP_AI_PROVIDER` can override routes at run time; the guard is
   checked for the configured model, as before.
4. **Migration 172 was edited in place** (three additions). The earlier
   copies `fixtures-local/t1-linear_algebra` and `t1-probability` applied the
   old 172 and lack them: discard them and re-copy. The migration is
   renumbered at merge anyway (main takes 171 for mobile M1); the head
   fixture `migration_head_172` was regenerated from the 170 head.
5. **`blocking_cutoffs` changed shape** (an entry with provenance, not a bare
   cosine). No vault has one yet (B3 recommends one only from 30 confirmed
   matches).

---

# Second Codex review (review)

The second review read the stage at `9eaa321a` and reported ten findings:
one High, five Medium, four Low. Nine are fixed. One (F5) is rejected: the
drift it describes does not happen. Its fix's test was still added, and two
false documentation claims behind it were corrected. Each finding was
reproduced before it was fixed. Commits: `c2e99eaf` … `8e6dba5c`, the
regenerated DB reference in `8dbb7e42`, and this file.

Owner decisions applied: frictionless defaults (no new paid default; the
escalated repair is still behind its two switches), the owner-directed
shape (the shortlist + judge + `judgment_ledger` step stays one component
parameterized by kind, and F6 widens its interface for the learner-text-gaps
stage), and §3.6 as written (S1.0's planted pairs are the standing suite).

## Findings

| ID | Severity | Title | Verdict | Commit | Test (or reason) |
|---|---|---|---|---|---|
| F1 | High | A later equal-authority `same` silently overrides a recorded `different` on the same pair | fixed | `c2e99eaf` | `test_recurrence_groups.py::test_an_equal_authority_conflict_on_one_pair_refuses_the_union_and_reports_it` (3 cases), `::test_a_later_same_at_the_judges_authority_is_refused_and_logged`, `::test_highest_authority_wins_a_tie_in_the_tier_is_different_and_unsure_never_counts` (rewritten), `::test_a_higher_tier_same_still_replaces_a_lower_different`, `::test_supersession_is_how_a_judges_different_is_replaced` |
| F2 | Medium | The guard does not cover the diagnoser-citation merge path | fixed | `26c5660e` | `test_recurrence_commands.py::test_a_validated_diagnoser_citation_of_the_planted_a_answer_blocks_the_switch`, `::test_a_citation_that_did_not_validate_merges_nothing_and_is_reported`, `::test_the_switch_needs_an_m1_case_checked_in_the_live_history_mode`, `::test_the_guard_judges_the_diagnosers_own_statement_for_the_b_answer` |
| F3 | Medium | B3's cutoff, top-k and P6 evidence come from labels the shortlist selected | fixed | `1953165b` | `test_recurrence_benchmarks.py::test_b3_measures_the_shortlist_only_on_labels_the_shortlist_did_not_select`; the three older B3 tests now use owner labels |
| F4 | Medium | The generated escalated repair cannot be acted on, is not validated and is not debited | fixed | `a70b2c43` | `test_recurrence_live.py::test_a_generated_escalated_repair_is_validated_shown_like_any_repair_and_debited_once`, `::test_an_invalid_generated_repair_is_never_shown_as_a_different_approach`, `::test_the_generated_repair_aims_at_the_recurring_causes_target`; `DiagnosisCard.test.tsx` "shows a generated escalated repair whole and only once" |
| F5 | Medium | Rebuild is not equal to live: every verdict regroups all history | rejected | `8e6dba5c` (test + doc fix) | Does not reproduce. A same-version rebuild never re-runs normalization ("Replay never re-normalizes", `substrate/replay.py`). Promotions, deferral exits and escalation receipts are WORKFLOW/RECEIPT rows decided when they happened and are never re-taken. The only group-dependent derived state is the recurrence projection, which every live verdict path refreshes. `test_recurrence_live.py::test_a_verdict_after_a_promotion_moves_only_the_group_projection_and_rebuild_matches_live` passes on the pre-review tree too. The false claim came from this stage's own docs (upgrade docstring, stage notes); those are corrected. |
| F6 | Medium | The shared matcher's interface will not fit the learner-text-gaps stage | fixed (`decider` authority recorded as a gap) | `7d355b62` | `test_matching.py::test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind`, `::test_the_judge_label_is_the_executors_and_reuse_is_per_label` |
| F7 | Low | T1 work can outlast the diagnose lease; a second worker repeats the paid escalated repair | fixed | `06bf363b` | `test_recurrence_live.py::test_slow_judging_renews_the_lease_so_no_second_worker_repeats_the_paid_repair`, `::test_a_lost_lease_stops_the_t1_calls_of_the_old_worker` |
| F8 | Low | The K=3 count includes refuted and content-scoped hypotheses | fixed | `8afb2de2` | `test_recurrence_live.py::test_a_refuted_earlier_cause_does_not_count_toward_the_escalation[retired, demoted]`, `::test_a_content_scoped_cause_in_the_group_does_not_count_toward_the_escalation` |
| F9 | Low | `escalation_card_enabled = false` still pays for a repair nobody sees | fixed | `8afb2de2` | `test_recurrence_live.py::test_a_hidden_escalation_card_pays_for_no_escalated_repair`, `::test_a_hidden_escalation_card_plans_no_escalated_repair` |
| F10 | Low | Judge producer identity is the model name only | fixed | `41a1ae0b` | `test_recurrence_commands.py::test_the_judge_producer_is_model_and_effort_so_codex_tiers_never_share_a_guard_pass` |

## Reproduction (before fixing)

The new and rewritten tests were run against the pre-review tree. That tree
was `git archive 9eaa321a` in a scratch directory with the new test files
copied in, run with the worktree's interpreter. Results: 25 tests failed and
`test_matching.py` failed to collect
(`TypeError: MatchKind.__init__() got an unexpected keyword argument 'query_record_kind'`,
the F6 interface gap). Most failures were on the reviewed behaviour itself,
not on setup:

- **F1:** att_a and att_b got one group key after a judge `different` and a later diagnoser `same`, with no refusal.
- **F7:** the other worker leased the job while the escalated repair was being requested, and the old worker kept judging after it lost its lease.
- **F8:** an escalation was written for two standing recurrences.
- **F9:** `recurrence_escalation_repair` was called with the card off.
- **F4:** the generated repair had no `id` and no validation.

Some findings also had a direct check on the pre-fix code:

- **F6:** an executor declaring `judge = "verifier"` wrote rows as `('llm',)`.
- **F10:** `model_label` gave `gpt-5.6-sol` for both the Codex low and medium configs.
- **F3:** the then-current `test_b3_replays_the_vaults_labelled_pairs` passed with only the backlog judge's shortlist-nominated `llm` labels. It reported positives, `recall@10 = 1.0`, a recommended `top_k` and `label_judge = "llm"`, which is the circularity itself.

The F5 bounding test passed on the pre-review tree as well.

## What changed, per finding

- **F1.** `matching/union.py`: the effective verdict on a pair comes from its
  top authority tier, and within it a `different` beats any `same`, whatever
  their order. The tie is a `Refusal(reason="conflict")`, written as a
  `refused_union` review row with `detail.reason = conflict` (chaining
  refusals carry `reason = chaining`). A higher tier still replaces a lower
  verdict, and supersession (`supersedes_id`, dropped upstream) is the only
  same-tier replacement. A new `verdict_conflict` case kind was not added: it
  would need a CHECK change in migration 172 and a regenerated head fixture
  for the same information. The test comment claiming a learner tap "is
  logged against the diagnoser's citation" was wrong and is corrected. The
  tap is below the citation's authority, so no union is refused. It stays in
  `diagnosis_feedback`, which the M3 report counts.
- **F2.** `recurrence guard --from-run` (`read_m1_run`) now also reads each
  planted case's completed diagnoses of the B answer (`review_diagnoses` and
  `review_context_receipts`). For each one it records whether a VALIDATED
  citation named a forbidden (A) answer, as a `diagnoser` row on the planted
  pair: `same` is a false merge on the citation path. A citation that never
  validated merges nothing and is reported as `unvalidated_links`. When M1's
  planted-cause judge said a diagnosis named the target cause, the guard also
  judges a case of the authored A against the DIAGNOSER's own statement for
  B (`<case>:dx`), registered as required like the others. M1 never diagnoses
  the A answer, so that side stays authored. `guard_status` reports
  `diagnoser.false_merges` and `m1_cases_checked`. `passed` now needs no
  false merge on either path, and the new `switch_ready` also needs at least
  one M1 case checked under the current `DIAGNOSIS_PROMPT_VERSION` in the
  vault's history mode. `upgrade --to mvp-0.11` checks `switch_ready` and
  names which part is missing. Diagnoser results are keyed on the prompt
  version and history mode, not the model, so a diagnoser fix (a new prompt
  version) needs a new M1 run.
- **F3.** Every recurrence label records how its pair was nominated:
  `shortlist` (hypothesis-level `llm` verdicts, from the live and backlog
  judge), `diagnoser_citation` (citations and card taps), `m1_link` (M1's
  attempt-level verdicts) or `other`. B3 computes recall@k, the recommended
  `top_k`, the cutoff and AUC only from labels the shortlist did not choose.
  It reports the shortlist-nominated ones apart (`shortlist_nominated`, never
  used to calibrate) and gives `labels_by_nomination` in its plan. The P6
  merge replay uses owner labels only (never `llm`) and reports their
  nominations, with `p6_decidable = false` when every label sits on a
  diagnoser-linked pair (those favour `exact_plus_citations`). This deviates
  from the literal fix in one respect: labels are excluded by nomination, not
  by judge label. M1's imported link-judge verdicts (`judge = llm`,
  attempt-level) were not chosen by the shortlist, so they still calibrate it.
- **F4.** At escalation the generated repair is shaped as a repair suggestion:
  - id `escalation:<diagnosis id>`;
  - its operator, representation, practice mode, rationale, eliciting
    question, expected-response contract and reveal budget;
  - its learning object, and `target_refs` of the recurring cause (or what
    this answer's own repairs target).

  `validate_repair_candidate` runs on it as on the diagnosis's repairs. An
  `invalid` one is dropped: status `invalid_repair`, with the honest
  same-kind label. `diagnosis/recurrence/display.py` puts it FIRST in every
  display of the attempt's repairs: the feedback bundle, the diagnosis card,
  the card's and the first-open reveal debits, and eliciting responses, which
  now record `suggestion_id`. As a result the feedback screen's lead repair
  and its "one question, unaided" response box are the escalated repair's.
  It is charged to the reveal ledger once on its own basis
  (`repair_display:escalation:<diagnosis>`), even after the diagnosis's own
  repairs were charged. The overlay is display-only:
  `fetch_attempt_feedback_metadata`, which materialization and repair
  selection read, is unchanged, so showing it never versions a hypothesis.
  It follows `escalation_card_enabled`. The card shows the repair whole
  (rationale, representation and mode, the question, pointing at the box
  below it) and lists it once.
- **F5.** Rejected; see the table. `upgrade.py`'s docstring and the stage
  notes (`slice-2-t1.md`: the deviation note, the owner command "optional:
  re-apply groups to past promotions and escalations" and open question 6)
  no longer claim a rebuild re-applies merges to past decisions.
- **F6.** `MatchKind` gains an optional query-side identity
  (`query_record_kind`, `query_field`, `query_task_prefix`, `query_recipe`;
  `pool_identity()`, `query_identity()`, `symmetric`). `shortlist_pairs`
  takes `query_vectors` for a query that was embedded but never stored.
  Asymmetric kinds compare by plain cosine, because two prompt spaces have
  different means. Symmetric kinds keep Slice 1's mean-centring. The
  `judgment_ledger.judge` label belongs to the executor (`executor.judge`,
  default `llm`): writes, reuse, claims and supersession are per label.
  **Recorded gap (`decider`):** migration 166's CHECK on `judgment_ledger.judge`
  does not allow `decider`, and widening it needs a table-rebuild migration,
  which belongs to the learner-text-gaps stage. T1's group builder reads only
  the judges in its authority map, so a `decider` verdict would be ignored by
  the groups, never ranked as `llm`. Recommendation for that stage: log the
  Decider as a second opinion that does not join groups until the owner
  places it in the authority order. If it sits in the `llm` tier, the F1
  rule makes an LLM/Decider disagreement refuse the union.
- **F7.** `apply_diagnosis` takes a lease heartbeat (`_lease_heartbeat`,
  using the existing but unused `renew_post_attempt_lease`). It renews the
  diagnose job's lease for a full term before every hypothesis-embedding
  request, judge call and escalated-repair request. Once another worker holds
  the job, the old worker makes no further paid call (`LeaseLost` stops the
  judge batch and releases its claim) and writes no escalation receipt; the
  new holder does. The job outcome is now `lease_lost` instead of `done` when
  the final settle is fenced. Not done: finishing the job before the judge
  (owner question 2 below).
- **F8.** The K count reads only heads that still stand as a learner belief:
  `causal_hypotheses_with_statement` returns `candidate`/`validated`
  `learner_state` heads by default, and an answer whose blind grade has no
  completed live diagnosis in force does not count.
- **F9.** With `escalation_card_enabled = false`, no escalated repair is
  requested (`generation.status = card_disabled`), and the diagnose dry run
  plans none.
- **F10.** The producer is `model@effort` (`producer_label`, from
  `model_settings`; for example `gpt-5.6-sol@low` vs `gpt-5.6-sol@medium`),
  stored in `judgment_ledger.judge_model` for the judge's verdicts. It is used
  for reuse, claims, the guard, the backlog plan and `configured_judge_model`.
  The profile NAME is not part of it: it is a config alias, Codex clients
  report `provider_name = "codex"` for every profile, and two profiles with
  the same model and effort are the same producer. The `LEARNLOOP_AI_PROVIDER`
  caveat is unchanged (documented in round 1, note 3).

## Phase 5a integration

5a's code is unchanged since round 1's re-check (`d460f644`; its tip
`7a754b75` adds only its review file). After the F3 changes to B3, the
real-harness test ran again in a throwaway copy of this branch's tree, with
5a's `ops/embedding_compare.py`, `ops/pf_calls.py`, `pf_contracts.py`,
`pf_sandbox.py`, `item_fingerprints.py` and `db/stores/pf.py`, plus its
`skeleton_content_hash` and a single-route `provider_list_for_task` shim. It
was `1 passed` through 5a's actual `run_compare` (`HARNESS_VERSION`
`embeddings-compare-v2`, imported from the copy). The copy was deleted, and
nothing of 5a is committed. The integration point is unchanged (see
"Phase 5a integration (F6)" above).

## Paid calls

None. The fixes change no external contract (the escalated-repair schema is
unchanged). Two free, read-only dry runs went through the app on the
existing backup copy `fixtures-local/t1fix-linear_algebra`:

- `recurrence guard --dry-run`: 15 pairs to judge for `gpt-5.6-sol@low`;
  `switch_ready = false`; no M1 case.
- `recurrence bench --suite b3 --dry-run`: 2 hypotheses, no independent labels.

## The review's "claims that don't hold", now

- An equal-or-higher-authority `different` now refuses a union on the same
  pair too, and the refusal is logged (F1).
- The learner-tap test comment is corrected (F1).
- The escalated repair is shown whole and can be acted on. "Trying a
  different approach" is claimed only for a validated repair with a new
  operator (F4).
- B3's cutoff comes from recall on matches the shortlist did not select (F3).
- The guard checks the citation path and diagnoser-written statements, and
  the switch needs an M1 run (F2).

## Spec conformance (changed rows)

| Item | Status now |
|---|---|
| §3.1 authority order, equal-tier conflicts | Holds: a tie is `different` and a logged refused union |
| §3.4 no-chaining | Holds, including same-pair conflicts. Not as-of by design: past decisions are never re-taken, and a late verdict changes only the projection |
| §3.6 guard blocks the switch | Holds on both merge paths. S1.0 cases are required (`switch_ready`) |
| §3.7 escalation card | Holds: the generated repair is validated, actionable and debited |
| R4 cutoff from recall on confirmed matches | Holds: only shortlist-independent labels |
| §4 shared framework | Query/pool identity split and judge label per executor. `decider` authority is left to the gaps stage (recorded) |

## Test results (gate)

Code at `8e6dba5c`; `8dbb7e42` regenerates only the DB reference. The commit
that records these numbers changes only this file.

- `uv sync --extra dev --extra mobile`: refused on this branch
  (`Extra 'mobile' is not defined`; mobile M1 is not on this branch's base).
  Ran `uv sync --extra dev` and `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7381 passed,
  1 skipped**, 0 failed, 247 s. The skip is
  `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  (`importorskip`; it ran in the 5a copy above).
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`: **78
  passed**, 7304 deselected, 72 s.
- Frontend (`apps/learnloop-tauri`, which changed): `npm install` done,
  `npm run typecheck` clean, `npm test` **77 passed** (18 files). The new card
  test fails against the pre-fix component.
- DB reference: there is no schema or config change, but
  `db_validate_reference.py` reported 16 stale source-line citations after the
  edits. `db_generate_reference.py` was rerun (`8dbb7e42`), and validate then
  gave `errors: []` (283 table notes).

Test count: 7357 collected after round 1, 7382 now.

## Notes for the owner

1. **Rerun the guard on any copy.** The judge producer is now `model@effort`
   (F10), so verdicts stored under the bare model name no longer count. The
   round-1 copy's dry run asks all 15 pairs again (Codex, subscription).
2. **The switch now needs an M1 run.** Run
   `learnloop recurrence guard --from-run <M1 run dir>` (`--dry-run` first).
   The run needs planted `same_answer_different_cause` cases diagnosed in the
   vault's history mode (`full`) under `diagnosis-v1-split`. This is stricter
   than before and follows §3.6. If no existing M1 run has such cases, a new
   (paid) Slice 1 M1 run is needed before `mvp-0.11`. A diagnoser prompt
   change makes earlier runs stop counting.
3. **The card still waits for T1** (judge calls and the escalated repair run
   inside the leased job, so E7 latency includes them). Finishing the job
   before the judge would move T1 work outside the lease and change the
   K=3/promotion ordering. Left as an open question.
4. **Escalated repairs lead the feedback screen.** When one was written, its
   question is the "one question, unaided" box, and the diagnosis's own
   repairs follow. An eliciting response records `suggestion_id`.
5. **Decider authority** is for the learner-text-gaps stage (F6, above).

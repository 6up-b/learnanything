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

Pending: filled in by the gate run on the commit that adds this file.

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

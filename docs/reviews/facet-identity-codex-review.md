# Facet identity: Codex review fixes

Branch `facets/identity`, worktree `learnanything-facet-identity`. The review
covered `7b44c9b0..ea3cb42a` (stage file: `docs/reviews/facet-identity.md`).
Every finding was reproduced first: as a failing test where it was testable,
and, for F1, F3 and F5, also on a backup-API copy of `linear_algebra`. All 11
are fixed and none were rejected. The fixes start at `86c070f6`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Merging two facets that share a criterion or recipe cuts that criterion's evidence | fixed | `86c070f6` | `test_facet_identity_actions.py::test_a_merge_of_two_facets_one_criterion_targets_counts_like_one_target[4,0]` (merged item's recall row equals a single-target item's; before: alpha 1.625 / mass 0.5, and no row on a wrong answer); `::test_a_recipe_naming_both_merged_facets_keeps_one_component`; `::test_authored_duplicate_targets_without_an_alias_load_unchanged`. Live: the 4 `linear_algebra` items (5 criteria) that target both "vector space" and "vector addition must be commutative…" load with one target per cell after the merge |
| F2 | High | Locked facets merged by default, against the knowledge model's single lock policy | fixed | `b1a3fa62` | `test_facet_identity_actions.py::test_the_default_lock_policy_refuses_and_the_owner_override_labels_the_lock`, `::test_dedupe_proposes_a_locked_set_and_applies_it_only_under_the_override`; `test_facet_identity_ingest.py::test_an_absorbed_precondition_never_grows_a_registered_facet`, `::test_an_absorb_into_a_locked_facet_adds_only_the_alias`, `::test_the_alias_only_append_gate_refuses_a_precondition_growth` |
| F3 | High | Undo writes no owner verdict, and the next dedupe re-merges what the owner undid | fixed | `ef37459d` | `test_facet_identity.py::test_an_undone_merge_is_an_owner_verdict_and_dedupe_never_reapplies_it`, `::test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again`; the reviewer's `test_fi_repro.py` now passes (3 owner rows, undone pair stays apart). Live: after an undo, a second dedupe pass grouped the set again and the owner verdicts kept it apart |
| F4 | Medium | Merge and undo are not crash-safe; undo erases merge history from exports | fixed | `83d3a2c5` | `test_facet_identity_actions.py::test_an_interrupted_merge_is_finished_by_recovery[_write_facets,refresh_derived_state]`, `::test_an_interrupted_undo_is_finished_by_a_retry[_write_facets,_delete_merge_rows,refresh_derived_state]`, `::test_doctor_reports_an_interrupted_merge_and_fix_state_finishes_it`, `::test_a_merge_intent_whose_file_changed_meanwhile_is_withdrawn`, `::test_dataset_exports_keep_the_merge_history_an_undo_removes_from_facet_merges` |
| F5 | Medium | Ingest judge spend missing from every dry run; the dedupe dry run migrates the database | fixed | `bbc84637` (read-only attach in `83d3a2c5`) | `test_facet_identity_ingest.py::test_the_synthesize_dry_run_plans_the_ingest_judge`, `::test_the_append_dry_run_plans_the_ingest_judge`, `::test_the_dedupe_dry_run_never_migrates_the_database`. Live: the dry run left the copy's database at schema 155 |
| F6 | Medium | The desktop panel can show the wrong undo state | fixed | `125a83cc` | `FacetIdentityPanel.test.tsx`: "re-reads the run's actions when it mounts…", "offers the undo once a merge's proposal has been applied…", "names why a facet is locked…", "marks an interrupted merge…"; `test_facet_identity_ingest.py::test_the_run_summary_names_its_run_and_each_action_its_lock_and_undo_limits` |
| F7 | Medium | Two actions on one in-run survivor undo each other's content | fixed | `1b98e4f9` | `test_facet_identity_ingest.py::test_two_sets_on_one_in_run_survivor_are_one_action_that_undoes_both` (before: two actions) |
| F8 | Low | The ledger records repaired verdicts as the judge's; the Decider re-pays on reruns | fixed | `a605d812` | `test_facet_identity.py::test_the_ledger_keeps_the_judges_verdict_and_marks_repaired_and_omitted_pairs`, `::test_a_rerun_of_the_decider_reuses_its_answers_and_ledger_rows`; the Decider ledger test now runs (simulated R0 ledger) instead of skipping |
| F9 | Low | Undo is not exact for evidence written during the merge window | fixed (documented) | `125a83cc` | Reported honestly rather than re-keyed: the undo result (`not_restored`), every action view (`undo_limits`), the CLI and sidecar docstrings, `actions.py` and the panel copy say that rows graded while the merge stood stay with the survivor. Tests: the run-summary test above and the panel's lock-label test |
| F10 | Low | Revalidation applies a stored plan with the switch off | fixed | `56056da4` | `test_facet_identity_ingest.py::test_revalidation_with_the_switch_off_replays_no_stored_plan`, `::test_the_gate_knows_aliases_only_while_facet_identity_is_on` |
| F11 | Low | Splitting a large neighbourhood can be very slow | fixed | `dddf133f` | `test_facet_identity.py::test_the_heap_split_matches_the_reference_average_link[4 seeds]` (identical to the original algorithm), `::test_a_neighbourhood_of_hundreds_of_facets_splits_in_seconds` (600 facets: 0.77 s; the original took 0.05 s at 80 facets and 0.40 s at 160) |

Also: `df65cf85` regenerates the DB and config references, and `8da459ca`
marks the claims in `facet-identity.md` that these fixes changed.

## What changed, by finding

**F1.** The loader collapses duplicates that alias resolution creates. A
criterion's targets keep one entry per canonical (facet, capability), with
the stronger role (`primary` over `supporting`). A recipe's `all_of` and
`any_of` keep one component per cell, with the stronger modality. Duplicates
written without an alias load as written, so a vault with no alias
references loads exactly as before. After a merge, an item that targeted
both facets counts like one written against the survivor alone. Projection
code is unchanged, so no algorithm successor is needed: the merge is the
vault-content change the handoff expects.

**F2.** `merge_locked_facets` now defaults to `false`, the knowledge model's
single lock policy (§3.4, §12.1). Dedupe lists each judged set that touches a
locked facet under `locked_proposals`: the survivor, the retirees, the lock
reasons and the judge's rationale. Nothing in such a set is applied. A
rerun under the owner's override applies these sets from the reused verdict,
with no new call. Attach runs `can_apply` on each registered target. An
alias is a sanctioned rename on any facet. An absorb grows only the worked
examples of an unlocked facet. It never adds a precondition (a contract
change). Either case falls back to adding only the alias, and the action's
`contract_note` says why. The alias-only append gate accepts example growth
only.

**F3.** An undo appends `judge='owner'`, `verdict='different'` rows for every
pair in the undone set, in the same transaction as the undo intent:

- each judge row that merged a pair is superseded on its own question
  (`supersedes_id`);
- each pair gets a facet-keyed row (`facet`/`facet`), unless the superseding
  row is already keyed that way.

Both judges then apply the owner's current verdicts after validation. A later
dedupe, a resynthesis or an append attach keeps such a pair apart, and the
group's notes say so. The ledger still keeps the judge's own verdict. A
candidate whose content matches a registered facet's is bound by that
facet's owner verdicts too.

**F4.** A vault merge now runs in four steps:

1. In one transaction, it inserts the action row (`applying`) and its
   `facet_merges` rows.
2. It replaces `facets.yaml` through a staged, fsynced temp file and an
   atomic rename (the same writer as proposal apply).
3. It refreshes the derived state.
4. It marks the action `applied`.

An undo records `undoing` (with the F3 owner rows) before it restores the
file. `recover_interrupted_actions` finishes either operation from whichever
side of the file write it stopped on. An `applying` row whose file changed
in the meantime is withdrawn (`abandoned`, its rows removed). Merge, undo,
dedupe and `doctor --fix-state` run the recovery; a plain `doctor` only
reports it. A retried undo now returns the finished result instead of
refusing.

Migration 172's status CHECK gains `applying`, `undoing` and `abandoned`.
The head fixture was re-upgraded from the base `migration_head_171` database
(backup API, `journal_mode=DELETE`, integrity ok, foreign keys clean).
Dataset exports now capture `facet_identity_actions`, so the merge history
that an undo removes from `facet_merges` survives.

**F5.** `learnloop synthesize --dry-run` (bootstrap and append) now carries a
`facet_identity` block and prints it: route, billing, cost basis, the
per-run caps and "up to N calls". The unused `dry_run_estimate` is gone. The
dedupe dry run reads the database through `Repository.attach(read_only=True)`
and migrates nothing.

**F6.** On mount and after each undo, the panel re-reads the run's actions
through `list_facet_identity_actions(runId)`; the run summary now carries
`run_id`. The lock label now names the actual source: practice history,
independent evidence, a goal's certified scope, probes or a misconception.
Interrupted and abandoned actions are labelled.

**F7.** Actions are keyed by (scope, survivor). One action restores the
survivor and re-mints every retiree, and it records each member's action and
group when they differ.

**F8.** Each ledger row carries the judge's own verdict, taken from its raw
partition (for the Decider, its per-pair answer). The rationale records:

- the raw set membership;
- whether the pair was listed or omitted (an unlisted label is kept distinct
  by the prompt's rule);
- whether it was applied;
- a `repaired` reason when the verdict and the applied result differ.

The Decider checkpoints each judged group and reuses its ledger rows, so a
rerun pays nothing and appends nothing.

**F9.** Documented, not re-keyed. Re-keying grading-time rows on undo would
mean rewriting raw ledgers, and storing the on-disk id at write time would
change what grading records. The undo result and the UI now say what does
not move back.

**F10.** Revalidation replays a stored plan only while the switch is on. The
gate's alias-aware known-facet set is also used only then.

**F11.** Average-link clustering is now heap-based, O(n² log n). The size
cap holds, and tie-breaking matches the original exactly.

## Claims in the stage file, revisited

- **"No algorithm successor… nothing scored, scheduled or projected changes
  meaning."** As built, this was false (F1). It now holds in the sense the
  handoff intends: a merge is a vault-content change resolved by aliases and
  `facet_merges`, and a merged item counts exactly like one written against
  the survivor. Projection code is unchanged.
- **"Undo restores … their evidence exactly."** This holds for evidence
  resolved at projection time. Grading-time rows stay with the survivor
  (F9), and every surface now says so. Undo is now the owner's verdict, and
  it sticks (F3).
- **"`--dry-run`: no client, zero calls, no change."** This holds now (F5,
  read-only attach).
- **"Kill switch restores today's behaviour exactly."** Off now means:
  - no judge and no new merges;
  - the old prompts;
  - stored plans are not replayed (F10);
  - today's gate (F10).

  Load-time alias resolution stays on by design, because merges already in a
  vault must keep resolving. It changes nothing for a vault without alias
  references.
- **"A rerun reuses the verdict and its ledger rows and pays nothing."** This
  holds for both judges now (F8).
- **"`dry_run_estimate` plans ingest calls."** The function is replaced by
  `ingest_dry_run`, which the synthesize dry run calls (F5).

## Spec conformance after the fixes

| Item | Status |
|---|---|
| 3 Ledger `same_facet`, spend caps, Codex `estimated_only` | Built. An undo appends owner verdicts (F3). The ingest judge appears in every dry run (F5). Rows record the judge's own verdict (F8) |
| 4 Live apply + one-tap undo | Built and crash-safe (F4). One action per survivor (F7). The desktop shows live state (F6). Undo exactness is limited to projection-time evidence and says so (F9) |
| 4 Kill switch `facet_identity.enabled` | Stored plans and the gate follow the switch (F10). Load-time alias resolution stays on |
| 4 Playbook if projections change | Projection code is unchanged. Merged items now count like single-target items (F1) |
| Lock policy (knowledge model §3.4) | Kept by default. Locked sets are proposals; the owner's override is `merge_locked_facets = true` (F2) |
| 6 `facets dedupe [--dry-run]` | The dry run changes nothing (F5) |
| Migration, table role, head fixture | 172 (WORKFLOW, now with in-flight states), captured in exports |

## Live check (backup-API copy `fixtures-local/fi-review-la` of the worktree's `fixtures/linear_algebra`)

The Codex judge is out until 2026-10-18 13:00 (usage limit, recorded in the
stage file), so the copy routes `facet_identity_judge = "openrouter_haiku"`.
The dry run ran first; every run was inside the caps (`--max-calls 3
--max-cost-usd 0.05`).

1. **Dry run:** 1 group of 39 facets, 741 pairs, 1 call, estimated $0.0045,
   20 facets locked, policy `refuse_locked`. The database stayed at schema
   155 (F5).
2. **Dedupe, default policy:** 1 call. The judge found 5 sets. All 5 touch
   locked facets (each one through the `probe` arm, three also through
   independent surface groups), so all 5 were listed as `locked_proposals`
   and **none were applied**. The sets:
   - coordinatewise addition;
   - the addition definition;
   - the vector-space definition with its 3 restatements, including the
     axiom subset;
   - the zero vector and the overloaded 0;
   - complex arithmetic, absorbed into scalar arithmetic.
3. **Dedupe with `merge_locked_facets = true`:** 0 calls (the judged group
   was reused) and $0. All 5 sets applied. The 5 criteria on 4 items that
   targeted both the vector-space and commutativity facets now load with one
   target per cell (F1).
4. **Undo the vector-space set, then dedupe again:** the undo restored 3
   facets and wrote 6 owner rows. The second pass made 1 call. The judge put
   the vector-space set together again, and the owner verdicts kept it apart
   (3 notes). The second pass also applied 2 new sets on the consolidated
   facets.

| Route | Calls | Tokens (reported) | Cost |
|---|---|---|---|
| OpenRouter `anthropic/claude-haiku-5.5` | 2 | 21,122 input, 7,495 output | **$0.0059** (OpenRouter-reported: $0.0029591 + $0.0029006) |

## Gate

Run on `8da459ca`, a clean tree. The commit after it adds only this file.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **12 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,705 passed, 0 skipped**, 46 warnings (the existing mobile-host, fork and sqlite datetime deprecations), 224 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **83 passed**, 7,622 deselected, 1 warning, 64 s |
| Frontend (`npm install`, `npm run typecheck`, `npm test`) | typecheck clean; **22 files, 101 tests passed** (4 new panel tests) |
| DB/config references (`db_generate_reference.py`, `db_validate_reference.py`; `validate_vault.py`) | 285 table notes, **0 errors**; docs-vault validation passed (1,053 notes) |

The stage gate had 7,672 passed and 1 skipped. Since then:

- the Decider ledger test runs (on a simulated R0 ledger) instead of
  skipping;
- this fix step adds 32 Python tests.

`cargo check` was not run because no Rust changed.

One process slip: a shell glob that matched nothing turned a targeted run
into a full run, which took 7 minutes outside the shared lock (7,699 passed,
at `56056da4`). It was not a gate run.

## Merge notes

- **Migration numbering.** Main is at 174: Phase 6 took 172/173 and Phase 5a
  took 174 (`pf_generation`). Router R0 has not merged. Renumber this
  stage's `172_facet_identity_actions.sql` to 175, or 176 if R0 takes 175.
  Then rename `fixtures/migration_head_172` and update its README, the five
  test/script paths and both `SCHEMA_HEAD` constants, and regenerate the
  references. The migration's SQL changed in this fix step (status CHECK),
  so re-upgrade the head fixture from main's head fixture rather than
  copying this one.
- **Router R0.** This stage needs no new `judgment_ledger` judge or task
  values beyond `decider`: owner rows use `judge='owner'` (already accepted)
  and task `same_facet`. `tests/test_facet_identity.py::_accept_decider`
  simulates R0's CHECK rebuild in a test database and does nothing once the
  real CHECK accepts `'decider'`. R0's rebuild must keep the append-only
  triggers, because owner supersession relies on the
  `judgment_ledger_validate_insert` same-question check. R0's
  `route_profile_mismatch` must accept a decider profile on
  `facet_identity_judge`.
- **Slice 2 T1** (`slice-2/t1`, not merged). The reuse points are unchanged:
  `grouping.centred_unit` becomes `matching.shortlist.centred_unit`, and
  `judge.partition_from_pairs` becomes `matching.union.union_with_refusals`.
  The new `judge.owner_vetoes` / `apply_owner_vetoes` (the owner's current
  verdicts) are the facet analogue of any owner-verdict lookup T1 adds to
  its ledger.
- **Defaults fingerprints.** Recomputed for `merge_locked_facets = false`.
  Recompute again after the merges that add config.

## Open questions for the owner

1. **Locked facets (stage question 1, now sharper).** Under the default
   strict policy, dedupe on `linear_algebra` applies nothing: the `probe`
   lock arm covers every facet the judge wants to merge. Keep the default
   until restructure-with-history exists, or set `merge_locked_facets =
   true` (option c on locked facets too, each merge with its undo)?
2. **Grading-time rows after an undo (F9).** They stay with the survivor and
   the UI says so. Should a future step store the on-disk facet id at grading
   time so that an undo moves them too?

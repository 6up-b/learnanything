# Slice A integration 2-3: Codex review fixes

**Branch:** `integrate/slice-a-2-3` (worktree `learnanything-integrate-2-3`), on top of
`3418d405`. Not rebased, not merged, not pushed.

**Review:** Codex job `20261012-004541-8kgyMB` over `94cf6bd6..integrate/slice-a-2-3`:
ten findings (1 High, 8 Medium, 1 Low), including the owner-directed Codex change for
the two Phase 2 paid routes.

**Result:** all ten are fixed. Each one was reproduced first: at least one new or changed
test per finding fails on the code before the fix. The rest are guards that also pass
before it. For F8 the kill switch was added; the algorithm
successor the finding also asked for was not, for the reason given below. The gate
passes; the numbers are under Gate results.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Family application can overwrite concurrent learner edits | Fixed | `f0612d25` | `test_activity_families.py`: `test_learner_edit_during_family_publication_is_not_lost`, `test_retire_from_a_stale_snapshot_keeps_family_membership`, `test_vault_mutation_lock_is_reentrant_per_thread_only` |
| F2 | Medium | Reader adoption can retire another commitment's card | Fixed | `0ccc2459` | `test_reader_adoption_ownership.py` (4 tests) |
| F3 | Medium | Both owner-directed field routes still reject Codex (OWNER-DIRECTED) | Fixed | `57730bec` | `test_field_llm_cli.py` (7 new) and `test_interaction_signals.py` (6 new) |
| F4 | Medium | Logged tutor classifications are discarded with no recovery path | Fixed | `c3c6f155` | `test_field_signal_production_paths.py`: the three mapping and classification tests |
| F5 | Medium | Ordinary practice questions never receive the early-help adjustment | Fixed | `2d6e3290` | `test_field_signal_production_paths.py`: the three ask-before-submit and window tests |
| F6 | Medium | Report 2 allows fast-tracking after reader confusion | Fixed | `363922ac` | `test_eval_harness.py::test_report2_shares_the_confusion_blocking_predicate` (5 cases) |
| F7 | Medium | Family rebuild and evaluation disagree about leaked attempts | Fixed | `b075f515` | `test_family_memory_projection.py::test_rebuild_and_evaluation_fold_the_same_leak_aware_rows` |
| F8 | Medium | Automatic reader adoption changes serving without a successor or kill switch | Fixed: kill switch and versioned provenance. No successor (reason below) | `5beeb041` | `test_daily_loop_reference_adoption.py::test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards` |
| F9 | Medium | Some returned family verdicts never reach judgment_ledger | Fixed | `5b79d306` | `test_family_proposals.py`: `test_unusable_returned_verdict_is_ledgered_and_never_groups`, `test_unusable_verdict_without_retry_budget_is_ledgered_and_reasked` |
| F10 | Low | The family contract rejects the specified ensemble source kind | Fixed | `8d78676f` | `test_activity_families.py::test_ensemble_source_kind_loads_and_round_trips` |

`74d94e04` regenerates the DB and config references for the final tree.

## What changed, per finding

### F1: practice-item writes share the family lock (High)

- **Reproduced.**
  - A family apply was paused inside its first `_write_atomic`, after the item patch had been computed. A concurrent `edit_item` returned at once, and the family then wrote the stale file over the learner's prompt.
  - In the other direction, `retire_item` with a sidecar snapshot taken before a family apply wrote `family_id: null` back. The vault then no longer agreed with the ledger.
- **Fix.**
  - `upsert_practice_item` reads, merges, validates and writes inside `vault_mutation_lock`. That is the lock family apply and undo already hold.
  - `edit_item` and `retire_item` hold the lock across their read and their write.
  - A retire that starts from a caller's snapshot re-reads the item from disk under the lock (`vault.writer.current_practice_item`). Stale fields are never written back.
- **Re-entrancy.** `vault_mutation_lock` is now re-entrant within one thread, keyed by pid and lock file.
  - Holders that publish through the writer (proposal accept, doctor apply-intent recovery) nest instead of timing out against themselves.
  - Other threads, other processes and forked children are still excluded.
  - An owner check (`guard_vault_mutations`) still runs on nested entry.
  - Two existing lock tests had used a nested acquire in the same thread to stand in for "another writer". They now hold the lock from a second thread.
- **Behaviour to know.** A sidecar edit that arrives while a family operation holds the lock waits for it. If the wait exceeds the default 10 s, the edit fails with `VaultLockTimeout`.

### F2: a reader question's card is its own

- **Reproduced.**
  - Two identical reader questions shared one card.
  - A card the learner had written independently with the same words was captured.
  - Retiring one question retired practice the other commitment still requested.
- **Fix.**
  - The card a reader question adopts gets an id derived from its commitment (`reader_practice_item_id`). `author_item` now takes an explicit `item_id`.
  - Crash recovery finds the card by that id and links it. Nothing else is reused.
- **Defence in depth.** `_retire_adopted_items` skips a card that the head of another unretired commitment still targets.

### F3: Codex on `field classify-questions` and `eval --prepare-llm` (owner-directed)

This follows `811866e4` (families propose) and Slice A plan §5 rule 6.

- **Admission.** Both CLI adapters accept a Codex profile (`codex_sdk` or the legacy `http`). Other non-metered types are still refused.
- **Subscription mode.** Both workers take `subscription=True`:
  - `SpendBudget` admits an unknown price and does not enforce the token or dollar caps;
  - the one-physical-request guard is lifted;
  - the candidate and call caps still apply.
- **Receipts.**
  - Root receipts declare the caps in force with `billing=subscription`, `cost_basis=estimated_only` and `physical_request_bound=false`.
  - Every finished receipt's `usage_json` carries the estimate: reported token usage, else the planned input-plus-output estimate.
  - A dollar figure appears only with `--price-per-million`.
  - The shared helper is `ai.spend.subscription_usage_estimate`. Families propose now uses it too.
- **Reports.** Both commands report `billing`, `cost_basis`, `physical_request_bound` and `caps_in_force`.
- **Billing check.** A lazily resolved client whose billing differs from the configured route is refused before any request.
- **Metered routes.** They are unchanged, with the full cap set and the physical-request bound.
- **Tests.** The four kinds families propose has, for both routes:
  1. A Codex dry run with no price and no client. It goes through the API, through the `field classify-questions` CLI, and through `learnloop eval --section field --prepare-llm --dry-run`.
  2. A fake Codex run under a 1-token and $0 cap, with two physical SDK turns in one operation, whose receipts carry `estimated_only` with `reported_usage`. A second run checks the planned-token fallback.
  3. The call cap stopping a Codex run.
  4. A metered regression: the hidden second request is blocked, an unknown price is refused, and the token cap holds.

  A billing-mismatch refusal test was also added. The help text for `--price-per-million` changed, so the CLI help snapshot was regenerated.

### F4: logged tutor facets reach an LO

- **Reproduced through the production writer and loader.** A feedback-screen `mechanism` question after a correct answer has a logged type and facets. It produced only a zero-mass row, and `classify-questions` skipped it.
- **Fix.**
  - `tutor_qa` persists `source_context.facet_learning_object_ids` with the answer. This is each logged facet's owning LOs at question time: blueprint facets and active items' facets.
    - A `prerequisite` question never targets its own item's LO, because it points below the item. When the only owner is that LO, the mapping is left unresolved.
  - The signal loader resolves logged facets through this immutable per-event mapping. Today's membership is still never used.
  - `classify-questions` treats a logged type with no resolvable LO as missing metadata. It keeps the logged type and facets and supplies only the LO, which becomes available at the classification time.
- **Effect on spend.** Historical typed tutor questions without an LO now show up as pending in the classifier's dry run. That is the recovery path, and it remains opt-in and capped.

### F5: practice-screen questions link to the attempt they preceded

- **Reproduced.** A question asked through `tutor_qa.ask_question` from the practice screen at second zero, followed by a correct one-hint attempt, got the ordinary 0.8 cap.
- **Fix.** `load_interaction_signals` links a practice-context question with no `attempt_id` to the next attempt on its item in its session. This is the window submission already uses to count it as a hint equivalent (`tutor_qa.hint_equivalents_for_submission`). Explicit links and other contexts stay as logged.
- **Tests.**
  - Ask-before-submit gets the 0.3 early-help cap.
  - A mid-attempt question is linked but is not early help.
  - An attempt on the item in another session closes the window.

### F6: one fast-track blocking rule

`signals.blocks_fast_track` is the union of the two lists that had drifted apart. The harness had no `reader_confusion` or `hint`; the helper had no `strategy`. Report 2 and `confusion_blocks_fast_track` both call it. The test checks every blocking kind against both, with a predictor that crosses the threshold, and checks that curiosity still does not block.

### F7: the projection folds the evaluated rows

- **One loader.** `field.outcomes.load_effective_replay_rows` is the one place interaction signals are folded into replay rows. These include linked leak telemetry and help before work.
- **Its readers.** The eval and families harness, the `family_memory` replayer and `field data-check`'s memory counts all read it.
- **Version.** The projection version is now `family-memory-cold-v4`.
- **Test.** The regression compares the evaluation's memory-training rows with the rebuilt `review_count` for question-only leak telemetry with no reveal row: 2 against 2. Before the fix it was 2 against 3.

### F8: adoption kill switch

- **Fix.**
  - `tutor_qa.adopt_reference_questions` defaults to `true` and appears in the template. It gates `adopt_reference_questions` itself.
  - Off restores the previous behaviour: references stay references, and Today's queue equals the baseline.
  - Cards adopted earlier are authored content and are never removed.
  - Cards the sweep adopts record `mechanism=reader_reference_adoption_v1` in their provenance event; write-time adoption keeps `reader_author_qa`. The change is therefore versioned and auditable.
- **Defaults.** The `mvp-0.9` effective-defaults fingerprint was recomputed for the new leaf and recorded in `DEFAULTS_SNAPSHOT_BY_ALGORITHM`. The new value is `a1b6b127…e30f`. The reference counts are now 529 leaves.
- **Why no algorithm successor.** The playbook's step 1 covers changes to *persisted meaning*: scoring, scheduling, projection or admissibility semantics. The sweep does none of these.
  - It writes authored practice items and raw commitment-target events.
  - Replay and rebuild of the same vault are unchanged, so there is no projection delta for a shadow rebuild to inspect.
  - The owner's standing decision is "live changes behind kill switches, no shadow stages by default". The kill switch is what makes the change reversible.
  - The owner can still ask for a successor at the checkpoint (open question 2).

### F9: unusable family verdicts are ledgered

A schema-valid `same` with an empty idea statement or retrieval target, or with a null relation, used to be retried before `append_judgment`.

- **Fix.** Such a verdict is now appended first:
  - with `verdict=unusable`;
  - under a fresh id;
  - with the reason, the pass's checkpoint id, the run and the attempt.
- **The checkpoint stays open.** The `pfj_` checkpoint id is left free. The pass is retried in this run, where each retry still spends a retry cap, or it is asked again in a later run.
- **No influence on grouping.** An unusable row is never a cache hit, a grouping vote or acceptance evidence.
- **Reporting.** The report counts `unusable_verdicts`.

### F10: `ensemble` source kind

`ActivityFamily.source_kind` accepts `ensemble` (spec §5.1). Such a family loads and writes without issues.

## Claims in the review

| Claim | Now |
|---|---|
| "Unrelated owner edits are retained" | Holds under concurrent sidecar writes (F1) |
| "Other commitments' targets are left alone" | Holds: per-commitment cards and the retirement guard (F2) |
| "All F1 portions of field §9 are covered" | Production mapping, pre-submission linkage and reader-confusion gating are now tested through the production paths (F4–F6) |
| Family projection and evaluation use the same effective rows | Holds: one loader (F7) |
| The adoption follow-up needs no successor | It now has a kill switch and versioned provenance. The successor question is answered above and left to the owner (F8) |
| Every returned family verdict is retained in the ledger | Holds (F9) |

## Integration choices (Unresolved item 4 of `slice-a-integration-2-3.md`)

- **Memory arms in the default `--section field` arm set.** Kept. Spec §7.2 says "every arm". The review found it conforms. Memory arms are never recommended, and G11 rejects them as active predictors.
- **Phase 3's regrade exclusion and full-mass `dont_know` dropped in favour of Phase 2 and spec §3.** Kept. The review called this a defensible resolution and noted that the spec's §4 wording conflicts. That wording is spec text the owner owns, so it was not edited here (open question 1).
- **Attempts without `grading_evidence` give no outcome row.** Kept. The review found it conforms, and `data-check` counts these attempts.

## Gate results

These checks ran on the final code tree (`74d94e04`). This record is the only commit after it.

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK. `uv sync` removes `pypdfium2`, so it was installed again |
| `uv run lint-imports --no-cache` | **8 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6,713 passed**, 0 failed, 14 warnings (the existing Python 3.12 fork and SQLite datetime-adapter warnings); 224 s. That is the 6,677 before plus the 36 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **64 passed**, 6,649 deselected; 28 s |
| `db_generate_reference.py` / `db_validate_reference.py` | Schema **168**, 266 table notes, **529** config leaves in 30 sections, **0 errors**. Run again after the reference commit: 0 errors |
| `validate_vault.py` (extra) | Passed: 1,028 notes |
| Frontend (`npm install`, `typecheck`, `test`) | Not run: no file under `apps/` changed |
| Migrations and fixtures | Unchanged: no migration and no new table. The tracked working vaults are untouched |
| Targeted runs during the fixes | Each finding's suites, the tutor, reader, proposal and authoring suites, and the lock and ingest-ownership suites |

## Open questions for the owner

1. **Spec §3 against §4 on `dont_know` mass.** The integration follows §3 (the configured effective mass), and §4's wording still conflicts with it. Reconcile the spec text.
2. **F8 successor.** The adoption sweep is behind a kill switch, with versioned provenance, and has no algorithm successor (reason above). Say if you want a successor anyway.
3. **F4 prerequisite targets.** A prerequisite question's question-time mapping excludes its own item's LO. When no other LO owns the facet, the opt-in classifier supplies the prerequisite LO. Confirm this reading of "a prerequisite question points below the item".
4. **"Help before work" is logged as an exact zero.** The practice screen (`AskOverlay.tsx`) logs fractional seconds since the item opened, so `seconds_into_attempt == 0` almost never holds. After F5 the linkage is correct, but the early-help cap only fires when the logged time is exactly zero.
   - This was Phase 2's deliberate rule: missing or late timing is not evidence.
   - A defensible alternative signal is a "no draft yet" marker, such as `attempt_progress`, or a small threshold.
   - This is a product decision and was not changed here.

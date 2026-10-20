# Daily loop DL2 (intent): Codex review and fixes

**Branch:** `daily-loop/dl2` (worktree `learnanything-dl2`), reviewed at `bbb0b05d3`
(base `fab576ac1`). **Codex job:** `20261020-000102-fgOsoH` ("not ready to land, 10
findings": 3 High, 7 Medium). Codex changed no files and made no live calls.

Fix step: every finding was reproduced first by a failing test in
`tests/test_intent_codex_review.py`. The test file was run against `bbb0b05d3`'s
`src/` and `migrations/` (from `git archive`, with `-o pythonpath=` pointing at them),
and every test for a fixed finding failed there for the reason the finding gives (the
reasons are listed below). The F2 pin and the positive F7 cases (`learn`, `master`)
passed there, as they should. No paid or live model calls ($0.00). No migration (217
still unused). No change under `src-tauri`.

## Findings

| ID | Sev | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Intent exclusion is bypassed by follow-ups and existing plan blocks | **fixed** | `1d5ba0272` | `test_f1_a_pending_follow_up_never_resurrects_a_paused_item`, `test_f1_a_follow_up_never_serves_an_item_a_check_once_still_holds`, `test_f1_pausing_after_the_plan_was_built_keeps_its_items_unserved`, `test_f1_a_check_once_chosen_after_the_plan_holds_its_planned_item` |
| F2 | High | The required intent successor is missing | **rejected** (owner's standing ruling; see below) | — | `test_f2_with_intent_off_commitments_change_nothing_in_the_ranked_list_or_the_plan` pins the predecessor with commitments populated |
| F3 | High | "Check once" bypasses cold-measurement eligibility | **fixed** | `1d5ba0272` | `test_f3_a_check_whose_answer_the_tutor_revealed_is_not_served_as_a_check_on_your_own`, `test_f3_a_hinted_attempt_does_not_use_up_the_check`, `test_f3_an_lo_check_prefers_a_candidate_that_can_be_taken_cold`, `test_f3_a_routine_display_makes_the_check_wait_until_it_is_cold_again`, `test_f3_an_exposure_after_planning_is_read_at_the_serve`, `test_f3_an_lo_check_planned_item_exposed_after_planning_is_displaced`; vitest `PracticeScreen.intentCheck` (the practice-labelled view) |
| F4 | Medium | Held grades become FSRS anchors | **fixed** | `1d5ba0272` | `test_f4_a_held_grade_never_becomes_the_anchor_through_the_real_attempt_path` (through `apply_attempt`, held as the live door holds it) |
| F5 | Medium | Primed retries inflate cost previews and suppress admission | **fixed** | `1d5ba0272` | `test_f5_a_primed_retry_changes_neither_the_cost_preview_nor_the_review_load` |
| F6 | Medium | Re-entry's intent order is undone by the chooser | **fixed** | `1d5ba0272` | `test_f6_the_chooser_takes_the_master_block_first_in_re_entry` (through `LegacyLanesSource` and `LaneQuotaChooser`) |
| F7 | Medium | Paused and maintenance-only sources still generate reading blocks | **fixed** | `1d5ba0272` | `test_f7_a_source_reads_only_under_learn_or_master` (7 choices), `test_f7_a_pause_after_the_plan_drops_its_pending_reading` |
| F8 | Medium | A deadline silently expands to other LOs sharing the concept | **fixed** | `1d5ba0272` | `test_f8_a_deadline_covers_its_own_los_not_others_on_the_same_concept` (negative assertion on a same-concept sibling with disjoint facets) |
| F9 | Medium | Interrupted deadline creation leaves active orphan goals | **fixed** | `1d5ba0272` | `test_f9_a_crash_between_publishing_and_linking_is_recovered_without_an_orphan`, `test_f9_concurrent_writers_publish_one_goal_and_one_link` |
| F10 | Medium | Today's headline still counts excluded material | **fixed** | `1d5ba0272` | `test_f10_the_headline_leaves_out_excluded_los_and_items` (LO level, item level, intent off) |

Fail-first on `bbb0b05d3` (23 failed, 3 passed): F1 queues still held `pi_a1` / `pi_b1`
and plans had no displacement; F3 views had no `cold` (always the cold banner), a
hinted attempt satisfied the check, an LO check served the exposed item, a routine
display did not hold it; F4 anchor `att_held`, not `att_review`; F5 cost 0.357 vs 0.179
min/day; F6 the chooser took `pi_plain`; F7 a reading row under Pause, Reference, Let
go, Keep and Light touch, and a reading step after the source was paused; F8 `lo_b` in
the goal's scope; F9 a readable-id goal, and a concurrent pair raised `UNIQUE
constraint failed: commitment_versions`; F10 `lo_a` still counted.

## What changed

### F1: intent at every insertion and serve boundary

- **Follow-up insertion** (`scheduler.build_due_queue`): the pending follow-ups pass
  the intent gate (`IntentServing.withhold_reason`) before `_insert_pending_followups`
  can rebuild one by id. A paused, referenced, let-go or answered-check item, and one a
  "Check once" still holds, is never resurrected; the task is left pending (nothing
  written) and serves once intent allows it.
- **Plans already built** (`daily_plan.engine.reconcile`, which every
  `advance_with_context` runs first): an unserved planned item that intent now
  withholds is displaced with the reason (`intent_paused`, `intent_check_waiting`,
  `intent_check_held`, ...). Learner picks and items already served are left alone.
  With intent changing nothing this is DL1's reconciliation.

### F2: rejected, with the reason

The finding asks for an `intent_v1` successor because the spec's §11 names one and the
playbook's 2026-10-17 rule makes measurement-admission changes successors. The fix step
keeps DL2 a live change behind `intent.enabled`:

1. **The owner's standing ruling** (UX Phase 1 landing on main; the facet-locks F6
   ruling; applied again to `plan.reading_from_furthest` and
   `plan.deterministic_staged_plans`, each recorded in spec §11): serving changes that
   replay never reads are live changes behind kill switches, not successors. That
   ruling superseded the spec's L6 ("serving changes are successors") for exactly this
   kind of change, and DL2's implement step verified both of its conditions (nothing
   persisted changes meaning; replay never reads intent; shadow rebuilds 0 / 0 / 0).
2. **The 2026-10-17 rule's trigger does not hold after F3's fix.** That rule covers "a
   change to which items are served as measurements, or to which new attempts are
   primed". DL2 changes neither: submit is untouched (priming is derived exactly as
   before), no cold task, probe, placement presentation or quick check is admitted or
   withheld differently, and the one new thing labelled a check on your own is now
   decided by the shared eligibility decision itself (`serve_eligibility.CHECK_ONCE`,
   below). A "Check once" attempt is an ordinary practice attempt in every ledger; the
   label is presentation.
3. **The predecessor is restored exactly by the switch, with commitments populated.**
   With `intent.enabled = false`, `intent_serving` returns `None` and every scheduler
   and plan branch is the predecessor's code; the new test pins the ranked list
   (priority and every component) and the plan of a vault holding Pause, "Check once"
   and Light touch commitments as equal to those of a vault holding none.
4. A tag would leave the control inert on the owner's vaults (at `mvp-0.8`) until a long
   upgrade chain, against "live changes behind kill switches, no shadow stages".

This stays an **open question for the owner/orchestrator** (below): if the owner wants
the spec's `intent_v1`, it is `mvp-0.29` gated on version and switch, with the upgrade
and fingerprint, and the F2 test becomes the below-the-tag pin.

### F3: "Check once" through the one eligibility decision

- `serve_eligibility` gains the request **`CHECK_ONCE`** (and the reason
  `check_once_answer_shown`): the cold check's question without a task. Standing
  exposure (submit would prime and only an attempt clears it) gives
  `serve_as_ordinary`; the cold check's holds (`cold_task_holds`: a routine display on
  the item or its LO, a non-routine reveal since the check was chosen, for one cold
  delay) or exposure that lapses by time give `defer_until`; otherwise `serve`. Pure;
  nothing persisted; submit and the existing requests are unchanged.
- **Selection** (`scheduling.intent.serving.build_checks`): every due candidate asks it.
  The eligible ones are the check's; with none, a hold makes the check wait
  (`intent_check_held`); with only exposed ones, the item is served as practice
  (`CheckState.servable`). An LO check therefore picks a cold sibling over an exposed
  top-ranked item.
- **Serving** (`intent.checks.served_check`, called at each serve): cold only when the
  decision says so now, so an exposure after planning is read at the serve. Not cold,
  the view is honest practice: `cold: false`, the banner "Practice: you've seen this
  answer, so this one is practice, not your check on your own. Your check comes back
  later.", no ladder header, locators shown. Help is still never blocked.
- **Answering**: only an attempt on your own (not primed, no hints, not a hinted
  attempt) answers the check. Any other attempt is practice: it answers nothing and the
  check is dated again `capture.test_me_later_days` after it (`date_source =
  "after_practice"`), so taking help or seeing the answer never uses up the one check.
  This is computed from the attempt ledger at every build; nothing is re-timed in
  storage.
- **Desktop**: the help ladder opens first only when the view carries `helpHeader` (a
  cold check); the DTO gains `cold` and the `after_practice` date source.

### F4: the anchor is the review that wrote FSRS state

`recall_targets.load_anchors` drops attempts whose grade is held for review now
(`held_grades.held_for_review_attempts`, the ledger's evaluation of the same predicate
the attempt step uses to leave FSRS state alone). A regrade or adjudication that
releases a hold makes the attempt an anchor again, as it makes it a review again.

### F5: the review interval runs from the anchor

`daily_plan.intent_cost.projected_cost` and `engine._review_items` (with intent active)
use the anchor as `ReviewItem.last_review_at`, falling back to `last_attempt_at` for
imported state with no qualifying attempt. With intent changing nothing,
`_review_items` is DL1's (the same quirk in DL1's admission is outside DL2's switch and
left as it is).

### F6: re-entry carries its order into block selection

`lanes.reentry_order` with intent tiers gives each item the rank of the position it
moves into as its `plan_rank` (the project-probe pattern), so `planner_value` and the
chooser's tie-break follow the intent order. Without tiers it is DL1's order exactly
(no `plan_rank`).

### F7: reading by the source's intent

`engine.reading_allowed`: a reading's source reads while any LO it teaches is
uncommitted or under an active Learn or Master; Pause, Reference, Let go, Keep, Light
touch and "Check once" on all of them stop new reading (§5, §6.10). Applied to the
plan's candidates (`next_reading_target(extraction_ids=...)`), to the split's reading
candidate at each boundary (`_context`), and in `reconcile` to a reading block placed
but not started (ended with `outcome = "displaced"`, `reason = "intent"`, 0 minutes
counted). With intent changing nothing the candidates are DL1's.

### F8, F9: deadline goals

- **Scope**: the goal names the commitment's LOs' canonical scope facets
  (`facet_scope.facets`), never concepts. A sibling with disjoint facets is outside the
  goal; a sibling that shares a facet still meets the goal on that facet (the goal
  model counts facets), which is the documented limit.
- **Recovery and serialization**: the goal id is derived from the commitment
  (`goal_intent_<commitment id>`); the commitment read, the read-modify-write of
  `goals.yaml` (written whole to a temporary file and atomically replaced) and the link
  run under `vault_mutation_lock`. A crash after publication is recovered by the next
  "Add a deadline" (it finds the goal by that id and links it); concurrent writers
  produce one goal and one link.

### F10: the headline counts what the plan can serve

`headline.intent_exclusions`: items whose resolved intent excludes them leave expected
recall; an LO leaves the counts when every item of it is excluded (an LO without items,
when its own intent excludes it). Intent off or no commitment: DL1's population.

## Claims corrected in `daily-loop-dl2.md`

"Pause / Reference / Let go keep items out" now holds at follow-up insertion and in
plans already built (F1); "A due Check once is served cold" holds only when the one
eligibility decision allows it, else it is labelled practice (F3); "the anchor is the
review that produced `due_at`" excludes held grades (F4); "re-entry orders by intent
tier" holds through the chooser (F6); "the commitment's LOs form the deadline scope"
holds by facets (F8).

## Open questions

1. **F2, the successor** (default in force: no tag, a live change behind
   `intent.enabled`, per the standing ruling). Owner/orchestrator to confirm, or ask for
   `mvp-0.29`.
2. **F3, a check after help** (default: an attempt that is not on your own does not use
   up the check, which comes back `capture.test_me_later_days` later). Alternative: any
   attempt ends it.
3. **F7, a source's intent** (default: reads while any LO it teaches is uncommitted or
   Learn/Master). Alternative: only when every LO is.

## Gate (fix step; targeted, per the owner rule of 2026-10-17)

The full pytest suite, the whole durability lane and the whole vitest run are the
landing gate's. Run here, with `TMPDIR` in the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| Fail-first: `tests/test_intent_codex_review.py` against `bbb0b05d3`'s `src/` and `migrations/` | 23 failed (every fixed finding), 3 passed (the F2 pin; F7 `learn` and `master`) |
| `pytest -n auto` on 163 files (list in `fixtures-local/tmp/dl2-fix-affected.txt`): the new `test_intent_codex_review.py`; the 7 `test_intent_*` files (`test_intent_goal_deadline.py` changed: the goal scope assertion now reads facets); the implement step's 133 affected files (`build_due_queue`, `requested_practice_item_ids`, the plan engine, lanes, re-entry, report, `get_practice_item`, `get_feedback`, `get_today_queue`, `prepare_queue_build`, the plan RPCs); every file that names `serve_eligibility`, the headline, `reentry_order`, `intent_cost`, the deadline, `served_check`, `recall_targets`, `load_anchors` or `held_grades`; and the contract pins (`test_architecture`, `test_config_refactor`, `test_registry_audit`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_vault_template`, `test_mobile_allowlist`, `test_sqlite_file_copies`, `test_ai_config`, `test_plan_determinism`, `test_reading_step_switch`) | **3,475 passed** (10 min) |
| `pytest -n auto --durable-sqlite tests/test_intent_*.py` (8 files) | **111 passed** |
| `npm install`, `npm run typecheck` | OK, clean |
| `npx vitest run`: `PracticeScreen.intentCheck` (+1 test: the practice-labelled view), every other `PracticeScreen*.test.tsx`, `IntentControl`, `IntentCheckFeedback`, `app/intentCheck` | **128 passed in 13 files** |
| `npm run frontend:build` | OK (existing chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | **0 errors** (no schema or config-key change; commit labels and line citations regenerated, separate commit) |
| Migrations | none (217 unused) |
| Tracked working vaults | untouched; no manual runs on copies were needed (all behaviour is under test with fakes) |

Paid or live calls: none ($0.00).

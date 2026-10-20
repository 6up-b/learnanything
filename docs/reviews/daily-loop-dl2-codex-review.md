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

1. **F2, the successor**: resolved by the re-review (below): DL2 is `mvp-0.29`.
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

---

# Re-review (Codex job `20261020-003824-5riC17`)

Codex re-reviewed `a220306fb` read-only: F1 **confirmed fixed**; F2 and F3 **reopened**;
one new finding, F11. Every reopened or new finding was reproduced first by
`tests/test_intent_codex_rereview.py`, run on `a220306fb`: **6 failed** for the reasons
the findings give (F2: the ranked list and plan moved with commitments at `mvp-0.27`,
intent was live there, a paused item's pending cold retry was withheld below any tag,
and `get_intent` answered `enabled: true` at `mvp-0.27`; F3: the unprimed attempt under
a sibling's LO hold satisfied the check; F11: `pi_a1` was missing from the queue with a
retired or a held-out cold sibling), **2 controls passed** (a cold attempt with its own
feedback row still answers the check; an available cold sibling is still preferred).
The F2 chain, gate, upgrade and new-vault pins name the new tag and have no predecessor
to fail on. No paid or live model calls ($0.00); no migration (217 still unused).

## Findings

| ID | Sev | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Intent exclusion bypassed by follow-ups and existing plan blocks | confirmed fixed (no change) | `1d5ba0272` | the F1 tests in `test_intent_codex_review.py`, rerun green at `mvp-0.29` |
| F2 | High | Missing intent successor (reopened) | **fixed** | `0fc6e3e96` | `test_f2_below_the_tag_commitments_change_nothing_with_the_switch_on`, `test_f2_below_the_tag_a_paused_items_cold_retry_is_still_served`, `test_f2_the_intent_control_is_off_below_the_tag`, `test_f2_the_chain_ends_at_the_intent_successor`, `test_f2_the_gate_reads_the_version_and_the_switch`, `test_f2_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest`, `test_f2_new_vaults_start_at_the_successor_with_intent_live` |
| F3 | High | "Check once" bypasses cold-measurement eligibility at completion (reopened) | **fixed** | `0fc6e3e96` | `test_f3_an_attempt_under_a_siblings_hold_is_practice_not_the_check` (+ control `test_f3_a_cold_attempt_still_answers_the_check_its_own_feedback_notwithstanding`) |
| F11 | Medium | An unavailable cold sibling suppresses the only servable practice candidate | **fixed** | `0fc6e3e96` | `test_f11_a_retired_cold_sibling_never_suppresses_the_servable_candidate`, `test_f11_a_held_out_cold_sibling_never_suppresses_the_servable_candidate` (+ control `test_f11_an_available_cold_sibling_is_still_preferred`) |

## What changed

### F2: intent is the successor `mvp-0.29`

The first fix step's rejection rested on "no measurement is admitted or withheld
differently". The re-review is right that F1's follow-up gate withholds a paused item's
pending cold retry, and that a "Check once" is a cold measurement of its own, so the
2026-10-17 rule (`docs/algorithm-change-playbook.md`) applies and the rejection is
withdrawn. The orchestrator had reserved `mvp-0.29` for this.

- `algorithm_versions`: `INTENT_ALGORITHM_VERSION = "mvp-0.29"`, appended to
  `SUCCESSOR_CHAIN` (so `LATEST_ALGORITHM_VERSION`, new vaults and every
  `successors_from` set follow), and `INTENT_VERSIONS`.
- `scheduling.intent.serving.intent_enabled` reads the version **and** the switch. It is
  the one gate: `intent_serving` (the scheduler, the plan engine, reconcile, the
  headline, `served_check`, `settle_answered_checks`), `plan report`'s intent section and
  the sidecar's `get_intent` / `set_intent` / `set_intent_deadline`. Below the tag, or
  switched off, `intent_serving` returns `None` and every scheduler and plan branch is
  the predecessor's own code (not a re-derivation); the control answers
  `enabled: false` and the writes refuse with a message naming the version.
- `learnloop upgrade --to mvp-0.29` (the default target; `intent_upgrade.upgrade_to_mvp029`):
  from `mvp-0.27`, or from `mvp-0.9` onwards through `upgrade_to_mvp027`; a tag change
  plus the idempotent projection rebuild (no projection change: replay never reads
  intent, as the implement step's shadow rebuilds showed, 0 / 0 / 0). Refuses anything
  older; a chained refusal passes through.
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.29"]` (only the version string moves it).
- **Landing note:** `mvp-0.28` is AD2+AD3's and lands first. The landing merge puts
  `INTENT_ALGORITHM_VERSION` after `mvp-0.28` in `SUCCESSOR_CHAIN`, points
  `intent_upgrade.PREDECESSOR` / `_upgrade_to_predecessor` at mvp-0.28's constant and
  upgrade, moves the chain-tail pins by one more and recomputes the snapshot comments
  ("until mvp-0.29 merged").
- Tests: the intent test vaults (`tests/intent_fakes.make_intent_vault` and three direct
  `create_daily_plan_vault` calls) now run at `mvp-0.29`; the chain-tail pins in 19 test
  files moved by one; the CLI help snapshot (only `upgrade --help` changed).
- Docs: the spec's §11 row (`intent_v1` = `mvp-0.29`), the two ruling sections of
  `daily-loop-dl2.md` (marked superseded) and its owner commands (an upgrade step),
  `Algorithm Versions and Reproducibility.md`, the schema/template/registry comments,
  the reference generator's `[intent]` note and an `intent.enabled` catalog entry.

### F3: completion asks the eligibility decision at the attempt

`serve_eligibility.check_once_at_attempt` is the `CHECK_ONCE` decision as it stood when
the attempt was submitted: the window bounded at the attempt (Q33's bound: later reveals
do not count), the attempt's own linked rows (its feedback) left out, and the exposure
read since the item's previous attempt. `build_checks` takes it as `cold_at`: an attempt
answers the check only when it is on your own **and** that decision is `serve`. Any other
attempt is practice and dates the check again `capture.test_me_later_days` after it,
which is what the practice view already promised. Pure read; nothing persisted; submit
unchanged. The decision is read at the submission instant, so a hold that lapsed
between the serve and the submit no longer counts (the hold is one cold delay, already
elapsed); a reveal of a sibling while the attempt is open does count.

### F11: the routine gate first

`serving_exclusions.routine_withhold_reason(vault, item, state, exclusions)` is the
scheduler's per-item routine gate (retired, inactive state, exam reservation, held-out
material, pending-variant hold, staged ownership, dialogue-turn instances, administered
probes, unservable stimuli, no LO, put-away LO), with its reason codes and order;
`build_due_queue`'s loop now calls it (a behaviour-preserving extraction). A due check's
candidates pass it (`build_checks(routinely_servable=...)`, read lazily once per build)
before the eligible / held / exposed split, so a candidate routine serving can never
offer neither is the check nor suppresses one that can be served.

## Gate (re-review fix step; targeted, per the owner rule of 2026-10-17)

`TMPDIR` in the worktree's `fixtures-local/tmp`. The full suite, the whole durability
lane and the whole vitest run are the landing gate's.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| Fail-first: the 8 behaviour tests of `test_intent_codex_rereview.py` on `a220306fb` | **6 failed, 2 passed** (the controls) |
| `pytest -n auto` on 176 files (list in `fixtures-local/tmp/dl2-rr-affected.txt`): the previous fix step's 163 (the `test_intent_*` files, every `build_due_queue` / plan / re-entry / headline / `serve_eligibility` / `served_check` / `recall_targets` / `held_grades` user and the contract pins `test_architecture`, `test_config_refactor`, `test_registry_audit`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_vault_template`, `test_mobile_allowlist`, `test_sqlite_file_copies`, `test_ai_config`, `test_plan_determinism`, `test_reading_step_switch`); every test naming `SUCCESSOR_CHAIN`, `LATEST_ALGORITHM_VERSION`, `DEFAULTS_SNAPSHOT_BY_ALGORITHM` or an upgrade (the `test_mvp0*_upgrade.py` files, `test_method_explicit_upgrade`, `test_regrade_contract_*`, `test_serve_eligibility_review`, `test_recurrence_commands`, `test_route_rules_in_grader`, `test_required_method_grading`, ...); every test naming `serving_exclusions`, `serve_eligibility` or the intent handler; and the new `test_intent_codex_rereview.py` | **3,773 passed** (one earlier run: 3,772 passed, 1 failed, `test_architecture`'s function-local edge inventory, fixed by importing the routine gate's two helpers at module level) |
| `pytest -n auto --durable-sqlite tests/test_intent_*.py` (10 files) | **123 passed** |
| Frontend | unchanged: no npm, vitest or build run needed |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | **0 errors** (head 213; the `mvp-0.29` snapshot, the intent catalog entries, commit labels; commit `c618fa765`) |
| Migrations | none (217 unused) |
| Tracked working vaults | untouched; no manual runs on copies (all behaviour under test with fakes) |

Paid or live calls: none ($0.00).

## Open questions (re-review)

1. **F3, a hold that lapses between the serve and the submit** (default: the decision is
   read at the submission instant, so such an attempt answers the check). Alternative:
   any hold seen at the serve makes the attempt practice (this needs the serve recorded).

---

# Fix round 3 (orchestrator rulings)

The final verify (Codex job `20261020-013947-7LLooy`, on `32040fcbc`) confirmed F1, F2
and F3 fixed, **reopened F11** (Medium) and found **F12** (Medium). The orchestrator
ruled the structural fix for both, so these stop recurring:

- **R1, one admission predicate.** Every per-item gate `build_due_queue` applies is
  expressed once and asked by both the build and the "Check once" candidate
  selection; cold-over-practice preference is applied only among the candidates it
  admits. Incumbent queue order unchanged.
- **R2, one "disclosures attributable to this attempt" function.** Submit's exemption
  (retry key + frozen trace hash, own-disclosure rows) is shared, and
  `check_once_at_attempt` uses it for both the exposure and the LO hold; other items'
  or unrelated disclosures still hold.
- **R3,** fail-before tests on `32040fcbc` for both verify reproductions as written.

## Findings

| ID | Sev | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F11 | Medium | A fresh diagnostic-probe sibling suppresses the only servable "Check once" candidate (reopened: the freshness gate stood outside the shared predicate) | **fixed** (R1) | `3f7be0a90` | `test_f11_a_fresh_diagnostic_probe_never_suppresses_the_servable_candidate`, `test_f11_the_plan_pool_offers_the_admitted_candidate` (+ control `test_f11_an_admitted_cold_sibling_is_still_preferred`); structure: `test_r1_every_gate_of_the_build_is_the_admission_predicates`, `test_r1_check_selection_asks_the_builds_admission_predicate`, `test_r1_the_predicate_names_the_freshness_reserve_for_a_check_candidate` |
| F12 | Medium | A frozen self-grade's own key display postpones the check it answers | **fixed** (R2) | `3f7be0a90` | `test_f12_a_frozen_self_grade_answers_the_check`, `test_f12_a_repeated_self_grade_never_postpones` (+ control `test_f12_an_unrelated_disclosure_still_holds`); structure: `test_r2_one_attributable_disclosure_function` |

All in `tests/test_intent_orchestrator_rulings.py`. The F12 tests drive the desktop's
real flow through the sidecar handlers: `save_practice_draft`, the freeze
(`record_self_grade_disclosure`), the key's display (the same call with a `displayId`,
an unlinked row), `submit_attempt` with a self-grade, `acknowledge_practice_submission`.

**Fail-before on `32040fcbc`** (its `src/` and `migrations/` from `git archive`, with
`-o pythonpath=` pointing at them; log `fixtures-local/tmp/dl2-fix3-failfirst.txt`):
**4 failed, 2 passed** (the controls). F11: `pi_a1` missing from the queue
(`['pi_b1', 'pi_c1', 'pi_c2']`), and the plan view's check item was `pi_a2` (the
fresh probe) instead of `pi_a1`; F12: `settle_answered_checks` returned `[]` for the
self-graded attempt (submit had admitted it unprimed), on the first check and on the
repeated one. The four R1/R2 structure tests name the new functions and have no
predecessor to fail on.

## What changed

### R1 / F11: `serving_exclusions.admission_reason`

- `admission_reason(vault, item, state, exclusions, gates, *, requested, intent_gate)`
  is the scheduler's whole per-item admission, in `build_due_queue`'s order and with
  its reason codes (`ADMISSION_GATES` = `ROUTINE_GATES` + `BUILD_GATES`): the routine
  gate (`routine_withhold_reason`, unchanged); the build's intent gate when given; then
  the build's gates (`BuildGates`): the diagnostic freshness reserve, placement and the
  cold-start gate (a request is exempt from both, as before), and the probe-episode
  gates (`diagnostic_reserved`, `voi_value_below_minutes_cost`).
- `scheduler._BuildAdmission` implements the build's gates over one build's reads,
  each item's read once: the placement decision and the probe scoring (the ranking
  components and, in an in-progress episode, the probe's value) moved out of the loop
  verbatim, so the gate and the ranking read the same values. The loop now asks
  `admission_reason` once per item (the only gate call; `zero_priority` stays the one
  ranking filter, which a request, as every check candidate is, never meets because
  of the requested floor). The reserved-surface slate annotation and
  `probe_item_ids` are recorded as before.
- The check's split (eligible / held / exposed) is now made lazily
  (`IntentServing.checks`, `split_check`) among the candidates the predicate admits as
  a request. `build_due_queue` binds its own admission
  (`IntentServing.bind_admission(admission.admits_check_candidate)`) before it reads a
  check (the request filter and the follow-up filter moved after the binding; the base
  reads stay where they were). A view built outside the queue (the plan's pool and
  re-planning, `served_check`, `settle_answered_checks`, `answered_check`, the
  headline) gets the same predicate over its own reads, with no session and nothing
  written (`scheduler.check_admission`, each read on first use).
- Incumbent order: the extraction is behaviour-preserving (the reason codes, their
  order and the components' key order are unchanged); the previous rounds' parity and
  determinism pins are in the gate below and pass.

### R2 / F12: `serve_eligibility.attributable_disclosure_ids`

- The disclosure identity (`trace_hash`, `disclosure_identity`, `is_own_disclosure`,
  the encoding version) moved into `serve_eligibility` (it stays a leaf: `json`,
  `hashlib`); `reveal_ledger` re-exports the same names, so writers and readers are
  unchanged.
- `attributable_disclosure_ids(rows, *, practice_item_id, submission_id,
  learner_answer_md)` is the one exemption: the item's own `answer_display` rows whose
  identity is exactly that retry key and trace. `gather` (submit, via
  `attempts.submit_eligibility_inputs`) computes `exempt_reveal_ids` with it;
  `check_once_at_attempt` recovers the attempt's own key and stored trace
  (`attempt_submission`, which `reveal_ledger._production_trace` now delegates to) and
  computes the same set.
- `cold_task_holds` skips exempt rows, so the attempt's own disclosure neither exposes
  it nor holds its LO. Only `check_once_at_attempt` and submit pass exempt rows, and
  submit does not read holds, so every other path is unchanged. A sibling's
  disclosure, another draft's, or any other display still holds (the control).

## Gate (fix round 3; targeted, per the owner rule of 2026-10-17)

`TMPDIR` in the worktree's `fixtures-local/tmp`. The full suite, the whole durability
lane and the whole vitest run are the landing gate's.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| Fail-before: the 6 behaviour tests of `test_intent_orchestrator_rulings.py` on `32040fcbc` | **4 failed, 2 passed** (the controls) |
| `pytest -n auto` on 278 files (list in `fixtures-local/tmp/dl2-fix3-affected.txt`): the re-review step's 176 (every `test_intent_*` file, every `build_due_queue` / plan / re-entry / headline / `serve_eligibility` / `served_check` / `recall_targets` / `held_grades` user, the successor-chain users and the contract pins `test_architecture`, `test_config_refactor`, `test_registry_audit`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_vault_template`, `test_mobile_allowlist`, `test_sqlite_file_copies`, `test_ai_config`, `test_plan_determinism`, `test_reading_step_switch`); the new `test_intent_orchestrator_rulings.py`; every test naming the reveal ledger, the disclosure identity, `submit_eligibility_inputs`, `serving_exclusions`, `intent_serving` or the self-grade disclosure; every test of production admissibility, coldness receipts, `submit_attempt` or `complete_self_graded_attempt` | **4,981 passed** (10 min) |
| `pytest -n auto --durable-sqlite tests/test_intent_*.py` (11 files) | **133 passed** |
| Frontend | unchanged: no npm, vitest or build run needed |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | **0 errors** (head 213; commit labels and line citations; commit `ef3d6042b`) |
| Migrations | none (217 unused) |
| Tracked working vaults | untouched; no manual runs on copies (all behaviour under test with fakes) |

Paid or live calls: none ($0.00).

## Open questions (fix round 3)

1. **The session in a view built outside the queue** (default: `check_admission` reads
   no session, so no calibration-session cap lift and no short-session probe rule).
   The queue build binds its own session-aware admission; the plan, the practice view
   and settling read the session-free one. They can differ only for a diagnostic
   surface of an in-progress probe episode in a short or calibration session.
   Alternative: thread the session into `intent_serving`.
2. **Slate composition is not admission** (default: unchanged). The teach-back value
   admission / session cap and `limit` act on the composed slate, after
   `pick_checks`, so a teach-back chosen as a check's item could still be dropped by
   the teach-back cap for that build. Alternative: apply `pick_checks` after the
   teach-back composition.

---

# Fix round 4 (orchestrator rulings)

The verify of `8e0ca1875` (Codex job `20261020-021715-9JeVsu`) confirmed F11 and F12
fixed and found **F13** (High), **F14** (Medium) and **F15** (Medium). The
orchestrator's rulings:

- **R1 (F13).** `on_your_own` is the activity policy's canonical assistance
  classification, the one the policy uses everywhere, not a `hinted_attempt` special
  case. Any assisted class (`reconstruction_after_walkthrough` included) leaves the
  check pending and follows the practice-postponement rule. A table-driven test over
  every activity class.
- **R2 (F14), structural.** A due "Check once" survives plan composition. Teach-back
  composition and `pick_checks` never drop an intent check for value or cost: the
  learner asked, so it is served within the plan's minutes. The only allowed
  non-serve is the plan's minutes exhausted, and it is recorded. Contract: a property
  test over randomized vaults at advancing clocks.
- **R3 (F15).** A due check whose item also carries a stricter measurement duty (an
  active diagnostic, a cold follow-up) is served under that duty; its banner promises
  no help ("measured on your own"); an on-your-own completion satisfies both. The
  diagnostic and cold-follow-up safeguards are unchanged. A vitest for both overlap
  cases, and a backend test that the server chooses the banner variant.

## Findings

| ID | Sev | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F13 | High | An assisted reconstruction satisfies "Check once" | **fixed** (R1) | `33a8ca802` | `test_f13_on_your_own_is_the_activity_policys_classification` (every `SUPPORTED_ATTEMPT_TYPES` entry x plain / primed / hinted), `test_f13_every_contamination_class`, `test_f13_an_assisted_reconstruction_leaves_the_check_pending_and_dates_it_again` (+ control `test_f13_an_independent_attempt_still_answers`) |
| F14 | Medium | Teach-back composition can suppress a due check indefinitely | **fixed** (R2) | `33a8ca802` | `test_f14_an_item_check_on_a_teach_back_survives_composition`, `test_f14_an_lo_check_whose_cold_candidate_is_a_teach_back_is_served`, `test_f14_the_teach_back_count_cap_never_drops_a_check`, `test_f14_a_due_check_is_planned_first_within_the_minutes`, `test_f14_a_check_the_minutes_cannot_hold_is_recorded_not_silent`; contract `test_f14_contract_a_due_check_is_planned_within_n_builds_or_every_miss_says_minutes` (16 seeds) |
| F15 | Medium | Overlapping diagnostic or cold-follow-up duties block check help | **fixed** (R3) | `33a8ca802` | `test_f15_a_check_with_a_cold_follow_up_is_served_under_that_duty`, `test_f15_a_check_under_an_active_diagnostic_is_served_under_that_duty`, `test_f15_the_serve_chooses_the_variant_server_side_and_one_completion_satisfies_both`, `test_f15_the_probe_contract_carries_the_diagnostic_variant`, `test_f15_a_pure_diagnostic_answer_satisfies_the_check` (+ controls `test_f15_an_ordinary_check_still_offers_help`, `test_f15_a_seen_check_with_a_cold_follow_up_stays_practice`); vitest: the two overlap cases in `PracticeScreen.intentCheck.test.tsx` |

Python tests in `tests/test_intent_fix_round4.py`. Fakes only: the F15 serve test
drives `start_session`, `get_practice_item` and `submit_attempt` through the sidecar
handlers with the `manual` grading provider; the probe-contract test stubs
`ready_grading_provider`.

**Fail-before on `8e0ca1875`** (its `src/`, `migrations/` and
`apps/learnloop-tauri/` from `git archive` into the scratchpad; pytest with
`-o pythonpath=` at the extracted `src`; vitest from the extracted app with the
worktree's `node_modules` linked; log `fixtures-local/tmp/dl2-fix4-failfirst.txt`):

- **pytest: 18 failed, 52 passed** (rerun on resuming the round, same result). F13: `on_your_own` returned True for unprimed,
  hint-free `guided_walkthrough` and `reconstruction_after_walkthrough` (2 table
  rows), and the reproduction's check resolved `satisfied` (`settle_answered_checks`
  returned the commitment). F14: the teach-back check item was missing from the queue
  on every build (item check; the LO check's cold teach-back, `[] == ['pi_a2']`; under
  the count cap); the plan recorded neither `checks` nor `checks_unplanned`; the
  contract failed on 6 of 16 seeds (no build planned the check and no miss carried a
  reason). F15: `served_check` had no `duty`, so the cold-follow-up serve carried the
  help banner, and the probe contract carried no `intentCheck`. The passes are the
  controls (the seen-check control included), the 46 table rows on which the old predicate already agreed with the
  policy, and the 10 contract seeds the old build happened to serve.
- **vitest: 1 failed, 8 passed** (rerun on resuming, same result). The diagnostic overlap showed the help banner ("Help
  is still here ...") instead of the measured one. The cold-follow-up overlap passes on
  the old app: its fix is server-side (the view the server sends), and the old app
  already renders whatever banner it is sent and opens no ladder without a help
  header; the backend tests above fail before for it.

## What changed

### R1 / F13: `on_your_own` is `attempt_counts_as_assisted`

- `scheduling/intent/serving.on_your_own(row)` is now `not
  causal_activity_policy.attempt_counts_as_assisted(attempt_type, primed, hints_used)`,
  the classification the canonical projection, the facet timeline and certification
  read. A guided walkthrough, a reconstruction after one, a hinted attempt, a primed
  attempt (repair activity) and an instructional diagnostic are practice: they answer
  nothing and date the check again (`after_practice`, the existing postponement). A
  pure diagnostic (`diagnostic_probe`, unprimed, no hints) is on your own. The
  historical exposure decision (`serve_eligibility.check_once_at_attempt`) is
  unchanged and still asked.
- `pyproject.toml`: the import-linter cycle contract exempts
  `scheduling.intent.serving -> diagnosis.causal_activity_policy`, beside the
  existing `recall_targets` exemption of the same leaf (it imports only dataclasses,
  typing and the top-level `learnloop.causal_activity_policy`).

### R2 / F14: due checks are planned first, within the plan's minutes

- Queue (`scheduler.build_due_queue`): the items `pick_checks` chose are left out of
  the teach-back value admission and kept by `_enforce_teach_back_session_cap`
  (`keep=`) without counting toward the cap. So whatever `pick_checks` selects for an
  LO check survives composition; selecting among survivors and exempting the
  selection from the only composition that dropped it are the same set. Queues with no
  due check are unchanged (`check_item_ids` empty).
- Plan (`daily_plan/engine._prepare_plan`): `_select_checks` takes every due "Check
  once" item in the pool, in pool order, while its estimate fits what the requests
  left of the budget. Its minutes come off the budget before the split, as requests'
  do. The first block places requests, then checks (`_Prepared.forced`). The item
  stays a scheduled check in the maintain lane (§5.2, §6.1), not a request
  (`split.requested` unchanged). The split records `checks` (item, commitment,
  minutes) and `checks_unplanned`: each check the minutes cannot hold, with
  `reason: "plan_minutes_exhausted"` and the minutes left; a due check with no item in
  the pool is recorded as `not_in_pool` (never expected; visible, not silent).
  Crash recovery (`advance_with_context`), the pending-minutes read of
  `_classified_pool`, `set_minutes` and `more_new` read the same forced rows
  (`_forced_rows`), and `_empty_extension` treats a plan with forced checks as
  non-empty. The first block's `why` says "the delayed check you asked for comes
  first" when only checks are forced.
- Plans with no intent view (`built.intent is None`) are unchanged: no `checks`
  keys, the same budget and the same first block.
- `tests/test_intent_plan.py::test_several_checks_due_on_one_day_are_bounded_by_the_minutes_not_a_count`
  at 10 minutes now allows 3 (the estimator puts each check at 2.81 minutes, so three
  fit in 10 and the other five are recorded as minutes exhausted); the bound stays the
  minutes, not a count.
- This resolves fix round 3's open question 2 (slate composition is not admission).

### R3 / F15: a stricter duty gives the measured view

- `intent/checks.served_check(..., duty=None)`: with a due cold follow-up on the item
  (`cold_retry`, `certification_cold_probe`, read through
  `active_followup_task_for_item`, `cold_followup_duty`), or with
  `duty="diagnostic"` passed, the view is `_measured_view`: `duty`, the
  `MEASURED_BANNER` ("A check on your own: this one is measured on your own, so no help
  is offered."), locators hidden, and **no** `help_header`, so the card opens no
  ladder. Only a cold check gets it: one whose answer was seen is practice (F3) whatever
  else the item carries, since the measured banner would claim a check that attempt
  cannot answer. The ordinary check's view (the D42 help banner and ladder header) is
  unchanged.
- Sidecar `get_probe_contract`: an active diagnostic presentation of a due check's item
  carries the check's measured view (`intentCheck`, `duty: "diagnostic"`); the
  contract is the server's word that the item is a probe.
- Desktop (`PracticeScreen.tsx`, `dto.ts`): while the probe is active, the card shows
  the contract's check view in place of the practice item's. Nothing else changes: the
  cold-follow-up refusal ("No hints on this one ...") and the diagnostic refusal
  ("hints are disabled during a diagnostic check ...") are the existing guards.
- One completion: the on-your-own answer completes the cold retry (its task leaves
  `pending`/`served`) and answers the check; a pure diagnostic answer answers it too.

## Gate (fix round 4; targeted, per the owner rule of 2026-10-17)

`TMPDIR` in the worktree's `fixtures-local/tmp`. The full suite, the whole durability
lane and the whole vitest run are the landing gate's.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| Fail-before on `8e0ca1875`: `tests/test_intent_fix_round4.py` | **18 failed, 52 passed** (the controls and agreeing table rows) |
| Fail-before on `8e0ca1875`: `PracticeScreen.intentCheck.test.tsx` | **1 failed, 8 passed** |
| `pytest -n 8` on 279 files (fix round 3's 278 in `fixtures-local/tmp/dl2-fix3-affected.txt` plus `test_intent_fix_round4.py`; list `fixtures-local/tmp/dl2-fix4-affected.txt`) | **5,050 passed, 1 failed** (24 min, load average about 50 from the other worktrees). The failure, `test_voi_v2.py::test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode`, passes alone at the tip and at `8e0ca1875`, and its file passes whole (39 passed): a load flake. Its vault has no intent commitment, so this round's code is not on its path |
| `pytest -n 8` on 24 more files naming `build_plan`, the teach-back session cap or value admission, `served_check`, the probe contract, `on_your_own`, `daily_plan` or `attempt_counts_as_assisted` (list `fixtures-local/tmp/dl2-fix4-extra.txt`) | **362 passed** |
| `pytest -n 8 --durable-sqlite tests/test_intent_*.py` (12 files) | **203 passed** (after the control fix below; before it, 1 failed, 202 passed, failing the same way at `8e0ca1875`) |
| `npm run typecheck` | OK |
| vitest, the 10 `PracticeScreen*.test.tsx` files | **117 passed** |
| vitest, whole run (run once by mistake, a wrong glob) | 34 timing failures under the same load in 15 files that this round does not touch except `PracticeScreen.intentCheck`; those 15 files rerun alone: **253 passed** |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | **0 errors** (head 213; commit labels and line citations; commit `2e87243ae`) |
| Migrations | none |
| Tracked working vaults | untouched; all behaviour under test with fakes |

Paid or live calls: none ($0.00).

## Rejected or left as is (fix round 4)

1. **The practice item's serve does not know about a diagnostic presentation**
   (default: the probe contract carries the diagnostic variant). The contract is where
   the server decides whether the item is an active probe, so the variant is chosen
   there; until the contract arrives the card shows the practice item's view. The probe's own guard
   (hints disabled) applies from the contract's arrival, as before.
2. **The queue's `limit` slice** can still cut a check from a session queue built with
   a limit; the plan's pool is not built with one, and the plan is what serves. The
   contract test covers the plan path.
3. **Fix round 3's control `test_f12_an_unrelated_disclosure_still_holds` was
   timing-dependent** (found by this round's durability run; it fails the same way
   at `8e0ca1875`). It submitted the sibling B with its own self-grade, and a
   submitted B is itself an on-your-own answer of the LO's check (its own disclosure
   is attributable to it), so the control held only when every write fell in one
   wall-clock second; the slower durable connections spread them. The control now
   freezes and displays B's key in its own session without submitting B; it passes
   in both modes, at the tip and at `8e0ca1875`. No production change.

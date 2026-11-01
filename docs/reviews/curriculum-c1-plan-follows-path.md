# Curriculum C1: the plan follows the deliverable

**Stage:** `curriculum-c1-plan-follows-path`, branch `curriculum/c1-plan-follows-path` (worktree `learnanything-ad1`),
base `94494b4cc` (main: mvp-0.38, migration head 228). **Spec:** `docs/specs/spec_deliverable_curriculum_v1.md` §7.6,
§8.1 and the §12 C1 row. **No paid or live call was made**: every model is a fake (`DeliverableFake`,
`PathJudgeFake`, C0a's `CoverageJudgeFake`); every ad-hoc script ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (`scratchpad/c1/iso.sh`). No owner vault was opened, `~/.config/learnloop`
was not read, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`.
**A successor**: `mvp-0.39` after `mvp-0.38`. **No migration** (C0's 228 holds every table C1 reads).

## Successor number

RW6b part 1 (`mvp-0.39`, migration 227) had not landed when this stage started (main `94494b4cc` is `mvp-0.38`,
`ls migrations/` ends at 226, 228), so C1 is built as **`mvp-0.39` after `mvp-0.38`**. Whichever of the two lands
second renumbers: the tag is ONE constant (`DELIVERABLE_PLAN_ALGORITHM_VERSION`), the chain is linear, and the
pins below move with it (see "Renumbering at landing").

## What was built

| Piece | Where |
|---|---|
| The tag `DELIVERABLE_PLAN_ALGORITHM_VERSION = "mvp-0.39"`, appended to `SUCCESSOR_CHAIN`; `DELIVERABLE_PLAN_VERSIONS` | `src/learnloop/algorithm_versions.py` |
| The upgrade, per the playbook and the mvp-0.36/0.37/0.38 pattern: accepts mvp-0.38 or mvp-0.9 onwards through the chain, one journalled `BEGIN IMMEDIATE` activation (predecessor's manifest, projection activation as the completion marker, registry refresh, journal, publication last), `complete_interrupted_activation` handing an earlier link's journal down the chain | `src/learnloop/deliverable_plan_upgrade.py` |
| `learnloop upgrade --to mvp-0.39`, the bare upgrade's target (the latest), the help text; the CLI's and the sidecar's installed completion is now this link's; the activation journal's docstring; the frozen-source-modules list | `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`, `activation_journal.py`, `pyproject.toml` |
| Kill switch `[curriculum] plan_uses_path` (default true), classified (`structural`, `operational`) in the parameter registry; every defaults snapshot mvp-0.9 … mvp-0.38 recomputed (the key is present and inert below the tag) and mvp-0.39 recorded | `config/schema.py`, `params/parameter_registry.py`, `config/template.py` |
| The gate `engine.deliverable_plan_active(vault)`: the tag, `curriculum.enabled`, `curriculum.plan_uses_path` **and RW7b's gate** (`reading_paths.enabled`, `reading_paths.plan_uses_path`) | `daily_plan/engine.py` |
| `_reading_on_path` gains its first branch: RW7b's own body is now `_reading_on_book_path` (unchanged), and with C1 active `_reading_on_deliverable` reads the deliverable the plan follows and walks its path in order | `daily_plan/engine.py` |
| Which deliverable: `plan_deliverable` walks `nearest_deliverables` (the active deliverables in the existing nearest-goal rule's order: nearest due date, then higher priority, then id) and follows the first whose path is fresh (or withheld) | `source_retrieval/deliverable_path.py` |
| `deliverable_plan_path(vault, repository, goal)`: RW7b's `plan_path`'s sibling. The lines are the Guide's own (`effective_lines`) from the judge's rows **for the learner's current state key**; `stale` (judged only for an older state), `withheld` (protection unreadable: followed, plans nothing), `unreadable` (recorded, RW7b decides), `no_scope` / `no_depth` / `not_judged` (not in play). Never judged here | `source_retrieval/deliverable_path.py` |
| The walk: `next_listed_reading_target(steps, from_furthest, exam, allowed)` takes the planned lines (`core`, `prerequisite`, a *read it anyway*) in the path's order across books, and runs the predecessor's rules first on each candidate: the exam predicate (an exam extraction, a section with an exam span), U4's front-matter rule (with `plan.reading_from_furthest`), DL2's `reading_allowed` per book; a finished section (DL1's rule, now `_unfinished_target`, shared) is passed | `daily_plan/reading.py` |
| Receipt `reading_path_plan_v2` (only where a deliverable path was in play): v1's keys with `predecessor` = **RW7b's choice**, `chosen_by` ∈ `deliverable` / RW7b's `path` / `order`, `deliverable` (goal id, status, depth, `input_state_key`, `judgment.state_key`, every row read with its judge and override row ids, the line chosen, every deliverable consulted) and `rw7b` (RW7b's own v1 receipt, or None) | `daily_plan/engine.py` |
| Plans already built (fix round 2: **one invariant**, `_reading_follows_fresh_choice`): while the plan's reading has no reading history, it is whatever a fresh build would choose right now. A v2 plan with no history whose fresh choice (`_fresh_reading`, the build's own selection: C1, else RW7b, else the order, under the current switches and freshness) differs from its staged reading withdraws the unstarted block and stages the new reading, with one entry in the receipt's bounded `moves`. A v1 receipt keeps RW7b's own rule (`_reading_path_switched_off`, unchanged from main). The block move (end the unstarted reading block unread, recompute the reading's minutes, re-split) is `_move_plan_reading` | `daily_plan/engine.py`, `daily_plan/records.py` |
| The fresh choice's memo (fix round 2, Low 6; fix round 3): the choice is memoized on a fingerprint of its inputs taken before any input is gathered: the whole vault database (`PRAGMA data_version` of a watcher connection, which moves on any commit by another connection, and that connection's own `total_changes`), the config hash, the vault's goals with their days left, the local and UTC dates, and the number of diagnosis waits run out by placement's own rule (`placement.state.diagnosis_waits_run_out`: a deadline crossed changes placement with no write). The watcher is checked against the file's device and inode on every fingerprint, and the sidecar drops the memo when a context loads or closes (fix round 4). A hit returns exactly what the computation returned | `daily_plan/reading_choice.py`, `daily_plan/engine.py` (`_remembered_fresh_reading`) |
| The daily quiet re-judgment: `deliverable_path.refresh_for_plan` judges the nearest in-play deliverable whose path is stale, under `plan_fallback.quiet()` (no OpenRouter offer, no grant); the sidecar starts it in the background from every plan RPC (`daily_plan._require` → `handlers/deliverables.refresh_for_plan`), at most once a local day per vault per sidecar process | `source_retrieval/deliverable_path.py`, `learnloop_sidecar/handlers/deliverables.py`, `learnloop_sidecar/handlers/daily_plan.py` |
| Refresh adoption is the invariant itself: once a refresh (or a Guide open) makes the nearest path fresh, the fresh choice is C1's step and a plan with no reading history takes it. The Guide's judgments and the daily refresh share one in-flight coalescing set keyed by (deliverable, depth, path state key), so neither sends a second judgment for the same state while the other's runs; each claims the key of the inputs it prepared, immediately before the call, and sends exactly those inputs (fix round 3); every claim carries its job's own token, so a job transfers and releases only its own claims (fix round 4) | `daily_plan/engine.py`, `source_retrieval/deliverable_path.py` (`refresh_for_plan`), `learnloop_sidecar/handlers/deliverables.py` (`_claim_path`, `_move_claim`) |
| Config reference: the kill switch's description; DB/config reference regenerated | `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`, the generated notes |
| Spec §7.6 "as built" note | `docs/specs/spec_deliverable_curriculum_v1.md` |

## Decisions taken here (open to the owner or the landing)

1. **C1 sits inside RW7b's gate.** `_reading_on_path` is only called with RW7b active, and the spec places C1 as its
   first branch, so C1 needs `reading_paths.enabled` and `reading_paths.plan_uses_path` too, besides
   `curriculum.enabled` (Q14: the plan never follows a path the learner cannot see; the Guide's slice lives in the
   path card, which shows only with `reading_paths.enabled`) and `curriculum.plan_uses_path`.
2. **"In whichever book" is any book the path names**, not only as-you-read imports (DL1's conservative rule for
   the per-book order). The deliverable is the learner's explicit act naming what to read across books. DL2's
   `reading_allowed` is applied per book, as it is to RW7b's candidate list; exam and held-out material is
   excluded twice (C0a's library never lists it, and the plan's exam predicate runs on each candidate).
3. **A fresh path with nothing left to plan** (every line finished, skipped, already shown, assumed, pending a
   check, or filtered) **leaves RW7b's choice**; the receipt says `status: path` with `step: null`. The deliverable
   leads while it has something to read; the learner's other reading is not blocked once it is done.
4. **A withheld path plans nothing** (fail closed, RW7b's rule): protection could not be read, so no reading.
5. **No deliverable in play leaves RW7b's plan byte for byte** (no v2 receipt), mirroring RW7b's "None when no path
   was in play". A deliverable without a resolution, a depth or any judgment is not in play.
6. **The v2 receipt keeps `rw7b`** (RW7b's own receipt) so that turning C1 off restores RW7b's reading exactly
   and turning both paths off restores the order's. When C1 and RW7b choose the same section, C1 off still moves
   the stored reading to RW7b's own copy (RW7b's `core` label, not C1's `prerequisite`): RW7b's plan exactly.
   Fix round 2: the switches are inputs of the fresh choice like any other. In whatever order they reach the plan
   (C1 off, then RW7b's switch off; C1 back on), a reading with no history ends where a build now would; the
   receipt's v2 keys record the latest choice and `moves` the first and the latest move (`move_count` counts
   all). Switching C1 back on moves an unread reading back to C1's step (RW7b's v1 "recorded once" rule is
   unchanged for v1 plans).
7. **The daily re-judgment runs in the background and the build never waits.** The sidecar answers one request
   at a time and the plan calls no model, so a synchronous judgment before the build would freeze the app for
   a model call. It starts with the first plan RPC of the day (`get_daily_plan` and every other plan RPC go
   through `_require`), once a local day per vault in a sidecar process (an in-memory marker: a restart may run it
   once more, and a fresh path pays nothing). "Plan route only" is `plan_fallback.quiet()` (no offer, no grant)
   **and** the route itself (fix round 5): the job asks only when the path judge resolves to the subscription
   ChatGPT-plan route (`chatgpt_plan`, `deliverable_path.plan_refresh_route_problem`); any other resolution,
   a metered provider priced and with budget left included, is `unavailable`, sends no call, and the plan's
   receipt stays `stale`. A learner's own Guide judgment keeps its route rules. The queued job rechecks C1's
   complete gate (`deliverable_plan_active` and the curriculum switches) on the vault as it is now before it
   starts and before its claim, and the judge asks it at every request and inside the write: a switch turned
   off meanwhile sends and keeps nothing. The CLI builds plans without it (a CLI build on a stale path follows
   RW7b and says `stale`).
8. **One invariant for plans already built (beyond the letter of §7.6; fix round 2).** The path's key holds the
   days left before the deadline and the books read (C0b's learner context), so a deadline deliverable's path is
   stale at **every** day's build, and starting a new book makes it stale too; without following later
   judgments C1 would almost never act for an exam. Fix round 1 adopted refreshes and switch changes through
   incremental state (judgment-identity markers, withdrawn-block exclusions, sequential transitions, a
   consulted-stale scan), and the scoped verify found four orderings it missed. Fix round 2 replaces all of it
   with: **while the plan's reading block has no reading history, it is whatever a fresh build would choose
   right now.** *Reading history* is a live reading block (a path reading withdrawn unread is none) that
   started, ended or took reading progress (`note_reading_progress`, a prefetched block read in the reader), or
   progress on the staged section since it was staged (the receipt's `staged_progress` snapshot, so a Library
   reading counts; DL2's intent ending of an unread block is none). On a C1 plan the invariant runs before DL2's
   intent ending, so an unread reading on a paused source moves to the fresh choice, and a reading with history
   keeps DL2's ending (fix round 3). With history nothing moves. Without, the fresh choice (memoized on a
   whole-database fingerprint)
   is compared with the staged reading: equal, nothing is written; different, the unstarted block is withdrawn,
   the new reading staged, the receipt's v2 keys updated to the latest choice and one `moves` entry added
   (reason `deliverable_path_moved` with C1 on, `deliverable_path_off` with C1 off and RW7b on,
   `reading_path_off` with both off). A plan that closed by itself only for want of a reading reopens when the
   fresh choice is one (live blocks only). A plan built with either switch off carries no v2 receipt and follows
   RW7b's own rule, so G-C4 holds. A choice made while protection or a path could not be read stands for that
   read but is never memoized.
9. **One block reason.** Any path withdrawal ends the block with `reading_path_off` (so
   `PlannedBlock.withdrawn_path_reading` keeps its meaning); the move's own reason distinguishes
   `deliverable_path_moved`, `deliverable_path_off` and `reading_path_off`.
10. **The block's "why" reuses RW7b's words** ("prerequisite on your reading path"): no DTO or frontend change.
11. **The learner context C0b deferred to C1** (RW1c's "that didn't help" rows, kept comparisons, DL1's minute
    estimates) is **already fed to the path judge**: C0b's Codex review fix F11 added all three
    (`deliverable_path.learner_context`: `didnt_help`, `kept`, `minutes_available` from DL1's daily budget times
    the days left, section minutes at `plan.read_words_per_minute`). Nothing to add; C0b's open item is closed.

## Constants

None new. `PLANNED_LABELS` reuses RW7b's; the once-a-day bound is the plan's own day (`engine.local_date`), a
structural cadence from the spec, not a parameter. The only new config key is the boolean kill switch, classified.

## Persisted meaning

A serving change only: which section the reading block opens. Never evidence, FSRS, the projection or replay
(replay never reads a plan's reading). The activation is the idempotent projection rebuild of the same namespace.
`test_a_shadow_rebuild_is_zero_and_never_reads_a_deliverable_path`: live database unchanged, summary
`{mastery: 0, facet: 0, schedule: 0}`, and no deliverable path read.

## Tests (`tests/test_curriculum_c1_plan_follows_path.py`, 37 tests; every model a fake)

Fail-first: with `deliverable_plan_active` forced to False, 21 of the 37 fail (every behaviour test; the G-C4
parity tests through their "on differs" check); the 16 that pass are the upgrade chain, the pure refresh function,
the no-deliverable and head-fixture parities and the shadow rebuild.

- The successor: one constant after mvp-0.38, the latest, defaults snapshots; the switch on by default,
  classified, and off with either curriculum switch, either RW7b switch, the plan off, or below the tag.
- What changes: the reading block opens the path's first unfinished line (a prerequisite in the notes) where RW7b
  opens "Chapter 5"; the receipt v2 (predecessor = RW7b's choice, the rows read, the line chosen); **across books
  in path order** (Lay's 5.2 next, a book the predecessor never reads); nothing left → RW7b's choice; the nearest
  deliverable with a fresh path is followed (a nearer one with no depth passed over and recorded).
- Filters first: the exam predicate (spans and whole extractions), DL2's `reading_allowed` (unit level and a real
  `set_intent` pause through the build), U4's front-matter rule (and not with DL1's order), a section held out
  since the judgment, a withheld path (plans nothing), an unreadable path (RW7b's choice, recorded).
- Stale: not followed, the receipt says `stale` with both keys; the daily refresh is quiet (offers suppressed
  inside the fake), runs before the build when inline, once a day (again the next day); the plan down → RW7b,
  `stale`, nothing relayed; the refresh function judges only a stale path and stops when switched off; refresh
  adoption (recorded once, then the switch still reaches the plan).
- G-C4: off (`plan_uses_path`, `curriculum.enabled`) every plan build is RW7b's byte for byte, the served plan,
  Today and the next item included (with RW7b's own path judged so its v1 receipt is present); no deliverable in
  play → RW7b's; the head fixture copy (`migration_head_228`) on, off and curriculum-off equal the predecessor's;
  turning C1 off after the build → RW7b's reading (`deliverable_path_off`); both paths off → the order's
  (`reading_path_off`, recorded once); the same section → RW7b's own label.
- The upgrade: from mvp-0.9, 0.32, 0.37, 0.38; the bare upgrade; refusal before the chain; an interrupted
  activation completed by the next CLI command, by the sidecar's open and by the upgrade; a failure after the
  rename leaves the predecessor and no journal; an interrupted mvp-0.38 activation then `--to mvp-0.39`; without
  a completion an attach refuses and the upgrade still completes the earlier journal.

## Gate (this step; the full suite runs once at landing)

Run on the stage tip (worktree `learnanything-ad1`), every test command inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, the big run also under
`flock /tmp/learnloop-fullsuite.lock`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** |
| `uv run pytest -n 6` on the 197 targeted files below | **9624 passed, 24 skipped, 3 xfailed, 0 failed** (45 min 52 s) |
| `tests/test_curriculum_c1_plan_follows_path.py` alone (iteration) | 37 passed |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` (config changed: one new leaf) | 1078 effective leaves in 75 sections, 357 table notes; **errors []**; vault valid (1166 notes, 1164/1164 reachable). The prose counts in `Configuration.md` and `Database.md` were moved from 1077 to 1078 by hand |
| `tests/cli_help_snapshot.json` | regenerated (`python tests/test_cli_help_snapshot.py --write` under `env -i`): only `upgrade` moved |

Not run, by the rule: the full suite, the whole durability lane (no migration, DB or connection code changed), vitest,
`npm run frontend:build` and `cargo check` (no frontend or `src-tauri` change).

The targeted files: every test file that exercises the daily plan (engine, reading, records, the sidecar's plan
RPCs, RW7b's reading paths), every file pinning the successor chain or the latest version, every deliverable /
section-coverage file, every file reading the activation journal, the defaults snapshots or the parameter
registry, and the contract tests (CLI help snapshot, mobile allowlist, desktop RPC contract, architecture,
table roles, coordinated migrations, tracked fixture databases, E0 isolation, config refactor):

<details><summary>197 files</summary>

- `tests/test_ad1_codex_rereview_fixes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_migration.py`
- `tests/test_ad1_outside_and_cli.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r5.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad23_intent_compose.py`
- `tests/test_ad23_inversion.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_pool_membership.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_ad2_serving.py`
- `tests/test_ad3_monitoring.py`
- `tests/test_ad3_reading.py`
- `tests/test_ad3_relatedness.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_denial_log.py`
- `tests/test_ad_epoch.py`
- `tests/test_ad_guard_offer_receipts.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_guard_reachable_reads.py`
- `tests/test_ai_config.py`
- `tests/test_approach_maps_schema.py`
- `tests/test_architecture.py`
- `tests/test_assumed_known.py`
- `tests/test_attempt_content_state_successor.py`
- `tests/test_batch3_landing.py`
- `tests/test_block_chooser_interface.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_cold_retry_reschedule.py`
- `tests/test_compare_keep_switch_off.py`
- `tests/test_config_refactor.py`
- `tests/test_constraint_engine.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_coverage_on_extract.py`
- `tests/test_curriculum_c0b_landing.py`
- `tests/test_curriculum_c1_plan_follows_path.py`
- `tests/test_daily_plan_admission.py`
- `tests/test_daily_plan_build.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_kill_switch.py`
- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_daily_plan_reading.py`
- `tests/test_daily_plan_reentry.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_daily_plan_review_regressions.py`
- `tests/test_daily_plan_rpc.py`
- `tests/test_daily_plan_split.py`
- `tests/test_deliverable_codex_review.py`
- `tests/test_deliverable_curriculum_migration.py`
- `tests/test_deliverable_path.py`
- `tests/test_deliverable_rpcs.py`
- `tests/test_deliverable_scope.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_dl2_rw4b_keyed_pick_check.py`
- `tests/test_duration_estimates.py`
- `tests/test_e0_isolation.py`
- `tests/test_evsi_staged_binding.py`
- `tests/test_exam_protection_identity.py`
- `tests/test_exam_protection_landing.py`
- `tests/test_exam_protection_review.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figures_show_me_codex_review.py`
- `tests/test_figures_switch_off.py`
- `tests/test_grading_cli.py`
- `tests/test_help_assists_schema.py`
- `tests/test_hint_contracts.py`
- `tests/test_hint_h2a_review_round2.py`
- `tests/test_instructional_layering.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intent_codex_review.py`
- `tests/test_intent_exclusion.py`
- `tests/test_intent_fix_round4.py`
- `tests/test_intent_fix_round5.py`
- `tests/test_intent_fix_round6.py`
- `tests/test_intent_fix_round7.py`
- `tests/test_intent_goal_deadline.py`
- `tests/test_intent_orchestrator_rulings.py`
- `tests/test_intent_plan.py`
- `tests/test_intent_recall_targets.py`
- `tests/test_intent_resolution.py`
- `tests/test_judge_routes.py`
- `tests/test_kinship_feature.py`
- `tests/test_learner_claim_application_migration.py`
- `tests/test_learner_claim_superseded_migration.py`
- `tests/test_learner_pick_proposal.py`
- `tests/test_learner_report_superseded.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_library_asks_migration.py`
- `tests/test_library_exercises.py`
- `tests/test_lp_claim_fixes.py`
- `tests/test_lp_claim_fixes_rereview.py`
- `tests/test_lp_claim_fixes_review.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_mcp_tools.py`
- `tests/test_method_explicit_landing.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_mvp010_upgrade.py`
- `tests/test_mvp011_upgrade.py`
- `tests/test_mvp013_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp022_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_open_world_gate.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_plan_determinism_landing.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_follows_path.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_pr4_superseded_claims_landing.py`
- `tests/test_rbeq_pr2_landing.py`
- `tests/test_reader_ca2_fix_orchestrator.py`
- `tests/test_reader_ca2_one_ask.py`
- `tests/test_reader_ca3_landing_ca5a.py`
- `tests/test_reader_ca4_landing.py`
- `tests/test_reader_ca4_table_by_point.py`
- `tests/test_reader_ca5a_find_section.py`
- `tests/test_reader_intent.py`
- `tests/test_reader_rw2b_review.py`
- `tests/test_reader_rw3a_landing.py`
- `tests/test_reader_rw3b_migration.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_reader_rw4b_admission_idempotency.py`
- `tests/test_reader_rw4b_fix6.py`
- `tests/test_reader_rw7a_migration.py`
- `tests/test_reader_tutor_switch_off.py`
- `tests/test_reading_paths.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_equivalence_review.py`
- `tests/test_recurrence_commands.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_registry_audit.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_required_method_grading.py`
- `tests/test_reread_safety_landing.py`
- `tests/test_retrieval_spaces_migration.py`
- `tests/test_router_card.py`
- `tests/test_router_g1_feasibility.py`
- `tests/test_router_g4_restraint.py`
- `tests/test_router_g7_fallback.py`
- `tests/test_router_presentations.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2b_agreement.py`
- `tests/test_router_r2bc_landing.py`
- `tests/test_router_r2b_requests.py`
- `tests/test_router_r2b_serving.py`
- `tests/test_router_r2c_retrieval.py`
- `tests/test_router_r2c_teach_back.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_router_why_copy.py`
- `tests/test_rw2c_switch_off.py`
- `tests/test_rw2d_receipts_migration.py`
- `tests/test_rw7b_codex_review_fixes.py`
- `tests/test_rw7b_fix_round2.py`
- `tests/test_salience_firewall.py`
- `tests/test_section_coverage_migration.py`
- `tests/test_section_coverage.py`
- `tests/test_section_coverage_review.py`
- `tests/test_section_coverage_rpcs.py`
- `tests/test_sensitivity_certificates.py`
- `tests/test_serve_eligibility.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_source_exercise_rpcs.py`
- `tests/test_source_roles.py`
- `tests/test_t1_batch_origin_migration.py`
- `tests/test_table_roles.py`
- `tests/test_teacher_te0_confidence_events.py`
- `tests/test_teacher_te0_review_fixes.py`
- `tests/test_today_headline.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_ux_phase1_landing.py`
- `tests/test_ux_phase1_round2_rereview.py`
- `tests/test_ux_phase1_round2_review.py`
- `tests/test_ux_phase1_usability_round1.py`
- `tests/test_ux_phase2_shell.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_voi_merge_composition.py`
- `tests/test_voi_stopping.py`
- `tests/test_voi_v2.py`

</details>

## Renumbering at landing

If RW6b part 1 (`mvp-0.39`) lands first, C1 becomes `mvp-0.40` after it: change the one constant, the upgrade's
`PREDECESSOR` / `_upgrade_to_predecessor` / completion import (RW6b's upgrade module), the CLI branch and help, the
runtime/sidecar completion import, the defaults snapshot key and the recomputed fingerprints (both successors'
keys present in every snapshot), the chain pins in the successor tests (the files edited here, plus RW6b's own),
the CLI help snapshot, the spec's as-built note and this record.

## Open questions

1. Should C1 stand on its own switches, independent of RW7b's `reading_paths.plan_uses_path` (decision 1)?
2. Should the deliverable branch read only as-you-read books, as DL1's order does (decision 2)?
3. Following later judgments and switch changes on a built plan (decision 8's invariant) is beyond the spec's
   letter; the alternative is a synchronous re-judgment before the day's first build (blocking the app for one
   model call). Keep the invariant?
4. A path goes stale whenever the learner starts a new book (C0b's key names books read); the daily refresh or a
   Guide open re-judges it. Should "books read" leave the key (a C0b change) so C1 follows longer between days?
5. A CLI-built plan never starts the refresh (decision 7). Acceptable?

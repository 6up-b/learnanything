# Follow-ups Nov 1c

Stage `followups-nov1c`, branch `fix/followups-nov1c` (base `a2c26e4525`, worktree `learnanything-ad1`).

This stage builds five queued follow-ups. Each has fail-first tests named after the review or ruling it closes.

- **No migration, no successor, no config key. Kill switches unchanged** (`[notes] enabled`, tend absent,
  `curriculum.enabled`; the fold skip has no switch: it changes when the fold runs, never what it computes).
- No new module constant with a numeric value (nothing for `params/parameter_registry.py`).
- Nothing here changes persisted meaning (scoring, scheduling, projections). (B) changes only whether a reload
  recomputes a cache that a recompute would leave unchanged. Rebuild/replay equivalence and shadow are unchanged
  (below).
- **No paid or live model call was made.** Every model in the tests is a fake. The owner's real `tend` was never run
  and no note of the owner's was opened: every notes test uses the FAKE `tend` of `tests/notes_fixtures.py` over
  synthetic notes. Python outside pytest (`lint-imports`, the reference generators, the timing script, one
  `learnloop rebuild --shadow`) ran only on a synthetic vault under the worktree's gitignored `fixtures-local/`, under
  `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and `LEARNLOOP_NOTES_TEND=off`. No
  owner vault, `~/.config/learnloop` or `fixtures/{linear_algebra,probability,arxiv_v2}` was opened.
- Cost: $0.

## A. C2 ruling R6: monotonic read tokens for hand-linked note snapshots

Ruling R6 (`curriculum-c2-notes-linked.md`): "Queued follow-up: give each read a monotonic token taken at read start
and publish by token order, with unchanged reads advancing the fence." It closes the two concurrent-refresh orderings
of the round-3 scoped verify (job `20261101-102907-K457GP`):

1. two refreshes observe the same marker revision; the older read writes first; the newer read's compare-and-set then
   fails, so the older text shows;
2. an unchanged read takes the equality shortcut and writes nothing, so it does not fence off an older refresh still
   in flight, which then publishes its older text.

### What changed

- `note_links._read_token()`: each read of a note made to show it (`link_by_hand`, `refresh_learner_links`) takes a
  ULID when it starts, before tend is asked. A ULID sorts after every ULID this process minted before it (the ids
  module's monotonic rule) and, across processes, by the wall clock's millisecond.
- `note_links._show_read(connection, note, token, now)`: inside the caller's write transaction it reads the note's
  **fence** (`store.current_fences`: the newest current-snapshot marker's read token, `""` with none or with a marker
  written before R6) and publishes only if its token is newer. It then always appends a marker naming its snapshot,
  carrying `{"read_token": token}` in the marker's `rationale`. An unchanged read therefore publishes a marker naming
  the snapshot already shown, which advances the fence. Since markers are appended only in token order, the newest
  marker is the newest read.
- `refresh_learner_links`: the equality shortcut is gone. An unchanged text goes through `_show_read` too (fencing),
  and it counts as refreshed only when the shown snapshot changed. The F9 rule (a link hidden meanwhile is not
  refreshed) is unchanged.
- The store (`db/stores/learner_notes.py`): `_markers` reads each marker's token; `current_revisions` (the rowid
  compare-and-set) is replaced by `current_fences`; `current_notes` is unchanged (newest marker in append order).
- No schema change: the token rides in the existing `judgment_ledger` marker row (R4 put the markers there).

### Tests (fail-first)

`tests/test_notes_linked.py`:

- `test_r6_two_concurrent_refreshes_resolve_to_the_newest_read`: two refresh threads on their own repository
  connections. The older one reads B and waits until the newer one (started after the note changed to C) has read C.
  The newer one waits until the older one has written. Before R6 the newer refresh returned 0 and B stayed shown.
  Now both publish (`{"older": 1, "newer": 1}`) and C shows.
- `test_r6_an_unchanged_read_fences_off_an_older_refresh_in_flight`: A shows. A refresh reads B slowly. Meanwhile the
  note changes back to A and a newer refresh reads A (unchanged). Before R6 the older refresh then published B. Now it
  writes nothing, A shows, no B snapshot is stored and no link row is written.

On base code (the two source files restored from `a2c26e4525`) both failed for these reasons: the newer refresh
returned 0, and B was published. With the fix all 55 tests of `test_notes_linked.py`, `test_notes_never_read.py` and
`test_learner_notes_migration.py` pass, including the round-3 F13 regressions.

### Notes

- A refresh now appends one marker per kept hand link per run, unchanged or not. The background run refreshes at
  most once a local day per path (plus waits). The growth is one small `judgment_ledger` row per hand-linked note per
  run.
- Across processes the token order is the wall clock's millisecond. Two processes reading the same note in the same
  millisecond are ordered by the random part. The R6 effect (one edit stale until the next refresh) is the worst case.

## B. Facet fold skip on unchanged inputs

Fix 2 of the facet-table rewrite investigation (`followups-oct31.md`), queued by ruling R2 of the substrate facet
write-on-change landing: "Fix (2) (fingerprint skip of the fold) ... queued follow-ups".

### What changed

`substrate/canonical_projection_rollout.refresh_canonical_projection_on_startup` (desktop load and every reload):

- With a current projection baseline, it takes `fold_inputs_fingerprint(vault, repository)` **before** the fold reads
  anything. It skips the fold when the fingerprint equals the one remembered for this database. After a fold it takes
  the fingerprint again. Only if the two are equal (the fold, and everyone else, committed nothing in between) is the
  fingerprint remembered.
- **The fingerprint** covers every input the fold reads:
  - the whole database: `PRAGMA data_version` of a read-only watcher connection kept open on the vault database. It
    changes whenever any other connection commits, in this process or another. Also the watcher's own
    `total_changes` and the file's device and inode (a database restored at the same path starts over). There is no
    list of the tables the fold reads, so a commit to any table forces the next fold, the outputs included (a
    half-finished replay, a hand edit). This is `daily_plan.reading_choice`'s watcher rule;
  - the loaded vault: a digest of exactly the `LoadedVault` fields the fold reads (`FOLD_VAULT_FIELDS`: root, the
    whole config, practice items, default rubrics, facet aliases), each dumped whole;
  - the code: the algorithm version and `CANONICAL_PROJECTION_VERSION`.
- **Why a remembered fingerprint is safe.** It is remembered only when the fold committed nothing. The cache then
  holds exactly what that fold computed from exactly those inputs, so a later fold with the same fingerprint would
  compute the same rows and write nothing (the writers are write-on-change). Nothing the fold reads depends on the
  clock (only write timestamps do).
- A fold that wrote is not remembered (a new attempt's projection, the baseline stamp, a restored cache): the next
  start folds again, finds nothing to write, and is remembered.
- A projection-version boundary (no current baseline) always folds and stamps, as before.
- **Nothing persisted** (in-process memo; no table, no migration). The first start of every process folds, which
  keeps the mvp-0.7 self-heal of the comment in `SidecarContext.load`.
- `SidecarContext.close()` and a vault switch call `forget_fold_memo()`, which closes the watcher.

### Tests (fail-first): `tests/test_canonical_projection_fold_skip.py` (new, 16 tests)

- A no-op refresh skips the fold and commits nothing (`data_version` unchanged over three refreshes). Folding
  afterwards writes nothing, so the skipped cache equals a fold's.
- The same with production durability and WAL (`durability` marker); a commit seen through the WAL forces the fold.
- `SidecarContext.reload(maintenance=False)` skips the fold after nothing happened, and folds after a new attempt.
  `close()` forgets the memo.
- The first refresh of a process always folds.
- Each input class forces the fold:
  - a new attempt;
  - any committed write anywhere (an unrelated table);
  - a tampered cache, where the restoring fold is not remembered and the next one is;
  - a database restored at the same path (another inode);
  - a config change (`evidence.certification.max_groups_per_attempt`);
  - a practice item's rubric change;
  - a default rubric change;
  - a facet alias change;
  - a projection version change (it also stamps);
  - a fold racing a commit is not remembered.
- `test_the_fold_reads_no_vault_field_its_fingerprint_leaves_out[False|True]`: the refresh and the fold run over a
  `LoadedVault` whose every field outside `FOLD_VAULT_FIELDS` raises on any access. One variant also runs the
  capability-residual activation's body.

On base code all 16 failed: the fold was never skipped ("an unchanged third refresh must skip the fold": 3 folds, not
2). All 16 pass in the plain lane and with `--durable-sqlite`.

### Reload timing (before/after)

Synthetic vault on btrfs under the worktree's gitignored `fixtures-local/nov1c-timing/` (the timing script is in the
stage scratch directory, not committed). Built with `create_placement_vault` + `add_followup_item`, 13 items, 300
self-graded attempts, production WAL + `synchronous=FULL`. `SidecarContext.load(maintenance=False)` with
`prepare_new_revisions` stubbed. Medians of 15 rounds each, runs alternated before/after on the same machine (load
average about 10 from other agents' work):

| run | projection alone | startup refresh | `reload(maintenance=False)` | fingerprint |
|---|---:|---:|---:|---:|
| before 1 | 100.8 ms | 118.9 ms | 227.8 ms | |
| after 1 | 90.7 ms | 15.0 ms | 108.2 ms | 0.59 ms |
| before 2 | 84.5 ms | 105.7 ms | 192.9 ms | |
| after 2 | 90.4 ms | 17.9 ms | 111.0 ms | 0.52 ms |

The skipped refresh costs the vault mutation lock, the baseline read and the fingerprint (about 0.5 ms here). A
reload saves the whole fold, about 90–105 ms on this vault, and the saving grows with the ledger. The fingerprint's
vault digest grows with the number of practice items (one pydantic dump each).

### Equivalence and shadow

- Rebuild/replay equivalence: `test_rebuild_equivalence.py`, `test_rebuild_equivalence_review.py`,
  `test_rebuild_orchestrator.py`, `test_replay.py`, `test_canonical_projection_rollout.py` and
  `test_facet_state_write_on_change.py` pass unchanged (targeted run below). Replay calls
  `project_canonical_facet_state` directly, never the startup refresh, so the skip cannot reach it.
- `learnloop rebuild --shadow --json` on the synthetic vault after the timing runs (loads and skipped reloads):
  **facet 0 / mastery 0 / schedule 0 changed** (11 facet, 4 mastery, 10 schedule rows unchanged), live database
  sha256 unchanged.

## C. Settings: hidden notes with show again (C2 ruling R5)

Ruling R5 ("a list of hidden notes in Settings is queued as a follow-up") and C2 open question 4 (a hidden link's undo
after the reading changes).

### What changed

- `note_links.hidden(vault, repository)`: the learner's standing hides (their newest row per (note, topic) or
  (note, passage) is `rejected`), newest first. Each names its note (title, heading, date label, Pocket Notes label;
  **never its text or where it lives**), where it was linked (the topic's title, else the reading › section) and who
  linked it. No tend call, no model call.
- RPC `notes.hidden` (desktop only: `NOTES_RPCS`, pinned in `tests/test_mobile_allowlist.py`; Rust passthrough;
  `api.notesHidden`, `HiddenNoteDto`). It refuses with the notes switched off or tend absent, like every notes RPC.
- Settings (`screens/reader/HiddenNotesSettings.tsx`, mounted after "also in your books"): a "hidden notes" row per
  hidden link with **show again**, the existing `notes.decide keep` (a `learner_card` verdict reversing the hide).
  Honest copy: a link the learner made "is shown again beside that passage"; a model's link is "shown again wherever
  LearnLoop's model still links that note" (F6: a keep is a decision only). It is absent while nothing is hidden or
  the notes are off.

### Tests

- `tests/test_notes_linked.py::test_r5_settings_lists_the_hidden_notes_and_show_again_unhides_through_decide`:
  - a model link and a hand link are hidden, and both are listed newest first, with labels and where they were
    linked;
  - no note text, notes path or Pocket Notes path appears in the list;
  - listing calls neither tend nor a model;
  - show again goes through `notes.decide keep`: the hand link shows again beside its passage, and the model link
    shows again on the path line;
  - the ledger's `learner_card` verdicts read `rejected, rejected, accepted, accepted`.
- `test_switched_off_every_rpc_refuses...` and `test_the_rpcs_are_registered_and_desktop_only` now include
  `notes.hidden`.
- Vitest `screens/reader/hiddenNotesSettings.test.tsx` (5 tests): the list (never the text), show again per link
  with its copy, a failed show again keeps the row, nothing when nothing is hidden or the RPC refuses.
- Fail-first: on base, `notes.hidden` does not exist and the component does not exist.

## D. Reader selection action "scope my deliverable from this passage"

### What changed

- `screens/reader/ScopeFromPassage.tsx`, given to `NotesRail` as `scopeAction`. The capture panel shows it after
  EXERCISES, inside the same `!offline && !protectionMessage` guard as the other model actions, so it never appears
  on a protected selection. It needs a deliverable (`curriculum.deliverables`; absent while the curriculum is off) and
  the selection's spans. It never sends an empty span list, which would read a syllabus whole (C3).
- Pressed, it calls the existing `curriculum.set_scope` with `kind: "passage"`, the main reading's `extractionId`,
  the selection's spans and `context: {"from": "reader_selection"}`, then shows the resolution's summary ("For
  midterm: 3 topics from your books") or the server's notice. With several deliverables there is one button each,
  named.
- Honest copy (as revised by review F3, `followups-nov1c-codex-review.md`): "This passage joins what you've already
  given your deliverable (its description, earlier passages, a syllabus). LearnLoop's model reads them all again and
  updates its scope, which can add topics or drop some. Review them in the Guide." This matches
  `deliverables.resolve`, which rereads every scope input in order, a later input refining an earlier one.
- **Refusals.** The existing guard (`deliverables.passage_texts`) refuses exam material, a reading held back, a span
  without teaching authority and an unreadable predicate. It refuses an exam-role reading or a held-out unit inside a
  teaching book with `exam_material` and `EXAM_REFUSAL`, before anything is written. The learner sees that message
  (`onError`).

### Tests

- Vitest `screens/reader/scopeFromPassage.test.tsx` (7 tests):
  - the exact `set_scope` call and the summary shown;
  - one named button per deliverable;
  - the server's exam refusal reaches the learner in its words;
  - nothing offered when the curriculum is off, with no deliverable, or with no spans;
  - the Notes rail shows the slot with the other model actions, never on a protected selection or offline.
- `tests/test_deliverable_rpcs.py::test_the_reader_selection_action_scopes_from_the_selected_passage_only`:
  - the action's exact call on a teaching passage records the input (spans `["s2"]`, the context, no text);
  - the resolver's prompt carries the selected span's text and no other span of the book;
  - the same call on the exam reading (`ext_exam`) and on the held-out unit of `ext_lay` is refused (`exam_material`,
    `EXAM_REFUSAL` verbatim) with no table changed and no model call.
- Fail-first: the component and the slot did not exist on base. The backend test pins the existing guard, which this
  action relies on (it passes on base by design).

## E. Router card provenance check for reading-derived gaps

The router card's open problems show a named gap's learner words (G5). They were withheld only by the shared leakage
rule over the gap's own answer and item. A gap named from a reading was written on a passage. That reading could be a
question asked in the Reader, an active-reading answer or a figure prediction. The rule never checked that passage, so
a question asked on an exam paper's passage reached the router model in the learner's words. The chat's read model
already checks recorded source refs (`learner_context`, `PastWork.source_reason`). The card did not. This is
exam-material protection, not privacy: per the owner (2026-11-01), learner Q/A/history outside grading is not a
privacy defect.

### What changed

- `diagnosis/text_gaps/provenance.reading_sources(connection, source_kind, source_id)`. It returns the passages a
  reading-derived learner text was written on, and whether they could be read:
  - `tutor_question`: `question_events.source_context` (a question asked outside the Reader names none);
  - `reader_formative`: `formative_record` (the book's passage and cited spans, or a figure's input spans);
  - any other source reads no passage.
- `learner_protection.PastWork.reading_reason(source_kind, source_id)`, in the one protection authority:
  - a passage that is or may be exam or held-out material gives `WITHHELD_EXAM` (`source_reason` →
    `exam_material.source_ref_protected`);
  - a passage that cannot be established (the question or active-reading record is gone), or an unreadable predicate,
    gives `WITHHELD_UNREADABLE` (fail closed);
  - a text written on no reading gives None.
- `daily_plan/router_card._open_problems`: after the existing leakage rule passes, a learner-named gap also takes
  `reading_reason`. A reason keeps the entry and withholds the words. Every other gap shows exactly as before.

### Tests (fail-first): `tests/test_router_card_reading_gaps.py` (new, 4 tests)

- Three Reader questions: one asked on an exam passage, one on a textbook passage, one during practice. All three keep
  their entries. Only the exam one is withheld (`WITHHELD_EXAM`), and its words appear nowhere in the card's open
  problems.
- An active-reading answer on an exam passage is withheld.
- A reading-derived gap whose question or active-reading record is gone is withheld (`WITHHELD_UNREADABLE`).
- An unreadable exam predicate withholds a reading gap's words.

On base all 4 failed (the words were shown). `test_mcp_c1a_landing.py`'s shared-leakage tests are unchanged and pass:
the existing rule runs first, so its reasons are unchanged.

## Gate (this step; the full suites run once in the landing gate)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, with `TMPDIR` in the stage scratch directory. The big targeted run was serialized behind `flock
/tmp/learnloop-fullsuite.lock`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **40 kept, 0 broken** |
| Fail-first on base code (source files restored from `a2c26e4525`, tests from the branch) | A: 2 failed; B: 16 failed; E: 4 failed (each for the reason above); C and D: the RPC and components did not exist |
| `pytest -n 6 tests/test_notes_linked.py tests/test_notes_never_read.py tests/test_learner_notes_migration.py` (after A) | 55 passed |
| `pytest -n 6 tests/test_canonical_projection_fold_skip.py`, plain lane / `--durable-sqlite` | 16 passed / 16 passed |
| **Targeted pytest** `pytest -n 6` over the 279 files below (under `flock`) | **5539 passed, 45 skipped, 8 xfailed, 0 failed** (16:20) |
| Durability lane on the touched files: `pytest -n 6 --durable-sqlite` / `pytest -n 6 -m durability` over `test_canonical_projection_fold_skip.py`, `test_facet_state_write_on_change.py`, `test_canonical_projection_rollout.py`, `test_notes_linked.py`, `test_router_card_reading_gaps.py` | 83 passed / 2 passed |
| `npm install`; `npm run typecheck` | ok; ok (final tree) |
| `npx vitest run --maxWorkers=4` over `scopeFromPassage.test.tsx`, `hiddenNotesSettings.test.tsx`, `splitRails.test.tsx`, `SettingsScreen.test.tsx`, `readerNotes.test.tsx`, `readerCorrespondenceSettings.test.tsx` | **6 files, 35 passed** |
| `npm run frontend:build` | ok |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` (passthrough `notes_hidden`) | ok |
| `db_generate_reference.py` then `db_validate_reference.py` (no schema change; `context.py` line citations moved) | errors `[]` |
| `desktop_generate.py` then `desktop_validate.py` (validator counts bumped for the two new components) | passed: 304/304 TS + 6/6 Rust, ACTIVE=310 (294 entry-build), reproducible byte for byte |
| `validate_vault.py` | passed (1376 notes) |
| `learnloop rebuild --shadow --json` on the synthetic timing vault (`env -i`) | facet 0 / mastery 0 / schedule 0 changed, live sha256 unchanged |

Not run here, by the owner's rule: the full pytest suite, the whole durability lane and the whole vitest run (landing
gate).

**Targeted files (279):** every test file that names the notes modules or RPCs, the canonical projection, its rollout or
the facet tables, the router card, `learner_protection`, the learner-text gaps or their provenance, the deliverables or
`curriculum.set_scope`, or that loads/reloads a `SidecarContext`, plus the contract tests (desktop RPC contract,
mobile allowlist, serializer snapshot, architecture, table roles, coordinated migrations, tracked fixture databases,
registry audit, CLI help snapshot, config defaults, sqlite file copies, shadow, rebuild equivalence and orchestrator,
replay, E0 isolation, public-tip guards): `test_ad1_attempt_columns.py`, `test_ad1_codex_rereview_fixes.py`, `test_ad1_codex_review_fixes.py`, `test_ad1_fix_round4.py`, `test_ad1_fix_round5.py`, `test_ad1_fix_round6.py`, `test_ad23_contract.py`, `test_ad23_fix_review.py`, `test_ad23_intent_compose.py`, `test_ad23_successor.py`, `test_ad2_model.py`, `test_ad2_serving.py`, `test_ad3_dose_arm.py`, `test_ad3_reading.py`, `test_ad3_subject_view.py`, `test_anti_double_count.py`, `test_approach_map_replay.py`, `test_approach_maps.py`, `test_architecture.py`, `test_assumed_known.py`, `test_batch3_landing.py`, `test_canonical_projection_fold_skip.py`, `test_canonical_projection_rollout.py`, `test_capture_desktop.py`, `test_capture_route_recovery.py`, `test_causal_p2_acceptance.py`, `test_characterization_certification_ledger.py`, `test_chatgpt_plan_sidecar.py`, `test_cli_help_snapshot.py`, `test_compare_sources_keep.py`, `test_config_refactor.py`, `test_conjunctive_instruments.py`, `test_coordinated_migrations.py`, `test_coverage_on_extract.py`, `test_coverage_rollup.py`, `test_curriculum_c0b_landing.py`, `test_curriculum_c1_codex_review_fixes.py`, `test_curriculum_c1_fix_round2.py`, `test_curriculum_c1_fix_round3.py`, `test_curriculum_c1_fix_round4.py`, `test_curriculum_c1_fix_round5.py`, `test_curriculum_c1_plan_follows_path.py`, `test_curriculum_c1_round5_followups.py`, `test_curriculum_c3_codex_review.py`, `test_curriculum_c3_exam_scoping.py`, `test_daily_loop_lo_lifecycle_serving.py`, `test_daily_loop_reader_retire.py`, `test_daily_loop_reentry_break.py`, `test_daily_loop_reentry_cap.py`, `test_daily_loop_reference_adoption.py`, `test_daily_loop_start_minutes.py`, `test_daily_plan_composition.py`, `test_daily_plan_kill_switch.py`, `test_daily_plan_reading.py`, `test_daily_plan_reentry.py`, `test_daily_plan_review_regressions.py`, `test_daily_plan_rpc.py`, `test_decider_landing.py`, `test_deferred_regrade.py`, `test_deliverable_codex_review.py`, `test_deliverable_path.py`, `test_deliverable_rpcs.py`, `test_deliverable_scope.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_async_router.py`, `test_diagnosis_card.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_diagnosis_pipeline.py`, `test_dialogue_causal_join.py`, `test_difficulty_band_guards.py`, `test_doctor.py`, `test_e0_isolation.py`, `test_embedding_backfill.py`, `test_error_hunt_items.py`, `test_evsi_router_composition.py`, `test_exam_protection_identity.py`, `test_exam_protection_review.py`, `test_exam_seeding.py`, `test_exam_session.py`, `test_facet_identity_actions.py`, `test_facet_outcome_view.py`, `test_facet_reword_paths.py`, `test_facet_rewords.py`, `test_facet_state_write_on_change.py`, `test_figure_predictions.py`, `test_figures_codex_review.py`, `test_figures_fix_round2.py`, `test_figures_scope_redesign.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_goal_projection.py`, `test_goal_scope_material.py`, `test_grading_cli.py`, `test_grading_support.py`, `test_graph_editor_reads.py`, `test_hint_authored_reveal_ruling.py`, `test_hint_blind.py`, `test_hint_discriminating.py`, `test_hint_evidence.py`, `test_hint_feedback_texts.py`, `test_hint_feedback_widening.py`, `test_hint_h2a_review.py`, `test_hint_h2a_review_round2.py`, `test_hint_h2b_review.py`, `test_hint_kill_switch.py`, `test_hint_outcome.py`, `test_hint_report.py`, `test_hint_service.py`, `test_hint_telemetry.py`, `test_hypothesis_reference_contract.py`, `test_ingest_jobs.py`, `test_ingest_latency_journey.py`, `test_instrument_servability_journeys.py`, `test_integration_daily_loop_field.py`, `test_intent_fix_round4.py`, `test_intent_orchestrator_rulings.py`, `test_intent_rpc.py`, `test_keep_local_retired.py`, `test_km2_activation.py`, `test_km2b_consumer_rekey.py`, `test_km2_canonical.py`, `test_km2_sim_gates.py`, `test_km2_write_path.py`, `test_knowledge_map_text_neighbors.py`, `test_learner_blindness_relax_codex_review.py`, `test_learner_blindness_relax.py`, `test_learner_notes_migration.py`, `test_learner_pick_proposal.py`, `test_learner_read_model_pinning.py`, `test_learner_report_superseded.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`, `test_learner_text_source_widening.py`, `test_library_exercises.py`, `test_lp_claim_fixes_rereview.py`, `test_lp_claim_fixes_review.py`, `test_map_untested.py`, `test_mcp_c1a_landing.py`, `test_mcp_c1a_narrow.py`, `test_mcp_c1a_review.py`, `test_mcp_runtime.py`, `test_mcp_tools.py`, `test_measurement_corrections.py`, `test_measurement_state_labels.py`, `test_method_explicit_landing.py`, `test_migrations.py`, `test_mobile_allowlist.py`, `test_mvp016_upgrade.py`, `test_notes_linked.py`, `test_notes_never_read.py`, `test_observation_ledger_bulk.py`, `test_owner_capture_1025.py`, `test_p0_cutover_mvp08.py`, `test_p0_projection_cutover.py`, `test_pfc_unassessed_readers.py`, `test_pfc_unverified_unassessed.py`, `test_placement_opening_probes.py`, `test_placement_sidecar.py`, `test_plan_determinism.py`, `test_plan_first_transport_grant_scope.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport.py`, `test_plan_first_transport_today_quiet.py`, `test_post_attempt_worker.py`, `test_pr4_superseded_claims_landing.py`, `test_practice_index_adapters.py`, `test_probability_cli.py`, `test_probe_episodes.py`, `test_projection_evidence_polarity.py`, `test_public_tip_guards.py`, `test_rbeq_pr2_landing.py`, `test_reader_active_reading.py`, `test_reader_branches.py`, `test_reader_ca1_as_printed.py`, `test_reader_ca1_astra_codex_review.py`, `test_reader_ca1_astra_fixes.py`, `test_reader_ca1_astra_redesign.py`, `test_reader_ca1_astra_rereview.py`, `test_reader_ca1_codex_review.py`, `test_reader_ca1_unicode_containment.py`, `test_reader_ca2_astra_handoff_recovery.py`, `test_reader_ca2_codex_review.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca5_also_in_books.py`, `test_reader_ca5_landing.py`, `test_reader_followups_successor.py`, `test_reader_formative_texts.py`, `test_reader_pdf_selection.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_reader_rw1b_review.py`, `test_reader_rw3a_landing.py`, `test_reader_rw3b_protection.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_rw4b_admission_idempotency.py`, `test_reader_rw4b_fix6.py`, `test_reader_tutor_retrieval.py`, `test_reader_workbench_rw2a.py`, `test_reading_request_sweep.py`, `test_rebuild_equivalence.py`, `test_rebuild_equivalence_review.py`, `test_rebuild_orchestrator.py`, `test_recall_coverage_interventions.py`, `test_receipt_derivation.py`, `test_receipt_exactness.py`, `test_registry_audit.py`, `test_regrade_contract_replay.py`, `test_regrade_contract_successor.py`, `test_replay.py`, `test_required_method_grading.py`, `test_required_method_round3_review.py`, `test_reread_safety_landing.py`, `test_reread_safety.py`, `test_router_card.py`, `test_router_card_reading_gaps.py`, `test_router_offer_log.py`, `test_router_outcomes.py`, `test_router_p2_bridge.py`, `test_router_probe_ties.py`, `test_router_r1_composition.py`, `test_router_r2a_landing.py`, `test_router_r2a_serving.py`, `test_router_r2b_serving.py`, `test_router_r2c_teach_back.py`, `test_router_reader_activity.py`, `test_route_rules_in_grader.py`, `test_scheduler.py`, `test_scoreboard.py`, `test_secondary_attach.py`, `test_serve_eligibility_review.py`, `test_session_ownership.py`, `test_shadow_rebuild.py`, `test_sidecar_adjudication.py`, `test_sidecar_contract.py`, `test_sidecar_exams.py`, `test_sidecar_goals.py`, `test_sidecar_item_presentation.py`, `test_sidecar_measurement.py`, `test_sidecar_serializer_snapshot.py`, `test_sidecar_trace_and_clarification.py`, `test_sidecar_transport.py`, `test_source_exercise_import.py`, `test_sqlite_file_copies.py`, `test_sqlite_wal.py`, `test_state_sync_scheduling_race.py`, `test_stuck_prompt_composition.py`, `test_stuck_prompt.py`, `test_table_roles.py`, `test_teach_back.py`, `test_teacher_te0_confidence_events.py`, `test_teacher_te0_fix_round2.py`, `test_teacher_te0_review_fixes.py`, `test_tier1_decider.py`, `test_today_headline.py`, `test_tracked_fixture_databases.py`, `test_tutor_promotion_w2.py`, `test_unresolved_cause_gate.py`, `test_ux_phase1_add_source.py`, `test_ux_phase1_connect_ai.py`, `test_ux_phase1_finish.py`, `test_ux_phase1_landing.py`, `test_ux_phase1_review_fixes.py`, `test_ux_phase1_round2_rereview.py`, `test_ux_phase1_round2_review.py`, `test_ux_phase1_usability_round2.py`, `test_ux_phase4_feedback.py`, `test_ux_phase4_landing.py`, `test_vault_watcher_refresh.py`, `test_voi_merge_composition.py`, `test_voi_stopping.py`, `test_workbench_chooser.py`, `test_workbench_discriminate.py`, `test_workbench_in_session_gaps.py`, `test_workbench_text_gaps.py`.

**Test files added or changed:** `tests/test_notes_linked.py` (A, C), `tests/test_canonical_projection_fold_skip.py`
(new, B), `tests/test_router_card_reading_gaps.py` (new, E), `tests/test_deliverable_rpcs.py` (D),
`tests/test_mobile_allowlist.py` (C), `apps/learnloop-tauri/src/screens/reader/hiddenNotesSettings.test.tsx` (new,
C), `apps/learnloop-tauri/src/screens/reader/scopeFromPassage.test.tsx` (new, D).

## Open items

1. **(A) Cross-process ordering is by wall clock.** Two processes refreshing the same note within one millisecond are
   ordered by the ULID's random part. The worst case is still R6's ("one edit stale until the next refresh").
2. **(B) First start per process.** The memo is in-process, so the first load of every desktop session still folds
   once. Persisting the fingerprint would need a table (out of scope: no migration).
3. **(D) The second pane.** The action reads the main pane's selection (`NotesRail` is the main reading's).
   Selections in CA6's side-by-side pane do not offer it.
4. **(E) Reader activity's hypotheses.** `router_reader._open_hypotheses` lists named gaps by id, kind and target
   only (no words), so it needs no passage check. Only the open problems' learner words are checked.

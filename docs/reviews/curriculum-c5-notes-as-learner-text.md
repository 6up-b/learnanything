# Curriculum C5: notes as learner text

**Stage:** `curriculum-c5-notes-as-learner-text`, branch `curriculum/c5-notes-as-learner-text` (worktree
`learnanything-dl2`), base `ea1366fff5` (main: C1 mvp-0.40, Reader through CA6b and the Nov 1/1b follow-ups,
RW5d P2b, C2 notes with migration 229 and head fixture `migration_head_229`, C3 syllabus scoping). **Spec:**
`docs/specs/spec_deliverable_curriculum_v1.md` §10.2 ("read for gaps only by opt-in"), §10.4 (privacy), the §12
C5 row and Q9 (DECIDED 2026-10-25: later and opt-in; off by default; "it only ever steers what to suggest,
never grades you").

**No paid or live call was made**: every model is a fake (`tests/text_gap_fakes.py`'s doubles, C2's
`NoteLinkFake`). **The owner's real `tend` was never run and no note of the owner's was opened**: every notes
test uses C2's FAKE `tend` executable over synthetic notes written into the test's tmp directory
(`tests/notes_fixtures.py`), and `conftest` keeps `LEARNLOOP_NOTES_TEND=off` and
`LEARNLOOP_NOTE_LINK_MODELS=off` for everything else. Every ad-hoc script (the head-fixture rebuild, the
fingerprint recompute, the reference generators) ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault was opened, `~/.config/learnloop` was not read, and
nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`. Tier 2, the
learner-text-gaps precedent: **no successor**.

## What was built

| Piece | Where |
|---|---|
| **Migration 231** (numbered 231: main's head is 229 and learner/data-relax-2 claims 230; the runner is set-based, renumber at landing if needed): `learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` gain `learner_note`, by the FK-safe temp-then-rename rebuild of 208 and 212 under `PRAGMA foreign_keys = OFF` (212's body exactly, with the one kind more: a test normalizes it back to 212 byte for byte). Every row and id kept; the three tables whose FKs name `learner_text_gaps` resolve to the rebuilt one; indexes and append-only triggers recreated with the same definitions. No new table, so nothing new to classify: `table_roles` unchanged (RAW_LEDGER / WORKFLOW), AD's guard never reaches the gap tables (unclassified there, so refused), the notes' own tables stay PROTECTED | `migrations/231_learner_note_source_kind.sql`; `tests/test_learner_note_source_kind_migration.py` (`C5_ALTERED_TABLES`) |
| Head fixture `migration_head_231` (renamed from 229; only 231 applied to a backup-API copy of main's tracked, sanitized 229 head under `fixtures-local/`; rollback mode, header 1/1, integrity ok, FK check empty; exactly the two tables' definitions changed, only `schema_migrations` gained a row; no note text). Every head path moved to 231 (46 test files, the sanitizer script, the two reference scripts); ten "nothing else changed" chain diffs now subtract `C5_ALTERED_TABLES`; three widening/head tests know 231 | `fixtures/migration_head_231/README.md` |
| **The switch** `notes.gaps_enabled` (default **false**: the learner's opt-in, Q9), classified in `parameter_registry`; every one of the 31 defaults snapshots records "Curriculum C5's [notes] gaps_enabled moves it too (off by default: tier-2 learner text, no successor)" and all 31 fingerprints were recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared; a second pass changed 0) | `config/schema.py` (`NotesConfig`), `params/parameter_registry.py`, `config/template.py` |
| **Which notes** (§10.2 "only linked notes"): exactly the links C2 shows, by C2's one rule (`note_links.effective_rows`, factored out of `effective` with no behaviour change): a model's proposal of a topic's current candidate state the learner did not hide, and a link the learner made by hand. A hidden link, an unlinked note, a proposal of a superseded state and a note's older snapshot never feed gaps. The gap's source is the linked **snapshot** (`learner_notes.id`), so a note is read with the text it is linked with now and a changed note (a new snapshot) is a new reading | `source_retrieval/note_gaps.py` (`linked_notes`, `note_text`) |
| **Keyed to what it is linked to**: its topics are the LOs its proposals were judged for, plus the LOs its hand-linked passages are provenance-linked to (`reader_progression.learning_objects_for_span`); the subject they share grounds it. The reader's context: the topics' titles and statements, the linked sections' first blocks read through C0a's protection (`section_coverage.peek`), the note's title, heading and date, and "a handwritten page, transcribed" for a Pocket Notes page. A note linked to protected material (by hand, to an exam unit) is **not read at all** (`NoteWithheld` -> the pipeline's `SourceWithheld`: the job ends skipped, "held out") | `note_gaps.note_text`, `diagnosis/text_gaps/sources.py` (`learner_note_text`) |
| **Tier 2 only**: `learner_note` is in `NON_SERVING_SOURCE_KINDS` (no sooner check, never a weak prerequisite observation for placement's fast track) and the reading writes gap rows, their jobs, ledger verdicts and receipts only: no attempt, grading evidence, FSRS, recall or capability state, probe observation, claim, check advance or commitment. **Never drafted into a new topic**: an unmatched prerequisite named from a note stays unmatched (`never_drafted_from_a_note`; a note is never a generation input, §10.2, §9.3). A matched prerequisite targets the existing LO with no edge (a note has no item). A wrong belief goes to the holding pen as for every tier-2 kind (a hypothesis) | `contract.py`, `pipeline.py` (`_create`) |
| **The ChatGPT plan only, C2's transport rules unchanged** (§10.4; the owner's pending personal-notes question leaves them in force): the note's reading **and every pair verdict** use one client, the notes' plan route (`ai.routing.note_link_judge`, already in `plan_fallback.PLAN_ONLY_TASKS`: never offered OpenRouter, never granted), resolved quietly and kept only when the route resolves to a `chatgpt_plan` profile with no fallback and the client itself is the plan's (`note_reader_client`; injected clients are checked by `provider_type` too). **Never the Decider** (an OpenRouter model; Tier 1's switches do not apply to a note's reading), never the gap judge's own route, **never embedded** (the structural and lexical candidates are judged by the plan), never the drafter. The context model's kind decides. With the plan down, or the route set to another provider, the reading **waits** (`ReadingWaits`): nothing is sent, the job is released with its attempt refunded and read again after the existing `BACKOFF_SECONDS`; it never fails for waiting and the rest of the queue goes on. A note's receipts keep no prompt text (`withhold_receipt_input`, as C2's F3) | `pipeline.py` (`note_clients`, `note_reader_client`, `_READING_NOTE`, `ReadingWaits`), `jobs.py` |
| **The gap row keeps no note text** (`learner_text` is empty for a note; `stored_words`), so no reader of the gap table (the router's learner-state card, the learner context and the MCP server, the diagnoser's history, `learnloop gaps report`) can carry a note's words anywhere; the note stays in its snapshot. The named gap (the model's words) is kept, as for every kind; no write-provenance record (no words stored) | `pipeline.py` |
| **Queueing**: `jobs.enqueue_learner_notes` (a `sweep_backlog` of the new `NOTE_BACKLOG_KINDS`) queues each linked snapshot with no reading yet, and queues again a job skipped while its note was hidden or the switch off, once it is linked again (`store.requeue_skipped_job`). Called when a background link run ends, when the learner links a note by hand or keeps a link (*undo*), when the opt-in is turned on and when the sidecar opens a vault; `learnloop gaps run --backlog` sweeps it too. Switched off the sweep's output is today's (no `learner_note` key) | `jobs.py`, `db/stores/learner_gaps.py`, `learnloop_sidecar/handlers/notes.py` (`queue_note_gaps`), `learnloop_sidecar/context.py` |
| **Settings' opt-in** (§12 C5, Q9): RPC `notes.set_gaps` (desktop only, pinned) writes `notes.gaps_enabled` (`settings_store.apply_config_updates`, then reload); a row in Settings, shown only where the notes are (the contract carries `notes`), off by default: "let my linked notes steer suggestions" with the line "Off unless you turn it on. LearnLoop's model on your ChatGPT plan reads the notes you've linked (never one you hid) for gaps in your understanding. It only ever steers what to suggest, never grades you." | `handlers/notes.py`, `apps/learnloop-tauri/src/screens/reader/NotesGapsSettings.tsx`, `SettingsScreen.tsx`, `api/client.ts`, `api/dto.ts`, `src-tauri` passthrough |
| ***ⓘ where this goes* on the notes surfaces** (UX §4.10) with the opt-in on: the opened notes under a margin mark and a path line say where a note goes, including the gaps line ("…reads a note you linked for gaps in your understanding. It only ever steers what to suggest, never grades you, and a note you hide is never read."); the picker's existing disclosure gains the same line. The prompt contract's `notes.gaps` is present only with the opt-in on, so switched off every surface is C2's exactly | `ReaderNotes.tsx` (`NotesWhereThisGoes`) |
| The `notes` route disclosure names what the opt-in sends (one linked note, its topics' titles and statements and the openings of its passages, plan only, never a hidden note) | `ai/disclosures.py` |

## A note is still never a source, a generation input or evidence

- **The one declared exception** to C2's `notes-are-never-a-source-or-evidence` import contract is the gap
  pipeline's adapter (`diagnosis/text_gaps/sources.py`), which reaches the notes only through
  `source_retrieval/note_gaps.py` (notes code, read-only), lazily and only after the config switch is read.
  `text_gaps` has no `__init__.py`, so it is a namespace package grimp does not graph (import-linter cannot
  see its imports at all: an `ignore_imports` entry is reported unmatched). The exception is therefore pinned
  statically in `tests/test_notes_never_read.py`: no module of the never-read packages other than that adapter
  imports `note_gaps`, the adapter reads `gaps_enabled` before importing it, and no `text_gaps` module names the
  notes' tables or modules. `note_gaps` joins the notes modules in the grimp test (only the sidecar and the CLI
  reach them otherwise). `lint-imports`: 37 kept, 0 broken.
- **Dynamically** (`tests/test_notes_as_learner_text.py`): the reading writes nothing outside the gap tables;
  no draft is asked for; no Decider state is built; the gap row and the ledger carry no note text.

## C5 tests

`tests/test_notes_as_learner_text.py` (14): the kinds (readable, non-serving, the plan-only set); **switched
off byte-identical** (the default is off; the link run queues nothing; C2's prompt contract exactly; with every
note-row read patched to fail, the sweep (today's keys exactly), `enqueue_learner_notes` and the adapter read
none and write nothing; a queued note job is skipped unread; the learner's hide/keep queue nothing); the
pipeline switch holds; **linked only** (only the linked notes' snapshots are queued, idempotently; the
snapshot's text, its topic `lo_eigen`, its subject, its context with the linked section's opening; a Pocket
Notes page labelled); a changed note is read with its new snapshot and the old one is not; **a hidden link is
never read** (skipped "nothing to read", nothing sent) and *undo* queues it again; an unlinked note is never
stored, queued or read; **tier 2 only** (a matched prerequisite: changed tables within the gap tables, every
evidence/mastery/claim/check/commitment table unchanged, no edge, `learner_text` empty, the note's own task
and prompt version, no note text in the ledger or the gap rows; an unmatched one is never drafted and no LO is
created); a note's receipts keep no prompt text; **the plan only** (plan down: `waiting_for_plan`, refunded,
queued for later, nothing sent; a metered reader: refused, nothing sent; plan up: the Decider and the gap
judge's own route are never asked, the reading and the pair verdicts are the plan's); the default reader is
resolved quietly and only on the plan (routing replaced by a double: no real client); **G-C1 for C5** on C3's
exam-scope fixture (every gap reading's context names no exam sentinel, no held-out section and not the
syllabus; the one note that copies a past-paper question carries it only in its own words; a note linked by
hand to the mixed textbook's exam unit is never read); the Settings opt-in RPC writes the switch, queues the
linked notes and, off again, the contract is C2's and a queued job is skipped unread; a vault opened with the
opt-in on queues its linked notes.
`tests/test_learner_note_source_kind_migration.py` (5, one durability): the widening keeps every row and id,
the FKs resolve, triggers and indexes are back, 212's body exactly plus the one kind, nothing new classified,
the head holds 231 in rollback mode with no note gap.
Frontend: `notesGaps.test.tsx` (4): Settings' opt-in off by default with its copy, on and off again, absent
without notes; the margin-mark note says *where this goes* with the gaps line only with the opt-in on, and
without it no disclosure is added.

## Decisions taken here (open to the owner or the landing)

1. **Migration 231, not 230**, because learner/data-relax-2 (running in parallel) claims 230 on
   `help_assists`; main had no 230 when this stage started. The head fixture holds 229 and 231.
2. **C2's transport rules extended to everything a note's reading sends**, not only the note text: the pair
   verdicts (which read the gap as the plan's model named it from the note) also run on the plan client, the
   Decider is never asked, and the named gap is never embedded. Reason: §10.4's "a model reads note text only
   on `chatgpt_plan`" is simplest to keep when nothing derived from a note leaves the plan either. Cost: no
   vector shortlist for a note's gap (structural and lexical candidates only) and no Decider second opinion.
3. **The notes' route** (`ai.routing.note_link_judge`) **is the note reader's route**: one setting says which
   model may read the learner's notes, and it is already plan-only (`PLAN_ONLY_TASKS`). No new route, no new
   disclosure key (the `notes` disclosure gained one sentence).
4. **No creation from a note**: §10.2/§9.3 say a note is never a generation input; drafting a prerequisite LO
   (and its seed item) from a note's gap would be one. An unmatched prerequisite stays unmatched.
5. **The gap row keeps no note text** (`learner_text = ''`): the router's card, the learner context (which the
   MCP server serves), the diagnoser's history and the owner's report read that column and send it to routes
   that are not the plan. The named gap stays, as for every kind (the model's words, as C2 shows its one line).
6. **Beliefs go to the holding pen only as sightings** (superseded by the Codex review, F1): a belief named from
   a note never becomes a new candidate (its statement is the plan's words for the note, and the holding pen is
   read by non-plan judges); it is a sighting of an entry that stands, or a signal only. The gap row keeps no
   model words for a note either. See `curriculum-c5-notes-as-learner-text-codex-review.md`.
7. **A note linked by hand to protected material is not read at all** (rather than read without that passage).
8. **Waiting never fails a note**: plan down, route not the plan, or (Codex review F5) the plan unavailable at
   inference releases the job with its attempt refunded, retried after the existing `BACKOFF_SECONDS` (60 s); the
   drain goes on.
9. **A skipped note job is queued again when its note is linked again** (hidden then *undo*; the switch off
   then on), so a hide never loses the note for good.

## Constants

None new. Bounds reused: `note_links.STATEMENT_CHARS` and `LEAD_CHARS` (prompt bounds), `jobs.BACKOFF_SECONDS`
(the wait before a waiting note is tried again). The switch is the learner's opt-in, classified as structural.
No weight, margin or threshold: which gap a note shows is the model's judgment.

## Gate (this step; targeted, memory-capped)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`, pytest at `-n 6`, vitest `--maxWorkers=4`, one test command at a time, `TMPDIR` outside the
worktree. No live model call; no real `tend`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` (after the contract note, and on the final tree) | **37 kept, 0 broken** |
| Head-fixture set: every test file naming `migration_head_231` or the extended chain lists (46 files) plus the migration test, the widening test, `test_table_roles.py`, `test_tracked_fixture_databases.py`, `test_coordinated_migrations.py` | first run 691 passed, 3 skipped, **13 failed** (the ten chain diffs that did not yet subtract 231's two rebuilt tables); after `C5_ALTERED_TABLES` the ten files plus the migration test: **52 passed** |
| Targeted set (135 files, listed below): every file exercising a changed module (text_gaps pipeline, jobs, sources, judges, contract, the gap store, `note_links`, the notes handler, the sidecar context, config schema, template snapshots, parameter registry, disclosures, plan fallback) and the contract tests (CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, coordinated migrations, tracked fixture databases, public-tip guards, Codex lockdown round 3, plan-first transport) | **2636 passed, 12 skipped, 5 xfailed, 0 failed** (23:09) |
| `tests/test_notes_as_learner_text.py`, `tests/test_notes_never_read.py`, `tests/test_notes_linked.py` on the final tree (with the two tests added after the targeted run started) | **64 passed** |
| Durability lane (`pytest -m durability`) over the head-fixture set and the migration, widening, tracked-fixture, coordinated-migration and table-roles tests | **26 passed** |
| Frontend: `npm install`, `npm run typecheck`, `npm run frontend:build` | ok |
| `npx vitest run --maxWorkers=4` on `notesGaps.test.tsx`, `readerNotes.test.tsx`, `compareKeep.test.tsx`, `SettingsScreen.test.tsx` | **4 files, 37 passed** |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` (`SCHEMA_HEAD` 231; prose leaf count 1106) | errors [] (360 table notes) |
| `desktop_generate.py` then `desktop_validate.py` (pinned inventory: 300 TS / 292 entry-build / ACTIVE 305, one new TSX file) | passed, reproducible byte for byte |
| `validate_vault.py` | passed (1371 notes) |
| Defaults fingerprints | all 31 recomputed with `defaults_fingerprint_for_version`; a second pass changed 0 |

Targeted test files:

- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad23_t1_routes.py`
- `tests/test_approach_maps_schema.py`
- `tests/test_architecture.py`
- `tests/test_attempt_content_state_successor.py`
- `tests/test_batch3_landing.py`
- `tests/test_chatgpt_plan_provider.py`
- `tests/test_chatgpt_plan_workspace.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_codex_lockdown_round3.py`
- `tests/test_cold_retry_reschedule.py`
- `tests/test_config_refactor.py`
- `tests/test_constraint_engine.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_coverage_on_extract.py`
- `tests/test_curriculum_c1_plan_follows_path.py`
- `tests/test_curriculum_c3_exam_scoping.py`
- `tests/test_decider_landing.py`
- `tests/test_deliverable_codex_review.py`
- `tests/test_deliverable_rpcs.py`
- `tests/test_deliverable_scope.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_context.py`
- `tests/test_diagnosis_history_modes.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_embedding_backfill.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figure_predictions.py`
- `tests/test_figure_rich_job.py`
- `tests/test_figure_rich_rpc.py`
- `tests/test_figures_codex_review.py`
- `tests/test_figures_fix_round2.py`
- `tests/test_figures_fix_round3.py`
- `tests/test_figures_fix_round4.py`
- `tests/test_figures_scope_redesign.py`
- `tests/test_figures_show_me_codex_review.py`
- `tests/test_figures_show_me.py`
- `tests/test_figures_switch_off.py`
- `tests/test_grading_cli.py`
- `tests/test_held_grade_composition.py`
- `tests/test_help_assists_schema.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_hint_feedback_widening.py`
- `tests/test_hint_h2b_review.py`
- `tests/test_hypothesis_reference_contract.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intent_orchestrator_rulings.py`
- `tests/test_kinship_feature.py`
- `tests/test_learner_notes_migration.py`
- `tests/test_learner_note_source_kind_migration.py`
- `tests/test_learner_report_superseded.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_learner_text_gaps_flow.py`
- `tests/test_learner_text_gaps.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_learner_text_gaps_review.py`
- `tests/test_learner_text_source_widening.py`
- `tests/test_library_ask_review.py`
- `tests/test_library_asks_migration.py`
- `tests/test_library_exercises.py`
- `tests/test_lp_claim_fixes.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_mcp_c1a_review.py`
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
- `tests/test_notes_as_learner_text.py`
- `tests/test_notes_linked.py`
- `tests/test_notes_never_read.py`
- `tests/test_open_world_gate.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_first_transport_grant_scope.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_plan_first_transport_paid_roles.py`
- `tests/test_plan_first_transport.py`
- `tests/test_plan_first_transport_today_quiet.py`
- `tests/test_plan_follows_path.py`
- `tests/test_probability_cli.py`
- `tests/test_public_tip_guards.py`
- `tests/test_reader_active_reading.py`
- `tests/test_reader_ca2_one_ask.py`
- `tests/test_reader_ca4_table_by_point.py`
- `tests/test_reader_followups_successor.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_reader_intent.py`
- `tests/test_reader_rw1b_review.py`
- `tests/test_reader_rw2b_review.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_reader_rw3b_review_fixes.py`
- `tests/test_reader_tutor_retrieval.py`
- `tests/test_reading_paths.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_equivalence_review.py`
- `tests/test_recurrence_commands.py`
- `tests/test_registry_audit.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_required_method_round3_review.py`
- `tests/test_router_reader_activity.py`
- `tests/test_rw2c_switch_off.py`
- `tests/test_section_coverage_rpcs.py`
- `tests/test_sensitivity_certificates.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_sidecar_close_cancels_jobs.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_source_roles.py`
- `tests/test_t6_followup_composition.py`
- `tests/test_table_roles.py`
- `tests/test_teacher_te0_review_fixes.py`
- `tests/test_tier1_decider.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_ux_phase2_shell.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_workbench_in_session_gaps.py`
- `tests/test_workbench_text_gaps.py`

Head-fixture test files (first run): the 46 files of `git grep -l "migration_head_231|227, 228, 229, 231" -- 'tests/*.py'`.

## Landing notes

- **Migration number.** 231 on main's 229. If data-relax-2's 230 lands first, keep 231 (or renumber if main
  takes 231), rebuild `migration_head_<N>` from main's head with this migration applied, and move
  `C5_ALTERED_TABLES` into any new chain diffs.
- **Expected conflicts:** `config/template.py` (one note per version and the 31 hashes: recompute),
  the head path in ~46 tests and the reference scripts, the chain diffs' altered-table sets,
  `tests/test_mobile_allowlist.py`, `src-tauri` command lists, `api/client.ts` / `dto.ts`, `ReaderNotes.tsx`,
  `SettingsScreen.tsx`, the generated reference notes and the desktop catalog's counts (`desktop_validate.py`:
  300 TS / 292 entry-build / ACTIVE 305).
- **No successor**, no algorithm version, no replayer.

## Open questions

1. **A gap read from a note whose link is hidden later** stays as it was read (every gap row is append-only);
   only future readings stop. The reversals table admits three kinds (`undo_edge`, `undo_creation`,
   `not_this_belief`), none of which fits "you unlinked this note". Should hiding a link also retract the gaps
   read from that note (a fourth reversal kind: another FK-safe rebuild)?
2. **New beliefs from notes.** A note may add a holding-pen candidate (decision 6). Should notes only sight
   beliefs already in the registry?
3. **The owner's pending personal-notes question** (curriculum §10.4, Q5-Q9). C2's rules are kept unchanged
   here; if the owner relaxes them, decision 2 could let the Decider and the embedding see the named gap.
4. **`text_gaps` is not graphed by grimp** (no `__init__.py`): import contracts silently skip the whole
   learner-text-gaps package. Adding the `__init__.py` is outside this stage (other contracts would start to
   apply to it); a later architecture pass could.

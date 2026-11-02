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

## Landing onto main

Branch `curriculum/c5-notes-as-learner-text` (worktree `learnanything-dl2`), from `67fe8fcc7d`. The orchestrator
fast-forwards and pushes. Every Python or CLI run outside pytest ran under `env -i` with an empty `HOME`, `CODEX_HOME`
and `LEARNLOOP_CONFIG_DIR`, and `TMPDIR` outside the worktree. pytest, vitest, npm and cargo ran in
`systemd-run --user --scope`: the full suite at 10G under `flock /tmp/learnloop-fullsuite.lock`, the rest at 5G, and
vitest with `--maxWorkers=4`. No live model call was made. The owner's real `tend` was never run and no note of the
owner's was read: every notes run used C2's FAKE `tend` over synthetic notes. No owner vault was opened: only fresh
backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035` were used.

### Step 0: note jobs never reuse a checkpointed reading (`dfb053fddb`, `236a323c92`)

This is the orchestrator's structural simplification under the stuck-loop rule. Codex (job
`20261101-190354-nKrEQg`) reopened F3 a third time: a note job's checkpointed reading and decision (the payload's
`reading`/`decided`) were reused on retry after the note's inputs changed, so the protected passage's sentinel
reached a pair request. Now:

- `contract.NOTE_UNCHECKPOINTED_FIELDS = ("reading", "decided")`.
- `pipeline._decide` neither reads nor writes either field for a note. Every attempt reads the text as prepared from
  the current links, with a fresh plan call (unmetered).
- `process_learner_text` drops both fields from a note's incoming progress, and its `checkpoint` filters them out.
- `process_next_gap_job` drops legacy fields from a note job's progress and from its stored payload.
- `store.requeue_skipped_job` clears them on requeue (`json_remove`).
- Every `NoteGate` check is kept.

This also resolves the earlier open item: the plan's reading of a note is no longer stored in the job checkpoint.

The regression tests were written first, from the exact reproduction, and failed on `67fe8fcc7d`. With the payload
assertion removed, the first test failed because the `learner_gap_same_prerequisite` request carried
`PASSAGE-SENTINEL-c5-L0`. The tests:

- `test_step0_a_checkpointed_note_reading_is_never_reused_after_its_inputs_change`;
- `test_step0_a_legacy_checkpointed_note_reading_is_cleared_on_requeue_and_ignored_on_retry[queued|skipped]`.

After the fix:

- C5, notes and matching tests: 94 passed;
- text-gaps neighbours: 277 passed;
- durable C5: 30 passed;
- lint-imports: 37 kept.

`236a323c92` corrects a comment and the codex-review record: the plan's `learner_gap_kind` verdict rationale in
`judgment_ledger` still names the gap (open item below). The codex-review record carries the orchestrator ruling.

### Merges

| Commit | What |
|---|---|
| `a8455f1b6e` | Merge of main `a2c26e4525` (learner-blindness relax, RW5d P2 sketch compartment). `config/template.py`: 31 snapshot hunks, main's blindness-relax note and C5's note both kept, every fingerprint recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`, second pass 0. `src-tauri/src/main.rs`: main's file with `notes_set_gaps` added after `notes_decide`. `desktop_validate.py` composed to 303 TS / 6 Rust / entry-build 293 / ACTIVE 309. The parameter registry auto-merged with both sides' entries. Generated references: main's side, regenerated in `3554efeed4` (1110 leaves). |
| `20be0dd94c`, `4000d5a73c` | Merge of main `c0017b5740` (learner data-relax 2, **migration 230**, head `migration_head_230`). **The migration stays 231.** `fixtures/migration_head_231` was **rebuilt from main's sanitized `migration_head_230/state.sqlite`** with only 231 applied: a backup-API copy under `fixtures-local/landing-c5/head231`, `apply_migrations` under `UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header 1/1), `integrity_check` ok, `foreign_key_check` empty, then copied into place with the backup API, with no companion files. Against 230's head, only the `learner_text_gaps` and `learner_text_gap_jobs` definitions changed, and only `schema_migrations` gained a row (231). The companion files are byte-identical to main's, and the README gains a C5 section above data-relax 2's. Git records the rename `migration_head_230 -> migration_head_231`. The head paths, `SCHEMA_HEAD` (231), the chain lists (`[..., 229, 230, 231]`) and the altered-table sets (`C5_ALTERED_TABLES \| DR2_ALTERED_TABLES`) were composed in 59 test files, the sanitizer and the two reference scripts. DR2's and C5's migration tests now expect `[230, 231]` on the way to head. DR2's schema diff also expects `C5_ALTERED_TABLES`, and its head test reads `migration_head_231`, which holds 230. Those two test resolutions missed the merge commit's index and landed in `4000d5a73c`. `template.py`: 31 hunks, both notes kept, fingerprints recomputed, second pass 0. References: main's side, regenerated in `d3cff6ad89`. |

After each merge:

- `db_validate_reference`: errors [] (final: 1111 leaves, which is main's 1110 plus `notes.gaps_enabled`; 360 table
  notes);
- `desktop_validate`: reproducible byte for byte (303 TS / 6 Rust / ACTIVE 309);
- `validate_vault`: passed (1375 notes);
- all 31 defaults fingerprints equal `defaults_fingerprint_for_version`.

The second merge needed manual Python resolution only in head paths, chain lists and altered-table sets, the data a
migration rebuild needs, plus snapshot data.

### Gate

| Step | Tree | Result |
|---|---|---|
| `uv run lint-imports --no-cache` | step 0, `a8455f1b6e`, `d3cff6ad89` | 37 kept (step 0, before main's new contracts), then **40 kept, 0 broken** |
| Targeted head-fixture and migration set (58 files: every test naming `migration_head_231` or an `*_ALTERED_TABLES` set, every `test_*migration*.py`, table roles, tracked fixture databases, coordinated migrations, public-tip guards, the C5 tests) | `20be0dd94c` | **757 passed, 3 skipped** |
| Full pytest (`flock … systemd-run … -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | `d3cff6ad89` | **23585 passed, 90 skipped, 47 xfailed, 0 failed** (39:47). A first run queued at `236a323c92` was stopped while it was still waiting for the lock, because main moved (data-relax 2). |
| Durability lane (`pytest -m durability -n 6`, 5G) | `d3cff6ad89` | **181 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh `copy_tree_with_databases` copies in the gitignored `fixtures-local/landing-c5/owner-lane`) | `d3cff6ad89` | **83 passed, 2 failed, 4 skipped**. Both failures are the known ones: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]`. 0 new receipts: probability keeps its 56 historical rows. |
| Frontend: `npm install`, `npm run typecheck`, whole vitest (`--maxWorkers=4`), `npm run frontend:build` | `a8455f1b6e` (`apps/` unchanged since) | typecheck ok, **251 files, 2401 passed**, build ok |
| `cargo check` (`src-tauri` differs from main by `notes_set_gaps`) | final | ok |

### Smoke on fresh owner copies (`fixtures-local/landing-c5-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every AI route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). The code came from `git archive` of main `c0017b5740` and of the branch `d3cff6ad89`, each with
`src/`, `migrations/` and `tests/`. Each copy ran under its own side's code: a bare `upgrade` (mvp-0.35 → mvp-0.40;
head 230 on main, 231 on the branch), the primary desktop start, `migrate_vault`, then `rebuild-derived-state`. An
audit hook logged every process start and refused non-loopback sockets and Codex starts.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today (3 queue variants, frozen clock), branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| Daily plan dump, branch vs main | **identical** (84,696 bytes) | identical (124,021) | identical (32,433) |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0 | 0/0/0 |

**Notes, on linear_algebra** (`scripts/c5_smoke.py`, a copy of the branch copy each):

- The FAKE `tend` ran over one synthetic note, with `[learner_text_gaps] enabled = true` so that the notes switch
  decides. The note was linked by hand (`notes.link`) to a real reading section of the copy.
- **`notes.gaps_enabled` off (the default):** the gaps-only note readers (`note_gaps.linked_notes`,
  `linked_note_ids`, `note_text`) were made to record and refuse for the whole run: the sidecar's open, the hand
  link, hide and keep. Around the backlog sweep, `enqueue_learner_notes` and `learner_text`, the notes store's row
  readers refused as well. The result:
  - 0 violations;
  - the sweep's keys are today's exactly;
  - `enqueue_learner_notes` returned 0 and `learner_text` returned None;
  - 0 `learner_note` jobs and 0 gap rows;
  - the prompt contract is C2's, with no `gaps` key.
- **On:** the hand link queued the note's gap job (`queued`, 0 attempts). One `process_next_gap_job` with the vault's
  own clients ended `retry_later` / `waiting_for_plan`: the notes' route is the blackhole, not the ChatGPT plan. The
  job went back to `queued` with 0 attempts and "waiting: your notes are read only by the ChatGPT plan, which isn't
  available now". Nothing was sent, and 0 gap rows were written.
- The shadow rebuild on both notes copies was **0/0/0**.

**0 new `model_call_receipts`** across all 17 smoke databases: every probability copy holds exactly the source's 56
historical rows (42 completed, 14 failed), and the rest hold none.

**Audit:** 4 process starts, all of them the FAKE `tend` (`search` and `serve` for each notes copy); 0 socket
connects; nothing refused.

### Rulings (verbatim)

- **R1:** "F3 closed structurally: note gap jobs never reuse a checkpointed reading or decision, and the plan's reading of a note is not persisted in the checkpoint; a retry always rebuilds from current links."
- **R2:** "Hiding a link after its note was read leaves existing tier-2 gap rows (append-only); a retraction kind needs another FK-safe rebuild and is queued as a follow-up. Owner note."
- **R3:** "Note-derived beliefs may only sight existing holding-pen entries, never create candidates. Accepted."
- **R4:** "C5 keeps C2's personal-notes transport rules (plan only, no Decider, no embedding) pending the owner's notes decision and the planned vault-native notes redesign (C2b)."

R1 settles open question 1's checkpoint part and the codex-review record's checkpoint open item. R2 answers open
question 1, R3 answers question 2 (already the code since Codex review F1), and R4 answers question 3.

### Owner items

- **Migration 231** applies on the first open after the update (no successor, no algorithm version). It rebuilds the
  two gap tables in place and keeps every row.
- **The opt-in:** `[notes] gaps_enabled` (default `false`), or Settings → "let my linked notes steer suggestions".
  With it on, a linked note is read only on the ChatGPT plan (`ai.routing.note_link_judge`). With the plan down the
  reading waits and nothing is sent. Hiding a link stops future readings, and gaps already read stay (R2).
- **R2 follow-up:** a fourth reversal kind ("you unlinked this note") would need another FK-safe rebuild of the
  reversals table.

### Open items

- **C2's Reader surfaces do not refilter stored links when the allowlist narrows.** The `›` margin marks and path
  lines check `notes.tend.paths` when a note is linked, not afterwards. C5's gaps input is filtered (F2); C2's own
  surfaces are C2's scope.
- **`text_gaps` has no `__init__.py`**, so grimp does not graph it and import-linter silently skips the whole
  learner-text-gaps package. The notes exception is pinned statically in `tests/test_notes_never_read.py` instead.
  Adding the package file belongs to a later architecture pass, because other contracts would start to apply.
- **The plan's kind verdict still names a note's gap in `judgment_ledger`.** `judges.log_reading` writes the
  `learner_gap_kind` verdict with `reading.named()` as its rationale for every kind, notes included. The gap row and
  the job checkpoint keep none of those words for a note. A consumer of ledger rationales that sends them off the plan
  would carry the plan's words for a note. None is known, but this is the one store left to audit.
- R2's retraction kind (above), queued as a follow-up.

After the gate, main was re-read: it was still `c0017b5740`, so no further merge was needed.

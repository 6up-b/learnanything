# Exam protection by extraction identity: Codex review fixes

Stage: `fix/reread-safety` (worktree `learnanything-ux-impl`), stage record `exam-protection-identity.md`.
Reviewed diff: `808dc9c01..35e2577e9`. Review: Codex job `20261015-073520-7PnfkW`, verdict "reopen", 6 findings
(3 High, 3 Medium). All 6 reproduced. Five are fixed in full. F6 is fixed for its kill switch; its successor
requirement is rejected under the owner's standing ruling (below). Main was not merged here.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | An old confirmation overrides newly added ambiguous protection | fixed | `5d6393b58` | `test_exam_protection_identity.py::test_identity_review_f1_a_confirmation_never_covers_an_ambiguous_mark_made_after_it` |
| F2 | High | Mixed known and unbound signals release previously held-out questions | fixed | `5d6393b58` | `test_identity_review_f2_an_unbound_signal_never_lets_a_known_one_mark_its_origin` (real `prepare_unit_inventory` reuse, then migration 225, two distinct questions); `test_identity_review_a_signal_of_unknown_reading_is_named_plainly`; `test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on` updated (below) |
| F3 | High | Migrated signals lose protection when exam membership disappears | fixed | `5d6393b58` | `test_identity_review_f3_an_upgraded_exam_signal_survives_its_qualification_leaving[assessment_profile, outline_pick, outline_pick_after_upgrade]`, `test_identity_review_f3_a_legacy_signal_survives_its_exam_membership_changing[re_role, remove, scope_removed]`; control `test_identity_review_f3_an_unchanged_membership_records_nothing`; pin `test_the_ledgers_exam_roles_are_the_role_authoritys` |
| F4 | Medium | PreparingView can no longer complete exam marking | fixed | `ddbf0a189` | `PreparingView.test.tsx`: "sends the reading and the proposal shown, and asks again when they changed"; control "marks nothing when the learner says not now to the fresh confirmation" |
| F5 | Medium | Confirmed owner verdicts never reach judgment_ledger | fixed | `5d6393b58` | `test_identity_review_f5_the_owners_marking_is_an_owner_verdict_in_the_judgment_ledger` (durability lane too) |
| F6 | Medium | The reading-admission change lacks a working rollback switch | fixed (kill switch); successor part rejected | `5d6393b58` | `test_identity_review_f6_the_kill_switch_restores_the_predecessors_reading_step[u4, dl1]`. The successor tag is rejected: the owner's standing ruling is live changes behind kill switches, not successors, for serving changes replay never reads, and the reading-step selection is ruled such a change (`ux-phase1.md`, "Versioning: the reading step is a live change, not a successor (owner ruling)") |

`883bdcefe` regenerates the DB and config references (provenance; the new `db/stores/held_out_signals.py` among the
ledger's source paths; migration 225 now reads `source_unit_selections`). `457b6f01d` registers that store as a SQL
write owner (`test_architecture.py`, found by the first full run). `72483df09` refreshes the references' provenance.

**Reproduction first.** The tests were written before the fixes and run against the reviewed code: 11 Python tests
failed and the one control passed. A second run against a `git archive` of `35e2577e9`'s `src` and `migrations`
(after the copy and pin tests were added) gave **13 failed, 1 passed** (the control). One vitest case failed and the
cancel control passed. Each failed on behaviour:

- **F1:** after the owner confirmed B and a legacy scope named `u1` later, `covers('extXB', 'y1')` was False (B's
  Theory, named by the new mark, released) and `mark_plan` returned None.
- **F2:** after the reuse and migration 225, `held_out_among(held, 'extXA', ['x1', 'x3'])` was `['x1']`: A's second
  question was released and the Reader refused only the first. The plain-copy test failed with `ambiguous == ()`.
- **F3:** every case left `held_out_material` empty once exam qualification ended: an `assessment`-profile inventory
  with no membership, an outline exam pick removed (backfilled before or after it), and a source-set member
  re-roled, removed, or whose exam scope was removed through the vault writer.
- **F4:** two `source_action` calls, not three: the fresh confirmation returned for the stale one was dropped.
- **F5:** no `judgment_ledger` row (the first run failed on the missing verdict path, the archive run with
  "DID NOT RAISE": nothing tried to record a verdict).
- **F6:** with `plan.reading_from_furthest` and `goals.held_out_selection` both off, the plan offered `1-vectors`
  where the predecessor offers `contents`; no plan recorded the rule (`KeyError: 'reading_rule'`).

The role pin fails on the archive because the store module did not exist; it is a pin, not a reproduction.

### What changed

- **F1** (`exam_material._Marks`, `exam_marking`). A book's *unplaced* marks are the marks that may be about any
  reading: a legacy exam scope's units (`scope:<unit id>`) and held-out signals of unknown reading
  (`signal:<inventory id>`, F2). The owner's marking records the unplaced marks it reviewed
  (`protection_marked.reviewed_unplaced`), and the proposal hash includes them. A confirmed reading counts as
  marked only while every unplaced mark of the book is one it reviewed. A new or changed one holds the reading back
  whole again, and the card offers the marking (its suggestion includes the new mark's units). A removed one
  releases nothing the owner reviewed. A marking made before this fix records none, so any unplaced mark holds its
  reading back (fail closed; only this branch's data can carry one).
- **F2** (`exam_material._protection_marks`). A signal of unknown reading is an ambiguous mark (`signal`): it protects
  its book, may be about any reading, and so no known signal marks a reading beside it. Every reading of the book is
  withheld whole until the owner marks it, and the marking reviews it (F1). The suggestion places it on every
  reading of its revision by its unit id and its span ids. The card says why in plain words
  (`exam_marking.FOUND_DETAILS`: "LearnLoop found exam questions in this book before it recorded which reading it
  found them on…"), and doctor's `source:reading_held_back` says the same when that is the only unclear mark.
- **F3** (migration 225, `db/stores/held_out_signals.py`, `vault/writer.py`, `Repository.upsert_unit_selection`).
  Where the database knows the role, the backfill records it: an inventory made under `assessment`, the profile only
  the exam role asks for, or on a book with an outline exam pick, gets `made_as_role = 'exam'` (the unmigrated
  fallback reads the same). Where only the vault knows it, whatever ends exam qualification records the book's
  role-unrecorded signals as exam material first: an appended copy (`hos_q_<row id>`, `made_as_role = 'exam'`),
  never an update of the RAW_LEDGER. The vault writer does this before a `source_sets.yaml` write that ends a book's
  exam membership in that set (an exam default role or exam scope entry removed, re-roled, or the member dropped),
  and refuses the write if it cannot record it (fail closed). The repository does it in the same transaction before
  an outline exam pick changes. A write that keeps the book exam material, or a book that never was, records
  nothing, so the owner's textbook signal still protects nothing. The copy keeps the inventory id, so a reviewed
  unknown-reading signal (F1) stays reviewed.
- **F4** (`PreparingView.tsx`). The preparing Reader sends `confirmedExtractionId` and `confirmedProposalHash` with
  the confirmation. If the sidecar returns a fresh confirmation it asks again, and "Not now" marks nothing.
- **F5** (`exam_marking._record_verdict`). The confirmed marking appends one owner verdict in the marking's
  transaction: task `exam_material_marking`, `judge = owner`, verdict `marked`, the reading
  (`left_kind = extraction`) and the book (`right_kind = source`), `input_hash` = the proposal hash, and a rationale
  with the reading, its revision, the proposal hash, the units held out, where they were suggested from, the
  unplaced marks reviewed and the time. Its id is derived from the proposal hash and checked first, so a retry of
  the same proposal writes nothing more. If the verdict cannot be written, nothing is marked.
- **F6** (`daily_plan.engine.reading_step_rule`). Exam protection in DL1's reading order is now behind the serving
  rules' kill switch, `goals.held_out_selection`, whose meaning is already "off restores the predecessor's serving
  selection". With it off and `plan.reading_from_furthest` off, the reading step and its minutes are DL1's
  selection exactly. U4's order keeps the exam filter it always had, behind its own switch. Each plan records the
  rule that chose its step (`split_json.reading_rule`: `furthest`, `book_order`, or `dl1`). The successor tag is
  rejected per the owner ruling cited in the table; the review's "no admissibility change" claim is corrected here.
  The step is a live serving change with a kill switch, and replay never reads it.

**Earlier test updated.** `test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on` used to accept A as
marked by its own signals beside two rebound rows, which is F2's loss. It now expects nothing marked while the
rebound rows exist and A marked once they are gone. Its `assessment` rows are now backfilled as `exam`.

### The owner's vaults

New backup-API copies (`copy_tree_with_databases`) of the main checkout's `fixtures/linear_algebra` and
`fixtures/probability` were made under `fixtures-local/epir-*` and migrated by this code (165 to 225):

| | linear_algebra | probability |
|---|---|---|
| ledger rows | 1 (`combined` profile, a video's inventory: `made_as_role` stays NULL) | 0 |
| protected books, held-back readings | none | none |
| exam material, held-out partition | empty | empty |
| marking verdicts | 0 | 0 |

Nothing changes for them. The main checkout's `git status --short fixtures/` was identical before and after. The
databases' size and mtime are unchanged and each `-wal` is still empty; only the gitignored `-shm` mtime moved.

### Residuals

- **A hand edit of `source_sets.yaml` that ends exam membership** bypasses the writer, so a role-unrecorded signal
  qualified only by that membership is released. The backfill covers what the database knows (the exam profile,
  outline picks). The owner's vaults have no such row.
- **A writer on a database not yet migrated to 225** has no ledger to record into. The app and CLI migrate on open.
- **`desktop_validate.py`** fails on main's unclassified `apps/learnloop-tauri/src/copy/denyList.ts`. That failure
  predates this stage and is not in the gate.

### Gate

Run on the final code tree (`72483df09`; only this record follows). `TMPDIR` was the worktree's
`fixtures-local/tmp`. No paid calls ($0.00); every test uses fakes.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | First run, on `883bdcefe`: 11,078 passed, 1 failed. The failure was `test_architecture.py::test_sql_writes_stay_in_registered_owner_modules`: the new store was not registered as a SQL write owner. It was real and is fixed in `457b6f01d`. Final run, on `72483df09`: **11,078 passed, 1 failed** (11 min 41 s, under parallel stages). The failure is `test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]`, the known load-only flake recorded in `reread-safety-codex-review.md` and `tutor-delivery-fixes.md`; it passed in the first run. Rerun alone, the file passes 5/5 three times. 11,079 tests = the record's 11,065 + 14 new. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **103 passed**, 10,976 deselected (102 before, plus the F5 verdict test) |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **596 passed** in 83 files (594 before, plus the two PreparingView marking tests) |
| `npm run frontend:build` | built |
| `cargo check` | not required: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | Regenerated (`883bdcefe`, then `72483df09` for provenance only). Validation passes with no errors (schema head 225, 322 table notes). `validate_vault.py` passes. No schema change: migration 225 changed its backfill only, and the head fixture has no inventories. |
| CLI help / snapshots / RPC pins | No CLI, RPC or config default changed. `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py`, `test_controller_snapshot.py` and `test_mobile_allowlist.py` pass in the full run. |

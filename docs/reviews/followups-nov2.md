# Follow-ups Nov 2 (stage `followups-nov2`, branch `fix/followups-nov2`)

Base `67c05ed37c` (main: C1 mvp-0.40; Reader through CA6b and follow-ups; RW5d P2/P2b/P4a; C2, C3, C5
(migration 231); data-relax-2 (230); blindness relax; followups-nov1c). Worktree `learnanything-ad1`.

Three queued follow-ups, each built with fail-first tests that name the ruling they close. Kill switches are
unchanged. **No live or paid call was made**: every model is a fake, every ad-hoc script ran under `env -i` with an
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, the real `tend` was never run, no owner vault or
`~/.config/learnloop` was opened, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`.

**Successor: mvp-0.41** for (b) (`HELP_FOLD_ATTACH_ALGORITHM_VERSION`, kill switch `hints.fold_follows_attach`),
added by the Codex review's F1 (`docs/reviews/followups-nov2-codex-review.md`): the "none" first decided below
did not hold, because the playbook's 2026-10-17 rule makes a change to which new attempts are primed a successor
even when replay is unchanged. (a) and (c) need none.

## (a) Figure learner-state provenance (closes learner data-relax 2, ruling R1's remainder)

R1: "F2 remainder (cached fuller delivery, pre-branch rich rows, revision inheritance) is ruled Low ... Stored quick
figures were never rechecked either. Queued follow-up: record inputs on quick rows and reconstruct fuller views from
current rows at delivery." Exam-material protection, not privacy.

What changed:

* **Quick rows keep the record.** `figures/service.py` `_with_learner_inputs`: a grammar or sketch figure whose
  author was sent a learner state keeps `learner_state_inputs` (`RICH.LEARNER_STATE_INPUTS_KEY`, the record rich rows
  keep since data-relax 2) in its `verification_report`, for shown and failed rows alike. No state sent (the switch
  off, or nothing to say): the report is exactly as before (no key). Never shown (`figure_view` reads named report
  fields only) and never sent to a model. No schema change.
* **Presentation-time recheck from the current rows.** `service.learner_state_withheld(vault, repository, row)`
  replaces `RICH.stored_learner_state_withheld` in `row_withheld` (behind `figure_withheld`, the sidecar's
  `deliver_figure`, `list_figures`, the compiled-figure read and the revision base), in `fuller_state`'s filter and in
  `_reusable`'s rich-only reuse. It reads the figure and every figure it was made from out of the current rows:
  * its earlier versions through `supersedes_id` (a revision's author is sent its base's spec or program):
    **revision inheritance**;
  * a fuller version's quick figure through `fuller_of_id` (its author is sent that figure's brief), and that quick
    figure's rich intent (`rich_intent`, the job's payload; `RICH.intent_learner_state_withheld`): **a fuller version
    stored with no record of its own** ("pre-branch rich rows") is checked by what its job carried.
  Each row is checked by its own record and its intent; a figure no author of which was sent a learner state has
  nothing to check, exactly as before. The walk visits each row once (a seen-set, so it ends; no new bound).
* **Kept build results are rebuilt from the current rows.** `deliver_figure` (every delivery of a figure job,
  including each cached read through `reader.figure_job`) now passes the kept view through
  `service.redelivered_view`, which reads the figure's row again and rebuilds its `fuller` line with `fuller_state`
  (the presented row via the new `_presented_row`, the same transforms `figure_view` applies): **cached fuller
  delivery**. A view with no fuller line (rich tiers off, or a rich figure) goes out exactly as kept.

Tests (`tests/test_followups_nov2_figure_provenance.py`, 8; fail-first: against the pre-fix sources 7 failed and 1
passed, the switch-off pin):

| Test | Ruling item |
|---|---|
| `test_a_quick_figure_keeps_the_inputs_of_the_learner_state_it_was_written_from` | record inputs on quick rows |
| `test_a_quick_figure_with_no_learner_state_keeps_its_report_as_before` | switch-off byte-identical report |
| `test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented` | "stored quick figures were never rechecked": listing, delivery and the kept job result |
| `test_a_revision_inherits_its_bases_learner_state_protection` | revision inheritance |
| `test_a_fuller_version_with_no_record_of_its_own_is_checked_by_its_jobs_payload` | pre-branch rich rows |
| `test_a_kept_build_results_fuller_line_is_read_again_from_the_current_rows` | cached fuller delivery (pending then ready) |
| `test_a_kept_result_naming_a_ready_fuller_version_is_not_delivered_once_its_inputs_are_protected` | cached fuller delivery (protected since) |
| `test_with_the_rich_tiers_off_a_kept_view_goes_out_exactly_as_kept` | switch-off byte-identical delivery |

Decision (revised by Codex review F3): a quick row built **before this branch** with a learner state (prompt
version `+learner-v1`) keeps no record of its own; with a rich intent carrying the inputs it is checked through
that; otherwise it is withheld for good (its dependencies cannot be named). Revised again by Codex re-review F5: they are
never inferred from a later press (the state hash strips what each statement was read from, so an identical
statement from another gap hashes the same); a press of the same input builds a fresh figure with its own record
under a recorded-inputs key (`_recorded_input_key`), reused from then on, and the old row is never given a record
or reused. Unmarked rows keep the no-learner-state reading.

## (b) The help fold counts exactly the help rows that attach

Follow-up: "the help fold counts exactly the help rows that attach (all help kinds; session rollover case)".

What was wrong: a keyed submit's fold (`help_assists._fold_rows`) read the key's shown, server-counted rows **in the
submit's own practice session only**, while H0's attach (`attach_submission`, after the commit) takes every row of
the key in any session. A hint shown under the key in a session that then ended (the learner went on in a new
session with the same draft) was attached to the attempt without being counted: `hints_used` 0, certification
eligible, beside an attached shown hint (reproduced through `submit_attempt` and `submit_dont_know`; a level 4-5 row
likewise never primed).

What changed:

* `_fold_rows`: a keyed fold reads the submission's rows of the item **by the key alone** (H0's attach rule); a
  keyless fold keeps its session window exactly (H2a round 3, W1).
* `help_assists.attach_keyed_fold` + `hint_fold.attach_keyed`, called in `apply_attempt`'s write transaction beside
  `attach_keyless`: a keyed attempt takes the rows it counted **in its own transaction, through the fold's own row
  definition**, so whichever help kinds the fold counts are exactly the kinds it attaches, and no other attempt can
  take a counted row between the commit and H0's attach. `submitted_at` and `submit_latency_seconds` are written
  exactly as `attach_submission` would (only where unstamped), so a hint shown during grading keeps its timing. H0's
  attach then binds the key's other rows (client reveals, unshown requests, answers) as before.
* **Generic over help kinds, for RW5d P3** (landing in parallel): the kind predicate in `_fold_rows` is untouched;
  P3 replaces it with its `HINT_EQUIVALENT_KINDS_SQL` (`'hint', 'figure'`), and the new attach follows that
  definition automatically. The two diffs touch adjacent lines of `_fold_rows` (a trivial textual conflict: keep
  this branch's clause structure with P3's kind constant).
* No telemetry gate: adaptive hints need `hints.telemetry_enabled` (`adaptive_enabled() and telemetry_enabled`), so
  with telemetry off no server row exists and nothing changes.

**Successor decision (playbook step 1): mvp-0.41** (corrected by Codex review F1; first recorded here as "none").
Replay re-applies the stored `hints_used` and `primed` and never refolds (`attempts._refold_server_hints` returns at
once for `replace_existing` or a draft with no fold, and replayed drafts carry none), and `help_assists` is
RAW_LEDGER that replay and rebuild never read; but the change alters which NEW attempts are primed and their hint
counts, which the playbook's 2026-10-17 eligibility rule makes a successor with a kill switch. Below the tag, or
with `hints.fold_follows_attach = false`, the fold is the predecessor's clause for clause and no keyed row is
attached in the attempt's transaction (`tests/test_help_fold_attach_successor.py`).

Tests (`tests/test_followups_nov2_help_fold.py`, 8; fail-first: 7 failed, 2 passed on the pre-fix tree, the second
pass being a pin that was then extended):

| Test | Pins |
|---|---|
| `test_session_rollover_..._is_counted_where_it_attaches[submit_attempt]`, `[submit_dont_know]` | the session rollover case: `hints_used` 1 and the row attached to that attempt |
| `test_session_rollover_worked_help_primes_the_attempt_it_attaches_to` | a level 4 row primes, counted 0 |
| `test_a_counted_row_is_attached_in_the_attempts_own_transaction` | attached with H0's attach disabled; a later keyless submit finds nothing |
| `test_the_same_session_keyed_flow_is_unchanged` | count, attach and stamp as before |
| `test_another_keys_rows_are_never_counted_or_taken` | H0 F1 still holds |
| `test_every_help_kind_the_keyed_fold_counts_is_exactly_what_the_attempt_attaches` | all seven `assist_kind` values, client/unshown/other-key rows, both sessions: counted == attached |
| `test_the_keyless_window_still_reads_its_own_session_only` | W1 unchanged |

## (c) C5 retraction kind `unlinked` (closes curriculum C5, ruling R2)

R2: "Hiding a link after its note was read leaves existing tier-2 gap rows (append-only); a retraction kind needs
another FK-safe rebuild and is queued as a follow-up."

* **Migration `235_learner_gap_unlinked_reversal.sql`** (numbered 235: main's head is 231 and RW5d P3 claims 232,
  curriculum C2b 233; the runner is set-based, renumber at landing if needed): `learner_text_gap_reversals.reversal`
  gains `unlinked` by the FK-safe temp-then-rename rebuild under `PRAGMA foreign_keys = OFF` (208/212/231's
  precedent): 182's definition exactly with the one kind more, every row and id kept, its own FK to
  `learner_text_gaps` recreated (no table references it), the append-only triggers recreated with the same
  definitions. No new table, so nothing new to classify (`learner_text_gap_reversals` stays RAW_LEDGER).
* **`jobs.retract_unlinked_notes`**: every gap with `source_kind = 'learner_note'` whose snapshot is not linked now
  (C2's one rule through `learner_note_ids`: the learner hid the link, the proposal was superseded, the note changed
  into a new snapshot, or its folder left the allowlist) gets one `unlinked` reversal (actor `learner`, detail
  `{note_id, why}`), idempotently; the queue revision is bumped when one is written. The gap row stays. Every reader
  that leaves out a reversed gap (the router's card, the learner context and MCP, the figure author's learner state,
  the router reader) leaves it out. It runs first in `enqueue_learner_notes`, so wherever the linked notes are
  queued (a link run's end, a hand link, the vault opening, the opt-in), and `notes.decide` now queues on **hide**
  too (it queues nothing new there: a hidden link is never queued). **Switched off** (the opt-in, the notes, tend or
  the pipeline) it reads no note row and writes nothing, so a missing tend never sets every note gap aside.
* Not a learner tap: `reverse_gap`/`REVERSALS` refuse `unlinked`. The gap's reading says
  *Set aside: the note it came from is no longer linked* (`gap_view`).
* Keeping a hidden link again does not bring the gap back (append-only; the snapshot is read again only as a new
  snapshot). Open question below.
* **Head fixture** `migration_head_231` renamed `migration_head_235`, rebuilt from main's tracked, sanitized 231 head:
  backup-API copy under `fixtures-local/head235/`, only 235 applied under `UPGRADE_SCRATCH_COPY`, checkpoint
  (0, 0, 0), `journal_mode=DELETE` (header 1/1), `integrity_check` ok, `foreign_key_check` empty; only
  `learner_text_gap_reversals`' definition changed and only `schema_migrations` gained a row (218 -> 219 rows);
  copied into place with the backup API, no companion files; README section added. Every head path moved (49 test
  files, the sanitizer's usage line, the two reference scripts with `SCHEMA_HEAD = 235`); head-version asserts moved
  to 235; the "applied from N" lists gained 235; the "nothing else changed" chain diffs that name
  `C5_ALTERED_TABLES` now also subtract `UNLINKED_ALTERED_TABLES` (the files that skip `learner_text_gap*` tables
  needed nothing).

Tests: `tests/test_followups_nov2_note_gap_unlinked.py` (5) and `tests/test_learner_gap_unlinked_migration.py` (6, one
durability). Fail-first on the pre-fix tree (no migration, no retraction): 9 failed, 1 passed (the
"never a manual reversal" pin).

| Test | Pins |
|---|---|
| `test_hiding_a_read_notes_link_sets_its_gaps_aside_and_only_its_own` | R2: the hidden note's gap leaves the learner context, the other note's stays; the gap row is unchanged; the label |
| `test_the_retraction_is_idempotent_and_keep_does_not_reopen_the_gap` | once per gap; keep does not reopen |
| `test_a_note_changed_into_a_new_snapshot_sets_the_old_snapshots_gap_aside` | "unlinked otherwise" |
| `test_switched_off_nothing_is_read_and_nothing_is_set_aside` | switch-off: no note row read, nothing written |
| `test_unlinked_is_never_a_learners_manual_reversal` | the pipeline's kind, not a tap |
| `test_235_widens_the_reversal_with_unlinked_and_keeps_every_row` (+ durability) | the FK-safe rebuild |
| `test_235_classifies_nothing_new`, `test_235_adds_unlinked_and_nothing_else` | 182's table exactly plus one kind |
| `test_the_head_fixture_holds_235_in_rollback_mode` | the head fixture |

## Constants

None new (the lineage walk ends by its seen-set; `UNLINKED` is a ledger label, not a bound). No config key, so the
defaults snapshots and `parameter_registry` are unchanged.

## Gate (this step; targeted only, owner rule 2026-10-17)

Every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`, one at a
time, `TMPDIR` outside the worktree; the 362-file lane behind `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 40 kept, 0 broken (after the last source change) |
| New files alone after their fixes: `test_followups_nov2_help_fold.py`, `test_followups_nov2_figure_provenance.py`, `test_followups_nov2_note_gap_unlinked.py` + `test_learner_gap_unlinked_migration.py` | 8 passed; 8 passed; 10 passed (+ the head-fixture test once the fixture existed) |
| Fail-first (pre-fix sources, new tests) | (b) 7 failed / 2 passed; (c) 9 failed / 1 passed; (a) 7 failed / 1 passed |
| Migration lane (95 files naming the head fixture, `discover_migrations`, `apply_migrations` or an altered-table set) | first run 1347 passed, 22 failed (the expected chain diffs and applied lists, all fixed); the 14 affected files rerun: 69 passed |
| Targeted lane (362 files: the migration lane, every `test_figure*`/`test_figures*` file, every test naming `help_assists`, `hint_fold`, `hints_used`/`hintsUsed`, `request_hint` or `submit_dont_know`, the notes/gap/learner-gaps readers, the figure delivery readers, and the contract tests: serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table_roles, coordinated migrations, tracked fixture databases, public-tip guards, SQLite file copies, registry audit, config refactor, CLI help snapshot; list in `docs/reviews/followups-nov2.targeted-tests.txt`) | **7514 passed, 2 failed**, 36 skipped, 5 xfailed (29:52). Both failures were pins this stage changes by design, updated and rerun (31 passed): `test_hint_h2b_fix3.py::test_r1_f10_...` (an interrupted H0 attach now leaves the row attached by the keyed attempt's own transaction) and `test_learner_data_relax_2.py::test_a_rich_figure_whose_learner_inputs_became_protected_is_not_delivered` (the quick figure, written from the same state, is withheld too) |
| Durability (`-m durability`) on the 30 migration-lane files that carry durability tests, plus the new migration file | 69 passed |
| DB reference: `db_generate_reference.py` then `db_validate_reference.py` (`SCHEMA_HEAD = 235`) | errors [] |
| `desktop_validate.py`, `module_validate.py`, `validate_vault.py` | pass (305/305 TS + 6/6 Rust; 14712/14712 wikilinks; 1377 notes) |
| Frontend, cargo | not run: no `apps/` change |

Not run here (owner rule): the full suite, the whole durability lane, the whole vitest run.

## Open questions

* (a) Closed by Codex review F3 and re-review F5: marked quick figures with no record stay withheld; a press of the
  same input builds a fresh figure with its own record.
* (b) The `_fold_rows` hunk conflicts textually with RW5d P3's `HINT_EQUIVALENT_KINDS_SQL` line: whichever lands
  second keeps this branch's clause order with P3's kind constant (the attach follows it with no other change).
* (c) Migration number 235 and head fixture `migration_head_235`: renumber/rename at landing after P3 (232), C2b (233)
  and TE1+C4 land. C2b changes `note_links`/`learner_notes`: the retraction reads only `learner_note_ids` (C2's one
  rule), so it follows whatever C2b defines as linked.
* (c) A hidden link kept again does not reopen its gap (append-only reversals; the note is read again only as a new
  snapshot). Re-reading the same snapshot after *keep* would need the gap row's UNIQUE (source) to allow a second
  reading; left as is.
* The generated references (`dac01602ca`) stamp the source commit in every note; the lander regenerates them on the
  merged tree anyway.

## Landing onto main

Prepared on `fix/followups-nov2` (worktree `learnanything-ad1`) from the stage tip `e2d45d5c4a`; the orchestrator
fast-forwards main and pushes. Main moved twice during the landing (TE1 + C4, then RW5d P4b), so the branch was
merged three times; the gate below ran once, on the final tree.

### Step 0: the final verify's F6 (ruling R1) — `3349d626e2`

The final verify (jobs `20261102-041024-Cg9xnj`, `20261102-041606-eSv4yJ`) confirmed F1-F5 fixed and reopened only
F6 [Low]: a fresh figure built for a marked legacy quick figure with no learner-inputs record sits under that input's
recorded-inputs key (`_recorded_input_key`), but the other-settings reuse lookup in `_build` searched only the plain
keys of the other settings (whose occupant, the marked row, is never reused), so toggling
`figures.advanced_panels_enabled` paid the author once more for a figure still drawable. Fix, as R1 names it: when a
learner state was sent, each other setting's key is followed by its own recorded-inputs key in `other_hash`;
`_reusable`'s checks (shown, `drawable_now`, never an unrecorded marked row) apply unchanged. With no learner state
the list is the predecessor's exactly. Regression
`test_followups_nov2_figure_provenance.py::test_a_fresh_figure_for_a_marked_row_is_reused_after_the_panels_are_switched`
reproduced first (built fresh-2 with a second author call), passes after; figure lane (`test_figure*`, 30 files)
616 passed. No further review round (R1).

### Merge 1: main `19c72752b3` (RW5d P3, migration 232; curriculum C2b, migration 233) — `47f2ffc037`

* `help_assists._fold_rows`: this branch's clause order kept, with P3's `HINT_EQUIVALENT_KINDS_SQL` in both the
  predecessor's clause list and the successor's, so the keyed attach (`attach_keyed_fold`) follows P3's kinds
  (`'hint', 'figure'`).
* `handlers/figures.deliver_figure`: the kept view is rebuilt from the current rows (`redelivered_view`) first, then
  P3's attempt-host recording and `attempt_view` apply to the rebuilt view.
* C2b: the retraction reads linked notes only through `learner_note_ids` -> `note_gaps.linked_notes` ->
  `note_links.effective_rows`, C2b's link model over vault-origin snapshots, so no code change was needed; the
  docstring drops the tend-era wording. `notes.decide` queues on hide as merged. The five retraction tests were
  ported from the fake tend to C2b's vault notes (the typed Reader note and the capture; `edit_annotation` makes the
  new snapshot).
* Generated references: main's side, then regenerated (`d8829bbcac`).

### Merge 2: main `1a33bb5db3` (teacher TE1 + C4, mvp-0.41, migration 234) and ruling R4 — `1f4746e57b`

* **Successor renumber (R4)**: `HELP_FOLD_ATTACH_ALGORITHM_VERSION = "mvp-0.42"`, after
  `TEACHER_ALGORITHM_VERSION` (`mvp-0.41`, untouched) in `SUCCESSOR_CHAIN`; `HELP_FOLD_ATTACH_VERSIONS` =
  `{mvp-0.42}`, `LATEST_ALGORITHM_VERSION` = `mvp-0.42`. `help_fold_attach_upgrade` now chains through
  `teacher_upgrade` (`PREDECESSOR = mvp-0.41`; mvp-0.9 to mvp-0.40 go through TE1's upgrade first; a journal naming
  another target is handed to TE1's completion, which hands it on). The CLI runtime and the desktop sidecar install
  `help_fold_attach_upgrade.complete_interrupted_activation`, the chain's latest. `cli/app.py`: help text, the
  `--to` dispatch and the refusal list name mvp-0.41 and mvp-0.42; `tests/cli_help_snapshot.json` changed for
  `upgrade` only. `activation_journal`, `config/schema.py`, `parameter_registry.py` and `db_generate_reference.py`
  name mvp-0.42. The template keeps TE1's mvp-0.41 snapshot block ("New vaults started here ... until follow-ups
  Nov 2's successor landed") and adds the mvp-0.42 block.
* **Migration and head fixture**: 235 keeps its number (TE1 took 234). `migration_head_234` renamed
  `migration_head_235`, rebuilt from main's tracked, sanitized `migration_head_234/state.sqlite`: a backup-API copy
  under `fixtures-local/head235/`, only `235_learner_gap_unlinked_reversal.sql` applied under `UPGRADE_SCRATCH_COPY`,
  `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header 1/1), `integrity_check` ok, `foreign_key_check`
  empty, copied into place with the backup API, no companion files. Against main's 234 head only
  `learner_text_gap_reversals`' definition changed and only `schema_migrations` gained a row (221 -> 222); every
  companion file is main's. README section added. `SCHEMA_HEAD = 235` in both reference scripts; the five hard-coded
  head paths and every head test name `migration_head_235`; "applied from N" lists end `..., 233, 234, 235]`; the
  "nothing else changed" diffs subtract `UNLINKED_ALTERED_TABLES` beside TE1's sets; TE1's head test now asserts the
  head holds 234 and is at 235.
* **Chain pins** (`e8fdaa52ec`): negative chain indices shift by one, the `*_VERSIONS` sets gain mvp-0.42 (and
  mvp-0.41 where they listed up to the latest), TE1's chain test (`SUCCESSOR_CHAIN[-3:]`, `TEACHER_VERSIONS` =
  `{mvp-0.41, mvp-0.42}`), its defaults parity (drops `hints.fold_follows_attach` too), its CLI-completion test (the
  CLI installs this link's completion, which imports TE1's) and its bare-upgrade test (goes through mvp-0.41 to
  mvp-0.42); the help-fold successor test now has `PREDECESSOR = mvp-0.41` and upgrades from mvp-0.9, 0.30, 0.39,
  0.40 and 0.41.
* References regenerated (`fd3c1e715f`; the desktop catalog's commit stamps of 8 notes were stale on main).

### Merge 3: main `de9a03763d` (RW5d P4b, the teacher's visuals; no migration, no successor) — `0f1d1abf38`

* One conflict: the 32 snapshot comments in `config/template.py` (P4b's `[teacher] visuals` beside this branch's
  `[hints] fold_follows_attach`).
* P4b's lesson figures follow this branch's learner-state provenance with no further change: they are built by
  `_build` (the record is kept whenever their author was sent a learner state) and shown through `figure_withheld`
  -> `row_withheld` -> `learner_state_withheld` (`teacher.visuals.lesson_view`). One new test pins it:
  `test_followups_nov2_figure_provenance.py::test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`.
* References regenerated (`349076c85a`).

**Config fingerprints**: after each merge every snapshot was recomputed with `defaults_fingerprint_for_version` with
`.pyc` cleared: merge 1, 32 of 32 then 0; merge 2, 33 of 33 then 0; merge 3, 33 of 33 then 0. **Config leaf count**:
1121 effective leaves in `Database.md` and `Configuration.md`.

### Gate (tip `349076c85a`, main `de9a03763d`)

* `lint-imports --no-cache`: 42 kept, 0 broken.
* Targeted, on the TE1 tree (420 files: the three nov2 test files and the migration file, the figure lane,
  hint/help/submit, notes and gap tests (C2b's `test_notes_*`, C5's), the migration and head-fixture set, table roles,
  tracked fixture DBs, public-tip guards, config fingerprints and registry, every successor/upgrade/landing test, TE1's
  lesson tests): 8220 passed, 42 skipped, 8 xfailed, 14 failed — all chain pins after the renumber, fixed in
  `e8fdaa52ec` and rerun (369 passed). After the P4b merge (59 files: P4b's `test_reader_rw5d_p4b_teacher_visuals.py`,
  every test file P4b touched, the figure lane, the teacher tests, the nov2 files, config/registry/CLI-help, guards):
  1027 passed.
* Full suite (`-n 8 --dist worksteal`, 10G scope, `flock`): **23876 passed, 0 failed**, 90 skipped, 47 xfailed
  (43:05).
* Durability lane: 186 passed, 1 skipped.
* Owner lane on fresh backup-API copies of `owner-copies-mvp035` (`fixtures-local/landing-nov2/owner-lane`): 83
  passed, 4 skipped, the 2 known failures (`test_activity_backfill...attempt_duration...`,
  `test_placement_fixture_copies...[arxiv_v2]`).
* Frontend: typecheck clean, whole vitest 257 files / 2448 tests passed (`--maxWorkers=4`), `frontend:build` ok. No
  `npm install` (dependencies unchanged since the last install). `cargo check` not run: nothing under `apps/`
  differs from main.
* References: `db_validate_reference.py` errors `[]` (schema head 235); `validate_vault.py`, `desktop_validate.py`
  (307/307 TS + 6/6 Rust, reproducible) and `module_validate.py` pass.
* An earlier full gate on the TE1 tree (`e8fdaa52ec`, before P4b reached main) had 23851 passed and 2 failures,
  each passing 3/3 alone: `test_stuck_prompt.py::test_kill_switch_restores_dont_know_exactly` (0.7 vs 0.6977, a
  mass decayed by elapsed time between two computations under load) and
  `test_mvp021_upgrade.py::test_the_successor_rebuild_equals_mvp020s_projection` (two rebuilds' capability evidence a
  few seconds apart). Neither touches hints or figures; neither failed on the final tree.

### Smoke (fresh owner copies, `fixtures-local/landing-nov2-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies; each neutralized under its own side's code
(every AI route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense, embeddings and the gap
pipeline off); `env -i` with an empty `HOME`, `CODEX_HOME` and config directory; an audit hook logging every process
start and socket connect and refusing non-loopback sockets and Codex starts (self-test: it logged a `127.0.0.1:9`
connect and a `true` start and refused `192.0.2.1:80`). Code: `git archive` of main `de9a03763d` and of the branch
`349076c85a`, each with `src/`, `migrations/` and `tests/`. Sides: **m** = main's code, bare upgrade mvp-0.35 ->
mvp-0.41; **b41** = branch code, `upgrade --to mvp-0.41`; **b** = b41 then a bare upgrade mvp-0.41 -> **mvp-0.42**;
**boff** = b with `hints.fold_follows_attach = false`. On each: the primary desktop load, `migrate_vault` (main head
234, branch head 235, 0 applied) and `rebuild-derived-state`. Every dump ran on its own fresh copy.

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, b41 / b / boff vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump, b41 vs main (both mvp-0.41) | byte-identical (84702 B) | byte-identical (124027 B) | byte-identical (32439 B) |
| Plan dump, b (mvp-0.42) vs main | identical after the version label | same | same |
| Plan dump, boff vs b | byte-identical | byte-identical | byte-identical |
| Stored attempts (`hints_used`, `primed`), help rows, help_outcomes | identical on every side | identical | identical |
| `hints report --json` vs main | identical but for its wall-clock `generated_at` and the config echo's new `hints.fold_follows_attach` key | same | same |
| Rollover fold (synthetic keyed row in an ended session, rolled back): m / b41 / b / boff | 0 / 0 (gate off below the tag) / **1** (gate on) / 0 (switched off) | same | same |
| `rebuild --shadow` on b and boff | 0/0/0, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |

The plan dump of b differs from main's only in the version label (`algorithm_version`, `plan.algorithmVersion`, the
version strings inside the router decisions' and AD selections' JSON) and the card, snapshot and payload hashes
computed over them (`plan_norm.py`). The owner copies hold no help row, so help_outcomes is empty on every side and
the stored counts are re-applied unchanged (nothing is refolded). **Receipts**: 0 new `model_call_receipts` across 12
compared databases. **Audit**: the log was empty for the whole smoke (no process start, no socket); no Codex
process.

### Rulings (orchestrator, verbatim)

- R1: "F6 is Low: one extra author call after a settings toggle, for legacy rows only. Fix it at landing if it is a small change (include derived recorded-input keys in the alternate-setting reuse lookup, preserving drawability and protection checks, plus the regression the reviewer named); no further review round."
- R2: "Legacy quick figures built with a learner state before this branch stay withheld until a press rebuilds them (fail closed). Accepted: the owner's vaults are still at mvp-0.35, so no such rows exist outside test copies."
- R3: "Keeping a hidden link again does not reopen a gap already set aside (append-only reversals); accepted as built."
- R4: "Successor renumber: teacher TE1+C4 claims mvp-0.41 and lands first; this branch's help-fold successor becomes mvp-0.42 <- mvp-0.41 (or the next free version if main has moved further). Migration 235 keeps its number if TE1 takes 234; otherwise the next free number."

### Open items

* Owner upgrade path: the owner's vaults (mvp-0.35) reach mvp-0.42 with a bare `learnloop upgrade` (through TE1's
  mvp-0.41); `hints.fold_follows_attach = false` restores the predecessor's fold without a downgrade.
* R2's legacy rows (marked quick figures with no record) stay withheld until a press rebuilds them; none exist
  outside test copies.
* R3: a hidden link kept again does not reopen its set-aside gap.
* Two timing-sensitive tests failed once under full-suite load on the TE1 tree and pass alone (above):
  `test_stuck_prompt.py::test_kill_switch_restores_dont_know_exactly`,
  `test_mvp021_upgrade.py::test_the_successor_rebuild_equals_mvp020s_projection`.
* TE1b (mvp-0.43, migration 236) lands after this branch and renumbers against mvp-0.42 / migration 235.

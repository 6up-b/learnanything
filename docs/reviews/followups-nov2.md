# Follow-ups Nov 2 (stage `followups-nov2`, branch `fix/followups-nov2`)

Base `67c05ed37c` (main: C1 mvp-0.40; Reader through CA6b and follow-ups; RW5d P2/P2b/P4a; C2, C3, C5
(migration 231); data-relax-2 (230); blindness relax; followups-nov1c). Worktree `learnanything-ad1`.

Three queued follow-ups, each built with fail-first tests that name the ruling they close. Kill switches are
unchanged. **No live or paid call was made**: every model is a fake, every ad-hoc script ran under `env -i` with an
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, the real `tend` was never run, no owner vault or
`~/.config/learnloop` was opened, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`.

**Successor: none** (decided below, per `docs/algorithm-change-playbook.md` step 1).

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

Decision: a quick row built **before this branch** with a learner state (prompt version `+learner-v1`) keeps no
record of its own; it is rechecked through its rich intent when it has one, and otherwise, as before this stage, not
for its learner inputs (failing it closed would hide every such figure and, because a fresh read gives the same state
and reuse key, a press would rebuild into the same unique key and show "withheld"). Open question below.

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

**Successor decision (playbook step 1): none.** Only new attempts change: replay re-applies the stored `hints_used`
and `primed` and never refolds (`attempts._refold_server_hints` returns at once for `replace_existing` or a draft
with no fold, and replayed drafts carry none), and `help_assists` is RAW_LEDGER that replay and rebuild never read.
No persisted meaning of an existing attempt changes.

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

* (a) Quick figures built with a learner state **before this branch** (since data-relax 2 landed, 2026-11-01) keep
  no record; with no rich intent they are not rechecked for their learner inputs (as before this stage). Fail them
  closed instead? (It would hide them, and a press would rebuild into the same reuse key.)
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

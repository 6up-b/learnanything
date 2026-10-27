# AD denial log: Codex review and fixes (2026-10-27)

Branch `fix/ad-denial-log`, worktree `learnanything-astrafix`. The Codex review (gpt-6.1-sol, job
`20261027-135452-IjhBJ6`) of the stage in `ad-denial-log.md` found one Medium and one Low. Both reproduced and
both are fixed. The owner's decision stands unchanged: the refusal log is cleared at upgrade, and each line
records which operation was refused.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Rotation can hide new denials from the live count | fixed | `357909efe` (tests `51ad30df1`) | `test_f1_a_denial_after_the_upgrade_returned_stays_live`, `test_f1_an_append_in_flight_never_writes_into_the_archive`, `test_f1_lines_appended_after_the_mark_stay_live_and_the_marked_ones_are_archived`, `test_f1_the_archival_waits_for_an_append_holding_the_log_lock` |
| F2 | Low | A report can count the same denials as both live and archived | fixed | `357909efe` (tests `51ad30df1`) | `test_f2_a_report_never_counts_a_line_live_and_archived` |
| C1 | claim | "Every upgrade function" completes a journalled activation | corrected | review-record commit | `ad-denial-log.md` §1 now says mvp-0.30, mvp-0.31 and mvp-0.32 activate without a journal; the CLI docstring no longer claims it |

## Reproduction (before the fix)

The tests were committed first (`51ad30df1`) and run against the unchanged module:

- **F1, sidecar variant.** The upgrade function is wrapped so a denial is appended through `append_denials`
  after it returns, as a sidecar operation under the successor would before the CLI archives. Before the fix the
  archive held that line and the live count was 0.
- **F1, overlapping-append variant.** An appender thread pauses between its two lines while the CLI upgrade
  runs. Before the fix both lines were written through the open handle into the renamed archive, and the live
  log did not exist.
- **F2.** A scratch test (not committed; it used the pre-fix `archive_denial_log` signature) archived the log
  between `summary()`'s live read and its archive listing. It returned `denials: 2` and `archived_denials: 2`
  for the same two lines. The committed F2 test runs the same interleaving against the new signature.

Before the fix 5 of the new tests failed: the two F1 scenarios on their assertions, the three others with
`AttributeError` (no `cutover_mark` before the fix).

## The fix

All of it is in `learnloop.adaptive_difficulty.denial_log`, with one call added in `cli.app.upgrade`.

- **The cutover is the command's start.** `cutover_mark` records the live log's identity (device, inode) and
  length. `learnloop upgrade` takes the mark before it dispatches to any upgrade.
  - After a successful upgrade, `archive_denial_log(..., mark=)` moves only the first `length` bytes.
  - When nothing was appended after the mark, the live file is renamed (atomic, byte-identical, as before).
    Otherwise the marked bytes go to the archive (`O_EXCL`, fsync) and the later lines replace the live file
    (staged file, fsync, `os.replace`).
  - If the live file at the archival is not the marked one, another archival already moved the marked lines,
    and nothing is archived. No log at the mark also archives nothing; the lines that appeared during the
    command stay live.
  - A denial during or after the upgrade therefore stays in the count. "Since the last upgrade" now means
    since the last upgrade began. A predecessor-era denial logged while the upgrade ran is counted too: the
    count errs toward showing a failure, never toward hiding one.
- **One leaf lock.** Appends, the mark, the archival and `summary` each hold an exclusive `flock` on
  `ad_guard_denials.lock` beside the log.
  - An append opens, writes and closes the live log inside the lock, so no append handle spans an archival.
  - The lock is a leaf: nothing else is acquired while it is held. It therefore comes after the vault
    mutation lock and SQLite's locks in every order, and the existing order is unchanged.
  - The archival no longer takes the vault mutation lock. The log lock now serializes archive names, so a
    sidecar holding the vault lock cannot time the archival out.
  - Without `fcntl` (non-POSIX) the lock is a no-op, as `vault_lock` degrades.
- **F2.** `summary` reads the live log and lists the archives in one critical section under the lock. If the
  lock cannot be opened (a read-only directory), it reads without the lock; nothing can archive there either.
- **Torn tails.** An append after a torn tail (a writer that died mid-line) starts with a newline, so its lines
  never join the torn bytes. A mark that falls after a torn tail splits on the following newline.
- **Mark failure.** If the vault does not load before the upgrade (so the log cannot be found), the mark is
  None and the archival takes the whole live log, as before the fix. This keeps the owner's clear-at-upgrade
  rule; the F1 window reopens only on that degraded path.
- **Crash windows,** documented in the module. Neither hides a line:
  - a death between the upgrade and the archival leaves the marked lines live until the next upgrade;
  - a death mid-split (archive written, live not yet replaced) counts the marked lines twice until the next
    upgrade.
- **`fixtures/.gitignore`** now also ignores the archives, the lock and the staging file. Before, only the live
  log was ignored, so an archive beside a tracked fixture would have shown as untracked.

There is no migration, no successor and no new parameter. The mark is a byte offset, not a model or decision
parameter. The CLI help text is unchanged.

## Gate

Every test command ran under `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with
`-n 6`.

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- `tests/test_ad_denial_log.py` alone, three more serial runs for the threaded tests: 16 passed each time.
- Targeted pytest, AD and contract files: **6084 passed** (515s).
  - `tests/test_ad_denial_log.py` (16), `test_ad_guard.py`, `test_ad_guard_offer_receipts.py`,
    `test_ad_guard_reachable_reads.py`
  - `test_ad23_contract.py`, `test_ad23_fix_r5.py`, `test_ad23_fix_r7.py`, `test_ad23_fix_r8.py`,
    `test_ad23_fix_review.py`, `test_ad3_monitoring.py`, `test_ad_protected_readings.py`,
    `test_ad23_intent_compose.py`, `test_ad23_inversion.py`, `test_ad23_pool_membership.py`
  - `test_cli_help_snapshot.py`, `test_architecture.py`, `test_salience_firewall.py`, `test_decider_landing.py`,
    `test_reading_hardening_landing.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`
- Targeted pytest, every test file that invokes the CLI `upgrade` command (each now goes through the mark and
  the archival): **975 passed, 12 skipped, 1 xfailed** (994s).
  - `test_ad23_successor.py`, `test_batch3_landing.py`, `test_exam_protection_identity.py`,
    `test_field_workbench_signals.py`, `test_intent_codex_rereview.py`, `test_lp_claim_fixes.py`,
    `test_method_explicit_upgrade.py`
  - `test_mvp09_upgrade.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`,
    `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`,
    `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`,
    `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`
  - `test_plan_follows_path.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`,
    `test_regrade_contract_upgrade.py`, `test_serve_eligibility_review.py`, `test_serve_eligibility.py`,
    `test_reader_ca2_one_ask.py`, `test_route_rules_in_grader.py`, `test_stuck_prompt.py`
- Not run, because nothing they cover changed:
  - durability lane: no migration and no DB/connection code;
  - frontend and cargo: untouched;
  - DB reference scripts: no schema change.
- No paid calls and no live calls. No owner-vault copies; synthetic vaults only.

The full suite runs at landing.

## Verify 2 fixes

The Codex verify of the fixes above (gpt-6.1-sol, job `20261027-143802-PmhjQw`) found two Mediums and one Low.
All three reproduced and all three are fixed. The invariant they protect: a line may be counted twice until the
next upgrade, but it is never lost or hidden from the live count.

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| V2-F1 | Medium | A failed mark archives the whole live log, a successor's denial included | fixed | `adedc67e3` (tests `f76db66b2`) | `test_v2_f1_an_unmarked_upgrade_leaves_the_log_live` |
| V2-W | Medium | `_fsync_write` ignores a short `os.write`; a split can then lose complete lines | fixed | `adedc67e3` (tests `f76db66b2`) | `test_v2_a_short_write_that_resumes_completes_every_byte[archive,staging]`, `test_v2_a_failed_write_keeps_the_live_log_and_removes_what_it_created[archive,staging]`, `test_v2_a_failed_archival_never_touches_an_existing_archive` |
| V2-F2 | Low | `summary` falls back to unlocked reads and can report a line both live and archived | fixed | `adedc67e3` (tests `f76db66b2`) | `test_v2_f2_a_report_without_the_lock_does_not_count_archives` |

### Reproduction (before the fix)

The tests were committed first (`f76db66b2`) and run against the unchanged module. All 7 failed; the 16
earlier tests passed.

- **V2-F1.** `cutover_mark` is patched to raise, and the upgrade is wrapped so a successor's denial is appended
  after it returns. The command archived the whole log, the successor's line included, and the live count was 0.
- **V2-W.** `os.write` is patched so one call writes a 64-byte prefix and returns 64. Later calls either write
  normally ("resume") or raise `EFBIG` ("fail"), as under `RLIMIT_FSIZE` or a full disk. Each case runs on the
  archive write and on the staging write of a split.
  - Resume, archive: the archive held 64 bytes of the two marked lines, and the live log was replaced by the
    later line. The marked lines were lost.
  - Resume, staging: the live log was replaced by 64 bytes of the later line. That line was lost.
  - Fail, archive: the live log survived, but a partial archive and the staging file were left behind.
  - Fail, staging: the call did not raise, and the live log was replaced by the truncated tail.
  - Fail beside an existing archive: the call did not raise.
- **V2-F2.** `_log_lock` is patched to raise `PermissionError`. Between the live read and the archive listing,
  the test renames the live log to an archive, as another process's archival would. The report gave
  `denials: 2` and `archived_denials: 2` for the same two lines.

### The fix

- **No mark, no archive.** Without a mark, the archival cannot tell the lines from before the upgrade from a
  successor's. `archive_denial_log(mark=None)` returns None and leaves the log live. The CLI says so on stderr,
  as on the other archive-failure path: "AD guard denial log not archived (it could not be marked at the
  upgrade's start); ad report counts its earlier lines until the next upgrade". The upgrade still succeeds.
  The owner's clear-at-upgrade rule waits for the next upgrade on this degraded path, which errs toward showing
  a denial. This replaces the "Mark failure" bullet above.
- **Every byte, or a clean failure.**
  - `_fsync_write` loops until every byte is written. A call that writes nothing raises `EIO`.
  - On any failure after its open, `_fsync_write` removes the file it opened. That file is one it created
    (`O_EXCL`) or the archival's own staging file. A failed exclusive open (a name already taken) leaves that
    file alone, so an existing archive is never touched.
  - In a split, a failure of the staging write or of `os.replace` removes the staging file and the new archive,
    then re-raises. The live log is replaced only by the last step, so it is untouched.
  - The CLI's existing handler names the failure on stderr, and the upgrade still succeeds. If an unlink itself
    fails, the file stays: its lines are counted twice, never hidden.
- **A report without the lock.** If the lock cannot be taken, `summary` gives the live count and its count by
  entry point. It sets `archived` and `archived_denials` to None, with `archived_unavailable` naming why. The
  markdown says "in the live log (archive counts unavailable: ...)" and omits the archived line. The live
  count is never withheld. There is no retry, because a read-only directory would not change within one.

There is no migration, no successor and no new parameter. The CLI help text is unchanged.

### Gate

Every test command ran under `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with
`-n 6`, one at a time.

- `uv run --no-sync lint-imports --no-cache`: 36 kept, 0 broken.
- `tests/test_ad_denial_log.py` alone, four runs: 23 passed each time.
- Targeted pytest, the AD and contract files listed in the first gate: **6091 passed** (574s). That is the
  earlier 6084 plus the 7 new tests.
- Targeted pytest, every test file that invokes the CLI `upgrade` command (the list in the first gate): **975
  passed, 12 skipped, 1 xfailed** (876s).
- Not run, because nothing they cover changed: the durability lane, frontend, cargo and the DB reference
  scripts.
- No paid calls and no live calls. No owner-vault copies; synthetic vaults only.

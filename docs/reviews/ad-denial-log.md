# AD guard denial log: archived at upgrade, each line names the refused operation (2026-10-27)

Branch `fix/ad-denial-log` from `cdd0a3c4f`, worktree `learnanything-astrafix`. This stage answers the two owner
questions carried from `ad-guard-offer-receipts.md` (§ landing ruling). The owner decided both on 2026-10-27:

- the refusal log is cleared at upgrade;
- each refusal line records which operation was refused.

**No migration and no algorithm successor.** `ad_guard_denials.jsonl` is a diagnostic file beside the database,
not persisted meaning. No table changes. No scoring, scheduling, serving or projection reads it. Only
`learnloop ad report` reads it. The algorithm-change playbook does not apply.

## 1. What changed

- **New module `learnloop.adaptive_difficulty.denial_log`.** The log's one home, with its rules in the module
  docstring:
  - `denial_log_path` and `denial_count` moved here from `operation.py`. `operation` re-exports both, so
    `O.denial_count` callers are unchanged.
  - `append_denials` writes the log lines.
  - `summary` builds `ad report`'s guard block.
  - `archive_denial_log` and `archived_logs` handle the archives.
- **Each line names the refused operation.** `operation._record_denials` writes `entry` beside `verb`, `table`,
  `why`, `reader` and `epoch`. The value is `op.guard.entry`:
  - for an `@entry` function, its qualified name (e.g. `learnloop.adaptive_difficulty.replay.load_events`);
  - for an operation opened without a name, the guard's caller chain (`a < b < c`), the same string the guard's
    warning already logs.

  The in-process `DENIALS` list carries the entry too. `Guard.denials` records are unchanged, since the guard
  tests compare them.
- **Old lines stay readable.** `summary` groups lines by `entry`. A line without one (written before this change)
  is `unrecorded`. A line that is not a JSON object (a torn append) is `unreadable`. The count is still the
  number of non-empty lines.
- **Cleared at upgrade.** `learnloop upgrade --to <version>` calls `cli.app._archive_ad_denial_log` after the
  upgrade result reports `upgraded`:
  - It runs once per command, after the final step. A chained upgrade (e.g. mvp-0.33 → mvp-0.35 through
    mvp-0.34) produces one archive named `<from>-to-<to>`.
  - Every upgrade function returns only after its journalled activation has committed and its journal has been
    removed, so the archive is made after the journal completes.
  - A refused upgrade never reaches the call: exit 1 ("vault is already …", a refused chain step) or exit 2
    (an unknown target). Neither does a failed one (an exception).
  - Without a live log it does nothing.
- **The archive.** The rename is `ad_guard_denials.jsonl` → `ad_guard_denials.archived-<from>-to-<to>-<UTC
  YYYYMMDDTHHMMSSZ>.jsonl`, beside it.
  - `os.rename` is atomic.
  - It runs under the vault mutation lock, so two upgrades never pick the same name.
  - A name already taken gets `-2`, `-3`, … An archive is never overwritten and never deleted.
  - A failure to archive never fails the upgrade, which has already succeeded. The CLI names the failure (its
    exception type only) on stderr, and the log stays live.
  - A process that dies after the upgrade but before the rename leaves the log live. Its lines are counted until
    the next upgrade archives them (documented in the module).
- **`ad report`.** The guard block is now `{denials, by_entry, archived: [{file, denials}], archived_denials}`.
  - `denials` counts the live file only.
  - The archives are listed by file name and line count. No line content is shown and there is no learner text;
    the entry and reader are code names.
  - The Markdown says "since the last upgrade" once an archive exists ("so far" before that), then lists the
    count by entry point and adds "N earlier denial(s) are archived (M archive(s) …); they are not counted
    above."
  - A report dict with the old `{"denials": n}` block still renders.
- **Docs.** `operation.py`'s module docstring and its `DENIALS` comment, and `report.py`'s guard-block comment,
  state the rule. The CLI `upgrade` help text is unchanged, so the CLI help snapshot is unchanged.

No new weight, margin or threshold. There is no parameter-registry key: the archive counter is a name collision
rule, not a parameter.

## 2. Tests (`tests/test_ad_denial_log.py`, 11)

Fail-first. On the commit with only the module and the tests (`abd5efa97`), before the wiring, 6 failed:

- successful upgrade archives;
- chained upgrade archives once;
- refused upgrade leaves the log in place;
- second upgrade never overwrites;
- a new denial line names the operation;
- old-format grouping and rendering.

The other 5 passed:

- the module's unit tests (append, counter on a taken name, no log);
- the failed-upgrade case, which holds trivially before the wiring;
- the no-log case.

All 11 pass after the wiring (`b2fe7c076`). The tests cover:

- a successful CLI upgrade (mvp-0.34 → mvp-0.35) archives the log, byte-identical, beside the database; the live
  count is 0; the summary lists the archive with its count;
- a chained upgrade (mvp-0.33 → mvp-0.35) archives once, named `mvp-0.33-to-mvp-0.35`;
- a refused upgrade ("vault is already mvp-0.35", exit 1) and an unknown target (exit 2) leave the log live and
  make no archive;
- a failed upgrade (`one_ask_upgrade._activate` raising) leaves the log live and makes no archive;
- no log: no archive and no live file created;
- two upgrades in the same second (stamp pinned) make two distinct archives, and the first keeps its single line;
  a third archive in the same second gets the counter (`-2`); no log returns None;
- the planted raw read in the slot's operation (`test_ad_guard._slot_serve`) logs lines whose `entry` is a
  `learnloop.` name and one of the refused operations' `guard.entry` values; `by_entry` sums to the line count;
- a mixed log (old line, two new lines, one torn line) counts 4 and groups `{entry: 2, unrecorded: 1,
  unreadable: 1}`, and the Markdown renders the count by entry and the archived line.

## 3. Gate

All test commands ran under `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`.

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- Targeted pytest, AD and contract files: 6063 passed.
  - `tests/test_ad_denial_log.py`, `test_ad_guard.py`, `test_ad_guard_offer_receipts.py`,
    `test_ad_guard_reachable_reads.py`
  - `test_ad23_contract.py`, `test_ad23_fix_r5.py`, `test_ad23_fix_r7.py`, `test_ad23_fix_r8.py`,
    `test_ad23_fix_review.py`
  - `test_ad3_monitoring.py`, `test_ad_protected_readings.py`, `test_ad23_intent_compose.py`,
    `test_ad23_inversion.py`, `test_ad23_pool_membership.py`
  - `test_cli_help_snapshot.py`, `test_architecture.py`, `test_salience_firewall.py`, `test_decider_landing.py`,
    `test_reading_hardening_landing.py`
- Targeted pytest, every test file that invokes the CLI `upgrade` command: 457 passed, 12 skipped, 1 xfailed (806.95s).
  - `test_ad23_successor.py`, `test_batch3_landing.py`, `test_exam_protection_identity.py`,
    `test_field_workbench_signals.py`, `test_intent_codex_rereview.py`, `test_lp_claim_fixes.py`
  - `test_method_explicit_upgrade.py`
  - `test_mvp09_upgrade.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`,
    `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`,
    `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`,
    `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`
  - `test_plan_follows_path.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`,
    `test_regrade_contract_upgrade.py`, `test_serve_eligibility_review.py`, `test_reader_ca2_one_ask.py`
- Not run, because nothing they cover changed:
  - durability lane: no migration and no DB/connection code;
  - frontend and cargo: untouched;
  - DB reference scripts: no schema change.
- No paid calls and no live calls. No owner-vault copies; synthetic vaults only.

The full suite runs at landing.

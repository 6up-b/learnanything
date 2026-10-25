# Storage S0 (clean tip): Codex review and fixes

Branch `storage/s0-clean-tip` (worktree `learnanything-lr1`), reviewed as the
diff `e9d4de1aa..c6266c306` by Codex (gpt-6-astra, high effort, read-only;
job `20261025-023747-Mb41ve`). Six findings. Each was reproduced first (a test
that failed on the reviewed code) and then fixed; none was rejected. No model
call, no paid call, no owner vault, no main-checkout file was touched. The one
manual script run read the `fixtures-local/owner-lane` copies (backup-API
copies of this worktree's git-HEAD versions, never the owner's) under
`env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Review

| Id | Severity | Title | Verdict | Commit | Test (reproduced first) |
|---|---|---|---|---|---|
| F1 | High | Landing validates a different database from the one the app will open | fixed | `06f164bd5` | `tests/test_s0_landing.py`: `test_copy_out_and_move_out_refuse_a_database_layout_s0_cannot_move[absolute,dotdot,symlink,not_sqlite]`, `test_check_and_verify_after_read_the_database_the_live_vault_config_names` |
| F2 | Medium | The landing gate accepts corrupt paper backups and missing textbook inventory | fixed | `06f164bd5` | `test_check_refuses_a_corrupt_paper`, `test_a_tracked_file_missing_from_the_working_tree_is_still_backed_up`, `test_a_wrongly_materialized_lfs_file_is_never_trusted`, `test_books_out_persists_the_inventory_from_git_before_copying`, `test_books_out_refuses_when_the_inventory_changed_since_its_manifest` |
| F3 | Medium | Moving the vaults disables the existing comparison safety check | fixed | `fcfe9df91` (+ marking in `06f164bd5`) | `tests/test_ai_compare.py`: `test_a_live_vault_moved_out_of_git_is_still_refused_and_its_copy_is_compared`, `test_an_unreadable_working_vault_mark_refuses`; `test_s0_landing.py::test_the_full_procedure_...` (the live vault is marked) |
| F4 | Medium | The documented recovery after a moved vault changes cannot work | fixed | `06f164bd5` | `test_after_a_moved_vault_changes_a_fresh_backup_of_the_moved_vaults_recovers`, `test_an_interrupted_landing_resumes`, `test_check_refuses_a_retired_copy_that_changed`, `test_move_out_refuses_a_vault_without_a_verified_backup` |
| F5 | Medium | G8's size limit is silently disabled for historical databases | fixed (bounded; the owner confirms the bounds, decision 5) | `bfe3f968b` | `tests/test_public_tip_guards.py::test_the_historical_databases_size_exception_is_bounded` (a 100 MB head database passed the old predicate) |
| F6 | Low | The default session guard still reads untracked vault databases | fixed | `5db984627` | `tests/test_tracked_fixture_databases.py::test_the_session_guard_reads_only_the_databases_git_tracks` |

16 of the 20 tests in the rewritten `tests/test_s0_landing.py` failed on the
reviewed script (the four that passed are the old refusals kept); both new
`test_ai_compare.py` tests and the F5 and F6 tests failed before their fixes.

### What changed

- **F1** (`scripts/s0_landing.py` `vault_database`). Each vault's
  `storage.sqlite_path` is read from its own `learnloop.toml` with
  `load_config(..., load_environment=False)` (no `.env`, no `settings.env`;
  no overlay touches that key). S0 supports only the plain layout: a relative
  `*.sqlite` path inside the vault and no symlink anywhere in it (outside the
  machine-local `.learnloop/`). Anything else (absolute, `..`, a symlinked
  database or directory, another file name, a missing database) is refused by
  `copy-out` and `move-out` before anything is copied or moved, with the hint
  to relocate it in S1 or by hand (spec §7.1 step 4). `copy-out` also checks
  that the backup holds the configured database. `check` and `verify-after`
  resolve the database from the live vault's actual config, and
  `verify-after` runs `integrity_check` on that file, not on a hard-coded
  `state.sqlite`. The tracked versions of all eight vaults have the plain
  layout (checked on the owner-lane copies); the owner's live copies are
  checked by the landing itself.
- **F2** (`media_inventory`, `books-out`, `check`). The inventory comes from
  git's index (`git ls-files -s`, `git cat-file blob`): a tracked file's
  expected sha256 is its LFS pointer's oid, else its blob's; an untracked file
  under `new_textbooks/` is listed with its current hash. `books-out` writes
  it to `S0-BOOKS-MANIFEST.json` before copying anything, refuses when the
  index later disagrees with it (a new `--books-root` then), copies a file
  only from bytes that hash to the expected value (working tree or LFS store;
  a plain tracked file the working tree lost comes from its blob), and
  removes a copy that does not verify. `check` requires the manifest, that it
  covers git's index, and that every entry (papers included) is in the books
  folder with its hash; after the merge it still verifies from the persisted
  manifest.
- **F3** (`src/learnloop/vault/working_vault.py`, `ai_compare.tracked_database_reason`).
  `move-out` marks each live working vault in `.learnloop/working-vault.json`
  with its resolved path and its directory's device and inode. A marked vault
  is refused in place, also after a later rename (same inode); a copy that
  carries the mark file (backup-API, `--copy-from`, `cp -a`) is a different
  directory and is compared. An unreadable mark refuses (fails closed). The
  mark sits under `.learnloop/`, which the landing manifests skip, so it does
  not make a live vault differ from its backup.
- **F4** (`copy-out`, `move-out`, `check`). `move-out` refuses a vault with no
  verified backup in the backup root and records each move in
  `S0-MANIFEST.json` as it happens. `copy-out --from-moved --backup-root <new>`
  backs up the vaults where `move-out` put them; a plain `copy-out` after the
  move says so. Every step resumes: `copy-out` keeps an earlier verified
  backup (it used to refuse because the directory existed), `books-out` skips
  verified copies, `move-out` skips moved vaults and marks any it moved
  before stopping. `check` compares each recorded retired copy with its
  backup too.
- **F5** (`tests/test_public_tip_guards.py`). The exemption by name is now a
  bound per database: the migration head at most 8 MiB (it gains a few tables
  per migration; 6,696,960 bytes at head 220), the frozen
  `mvp017_route_check_replay` at most 6 MiB (5,976,064 bytes; only
  `e238fa07a` can regenerate it). These are guardrails, not model parameters;
  S3's text dumps end them. The owner confirms or tightens them (stage record,
  owner decision 5).
- **F6** (`tests/conftest.py`). The session guard's repository side is
  `tracked_fixture_files("*.sqlite")`; the owner lane's copies come only from
  `LEARNLOOP_OWNER_VAULTS`.
- Audits: the landing's git calls go through one helper, approved in
  `tests/test_codex_lockdown_round3.py` as `("scripts/s0_landing.py", "_git", "subprocess.run")`
  (read-only `git ls-files` / `git cat-file blob`, fixed argv, no shell, no
  model call); `tests/test_sqlite_file_copies.py` records the script's one
  remaining `shutil.copyfile` (media only, each checked by sha256).
- The stage record (`docs/reviews/storage-s0-clean-tip.md`) now describes the
  landing as it is, including the claims the review found did not hold
  (every paper hashed, walkers and the session guard on tracked files only,
  the recovery instruction, G8's bounded exception), and closes the
  `ai compare` open finding.

### Claims the review found did not hold, now

- "Every textbook and paper has the right hash": papers and textbooks are
  verified against a persisted inventory taken from git's index.
- "Fixture walkers walk only what git tracks": so does the session database
  guard.
- "Run copy-out again to a new --backup-root": `copy-out --from-moved` does it
  after the move.
- G8: the size rule holds for every file, with a bounded, named exception for
  the two historical databases until S3.

## Gate (this step; the full suite runs once at landing)

Every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 35 kept, 0 broken |
| `pytest -n 6` on the 25 files below | 478 passed, 33 skipped (the `owner_vaults` lane and pre-existing skips) |
| `pytest -n 6 -m durability tests/test_migrations.py tests/test_tracked_fixture_databases.py tests/test_sqlite_wal_lifecycle.py` | 4 passed, 1 skipped |
| `LEARNLOOP_OWNER_VAULTS=fixtures-local/owner-lane pytest -n 6 tests/test_tracked_fixture_databases.py tests/test_migrations.py` (the guard with the owner lane on) | 48 passed |

No migration, schema, config, CLI, frontend or Rust change: no DB reference
regeneration, snapshot, vitest or cargo run needed (the CLI help snapshot
test ran and passed).

Test files run: `test_ai_compare`, `test_s0_landing`, `test_public_tip_guards`,
`test_tracked_fixture_databases`, `test_codex_lockdown_round3`,
`test_sqlite_file_copies`, `test_ad23_successor`, `test_config_refactor`,
`test_daily_loop_start_minutes`, `test_daily_plan_kill_switch`,
`test_field_workbench_signals`, `test_intent_recall_targets`,
`test_placement_fixture_copies`, `test_router_r2a_serving`,
`test_router_r2b_serving`, `test_yaml_fast_read`, `test_migrations`,
`test_receipt_exactness`, `test_receipt_derivation`, `test_architecture`,
`test_cli_help_snapshot`, `test_table_roles`, `test_ai_tool_isolation`,
`test_e0_isolation`, `test_coordinated_migrations`; plus `test_sqlite_wal_lifecycle`
in the durability run.

## Re-review (Codex job `20261025-025939-w2DcU8`, `c6266c306..2c10704dd`)

Verdict REOPENED: F1 reopened (a symlinked vault root), two new Mediums (F7,
F8). F2-F6 were not reopened. Each was reproduced first by a test that failed
on `2c10704dd` (6 of the 8 new tests failed; the other two pin behaviour that
already held: committed edits are backed up, and `check` refuses a manifest
missing a paper while git still tracks it) and then fixed; none was rejected.
No model call, no paid call, no owner vault, no main-checkout file.

| Id | Severity | Title | Verdict | Commit | Test (reproduced first) |
|---|---|---|---|---|---|
| F1 (reopened) | High | A vault root that is itself a symlink passes the preflight; `move-out` renames the link | fixed | `af08eb9e6` | `tests/test_s0_landing.py::test_copy_out_and_move_out_refuse_a_vault_root_that_is_a_symlink` (copy-out returned 0 on a relative `fixtures/linear_algebra -> actual-vault`), `::test_check_refuses_a_live_vault_that_is_a_symlink` |
| F7 | Medium | Media backup silently substitutes tracked bytes for local edits | fixed | `af08eb9e6` | `::test_books_out_refuses_uncommitted_edits_to_a_tracked_text_file`, `::test_check_refuses_uncommitted_edits_made_after_books_out`; `::test_committed_edits_to_a_tracked_text_file_are_backed_up` (passes before and after) |
| F8 | Medium | Reference papers become optional when absent from the index | fixed | `af08eb9e6` | `::test_books_out_refuses_when_a_paper_is_in_neither_the_index_nor_head` (an empty manifest was written), `::test_a_paper_staged_for_removal_is_recovered_from_head`; `::test_check_refuses_a_books_manifest_without_every_paper` (passes before and after) |

### What changed

- **F1** (`vault_database`): a vault root that is itself a symlink is refused
  before anything else is read. `os.walk` follows a symlink given as its root,
  and `os.rename` moves the link, not the vault. `copy-out`, `move-out`,
  `check` and `verify-after` share this preflight, so a symlinked live vault
  also fails `check`.
- **F7** (`_local_edits`, used by `books-out` and `check`): `books-out`
  refuses, before it writes the manifest or copies anything, when a plain
  (non-LFS) tracked file's working bytes differ from git's blob. The working
  file is then the only copy of the edits, so the owner must commit or
  discard them first. `check` reports the same thing if the edits were made
  after `books-out`. A missing working file is still restored from its blob.
  LFS files are left out, because a pointer or a wrongly materialized file in
  the working tree is expected there, and only the oid's bytes are trusted.
- **F8** (`media_inventory`, `_missing_papers`): the index decides first. A
  file already staged for removal (or `git rm --cached`) is recovered from
  HEAD (`git ls-tree -r HEAD`), and its bytes come from the working file, the
  LFS store or the blob, each only when it hashes to the expected value.
  `books-out` will not write a first manifest unless every `PAPERS` entry is
  in that inventory. `check` requires every paper in the persisted manifest,
  which also covers a manifest written by the earlier script. A paper found in
  neither the index nor HEAD is refused, with the hint to `git add` it or to
  land from a checkout that still tracks it. Its working bytes alone are never
  trusted.
- The new git reads (`ls-tree`, `rev-parse --verify HEAD`) go through the
  same `_git` helper, so the approved launch site in
  `tests/test_codex_lockdown_round3.py` is unchanged; only its comment now
  names the extra read-only commands.
- The stage record (`docs/reviews/storage-s0-clean-tip.md`) and the script's
  docstring describe the new refusals.

### Gate (re-review step)

Every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 35 kept, 0 broken |
| `pytest tests/test_s0_landing.py` (serial, on `2c10704dd` plus the new tests) | 6 failed, 22 passed (the reproductions) |
| `pytest -n 6` on the 7 files below, after the fix | 112 passed |

Test files run: `test_s0_landing` (28 tests), `test_codex_lockdown_round3`,
`test_sqlite_file_copies`, `test_ai_compare`, `test_public_tip_guards`,
`test_architecture`, `test_tracked_fixture_databases`. No migration, schema,
config, CLI, DB/connection, frontend or Rust change, so no durability,
snapshot, vitest, cargo or DB-reference run was needed.

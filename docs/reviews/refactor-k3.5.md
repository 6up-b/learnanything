# Refactor K3.5: apply recovery is safe and automatic

Branch `refactor/k3.5-apply-recovery`, based on main `72ace2968a` (K0 pins, K3.1-K3.3 and D2a landed). Step K3.5 of
arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in `docs/reviews/k2-ingestion-strategy-2026-11-11.md`
§3.1 from the K2 map's KD2 and crash windows W1-W6 (`docs/reviews/k2-ingestion-map-2026-11-11.md` §2.8). KM5 is not
here.

Rules held: no learner scoring change, no successor, no `algorithm_version` change; no live model call; a vault with
no pending intent opens, accepts and runs doctor as before (checked on copies, below). The orchestrator chose the
migration over the no-migration fallback; step 0 found the rebuild safe (no foreign key names `apply_intents`, no
trigger, one index), so the migration is used.

**After landing, the owner restarts the desktop app and the phone host: migration 255 runs when the desktop opens
each vault, and the phone host (a secondary) refuses a vault whose schema is behind until then.**

## The problem (KD2)

- Recovery wrote an intent's post-image over whatever a file held: `pre_hash` was recorded per target and never
  read; `materialize_targets` skipped a file only when it already held `post_hash`.
- Only `doctor --fix-state` recovered, though the module said "startup". The sidecar recovered facet actions only,
  so a crash between two renames (W2) left a half-applied vault that the app served and the next accept built on.
- Recovery skipped the content recalibration, and the apply stamped it after marking the intent applied, so a crash
  in between (W6) was never recovered.
- The maintenance feed's "Complete pending apply" action had no handler anywhere.

## Failing tests (red on the base, green after)

`tests/test_apply_recovery.py`. Red run: the base tree (`git archive 72ace2968a src migrations` under the gitignored
`fixtures-local/`) put first on `sys.path` (`-o pythonpath=...`), with a copy of the test file whose imports name
only what the base has; green on this branch.

| Test | Red on the base | Green |
| --- | --- | --- |
| `test_recovery_keeps_a_file_changed_after_the_intent_and_marks_it_conflicted` (P-fail 1) | recovery returned the intent as recovered: it wrote over the hand-edited file | the newer file kept, the other target unwritten, intent `conflicted` with the file, no DB effect |
| `test_a_crash_between_two_renames_is_completed_at_the_next_sidecar_bind` (P-fail 2: a real `os._exit` after the first of two renames, then `initialize`) | the LO file present, the practice item missing after the bind | both files, both items accepted, nothing outstanding |
| `test_an_accept_with_a_pending_intent_is_refused` (P-fail 3) | DID NOT RAISE: the second proposal applied over the pending one | `OutstandingApplyIntentError` naming the intent; no second intent |
| `test_recovery_runs_the_content_recalibration` (W6) | 0 recalibration markers after recovery | 1, the marker the apply stamps |
| `test_the_apply_recalibrates_before_it_marks_the_intent_applied` (W6) | 0 markers when the mark fails | 1 marker, the intent still pending, recovery completes it |

Also new, green: the pre-image rule as a unit (`test_materialize_writes_over_the_pre_image_only`, including an
unguarded write without `pre_hash`), no apply lock at a bind with nothing pending, a bind that opens with a
conflicted intent and leaves it, the sidecar accept's `apply_intent_outstanding` error with the intent named, an
accept whose target changes under it rolling back, doctor and the feed surfacing a conflict, `keep_files` settling
it and accepts opening again, and `complete` re-checking a conflict. Desktop:
`MaintenanceScreen.applyIntent.test.tsx` (both buttons call `resolve_apply_intent`).

## What changed

| File | What |
| --- | --- |
| `migrations/255_apply_intents_conflicted.sql` | `apply_intents` rebuilt temp-then-rename: `status` also admits `conflicted` and `set_aside`; nullable `conflict_json`, `conflicted_at`, `set_aside_at`; `idx_apply_intents_status` recreated unchanged |
| `src/learnloop/content/proposals/apply_protocol.py` | `ApplyTargetConflict`, `target_conflicts`; `materialize_targets` checks every target that carries `pre_hash` first and writes nothing if any file holds neither image; `complete_apply_intent` (materialize, sync, effects, recalibrate, mark applied; conflict marks `conflicted`); `recover_apply_intents` takes the vault lock only when something is pending; `resolve_apply_intent` (`complete`, `keep_files`) and `ApplyIntentResolutionError` |
| `src/learnloop/content/proposals/patches.py` | `OutstandingApplyIntentError(PatchApplicationError)`, raised first under the lock while an intent is pending or conflicted; a conflict at the accept's own rename rolls its intent back (nothing was written); `applied_content_learning_object_ids` and `recalibrate_applied_content` (moved out of the apply body, kept in this module so the frozen function-local edge to `substrate.replay` stays where it was), run before the applied mark |
| `src/learnloop/db/repositories.py` | `outstanding_apply_intents`, `apply_intent`, `mark_apply_intent_conflicted`, `mark_apply_intent_rolled_back`, `mark_apply_intent_set_aside`; the decoder reads `conflict_json` as `conflicts` |
| `src/learnloop_sidecar/context.py` | `_recover_apply_intents` at bind; failures and conflicts are logged and never block opening |
| `src/learnloop_sidecar/handlers/proposals.py` | `resolve_apply_intent` RPC; `accept_proposal_items` maps the refusal to `apply_intent_outstanding` with `details.intents` |
| `src/learnloop/ops/doctor.py` | `apply_intents:conflicted` (error, with the files) with or without `--fix-state`; the pending warning names `--fix-state` and the app's bind |
| `src/learnloop/ops/maintenance_feed.py` | notices from `outstanding_apply_intents`: `append_partially_complete` (pending; action `resolve_apply_intent`/`complete`, now `auto_resolution` so it clears) and the new `apply_conflicted` (action `resolve_apply_intent`/`keep_files`) |
| `apps/learnloop-tauri` | `resolve_apply_intent` passthrough (`commands.rs`, `main.rs`), `api.resolveApplyIntent`, the Maintain feed's button calls it for these two notices |

`materialize_targets` has two other callers that use it as a plain atomic write under the vault lock
(`facet_identity.authority.write_registry_text`, `ops.content_fixes`); they pass no `pre_hash` key and write as
before.

## The migration

255 (`ls migrations/` head was 254). Table role unchanged (`apply_intents` is `WORKFLOW`; no new table, no replayer).
The head fixture `fixtures/migration_head/state.sqlite` was upgraded in place: a `backup_database` copy outside the
checkout, `apply_migrations` under `upgrade_allowance(UPGRADE_SCRATCH_COPY)` (applied `[255]` only),
`wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), `integrity_check` ok,
`foreign_key_check` empty, written back with `backup_database`, no companion files. Against the 254 file only the
`apply_intents` definition changed (no rows there) and only `schema_migrations` gained a row. The fixture README has
the section "Refactor K3.5 (migration 255)" naming the head.

No new object joins the earlier migrations' `*_ADDED_OBJECTS` (the index keeps its name and definition); the table's
changed definition joins their "nothing else changed" diffs as `K35_ALTERED_TABLES = {"apply_intents"}`
(`tests/apply_intents_conflicted_migration_helpers.py`), added beside each `B1_ALTERED_TABLES` use in the 16 test
files whose diffs failed (a scripted, exact-pattern edit). All 55 migration and schema test files pass.

## Recovery order at bind

`SidecarContext.load`: open the repository (migrations, interrupted activation) → facet-identity recovery →
**apply-intent recovery** → one `load_vault` if either changed files → ingest binding → `sync_vault_state` → the rest.
The apply comes after the facet action because both check file state against their own record, so either order is
safe; this way the apply's state sync sees settled facets. The phone host attaches with `load_secondary` (no
migration, no recovery, no writer bound), so it does not recover; its accepts still meet the refusal.

## The refusal surface

`apply_accepted_items` raises `OutstandingApplyIntentError` (a `PatchApplicationError`, so every existing catch site
handles it: the CLI `accept` prints it, auto-apply in synthesis and append fails its job with it) while any intent is
`pending` or `conflicted`. Its message names the first intent and what to do; `.intents` lists
`{id, status, proposed_patch_id, paths}`. The sidecar's `accept_proposal_items` returns code
`apply_intent_outstanding` with `details.intents`. Conflicts surface in: `doctor` (error `apply_intents:conflicted`,
with the files, in plain and `--fix-state` runs), the Maintain screen's feed (`apply_conflicted`, action needed), and
the sidecar log at bind.

## The maintenance action: given its handler

The code decided it: every generic feed button on the Maintain screen had no `onClick`, and no sidecar method
matched the action, but a conflicted intent needs an owner's decision that no automatic path can make, and accepts
wait on it. So the action got a handler instead of being removed: the sidecar's `resolve_apply_intent` with
`complete` (a pending intent: run recovery now; a conflicted one: re-check, finishing it once each named file is back
at its pre-image or post-image) or `keep_files` (set a conflicted intent aside: files kept, its DB effects never run,
its proposal items stay pending, derived state synced). The feed's pending notice calls `complete`, the conflicted
notice calls `keep_files`.

## Copy check

Fresh backup-API copies (`copy_tree_with_databases`) of `~/learnloop-backups/20261109-copy` (`arxiv_v2`,
`linear_algebra`, `probability`; each `state.sqlite` at its root) under the gitignored `fixtures-local/k35/`, two copies
per vault: one run under the base tree (the `git archive` of `72ace2968a`), one under this branch. Each run: open
through `open_vault_repository` (the sidecar's opener: the coordinator migrates), `recover_apply_intents`, plain
doctor, then accept a synthetic one-LO proposal (this script's ids and text, under the vault's first concept) with a
frozen clock, then doctor again. Counts only; the copies were deleted afterwards.

| | `arxiv_v2` | `linear_algebra` | `probability` |
| --- | --- | --- | --- |
| head before → base / K3.5 | 250 → 254 / 255 | 250 → 254 / 255 | 250 → 254 / 255 |
| `apply_intents` rows (all `applied`), before → after the migration | 3 → 3 | 21 → 21 | 15 → 15 |
| ids preserved (hash of the sorted ids) | yes | yes | yes |
| columns after (base / K3.5) | 9 / 12 | 9 / 12 | 9 / 12 |
| recovered / outstanding at open (K3.5) | 0 / 0 | 0 / 0 | 0 / 0 |
| `integrity_check` | ok | ok | ok |
| synthetic accept | 1 applied, both trees | 1 applied, both trees | 1 applied, both trees |
| files the accept changed | 1 (the synthetic LO) | 1 | 1 |

No pending intent on any copy, so this is the "behaves as before" case: on every vault the base and K3.5 runs gave
the **same vault tree after the accept** (a hash over every file's bytes), **the same doctor issue counts** before
and after the accept (no `apply_intents:*` code in either), and the same row count in every table except
`schema_migrations` (one more row: 255). A pending or conflicted intent on a real vault is covered by the tests
above, not by these copies (none holds one).

## Durability

`--durable-sqlite` (production pragmas, WAL, fsync on) over `tests/test_apply_recovery.py` and
`tests/test_apply_write_ahead.py`: 22 passed; `--fresh-connections` over the same: 22 passed.

## Vault

`Workflows/Doctor Migrations and Recovery.md`: the findings table (pending and conflicted), the `--fix-state`
sentence, and a new section "Proposal apply recovery" (who recovers, the pre-image rule, the refusal, settling a
conflict). `Architecture/Content Pipeline.md` stage 7 and `Examples/Recovery and Rebuild Drill.md` point there.
The reference notes were regenerated once after the source commits (`dcf1eb5301`: 38 generated notes, mostly line
anchors and the new test's import lists, beside the three hand-written notes); a second `generate_all.py` run changed
nothing.

## Gates

- `scripts/affected_tests.py` on the diff selects the whole suite (the migration, the head fixture and
  `repositories.py` reach every test), so the selection was taken over the changed modules without those three
  (799 files) and run in eight chunks of 100 at `-n 4`, `-m "not arc_close"`, under the 5 GB cap, on `4f85aa885e`:
  14,392 passed, 0 failed. Plus all 55 migration and schema test files (713 passed), and the named gates
  (`test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`,
  `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_migrations`, `test_table_roles`,
  `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_apply_write_ahead`, `test_source_append`,
  `test_maintenance_feed`, `test_doctor`, `test_sidecar_append`, the new file) on the final tree: 460 passed.
- Pins: unchanged (no config default, no identity view touched).
- `lint-imports --no-cache`: 42 kept. `ruff check`: clean. The frozen function-local edge
  `content.proposals.patches -> substrate.replay` stays where it was (the recalibration helper lives in `patches.py`).
- Desktop: vitest (`MaintenanceScreen.applyIntent.test.tsx`, `MaintenanceScreen.transcription.test.tsx`, 7 passed),
  `npm run typecheck` clean, `cargo check` clean.
- The four vault validators pass; `scripts/check_gate_partition.py`: 30,969 collected, landing 30,909 + arc_close
  60.
- No full suite (the orchestrator's landing gate).

## Open items

- **Undo is not refused.** `reject_applied_items` (and the book's Undo) still runs while an intent is outstanding;
  the strategy asked only for accepts. A reject reverts applied items, not the outstanding intent's files.
- **A set-aside intent leaves its files as found.** If some targets were already at their post-image, those YAML
  changes stay while the items are pending; re-accepting restages from the current files. That is the owner's
  decision the notice asks for; nothing reverts them automatically (no pre-image content is stored, only its hash).
- **`facet_identity.authority.write_registry_text` writes `post_hash` without the `sha256:` prefix**, so its
  idempotent skip never matches (it always rewrites). Harmless and pre-existing; not changed here.
- **The `complete` re-check of a conflicted intent has no button** (the RPC takes it); the feed offers one action per
  notice.
- **D2b's broad test edits** touch test files; the 16 migration-diff files edited here may conflict mechanically.
- **Process notes.** The repository methods (`src/learnloop/db/repositories.py`) went in through a short exact-pattern
  script rather than the Edit tool; the Rust registration lines and the 16 migration-diff test files were scripted
  mechanical edits; everything else used the Edit tool. `npm ci --offline` and `cargo check --offline` ran with the
  real `HOME` (for their caches), in the 5 GB scope; every Python and CLI run used the isolated environment.

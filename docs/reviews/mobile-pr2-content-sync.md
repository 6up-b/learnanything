# Mobile PR-2: content sync never restores stale scheduling state

Stage `mobile-pr2-content-sync`, branch `mobile/pr2-content-sync` in `learnanything-ad1`, base `eae00d58a`
(migration head 220 on this base, latest algorithm `mvp-0.32`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §3.3
PR-2, §10 G6b (the PR-2 clause), §11 (`test_state_sync_scheduling_race.py`); as-built note §9.3. Only PR-2: PR-3..PR-8,
the workers and the adapter are not started. No migration, no successor, no new config key or parameter, no model
call (no paid calls were made).

## 1. The defect

`sync_vault_state` read every `practice_item_state` row once (`repository.practice_item_states()`), then, for each
item whose content hash or active flag differed, called `upsert_practice_item_state` with the *snapshot's*
difficulty, stability, retrievability, due date and last-attempt time. An attempt committed by another process
between that read and the write (the phone host, the desktop sidecar, the TUI, a CLI command) was overwritten: its
new memory state and due date reverted to the pre-attempt values. The same pattern was in two more places:

* the create branch: a snapshot with no row, then an attempt that created the row, then the sync's upsert with all
  scheduling fields `NULL`, which wiped the attempt's state entirely;
* the deactivate branch (an item gone from the vault): the snapshot's fields written back with `active = 0`;
* the desktop's incremental watcher refresh (`SidecarContext.refresh_vault_files`), which read one row and wrote it
  back the same way. It is the path the desktop takes on every Practice Item edit, so it is the one most likely to
  meet a phone attempt.

## 2. What changed

* **`Repository.update_practice_item_content_state(item_id, *, active, content_hash, clock=None)`**
  (`src/learnloop/db/repositories.py`): a targeted `UPDATE` of `active`, `content_hash` and `updated_at` only, the
  change §3.3 PR-2 names. (The first version also took an `expected` row for a compare-and-swap; the Codex review
  fix removed it, see below.)
* **`Repository.initialize_practice_item_state(…, active=True)`**: the existing insert-if-missing
  (`ON CONFLICT DO NOTHING`) gained an `active` argument (default unchanged for its one caller, `pf_publish`).
* **`reconcile_practice_item_state(repository, item_id, item, *, state, review_parked, measurement_superseded,
  content_hash=None, clock=None) -> (outcome, active)`** (`src/learnloop/substrate/state_sync.py`): the per-item
  step both sync paths now share.
  1. Decide `active` with `practice_item_activatable` from the caller's snapshots (the row and the two lifecycle
     sets). If flag and hash already agree, nothing is written.
  2. Otherwise, inside one `Repository.atomic()` (`BEGIN IMMEDIATE`) transaction: re-read the row, the
     review-parked set and the measurement-superseded set, decide again from them, and insert the row if it is
     missing or update the two content columns if they differ.

  Why the decision runs under the write lock: it reads the row and the lifecycle tables. An attempted
  `diagnostic_probe` is single-use (its attempt writes `active = 0` and `last_attempt_at`); a measurement
  correction supersedes its original; a parked instance waits for review. A sync deciding from inputs read before
  any of those commits would reactivate the item. As first built, the update was guarded on the row snapshot and,
  when the guard missed, decided again from a fresh read and wrote *without* a guard; Codex review F1/F2 showed that
  an attempt landing after that fresh read, or a correction or parking landing after the lifecycle sets were read,
  was still undone. Under the lock nothing can commit between those reads and the write. Neither write touches a
  scheduling field.
* **`sync_vault_state`** uses the helper for the create and update branches and `set_practice_item_active(…,
  active=False)` (flag only, already existing) for the deactivate branch. Counts are unchanged in meaning; a row an
  attempt created first counts as neither created nor updated.
* **`SidecarContext.refresh_vault_files`** (`src/learnloop_sidecar/context.py`) uses the same helper, so the desktop
  watcher and a full sync share one write rule. It still calls `deactivate_practice_item_serving` when the item ends
  inactive, and still reports the item as changed.
* **Docs:** spec §9.3 (as built); the DB reference regenerated (`db_generate_reference.py`), keeping only the four
  config notes whose `context.py` line citations moved (the rest of the regeneration was commit-stamp churn and was
  not committed, to spare the landing merge).

## 3. Persisted and served meaning

No change without a concurrent writer: the old code wrote back exactly the values it had just read, so the row's
scheduling columns were already what they now keep. The differences are `updated_at` (no longer bumped by the
incremental refresh when flag and hash already agree; nothing reads it for decisions) and the race itself. No replay
input, projection, scorer or scheduler reads changed, so no successor is needed under the algorithm-change
playbook, and nothing touches `mvp-0.33`/`mvp-0.34`. No migration; `practice_item_state` stays `compat` in
`table_roles.py` and `DENIED` in the AD protected-table registry (neither registry names repository methods).

## 4. Interaction with the rebuild-equivalence fix (landing in `learnanything-merge2`)

That fix makes replay restore retired items as inactive. PR-2 does not touch replay or
`reset_learning_object_derived_state`, and the two compose:

* Replay deletes rows for an LO's attempted items and re-creates them with full upserts. If it deletes a row between
  a sync's snapshot and its write, the sync's read under the write lock finds nothing and it inserts a fresh row
  (replay cannot interleave with that transaction); replay's later full upsert overwrites it. If replay finished first, the sync's
  insert is a no-op and replay's row stands. Either way replay's state wins, which is what rebuild equivalence needs.
* What PR-2 does **not** change: the sync's activation rule. A full sync reactivates every YAML-active item that is
  not review-parked, measurement-superseded, a microprobe or an attempted diagnostic probe. If the fix retires items
  for some other reason, a later sync would reactivate them exactly as it did before PR-2. That rule lives in
  `practice_item_activatable` (now reached through `reconcile_practice_item_state`); if the fix needs a new retired
  class to survive syncs, that is where it belongs, and it will apply to the incremental refresh too. A textual merge
  conflict is unlikely: the fix lives in replay, this change in `state_sync.py`, the two repository methods and the
  watcher refresh.

## 5. Tests

New, `tests/test_state_sync_scheduling_race.py` (module marked `durability`: production pragmas and WAL on vaults
built `fresh=True`). Each race test commits a real self-graded attempt (`complete_self_graded_attempt`, no model)
inside the window, through a second `Repository` (its own connection) or a second Python process, and checks that
the attempt's five scheduling fields survive and the content columns still reconcile:

| Test | Branch | Window |
|---|---|---|
| `test_content_change_sync_keeps_an_attempt_committed_after_its_snapshot` | update (decision re-taken under the write lock writes the edited hash) | after `practice_item_states()` |
| `test_creating_sync_keeps_a_row_an_attempt_inserted_after_its_snapshot` | create (row appeared first) | after `practice_item_states()` |
| `test_deactivating_sync_keeps_an_attempt_committed_after_its_snapshot` | deactivate | after `practice_item_states()` |
| `test_a_stale_snapshot_never_reactivates_a_probe_an_attempt_retired` | decision from the row under the lock | unit, direct call |
| `test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read` | desktop watcher refresh | after `practice_item_state(id)` |
| `test_an_attempt_from_a_second_process_survives_a_concurrent_content_sync` | update, real second process (G6b's PR-2 clause) | after `practice_item_states()` |
| `test_a_probe_attempt_after_the_fallback_read_stays_retired` | Codex F1: real probe attempt; decision read under the lock | after the row read |
| `test_a_measurement_correction_after_the_lifecycle_reads_keeps_the_original_retired` | Codex F2: real measurement correction | after `superseded_measurement_item_ids()` |
| `test_review_parking_after_the_lifecycle_reads_keeps_the_item_inactive` | Codex F2 (`review_parked` twin) | after the `pending_review` read |

The subprocess runs under a minimal environment (`PATH`, an empty `HOME` and `LEARNLOOP_CONFIG_DIR` under
`tmp_path`, `PYTHONPATH`); the self-graded path makes no provider call.

**Red on the base.** With `state_sync.py` and `context.py` restored to `eae00d58a` (the new helper appended so the
module imports), the five race tests fail and only the direct helper unit test passes; with the change all six pass.

## 6. Gate (this step; the full suite runs once in the landing gate)

All pytest runs inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6` at most.

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Targeted pytest (`-n 6`), **655 passed, 6 skipped** (the skips are owner-vault-marked): `test_state_sync_scheduling_race`,
  `test_state_sync`, `test_vault_watcher_refresh`, `test_exam_protection_identity`, `test_pf_generation`,
  `test_router_p2_bridge`, `test_secondary_attach`, `test_mobile_host_coexistence`, `test_diagnostic_probe_single_use`,
  `test_diagnostic_probe_freshness`, `test_probe_instance_generation`, `test_measurement_corrections`,
  `test_daily_loop_lo_lifecycle_serving`, `test_doctor`, `test_attempt_write_order`, `test_replay`,
  `test_sidecar_contract`, `test_architecture`, `test_table_roles`, `test_repository_scopes`,
  `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_mobile_allowlist`,
  `test_ad_guard`, `test_probe_dialogue`.
* Durability lane (`-m durability`, `-n 6`): `test_state_sync_scheduling_race`, `test_mobile_host_coexistence`,
  `test_secondary_attach`: **8 passed.**
* Every test file that imports `state_sync` or calls `sync_vault_state` (137 files, `-n 6`, list from `git grep -l "sync_vault_state\|state_sync" -- 'tests/test_*.py'`): **2058 passed, 22 skipped, 2 xfailed** in 20 min 25 s, on the final code (only docs changed after it).
* DB reference: `db_generate_reference.py` then `db_validate_reference.py`: **errors: []** (no schema change; run
  because the generated config notes cite `context.py` lines this change moved).
* No frontend, Tauri or schema change, so no npm, vitest, cargo or migration fixture work.

## 7. Open questions

1. **The reverse race (not PR-2's scope).** An attempt writes its whole `practice_item_state` row
   (`_upsert_practice_item_state_record`), including the `active` and `content_hash` it computed from the item it
   graded. A sync that changes the flag while an attempt is being graded (for example retiring a superseded item)
   can be overwritten by that attempt, and the attempt path also sets `active = 1` for any non-probe item it grades.
   A later content sync repairs the hash and a superseded/parked flag, but nothing guarantees when one runs (queue reads do not trigger one), so the stale flag can be served more than once until then (the Codex review corrected an earlier "one stale serve at most"). The
   symmetric fix is for attempt recording to write only its scheduling columns (and `active = 0` for a probe).
   Suggest folding it into PR-4 or the M2 two-process gate (G6b), whose `test_mobile_two_process.py` would catch it.
2. **The rebuild-equivalence fix's retired class** (§4): if it retires items for a reason
   `practice_item_activatable` does not know, a later sync reactivates them, before and after PR-2 alike. Worth a
   look when that fix lands.

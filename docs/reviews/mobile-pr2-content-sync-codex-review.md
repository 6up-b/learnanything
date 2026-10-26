# Mobile PR-2 (content sync): Codex review and fixes

Stage `mobile-pr2-content-sync`, branch `mobile/pr2-content-sync` in `learnanything-ad1`. Codex review job
`20261025-200549-v1xTHh` (source-level interleaving analysis; Codex could not run tests because `systemd-run`
could not reach its user bus). The implementer record is `docs/reviews/mobile-pr2-content-sync.md`. No migration, no
successor, no new config key or parameter, no model call and no paid call in this step.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The fallback update can reactivate an attempted diagnostic probe | fixed | `c36ecd6c4` | `test_a_probe_attempt_after_the_fallback_read_stays_retired` (red on `c9cab102a`: the attempted probe ended `active = 1`) |
| F2 | Medium | Retrying with stale lifecycle sets can undo an accepted measurement correction (and `review_parked` alike) | fixed | `c36ecd6c4` | `test_a_measurement_correction_after_the_lifecycle_reads_keeps_the_original_retired`, `test_review_parking_after_the_lifecycle_reads_keeps_the_item_inactive` (both red on `c9cab102a`: the superseded original and the parked item ended `active = 1`) |

Claims Codex flagged as not holding, all corrected in `4dc445de7`:

* Spec §9.3 "a stale snapshot cannot reactivate a diagnostic probe its attempt just retired": true now, by the new
  mechanism; the bullet describes it.
* Implementer record §2 "if the row changes yet again … the item is left to that writer": the fallback is gone; §2
  describes the locked decision and records why the first version was replaced.
* Implementer record §7 "one stale serve at most" for the reverse race (attempt overwriting a sync's flag): no such
  bound exists, since repair waits for some later content sync and queue reads do not trigger one. Reworded in the
  record and in §9.3's "not built here". The reverse race itself stays out of PR-2's scope (open question 1, proposed
  for PR-4 / the G6b two-process gate).

## Reproduction

Each new test (in `tests/test_state_sync_scheduling_race.py`, durability lane: production pragmas, WAL, fresh vault)
commits a real lifecycle change right after one of the reads the activation decision depends on:

* **F1:** a vault-authored `diagnostic_probe`, prompt edited. After the sync's snapshot, another writer changes the
  row's hash (so the old snapshot guard missed). Right after the sync's next read of the row, a real diagnostic
  administration (`apply_attempt`, own `Repository`) commits `active = 0` and `last_attempt_at`. On the old code
  the unguarded fallback then wrote `active = 1`.
* **F2:** an attempted ordinary item, prompt edited. Right after the sync read `measurement_superseded`, a real
  `create_measurement_correction` (own `Repository`) records the correction, writes the corrected sibling and runs
  its own sync, which retires the original. On the old code the guarded write missed, the fallback re-read the row
  but reused the stale set, and wrote `active = 1`.
* **F2, parked twin:** right after the sync read the `pending_review` set, an instance-review parking commits (a
  `probe_item_family_links` row with `review_status = pending_review`, the item's flag cleared). The old code
  reactivated it the same way.

The hook checks whether the syncing repository holds the write lock (a second connection's `BEGIN IMMEDIATE` with
`busy_timeout = 0`). On the old code it does not, so the change commits inside the window and the test fails on the
final flag. With the fix it does: the change is run after the sync instead, and the test asserts both the final
flag and that the decision read was taken under the lock (F1).

## Fix

`reconcile_practice_item_state` (`src/learnloop/substrate/state_sync.py`):

1. The caller's snapshots (the row, `review_parked`, `measurement_superseded`) only decide whether a write may be
   needed. If flag and hash already agree by the snapshot, nothing is written (skipping a write cannot reactivate
   anything; a change committed since is its writer's to reconcile).
2. Otherwise, inside one `Repository.atomic()` (`BEGIN IMMEDIATE`) transaction: re-read the row,
   `pending_review_instance_ids(repository)` and `superseded_measurement_item_ids()`, decide with
   `practice_item_activatable`, then insert the row if missing or update `active` and `content_hash` only, and
   commit. No attempt, correction or parking can commit between those reads and the write.

`Repository.update_practice_item_content_state` lost its `expected` compare-and-swap argument (no longer needed
under the lock; no other caller). Both the full sync and the desktop watcher's incremental refresh go through the
helper, so both are fixed. The extra cost is two small set queries per item that actually needs a write; items
whose flag and hash already agree open no transaction.

## Gate (this step; the full suite runs once in the landing gate)

All pytest runs inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6` at most,
one run at a time.

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Red check: the three new tests on the pre-fix code: **3 failed** (each on the final `active` flag).
* Targeted pytest (`-n 6`): **658 passed, 6 skipped** (owner-vault-marked skips): `test_state_sync_scheduling_race`,
  `test_state_sync`, `test_vault_watcher_refresh`, `test_exam_protection_identity`, `test_pf_generation`,
  `test_router_p2_bridge`, `test_secondary_attach`, `test_mobile_host_coexistence`, `test_diagnostic_probe_single_use`,
  `test_diagnostic_probe_freshness`, `test_probe_instance_generation`, `test_measurement_corrections`,
  `test_daily_loop_lo_lifecycle_serving`, `test_doctor`, `test_attempt_write_order`, `test_replay`,
  `test_sidecar_contract`, `test_architecture`, `test_table_roles`, `test_repository_scopes`,
  `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_mobile_allowlist`,
  `test_ad_guard`, `test_probe_dialogue`.
* Durability lane (`-m durability`, `-n 6`): `test_state_sync_scheduling_race`, `test_mobile_host_coexistence`,
  `test_secondary_attach`, `test_repository_scopes`: **18 passed.**
* Sync sweep: every test file that calls `sync_vault_state` or names `state_sync`, `reconcile_practice_item_state` or
  `update_practice_item_content_state` (137 files, from `git grep -l` over `tests/test_*.py`; every sync write now
  runs in a transaction): **2061 passed, 22 skipped, 2 xfailed** in 27 min 17 s (`-n 6`), on `4dc445de7` (only this review file and the record's test table changed after it).
* DB reference: `db_generate_reference.py` then `db_validate_reference.py` under `env -i` with empty
  `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`: **errors: []**. Kept only the three table notes whose lists changed
  (`practice_item_state` now names `Repository.update_practice_item_content_state()`; `measurement_contract_corrections`
  and `probe_item_family_links` name the race test file); the other 420 regenerated notes were commit-stamp churn.
* No frontend, Tauri or schema change: no npm, vitest, cargo or migration fixture work.

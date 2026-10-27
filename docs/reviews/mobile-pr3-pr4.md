# Mobile PR-3 and PR-4: the synthesis sweep is the primary's; atomic sessions and ownership

Stage `mobile-pr3-pr4`, branch `mobile/pr3-sweep-primary-only` in `learnanything-merge2`, base `5c6a0834f`
(migration head 224, latest algorithm `mvp-0.35`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §3.3 PR-3 and PR-4,
§6.5, §8 (the `sessions` columns and `session_handoffs`), §10 G6a (the synthesis clause), G6b (PR-2's reverse
clause) and G10 (its PR-4 clauses), §11; as-built notes §9.4 and §9.5. Also PR-2's open question 1
(`docs/reviews/mobile-pr2-content-sync.md`): the reverse race.

Scope: PR-3 and then PR-4 only. No host (M2) code, no phone UI, no desktop UI. One migration (**225**), no algorithm
successor, no new config key or parameter. No model calls and no paid calls were made. Synthetic vaults only, and
no owner-vault copies.

## Commits

| Commit | What |
|---|---|
| `9eb86be0a` | PR-3: `sweep_abandoned_synthesis` on `DurableIngestJobs.bind` and `IngestRunner.recover_stale_leases`, and its tests |
| `bf21ae4e9` | PR-4, the race: a live attempt writes only its scheduling columns, with the interleaving tests |
| `3d7dd4b11` | PR-4: the session operations, the sidecar's ownership checks, migration 225, head fixture `migration_head_225`, and the paths moved |
| `0bf8af07c` | PR-4: the earlier migrations' "nothing else changed" diffs read 225's objects; fixture README; DB reference regenerated |
| (this record) | the record and the spec's as-built notes |

## 1. PR-3: the abandoned-synthesis sweep belongs to primary hosts only

**The defect (latent).** `IngestRunner.recover_stale_leases` does two things on a host's first bind:

- it expires stale leases;
- it runs `_finalize_abandoned_synthesis_runs_locked`, which fails every `created`/`running` synthesis run older than
  the lease cutoff, unless a synthesis *job* holds a live lease.

Synchronous synthesis runs (the desktop's RPC, a CLI command) hold no lease. A secondary host binding ingest while
the desktop runs one would therefore fail the desktop's live run. Nothing binds ingest on a secondary yet:
`load_secondary(bind_ingest=True)` is refused (§9.2). So the fix is the seam the spec names, before M3 uses it.

**Change.**

- `recover_stale_leases(*, sweep_abandoned_synthesis=True)` skips only the sweep when False. Lease fencing still
  runs: expired leases become `failed(interrupted)` and their queued siblings resume.
- `DurableIngestJobs.bind(…, sweep_abandoned_synthesis=True)` passes the flag at the first bind of a vault, the only
  place it recovers.
- The default is the primary's. `SidecarContext.load`, the CLI's three `recover_stale_leases` calls and every
  existing bind are unchanged.

**Tests.** `tests/test_synthesis_sweep_primary_only.py` (durability lane, fresh vaults) seeds a leaseless synchronous
run and a leased job, both from 2020:

| Test | Checks |
|---|---|
| `test_a_secondary_bind_fences_expired_leases_and_never_sweeps_synthesis` | bind with False: run stays `created`, lease `failed(interrupted)` |
| `test_the_primary_default_still_sweeps_abandoned_synthesis_runs` | default bind: run `failed` (the control) |
| `test_recover_stale_leases_skips_only_the_sweep_when_asked` | the runner method; then a primary recovery still sweeps |
| `test_a_desktop_synchronous_run_survives_a_secondary_start_in_another_process` | G6a's clause: a real second process (spawn) binds with False on WAL |

**Red on the base:** with the flag ignored (the sweep always runs), the three secondary tests fail and the control
passes. With the change, all four pass.

## 2. PR-4, part 1: PR-2's reverse race

**The defect.** PR-2 stopped content sync from writing back stale scheduling fields. The reverse direction was still
open:

- `record_attempt_outcome` upserted the whole `practice_item_state` row;
- that included the `active` flag (1 for every non-probe item) and the `content_hash` it computed from the vault the
  answer was graded against.

So a content sync committed by another process while an answer was being graded was undone by the attempt's commit:

- a retired, superseded or parked item reopened;
- an edited item got its old hash back.

Nothing bounded when a later sync would repair it.

**Change** (`Repository._record_attempt_practice_item_state`, used only by `record_attempt_outcome`, the live write).

- An existing row takes only `difficulty`, `stability`, `retrievability`, `due_at`, `last_attempt_at` and
  `updated_at`.
- Its `active` can only close (`MIN(row.active, computed)`), so a diagnostic probe's single use (`active = 0`) still
  lands, and a non-probe attempt never reopens a row.
- `content_hash` is never written to an existing row.
- A missing row is inserted whole, as before. That covers an item's first attempt, and a row that replay deleted.
- **Replay is unchanged.** `replace_attempt_derived_outcome` keeps the full upsert. `reset_learning_object_derived_state`
  deletes the rows it rebuilds first, so replay always inserts. `keep_practice_items_inactive` re-closes what was
  closed outside the ledger, so live and replayed rows still agree.

This is the change the PR-2 record suggested ("attempt recording writes only its scheduling columns, and `active = 0`
for a probe"). It is the mirror of PR-2's rule: content sync owns `active` and `content_hash`, and an attempt owns the
memory state.

**Tests.** `tests/test_attempt_content_state_race.py` (durability lane, fresh vaults). Each race test grades an answer
against a vault loaded *before* a content change. It then commits the sync right before the attempt's transaction
opens (a hook on `apply_attempt`, after grading), through a second `Repository` or a second Python process.

| Test | Window | Checks |
|---|---|---|
| `test_an_attempt_graded_before_a_retiring_sync_keeps_the_item_closed` | YAML `status: retired`, synced in the window | `active` stays 0, the hash stays the sync's, the scheduling fields land |
| `test_an_attempt_graded_before_an_editing_sync_keeps_the_edited_hash` | prompt edited, synced in the window | the edited hash stays, `active` 1, the scheduling fields land |
| `test_a_retiring_sync_from_a_second_process_survives_an_attempt_graded_before_it` | the retiring sync in a real second process | as the first (G6b's reverse clause) |
| `test_a_probe_attempt_still_closes_its_single_use_surface` | none (control) | a real probe administration still sets `active = 0` |
| `test_an_attempt_on_an_item_with_no_row_inserts_the_whole_row` | none (control) | the insert path keeps the computed flag and hash |

The second process runs with a minimal environment (`PATH`, empty `HOME` and `LEARNLOOP_CONFIG_DIR` under
`tmp_path`, `PYTHONPATH`). The self-graded path makes no provider call.

**Red on the base:** with `record_attempt_outcome` back on the full upsert, the three race tests fail and the two
controls pass. With the change, all five pass.

## 3. PR-4, part 2: atomic session operations and ownership

### Migration 225 (`225_session_ownership.sql`)

The §8 rows, exactly:

- `sessions.owner_device_id TEXT` (NULL is the desktop) and `sessions.owner_generation INTEGER NOT NULL DEFAULT 0`.
  These are `ALTER TABLE ADD COLUMN`, so every existing row reads `(NULL, 0)`: a desktop session that was never handed
  off.
- `session_handoffs` (`id`, `session_id` → `sessions`, `kind` ∈ `adopt`|`replace`, `from_device_id`, `to_device_id`,
  `generation ≥ 0`, `checkpoint_json`, `at`), one index, and two triggers that make it append-only.
  - It is classified `RECEIPT` in `db/table_roles.py`. It is not DERIVED, so it has no replayer.
  - It is not in the AD guard's registry, so it is unreadable inside an AD operation, like `sessions`.
- No foreign key on the owner. NULL is a real owner (the desktop), and a revoked device keeps its `mobile_devices` row.
- **Number.** 225 is the next free number on this base. The stage brief says another stage may take 225. If it lands
  first, this migration, `migration_head_225` and the paths take the next free number together (the runner is
  set-based).

**Head fixture `migration_head_225`.**

- Built from a backup-API copy of the tracked, sanitized `migration_head_224/state.sqlite`, with only 225 applied
  (`apply_migrations` under `UPGRADE_SCRATCH_COPY`, run under `env -i` with empty `HOME`, `CODEX_HOME` and
  `LEARNLOOP_CONFIG_DIR`).
- Checks after the upgrade: `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1),
  `integrity_check` ok, `foreign_key_check` empty, no companion files. It was copied into place with the backup API.
- Diff against 224:
  - added: exactly `session_handoffs`, its autoindex, `idx_session_handoffs_session` and the two triggers;
  - changed: only `sessions`;
  - rows: only `schema_migrations` differs. The two sessions keep every value and read `(NULL, 0)`.
- Git records the directory rename `migration_head_224 → migration_head_225`, and the README has a section for it.
- The hard-coded paths moved to 225:
  - 41 tests;
  - the sanitizer's usage line;
  - `db_generate_reference.py` and `db_validate_reference.py` (both with `SCHEMA_HEAD = 225`).
- The 14 earlier migrations' "nothing else changed" diffs now import `PR4_ADDED_OBJECTS` and `PR4_ALTERED_TABLES`
  (from `tests/test_session_ownership_migration.py`). Their applied lists end in 225.

### The operations (`src/learnloop/db/stores/session_ownership.py`, a `Repository` mixin)

Each operation is one `Repository.atomic()` (`BEGIN IMMEDIATE`) transaction that reads the session rows under the
write lock and decides from them. Refusals raise `SessionOwnershipError(code, message, details)`.

- **`start_session_exclusive(fields, owner_device_id, replace=None, *, settle_checkpoint=None)`.**
  - It reads the open sessions.
  - **None open, or only the caller's own:** it creates the session and ends every other one at its last activity,
    as the old two-commit start did. The caller's own session is replaced silently, with no receipt.
  - **One another device owns, with `replace` null or naming any other id:** it raises `session_open_elsewhere` with
    §6.5's snapshot (`session_id`, `started_at`, `owner_device_id`, `owner_label`, `owner_generation`,
    `current_practice_item_id`, `has_draft`, `draft_first_line`, at most 120 characters).
  - **`replace` equal to that session's id (start fresh):** it records a `replace` handoff holding the session's
    checkpoint (so the draft is preserved), ends it, and creates the new session. This is a compare-and-swap on the
    id: a stale `replace` gets `session_open_elsewhere` again.
  - `settle_checkpoint` runs inside the transaction on the checkpoint of every session about to end. The sidecar
    settles a pending self-grade disclosure there, as it did before.
- **`adopt_session(session_id, owner_device_id, expected_generation, *, current_item_ineligible=None)`.**
  - A compare-and-swap on `owner_generation`. It sets the owner, increments the generation, and records an `adopt`
    handoff (with the checkpoint as it stood, for the receipt).
  - The checkpoint itself is untouched, and the session id carries over. So do the caps, the stable `submission_id`
    and the offer binding.
  - **A stale generation** raises `session_moved` with the current owner and generation. The spec names no code for
    this case. `session_moved` is the one that tells the client to re-read.
  - **An adopt by the device that already owns the session** changes nothing and returns its snapshot, so a retried
    adopt is harmless.
  - `current_item_ineligible` is PR-6's seam. When it says the checkpoint's current item is ineligible **and** the
    draft is non-empty, the adopt raises `current_item_desktop_only` and changes nothing. With no draft, the adopt
    proceeds.
- **`require_session_owner(session_id, device_id, *, require_open=True)`.** The check every session-scoped write makes:
  - `not_found` when the session is missing;
  - `session_moved` (owner label and generation) when another device owns it;
  - `session_ended` when it has ended and the write needs an open session.
- **`end_session_owned(session_id, device_id, *, clear=None)`.** The ownership check, the end and the checkpoint clear
  in one transaction. Ending an ended session returns it unchanged, as before.
- **Reads:** `device_label` (a device's label, or `desktop` for NULL), `session_owner_snapshot` and `session_handoffs`.

### The sidecar (`handlers/sessions.py`, `practice.py`, `teach_back.py`)

- **`start_session`** goes through `start_session_exclusive`, with the desktop as owner and the disclosure settle
  callback.
- **`require_owned_session(ctx, repository, session_id)`** is the ownership check. It runs at:
  - `update_session_checkpoint` and every other checkpoint patch (`patch_checkpoint`, whose read-merge-write is now
    one `atomic()` with the check inside it, as §6.5 asks);
  - `clear_session_checkpoint` (check and clear in one transaction);
  - `save_practice_draft` (before it binds the offer; the patch checks again inside its transaction);
  - `record_self_grade_disclosure` (through the patch);
  - `skip_practice_item`;
  - the acceptance of `submit_attempt` and `submit_dont_know`;
  - `start_teach_back` and `submit_teach_back_turn`;
  - `acknowledge_practice_submission` (check, settle and compare-and-delete in one transaction);
  - `end_session` (through `end_session_owned`).
- **Unrestricted:** reads (`get_session` and the rest), `recover_practice_submission`, and an already-recorded
  submission's cached receipt, which `submit_*` returns before acceptance. The spec's list does not include hint
  requests, hint reveals or workbench writes, and they are not checked.
- **`request_device_id(ctx)`** returns None, the desktop. It is the one place PR-5 replaces with the request origin.
  A device is never a parameter.
- **`ownership_error`** maps a refusal onto `SidecarError`:
  - `not_found`, and an ended session (`validation_error`, "Session … has ended."), keep the codes and messages the
    desktop always got;
  - `session_moved`, `session_open_elsewhere` and `current_item_desktop_only` are new, not retryable, and carry the
    snapshot as details.

**Desktop behaviour.** Desktop starts create sessions with `owner_device_id` NULL. Nothing in this stage can make
another device own a session, because only the host (M2) will call `adopt_session` or start with a device id. So every
desktop response is what it was, except:

- the start is atomic: two concurrent starts no longer end each other;
- a checkpoint patch serializes with other writers.

The desktop's adopt / start-fresh / cancel prompt for `session_open_elsewhere`, its `session_moved` banner and a
`replace` parameter on the `start_session` RPC are M2's (§6.5). No RPC method, parameter or response key changed, so
the desktop RPC contract, the serializer snapshot and the mobile allowlist are unchanged.

### Tests

`tests/test_session_ownership.py` (durability lane, fresh vaults, 18 tests). The other device is a second `Repository`
acting as one (`dev_phone` and `dev_tablet` rows in `mobile_devices`). The desktop is a sidecar context attached with
`load_secondary`, which binds no workers and leaves no thread.

| Test | G10 clause |
|---|---|
| `test_interleaved_starts_from_two_writers_leave_exactly_one_open_session` | interleaved starts: the first start pauses right after creating its session; the second runs in another thread |
| `test_concurrent_starts_from_two_processes_of_one_device_keep_one_open_session` | 2 real processes × 5 barrier-aligned starts |
| `test_a_start_from_another_device_never_ends_the_open_session_silently` | `session_open_elsewhere` and its exact snapshot; a stale `replace` |
| `test_starting_fresh_keeps_the_replaced_draft_and_ends_that_session` | draft preserved in `session_handoffs`; the receipt is append-only |
| `test_a_device_replaces_its_own_session_silently` | own session replaced, no receipt |
| `test_adopt_is_a_compare_and_swap_that_carries_the_session_and_its_checkpoint` | adopt carries the id and checkpoint; a stale generation; an idempotent retry; adopting back |
| `test_adopting_never_loses_a_draft_on_an_item_the_device_cannot_answer` | `current_item_desktop_only`; no draft, so the adopt proceeds |
| `test_two_devices_adopting_at_once_leave_one_owner` | concurrent adopt compare-and-swap |
| `test_every_session_scoped_write_from_the_old_owner_is_session_moved` (×8) | each of the eight listed writes after the phone adopted: `session_moved` with the owner, nothing written, reads still served |
| `test_the_owner_writes_as_before_and_ended_sessions_keep_their_old_errors` | desktop codes and messages unchanged |
| `test_the_desktop_start_reports_a_phone_session_instead_of_ending_it` | the desktop's start through the RPC |

`tests/test_session_ownership_migration.py` (4 tests) covers:

- the number and the table roles;
- existing rows kept and read as `(NULL, 0)`;
- the receipt's CHECKs, foreign key and append-only triggers;
- the head fixture holding exactly 225's objects in rollback mode.

**Red on the base:** with the sidecar's `start_session` restored to the two-commit sequence, the interleaving test
fails (the two starts end each other and no session stays open), and so does the desktop-start test. The ownership
tests fail by construction on the base, which has neither the columns nor the codes.

## 4. Persisted and served meaning

> **Superseded by the Codex review (F4, `docs/reviews/mobile-pr3-pr4-codex-review.md`).** The second bullet below
> (a closed row stays closed until the next sync) changes which items are served even without a concurrent writer,
> so the attempt write is now the successor **mvp-0.36** (`ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION`, kill switch
> `practice.attempt_keeps_content_state`); below the tag, or off, the attempt upserts the whole row as before. The
> text below is the original reasoning, kept as written.

**No successor** under the algorithm-change playbook:

- no scorer, scheduler, projection or replay input changed;
- the new columns and table are read by nothing that computes evidence.

The attempt write is the only change to an existing derived row. Without a concurrent writer, it differs from the old
write in two ways:

- **An attempt on an item whose row is closed no longer reopens it.** The row can be closed while its YAML is active:
  review-parked, measurement-superseded, an attempted probe, or a deactivation kept by replay.
  - Before, the next content sync re-decided the flag by the same rule (`practice_item_activatable`). So the old write
    only reopened the row until that sync.
  - Now the row stays as the sync rule left it until that sync, which reopens it if the rule allows.
- **`content_hash` is not refreshed by an attempt.** The sidecar syncs on every load and on every watched edit, so the
  row's hash is already the item's.

Rebuild equivalence holds: replay deletes and re-inserts the rows, then re-closes what was closed before the rebuild.
No config key, parameter or constant was added. The 120-character draft preview is a display bound (the spec's "the
draft's first line"), not a model parameter.

## 5. Gate (this step; the full suite runs once in the landing gate)

All pytest runs inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6` at most,
one at a time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** |
| New files while building: `test_synthesis_sweep_primary_only` (4), `test_attempt_content_state_race` (5), `test_session_ownership` (18) | all passed; the red-on-base checks are in §1–§3 |
| Every test file naming the head fixture (41) + `test_session_ownership_migration`, `test_tracked_fixture_databases`, `test_table_roles` | first run: 603 passed, 36 failed (the expected earlier-migration diffs). Fixed, then the 16 migration files: 119 passed, of which 12 still failed (the altered-table sets); fixed, then those 6 files: 33 passed |
| **Targeted set**, 374 files (`docs/reviews/artifacts/mobile-pr3-pr4-targeted-tests.txt`): every file that calls a changed function (`start_session`, `end_session`, checkpoint update/clear/patch, `save_practice_draft`, `skip_practice_item`, `acknowledge_practice_submission`, `submit_attempt`, `submit_dont_know`, teach-back, ingest bind/lease recovery, `practice_item_state`, `apply_attempt`/`complete_self_graded_attempt`, session/checkpoint reads), the head-fixture files, and the contract set (architecture, CLI help snapshot, desktop RPC contract, sidecar serializer snapshot, sidecar contract, mobile allowlist, table roles, tracked fixture databases, coordinated migrations, migrations, replay, rebuild equivalence, shadow rebuild, repository scopes, public tip guards, SQLite file copies, secondary attach, host coexistence, PR-2 race) | **12,630 passed**, 43 skipped, 3 xfailed, **5 failed** in 44 min 31 s. 3 failures are `test_codex_lockdown_round2` (the machine's Codex CLI 0.164.0, which fails on main too and is another stage's fix). 2 were this stage's: `test_architecture::test_sql_writes_stay_in_registered_owner_modules` (the new store registered as a SQL owner) and `test_attempt_write_order` (its hook moved to the live write's new method). After those fixes, both files: **19 passed** |
| Durability lane (`-m durability`) on the new files, the PR-2 race, secondary attach, host coexistence, repository scopes, the 14 migration-diff files, figure requests, tracked fixture databases and coordinated migrations | **59 passed** |
| DB reference: `db_generate_reference.py` then `db_validate_reference.py` | **errors: []** (354 table notes; regenerated at head 225, committed whole) |

No frontend, Tauri or config change, so no npm, vitest, cargo or defaults-snapshot work.

## 6. Open questions

1. **Migration number.** 225 may be taken by another stage first. Rename the file, `migration_head_225`, the paths
   and `SCHEMA_HEAD` together at landing, and rebuild the head from main's tracked head.
2. **The stale-adopt code.** The spec names no code for a stale `expected_generation`; this stage returns
   `session_moved` with the current owner and generation. Does the owner want a distinct code, for example
   `session_generation_stale`?
3. **G10's cap-boundary clause.** "Concurrent admission at the probe-observation cap boundary never exceeds the cap"
   is not built here. Cross-device admission can no longer race, because the non-owner's writes are refused. The
   remaining case is the host's two workers acting for one device, which belongs to M2 with the workers.
4. **Desktop handling (M2).** Today the two new codes reach the desktop only if a device owns a session, which nothing
   can arrange yet. M2's desktop needs:
   - the adopt / start-fresh / cancel prompt for `session_open_elsewhere`;
   - the `session_moved` banner;
   - a `replace` parameter on `start_session`;
   - an `adopt_session` RPC for "take it back".
5. **Writes outside the spec's list.** Hint requests and reveals, workbench writes and `recover_practice_submission`
   are not ownership-checked. Should any be added before M2?

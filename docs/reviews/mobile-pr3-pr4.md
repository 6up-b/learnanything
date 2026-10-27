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

## Landing onto main (2026-10-27)

Landed in `learnanything-merge2` on `mobile/pr3-sweep-primary-only` (stage tip `92af02c3b`, base `5c6a0834f`) by merging
`main` twice: `a25e9b45d` (the learner-report successor, mvp-0.36, migration 225, `migration_head_225`) and then
`416a9ddfe` (the AD denial-log archival at upgrade). Main was neither fast-forwarded nor pushed. The learner-report
successor landed first, so this stage's successor is now **mvp-0.37** and its migration **226**.

### Commits and conflicts

| Commit | What |
|---|---|
| `57375428f` | `--no-ff` merge of `main` `a25e9b45d`. Conflicts, resolved keeping both sides: the chain (`algorithm_versions.py`: `SUPERSEDED_CLAIMS_ALGORITHM_VERSION` then this stage's constant), the upgrade CLI (help, dispatch, the unknown-target list), both activation completers (`cli/runtime.py`, `learnloop_sidecar/context.py`) and the journal docstring, the defaults snapshots (`config/template.py`), and 14 test files (chain pins, comments, and earlier-migration schema diffs, which now take both `SUPERSEDED_ALTERED_TABLES` and `PR4_ADDED_OBJECTS`/`PR4_ALTERED_TABLES`). The ~430 reference notes and the head fixture were taken from main and regenerated or rebuilt afterwards. |
| `0048ada3b` | The renumbering. `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION = "mvp-0.37"`, one constant, appended after mvp-0.36. `attempt_content_state_upgrade.PREDECESSOR` is now mvp-0.36 and its upgrade (`upgrade_to_superseded_claims`); its completion hands any other link's journal to `superseded_claims_upgrade.complete_interrupted_activation`, which hands it on in turn. Both completers install this module's completion. `225_session_ownership.sql` is now `226_session_ownership.sql`. `migration_head_225` was `git mv`'d to `migration_head_226` and rebuilt (below). The 5 hard-coded paths and `SCHEMA_HEAD = 226` in both DB reference scripts follow, as do every test path naming the head (51 files) and every earlier-migration "nothing else changed" pin (`[..., 225, 226]`, max 226). The defaults fingerprints were recomputed for mvp-0.35, mvp-0.36 and the new mvp-0.37; the branch had already recomputed mvp-0.9 to mvp-0.34 for `practice.attempt_keeps_content_state`. The template `.pyc` was cleared. Latest-version pins (`LATEST == "mvp-0.37"`, every `*_VERSIONS` set gains mvp-0.37) and the CLI help snapshot were updated. Interactions (i) and (ii) were tested. |
| `684664e9a` | The DB/config reference regenerated at head 226. |
| `31c28b737` | `--no-ff` merge of `main` `416a9ddfe`. **No conflicts.** The archival runs in the CLI `upgrade` command after the final step, so it covers `--to mvp-0.37` and every chain through it. |
| `711bc671e` | Interaction (iii) tests. The reference regenerated again: only `cli/app.py` citation line numbers and test lists moved. |

The diff against main adds **no tracked database or binary other than the head fixture**: `git diff --numstat -M main`
lists only `fixtures/{migration_head_225 => migration_head_226}/state.sqlite`. Neither `.gitignore` changed, and
nothing under `fixtures-local/` is tracked.

### The head fixture

`fixtures/migration_head_226/state.sqlite` was rebuilt from main's tracked, sanitized `migration_head_225/state.sqlite`:

- a backup-API copy, with only `226_session_ownership.sql` applied through `apply_migrations` under
  `UPGRADE_SCRATCH_COPY`;
- `wal_checkpoint(TRUNCATE)` (0, 0, 0) and `journal_mode=DELETE` (header bytes 1/1);
- `integrity_check` ok and `foreign_key_check` empty;
- copied into place with the backup API, with no companion files.

226 adds its 5 objects and the two `sessions` columns. Only `schema_migrations` and `sessions` (the new columns, both
sessions `(NULL, 0)`) changed rows. Every companion file is byte-identical to main's. The README has a new section,
and the branch's own `migration_head_225` was dropped.

### Interactions (`tests/test_pr4_superseded_claims_landing.py`, `tests/test_attempt_content_state_successor.py`)

- **(i) The replace seam vs PR-4's attempt write and ownership** (`test_landing_i_a_too_easy_retirement_during_a_session`).
  - On the desktop sidecar at mvp-0.37, in one session: answer, then a `too_easy` retirement (the first report).
  - Then a second answer on the same LO, while a second `too_easy` retirement of that item commits between the grading
    and the attempt's transaction (another writer).
  - The second report replaces the first (`superseded_by`) atomically with its re-anchor. The attempt keeps the
    retirement's closed row and its content hash; its scheduling columns land.
  - After a phone adopts the session, the desktop's `submit_attempt` is `session_moved` and writes nothing. Its
    retirement of another item still lands, because `retire_practice_item` is not session-scoped: §9.5 does not list
    it.
  - `rebuild --shadow` is **0/0/0** after the race and again at the end.
  - The control at mvp-0.36 (`test_landing_i_control_...`) shows the same seam, but the row reopens.
  - Nothing was broken, so no fix was needed.
  - A real wall clock leaves ~1e-9 logit and 1 s due-time noise between live and replay at every version, the
    predecessor's included: live keeps sub-second times and the ledger stores whole seconds. The test therefore holds
    the system clock at whole seconds and steps it explicitly.
- **(ii) An interrupted mvp-0.36 activation, then `upgrade --to mvp-0.37`.**
  - With the CLI's completion installed, the opener hands the mvp-0.36 journal down the chain and completes it. The
    upgrade then reports "mvp-0.36 -> mvp-0.37", leaving no journal and both activations recorded.
  - With no completion installed, an attach refuses with "`learnloop upgrade --to mvp-0.36`" and leaves the vault as it
    was. The mvp-0.37 upgrade itself still completes the mvp-0.36 activation first, then activates mvp-0.37.
  - An mvp-0.35 (CA2) journal is handed down two links and completed.
  - On the three owner copies (a real `os._exit(17)` after mvp-0.36's publication, then `upgrade --to mvp-0.37`): all
    three complete, with no journal left. The shadow afterwards is the `algorithm_version` stamp only.
- **(iii) The AD denial-log archival (main `416a9ddfe`).**
  - `upgrade --to mvp-0.37` archives the log **exactly once per command**: from mvp-0.36 directly, and chained from
    mvp-0.35, where the archive is named `…archived-mvp-0.35-to-mvp-0.37-…`.
  - A refused upgrade leaves a live log in place: one already at the tag, or a chain refused at its first link from
    mvp-0.8.
  - On the probability copy, the 6 historical lines were archived once by the chained upgrade, and once by each
    `--to mvp-0.36` in (a).

### Regeneration

- DB reference: `db_generate_reference.py`, then `db_validate_reference.py`: **errors []** (354 table notes; config
  field count 1,065, with `practice` at 2 keys).
- CLI help snapshot: regenerated. Only the `upgrade` entry changed.
- The sidecar serializer snapshot, desktop RPC contract, embedding recipe pins, mobile allowlist and config refactor
  tests pass as merged (359 passed). No RPC, serializer or allowlist change.
- `tests/test_ad_guard_reachable_reads.py` passes with `session_handoffs` and the new `sessions` columns, with no AD
  column-class change needed.

### Gate (at `711bc671e`; `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing-pr34/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (5G scope); `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,289 passed, 1 failed**, 89 skipped, 44 xfailed. pytest time 2,323.4 s (38:43); wall time 38 min 47 s, with no lock wait. The failure is the known load flake `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`; the parity scripts were running alongside. Rerun alone 3 times, with no other full suite running: **3/3 passed**. No faulthandler dump and no hang. A run started before the second merge was stopped and does not count. |
| durability (`-m durability`, 5G scope) | **176 passed**, 1 skipped (72 s) |
| owner lane (`-m owner_vaults`, fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/landing-pr34/owner-lane/`) | 80 passed, **9 failed**: the 9 recorded at the learner-report landing (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`, and the three probability-data ones in `test_daily_plan_kill_switch`, `test_field_workbench_signals` and `test_router_r2a_serving`). **Main's own tree** (`git archive 416a9ddfe`, `PYTHONPATH` on its own fresh copies) gives the same 80 passed and the same 9 failed. |
| frontend / Tauri | not run: nothing under `apps/` changed |

Iteration runs before the gate were targeted: 70 files, 1,422 tests, with 3 pin failures that were then fixed and
rerun.

### Parity (fresh backup-API copies of the same mvp035 owner copies; `fixtures-local/landing-pr34/`, scripts in `scripts/pr34_*.sh`)

Setup: `base/` holds the copies, all at mvp-0.35. Routes go to the `127.0.0.1:9` blackhole (65 tasks). The only route
pointing elsewhere is the opt-in `embedding` route, which is off and has no key. `code_main` is
`git archive 416a9ddfe`; `code_branch` is `git archive 711bc671e`. Every run went through `env -i` with empty dirs.
`run.py`'s audit hooks refuse Codex process starts and non-loopback sockets; no audit line was written.

- **(a) `upgrade --to mvp-0.36`, main's code vs the branch's** (then a primary sidecar load; a second main copy is the
  noise control).
  - Every pre-existing row is identical: 18,813 / 10,300 / 23,713 rows in 358 tables. The only raw differences are the
    3 tables that differ between main and main's own second copy (activation timestamps).
  - The branch adds only the new columns and table:
    - `session_handoffs` (empty) and its 4 objects;
    - `sessions.owner_device_id`, NULL on every session (17 / 1 / 0), and `owner_generation` 0;
    - `schema_migrations` +226.
  - Integrity ok; foreign keys 0.
  - `rebuild --shadow` right after the upgrade: mastery 21 / 18 / 34, facet 0, schedule 0, identical on both sides.
    Every change is the `algorithm_version` stamp only, as at the earlier landings.
  - After `rebuild-derived-state` on each side: **0/0/0** on both. A normalized row comparison (ULIDs and times masked)
    of main vs branch then shows no differing table; the branch only adds `schema_migrations` +1 and
    `session_handoffs`.
  - `doctor` is identical: 57 issues / 1 error, 102 / 48 and 76 / 47, all known content errors.
- **(b) `upgrade --to mvp-0.37`** (branch code, on copies of (a)'s branch vaults). It prints
  "mvp-0.36 -> mvp-0.37" and leaves no journal.
  - **0 LOs and 0 item schedules moved.**
  - Rows are preserved. The only changes are the projection activation's rewrite of the facet rows (36 / 1 / 2
    `facet_capability_evidence`, 76 / 2 / 4 `facet_recall_state`), the `parameter_registry` refresh (352), and +1
    `derived_state_rebuilds` and +1 `parameter_registry_manifests`.
  - Every existing session keeps `owner_device_id` NULL (the desktop), and `session_handoffs` stays empty.
  - **Serving: no change.** The Today queue and the certification/curve dumps are identical after the version stamp.
    The daily plan picks the same blocks and items; only the router card's `card_hash`/`snapshot_hash` move, because
    the card carries the version.
  - The rows mvp-0.37 could serve differently, if an attempt met one (closed while the YAML is active), number 1 / 10 /
    0.
  - Shadow right after the upgrade: the stamp only (21 / 18 / 34 mastery). After `rebuild-derived-state`: **0/0/0**.
  - After a primary load and **12 live attempts** (with two `too_easy` retirements on one LO, the replace seam:
    claims 2 -> 3 with 1 superseded, 1 -> 2 with 1, 2 -> 3 with 1): **0/0/0** on all three.
  - Without that rebuild the live shadow is the activation's stamp only.
  - The bare `upgrade` goes from mvp-0.36 to mvp-0.37. `--to mvp-0.37` from mvp-0.35 chains through mvp-0.36.
  - `doctor` shows only the known content errors (1 / 48 / 47).
- **(c) The kill switch off reproduces mvp-0.36.**
  - On copies at mvp-0.36, at mvp-0.37 with `practice.attempt_keeps_content_state = false`, and at mvp-0.37 on: close
    one open row (as the sync rule keeps a parked or superseded row), answer it, then run 12 live attempts with two
    retirements.
  - mvp-0.36 and mvp-0.37-off both reopen the row, and their whole `practice_item_state` table is identical.
  - mvp-0.37-on keeps it closed (`inactive_state`), and only that row differs.
  - Mastery, schedules and Today are identical across all three after the version stamp. The next primary load's
    content sync re-decides the manually closed row the same way in each.
- **(d) An interrupted mvp-0.37 activation** (`os._exit(17)` after the config publication) on all three copies:
  - `upgrade --to mvp-0.37` completes it ("completed the interrupted activation of mvp-0.37"; run again: "vault is
    already mvp-0.37").
  - The desktop start completes it.
  - Both equal the clean upgrade: 0 LOs moved.
  - `Repository`, `open_vault_repository` without a completer and the secondary attach refuse with "The upgrade to
    mvp-0.37 did not finish ... run `learnloop upgrade --to mvp-0.37`". The remote schema check raises
    `SchemaMismatch`. Each leaves the vault as it was.
  - Plain `doctor --json` is a read-only attach and refuses too (the journal stays), as at the earlier landings.
- **(e) `ad report --json`: no new denials.**
  - linear_algebra and arxiv_v2: 0 throughout.
  - probability: 6 live denials at mvp-0.35 (its historical lines). (a)'s upgrade archived them, so from then on the
    report shows 0 live and 6 archived, unchanged after the upgrade to mvp-0.37 and after the live run.
- **Receipts and calls.** No run wrote a `model_call_receipts` row: 59 copies hold 0, and the 32 probability copies
  hold the source's 56 historical receipts. The empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty.
  **Spend: $0.** Nothing under `~/learnloop-vaults`, `~/learnloop-retired` or `~/learnloop-books` was opened or listed.

**Found here, not from this stage.** Answering a row closed *outside the ledger* (the harness's
`set_practice_item_active(False)`) leaves `rebuild --shadow` at mastery 1 / schedule 1 on that item's LO and row:
different `due_at` and logit. **Main's code at mvp-0.36 gives the same** (`cy3`), and an open-row control is 0/0/0 on
both sides (`cy4`, `cy5`). It is identical at mvp-0.36, mvp-0.37-off and mvp-0.37-on, so PR-4 neither causes nor
closes it. It needs its own look: a replay of a deactivation that has no ledger event.

### Owner notes

- Back up each vault, then close the desktop app, MCP and the phone page.
- Run `learnloop upgrade --to mvp-0.37`; the bare `upgrade` now targets it. It accepts mvp-0.36 directly, and mvp-0.9
  to mvp-0.35 through the chain (mvp-0.35 vaults pass through the kept-replaced-claims mvp-0.36). The command
  archives the AD guard's denial log once, at the end.
- At the activation nothing moves: 0 LOs and 0 schedules on all three copies, and every session stays the desktop's.
  From the tag on, an answer never reopens a question that was retired, parked or set aside, or brings back its old
  text.
- Kill switch: `[practice] attempt_keeps_content_state = false` restores mvp-0.36's whole-row write, with no downgrade.
- If an upgrade is interrupted, rerun the same command or open the desktop app.

### Open items (carried from the stage)

- **A distinct code for a stale adopt.** A stale `expected_generation` returns `session_moved` with the current owner
  and generation. Does the owner want its own code, for example `session_generation_stale`? (§6, question 2)
- **G10's cap-boundary clause is M2's**: the host's two workers acting for one device. (§6, question 3)
- **The M2 desktop prompts**: the adopt / start-fresh / cancel prompt for `session_open_elsewhere`, the
  `session_moved` banner, a `replace` parameter on `start_session`, and an `adopt_session` RPC. (§6, question 4)
- **`request_device_id` returns None (the desktop) until PR-5** replaces it with the request origin. Until then
  nothing can make a device own a session.
- **Writes outside §9.5's list are not ownership-checked**: workbench, tutor, Ask, daily-plan and the other
  session-keyed writes outside practice. (§6, question 5)
- **The closed-outside-the-ledger replay divergence** recorded above, which is pre-existing on main.

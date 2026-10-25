# Mobile PR-1: secondary attach

Stage `mobile-pr1-secondary-attach`, branch `mobile/pr1-secondary-attach` in `learnanything-ad1`, base `fa2eb72f8`
(migration head 220, latest algorithm `mvp-0.31`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §3.1 (M2: secondary
attach mode, content freshness), §3.3 PR-1, §10 G12, §11 (`test_secondary_attach.py`); reconciled with
`docs/specs/spec_storage_sync_v1.md` §6.2 and §6.9. Only PR-1: PR-2..PR-8, the workers and the adapter are not
started. No migration, no successor, no new config key, no model call (no paid calls were made).

## 1. What changed

> The Codex review's fixes (`docs/reviews/mobile-pr1-secondary-attach-codex-review.md`) change three points below: `load_secondary` publishes only a settled load (`settled_load_vault`) and refuses an unsettled one (`vault_unsettled`); the freshness window starts at the after-load check and does not advance on a failed refresh; and `content_files` prunes by name at the root only, follows directory links, keeps every name a file is reachable by (cutting only cycles) and fingerprints each link's target (the re-review's F3 and F5).

* **`SidecarContext.load_secondary(vault_path, *, bind_ingest=False)`** (`src/learnloop_sidecar/context.py`):
  1. takes the content fingerprint, then loads the vault's files (`load_vault`);
  2. attaches the database with `Repository.attach(read_only=False)` only if `schema_is_current` holds, else
     `SidecarError("schema_mismatch")` naming `learnloop doctor --fix-state --vault …`. The context is left
     unchanged on a refusal, and a missing database is refused, never created;
  3. on a vault switch, closes the previous vault's map builds and revokes its OpenRouter grants, as `load()` does;
  4. publishes the vault (bumping `vault_generation`), marks the context `secondary`, records the fingerprint, and
     binds the in-memory map-build registry so a serve's background builds can run in this process.

  It runs none of `load()`'s primary duties: migration (`open_vault_repository`), facet-identity recovery,
  `sync_vault_state`, reference-question adoption, ingest binding and lease recovery, the post-attempt worker
  binding, `refresh_canonical_projection_on_startup`, `schedule_certification_cold_probes`,
  `prepare_new_revisions`, `run_startup_maintenance`, and the maintenance recoveries (hint work, post-attempt
  jobs, import key checks, reading builds, book preparation). It is not a read-only mode: handlers on the context
  write as they do on a primary.
* **Reloads stay secondary.** `reload()` on a secondary context runs `load_secondary` again. Roughly 40 handlers
  call `ctx.reload(maintenance=False)` after their writes, and a primary reload migrates, syncs, adopts and
  re-projects, so without this the first handler write would have turned the host into a primary. Only an
  explicit `load()` (for example `app.open_vault`) makes a context primary; it clears the flag.
* **Refusals for modes not built yet:** `bind_ingest=True` (`secondary_ingest_unavailable`; M3's promotion runner
  and PR-8's submit-only binding do not exist), and `load_secondary` on a context already holding a vault as
  primary (`vault_loaded_as_primary`; demotion is PR-8's).
* **`refresh_if_content_changed(*, now=None)`**: the per-request freshness check. It compares
  `vault_content_fingerprint(root)` with the fingerprint taken before the last load, at most every
  `CONTENT_FINGERPRINT_TTL_SECONDS` (2.0 s, the G12 bound; a guardrail on stat cost, not a model parameter), and on
  a mismatch reloads with `load_secondary`. Because the fingerprint is taken *before* the load, a file written
  while the load ran makes the next comparison differ, so such a write is never missed.
* **One fingerprint for both secondaries.** C1a's chat runtime (`learnloop.remote.runtime`) already had
  `content_files` and `vault_content_fingerprint` (path, size and `mtime_ns` of every `.yaml/.yml/.toml/.md` outside
  dot-directories and the raw source store, as a digest). They now live next to `load_vault` in
  `learnloop.vault.loader`, as the spec asks, together with `content_digest` and `CONTENT_FINGERPRINT_TTL_SECONDS`.
  The runtime imports them and keeps its public names (`FINGERPRINT_TTL_SECONDS`, `content_files`,
  `vault_content_fingerprint`), so its settle logic is unchanged.
* **`learnloop.db.migrate.schema_is_current(sqlite_path)`**: the exactly-this-code's-migrations check, read-only.
  `remote.runtime.check_schema` now uses it. The mobile host's identical M1 check (`learnloop_mobile/host.py`) was
  left as built.
* **Spec:** the mobile spec gains §9.2 "As built (PR-1)" and a note on §3.1's fingerprint bullet.

## 2. Tests (`tests/test_secondary_attach.py`, 11 tests)

"Writes nothing" is checked three ways:
- every table's rows and the schema, before and after;
- every vault file's bytes (except the database and its companions), before and after;
- an SQLite authorizer, installed through `learnloop.db.scopes.connection_hook`, that refuses and records any
  INSERT, UPDATE, DELETE, CREATE, DROP or ALTER on connections opened during the attach.

The vault is seeded with work a primary load acts on: a leaseless synchronous synthesis run older than the lease
cutoff, a leased ingest job, and item state that content sync has not written.

| Test | Checks |
|---|---|
| `test_load_secondary_writes_nothing_where_load_writes` | No write by any of the three checks. The synthesis run survives. No ingest runner and no post-attempt supplier are bound. Control: the same vault, loaded as a primary on a backup-API copy, does write (content sync) |
| `test_reload_and_switch_of_a_secondary_stay_secondary` | `reload()`, `reload(maintenance=False)` and a vault switch write nothing to either vault and stay secondary. The generation bumps once per load |
| `test_secondary_handlers_still_write` | The repository is writable (a queue-revision bump commits) |
| `test_secondary_refuses_a_schema_it_would_have_to_migrate` | A database one migration behind gives `schema_mismatch`, stays byte-for-byte equal, and leaves the context unloaded |
| `test_secondary_never_creates_a_missing_database` | Refused; no file created |
| `test_secondary_refusals_for_unbuilt_modes` | `bind_ingest=True`; demoting a primary; fingerprint refresh on a primary |
| `test_content_fingerprint_reload_within_the_freshness_bound` | G12: a YAML edit is not reloaded inside the 2 s window, and is reloaded at exactly 2 s, writing nothing. No change means no reload |
| `test_a_change_during_the_load_is_loaded_at_the_next_comparison` | A write that races the load is picked up at the next comparison |
| `test_fingerprint_sees_renames_and_older_mtimes` | A rename with the same size, mtime and count; a rewrite back-dated to an older mtime |
| `test_fingerprint_covers_every_file_the_loader_reads` | Drift guard: an audit hook records every file `load_vault` opens under the vault, and each one must be in `content_files` |
| `test_second_process_attaches_beside_a_writing_primary_on_wal` (`durability`) | A spawned second process runs `load_secondary` on a fresh WAL vault while the parent holds `BEGIN IMMEDIATE` with an uncommitted write. The attach must finish in under `busy_timeout`, so any write attempt would have failed it. The secondary does not see the uncommitted write. The database and the files are unchanged. After the parent commits, the child sees the new queue revision without a reload, and sees a YAML edit at its next request past the bound |

**Mutation checks**, run by hand and then reverted:
- Adding `sync_vault_state` to `load_secondary` fails four tests, including the two-process one.
- Dropping `.md` from the fingerprint's suffixes fails the drift guard.

## 3. Reconciliation with storage spec §6.9 (roles: hub, primary, clients)

The storage spec postdates the mobile spec's PR-1 text. Where the two differ, this build follows the storage spec
and records the difference here.

1. **Post-attempt worker: storage wins.** The mobile spec's list of skipped work (§3.1) does not name the
   post-attempt worker. Storage §6.2 makes it a primary duty: "the diagnosis of an attempt made on any surface, run
   in the primary's process". §6.9 also relies on it ("a diagnosis queued by the host waits until something in
   the desktop process notifies its worker"). So the secondary leaves the worker unbound, and queued diagnoses stay
   durable for the primary. Queue discovery, which fixes the wait, is PR-8. See open question 1 for one
   consequence for M2.
2. **`load()`'s list has grown since the mobile spec cited `context.py:45-80`.** It now also covers facet-identity
   recovery, reference-question adoption, AD preparation of new revisions, and the maintenance recoveries. All of
   these are primary duties in storage §6.2's list, and the secondary skips them all. There is no conflict, only a
   stale citation, which §9.2 notes.
3. **`bind_ingest` as a boolean is too narrow.** Mobile M3 wants a promotion-only runner (`bind_ingest=True`).
   Storage PR-8 wants a submit-only binding for the desktop secondary, while the mobile host keeps `False`. That is
   three modes, not two. PR-1 keeps the spec's signature and refuses `True`, so PR-8 can turn the flag into a mode
   without a silent behaviour change. **Conflict to settle in PR-8.**
4. **Fingerprint form.** The mobile spec says "file count and newest `mtime_ns`". Storage §6.2 reuses "the mobile
   spec's `vault_content_fingerprint`" for the hub's content re-sync. As built (C1a, now shared), it is a digest of
   path, size and mtime: it contains the spec's form and is strictly more sensitive. No conflict.
5. **"Reload" and "vault switch" stay secondary.** Storage §6.2 requires the desktop-as-secondary behaviour to hold
   "on first attach, on every `reload()`, and on a vault switch". The reload routing and the switch path above
   implement that for `load_secondary`. PR-8's primary-lock retry and promotion are not built.
6. **One code version per vault.** A secondary refuses any schema other than its code's (`schema_mismatch`),
   which is the attach half of storage §6.2's rule. The `attach.lock`, the update marks, `deploy.lock` and the
   `flock` launcher are PR-8.
7. **T7 wording** ("the desktop app and the `learnloop` CLI remain the primary hosts" becomes "whichever process
   holds the primary role"). `load_secondary` does not depend on which process is primary. No conflict for PR-1.
   The spec text is to be updated when S5 starts (storage §7.5).

## 4. Gate (this step; the full suite runs once, in the landing gate)

All pytest runs used `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest
-n 6 …`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| pytest: `test_secondary_attach`, `test_architecture`, `test_public_tip_guards`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_table_roles`, `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_coordinated_migrations`, `test_migration_coordinator`, `test_migrate_fresh` | 172 passed, 6 skipped |
| pytest: `test_mcp_c1a_landing`, `test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_cli`, `test_mcp_http`, `test_mcp_runtime`, `test_mcp_tools`, `test_mobile_allowlist`, `test_mobile_capture`, `test_mobile_doctor`, `test_mobile_host_auth`, `test_mobile_host_coexistence`, `test_mobile_pairing`, `test_mobile_shortcuts`, `test_diagnosis_input_provenance_landing` | 486 passed, 2 xfailed |
| pytest: `test_vault_watcher_refresh`, `test_ad1_fix_round5`, `test_ad1_fix_round6`, `test_canonical_projection_rollout`, `test_daily_loop_reference_adoption`, `test_capture_route_recovery`, `test_sidecar_golden_path`, `test_ingest_jobs`, `test_placement_sidecar`, `test_migrations` | 151 passed |
| pytest `-m durability`: `test_secondary_attach`, `test_mobile_host_coexistence`, `test_migrations`, `test_migration_coordinator`, `test_migrate_fresh`, `test_mcp_runtime`, `test_mcp_c1a_review`, `test_coordinated_migrations` | 5 passed |
| pytest `--durable-sqlite tests/test_secondary_attach.py` (every test on production pragmas, WAL and fresh vaults) | 11 passed |

| `db_validate_reference.py` (under `env -i`, empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`) | First run: 10 errors, all stale `src/learnloop_sidecar/context.py:<line>` citations moved by this change. After `db_generate_reference.py` (keeping only the notes whose content changed: 5 config field notes for the citations, and 4 table notes that now list `tests/test_secondary_attach.py`; the commit-hash-only churn in about 415 other notes was reverted), 0 errors |
| `validate_vault.py` | passed (1155 notes) |
| `module_validate.py`, `desktop_validate.py` | fail, but not because of this change. The module catalog is missing about 1193 notes for modules added since it was generated (architecture docs come last in the queue). The desktop validator fails on an unclassified frontend file, `pdfSelection/testing/syntheticBook.ts`. This stage touches neither |

No frontend, `src-tauri` or schema change, so there was no npm, vitest or cargo run.

## 5. Open questions

1. **M2: a secondary's `notify()` and `wait_for`.** On a secondary, a handler's `post_attempt_worker.notify()`
   starts the worker's threads, which find no supplier and idle. A next-item `wait_for` then sees the worker as
   `running` and can wait out its whole timeout for a diagnosis only the primary will run. This does not matter
   for PR-1, since no handler runs on a secondary yet. M2 (or PR-8's queue discovery) should decide one of:
   - make `notify` a no-op when nothing is bound, and have the host skip the wait;
   - let the host wait for the primary's drain, bounded by PR-8's dispatch bound.
2. **`bind_ingest` modes** (§3 item 3): PR-8 should turn the flag into a mode (none / submit-only /
   promotions-only).
3. **The mobile host's M1 schema check** (`learnloop_mobile/host.attach`) duplicates `schema_is_current`. It was
   left as built to keep PR-1 off M1's code, and can switch to the helper whenever that code is next touched.

## Landing onto main

Landed in `learnanything-merge2` on `merge/pr1-onto-main`, cut from main `fa2eb72f8` (the stage's own base, so the
merge brings in nothing else). The stage tip is `d95d5dfd8`. Orchestrator rulings: Codex confirmed F1, F2, F4 and F5
fixed; F3 was reopened by the re-review for one layout (below) and **ruled non-blocking (Low)**; ready to land. **No
algorithm successor, no migration, no config key, no frontend change.** Main was neither fast-forwarded nor pushed.

### Commits and conflicts

- `4b68f0fa3`: the `--no-ff` merge of `mobile/pr1-secondary-attach`. **No conflicts.**
- `03b25498d`: this record (docs only).
- `d88187d66`: **main moved during the gate** to `1669817d1`, which adds two docs-only specs
  (`spec_deliverable_curriculum_v1.md`, `ux_reader_compare_ask_v1.md`). Main was merged in, with no conflict, so
  the tip descends from current main. Re-checked after it: `test_public_tip_guards`, `test_architecture`,
  `test_secondary_attach` and `test_cli_help_snapshot` gave 59 passed, `validate_vault.py` passes, and
  `db_validate_reference.py` gives 0 errors. The full gate below ran at `4b68f0fa3`; the two specs touch no code.
- The note above about main's move (docs only).

The diff against main adds three files (this record, the Codex review record and `tests/test_secondary_attach.py`):
no database or binary (G8), and the root `.gitignore` is unchanged. No test in the stage reads an owner vault.

### Regeneration

Nothing needed regenerating:
- **References.** `db_validate_reference.py`: **0 errors**. `db_generate_reference.py` rewrote 423 notes, all of
  them `source_commit` provenance only, so all were discarded. The stage's regenerated `context.py` citations hold on
  the merged tree.
- **CLI help snapshot, RPC pins, defaults snapshots:** their tests pass in the full suite with no file changed. No
  config key changed, so the defaults fingerprints do not move.
- **`validate_vault.py`**: passes (1,155 notes, 1,153/1,153 reachable).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0) in 5G scopes. The pytest lanes
ran in 10G / 2G swap scopes under `flock /tmp/learnloop-fullsuite.lock`, and everything else ran in 5G / 1G scopes.
Every Python run used `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. Logs are in
`fixtures-local/pr1-landing/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`pytest -n 8`, at `4b68f0fa3`, 2 h 57 min while the parity runs and two other worktrees' suites shared the machine) | 21,287 passed, **101 failed**, 74 skipped (the owner lane), 38 xfailed |
| 100 of the failures: `test_codex_tool_lockdown` (64), `test_codex_isolation_mcp_check` (25), `test_codex_lockdown_round2` (6), `test_codex_lockdown_round3` (5) | **The landing's environment, not the code.** The run's empty `CODEX_HOME` named a directory that did not exist, so the lockdown refused (`CodexLockdownUnavailable: CODEX_HOME … is not a directory`). With the empty directory in place, the four files give **221 passed, 1 skipped** |
| failure 101, alone, 3 times | `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`: **3/3 passed** (42 s each). It is a known load flake, and PR-1 does not touch the transport |
| durability (`-m durability`) | **124 passed**, 1 skipped. The one more than TE0's 123 is PR-1's two-process WAL test |
| `--durable-sqlite tests/test_secondary_attach.py` | **27 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **210 files, 1,822 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean apart from `fixtures-local/`; no non-empty `-wal` beside a tracked fixture |

### Parity (backup-API copies; no model call)

**Setup.** Scripts are in `fixtures-local/landing-pr1/scripts/` (TE0's, re-pathed). The new ones are:
- `setup_pr1.sh`, `a_pr1.sh`, `b_pr1.sh`, `b2_pr1.sh` and `c_pr1.sh`, which drive the runs;
- `primary_load.py`, the normal primary load;
- `scripts_b/` (`b_parent.py`, `b_child.py` and `b_common.py`), the two-process check;
- `scripts_c/c_mcp.py`, the chat runtime.

The details:
- **Copies.** The owner's backups `fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}` (in the
  main checkout; `mvp-0.30`, schema 218) were each copied once with `copy_tree_with_databases` into
  `landing-pr1/orig/`, and every other copy came from those. `u31` is `orig` brought to `mvp-0.31` **with main's
  code**: `upgrade --to mvp-0.31`, then `rebuild-derived-state` twice, rc 0 each. **Not opened:** anything in
  `~/learnloop-vaults`.
- **Code.** Main's is `git archive fa2eb72f8` and the merge's is `git archive 4b68f0fa3`, each first on `sys.path`.
  The audit hook logs every process start and socket connection, and refuses Codex processes and non-loopback
  connections. It logged **8 process starts**, all of them (b)'s own `b_child.py` second processes, and **no socket
  connection**.
- **Environment and routes.** `env -i` with empty `HOME` / `CODEX_HOME` / `LEARNLOOP_CONFIG_DIR`, which were still
  empty afterwards. `neutralize3.py` set 60 route fields to `127.0.0.1:9` loopback profiles with unset keys. 63 tasks
  resolved the same way on both codes, and the only one not on a loopback is the disabled, keyless `embedding`
  profile. Rewrite, rerank, dense and embeddings are off, and so are `build_on_serve` and outcome placement.
- **Clock and ids.** The clock is frozen at 2026-10-19 09:00 UTC, with TE0's deterministic ids.

**(a) Main vs the merge, normal (primary) sidecar load** (copies of `u31`; each code ran `SidecarContext.load` on its
own copy, with startup maintenance, and then drained).
- **Schema and rows:** identical, raw, row for row, after the load. LA has 1,503 objects, 356 tables and 18,301 rows;
  probability has 1,502 objects and 8,208 rows. FK 0, integrity ok, journal WAL, 0 `model_call_receipts`. A second
  main run is identical too. The merge's context reports `secondary = False` after `load()`.
- **`rebuild --shadow`:** 0 differences between the codes, and the live database is unchanged on both. **`doctor`:**
  0 differences (LA 57 issues / 1 error, probability 101 / 48).
- **Certification and curves** (LA 129,651 bytes, probability 17,495), **Today** (LA 43 items, 528,665 bytes;
  probability 67, 741,269 bytes) and **the daily plan** (read, serve, serve again, read; LA 84,714 bytes, probability
  40,799): **byte-identical** main vs merge, and main vs main.

**(b) `load_secondary` beside a primary: two processes** (the merge's code, a copy of `u31` per vault, WAL). The
parent holds the vault as primary (`SidecarContext.load`, drained). A spawned second process attaches with
`load_secondary`.
- **The attach writes nothing.** The whole-database digest (schema, plus every row of every table, per table) and
  every vault file's bytes are **unchanged by the attach** on both vaults. The attach took 0.09 s (LA) and 0.10 s
  (probability), and the context is `secondary`.
- **Handler reads match the primary's.** The reads were `get_practice_item` for 5 items, `list_source_sets`,
  `get_vault_tree` and the repository's `queue_revision()`. All are **equal** on both vaults, with one exception,
  `get_queue_revision` (finding 1).
  - The first `get_practice_item` read writes rows in `assessment_contract_versions` (and on LA `followup_tasks`).
  - These are the handler's own first-read writes. **Either process writes them**: rerun with the primary reading
    first (`b2_pr1.sh`), the primary's read writes the same tables and the secondary's then writes nothing. This is
    not a secondary effect.
- **A primary database write is seen without a reload.** After a queue-revision bump on the primary (LA 37 to 38,
  probability 49 to 50), the secondary's `repository.queue_revision()` returns the new value at once.
- **A primary content write is reloaded within the bound.**
  - The test: the secondary polls `refresh_if_content_changed()` every 50 ms, and the primary runs
    `edit_practice_item`, which writes the YAML and reloads, taking 1.11 s (LA) and 0.96 s (probability).
  - The reloading request started **1.80 s** (LA) and **0.20 s** (probability) after the edit began. Both are within
    `CONTENT_FINGERPRINT_TTL_SECONDS` (2.0 s) plus the 50 ms poll.
  - After the reload, the secondary serves the edited prompt, equal to the primary's.
- **The secondary's reload writes nothing.** A second edit was made, the database settled, and the secondary then
  refreshed (`reloaded = True`). The database digest and the files are **unchanged by that reload**, and the reads
  again equal the primary's, `get_queue_revision` aside.

**(c) The chat runtime** (`learnloop mcp`; the runtime now imports the moved fingerprint code). Each code ran on its
own copy of `u31`: `RemoteRuntime.attach`, then all six tools through the SDK client (`status`, `today`, `progress`,
`library`, `learning_context` with and without a topic, and `find_sources`), with every model client refused.
- **It settles on both codes:** the snapshot is settled and not marked `SNAPSHOT_UNSETTLED`.
- **The content fingerprint and the `content_files` list** of the same `u31` vault are **identical** under both codes
  (LA 137 files, probability 109).
- **Every tool's answer is byte-identical** main vs merge; the only difference in the dump is the code path.
- **The rows the tools write are the same:** LA 4 `source_exposure_events` and 7 `interaction_events`, probability 6
  and 7. They differ only in each telemetry event's `duration_ms` (and so its `payload_hash`), which also differs
  between two runs of main.
- **No paid route was asked for.**

**Calls.** All 21 learner databases under `landing-pr1/` have **0 `model_call_receipts` rows** of any status. **No
model was called. Spend: $0.**

### Findings

1. **`get_queue_revision` fails on a secondary** with `RuntimeError: Ingest jobs are not bound to a vault yet.` The
   handler lists the ingest batches (to reload once after an applying job) before it reads the revision, and a
   secondary leaves ingest unbound by design. About 15 handler modules use `ctx.ingest_jobs`.
   - This does not matter for PR-1, since no handler is served from a secondary yet.
   - **For M2 / PR-8:** the mobile host's handler set must avoid these handlers, or PR-8's `bind_ingest` modes must
     give a secondary a binding that answers reads (open item 2).
2. **Pre-existing, main's code: after a primary load, `rebuild --shadow` on LA reports 30 schedule differences.**
   They are `practice_item_state.active`: 0 live, 1 in the replay. They are identical on main and the merge, so they
   do not come from PR-1. On a copy of `u31` that no primary had loaded, the shadow is 0 / 0 / 0. TE0's parity did
   not load before its shadow, which is why it saw none. This is for the projection track.
3. **Landing environment:** a gate's empty `CODEX_HOME` must be an existing directory, or the Codex lockdown tests
   refuse. It was missing in this landing's first run.

### For the owner

- **No migration, no successor.** Your vaults stay at `mvp-0.31`. There is nothing to run.
- **Nothing changes on screen or in what is served:** parity (a) and (c) are byte-identical. PR-1 is groundwork for
  the phone host. A second process (the mobile host's workers, and later the desktop when the hub runs) can attach to
  a vault the desktop holds without writing anything, and it picks up content edits within about 2 seconds.

### Open items

1. **F3 (re-review), ruled non-blocking Low, open.**
   - The gap: when an ancestor link (for example `subjects -> .`) is combined with a nested link that is then
     retargeted, the retarget is not fingerprinted, so a secondary can keep stale content after it.
   - Why it is Low: the layout is contrived; the refresh is a staleness bound, not a protection boundary; and the
     primary's own load is unaffected.
2. **Recorded at their defaults** (§5):
   - **`post_attempt_worker.notify` on a secondary** is resolved in M2 / PR-8: `notify` becomes a no-op when no vault
     is bound, and the host skips the wait.
   - **`bind_ingest` becomes a mode** (none / submit-only / promotions-only) in PR-8. That mode should also settle
     finding 1.
   - **The mobile host's duplicate schema check** switches to `schema_is_current` when that code is next touched.
3. `desktop_validate.py` and `module_validate.py` fail as before; this stage touches neither.
4. The parity copies' backup-API reads left an empty `state.sqlite-wal` and a refreshed `-shm` beside the backup
   databases in the main checkout's `fixtures-local/vault-backups-20261025-mvp030/`, as at earlier landings. The
   databases are unchanged.

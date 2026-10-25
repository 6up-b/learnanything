# Mobile PR-1: secondary attach

Stage `mobile-pr1-secondary-attach`, branch `mobile/pr1-secondary-attach` in `learnanything-ad1`, base `fa2eb72f8`
(migration head 220, latest algorithm `mvp-0.31`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §3.1 (M2: secondary
attach mode, content freshness), §3.3 PR-1, §10 G12, §11 (`test_secondary_attach.py`); reconciled with
`docs/specs/spec_storage_sync_v1.md` §6.2 and §6.9. Only PR-1: PR-2..PR-8, the workers and the adapter are not
started. No migration, no successor, no new config key, no model call (no paid calls were made).

## 1. What changed

> The Codex review's fixes (`docs/reviews/mobile-pr1-secondary-attach-codex-review.md`) change three points below: `load_secondary` publishes only a settled load (`settled_load_vault`) and refuses an unsettled one (`vault_unsettled`); the freshness window starts at the after-load check and does not advance on a failed refresh; and `content_files` prunes by name at the root only and follows directory links.

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

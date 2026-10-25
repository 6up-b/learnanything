# Mobile PR-1 (secondary attach): Codex review and fixes

Stage `mobile-pr1-secondary-attach`, branch `mobile/pr1-secondary-attach` in `learnanything-ad1`. The review was
Codex job `20261025-115714-awcg6X`, run on `da24c9834`; it read `docs/reviews/mobile-pr1-secondary-attach.md`. The stage
record is that file. This file covers the review and the fix round.

No migration, successor, config key, model call or paid call. The settle constants (`SETTLE_ATTEMPTS = 3`,
`SETTLE_PAUSE_SECONDS = 0.05`) are not new. They moved from `learnloop.remote.runtime` into `learnloop.vault.loader`,
where both secondaries share them. They are guardrails on a reader's retry cost, not model parameters, and they are
module constants rather than config keys.

## Findings

Each finding was reproduced first. The new tests were run against the pre-fix sources (`da24c9834`'s
`loader.py`, `runtime.py` and `context.py`, with the new test file): 9 failed and 12 passed. With the fixes, all 21 pass.

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | High | Secondary attach publishes partially rewritten protection metadata | fixed | `aed32b727` | `test_a_source_sets_rewrite_during_the_load_never_publishes_empty_protection[attach,refresh]`, `test_a_source_sets_file_that_stays_truncated_is_refused_not_published` (before the fix: the exam member was missing from the published vault, and the attach that stayed truncated was not refused) |
| F2 | Medium | A failed refresh permits subsequent requests to use stale state | fixed | `aed32b727` | `test_a_failed_refresh_is_retried_by_every_later_request[config_parse,schema_mismatch]` (before the fix: the requests inside the next 2 s returned `False` and were served from the old vault) |
| F3 | Medium | Fingerprint coverage differs from the loader's accepted paths | fixed | `aed32b727` | `test_fingerprint_covers_every_file_the_loader_reads[ordinary, subject_named_canonical_sources, linked_subject_dir, linked_items_dir, linked_item_file]`, `test_fingerprint_walks_a_link_cycle_once` (before the fix: `subject_named_canonical_sources`, `linked_subject_dir` and `linked_items_dir` failed; `linked_item_file` already passed, because `os.stat` follows file links) |
| F4 | Medium | Initial attach starts the freshness window after loading finishes | fixed | `aed32b727` | `test_a_change_during_a_slow_load_is_in_the_snapshot_and_the_window_starts_after_it`, which replaces `test_a_change_during_the_load_is_loaded_at_the_next_comparison` (before the fix: the old prompt was published) |

### F1: settled snapshots only

- **New helper.** `learnloop.vault.loader.settled_load_vault(root, *, load, fingerprint, attempts, pause_seconds)`
  returns a `SettledLoad(vault, fingerprint, verified_at)`. A load is kept only when two conditions hold:
  1. the content fingerprint is the same before and after it;
  2. `sources/source_sets.yaml` is not empty.

  Otherwise the load is tried again, up to `SETTLE_ATTEMPTS` times. A file that stays empty across all attempts is
  therefore covered too, and so is the empty-source-sets case.
- **One rule for both secondaries.** This is C1a's `RemoteRuntime._settled_load` rule. The runtime now delegates to
  the helper. It keeps its own behaviour on an unsettled load: it publishes the load marked `SNAPSHOT_UNSETTLED`, and
  protection fails closed. `test_mcp_c1a_review`'s settle tests pass unchanged.
- **The sidecar refuses instead.** `SidecarContext.load_secondary` refuses an unsettled load with
  `SidecarError("vault_unsettled")` and publishes nothing. Its handlers do not consult `protection_issues`, so a
  snapshot that is published but marked would not fail closed there.
- **Tests.** One test truncates `source_sets.yaml` during the load and rewrites it afterwards, on the attach and on a
  refresh. It asserts that the exam-role member is in the published vault. A second test leaves the file truncated.
  It asserts that the attach is refused with nothing published, and that a refresh is refused on two consecutive
  requests while the attached vault is kept.

### F2: the window advances only on success

`refresh_if_content_changed` now advances `_fingerprint_checked_at` in two cases only:
- the fingerprint matched;
- `load_secondary` succeeded (it sets the window from its own verification).

A reload that raises leaves the window expired, so every later request compares again and fails again until the vault
loads. Both of the review's cases are tested at 0, 0.1, 0.5 and 1.9 s after the first failure:
- an unparseable `learnloop.toml`;
- a schema one migration behind, plus a content edit that triggers the reload.

After the cause is restored, the next request reloads.

### F3: the walk matches the loader's paths

`content_files` now prunes by name only at the vault root: dot-directories, `canonical-sources`, `node_modules` and
`__pycache__`. Below the root nothing is skipped by name, because the loader reads every directory under `subjects/`.

The walk also follows directory symlinks (`os.walk(followlinks=True)`), as the loader's `Path` operations do. A cycle
guard by `(st_dev, st_ino)` walks each directory once, and subdirectories are walked in sorted order, so repeated walks
produce the same names.

The drift guard (the audit hook on `open`) now records paths as the loader names them (`abspath`, not `realpath`), so
linked content counts as under the vault. It runs over five layouts:
- an ordinary subject;
- a subject folder named `canonical-sources`;
- a symlinked subject directory outside the vault;
- a symlinked `practice-items` directory;
- a symlinked item file.

For each layout it also asserts that an edit to the item changes the fingerprint.

### F4: the window starts at the after-load check

`SettledLoad.verified_at` is the `time.monotonic()` reading taken just before the after-load fingerprint is collected.
`load_secondary`, including every secondary `reload()`, sets the window from it.

A write that lands during the load makes the before and after fingerprints differ, so the load is retried, and the
published snapshot contains the write. A write after `verified_at` is seen by the first request at most
`CONTENT_FINGERPRINT_TTL_SECONDS` after it.

The test edits the item inside a slow load (0.2 s after the edit) and then makes three checks:
- the published prompt is the edit;
- the window starts after the edit;
- an immediate request is current.

The same holds for an explicit `reload()`.

### The review's "claims that don't hold"

The three claims in the stage record are corrected by F1 to F4 above. The stage record's §1 now points here. The
mobile spec's §3.1 note and §9.2 describe the settled load, the refusal, the window and the walk as built.

## Gate (this step; the full suite runs once, in the landing gate)

Every pytest run used `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 …`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| pytest `test_secondary_attach` (pre-fix sources, reproduction) | 9 failed, 12 passed (as expected) |
| pytest `test_secondary_attach`, `test_diagnosis_input_provenance_landing`, `test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_c1a_landing`, `test_mcp_cli`, `test_mcp_http`, `test_mcp_runtime`, `test_mcp_tools`, `test_reread_safety_landing`, `test_mobile_allowlist`, `test_mobile_host_coexistence`, `test_mobile_doctor`, `test_mobile_capture` | 466 passed, 2 xfailed |
| pytest `test_architecture`, `test_public_tip_guards`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_table_roles`, `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_vault_watcher_refresh`, `test_sidecar_golden_path`, `test_mobile_host_auth`, `test_mobile_pairing`, `test_mobile_shortcuts` | 183 passed, 5 skipped |
| pytest `test_doctor`, `test_vault_writer`, `test_vault_template`, `test_cli_help_snapshot`, `test_exam_protection_identity`, `test_ad1_fix_round5`, `test_ad1_fix_round6`, `test_ingest_jobs`, `test_placement_sidecar` (`load_vault` consumers) | 140 passed, 1 skipped |
| pytest `-m durability`: `test_secondary_attach`, `test_mcp_runtime`, `test_mcp_c1a_review`, `test_mobile_host_coexistence` | 3 passed |
| pytest `--durable-sqlite tests/test_secondary_attach.py` (every test on production pragmas, WAL and fresh vaults) | 21 passed |

**Reference docs.** `db_validate_reference.py` was run under `env -i`, with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`:
1. First run: 10 errors, all stale `src/learnloop_sidecar/context.py:<line>` citations that the fix moved.
2. `db_generate_reference.py` was then run. Of its output, only the notes whose content changed were kept: 5 config
   field notes (hints, ingest, scheduler, ui, workbench). The commit-hash-only churn in 418 other notes was reverted.
3. Second validate run: 0 errors.

There was no frontend, `src-tauri`, schema or migration change, so no npm, vitest or cargo run was needed.

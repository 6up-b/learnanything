# Phase 1 fix round, group FR-A: upgrades and the version floor

Rows U1-U8, T1 and T5 of `docs/reviews/refactor-phase-1-review.md`, on branch `refactor/p1-fixes-upgrades` from main
`e231d7fb59`. One commit per row, test and fix together; every fix starts from a test that fails at the base.

## U1: the publication sets the setting and reads it back

**Reproduced.** `tests/test_upgrades.py::test_the_publication_changes_the_setting_not_the_same_text_elsewhere`
(both decoys: a comment `# algorithm_version = "mvp-0.58"`, and a `[notes]` table holding the same line, each placed
before `[algorithms]`). At the base both fail the same way: `upgrade()` reports `upgraded=True`, commits the mvp-0.59
rebuild and removes its journal, and the parsed config still names `mvp-0.58` (`assert 'mvp-0.58' == 'mvp-0.59'`).
The new stage `renamed without the tag` of `test_a_failure_before_the_commit_leaves_the_predecessor_readable_and_no_journal`
(a publication whose rename lands a file still naming the predecessor) showed `DID NOT RAISE` at the base: nothing read
the tag back.

**Fix.** `ops/upgrades.rewrite_algorithm_version` sets `[algorithms] algorithm_version` through tomlkit (the writer the
Settings tab already uses; `settings_store.updated_config_text` is `apply_config_updates`'s parse-and-set step, split
out so the upgrade keeps its own durable write), so comments and layout stay and a comment or another table is never
the one changed. Its `from_version` check parses the config (`published_algorithm_version`, the same `load_config`
openers use) instead of matching text. After the publication, inside the transaction, the activation reads the tag
back from the renamed file; anything but the target raises `UnpublishedTag`, which takes the existing failure path:
the predecessor's label is restored (now written whatever the file names, since the read-back can be what failed), the
journal removed, the transaction rolled back.

**Callers and siblings checked.**
- `publish_algorithm_version` / `rewrite_algorithm_version` callers: `_activate_as_writer` (publication and the
  restore), and tests (`tests/test_upgrades.py`, `tests/test_batch3_landing.py`, `tests/followups_nov2_help_fold_helpers.py`,
  `tests/test_route_rules_in_grader.py`): all pass a `from_version` the config names under `[algorithms]`; unchanged.
- Init: `config/template.default_config_text` substitutes the placeholder `@ALGORITHM_VERSION@`, which occurs once in
  a template the code owns; sound.
- Settings saves (`settings_store.apply_config_updates`, sidecar settings/hints/first-run handlers): tomlkit, keyed
  by path; none sets `algorithm_version`; sound.
- Other text writers of the line: `learner/recall_calibration._fresh_calibration_vault`,
  `curriculum/golden_path_fixture._pin_algorithm_version` and `tests/helpers._set_algorithm_version_at` rewrite by
  regex, but only a config just written from the template (one occurrence, no comment naming the key); left as they
  are.

**Not verified.** A real power loss between the rename and the read-back (the read-back is inside the transaction, so a
death there is the existing "death after the publication" case the journal covers).

## U3: a journal that cannot be read is not torn

**Reproduced.** `tests/test_upgrades.py::test_a_journal_that_cannot_be_read_is_kept_and_the_vault_is_not_opened`: the
interrupted state (journal written, config naming the successor, predecessor's database), then the journal's mode set
to 0 (a real permission error; the directory still allows unlinking). At the base `open_vault_repository` did not
raise: `_read_journal` took the `PermissionError` for a torn journal, deleted it, and the vault opened under the
successor's label over the predecessor's database (the test's later `chmod` hit `FileNotFoundError`).

**Fix.** One reader, `activation_journal.read`: `None` when the file is gone, `"torn"` only when its bytes were read
and are not a whole record (malformed JSON, undecodable bytes, missing keys), and any other `OSError` raises
`InterruptedActivation` naming the file and keeps it. The opener's floor pre-check (`activation_journal.complete`) and
the completion (`upgrades.complete_interrupted_activation`) both read through it, so neither treats a read error as
torn. `upgrade()` returns the refusal as a problem (`learnloop upgrade` exits 1 naming the journal) instead of a
traceback. Once the file is readable again the next opener completes the activation (asserted).

**Callers and siblings checked.**
- `upgrades._read_journal` (removed; its one caller now uses `activation_journal.read`) and `activation_journal._link`
  (removed, same) were the two readers that decided; both had the defect (`_link` sent the read error on to the
  completer, which then deleted the file).
- `activation_journal.message` swallows `OSError` only to choose the message's wording; it decides nothing. Sound.
- `pending`, `refuse_if_interrupted`, `remote/runtime.py`, `learnloop_mobile/host.py`, `vault/repository.py` and
  `upgrades._upgrade` test existence only and refuse; sound.
- Other "torn" readers (`adaptive_difficulty/denial_log.py`, the contextual-embeddings adapters) are append logs
  whose torn tail is a line, not a recovery record; not this question.

**Not verified.** An I/O error other than a permission error (the test uses `chmod 0`; the code treats every
`OSError` but `FileNotFoundError` the same). Running as root skips the test.

## U2: a bound sidecar stops serving an unservable vault

**Reproduced.** `tests/test_sidecar_stops_serving.py`, on a context loaded at the head:
- `test_a_reload_refused_below_the_floor_stops_serving_until_a_load_succeeds`: the file retagged below the floor,
  then `reload_vault`. At the base the RPC failed as `internal` (no message: `BelowOldestSupported` was mapped only by
  `initialize`), and a variant asserting on the next call showed `app_snapshot()` still serving the cached vault.
- `test_a_journal_that_appears_while_bound_stops_serving_until_a_load_succeeds`: another process's journal written
  beside the bound database; at the base `app_snapshot()` did not raise.

**Fix.** The one place handlers get the vault is `SidecarContext.require_vault`; the post-attempt worker gets it from
`_worker_target` (its supplier, called per iteration); background AD jobs admit their snapshot through
`LoadedVaultProvider.admit`. All three now ask `SidecarContext.serving()`: false while `refusal` holds, and a journal
seen beside the bound database (one `stat`, skipped inside the activation's own completion) sets the refusal. The
refusal is also set when a load of the bound vault is refused (`load`, `load_secondary`: `BelowOldestSupported` or
`InterruptedActivation`), and setting it moves the vault generation, so a job holding an older snapshot fails its next
admission. It holds until a load of a vault succeeds (`refusal = None` beside the publication of the new vault): a
journal that goes away has changed the database under the cached vault, so its disappearance alone does not serve
again. `refresh_vault_files` (the watcher's handoff), while refused, tries a full reload first instead of refusing,
so the upgrade's own publication of `learnloop.toml` (or an owner's fix of it) brings the vault back without a
restart; the full-reload block it repeated twice is now `_full_refresh`. The server maps both refusals for every
method (`unservable_error`: `vault_below_oldest_supported` with the floor's details, as `initialize` had, and
`vault_upgrade_unfinished`); `initialize` drops its own copy of the mapping.

**What the desktop then shows.** Every action reaches `require_vault` and fails with the refusal's own message, which
`errorMessage` shows as the toast (classic) or error notice (simple shell): below the floor, the message naming the
`pre-floor` route; with a journal, "The upgrade to … did not finish … open the desktop app or run
`learnloop upgrade --to …`". No new frontend copy; the frontend was not run.

**Callers and siblings checked.**
- `require_vault` callers: the handlers (326 calls) and `app_snapshot`; all refused through the one check.
- Direct `ctx.vault` / `ctx.repository` reads outside it: `handlers/chatgpt_plan.py` and `handlers/vault.py` read the
  AI config only (plan profiles; the AI settings a new vault inherits); `server._observed_model_calls` wraps a handler
  that is itself refused before any model call; `learnloop_mobile/runtime.py` reads the config for readiness. None
  reads learner state; left as they are.
- `LoadedVaultProvider.snapshot()` / `__call__` still return the cached vault: a job that falls back to it is stopped
  at its admission (`SendGuard` refuses on a failed admission), which is where a model request or record is admitted.
- The MCP runtime (U4) and the phone host's per-request reload (`refresh_if_content_changed`, whose window does not
  advance on a failed reload) are the other attach paths; the phone host's handlers run on a `load_secondary` context
  and get the same refusal.

**Not verified / open.** The bound background runners (`ingest_jobs`, `exam_grading`, `map_builds`,
`background_jobs`) keep running while refused: they were bound with the repository at load and do not ask the context
again. Stopping them is `close()`, which joins threads and would be called from a request thread; whether a refusal
should do that is a design question (below). Whether the Rust watcher reports a change to `learnloop.toml` itself
was not checked; `reload_vault` works either way.

## U4: the MCP runtime serves nothing after a failed load

**Reproduced.** `tests/test_mcp_runtime.py::test_a_reload_refused_below_the_floor_serves_nothing_until_a_load_succeeds`,
with the runtime module's monotonic clock pinned: attach at the head, retag the config below the floor, move past the
fingerprint window, then call `runtime.vault()` twice at the same moment. At the base the first call raised
`SchemaMismatch` and the second returned the cached head vault (`DID NOT RAISE`): `_checked_at` had advanced before the
load.

**Fix.** `RemoteRuntime.vault` advances the window only after a load that settled or a fingerprint that matched. Any
failed load (not only a floor refusal) drops the cached vault and its fingerprint and resets the window, so the next
request loads again and nothing older is served meanwhile; a floor refusal is still reported as `SchemaMismatch`.

**Callers and siblings checked.**
- `RemoteRuntime.vault` callers: `attach` and the four views in `remote/views.py`; each gets either a load that
  succeeded or the raise.
- `SidecarContext.refresh_if_content_changed` (the phone host's per-request check) already advances its window only on
  a match or a successful `load_secondary`; with U2 a floor or journal refusal of the bound vault also stops its
  handlers. Sound.
- The journal check (`refuse_interrupted_activation`) runs before the cache on every request; sound.

**Not verified.** The MCP server end to end over stdio after such a refusal (the runtime is what every tool asks).

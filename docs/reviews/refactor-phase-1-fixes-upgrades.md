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

## U5 and U6: every CLI door meets the floor before it reads or writes the vault

One commit for both rows: the fix is one check at the CLI's vault-root resolvers.

**Reproduced.** Five new doors in `tests/test_version_floor.py::test_a_vault_below_the_floor_is_refused_at_each_door`,
each through `_cli_refused_unchanged` (every file under the vault byte-identical, none added, and the refusal naming the
floor and the `pre-floor` route). At the base all five failed:
- `doctor_fix` (U5; the config's `active_provider` pinned to Codex): `learnloop.toml` was rewritten before
  `run_doctor` refused.
- `mcp_activity` (U6): exit 0 with the stored activity report.
- `mcp_token` (`mcp token show`, found by the sweep): `.learnloop/mcp/endpoint-token` and its `.gitignore` written.
- `project_enroll` (U6): `projects/project_store.sqlite` created.
- `source_set_create` (`source-set create`, found by the sweep): `sources/source_sets.yaml` and the subject's
  `subject.md` written before the command's own `load_vault` refused.

**Fix.** `vault.loader.refuse_vault_below_floor(root)` reads only `learnloop.toml` (no environment) and refuses below
the floor; a missing or unreadable config is left to the command's own load (`doctor` reports it as
`config:invalid`). It runs in each resolver a command gets its vault root from: `cli/runtime._root` (about 200
commands, `doctor` among them), `cli/project._vault_root` (every `project` command), `cli/mcp._root` (`serve`,
`token show|rotate`, `activity`; refused there with exit 78, as `serve` already refused at attach, so a supervisor does
not loop) and `cli/facets._root`. `upgrade` alone passes `below_floor=True`: its table refuses with the route itself
and its result message is what the owner reads. `remote/runtime.refuse_below_floor_as_mismatch` now uses the same
helper instead of its own copy.

**The doors listed** (grep under `src/learnloop/cli` for `load_config`, `Repository.attach`, `vault_sqlite_path`,
`connect(`, `Repository(`; then the library functions they call with a bare root):
- Config or database opened without `load_vault`: `doctor --fix` (`app.py`, `fix_codex_pins`), `mcp activity`
  (`vault_sqlite_path` + `Repository.attach`), `project *` (`_config`, `ProjectStore`), `ai compare`
  (`_configured_database`, below). Fixed except `ai compare`.
- Writers reached with a bare root: `source-set create|update` (`vault/writer.upsert_source_set` loads the config
  itself), `mcp token show|rotate` (`endpoint_token`), `doctor --fix-content` (`fix_criterion_dependencies`), every
  `_root` caller that writes before its load. Fixed by the resolvers.
- Every other `Repository.attach` / `connect` in the CLI (`ad`, `placement`, `recurrence`, `embeddings`,
  `data_capture`, `diagnose`, `decider`, `field`, `field_classification`, `gaps`, `plan`, `reader`, `router`,
  `practice_index`, `success_head`, `probability_arms`, `receipts`, `app.py`'s three) takes its path from a
  `load_vault` result: already refused there.
- Outside the CLI: `vault/writer._vault_paths` (FR-C's file; reached from the CLI only through `source-set`, now
  refused first, and from the sidecar, whose bound vault passed the floor), `projects/capture.py` (through the
  `project` commands), the ingest pipeline's `load_config` calls (inside a sidecar or CLI runner bound to a vault that
  passed), `symbolic_view` (reads one switch), `bootstrap`/`init_vault` (create a vault at the head), `ops/doctor`
  (after `run_doctor`'s own refusal), `learnloop_mobile/cli.py` (the host's `attach`, already refused).
- Not changed: `ai compare --vault <copy>` reads a source vault's `storage.sqlite_path` to copy it; the copy is then
  loaded and refused. It writes nothing into the source. Left as a read for a copy; say if it should refuse first.

**Not verified.** The sidecar's handlers that take a vault path of their own (vault creation, a switch) go through
`SidecarContext.load`, refused there; the TUI opens through `load_vault`. The full CLI suite runs at landing.

## U7: what the `pre-floor` route can and cannot do

**What the tagged code does** (`git show pre-floor:<path>`, tag at `5231b1bf1b`):
- `version_floor.upgrading` is the only allowance below the floor, and only `cli/app.py`'s `upgrade` enters it; every
  other command (`recurrence guard` included: `cli/recurrence.py` loads through `load_vault`) refuses a vault below
  `mvp-0.58` there, as here.
- Of the 48 upgrade modules at the tag, one refuses and asks for another command: `diagnosis/recurrence/upgrade.py`
  (`mvp-0.12`). With `recurrence.require_guard = true` and the guard not passed for the configured judge, it refuses
  and asks for `learnloop recurrence guard` (or `--from-run <M1 run dir>`). That command cannot run on such a vault
  at the tag (nor here). The tag's documented switch is `recurrence.require_guard` (schema default `false` since
  2026-10-12; the upgrade then reports the guard's status in `notes` and proceeds). Its other refusal, "cannot tell
  which model the same-cause judge route resolves to", is a config setting and is reached only while the guard is
  required.
- No other link names a command: `mvp-0.7`'s readiness problems are vault files to edit (facet registry), and the
  rest are jumps or "already at" results. `regrade_contract_upgrade`'s "held for review until a regrade" is a note.

**The honest answer, for the orchestrator:** a vault below `mvp-0.12` whose config sets
`recurrence.require_guard = true` and whose guard has not passed cannot be upgraded through `pre-floor` without
editing its config (`recurrence.require_guard = false`). Keeping the guard required and upgrading is impossible on
either code. I made the route say so and stopped there; no command was invented.

**Reproduced** (the message's gap, not the tagged code's behaviour, which was read, not run):
`tests/test_version_floor.py::test_the_route_names_what_works_at_pre_floor_for_a_required_guard`: at the base the
refusal for a vault at `mvp-0.11` with `require_guard = true` did not name the switch (the `[mvp-0.11-True-True]` case
failed; the two cases that must not name it passed).

**Fix.** `BelowOldestSupported` takes `guard_required` (from the config `refuse_below_floor` already has) and, when the
route crosses `mvp-0.12` (the vault's tag, or a journal's predecessor, below it, or no tag), adds: the upgrade there
refuses until the guard passes, `learnloop recurrence guard` cannot run below the floor there or here, set
`recurrence.require_guard = false` under `[recurrence]` first. ADR-019's "Restoring a backup below the floor" gains
the paragraph "What `pre-floor` can and cannot do"; `version_floor`'s docstring says the same.

**Callers and siblings checked.** `BelowOldestSupported` is raised by `refuse_below_floor` (every load and the new CLI
resolvers; it has the config) and `refuse_journal_below_floor` (a journal's predecessor; no config at hand, so the
guard line is not added there: a journal from below the floor is at least `mvp-0.57`'s predecessor in practice, past
`mvp-0.12`).

**Not verified.** The route was not run end to end in a `pre-floor` worktree (no checkout of the tag was made; the
reading above is from `git show`).

## U8: the mvp-0.58 to mvp-0.59 activation derives the successor's state

**Reproduced, with one qualification.** A receipt-only mutant of the table's `whole_vault_rebuild` (its `run` writes
the scope-`all` receipt under the tag and replays nothing), applied to the tip and reverted: of `tests/test_upgrades.py`
(the table's 37 cases at the time) and `tests/test_facet_belief_successor.py`, every case passed but one,
`test_every_opener_that_may_write_completes_an_interrupted_activation_first[sidecar_start]`, which failed only because
the sidecar's startup projection then changed state the mutant's "clean" baseline lacked: incidental, not a check of
the activation. The tag, receipt and recovery tests compare against another run of the same upgrader, so they pass on
the mutant.

**Fix (test only).** `tests/test_facet_belief_successor.py::test_the_upgrade_derives_the_successors_state_from_the_history`
restores the deleted `test_the_upgrade_rebuilds_under_the_tag_and_completes_once` through `ops.upgrades.upgrade`: on a
vault at mvp-0.58 with history (two don't-knows, then a success) it first asserts the predecessor's state (no
`facet_uncertainty` row; the aggregate recall streak not ended by the success), then that the upgrade leaves the tag,
the whole-vault receipt, a successor-tagged uncertainty row for the LO and a streak of 0, and that a rerun is
"already". It fails on the receipt-only mutant and passes at the tip.

**Callers and siblings checked.** The other deleted tests of that file (the chain from mvp-0.47, mvp-0.8 refused, born
at the tag, the CLI by name and default) are covered per row by `tests/test_upgrades.py` over the table, or are below
the floor (refused by `test_version_floor.py`); not restored.

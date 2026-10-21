# Security stage: Codex tool lockdown, Codex review and fix round (2026-10-21)

Review: Codex job `20261021-111619-GGirNP` (gpt-6-astra, high effort, read-only) of
`c80c54cbb..security/codex-tool-lockdown` (stage head `f68295d05`). Fix commit: `6780e8d97`.
Stage record: `docs/reviews/security-codex-tool-lockdown.md`.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Workspace commands can read inherited credentials | fixed | `6780e8d97` | `test_a_workspace_command_cannot_see_inherited_credentials[default-policy, set-and-filters, include-all-and-profile]` (installed codex-cli 0.163.0, `codex sandbox -- /usr/bin/env`), `test_every_turn_pins_the_command_environment_and_turns_shell_snapshots_off[False, True]` |
| F2 | High | Cached checks miss workspace-local MCP configuration changes | fixed | `6780e8d97` | `test_editing_a_workspace_project_layer_runs_the_check_again`, `test_a_sibling_workspace_with_other_mcp_servers_gets_its_own_check`; guard `test_fresh_workspaces_without_a_project_layer_still_share_one_check` |
| F3 | Medium | Captured usage is discarded on ordinary SDK failures | fixed | `6780e8d97` | `test_tokens_reported_before_an_ordinary_failure_reach_the_receipt_and_the_settle[sdk_timeout, connection_closed, learner_interrupt, request_deadline]`; guard `test_a_failure_before_any_usage_reports_nothing_new` |

### F1: reproduced, then fixed

**Reproduction** (installed `/usr/bin/codex` 0.163.0, `env -i` with empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`,
synthetic variables only, no model call): `codex <the stage's isolated_turn_overrides(shell=True)> sandbox -- /usr/bin/env`
in a throwaway turn directory printed `LL_SYNTH_API_KEY=canary-1`, `PLAIN_VAR=canary-2` and a user-config
`set` entry `USER_SET_TOKEN=canary-3`. `codex sandbox` builds the command's environment with the same
`create_env(shell_environment_policy)` the shell tool uses (`cli/src/debug_sandbox.rs:258`), under the turn's
permission profile. Codex 0.163.0's default policy is `inherit = "all"` with `ignore_default_excludes = true`
(`config/src/shell_environment_policy.rs`), and the SDK starts the app server with `os.environ.copy()`
(`sdk/python/src/openai_codex/client.py`), which holds the keys LearnLoop loaded.

**Fix** (`codex_lockdown.shell_environment_overrides`, added to every turn's `isolated_turn_overrides`):

* `shell_environment_policy.inherit="core"`: nothing the app server inherited beyond Codex's Unix core set;
* `shell_environment_policy.ignore_default_excludes=false`: the `*KEY*`/`*SECRET*`/`*TOKEN*` excludes back on;
* `shell_environment_policy.include_only=[PATH, HOME, LANG, LC_ALL, LC_CTYPE, TMPDIR, TEMP, TMP, SHELL, USER, LOGNAME]`
  (`SHELL_ENVIRONMENT_ALLOWLIST`): `populate_env` applies it after `set`, so a user's `set` entry under any other
  name is dropped; a legacy `include_only` in the CLI layer displaces a lower layer's `filters` table
  (`config/src/merge.rs` `replace_shell_environment_policy_filter_representation`), so a config
  `"*KEY*" = "include"` filter cannot widen it, and arrays replace wholesale, so a user's `include_only = ["*"]`
  is gone too;
* `shell_environment_policy.experimental_use_profile=false`: commands never source the login profile;
* `features.shell_snapshot=false` in workspace turns too (moved from `SHELL_FEATURES` to
  `LOCKDOWN_DISABLED_FEATURES`; it was already off in text turns): a snapshot replays the login shell's
  environment into every command. `features list` must report it off, or the turn is refused.

After the fix the same probe prints only `CODEX_SANDBOX_NETWORK_DISABLED`, `HOME`, `PATH` (Codex keeps its own
helper directories in front) and `PWD`, for the default config, a config with `set` + `filters` including
`*KEY*`, and a config with `include_only = ["*"]` + `experimental_use_profile = true`. The test keeps a control:
the same probe with the policy overrides removed (the stage's shipped set) must show the canary, so the test
cannot pass by not running the shell.

Residual: a user who writes a secret into an allowlisted name in their own Codex `set` (for example `HOME`)
would still pass it on; that is not an inherited credential.

### F2: reproduced, then fixed

**Reproduction** (fake codex-cli whose `mcp list` now also reads `[mcp_servers.*]` from `.codex/config.toml` in
the directory it runs in, i.e. a trusted workspace's project layer): a workspace turn with server `docs` pins it
off; the layer is edited to add `shell_bridge`; the next turn reused the cached check (no new probe) and launched
the app server without `mcp_servers.shell_bridge.enabled=false`. Two sibling workspaces (`docs` / `fetcher`):
the second turn reused the first one's pinned list, so `fetcher` started enabled. The fingerprint held only
`(root / ".codex").exists()` for the turn directory itself.

**Fix** (`codex_lockdown.check_fingerprint`): a turn directory that has a `.codex/` adds its resolved path and the
stat identity of `.codex/` and `.codex/config.toml`; one without (every scratch turn and every diagnosis
export LearnLoop makes) adds only that it has none, so those turns still share one check. `_stat_signature`
now also records `st_dev` and `st_ctime_ns` (any write or rename moves the ctime, and unlike the mtime it
cannot be set back), for every layer the fingerprint covers. Content is still never read.

### F3: reproduced, then fixed

**Reproduction** (fake SDK): a workspace turn reports two cumulative usage updates (1,050 then 2,420 tokens,
a `commandExecution` between them) and then fails with a `TimeoutError`, a `BrokenPipeError`, a learner
interrupt or the request deadline, with no lockdown violation. The receipt's finish had no `input_tokens`
(`KeyError: 'input_tokens'`), the admission settle got none and the client's accounting stayed at zero.

**Fix** (`SdkCodexClient._run_sdk_turn`): every exception path (interrupt, timeout, lockdown refusal, sandbox
failure, any other SDK exception) calls one `settle_failed_turn`, which meters the notification usage through
`_report_turn_usage(None, lockdown)` exactly once (receipt fields, admission settle, `record_token_usage`). A
turn that failed before any usage arrived reports nothing, exactly as before; a lockdown refusal reports
always, as the stage already did. A metering error is logged and never replaces the turn's own failure.

### Claims the review said don't hold

* "A stale pass cannot turn [MCP servers] on" (stage record, residual risk 4): true again for the workspace's own
  project layer after F2. Still true that a change the fingerprint does not see (a file deep in a plugin
  directory, an env var outside `CODEX_*`) keeps a passed check until the process restarts.
* "The diagnosis shell reads only its export and platform minimum": its environment is now the allowlist (F1).
* "Captured tokens reach receipts and admission settlement on failed turns": now on every exit (F3).

### Not changed

* Spec conformance rows the review marked as implemented or deferred (fix 5, the owned model catalog: still not
  built, open question Q1 of the stage record; the bundled-vs-remote catalog limit: residual risk 3) are
  unchanged.
* No new LearnLoop configuration key, migration, schema, frontend or `src-tauri` change; no algorithm successor.

### Fail-first

`git archive f68295d05 src` into `fixtures-local/tmp/base-fix`, the fixed `tests/` and `pyproject.toml` copied
beside it, run there with `--rootdir` (so its `pythonpath = ["src"]` is the base source):
**11 failed, 2 passed** of the 13 new tests. The two that pass are the unchanged-behaviour guards
(`test_fresh_workspaces_without_a_project_layer_still_share_one_check`,
`test_a_failure_before_any_usage_reports_nothing_new`). Failures: the three installed-binary F1 cases (canary in
the command's environment), the two override pins (`shell_environment_overrides` missing), both F2 cases, all
four F3 endings (`KeyError: 'input_tokens'`).

### Gate (this step)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok. `TMPDIR=fixtures-local/tmp`.
* `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
* `uv run pytest -n auto <59 files>`: **2083 passed, 1 skipped** in 68.1 s (the stage gate's 2069 plus the new
  tests). Files (all under `tests/`): `test_ad1_codex_rereview_fixes test_ad1_fix_round5 test_ai_config
  test_ai_runtime test_ai_single_request test_ai_tool_isolation test_approach_maps test_architecture
  test_chatgpt_plan_provider test_cli_help_snapshot test_cli_ingest test_cli_json test_codex_attempt_flow
  test_codex_http_client test_codex_isolation_mcp_check test_codex_output_schema test_codex_runtime
  test_codex_tool_lockdown test_config_refactor test_coordinated_migrations test_deferred_regrade
  test_desktop_rpc_contract test_diagnosis_history_modes test_diagnosis_input_provenance test_diagnosis_isolation
  test_e2e_codex_mock test_ingestion_checkpoints test_ingest_runner test_learner_review_system_entries
  test_lo_general test_mcp_tools test_mobile_allowlist test_openai_chat_client test_openai_embedding_client
  test_output_budget test_pf_generation test_practice_index_adapters test_practice_index_dossiers
  test_practice_index_find test_project_atomicity test_project_blindness test_project_capture test_project_cli
  test_project_experiment_store test_project_hooks test_project_probes test_project_redaction test_project_report
  test_provider_resolution_parity test_sidecar_serializer_snapshot test_source_retrieval_codex_unavailable
  test_source_service_spend_accounting test_sources_merge_composition test_sqlite_file_copies
  test_structured_transport_parity test_t6_followup_review test_table_roles test_teach_back
  test_tracked_fixture_databases`. Chosen as the stage gate's list (every file importing the Codex provider, its
  fakes, `project_support`, `ai_runtime` or `PaidCalls`, plus the contract pins); `git grep` for
  `codex_lockdown`, `check_fingerprint`, `isolated_turn_overrides`, `codex_cli_fakes`, `_report_turn_usage` and
  `SdkCodexClient` finds no other test file.
* After the last (docstring-only) edit: `tests/test_codex_tool_lockdown.py tests/test_codex_isolation_mcp_check.py`
  **167 passed, 1 skipped**.
* `PYTHONPATH=<codex 0.163.0 checkout>/sdk/python/src uv run pytest tests/test_codex_tool_lockdown.py::test_the_real_sdk_has_the_seams_the_lockdown_replaces`: **1 passed**.
* The 10 new fake/installed-binary tests rerun alone 3 times: 10 passed each time.
* Not run (owner rule 2026-10-17): the full suite, the whole durability lane, vitest. No migration, DB or
  connection code, frontend, `src-tauri`, schema or config key changed, so no durability, npm, cargo,
  reference, snapshot or registry step applies.

### Live calls and cost

None. No model call of any kind in this round: the installed CLI ran only `sandbox -- /usr/bin/env`,
`mcp list`, `features list` and `debug models --bundled` under throwaway homes with synthetic variables.

### Process notes

* Two commands ran outside `env -i`: an empty `python3 -` heredoc (no code ran) and one
  `uv run python -c` that imported `learnloop.ai.providers.codex_lockdown` from the base export to print its
  `__file__` (no config, network, model or vault access). Every edit script and CLI probe otherwise ran under
  `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.
* No vault opened or copied; no credential file read; no git stash.

## Hardening round 2 (orchestrator)

Verify: Codex job `20261021-113946-qZgmYP` of `c80c54cbb..bc90f31ae`. It confirmed that ordinary text-only turns are
not refused (both `phase="final_answer"` and a phase-less answer set `_answered` before usage arrives), and found
four configuration-dependent Highs and one Low. All five are fixed in `cfa028fa9`, with tests in `tests/test_codex_lockdown_round2.py` (37 tests).

| id | severity | finding | fix | tests |
|---|---|---|---|---|
| H1 | High | Inherited permission grants: the fixed `learnloop_isolated_turn` profile was overlaid on every layer, and Codex merges `permissions.<name>` recursively and honours a lower `extends`; `extends=":read-only"` gave full-disk read, a lower read/write root survived | a fresh, unique name per process (`codex_lockdown.ISOLATED_PROFILE = learnloop_isolated_turn_<16 hex>`), so no layer can name it; the launch check then reads the effective profile back with `codex debug prompt-input` (the thread's model-visible context, no model request) and refuses unless it is exactly: read the turn's directory, read `:minimal`, Codex's own `$CODEX_HOME/tmp/arg0*/codex-arg0*` helper, nothing written, "Network access is restricted." (`permission_profile_violations`) | installed 0.163.0: `test_a_lower_layer_cannot_widen_the_turns_permission_profile[user, profile, project]` (`extends=":read-only"`, an extra read root and a write root on the old name, in `config.toml`, `--profile wide` -> `wide.config.toml`, and a trusted project's `.codex/config.toml`), `test_a_layer_that_names_the_turns_profile_is_caught_by_the_readback[user, profile, project]`, `test_the_launch_check_refuses_a_widened_profile_before_any_turn[user, project]`; fake CLI: `test_a_profile_the_turn_did_not_pass_refuses_it_and_launches_nothing[full-disk-read, write-root, read-root, network]`; pins `test_the_profile_name_is_fresh_and_never_the_fixed_one`, `test_an_unreadable_or_missing_readback_refuses` |
| H2 | High | A relative `CODEX_HOME` and a bare `codex` were fingerprinted from LearnLoop's directory; the subprocess resolves both from the turn's | `SdkCodexClient._launch(root, sandbox)`: `resolve_codex_home` (Codex's rule: an existing directory, canonicalized, relative to the child's cwd; unset = `$HOME/.codex`; a relative `CODEX_HOME` missing from the turn's directory or a relative `HOME` refuses) and `resolve_executable` (a path relative to the child's cwd; a bare name through the child's `PATH`, relative entries against its cwd). Every probe runs with `env={**os.environ, CODEX_HOME: <absolute>}` and the absolute executable; the app server gets the same (`SdkAppConfig(env=...)`, `codex_bin`/`launch_args_override[0]` absolute; an SDK without `env` and a relative home refuses). Under bubblewrap the sandbox's own pinned private home is used. `check_fingerprint` takes the resolved home and stats the binary as named and as its real file | `test_a_relative_codex_home_is_resolved_from_the_turns_directory_and_pinned` (`CODEX_HOME=../codex-home`, two turn directories with their own homes; an MCP server added to the real home is pinned off on the next turn), `test_a_relative_codex_home_missing_from_the_turns_directory_refuses`, `test_a_bare_codex_launch_command_is_resolved_through_path_and_pinned` (`codex app-server`; another `codex` on `PATH` gets its own check), `test_resolution_follows_the_child_not_this_process` |
| H3 | High | The legacy HTTP Codex transport bypassed the lockdown, and its runtime check could run `startup_command` | refused: `codex_lockdown.refuse_legacy_http_transport` raises `CodexHttpTransportRefused` (a `CodexLockdownUnavailable`, naming the lockdown) at every entry: `make_ai_provider_client_from_profile` for `http`/`http_adapter`, `make_codex_client(provider="http")`, `HttpCodexClient.__init__` (so `HttpAdapterProviderClient` too), `supports` (False), `complete_legacy` for each of the eight operations, `_post`, `default_http_healthcheck`, `default_startup`; `check_codex_runtime` returns `codex_unavailable` with the refusal for any non-`sdk` provider before any healthcheck, revision read or startup | `test_an_http_profile_is_refused_by_the_lockdown[http, http_adapter]`, `test_the_legacy_provider_http_is_refused_by_the_lockdown`, `test_every_legacy_operation_is_refused_even_on_an_existing_client[8 operations]`, `test_the_http_runtime_check_never_runs_its_health_request_or_startup_command` (also `check_ai_runtime`; `urlopen` and `Popen` fail the test if reached) |
| H4 | High | `debug models --bundled` validated a catalog the turn need not use (`model_catalog_json`, a remote or cached catalog) | the validated `--bundled` output is written verbatim to a LearnLoop file (a private per-process directory; under bubblewrap a per-turn `.learnloop-codex-catalog-*` directory in the sandbox workdir, removed after the turn) and every turn is pinned to it with `-c model_catalog_json=...` (last override); codex-cli 0.163.0 then serves it through `StaticModelsManager` (no refresh, no cache). `debug models` (no `--bundled`) under the final overrides must return exactly the validated catalog, or the turn is refused (`catalog_violations`). A cached check re-writes the same bytes | fake CLI: `test_a_configured_catalog_cannot_give_the_turns_model_a_tool` (the verify's `experimental_supported_tools=["test_sync_tool"]`), `test_a_catalog_layer_that_beats_the_pin_refuses_the_turn`, `test_a_cached_check_still_pins_the_validated_catalog`; installed: `test_the_installed_codex_serves_the_pinned_catalog_over_a_configured_one` |
| L5 | Low | The AST sweep had a textual prefilter, missed `sdk.Codex(...)`, saw `.turn()` only on `thread`, and covered no HTTP or subprocess launch | new sweep over every module of the four packages (no prefilter): SDK import aliases resolved (`import openai_codex as sdk`, `from openai_codex import Codex as C`), `thread_start`/`resume`/`fork`, `.turn`, `.run_turn` on any receiver, `.run` on a name bound to a thread or turn; all must sit in `_run_verified_sdk_turn` with `approval_mode=deny_all`; subprocess/`os.exec*`/`spawn`/`asyncio` launches whose arguments name Codex only in `_codex_probe` and the refused `default_startup`; HTTP calls in Codex provider modules and every import of the HTTP adapter only after the refusal in the same function; only the Codex provider imports the SDK. New import-linter contract `codex-sdk-only-in-its-provider` (`openai_codex`, `codex_cli_bin` forbidden for all four root packages but `learnloop.ai.providers.codex`; this needed `include_external_packages = true`, which changes no other contract's verdict) | `test_every_codex_turn_app_server_and_transport_in_the_source_is_the_locked_down_one`, `test_the_sweep_sees_aliases_qualified_constructors_and_turns_on_any_name` (detector self-test), `test_only_the_codex_provider_may_import_the_sdk_by_import_contract`; contract checked by hand to break on a temporary `import openai_codex as sdk` in a provider module |

### Notes on the fixes

* **What the launch check runs now** (once per process and config fingerprint, as before): `mcp list` (twice when
  servers are pinned), `features list` (twice when an unclassified feature is switched off), `debug models
  --bundled`, `debug models` (pinned) and `debug prompt-input`: about 0.4 s more on an empty home. None makes a model
  request; with the pin in force `debug models` makes no network request either. `debug prompt-input` builds an
  ephemeral thread under the turn's own overrides (MCP, plugins, apps, hooks off), as the app server's
  `thread_start` does.
* **`_run_sdk_turn` split**: the turn after its launch check is `_run_verified_sdk_turn`, so the sandboxed turn's
  catalog directory is removed on every exit. No behaviour change otherwise.
* **Served behaviour**: Codex turns now use the binary's bundled model metadata (the catalog the check validated)
  instead of the remote-refreshed or cached one. That was stage open question Q1's concern; the orchestrator chose
  the pin. A model the bundled catalog does not list was already refused.
* **The HTTP adapter as a test double**: 19 test files (16 module-wide, 3 for single tests) drive an in-process HTTP server through the adapter
  as a stand-in model (CLI attempt/propose/ingest/generate-practice, sidecar tutor/teach-back/contract, TUI feedback,
  deferred regrade, receipts, capture). They now request the conftest fixture `legacy_codex_http_double`, which
  replaces `codex_lockdown.refuse_legacy_http_transport` for that test only (each call site looks it up on the
  module). No configuration key, environment variable or flag reaches it. Moving those tests to a structured fake
  and deleting the adapter is a follow-up.
* **Stage record**: residual risks 3 (bundled vs remote catalog) and 6 (legacy HTTP adapter) and open questions Q1
  and Q5 are superseded by H4 and H3.

### Fail-first

`git archive bc90f31ae src pyproject.toml migrations` into `fixtures-local/tmp/base-r2`, the fixed `tests/` copied
in, run there with `--rootdir . -o pythonpath=src` (the base source first): **36 failed, 1 passed** of the 37 new
tests. The one that passes is the sweep's detector self-test (it tests the test's own parser). Failures by kind:
the installed binary showing `:root` (and the extra read/write roots) on the old name in the user, profile and
project layers (3); the fake CLI's widened profile and forced catalog not refused, the missing relative home not
refused (`DID NOT RAISE`, 6); `the stale check left the new server on` (relative `CODEX_HOME`) and `the other codex
on PATH reused the first one's check` (bare `codex`); the installed binary serving `test_sync_tool` over the bundled
catalog; the HTTP runtime check reporting `ready` (1) and each of the eight operations still declared (`supports`
True, 8); the sweep finding the turn outside the new owner and HTTP calls before any refusal; the missing import-linter
contract; and the new lockdown API (`ISOLATED_PROFILE`, `permission_profile_violations`, `CodexHttpTransportRefused`,
`catalog_pin_path`, `resolve_executable`: `ImportError`/`AttributeError`, 13).

### Changed existing tests

* Every exact comparison of a launch with `isolated_turn_overrides(...)` passes `model_catalog=catalog_pin_path(...)`;
  probe sequences and counts gain `debug models` and `debug prompt-input` (`test_codex_isolation_mcp_check`,
  `test_codex_tool_lockdown`, `test_diagnosis_isolation`, `test_ai_tool_isolation`). Two bubblewrap tests assert the
  per-turn catalog directory is gone after the turn and list without the pin afterwards.
* The old AST sweep in `test_codex_tool_lockdown.py` keeps only the order checks inside the turn; the sweep moved to
  the new file.
* Fakes: `write_fake_codex` answers `debug models` without `--bundled` (pin, `user_catalog`, `forced_catalog`) and
  `debug prompt-input` (`permission_layers`, `forced_permissions`), reads a user layer's MCP servers from
  `$CODEX_HOME/config.toml`, and its app server reports the catalog's experimental tools and `CODEX_HOME`;
  `stub_isolation_probe` answers both new probes and stubs `_launch`; `install_fake_codex_sdk(spawn=True)` passes the
  SDK's `env`; `scripts/benchmark_chatgpt_plan_latency.py` uses `stub_isolation_probe`.

### Gate (this round)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok. `TMPDIR=fixtures-local/tmp`. Run under
  `flock /tmp/learnloop-fullsuite.lock` (it waited for the merge2 landing's suites and two other worktrees' gates).
* `uv run lint-imports --no-cache`: **29 kept, 0 broken** (the stage's 28 plus `codex-sdk-only-in-its-provider`).
* `uv run pytest -n auto <75 files>`: **2434 passed, 1 skipped** in 76.7 s. The stage gate's 59 files, the new
  `test_codex_lockdown_round2`, and every other test file this round changed or that imports their HTTP-double
  helpers (all under `tests/`): `test_ad1_codex_rereview_fixes test_ad1_fix_round5 test_ai_config test_ai_runtime test_ai_single_request test_ai_tool_isolation test_approach_maps test_architecture test_chatgpt_plan_provider test_cli_help_snapshot test_cli_ingest test_cli_json test_codex_attempt_flow test_codex_http_client test_codex_isolation_mcp_check test_codex_output_schema test_codex_runtime test_codex_tool_lockdown test_config_refactor test_coordinated_migrations test_deferred_regrade test_desktop_rpc_contract test_diagnosis_history_modes test_diagnosis_input_provenance test_diagnosis_isolation test_e2e_codex_mock test_ingestion_checkpoints test_ingest_runner test_learner_review_system_entries test_lo_general test_mcp_tools test_mobile_allowlist test_openai_chat_client test_openai_embedding_client test_output_budget test_pf_generation test_practice_index_adapters test_practice_index_dossiers test_practice_index_find test_project_atomicity test_project_blindness test_project_capture test_project_cli test_project_experiment_store test_project_hooks test_project_probes test_project_redaction test_project_report test_provider_resolution_parity test_sidecar_serializer_snapshot test_source_retrieval_codex_unavailable test_source_service_spend_accounting test_sources_merge_composition test_sqlite_file_copies test_structured_transport_parity test_t6_followup_review test_table_roles test_teach_back test_tracked_fixture_databases test_codex_lockdown_round2 test_capture_desktop test_capture_route_recovery test_cli_attempt test_cli_generate_practice test_cli_propose test_field_signal_production_paths test_model_call_receipt_owners test_sidecar_contract test_sidecar_teach_back test_sidecar_tutor_qa test_teach_back_generation test_tui_feedback test_tutor_delivery_fixes test_causal_repair_sidecar_rpcs test_hypothesis_surface_wiring `.
* The installed-binary tests ran against codex-cli 0.163.0 (`/usr/bin/codex`) and passed, among them the bubblewrap
  ones (the readback and the pin inside the sandbox).
* Not run (owner rule 2026-10-17): the full suite, the whole durability lane, vitest. No migration, DB or connection
  code, frontend, `src-tauri`, schema or config key changed. The landing gate's full suite covers any other test
  file that drives the legacy HTTP adapter without the `legacy_codex_http_double` fixture (none found by grep for
  the adapter's helpers, servers and endpoint paths).

### Live calls and cost

None. The installed CLI ran only `debug prompt-input`, `debug models` (with and without `--bundled`), `mcp list`,
`features list` and `--help` under throwaway homes (the probes by hand under `env -i` with empty `HOME`/`CODEX_HOME`/
`LEARNLOOP_CONFIG_DIR`; the tests under pytest with a throwaway `CODEX_HOME`).

### Process notes

* One `python3` heredoc that edited `pyproject.toml` (string replacement only, no LearnLoop import, no config, network
  or vault access) ran outside `env -i` before I applied the rule to it; every later script, edit and CLI probe ran
  under `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.
* The Codex source read was the local checkout `~/Documents/thinking/codex` (`c955f73078`, June: `models-manager`,
  `model-provider`, `utils/home-dir`, `cli/src/main.rs`, `core/src/prompt_debug.rs`); every behaviour the fixes rely
  on was then confirmed on the installed 0.163.0 by the non-model probes above.
* No vault opened or copied (the base export holds only `src`, `pyproject.toml`, `migrations`); no credential file
  read; no git stash.

## Hardening round 3

Verify: Codex job `20261021-130509-fPY40I` of `bc90f31ae..3c16fa0d1` (REOPENED). It confirmed the round-2 fixes
(unique profile, child-side path resolution, HTTP refusal, catalog pin), that the HTTP fixture is test-only, and
that ordinary text turns pass the early-stop logic. It found three Highs and one Low. Binding orchestrator ruling:
**every LearnLoop Codex turn is tool-free by construction**. Fix commit: `cc4a9919a`. Tests:
`tests/test_codex_lockdown_round3.py` (14 tests).

| id | severity | finding | fix | tests |
|---|---|---|---|---|
| R3-H1 | High | Inherited execution-policy `allow` rules (`$CODEX_HOME/rules`, project `.codex/rules`) make an allowed command skip the sandbox; the snapshot diagnosis kept a shell | **No route keeps a shell.** The Codex transport inlines a read-only workspace: `SdkCodexClient._inline_workspace` reads every export file with the ChatGPT plan provider's `ServedWorkspace.inline_block` (each recorded as served, so `workspace_activity()` names exactly what the turn was shown and the diagnosis provenance maps it), appends `INSTRUCTIONS_INLINE` and the blocks to the prompt, and runs the turn tool-free in a fresh scratch directory. An export over `INLINE_WORKSPACE_MAX_CHARS` (400,000, the plan provider's default) refuses before launch, never cut short. The diagnoser admits the inlined size (`inlines_workspace`). With no command tool, no rule has anything to apply to; read back as an empty tool list (R3-H3) | installed 0.163.0: `test_the_installed_codex_offers_the_turn_no_tool_at_all[text, snapshot-diagnosis]` (a real `prefix_rule(pattern=["python3"], decision="allow")` in `$CODEX_HOME/rules`; control: the bundled catalog offers `functions.exec`/`functions.wait`); `test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output`, `test_an_export_over_the_inline_budget_refuses_before_launch` |
| R3-H2 | High | Native skill discovery (user, `~/.agents/skills`, system, project roots, following symlinks) and `$name` / SKILL.md-link expansion can bring host or vault files into a turn | every turn gets `skills.bundled.enabled=false`; the launch check reads the rendered skills catalog back from `debug prompt-input` (with `skills.max_context_tokens=10000` so it renders in full), disables every listed skill **by name and by path** with a `-c skills.config=[...]` (the highest layer; codex-cli 0.163.0 `skill_config_rules_from_stack` applies it last, and mention selection only takes enabled entries), reads back again, and refuses unless no skill is listed or if the listing cannot be parsed (`rendered_skills`, `skill_disable_overrides`). The skills found are cached with the check; the fingerprint now covers `/etc/codex/skills`, `~/.agents{,/skills}` and every ancestor's `.codex/skills` / `.agents{,/skills}` | installed: `test_the_installed_codex_lists_and_expands_no_skill` (a skill directory in `~/.agents/skills` symlinked to a file outside with a canary body; the prompt carries `$canary-skill` and a link to its SKILL.md; control: listed without the overrides); fake: `test_a_skill_that_stays_listed_refuses_the_turn`, `test_the_skills_parser_reads_the_rendered_catalog` |
| R3-H3 | High | A hidden code-mode continuation after a final answer is not admitted before its request | **Q1 answered yes: LearnLoop owns the catalog.** The pin (round 2) now writes the validated `debug models --bundled` output with every tool removed from every entry (`TOOL_FREE_METADATA`: `tool_mode=direct` (code mode off), `apply_patch_tool_type=null`, `shell_type=disabled`, `experimental_supported_tools=[]`, `supports_search_tool=false`, `multi_agent_version=disabled`, `node_repl_disabled=true`, no skills/plugins/apps usage instructions). The launch check verifies `debug models` returns exactly it and that `debug prompt-input` with `features.incremental_tools=true` (probe only; it makes codex-cli 0.163.0 declare the model-visible tools as an `additional_tools` input item, `core/src/session/turn.rs build_prompt`) declares **no tool**, gated on the incremental form being in effect (the first developer message is exactly the model's pinned `base_instructions`); a model not served through Responses Lite cannot be read back and is refused. No tool, so no tool call, so no continuation. The early stop, item checks and request count stay as the backstop | `test_the_pinned_catalog_removes_every_tool_from_every_entry`, `test_every_turn_is_pinned_to_the_tool_free_catalog`, `test_a_turn_that_would_offer_any_tool_is_refused_before_launch[catalog-with-tools, a-tool-from-elsewhere, no-read-back]`, and the installed test of R3-H1 |
| R3-L4 | Low | The AST sweep misses aliased (`from subprocess import Popen as launch`, `import subprocess as sp`) and variable-argument launches | every **reference** (not only calls) to a process-launching function of `subprocess`, `os` (`system`, `popen`, `exec*`, `spawn*`, `posix_spawn*`, `fork*`), `asyncio` and `pty`, through any import alias, `getattr(<module>, ...)` or `*.subprocess_exec/shell`, in `src`, `scripts` and `integrations`, must be on `APPROVED_LAUNCH_SITES` (31 reviewed sites, file + enclosing scope + target); whatever the arguments, the site is listed. The Rust shell must start exactly one process (`sidecar.rs`) | `test_every_process_launch_site_is_approved`, `test_the_launch_sweep_sees_aliases_variables_and_references` (the verify's three shapes, a default-argument reference, `getattr`, `loop.subprocess_exec`) |

Stage open questions answered by the ruling: **Q1** (a LearnLoop-owned catalog) yes, by necessity: the bundled
catalog minus its tools; **Q2** (the snapshot diagnosis's shell) inline. Residual risks 1, 2 and 7 of the stage
record (code mode and `apply_patch` advertised, detection not prevention, the diagnosis shell) are closed by them.

### What could not be done by configuration (recorded, not silently skipped)

* **Excluding inherited `.rules` files.** codex-cli 0.163.0 loads `<layer>/rules/*.rules` for every layer
  (`core/src/exec_policy.rs load_exec_policy`); only `codex exec --ignore-rules` sets
  `ignore_user_and_project_exec_policy_rules`, and the app server has no equivalent key or flag. There is also
  no non-model read-back of the effective exec policy (`codex execpolicy check` takes explicit rule files). The
  fix is therefore structural: no turn has a tool that runs a command, which the read-back proves. A future CLI
  that adds a command tool fails the tool read-back and refuses every turn.
* **Proving the tool list without a model request.** The tool read-back uses a probe-only
  `features.incremental_tools=true`; the turn itself does not enable it (an under-development feature). It
  relies on incremental declaration listing the same `model_visible_specs` the turn would send (source-traced:
  `build_prompt` chooses between declaring them in `tools` and as an item, from one list).

### Behaviour changes

* **Diagnosis (expected, ruled):** the snapshot diagnosis no longer explores the export with a shell; it reads it
  inline (the prompt grows by the export, about 100k tokens at most). The output contract, validation, provenance
  shape and prompt version are unchanged; `opened` in the receipt now lists every export file (all were shown)
  instead of the shell commands. An export over 400,000 characters fails the diagnosis (status `failed`,
  `AIProviderUnavailable`) instead of being explored; open question below.
* **Every Codex turn:** the model's instructions and metadata come from the binary's bundled catalog minus its
  tools (round 2 already moved them off the remote catalog). The base instructions still describe tools the turn
  no longer has; a model that tries to call one has no tool to call.
* **Launch check:** `debug prompt-input` now runs once more when skills exist (about 0.4 s, cached).
* **Models not served through Responses Lite** (in 0.163.0's bundled catalog: `gpt-5.5`) are refused, since
  their tools cannot be read back.

### Fail-first (on `3c16fa0d1`)

`git archive 3c16fa0d1 src pyproject.toml migrations` into `fixtures-local/tmp/base-r3`, the fixed `tests/` copied
in, run with `--rootdir . -o pythonpath=src`: **13 failed, 1 passed** of the 14 new tests. The pass is the launch
sweep's detector self-test (it tests the test's own parser). Failures: the installed binary offering the turn tools
for the text turn and the snapshot diagnosis (2, "the turn would be offered tools"); the installed binary listing
the linked skill in the turn's context (1); a widened catalog, a tool from elsewhere and a model without read-back
not refused (`DID NOT RAISE`, 3); no skill overrides in the launch (1); the snapshot diagnosis inlining nothing
(1); the approved-launch list (1); the new API (`tool_free_catalog`, `tool_free_violations`, `rendered_skills`,
`INLINE_WORKSPACE_MAX_CHARS`: `AttributeError`, 4).

### Changed existing tests

The workspace-turn tests now expect a scratch cwd, `shell=False` and the inlined blocks (`test_codex_tool_lockdown`,
`test_codex_isolation_mcp_check`, `test_diagnosis_isolation`, `test_diagnosis_history_modes`,
`test_ai_tool_isolation`: a workspace outside the sandbox is now inlined, not refused); a command item refuses
every turn; F3's usage test uses one answered request; round 2's F2 project-layer tests became
`test_a_workspaces_own_project_layer_never_reaches_the_turn`; probe lists end with `debug prompt-input` under the
read-back overrides; round 2's catalog tests expect the tool-free catalog; the relative-`CODEX_HOME` test places
scratch turns through `tempfile.tempdir`. Fakes: the renderer declares the pinned entry's tools in incremental form
and lists `skills` minus `skills.config` disables; `install_fake_codex_sdk` takes `respond`; the bubblewrap
`/bin/sh` fake serves the pinned catalog and an incremental read-back.

### Gate (this round)

* Under `flock /tmp/learnloop-fullsuite.lock`; `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: **29 kept, 0 broken**.
* `uv run pytest -n auto <100 files>`: **2722 passed, 1 skipped, 2 xfailed** in 118 s: round 2's 75 files plus
  `test_codex_lockdown_round3 test_diagnose_review test_diagnose_review_spend test_diagnosis_adjudication test_diagnosis_async_router test_diagnosis_card test_diagnosis_context test_diagnosis_contract test_diagnosis_embeddings test_diagnosis_input_provenance_landing test_diagnosis_pipeline test_diagnosis_replay test_diagnosis_reports test_diagnostic_augmentation test_diagnostic_gate test_diagnostic_generation test_diagnostic_pack test_diagnostic_probe_freshness test_diagnostic_probe_single_use test_diagnostic_review_policy test_facet_diagnostics_v03 test_followup_diagnostic_selection test_placement_diagnosis_decides test_residual_diagnostics test_sidecar_diagnostic `(all under `tests/`; every diagnosis test file).
* The installed-binary tests (round 2 and 3, bubblewrap included) ran against `/usr/bin/codex` 0.163.0 and passed.
* Not run (owner rule): the full suite, the durability lane, vitest.

### Residuals for the owner's first live use (no live call this round)

1. **The served turn has no tool.** Run one tutor question with `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG`: the turn
   should answer in text, and a prompt that asks it to run code should get a text refusal, not a
   `CodexToolUseRefused` (which would mean a tool was offered). The read-back proves the tool list only through
   the incremental declaration path.
2. **Skill expansion.** `debug prompt-input` does not run the turn-start skill injection; that no enabled skill
   exists is what is verified. A live turn whose prompt names a disabled skill (`$imagegen`) should not bring its
   SKILL.md into the context.
3. **A snapshot diagnosis inline:** the first live one should complete with `opened` listing every export file;
   watch the prompt size on the largest vault.
4. **Model quality:** the bundled instructions still mention tools the model no longer has; check the first
   gradings and tutor answers read as before.

### Open questions (with defaults)

* **R3-Q1.** An export over 400,000 characters fails the snapshot diagnosis. Fall back to the `exact` mode for it,
  or send a deterministic excerpt (the newest attempts first)? **Default: fail, as the ChatGPT plan's inline mode
  does** (never cut short silently).
* **R3-Q2.** Strip the tool paragraphs from the bundled base instructions too? **Default: no** (instructions stay the
  bundled ones, as ruled).
* **R3-Q3.** Allow `gpt-5.5` (not Responses Lite) by trusting the tool-free catalog without a read-back?
  **Default: no** (fail closed).

### Live calls and cost

None. Non-model CLI commands only (`debug prompt-input`, `debug models`, `features list`, `mcp list`), by hand
under `env -i` with throwaway homes and in tests with throwaway `HOME`/`CODEX_HOME`. Codex 0.163.0 source was read
from a sparse, shallow clone of `rust-v0.163.0` in the session scratchpad.

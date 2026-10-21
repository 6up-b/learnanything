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

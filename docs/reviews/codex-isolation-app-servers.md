# Codex isolated turns refused to launch on plugin MCP servers (codex-isolation-app-servers)

Stage `codex-isolation-app-servers`, branch `fix/codex-isolation-app-servers`,
worktree `learnanything-codex-sandbox`, from main `495c7437f` (mvp-0.25,
migrations to 206). Urgent: the orchestrator started it on 2026-10-16 after the
chatgpt-plan-peer stage's live check found that every isolated Codex turn on
this machine failed at launch, before any model request, with

```
Codex process closed stdout. stderr_tail=Error: invalid transport in mcp_servers.codex_app
```

Owner decisions in force (2026-10-12): the recommended defaults recorded in each
spec are accepted; Codex on the ChatGPT subscription may run every paid LLM role,
with cost estimated from token usage; frictionless defaults (honest labels,
generous defaults, live changes behind kill switches). This is a transport fix
only. No algorithm successor: replay reads none of it, no schema, CLI, RPC or
frontend change.

## 1. What changed

| Commit | What |
|---|---|
| `cd78e6d6e` | The fix in `src/learnloop/ai/providers/codex.py` (the launch check), the fail-first tests `tests/test_codex_isolation_mcp_check.py`, the fake CLI `tests/codex_cli_fakes.py`, and the fake SDK's spawn mode passing `config_overrides` the way the real SDK does (`tests/project_support.py`). Existing isolation tests now stub the new probe seam (`_codex_probe`) instead of the removed `_configured_mcp_server_ids`. |
| `44a48e326` | `isolated_turn_overrides`' docstring states what a shell-off turn still offers on codex-cli 0.163.0 (section 7) |
| this commit | Server names with `:`, `@`, `/` (valid in 0.163.0) are disabled by name; only a dotted name refuses; two tests; this review |

## 2. Cause

Isolated turns (Slice 1 §4/§5.6) carry the blind grader, the snapshot and
no-workspace diagnoser, and every isolated judge or checker: offline-review
judges and probes, recurrence judging and benchmarks, text-gap judges,
contamination judge, PF calls, the Reader quick check, method phrasing and
method-statement judges, field classification and probability prep (every
`isolated=True` caller in `src/learnloop`). Each launches the Codex app server
with `-c` overrides that put the turn under the `learnloop_isolated_turn`
permission profile and switch off its tools and integrations. Because an MCP
tool runs outside the command sandbox, the transport also ran `codex mcp list
--json` with **no** overrides, and disabled every listed name with
`-c mcp_servers.<name>.enabled=false`.

On 2026-10-15 the owner's Codex CLI became codex-cli 0.163.0. `codex mcp list
--json` lists the servers a config file defines **and** the ones an enabled
plugin brings. On this machine (names and enabled state only):

| Listed server | Enabled | Where it comes from (shown by behaviour) |
|---|---|---|
| `codex_app` | false | a plugin: gone under `-c features.plugins=false` |
| `cua_repl` | true | a plugin: gone under `-c features.plugins=false` |
| `node_repl` | true | a config file: survives `features.plugins=false`, disabled by its name override |
| `openaiDeveloperDocs` | true | a config file: same |

Codex applies `-c a.b.c=v` by splitting the key on `.` and creating every
missing table (0.163.0 `codex-rs/config/src/overrides.rs:18-22`,
`apply_toml_override`). For `codex_app` no config file has a
`[mcp_servers.codex_app]` table, so the override creates one holding only
`enabled = false`. An MCP server table must have `command` (stdio) or `url`
(streamable HTTP), so loading it fails with `invalid transport`
(`codex-rs/config/src/mcp_types.rs:543`), and every subcommand, `app-server`
included, refuses to start: `Error: failed to load bootstrap configuration ...
invalid transport in mcp_servers.codex_app`.

Plugin servers have been listed by `mcp list` since Codex merged plugin MCP
servers into the configured set (`feat: load from plugins`, 2026-03-01 in the
source history). So the old code was wrong for any plugin with an MCP server.
The 0.163.0 update is when such plugins became active on this machine (plugin
servers that are enabled, or merely listed like `codex_app`).

**Reproduced three ways, fail first:**

1. A fake `codex` modelled on 0.163.0 (`tests/codex_cli_fakes.py`) behind the
   fake SDK, which launches it exactly as the real SDK does:
   `test_plugin_servers_are_disabled_by_feature_and_config_servers_by_name`
   failed on the old code with `Codex process closed stdout. stderr_tail=Error:
   failed to load bootstrap configuration ... invalid transport`. 17 of the 19
   new tests failed before the fix. The 2 that passed document the cause on the
   installed binary.
2. The installed binary, hermetically: a throwaway `CODEX_HOME` with one config
   server and one plugin of its own (`plugins/cache/test/sample/local` with a
   `.mcp.json`). `codex -c mcp_servers.sampleplug.enabled=false mcp list --json`
   fails with `invalid transport in mcp_servers.sampleplug`
   (`test_the_installed_codex_rejects_a_name_override_for_a_plugin_server`).
3. Live, through `SdkCodexClient` and the real SDK on the owner's setup, before
   the fix (section 6, call 1): `AIProviderUnavailable: Codex process closed
   stdout. stderr_tail=Error: invalid transport in mcp_servers.codex_app`, after
   0.6 s, with 0 tokens.

## 3. The Codex facts behind each override

The SDK checkout at `~/Documents/thinking/codex` (`c955f73078`, 2026-06-02) is
four months older than the CLI that runs. So each fact below was read in the
0.163.0 source (tag `rust-v0.163.0`, `83086188a`, shallow-cloned read-only into
the session scratchpad) **and** checked against the installed binary.

| What the isolated turn must have off | 0.163.0 source | What turns it off | Checked on the binary |
|---|---|---|---|
| MCP servers a **config file** defines | `core/src/config/mod.rs:1865` registers `self.mcp_servers` (config layers) into the catalog | `-c mcp_servers.<name>.enabled=false`. The layer merges onto the config table, which has a transport | `node_repl`, `openaiDeveloperDocs`, `fsserver` list `enabled: false` |
| MCP servers a **plugin** brings | `core/src/config/mod.rs:1821-1859` registers active plugins' servers; `core-plugins/src/manager.rs:821-823` loads no plugins when `!plugins_enabled`, which is `features.enabled(Feature::Plugins)` (`core/src/config/mod.rs:1767-1772`) | `-c features.plugins=false`, already in `_ISOLATION_DISABLED_FEATURES`. A name override is **invalid** here (section 2) | `codex_app`, `cua_repl`, `sampleplug` are absent from the list |
| The ChatGPT **connectors** server `codex_apps` | `core/src/mcp.rs:402-417` registers it only when `apps_enabled`; the host extension `ext/mcp/src/lib.rs:38-62` contributes it only under `Feature::Apps`, else removes it; `codex-mcp/src/mcp/mod.rs:438-440` drops it unless `host_owned_codex_apps_enabled` (apps on and ChatGPT auth) | `-c features.apps=false` (already in the list) | `features list` shows `apps false`. **`mcp list` never shows `codex_apps`** (it lists `configured_servers`, "config- and plugin-backed servers without runtime contributions", `core/src/mcp.rs:459`; `cli/src/mcp_cmd.rs:690-696` with an empty extension registry, `:535-541`), so this feature has to be checked separately |
| **Cloud plugin** connectors | `ext/mcp/src/plugin.rs:197-205`: contributed only when `Feature::Plugins` | `features.plugins=false` | `features list` shows `plugins false` |
| Servers of plugin roots a client **selects** for a thread | `core/src/mcp.rs:254-290`: registered unless the plugin id is disabled, **even with `features.plugins=false`** | nothing in the overrides; LearnLoop never selects capability roots (the SDK `thread_start` passes none) and runs no remote executor | not reachable from LearnLoop's launch; noted as a residual (section 10) |
| An enabled server started at all | `codex-mcp/src/connection_manager.rs:330-332` starts only `server.enabled()` servers | the above | the turns' items show no MCP call (section 6) |

Two more facts the fix relies on:

* **Unknown feature keys are ignored.** `codex -c
  features.nonexistent_feature_xyz=false mcp list --json` succeeds and lists the
  same servers. So the feature list stays valid on older and newer CLIs.
* **A name override is valid only for a config-defined server.** Under the
  feature overrides a plugin server is gone. So a server still listed is a
  config one, and only those get a name override. A server Codex keeps listing
  that no config file defines would make the name override invalid: the check
  catches that and refuses (section 4).

## 4. The fix

> **Corrected after the Codex review (2026-10-16,
> `docs/reviews/codex-isolation-app-servers-codex-review.md`, commit `08da634f5`).**
> Three statements in this section did not hold.
>
> * Step 2: already-disabled servers are now pinned off too (F1).
> * Step 3, "the exact launch set": an `sdk_launch_command`'s options after
>   `app-server` are now part of that set (F2).
> * "Not cached": under bubblewrap the check now runs **inside** the sandbox, in
>   the turn's directory. On the host it could see a layer the sandbox lacks, such
>   as a trusted ancestor project's `.codex/config.toml` (F1). So "can load no more
>   than was checked" and "Nothing was loosened" were wrong as written.
>
> The probes also run inside the request's deadline and stop on interrupt (F3).
> The text below is the stage as first written.

`SdkCodexClient._verified_isolated_overrides(root, shell=...)` replaces
`_configured_mcp_server_ids` on the isolated launch path (`_run_sdk_turn`):

1. `codex <isolated overrides> mcp list --json` in the turn's own directory
   (the empty scratch directory, or the read-only workspace) with this process's
   environment, as the app server is launched. Under those overrides
   `features.plugins=false` has already removed the plugin servers.
2. Every server still listed and not exactly `enabled: false` gets
   `mcp_servers.<name>.enabled=false`. 0.163.0's `codex mcp add` accepts
   letters, digits and `-_:@/.` in a name (`cli/src/mcp_cmd.rs:1141-1150`).
   Codex splits a `-c` key on `.`, so a dotted name cannot be addressed:
   `mcp_servers.a.b.enabled=false` creates a table `a` without a transport, as
   the binary shows. A listed name containing `.` refuses the turn. Names
   with `:`, `@` or `/` are disabled by name, which the binary accepts.
3. **The check, on the exact launch set:** `mcp list --json` again (skipped
   when step 2 added nothing, because then step 1 already ran the exact set) must
   list every server off or absent. If Codex rejects one of our name overrides
   (`invalid transport in mcp_servers.<name>`), that server is not a config one
   and nothing here disables it: refuse, naming it. Then `codex features list`
   must report `apps` and `plugins` **false**. A renamed key that Codex silently
   ignored would leave connectors or plugins on, and `mcp list` cannot show the
   connectors server.
4. Fail closed throughout. A check that cannot run, exits non-zero, times out
   (60 s each), or returns no server list raises `CodexUnavailable` ("...;
   refusing the isolated turn.") before the app server starts. From Codex's
   stderr only the name of a rejected `mcp_servers` table is passed on, because
   its config errors can quote config lines (headers, env). From `mcp list` only
   names and enabled state are read.

**Not cached.** The answer depends on config files (user, system, managed,
project `.codex/config.toml` of the turn's directory), the plugin cache and
installed plugins. Any of these can change between turns without a new binary
or version. And an isolated turn's directory is new each time, so a per-cwd
cache would never hit. Cost: two or three `codex` subcommands per isolated turn,
0.04 to 0.45 s each on this machine, against turns of 10 s or more. Under
bubblewrap (project routes) the check runs on the host. The sandboxed app
server's private home holds only the host's `config.toml` (no plugin cache), so
it can load no more than was checked.

The override set itself is unchanged (the same profile, features and tool
switches as before), apart from **which** servers get a name override. Nothing
was loosened. A turn that launched before still launches with the same
overrides when it has no plugin servers.

## 5. Tests

`tests/test_codex_isolation_mcp_check.py`: 21 tests. Of the 19 written before
the fix, 17 failed on the old code. The last two rows of the table below were
added for server names after the 0.163.0 name rule was read.

| Case | Test |
|---|---|
| The owner's shape: config servers disabled by name, plugin servers by feature, no name override for `codex_app`/`cua_repl`; probe order and the exact launch set | `test_plugin_servers_are_disabled_by_feature_and_config_servers_by_name` |
| A read-only workspace turn is checked under its own (shell-on) overrides | `test_a_read_only_workspace_turn_is_checked_under_its_own_overrides` |
| Nothing to disable: the first listing is the check (2 probes) | `test_without_servers_the_first_listing_is_the_check` |
| The old CLI shape (config servers only, fewer fields; an already-off server gets no override) | `test_the_old_cli_shape_still_disables_config_servers_by_name` |
| A server nothing disables refuses: listed whatever the features with its override rejected; override accepted but it stays on; a name a `-c` path cannot address | `test_a_server_nothing_disables_refuses_the_turn` (3) |
| The check failing, returning garbage or timing out (`mcp list` and `features list`) refuses, and no stderr or transport text leaks into the error | `test_a_check_that_fails_or_times_out_refuses_the_turn` (5) |
| Connectors or plugins left on (an ignored override; a missing feature row) refuse | `test_connectors_or_plugins_left_on_refuse_the_turn` (2) |
| No Codex CLI at the configured path refuses | `test_a_missing_codex_cli_refuses_the_turn` |
| Non-isolated turns run no check | `test_non_isolated_turns_run_no_check` |
| Installed binary, throwaway home with its own plugin: the old override set is rejected; the new check passes and leaves only the config server, disabled (shell on and off) | `test_the_installed_codex_rejects_a_name_override_for_a_plugin_server`, `test_the_installed_codex_passes_the_launch_check` (2) |
| Config server names with `/`, `@`, `:` are disabled by name | `test_config_server_names_with_path_characters_are_disabled_by_name` |
| Installed binary: `/` is addressable, a dotted name is not (its override names table `a`), and the check refuses `'a.b'` | `test_the_installed_codex_addresses_path_characters_but_not_dots` |

All existing isolation tests stay green. `tests/test_diagnosis_isolation.py`'s
installed-binary test now goes through `_verified_isolated_overrides`. The
fake-SDK tests in it, `tests/test_diagnosis_history_modes.py`,
`tests/test_pf_generation.py` and `tests/test_ai_tool_isolation.py` (the
bubblewrap ones included) stub `_codex_probe` with
`tests.codex_cli_fakes.stub_isolation_probe`, a model of config servers and
feature overrides.

## 6. Live verification (Codex subscription; 4 of the 6 allowed calls)

Calls 1 to 3 went through `SdkCodexClient` and the real SDK from the checkout,
`gpt-5.6-sol` at low effort, in scratch directories under the session
scratchpad (no vault content), via a driver that records only server names,
enabled state, feature states, item types and usage.

| # | Call | Result | Tokens (input / output, cached, reasoning) |
|---|---|---|---|
| 1 | **Before the fix**: isolated turn, shell off, empty scratch directory | Refused at launch after 0.6 s: `Codex process closed stdout. stderr_tail=Error: invalid transport in mcp_servers.codex_app`. No model request | 0 / 0 |
| 2 | After the fix: isolated turn, shell off, empty scratch directory, trivial prompt ("pong") | Launched and answered `pong`. Check: base listing `node_repl` on, `openaiDeveloperDocs` on (no `codex_app`, `cua_repl`); after the two name overrides both `enabled: false`; `features list` `apps false`, `plugins false`, `shell_tool false`. Turn items: `userMessage`, `reasoning`, `agentMessage` only | 10,835 / 110, 0, 40 |
| 3 | After the fix: isolated turn with the read-only workspace (a scratch directory with one `NOTE.txt`) | Launched; answered with the note's sentence. Same check (both config servers off; `apps`, `plugins` false; `shell_tool` true for a workspace). Items: two `commandExecution` (`sed -n '1p' NOTE.txt`; and the requested network probe `curl -sS -m 5 https://example.com`, which printed `curl: (6) Could not resolve host: example.com` / `NET-BLOCKED`), no MCP, connector or web-search item; `workspace_activity()` reported both commands | 23,310 / 481, 11,264, 88 |
| 4 | After the fix: **one blind grading through the normal practice door** on a backup-API copy of this worktree's tracked `fixtures/probability` (`learnloop.db.copies.copy_tree_with_databases` into `fixtures-local/probability-codex-isolation`, upgraded on the copy from mvp-0.8 to mvp-0.25 so its practice door grades blind) | `learnloop attempt pi_using_the_three_trial_sa --ai-provider codex_low --no-diagnose --max-calls 2` (dry run first: kind `blind`, 1 call, `estimated_only`). Graded `grading_source codex`, rubric score 3/3, blind record `mvp-2.1-blind-reference-policy+own-route-v2` / `blind_grading_proposal_v1`. The isolated launch check ran in a scratch directory outside the vault: both config servers off, `apps`, `plugins`, `shell_tool` false. Items: `userMessage`, `reasoning`, `agentMessage` | 17,281 / 610, 0, 126 |

Totals: 4 calls, 3 with model requests; 51,426 input and 1,201 output tokens on
the subscription. Spend reported `cost_basis estimated_only`,
`metered_estimated_usd 0.0`. No OpenRouter or other paid call was made. The
tracked fixture is unchanged (`git status fixtures/` clean). An earlier
`learnloop attempt` invocation without `--criterion-points` stopped at the CLI's
self-grade prompt before any call, so it is not counted.

## 7. Second finding: what a shell-off isolated turn still offers on 0.163.0

Call 2's model reported its tools as `exec`, `wait`, `request_user_input` and
`collaboration.{spawn_agent, send_message, followup_task, wait_agent,
list_agents, interrupt_agent}`. The docstring had promised "nothing but its
prompt". From the 0.163.0 source:

* **`features.unified_exec=false` is ignored**: "Only managed requirements may
  disable the remaining unified-exec implementation"
  (`core/src/config/managed_features.rs:178-183`). `features list` reports it
  `true` under the overrides. It does not matter here: shell tools are added only
  when `shell_tool` is on (`core/src/tools/spec_plan.rs:1245-1256`), and
  `shell_tool=false` is honoured. No shell, no file read.
* **`exec`/`wait` are code mode's tools.** The tool mode comes from the model's
  own metadata (`model_info.tool_mode`, `core/src/tools/mod.rs:63-73`) before
  any feature. They call the turn's other tools, which have no shell, MCP or
  connector.
* **Sub-agents come from the model's metadata too.** `multi_agent_version` is
  overridden only by `features.multi_agent_v2` or `[agents] enabled = false`
  (`core/src/config/mod.rs:1637-1664`), so `features.multi_agent=false` no
  longer removes them. A sub-agent's config is a clone of the turn's: same
  features, cwd, approval policy and permission-profile snapshot
  (`core/src/agent/child_config.rs:132-202`), and a role can only turn features
  off (`core/src/agent/role.rs:91-103`). So a sub-agent stays inside the same
  read boundary. It costs extra requests; it does not widen what can be read.

So the read boundary holds, and the label is now honest (commit `44a48e326`).
I did **not** add `-c agents.enabled=false`. In the June-era CLI, `[agents]`
flattens unknown keys into role tables (`codex-rs/config/src/config_toml.rs:659-688`
at `c955f73078`), so that override would be read as a role named `enabled`.
That would make the config fail to load: exactly the class of breakage this
stage fixes, on older CLIs. See open question 1.

## 8. Which `codex` the desktop app runs

From the code; the owner's config was not read.

1. The Tauri shell starts the sidecar with the app's own environment (only
   `PYTHONPATH` is set; nothing is cleared:
   `apps/learnloop-tauri/src-tauri/src/sidecar.rs` `launch`). The interpreter is
   the first that starts of `LEARNLOOP_PYTHON`, the active
   `VIRTUAL_ENV`/`CONDA_PREFIX` python, `uv run python` (when `uv.lock` exists),
   the repo `.venv` python, `python3`, `python` (`sidecar_command_specs`).
2. In the sidecar, a Codex profile (`codex_low`, `codex_medium`, ...) resolves
   the CLI in this order (`SdkCodexClient._codex_command` for the launch check,
   `_resolved_sdk_codex_bin` and the SDK for the app server; the two agree):
   `sdk_launch_command` (its argv before `app-server`), else `sdk_codex_bin`,
   else the SDK's pinned runtime `codex_cli_bin.bundled_codex_path()` when the
   `openai-codex-cli-bin` package is importable in the sidecar's interpreter,
   else `shutil.which("codex")` on the inherited `PATH`.
3. The default profiles leave `sdk_codex_bin` and `sdk_launch_command` empty
   (`src/learnloop/config/template.py:546,619`; the effective config of the
   probability copy shows both unset). `openai-codex-cli-bin` is not installed in
   the repo `.venv`, and `which -a codex` finds only `/usr/bin/codex`
   (codex-cli 0.163.0).

So, by default, the desktop app runs the same `/usr/bin/codex` 0.163.0 that
failed. It would run a different binary only if the owner's vault or global
config sets `sdk_codex_bin`/`sdk_launch_command`, the app's `PATH` puts another
`codex` first, or the chosen interpreter has `openai-codex-cli-bin`. Whichever
it resolves, the launch check runs that same binary.

Impact on the owner's grading: the practice door grades in an isolated turn
only in a vault whose algorithm version has the Slice 1 split (mvp-0.10 and
later). This worktree's tracked `fixtures/probability` is mvp-0.8, which grades
jointly and was not isolated, so it was not affected. The owner's live vault
configs differ from the tracked ones (they are modified in the main checkout),
so their versions are unknown here. Every isolated judge, diagnosis and PF call
was affected regardless of vault version.

## 9. Gate (on the commit that adds this review)

See the stage result for the exact counts. Commands:
`uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`;
`uv run lint-imports --no-cache` (22 kept, 0 broken);
`TMPDIR=fixtures-local/tmp flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto`;
`flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability`.
Frontend, `src-tauri`, schema, CLI help and RPC pins are unchanged, so their
gates do not apply.

**Process note.** While restarting my full-suite run I killed PID 2693278. It
was the merge4 stage's `flock` wrapper for its own full suite (cwd
`learnanything-merge4`, the same command line as my stopped run), which I took
for my run's orphan. Its pytest child kept running and holding the lock. But
merge4's gate wrapper will have seen `flock` exit on SIGTERM (143), so merge4's
full-suite result from that run should be treated as void and rerun.

## 10. Open questions

1. **Sub-agents and code mode in isolated turns (0.163.0).** They stay inside
   the read boundary (section 7), but a "tools off" turn can still spawn
   sub-agents. Should a follow-up add `[agents] enabled = false`, guarded by a
   probe that keeps it only on CLIs that accept it (older ones read it as a
   role)? Recommended: yes, as its own small stage, verified live.
2. **Selected plugin roots** register MCP servers even with
   `features.plugins=false` (`core/src/mcp.rs:254-290`). LearnLoop never selects
   capability roots, so this cannot happen today. If it ever does, the
   `mcp list` check would not see those servers.
3. **SDK checkout age.** The SDK in `~/Documents/thinking/codex` is from
   2026-06-02 while the CLI is 0.163.0 (2026-10-15). It still drives the app
   server correctly (calls 2 to 4). Updating it is the owner's call.

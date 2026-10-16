# Codex review of codex-isolation-app-servers: fixes

Stage `codex-isolation-app-servers`, branch `fix/codex-isolation-app-servers`,
worktree `learnanything-codex-sandbox`, from main `495c7437f` (mvp-0.25,
migrations to 206). The stage itself is recorded in
`docs/reviews/codex-isolation-app-servers.md`. The Codex review
(job `20261016-013438-p7jJLD`) reviewed the stage tip `d14c48bb6` and found
two High findings and one Medium. All three reproduced, fail first, and are
fixed in `08da634f5`.

Owner decisions in force (2026-10-12): the recommended defaults recorded in each
spec are accepted; Codex on the ChatGPT subscription may run every paid LLM role,
with cost estimated from token usage; frictionless defaults (honest labels,
generous defaults, live changes behind kill switches). This is still a transport
fix only. It adds no algorithm successor (replay reads none of it) and changes
no schema, CLI, RPC or frontend.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Host-disabled MCP servers can become enabled inside bubblewrap | fixed | `08da634f5` | `test_the_installed_codex_pins_a_server_only_an_unseen_ancestor_project_disables` (installed binary + bubblewrap), `test_the_check_runs_inside_the_sandbox_in_the_turns_own_directory`, `test_a_check_the_sandbox_refuses_refuses_the_turn`, `test_the_old_cli_shape_still_disables_config_servers_by_name` (now expects the already-off server pinned) |
| F2 | High | Launch verification ignores configuration flags after `app-server` | fixed | `08da634f5` | `test_configuration_flags_after_app_server_are_checked_and_launched_as_one_set`, `test_a_feature_toggle_that_turns_an_isolation_feature_back_on_refuses_the_turn` (3), `test_an_argument_after_app_server_the_check_cannot_read_refuses_the_turn` (4); `test_the_app_servers_own_arguments_stay_after_it` (5) guards the arguments that stay |
| F3 | Medium | Additional probes run outside the request deadline and cancellation | fixed | `08da634f5` | `test_the_check_runs_inside_the_request_deadline`, `test_the_turn_gets_only_what_the_check_left_of_the_deadline`, `test_an_interrupt_during_the_check_stops_it_and_nothing_launches`, `test_an_interrupt_stops_a_check_running_inside_the_sandbox` |

**Fail first.** All tests are in `tests/test_codex_isolation_mcp_check.py`,
which grew from 21 to 41 tests. With `src/learnloop/ai/providers/codex.py` and
`src/learnloop/ai/isolation.py` put back to the stage tip (`git show HEAD:...`,
with the fixed files copied aside and restored, `cmp`-checked), the final test
file gives **16 failed, 25 passed**. The 16 are every F1, F2 and F3 test in the
table except `test_the_app_servers_own_arguments_stay_after_it`, which passes
on both trees by design. Each failed for the reason it was written for:

* **F1:** the overrides held no `mcp_servers.fsserver.enabled=false` (and no pin
  for `docs`, which was already off). With bubblewrap unavailable, the old probes
  had already run on the host.
* **F2:** the launched app server reported `cua_repl` and `node_repl` on.
  `--enable`, `--remote-control`, `proxy` and a bare `--listen` all launched.
* **F3:** a hanging probe ran its full 8 s cap and raised `CodexUnavailable`, not
  `CodexTurnTimeout`. A turn of 1.0 s still finished within a 1.6 s deadline after
  1 s of probes. An interrupt took about 12 s to stop the check.

## F1: the check now sees what the sandboxed app server sees

**Reproduced on the installed binary** (codex-cli 0.163.0, throwaway
`CODEX_HOME`, no model call). The user config defines `fsserver` (enabled) and
trusts a project. That project's `.codex/config.toml` sets `enabled = false`, and
the sandbox's working directory lies inside the project:

| Where `codex mcp list --json` runs | Result |
|---|---|
| host, in the turn's directory | `fsserver` **false** (the trusted ancestor's layer applies) |
| inside bubblewrap, same directory | `fsserver` **true** (the ancestor is not mounted, so its layer is absent) |
| stage tip: overrides verified on the host, listed inside bubblewrap | `fsserver` **true**: the host check saw it off, so it added no pin |

Why the views differ, from the 0.163.0 source: project layers are discovered
from the cwd up to the project root, trusted ones only
(`config/src/loader/local.rs:142-183`). The app server loads a thread's config
with the thread's cwd (`app-server/src/request_processors/thread_processor.rs:1354-1357`).
Bubblewrap mounts only the working directory, the system trees and the private
home's `config.toml`/`auth.json`, so a project file above the working
directory is gone inside it.

**Fix** (`_verified_isolated_overrides`, `_codex_probe`):

1. Under `tool_isolation` (project routes) every probe runs **inside the same
   bubblewrap sandbox** as the app server: same isolation, same agent home,
   same executable. It starts in the turn's own directory, as the thread does.
   `sandboxed_command`/`sandbox_arguments` in `src/learnloop/ai/isolation.py`
   take an optional `chdir`. It must be the working directory or inside it, or
   the sandbox refuses. The state-location check reads the project files from
   that start directory up, and resolves relative `-c` values against it. When
   bubblewrap is unavailable, the probe refuses before anything runs, so a
   probe never falls back to the host.
2. **Every server still listed** under the isolation features is pinned off by
   name, **already-disabled ones too**. A listed server is a config one, since
   `features.plugins=false` has removed the plugin ones, so the name override is
   valid. This restores the earlier rule that every listed server is disabled,
   without the plugin servers that broke it.
3. Residual: a dotted name cannot be addressed. If it is enabled, the turn is
   refused (as before). If it is already off in the configuration the launch
   loads, it is left that way: the probe now runs in that same configuration.

Outside a sandbox nothing changes about where the check runs. Probe and app
server both run on the host, in the turn's directory, with this process's
environment.

## F2: the launch command's configuration options are one set

**Reproduced on the installed binary** (`codex ... features list`, throwaway
`CODEX_HOME`, no model call):

| Command | `apps` |
|---|---|
| `-c features.apps=false features list` | false |
| `-c features.apps=false features list --enable apps` | **true** |
| `--enable apps -c features.apps=false features list` | **true** |
| `-c features.apps=false features list -c features.apps=true` | **true** |
| `-c features.apps=true features list -c features.apps=false` | false |
| `-c features.apps=false features list --disable apps --enable apps` | false |

The source agrees. `-c`/`--config` is a global, appending clap option
(`utils/cli/src/config_override.rs:29-36`), so it is read after the subcommand
too, and a later `-c` wins. `--enable`/`--disable` are global
(`cli/src/main.rs:952-960`). They are folded in as `features.<name>=true` and
then `=false` overrides **after** every `-c` (`cli/src/main.rs:977-988`,
`:1062-1063`), wherever they stand. The app server is started with those root
overrides (`cli/src/main.rs:1237-1290`). `app-server`'s own options are
`--strict-config`, `--listen`, `--stdio`, the hidden `--remote-control` and
`--managed-daemon`, `--analytics-default-enabled`, the websocket auth and
code-mode host options, and its tooling subcommands (`cli/src/main.rs:571-640`: the struct ends at 623, the subcommands follow).

**Fix** (`_isolated_launch_parts`, `_reenabled_isolation_features`):

* For an isolated turn, every `-c`/`--config`, `--enable` and `--disable` written
  after `app-server` is moved in front of the turn's overrides. All forms clap
  accepts are read: `-c V`, `-cV`, `-c=V`, `--config V`, `--config=V`, and the same
  for the toggles. The probes run `command + overrides + <subcommand>` and the
  app server starts as `command + overrides + app-server + <its own options>`.
  `command` is the argv before `app-server` plus the moved options, so verification
  and launch use one configuration, and every `-c` of the user's comes before the
  turn's.
* `--enable F` anywhere in the launch command, where `F` is a feature the turn
  turns off, refuses the turn. A toggle applies after every `-c`, so it cannot
  be reordered.
* After `app-server` only `--listen` (with its value), `--stdio`,
  `--strict-config` and `--analytics-default-enabled` stay. Anything else
  refuses the turn, naming the argument: a subcommand, `--remote-control`,
  an option with an unexpected `=value`, an option missing its value, or an
  unknown option.

Residual (noted, not changed): TUI options written **before** `app-server`
reach the probes but not the app server. One is `-p/--profile`: `mcp list`
layers `$CODEX_HOME/<name>.config.toml` (`cli/src/main.rs:1196-1198`), while the
app server starts with `LoaderOverrides::default()` (`:1284`). So the check can
see more than the launch, never less. A profile that disables a server is
pinned like any listed server. A profile that defines a new server gets a pin
the launch rejects (`invalid transport`), which fails closed at launch.
`sdk_launch_command` is empty by default.

## F3: the check runs inside the request's deadline and stops on interrupt

**Fix** (`_Deadline`, `_raise_if_stopped`, `_codex_probe`, `interrupt`):

* `_run_sdk_turn` sets one deadline (the request's timeout) before the launch
  check. Each probe gets what is left of it, at most `_CODEX_PROBE_TIMEOUT_SECONDS`
  (60 s). A probe that the request deadline ends raises
  `CodexTurnTimeout("... deadline in the isolated turn's launch check (...)")`.
  One that hits the 60 s cap still refuses with `CodexUnavailable` ("did not
  finish"). The turn's timer is set to what the deadline leaves, not the full
  timeout again.
* Probes run as `Popen` in their own session. `interrupt()` kills the running
  probe's process group (under bubblewrap that is `bwrap`, and
  `--die-with-parent` takes the sandboxed `codex` with it). Interrupts and the
  deadline are checked before each probe, after each probe and before launch,
  so an interrupted check launches nothing.

Residual (pre-existing, not widened): the turn's timer is still armed after
`thread.turn(...)`. App server startup and `thread_start` count against the
deadline now, but a hang inside them is not interrupted by it.

## Claims in the stage review that did not hold

The Codex review flagged three statements in `docs/reviews/codex-isolation-app-servers.md`
section 4. Each is now marked there as corrected, pointing here:

* "The check, on the exact launch set": the launch command's own options after
  `app-server` were not in the probes (F2). They are now.
* "[The sandboxed app server] can load no more than was checked": losing a
  configuration layer can turn a server back on (F1). The check now runs in the
  sandbox.
* "Nothing was loosened": the stage stopped pinning already-disabled servers
  (F1). It pins them again.

## Live verification (Codex subscription; calls 5 and 6 of the 6 allowed)

A driver in the session scratchpad ran `SdkCodexClient` with the real SDK from
the checkout (`gpt-5.6-sol`, effort low) in scratch directories under this
worktree's `fixtures-local/tmp`, with no vault content. It recorded only server
names, enabled state, feature states, turn item types and usage. No config,
auth or credential file was read.

**No-call check first** (`mcp list` / `features list` only, owner's setup):

| Where | Check time | Listed under the isolation features | Pinned | Launch set |
|---|---|---|---|---|
| host | 0.69 s | `node_repl` on, `openaiDeveloperDocs` on | both | both off; `apps`, `plugins`, `shell_tool` false |
| inside bubblewrap | 0.54 s | `node_repl` on, `openaiDeveloperDocs` on | both | both off; `apps`, `plugins`, `shell_tool` false |

**Live turns** (`isolated=True`, shell off, prompt asks for `{"reply": "pong"}`):

| # | Where | Result | Items | Tokens (input / output) |
|---|---|---|---|---|
| 5 | host | `{"reply":"pong"}` in 6.3 s | `userMessage`, `agentMessage` | 10,699 / 15 |
| 6 | inside bubblewrap (`tool_isolation`, the path F1 changed) | `{"reply":"pong"}` in 5.2 s | `userMessage`, `agentMessage` | 9,043 / 15 |

Totals for this fix step: 2 calls, 19,742 input and 30 output tokens on the
subscription (cost estimated from token usage). The stage, all steps: 6 calls
(the 6 allowed), 71,168 input and 1,231 output tokens. No OpenRouter or other
paid call was made. No tracked fixture was opened or changed.

## Gate (on `08da634f5`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `TMPDIR=fixtures-local/tmp flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12024 passed, 2 xfailed**, 0 failed, 0 skipped (17:13) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 11920 deselected (1:52) |
| `git diff --check` | clean |

The full suite includes `tests/test_coordinated_migrations.py` (green). Frontend,
`src-tauri`, schema, references, snapshots, CLI help and RPC pins are unchanged,
so their gates do not apply. The tracked fixtures are unchanged (`git status`
shows only this review and the stage review's correction note). The full suite
waited for the lock behind the merge4 stage's run, and no other stage's process
was touched.

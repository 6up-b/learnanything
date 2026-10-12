# fix-codex-sandbox: Codex review fixes

**Branch:** `fix/codex-sandbox`, on top of `a3212fab` (the stage review).
**Review:** codex-job `20261012-030026-DKJ7yD`, 2 findings (1 High, 1 Medium).
**Scope:** `src/learnloop/ai/isolation.py` and `tests/test_ai_tool_isolation.py`. The
Codex provider, the project runtime, config, schema and frontend are unchanged.
**Kill switch:** unchanged. `project.require_tool_isolation = true` still refuses an agent
that can't be confined, and a refused layout fails the call before launch.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | A later working-directory mount can expose the private agent home | **fixed** | `e4a5a7b6` | `test_a_working_directory_that_holds_the_agent_home_is_refused[workdir/.codex, workdir]`, `test_an_executable_package_that_holds_the_agent_home_is_refused`, `test_codex_refuses_a_working_directory_that_holds_its_home[sdk_codex_bin, sdk_launch_command]` |
| F2 | Medium | Configured SQLite paths bypass the private-home guarantee | **fixed** | `e4a5a7b6` | `test_inherited_state_locations_are_pinned_to_the_private_home` (6 params), `test_a_configured_sqlite_home_outside_the_private_home_is_refused` (4), `test_a_configured_sqlite_home_inside_the_private_home_runs_privately` (3), `test_every_config_layer_that_moves_the_state_databases_is_checked` (5), `test_command_line_overrides_of_the_state_databases_are_parsed_like_codex`, `test_a_config_file_tomllib_cannot_parse_is_refused_only_when_it_names_the_setting`, `test_the_sandbox_pins_the_agent_home_and_state_locations` |

Both findings reproduced before the fix. No finding was rejected.

## F1: a later mount uncovered the private home

### Reproduction (at `a3212fab`)

`sandbox_arguments` mounts the in-memory agent home, then binds the executable's package
(read-only) and the working directory (read-write) on top. Either one that contains the home
replaces it with the host's.

- **Working directory holds the home.** Synthetic files under real bubblewrap:
  `workdir=S/work`, `home=S/work/.codex` holding `history.jsonl` and `installation_id`.
  The sandboxed `sh` printed `HOST HISTORY` and rewrote the host's `installation_id` to
  `SANDBOX-ID` (rc 0).
- **Executable package holds the home.** A Node launcher package `S/pkg` (with
  `package.json`) and `home=S/pkg/home`. The launcher read the host's `history.jsonl`
  through the read-only package bind.
- **Through the provider.** `CodexSDKProviderClient._run_structured` with `CODEX_HOME`
  inside the isolation working directory. The Codex-like fake printed
  `seen-id:HOST-INSTALLATION-ID` and `seen-history:AGENT HISTORY`.

The new tests fail at `a3212fab` with exactly these outputs.

### Fix

`_refuse_if_it_covers_the_home` runs before each bind that follows the home tmpfs: the
working directory and any executable package outside the system trees. If the bind contains
the home (its lexical or resolved path), the layout is refused with `ToolIsolationUnavailable`:

> the working directory /…/work contains the agent home (/…/work/.codex); it is mounted after
> the private in-memory home, so the agent would see and write the host's home (its history,
> transcripts and installation_id); use a working directory and an agent executable that do
> not contain the agent home

A refusal was chosen over reordering the mounts. Reordering would leave the host's home
inside the agent's working directory, and bwrap would create missing mount points on the
host. A home that contains the working directory or the executable stays allowed: the bind
then shows only that directory or file inside the private home.

The system trees are bound *before* the home tmpfs, so a home under `/opt` or `/usr` is
still covered by the tmpfs. The single-file executable bind cannot contain a directory.

The bwrap test probe used `/` as its working directory, which contains every home; it now
uses a temporary directory. `test_a_hidden_path_inside_the_working_directory_is_masked` put
its home inside the working directory; its layout now keeps them apart.

## F2: settings and environment moved the state out of the home

### Reproduction (at `a3212fab`)

These were credential-free real Codex 0.161 startups. Each used a synthetic `CODEX_HOME` with
no `auth.json`, ran the real sandboxed `codex app-server`, sent `initialize` (plus
`thread/start` where noted), then closed stdin. No turn was started and no model request was
sent.

| Case | Result at `a3212fab` |
|---|---|
| default layout | rc 0; host working directory and home empty after exit |
| `CODEX_SQLITE_HOME=.` | rc 0; **host working directory kept** `state_5`, `logs_2`, `goals_1`, `memories_1`, `queue_1` `.sqlite` files with `-wal`/`-shm` |
| `sqlite_home = "/opt/review-state"` in `config.toml` | rc 1, `Error: failed to initialize sqlite state runtime under /opt/review-state` |
| `sqlite_home = "<workdir>"` in `config.toml` | rc 0; **15 database files** left in the host working directory |
| `sqlite_home = "."` in `config.toml` | rc 0; private. Codex resolves it against the file's directory, which is the home |
| `CODEX_ROLLOUT_TRACE_ROOT=.` (+ `thread/start`) | rc 0; **a `trace-*` bundle** (`manifest.json`, `trace.jsonl`, `payloads/*.json`) left in the host working directory |
| `log_dir = "<workdir>/logs"` (+ `thread/start`) | rc 0; nothing written. The app-server does not use `log_dir` (TUI and login only) |

The trace root is the same class of leak as `CODEX_SQLITE_HOME`. It was found while checking
which environment variables Codex 0.161 reads (`CODEX_*` names in the native binary), so it
is fixed here too.

Codex's precedence comes from `core/src/config/mod.rs` in the local source checkout, and the
startups above confirm it. `sqlite_home` comes from the merged config layers first, then
`$CODEX_SQLITE_HOME` (relative to the working directory), then `$CODEX_HOME`. The layers are,
in order:

1. `/etc/codex/config.toml`
2. `$CODEX_HOME/config.toml`
3. project `.codex/config.toml` files in the working directory and its parents
4. `-c` overrides, with relative paths resolved against the working directory
5. `/etc/codex/managed_config.toml`, on top of everything

### Fix

- **Environment, pinned.** The sandbox gets `--setenv CODEX_HOME <home>`,
  `--setenv CODEX_SQLITE_HOME <home>` and `--unsetenv CODEX_ROLLOUT_TRACE_ROOT`. The home is
  made absolute first, so the tmpfs and the agent's `$CODEX_HOME` are one path even when the
  host's `CODEX_HOME` is relative.
- **Configuration, checked before launch.** A config layer outranks the environment, and it
  is read from a file the sandbox cannot rewrite. `_refuse_state_outside_the_home` therefore
  reads `sqlite_home` from every layer the agent sees:
  - the system and legacy managed files;
  - the user file bound into the home;
  - `config.toml` in the working directory;
  - `.codex/config.toml` in the working directory and in any parent inside a mounted tree;
  - `-c`/`--config` overrides in the launch command, parsed as Codex parses them: split on the
    first `=`, the value as TOML, else as a bare string.

  It resolves each value as Codex does and refuses the launch if the result is not inside the
  private home:

  > the agent's sqlite_home in /…/home/config.toml puts its run state at /opt/review-state,
  > outside its private in-memory home (/…/home); only that home is private by construction
  > (in the working directory the state would reach the host, on a read-only mount the agent
  > would not start); remove the setting or point it inside /…/home
- **Unparseable files.** Python's `tomllib` reads TOML 1.0, and Codex's parser also accepts
  TOML 1.1. A file `tomllib` cannot parse is refused only when it names the setting. Without
  the setting, it cannot move the databases.

The rule is strict. Some locations outside the home would also be private (the sandbox's
root tmpfs, for example), but only the home is private *by construction*, so those are
refused too. The owner's real `~/.codex/config.toml` parses with `tomllib` and sets neither
`sqlite_home` nor `log_dir`. The check printed only those booleans, no contents. Neither
`CODEX_SQLITE_HOME` nor `CODEX_ROLLOUT_TRACE_ROOT` is set in the owner's environment. The
owner's current setup is therefore unaffected.

`log_dir` is not checked: the app-server doesn't write there (see the table above).

### After the fix (same credential-free startups, `e4a5a7b6`)

| Case | Result |
|---|---|
| default layout | rc 0, `initialize` OK; host working directory and home empty |
| `CODEX_SQLITE_HOME=.` | rc 0, `initialize` OK; host working directory **empty** |
| `sqlite_home = "/opt/review-state"` | **refused before launch** with the message above |
| `sqlite_home = "<workdir>"` | **refused before launch** |
| `sqlite_home = "."` | rc 0; host working directory empty |
| `CODEX_ROLLOUT_TRACE_ROOT=.` (+ `thread/start`) | rc 0; host working directory **empty** |
| default + `thread/start` | rc 0; host working directory empty |
| F1 layouts (`sh` and Node launcher) | **refused before launch** |

A proof against the owner's real agent home followed. The real sandboxed `codex app-server`
started with `home=~/.codex`, which binds `auth.json` and `config.toml` back by path. It ran
`initialize` and `thread/start`, with no turn and no model request. Both returned OK (rc 0).
The pinned variables were `CODEX_HOME`, `CODEX_SQLITE_HOME`, `CODEX_ROLLOUT_TRACE_ROOT` and
`TMPDIR`. The host working directory was empty after exit. No top-level entry of the host's
`~/.codex` was created or modified, judged by name and mtime only. No credential file was
read.

## Claims corrected

- **"None of [the run state] reaches the host."** Now true for every layout the sandbox
  launches: the environment is pinned, and the layouts and settings that broke it are
  refused. The module docstring states the conditions.
- **"Each isolated launch creates a fresh id in its private home."** Now true: a mount that
  would cover the home is refused.
- **"The fake writes everywhere the real app-server does."** The fake now also follows
  `sqlite_home`, `$CODEX_SQLITE_HOME` and `$CODEX_ROLLOUT_TRACE_ROOT` as Codex does. It
  prints the history it can see. The private-home test now requires the working directory to
  hold only the agent's answer.

## Calls and cost

- **Real Codex app-server launches:** 14. Of these, 13 used synthetic, credential-free homes
  (8 before the fix, 5 after) and 1 used the owner's real home, `initialize` and
  `thread/start` only.
- **Model requests:** 0. No turn was started, so there were no tokens and no spend; the
  subscription estimate is $0.
- **OpenRouter:** no calls.
- **Vaults:** none touched. All files were synthetic, in temporary directories.

## Gate results

Run at `e4a5a7b6`. The commit that adds this file changes only this file.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | OK (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **8 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6,371 passed**, 0 failed, 0 skipped, 14 warnings (128.3 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **63 passed**, 6,308 deselected (26.0 s) |
| `tests/test_ai_tool_isolation.py --durable-sqlite` | **50 passed**, none skipped: bubblewrap ran for real (24 before, 26 new) |
| Tests matching `isolation`, `codex` or `project` (`-k`) | **636 passed** |
| Frontend | not touched, not run |
| DB reference scripts | schema not touched, not run |

## Residual limits

1. **Wrappers inside `sdk_launch_command`.** The owner can write a launch command that sets
   variables itself, for example `env CODEX_SQLITE_HOME=. codex app-server`, or one that wraps
   Codex in another program. Those run inside the sandbox after the pinning, and the isolation
   can't see into them. `-c` overrides in the command are checked. The launch command is the
   owner's own configuration, not the agent's.
2. **Arguments the SDK appends** to a `write_launcher` program aren't known when the launcher
   is written, so a `-c` among them isn't checked. LearnLoop's Codex client passes no
   `config_overrides`; the SDK appends only `app-server --listen stdio://`. The
   `write_launcher` docstring says so.
3. **Newer Codex versions** may add settings or variables that move run state. The constants
   `AGENT_ENV_PINNED_TO_HOME`, `AGENT_ENV_UNSET`, `AGENT_STATE_SETTINGS` and
   `AGENT_SYSTEM_CONFIG` list the ones Codex 0.161 has, so a new one is a one-line addition.
   The stage review's open questions 1 and 2 still apply here. A readiness-time startup probe
   would catch a new failure mode before a paid sweep.

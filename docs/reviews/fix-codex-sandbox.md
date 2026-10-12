# fix-codex-sandbox: Codex could not start inside the tool-isolation sandbox

**Branch:** `fix/codex-sandbox`, from `main` at `5f1c4515`.
**Scope:** `src/learnloop/ai/isolation.py` and its tests. The Codex provider is unchanged.
**Migration / schema / config / frontend:** none.
**Kill switch:** unchanged. `project.require_tool_isolation = true` still refuses an
agent that can't be confined.

## Symptom (live run, 2026-10-12)

`learnloop project sweep` ran on a `fixtures-local` vault copy with an enrolled scratch
repo. Every diff then failed with:

```
AIProviderUnavailable: Codex process closed stdout. stderr_tail=Error: Read-only file system (os error 30)
```

Readiness said every project route (`codex_low`, `codex_sdk`, `gpt-5.6-sol`) was ready
with `tool_isolation=bubblewrap` and "Codex runtime is ready".

## Reproduction

1. **Setup.** A scratch repo `fixtures-local/scratch-repo` had one commit: `ellipse.py`,
   20 added lines, with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
   `fixtures/conic-sections` was copied to `fixtures-local/conic-sandbox` with
   `learnloop.db.copies.copy_tree_with_databases`.
2. **Enroll.** `uv run learnloop project enroll fixtures-local/scratch-repo --vault fixtures-local/conic-sandbox`
   captured 1 diff.
3. **Dry run.** `project sweep --dry-run --json` estimated 1 diff, 3 calls,
   28,141 tokens and $0.28 at the subscription reference rate.
4. **Sweep at `5f1c4515`.** `project sweep --json` failed in 0.98 s with the exact
   live error. The diff stayed `pending`. No model request was sent: the app-server
   died before `initialize`.
5. **By hand.** Running the sandboxed command from `sandboxed_command(...)` and sending
   one `initialize` gave rc 1 and `Error: Read-only file system (os error 30)`. Neither
   `RUST_LOG=trace` nor `RUST_BACKTRACE` gave anything more, and the host has no strace.

## Root cause

Bisected by hand with the same bwrap arguments, varying only the binds into the agent
home:

| Case | Agent-home binds | Result |
|---|---|---|
| A | `auth.json` (rw) only | `initialize` OK; Codex creates a fresh `installation_id` |
| B | A + `config.toml` (ro) | `initialize` OK |
| C | A + `installation_id` (ro) | **`Error: Read-only file system (os error 30)`** |
| D | A + `installation_id` (rw) | `initialize` OK, using the host's id |
| E | `sh`: `exec 3<>` on a ro-bound file | `Read-only file system` |

Inside the sandbox, bubblewrap 0.13's root, `/tmp` and the agent-home tmpfs are all
writable. Only bind mounts are read-only.

Codex 0.161 opens `$CODEX_HOME/installation_id` read-write at startup, even when the
file exists. The source is `core/src/installation_id.rs`. Codex locks the file, then
sends the id as `x-codex-installation-id`. M1 bound that file read-only, so the open
failed with `EROFS` and the app-server exited before its first request.

The fake agents in the M1 tests never opened that file for writing, so they missed it.
Readiness never starts the sandboxed app-server, so it missed it too.

## What the real app-server writes (observed live, inside the fixed sandbox)

A wrapper `sdk_codex_bin` recorded the private home and `/tmp` from inside the sandbox
every 0.3 s, then exec'd `/usr/bin/codex`. It ran through the real
`CodexSDKProviderClient` launch path under `tool_isolation`, with one real turn on
`codex_low`.

In `~/.codex`, all of it in the private tmpfs:

- `installation_id`;
- the state, log, goal, memory, queue and thread-history databases: `state_5`, `logs_2`,
  `goals_1`, `memories_1`, `queue_1` and `thread_history_1` `.sqlite` files, each with
  `-wal` and `-shm`;
- `sessions/2026/10/12/rollout-*.jsonl`;
- `shell_snapshots/*.sh`;
- lock files: `thread-writer-locks/*.lock`, `mcp-oauth-locks/file-store.lock`;
- caches: `models_cache.json`, `cache/codex_apps_server_info/*.json`,
  `cache/codex_apps_tools/*.json`, and the account's remote plugins (`plugins/cache/...`,
  about 480 files, including one created by the owner);
- system skills (`skills/.system/...`, about 70 files);
- `tmp/arg0/codex-arg0*/` helpers (`codex-linux-sandbox`, `apply_patch`, `.lock`);
- `.sandbox_migration`.

Elsewhere:

- **`/tmp`:** nothing of Codex's. Only the working directory and the skeleton leading to
  the wrapper file bound for this probe.
- **`/`:** only the standard mount points.
- **Bound host files:** `config.toml` was only read. `auth.json` had no refresh due.

## Fix (`4d22344f`)

`AGENT_HOME_READ_ONLY` is now `("config.toml",)`. `installation_id` is no longer bound
back. Codex creates a fresh id in the private in-memory home, next to the rest of its run
state, and all of it is discarded at exit. The module docstring now lists the private,
writable, discarded state. It also states the rule: a host file is bound back only in a
mode the agent can open it with.

Alternatives rejected:

- **A writable bind of `installation_id`.** This would let the sandboxed agent write a host
  file that the owner's own Codex reads and sends with its requests. The regression test
  fails on this variant.
- **A private copy of the host id.** bwrap `--file FD` could do it in the shell-launcher
  path. The `sdk_launch_command` path is an argv the SDK spawns, so it can't pass an fd,
  and the two paths would differ. The id is analytics metadata, not a credential, and the
  account token identifies the owner anyway. See open question 3.

### Guarantees kept

These are unchanged and still pass on real bubblewrap in `tests/test_ai_tool_isolation.py`:

- **Unreadable:** the project store, `state.sqlite`, a repo file, the agent's session
  transcripts and `history.jsonl`. Covered by `test_out_of_scope_reads_fail[...]` (5
  params) and by `test_the_codex_app_server_launches_inside_the_sandbox`, which also shows
  that the same launch *can* read them without isolation.
- **No host processes**, and only the mount skeleton is visible.
- **Bound back:** only `auth.json` (rw) and `config.toml` (ro).
- **Refusal:** without bubblewrap, for an unconfinable agent, and when a hidden path holds
  the executable, the working directory or the agent home.
- **Hidden paths masked** inside mounted packages and the working directory.

Live check, after all the real turns below:

- None of the 4 host session rollouts modified in the last hour names a LearnLoop project
  purpose (`grep -l` count 0). Those rollouts belong to other Codex sessions.
- No top-level entry in the host's `~/.codex` was modified after the scratch commit.

The check counted file names only and printed no contents.

### Regression test

`test_the_app_server_keeps_its_run_state_in_a_private_home[sdk_codex_bin | sdk_launch_command]`
runs the real launch path: `CodexSDKProviderClient._run_structured` under `tool_isolation`,
then `_isolated_launch`, then `write_launcher` or `sandboxed_command`, then bwrap. Its fake
app-server writes everywhere the real one does:

- an `O_RDWR|O_CREAT` open of `installation_id`;
- the six databases with `-wal` and `-shm`;
- a session rollout, shell snapshot, locks, caches, system skills and `tmp/arg0`;
- `$TMPDIR`;
- an in-place `auth.json` refresh.

It also checks that `config.toml` is readable but not writable, and that it can write to
the working directory.

The test asserts that:

- the process exits 0;
- the host id is not visible;
- the host home is unchanged except for the refreshed `auth.json`;
- the vault and repo trees are unchanged;
- nothing reaches the host `/tmp`;
- the working-directory output persists.

`install_fake_codex_sdk(spawn=True)` now also records the spawned return code.

Results:

- **At `5f1c4515`:** both params fail with `Error: installation_id: Read-only file system (os error 30)`.
- **With a writable bind:** both fail, because `seen-id:HOST-INSTALLATION-ID` reaches the
  sandbox.
- **With the fix:** both pass.

## End-to-end proof (real Codex, owner's ChatGPT subscription)

These are the same sweep commands on the same copy (`fixtures-local/conic-sandbox`). Cost
is estimated from token usage at the subscription reference rate the sweep reports
($10 per million tokens). The subscription is not billed per token.

| Run | Code | Command | Turns sent | Outcome | Tokens (in / out) | Est. USD |
|---|---|---|---|---|---|---|
| 1 | `5f1c4515` | `project sweep --json` | 0 | EROFS at launch: the live failure | none | 0 (tracker admitted 0.116) |
| 2 | fixed | `project sweep --json` | 1 | authoring rejected upstream: "Selected model is at capacity" | none reported | 0 (tracker admitted 0.116) |
| 3 | fixed | `project sweep --json` | 2 | authoring **completed**; closed-book rejected for capacity, diff `failed` | 15,428 / 1,653 | 0.171 |
| 4 | fixed | `project sweep --retry-failed --json` | 2 | closed-book **completed**, grading **completed**; status `complete` | 14,539 / 342 and 16,347 / 365 | 0.149 + 0.167 |

All four project receipts that reached the model record `tool_isolation: "bubblewrap"`, with
scopes `diff` (authoring), `questions_only` (closed-book) and `quoted_evidence` (grading).

**Questions generated:** 6 candidates on `ellipse.py`: 2 `what_does`, 3 `predict` and 1
`where_change`. The closed-book check answered 5 of them correctly without the diff, so
they were rejected as `rejected_generic`. That is the filter working on a toy diff whose
names give the answers away. One survivor was selected, a `what_does` question on how
`ellipse_eccentricity` normalizes and validates its inputs (closed-book score 0.85). The
diff is therefore `under_probed`: 1 of the 2 wanted.

The probe turns are separate from the sweep runs above. They ran on `codex_low` through
the provider directly:

- **Run a:** completed. Usage was not recorded; it was the same prompt as run c.
- **Run b:** rejected upstream for capacity.
- **Run c:** completed in 7.0 s, 13,930 / 15 tokens, $0.139.

**Totals:**

- **Requests sent to OpenAI:** 8 turns. 5 completed and 3 were rejected upstream for
  capacity before generating. The EROFS launch sent no request.
- **Tokens:** about 76.6k on completed turns. 62,619 were recorded (48,674 in the sweep
  and 13,945 in probe c), and probe a added an unrecorded ~14k.
- **Estimated subscription cost:** about $0.77, of which $0.487 was the sweep. The spend
  tracker's admitted estimates for the three failed project calls ($0.293) consumed no
  tokens.
- **OpenRouter:** no calls; embeddings were not enabled.

## Gate results

Run at `4d22344f`. The commit that adds this file changes only this file.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | OK (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **8 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6,345 passed**, 0 failed, 0 skipped, 14 warnings (167.5 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **63 passed**, 6,282 deselected (26.2 s) |
| `tests/test_ai_tool_isolation.py --durable-sqlite` | **24 passed**, none skipped: bubblewrap ran for real |
| Isolation, embedding-isolation, `test_project*`, `test_codex*`, `test_ai_provider*` | **481 passed** |
| Frontend | not touched, not run |
| DB reference scripts | schema not touched, not run |

## Files touched

- `src/learnloop/ai/isolation.py`: `installation_id` is no longer bound; the docstring
  lists the private run state and states the binding rule.
- `tests/test_ai_tool_isolation.py`: the regression test (2 params) and its
  Codex-like fake app-server.
- `tests/project_support.py`: `install_fake_codex_sdk(spawn=True)` records `returncode`.
- `docs/reviews/fix-codex-sandbox.md`: this file.

## Open questions

1. **Readiness doesn't start the sandboxed app-server.** "Codex runtime is ready" with
   `tool_isolation=bubblewrap` was reported while every launch failed. A startup probe
   could catch this class of failure before a paid sweep is admitted: spawn the sandboxed
   `app-server`, send `initialize`, close, with no model request. It takes under 1 s.
   That probe would live in the project readiness path, outside the isolation module, so
   it was not done here.
2. **The bubblewrap check doesn't try bubblewrap.** `isolation_unavailable_reason()`
   only checks that `bwrap` is on the PATH, not that it can create a namespace (Ubuntu's
   AppArmor user-namespace restriction, for example). Such a host still fails closed at
   launch, but readiness would again claim `bubblewrap`. A cached `bwrap ... true` probe,
   like the test suite's `_bwrap_works`, would make readiness honest.
3. **Installation id.** Each isolated launch now reports a fresh `installation_id`. If the
   owner wants isolated calls to carry the interactive id, the launcher path could seed
   a private copy with bwrap `--file`, and the `sdk_launch_command` path would keep a
   fresh id.
4. **Remote apps and plugins reach the sandboxed agent over the network.** On every
   launch, Codex fetched an app tool list (`cache/codex_apps_tools`) and the account's
   remote plugins into the private home. The plugins included one created by the owner;
   the files' contents were not read. The
   M1 sandbox deliberately leaves the network open for the model API. If the ChatGPT
   account has a connector to where the enrolled repos live (GitHub, for example), a
   closed-book or grading turn could in principle fetch the code through it. The scope
   promise covers the local filesystem only. To close this, isolated launches could
   disable apps, plugins and web search with Codex config overrides; this needs
   checking against Codex 0.161's flags. Every isolated launch also pays the plugin
   download, which is part of each call's latency.
5. **Capacity errors fail a diff.** `gpt-5.6-sol` returned "Selected model is at
   capacity" on 3 of 8 turns today. The second one moved the diff to `failed`, which then
   needed `--retry-failed`. Upstream capacity errors could be treated as transient: no
   attempt counted, or a fallback to `codex_medium`. Out of scope here.
6. **Spend reporting counts calls that never ran.** The sweep's
   `subscription_estimated_usd` includes the admission estimate for calls that failed
   before any request. In run 1, the sweep reported $0.116 although nothing was sent.
   The receipts are honest, with no tokens recorded, but the summary number is not.

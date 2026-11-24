# Notebook runtime B1–B3: the supervised sandboxed marimo server, the frame proxy and the RPCs

- **Base:** `ba7884c102` (origin/main, unchanged since the gate); branch `notebook/na0.2-sandboxed-server`, on top
  of the gate record (`docs/reviews/notebook-na0.2.md`). Date 2026-11-23.
- **Scope:** build steps B1 (runtime and supervisor), B2 (frame proxy) and B3 (RPCs, Rust passthroughs, typed
  client, the main window's `frame-src` entry) from the gate record, as product code. B4–B7 follow with frontend
  workers.
- **No migration:** a session is process state, not persisted meaning. No kill switch (nothing starts until a
  notebook is opened), no algorithm tag, no model call, no UI component.

## What was built

| Piece | Where | What it does |
|---|---|---|
| The shared sandbox profile | `learnloop/sandbox_profile.py` | The hardened bubblewrap profile, moved out of the Manim module unchanged (figures, the inspector, PF and declared-function checks keep their exact commands). Callers add their own mounts through `extra_args`. Standard library only |
| The marimo adapter | `notebook_runtime/adapter.py` | Every private marimo interface the runtime relies on, and the launcher that runs inside the sandbox (patches `uvicorn.Config` to bind the Unix socket, guarded for marimo's spawn kernel). `interface_problems()` checks the installed marimo still has each one |
| The launch | `notebook_runtime/sandbox.py` | The server's mounts on top of the profile, the scope, the environment |
| The supervisor | `notebook_runtime/supervisor.py` | One session's state machine: start, ready check over the socket, graceful and forced stop, crash restart with backoff, the real backend |
| The frame proxy | `notebook_runtime/proxy.py` | Per-session `127.0.0.1` port and secret path, Host and path checks, the frame's API allowlist, token injection, cookie stripping, skew-token rewrite, CSP, bridge injection, WebSocket relay, UI-value recording and replay |
| The runtime | `notebook_runtime/runtime.py` | Sessions per owner, scoped by vault and epoch, on an event-loop thread of its own; the session limit, idle stop and the run-directory bound |
| Named settings | `notebook_runtime/settings.py`, `NotebooksConfig` | Below |
| The RPCs | `learnloop_sidecar/handlers/notebooks.py` | `notebook.open`, `notebook.status`, `notebook.close`, `notebook.release`, `notebook.run_cells`; desktop only |
| The context | `learnloop_sidecar/context.py` | A vault switch stops the previous vault's sessions; `close` stops them all and the runtime's thread |
| Desktop bridge | `commands.rs`, `main.rs`, `client.ts`, `dto.ts`, `tauri.conf.json` | Five passthroughs, typed client calls and DTOs, `frame-src ... http://127.0.0.1:*` |

The gate's five design changes are all in: the hosts file (two lines of our own, bound read-only at `/etc/hosts`),
the guarded launcher, `OOMPolicy=continue` on the scope, the proxy's skew-token rewrite, and the frame's narrow
API allowlist with full edit rights only for the sidecar over the socket. (Fix round: that holds against the frame,
not against the notebook's own code. That code runs in marimo's kernel beside the server, in the same sandbox as the
same user, so it can read the token and enable or run any of its own cells; see NBF-16.)

## The contract as built

**`notebook.open {owner, path, view?}`.** `owner` is `pad:<id>` or `lesson:<id>` (never a desk or a window, so
moving a pad keeps its kernel). `path` names a `.py` file relative to the vault root; it must resolve inside the
vault and be at most 2 MiB; the session runs a snapshot of its bytes (later edits to the file don't reach it). `view`
is `app` (default: `view-as=present&show-chrome=false`) or `edit` (cells shown). It answers at once:

```
{version: 1, sessionId, owner, state, stopReason, error, restarts, framesAttached, cells, startSeconds,
 frameUrl, memoryBytes}
```

with `state: starting` when cold. The window loads `frameUrl` once `notebook.status` reads `ready`. Opening the same
owner on the same revision and view returns its session; after an idle stop it restarts the same session (same URL,
recorded UI values replayed into the next page's instantiate). A new revision replaces the session.

**`notebook.status {sessionId}`**, **`notebook.close {sessionId}`** (graceful, then forced, then forgotten).

**`notebook.release {sessionId, cells}`.** Releases held cells, which a notebook ships with `@app.cell(disabled=True)`
so marimo never runs them or anything below them; marimo runs a released cell at once. A held cell hides output
from the frame, not from the notebook's own code: held cells are display gating, not a security boundary (NBF-16). It needs a frame attached
(marimo routes the request to the frame's own connection); without one it answers `notebook_not_connected`.

**`notebook.run_cells {sessionId, cells: [{name, code}]}`.** Runs named cells with the given code, for a pad cell's
⇧↵ and later the teacher's edits. It needs a frame attached too.

**Errors** (stable codes): `notebook_runtime_unavailable` (no bubblewrap, no notebook extra, or a runtime directory
too deep for a socket path), `notebook_path_invalid`, `notebook_session_not_found` (including another vault's
session), `notebook_sessions_full` (retryable), `notebook_not_connected` (retryable), `notebook_cell_unknown`,
`notebook_kernel_refused` (retryable), `notebook_runtime_busy` (retryable).

**Lifecycle:**
- Each session has its own scope (`learnloop-notebook-<hex>.scope`) with `MemoryMax`, `MemorySwapMax=0`,
  `CPUQuota=200%`, `TasksMax=512` and `OOMPolicy=continue`. Without a user manager it falls back to
  `prlimit --as`, where `memoryBytes` reads null.
- A server that exits on its own is restarted, with backoff, up to three times; then the session fails with the
  reason. A restart keeps the proxy, so the frame URL is unchanged.
- Idle stop happens after `idle_minutes` with no frame attached. The sweep runs every 30 s.
- The session limit: opening another session stops the least recently used one with no frame attached, else it
  is refused.
- The sandbox has no writable host path (fix round, NBF-5). The run directory holds the socket and the token,
  both made by the unsandboxed side; the sandbox never sees it.
- A vault switch stops and forgets every other vault's session. The context's `close` stops everything and joins
  the runtime's thread, bounded.
- The server's output (it prints its access token) is kept as a 16 KiB tail in memory only, never written to disk
  or returned by an RPC.

**The frame** (B4 builds the component) gets `frameUrl` = `http://127.0.0.1:<session port>/s/<secret>/?...`.
- Each session has its own port, so each notebook is its own origin.
- The proxy refuses another `Host` (421), another path (403), a service worker (403), and any API outside the
  allowlist (403). The allowlist is the page, `assets/`, `@file/`, `health`, `instantiate`,
  `set_ui_element_value`, `set_model_value` and `function_call`.
- It answers 503 while the server starts and 502 while it is down.
- Every response carries the frame CSP: `'wasm-unsafe-eval'`, no `'unsafe-eval'`, and
  `connect-src 'self' ws://127.0.0.1:<port>`, which leaves out `ipc:` and `http://ipc.localhost`. Its
  `frame-ancestors` lists the app's origins (`tauri://localhost`, `http(s)://tauri.localhost`, and the dev server
  `http://localhost:1420`).
- The injected bridge posts the four messages only to the first ancestor origin, and only when that origin is one
  of the app's.

## Settings (the owner's six decisions, each one name while the owner is asked)

| Decision | Default | Where |
|---|---|---|
| 1. Notebook origins in the main window's CSP | `frame-src http://127.0.0.1:*` (port wildcard) | `tauri.conf.json`; the proxy's bind host is `settings.FRAME_HOST` |
| 2. How pad cells render | not decided here (B6) | — |
| 3. Learner-written cells sandboxed too | yes | `settings.LEARNER_CELLS_SANDBOXED` (only `True` is built; `False` is refused) |
| 4. Scratch size cap | a size-capped tmpfs as the session's home and working directory, 256 MiB | `notebooks.scratch_mib` |
| 5a. Memory per session | 2048 MiB | `notebooks.memory_max_mib` |
| 5b. Idle minutes | 10 | `notebooks.idle_minutes` |
| 5c. Most concurrent sessions | 6 | `notebooks.max_sessions` |
| 6. GPU | none (CPU only) | `settings.CPU_ONLY` (only `True` is built) |

Where each default comes from (the gate's measurements):
- **Memory, 2048 MiB.** An idle session of the synthetic notebook held 125–137 MB with peaks of 138–153 MB;
  2048 MiB is about thirteen times that peak. It is half a figure render's 4 GiB cap, because several sessions run
  at once. A cell's child that passes the cap is killed while the session keeps serving.
- **Idle stop, 10 minutes.** Resuming costs about a second (server start 0.37–0.42 s, warm reload 0.5–0.6 s, values
  replayed), so a short idle limit costs little.
- **Six sessions.** Six idle sessions hold about 0.8 GB.
- **Scratch, 256 MiB.** A session wrote kilobytes there; a 64 MiB write went through when nothing capped it. The
  tmpfs is charged to the session's memory.

The four config fields form one section, `[notebooks]`. The section is left out of every dump at its defaults
(`exclude_if`), so whole-config hashes keep their bytes; `tests/goldens/effective_defaults.toml` is unchanged, and
therefore does not list these defaults either.

## Proofs and tests

- **Figures' sandbox unchanged:** the moved profile builds byte-identical commands to the pre-change module on
  every caller's shape. I compared 40 cases (5 commands × 2 workdirs × hardened or not × with and without unset
  variables) through `concept_animation._sandboxed_command`, `pf_sandbox._sandboxed_command` and the old module,
  plus the flags, the bubblewrap lookup, the mount roots and `render_launch` with and without a scope. The figure,
  Manim, PF and declared-function test files pass unchanged.
- **Unit tests with fakes** (`tests/test_notebook_runtime.py`):
  - the supervisor's states: ready, a server that never answers, a failed spawn, restart with backoff, the restart
    limit, graceful then forced stop, a stop during backoff, a restart after stop;
  - the runtime: one session per owner and revision, replacement, vault scoping, a switch, the session limit,
    full, idle stop and resume with values, the run-directory bound, release and run needing a frame and known
    cells, a refused runtime, close;
  - the proxy's checks: Host, path, allowlist both ways, upstream and downstream headers, the CSP, the bridge, and
    the ASGI refusals before the server;
  - the adapter's parsing, the launch command and scope, the settings and their dump, and the CSP entry.
- **The adapter test** (`tests/test_notebook_runtime_adapter.py`): every private interface holds in the installed
  marimo, the installed version is the pinned one, no other runtime module names marimo or its API paths, and the
  adapter imports only the standard library and ends with its `__main__` guard.
- **Real sandbox** (`tests/test_notebook_runtime_sandbox.py`, marker `notebook_sandbox`, skipped without bubblewrap
  or the notebook extra; 4 tests in about 8 s), each through the proxy as a frame would (no browser):
  - an edit round trip (slider 3 → 4, `square=16`), then a stop with no process left;
  - the frame's own `set_cell_config` refused (403) while the sidecar's release runs the held cell;
  - a SIGKILLed server restarted on the same URL, and a fresh page getting the recorded value (`square=49`);
  - a vault switch stopping only the other vault's server.
- **RPCs** (`tests/test_notebook_rpcs.py`): registered, desktop only, extra fields refused, owner pattern,
  versioned replies naming the vault open now, the snapshot and settings passed, paths outside the vault refused,
  every refusal's stable code, the context's switch and close.

## What B4–B7 need

- **B4 `NotebookFrame`:**
  - poll `notebook.status` until `ready`, then mount the iframe with
    `sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"`; retry on 502/503 as §11.2 says;
  - check bridge messages by `event.source` and `event.origin` and treat their payloads as untrusted notebook text;
  - one live frame per session (the overview shows a placeholder);
  - hide marimo's "Reconnected" banner in the paper theme (its Restart button calls an endpoint the frame may not
    use).
- **B5 packaged-app check:** the items below.
- **B6 pad cells:** the sidecar writes a pad's cells to a notebook file revision (H's cell writer) and opens
  `pad:<id>` on it, starting on the first ⇧↵. `notebook.run_cells` runs changed cells. Owner decision 2 decides how
  they render. New cells need a new revision, since `run_cells` only addresses cells marimo already reported.
- **B7 lesson notebooks:** open `lesson:<id>` on the lesson's notebook revision; held cells ship `disabled=True` and
  NA2's commit path calls `notebook.release`.

## Still unverified (the packaged app on WebKitGTK)

- whether Tauri's init scripts or IPC reach a cross-origin `http://127.0.0.1` subframe (the frame's CSP and its
  origin say no; the packaged run must show it);
- WebSocket relay and reconnect, `'wasm-unsafe-eval'` and the frame CSP as WebKitGTK applies them;
- `location.ancestorOrigins` in WebKitGTK, which the bridge uses to name the workbench; without it the bridge stays
  silent;
- time to interactive and memory in the packaged app (NA0.3).

## Judgment calls

- The profile moved to a new root module rather than into the runtime package, so figures don't depend on the
  notebook runtime. That raised `first_level_root_modules` from 36 to 37, and the new package raised
  `first_level_packages` from 51 to 52; both goldens were raised by hand, with the reason on each line.
- (Superseded in the fix round, NBF-5.) The run directory was a writable host path, because the socket had to be
  visible to the host. The fix round removed that: the host now creates and listens on the socket and hands it to
  the server as a descriptor.
- The real-sandbox tests make their runtime directory with `tempfile.mkdtemp` in the system temp directory and
  delete it, rather than under `tmp_path`: a test's `tmp_path` is too deep for a Unix socket's path.
- RD3's fix round (on its own branch, not yet on main) keys polled jobs by `polled_jobs.vault_key` and ends the
  background epoch on a switch. The runtime does the same itself (`_vault_key` in the handler, its own epoch), and
  its switch hook sits in the same block of `SidecarContext.load`; the merge should keep both lines.

## Fix round (adversarial review of the notebook work on main, 2026-11-23)

| Finding | Ledger | What changed | Proof |
|---|---|---|---|
| BLOCKER: a sandbox-to-host write through the token file. Notebook code could replace `run_dir/token` with a symlink to a host file; on restart the unsandboxed supervisor's `write_text` and `chmod` followed it. The socket could be swapped the same way (a symlink to a host socket, reached by the proxy with frame-chosen requests), and a FIFO in the token's place hung the server | NBF-5 | Fixed as a class. The sandbox has no writable host path any more (`sandboxed_command` takes `workdir=None`; its home and working directory and its `/tmp` are tmpfs). The token is written by the host into the private run directory and mounted read-only at `/ll/token`. The socket is created, bound and listening by the host (`hostfiles.listening_socket`) and passed to the server as an inherited descriptor (`uvicorn.Config(fd=…)`), so the server never names or creates a socket path. Every host file of a session goes through `notebook_runtime/hostfiles.py`: directories are opened with `O_NOFOLLOW` and checked to be this user's and private (the base may sit in the shared temporary directory); files are created afresh with `O_CREAT\|O_EXCL\|O_NOFOLLOW` through the directory's descriptor and checked to be a regular file with one link; a directory where a file belongs is refused; the socket is checked with `lstat` (a socket of this user, never a link) before every connection, by the supervisor's client, the proxy's client and the WebSocket relay | `tests/test_notebook_host_boundary.py`: from inside a running notebook, a symlink to a host file, a hard link, a FIFO, a directory and the socket swapped for a symlink to a host socket are each planted at the token's or socket's path, then the server is killed (the supervisor restarts it) or the host connects. Before the fix: the host file was overwritten with the token, the host socket was reached, and the FIFO hung the session. After: every plant is refused inside the sandbox, the host file is unchanged, the host socket is never reached, and the session restarts. A static test fails on any filesystem call in the unsandboxed modules outside `hostfiles` (an allowlist names the reads of non-sandbox paths, each with its reason); on the pre-fix files it lists 20 call sites. A third test pins that the launch has no writable bind and mounts the token read-only |
| The secret path was in process arguments (`--base-url /s/<secret>`), readable by any local user | NBF-7 | The launcher takes the base URL from `LEARNLOOP_NOTEBOOK_BASE_URL` (removed before marimo runs, so children do not inherit it) and adds it to marimo's argv in memory. Scope: another local user. A hostile process of the same user is not isolated by any file permission and is out of scope (stated in `hostfiles`) | No running process's `/proc/<pid>/cmdline` holds the secret (three did before); the launch argv test pins it |
| The frame could exhaust the sidecar's memory through recorded UI values and unbounded request bodies | NBF-8 | Bodies over `settings.REQUEST_MAX_BYTES` get 413; `supervisor.record_ui_values` keeps only accepted values of the notebook's own controls (`<cell id>-<n>`) within `settings.UI_VALUES_MAX_BYTES`; lesson commits are read from accepted values only | The oversized request is refused with nothing kept; a request the server never took (503) keeps nothing; unknown ids and a value past the bound are dropped |
| A close or switch could miss a server being spawned and leave it running | NBF-9 | `Supervisor.start` records itself; `stop` waits for it (bounded); `_launch` kills a server whose spawn returns after a stop, or whose readiness wait a stop ended | A stop during a gated spawn: once the spawn returns, the process is killed and the session ends `stopped` |
| Close could cancel a stop before its server was killed | NBF-10 | `NotebookRuntime._kill_left`: after the bounded graceful stop (`CLOSE_SECONDS`), every listed session's process group still alive gets SIGKILL from the calling thread, on `close` and `switch_vault` | A server that stalls `shutdown` and ignores SIGTERM is killed by `close` within its deadline |
| The writable host directory had no storage cap; `/tmp` was unsized | NBF-11 | Nothing on the host is writable by the sandbox (NBF-5). Its `/tmp` is a tmpfs at the scratch size, like `/scratch`. The run-directory size sweep, its setting and its `run_dir_full` stop reason are gone (the test that wrote a filler into the run directory went with them) | A notebook writing 80 MiB to `/tmp` and to `/scratch` (64 MiB caps) gets "no space" in both; the launch argv pins the sized `/tmp` |
| The fallback without a user manager lost every aggregate cap (or ran uncapped) | NBF-12 | Notebooks need `systemd-run --user --scope`; without it `missing_requirements` says so and the frame shows the runtime unavailable. The real-sandbox tests now run inside a scope too (they ran unscoped under a test wrapper that strips the session bus) | `missing_requirements` lists the user manager when the probe fails; `scope_prefix(scoped=False)` raises `RuntimeUnavailable` |
| Notebook Python holds the marimo credential and can release its own held cells (STOPPED with options) | NBF-16 | Verified: the token is mounted read-only into the sandbox (the server needs it), and the kernel that runs the notebook's cells shares the sandbox, user and process tree with the server, so cell code can read the token and change its own cells' configuration in the kernel. Held cells gate what the frame shows; they never protected anything from the notebook. Records corrected (here and in the B7 record). Options: **(a)** accept as display gating and keep protected values out of notebooks (NA §10.5 already keeps keys and cold-eligible masked values out of the notebook and the kernel); **(b)** host-owned reveals, the reveal kept by the sidecar and sent into the kernel only after a frozen commit (NA §6.3; changes the authoring format, so it belongs with NA's commit gate); **(c)** server and kernel in separate sandboxes with a narrow channel, which closes token reading but not (b)'s gap by itself. Recommendation: (a) now, (b) with NA's commit gate | — |

# Notebook NA0.2: the native marimo server under the sandbox (a gate)

- **Base:** `ba7884c102` (origin/main); branch `notebook/na0.2-sandboxed-server`. Date 2026-11-23.
- **Scope:** `spec_notebook_activities_v1.md` §5.1 and §6.3a ("So NA0.2 is a gate, not a spike"), for the Reader
  workbench's RD9b (`spec_reader_workbench_v2.md` §11, §16). The owner moved marimo up on Nov 23, ahead of the spec's
  "runtime track starts only after S0".
- **No product code changed.** The spike code is disposable and lives in a scratch root outside the repository; this
  record is the only tracked output. No defect was found in existing code, so no ledger row was added.
- **Only synthetic notebooks** written for the spike were run: no owner notebook, vault or model call.

## Verdict (read first)

**The gate passes in headless Chromium, with five changes to the design as written and one part left to the
packaged-app run.** An edit-mode marimo server runs under the PF hardened bubblewrap profile with no network
namespace, listens only on a Unix socket bound into the sandbox, and is reached by a per-session proxy on
`127.0.0.1` that authenticates, filters, sets a strict CSP and carries WebSockets. The changes:

1. **The profile needs a hosts file.** marimo's edit kernel connects back to the server over multiprocessing's
   AF_INET listener, which binds `("localhost", 0)`. The hardened profile mounts no `/etc/hosts`, so without one
   every session fails to start its kernel ("Temporary failure in name resolution"). A two-line hosts file of our
   own (`127.0.0.1 localhost`, `::1 localhost`), bound read-only, fixes it; nothing else from the host's `/etc` is
   needed.
2. **The launcher must be import-safe.** The kernel is a multiprocessing *spawn* child that re-executes the
   launcher's main file. The socket launcher keeps its work under `if __name__ == "__main__"`.
3. **The scope needs `OOMPolicy=continue`.** Under systemd's default policy, one cell's child process hitting the
   scope's `MemoryMax` stops the whole scope: server and kernel die and the session is lost. With
   `OOMPolicy=continue`, only the process the OOM killer chose dies, and the session keeps serving. A scope stopped
   that way also stays listed as a failed unit until it is reset, so the supervisor resets its own unit by name.
4. **The proxy owns marimo's skew-protection token.** After a supervised restart the server has a new token, so the
   open page's calls fail ("Invalid server token") and it shows "Failed to instantiate". Rewriting the
   `Marimo-Server-Token` header at the proxy (the frame is always the pinned marimo, so skew protection guards
   nothing here) lets the open page reconnect and re-instantiate by itself.
5. **The frame gets a narrow API capability, the sidecar the full one.** The frame's JavaScript (which includes
   model-written widget code) reaches marimo only through the proxy's allowlist: no cell config, run, scratch,
   execute, save, document edits, restart, shutdown, file browsing, terminal or package endpoints. The sidecar
   talks to the socket directly with edit rights. Holding and releasing cells therefore stays with the host, as
   §6.3a requires.

**Not verified here:** the packaged app on WebKitGTK (RD-spike, NA0.1, NA0.3). In particular, whether Tauri's init
scripts or IPC reach a cross-origin `http://127.0.0.1` subframe, WebKitGTK's third-party-cookie and WebSocket
behaviour in that frame, and its timings. The design avoids cookies entirely (below), so the cookie question
should not matter, but the packaged run must confirm the IPC denial.

| Required (§6.3a and the brief) | Verdict | Evidence (numbers below) |
|---|---|---|
| Edit-mode server under the hardened sandbox, behind an app-view front end | pass, with changes 1 and 2 | `marimo edit` on a socket; frame opened with `view-as=present&show-chrome=false`; no code, no editor chrome |
| No network beyond a socket the host reaches | pass | `--unshare-all` (network namespace with loopback only); server on a Unix socket in the session's run directory; the kernel's own loopback stays inside the namespace |
| Read-only notebook; writable scratch only inside the scratch root | pass | notebook bound read-only (writes: EROFS; marimo's save: 500, file unchanged); root remounted read-only; only the session scratch is writable |
| Start time, idle and running memory, reactive edit round trip | measured | server ready 0.37–0.42 s; first frame interactive 3.3 s (cold, headless Chromium); warm reload 0.5–0.6 s; idle session 125–137 MB; slider round trip median 18–28 ms, p95 24–31 ms |
| Socket bridge with authentication, WebSocket proxying and reconnect | pass | secret path, Host check, upstream token injection; WS proxied; a dropped WS reconnects in 3.0 s with state kept |
| Held cells through the host | pass | the cell ships `disabled=True`; the sidecar's `set_cell_config` releases it and marimo runs it in 22–27 ms; the frame's own attempt is refused (403) |
| UI-state replay | pass | the proxy records `set_ui_element_value`; after a crash, a fresh page's `instantiate` gets the recorded values and shows the slider at its old value |
| Two sessions at once, isolated | pass | two sandboxes, two scopes, two origins; parallel start 0.42 s; both interactive 3.4 s; cross-frame DOM and fetch blocked |
| Clean stop and crash recovery by the supervisor | pass, with change 3 | graceful stop 0.19–0.35 s (exit 0); forced stop immediate; parent SIGKILL leaves nothing (7 ms); server SIGKILL to ready 0.87–0.92 s; the open page re-instantiates by itself 3.2 s after the kill |
| What the sandbox blocks | table below | 30 kernel-side attempts: 27 blocked; the three not blocked are by design or a gap (private `/tmp`, scratch writes, scratch size) |
| Private marimo interfaces relied on | listed below | |
| Strict CSP, no Tauri IPC in the frame | pass in Chromium; packaged app unverified | `connect-src 'self' ws://127.0.0.1:<port>` blocks `ipc:` and `http://ipc.localhost`; no `__TAURI__` globals in the frame |
| Bridge (workbench §11.3) | pass | all four messages cross with the right origin; see the forged-message caveat |
| Sidecar observe, edit, run, inspect, save/reload (NA0 §15 item 2) | pass, save excepted by design | edit+run reaches the frame in 16–20 ms; inspect via `/api/kernel/execute` 59 ms; kiosk observation over the socket; save refused (read-only notebook); `restart_session` re-renders in 0.31 s |

## Method

- **Machine and versions:** CachyOS, Linux 7.3.5, bubblewrap 0.13.1, systemd 262, Python 3.12.14, marimo 0.25.2 and
  wigglystuff 0.6.0 from the `notebook` extra, anywidget 0.11.0, numpy 2.5.1, uvicorn 0.54.0, httpx 0.28.1,
  websockets 16.0, headless Chromium from Playwright 1.65.2 (its pinned build).
- **The sandbox** is LearnLoop's own `_sandboxed_command(..., hardened=True)` from
  `content/authoring/concept_animation.py` (every namespace unshared, `--unshare-user --disable-userns --cap-drop
  ALL`, `--die-with-parent --new-session`, read-only `/usr` and interpreter mounts, a fresh `/tmp`, the session
  scratch as the only writable bind), plus: the notebook bound read-only at a fixed path, the socket launcher bound
  read-only, the hosts file, and `--remount-ro /`. Environment: `HOME`, `XDG_*` and caches inside the scratch, no
  session bus (unset inside the sandbox).
- **The scope:** `systemd-run --user --scope` with `MemoryMax=4G` (1G for the memory probe), `MemorySwapMax=0`,
  `CPUQuota=200%`, `TasksMax=512`, a unit name per session, and `OOMPolicy=continue` in the variant that keeps the
  session alive.
- **The launcher** patches `uvicorn.Config.__init__` to pass `uds=<socket>` (marimo's CLI has no socket option,
  §6.3a) and calls marimo's CLI entry point with `edit <notebook> --headless --token-password-file <file>
  --base-url /s/<secret> --skip-update-check --no-sandbox`. marimo config inside the scratch: autosave off, no
  language servers, no Copilot.
- **The proxy** (a sidecar stand-in, Python asyncio in one process with the supervisor): one ASGI server per
  session on its own `127.0.0.1` port, so each notebook has its own origin. It forwards HTTP through a pooled httpx
  client over the socket and WebSockets through `websockets.unix_connect`.
- **The workbench stand-in** is a page served from a third `127.0.0.1` port with
  `frame-src http://127.0.0.1:*`, which frames the notebooks with
  `sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"` and validates bridge messages by
  `event.source` and `event.origin`.
- **Synthetic notebooks:** a reactive one (a `mo.ui.slider` driving a computed cell, a `mo.state` counter and
  button, a wigglystuff `Slider2D` through `mo.ui.anywidget`, a cell reporting the kernel's pid, and a `reveal` cell
  shipped `disabled=True`), and a probe notebook whose single cell tries the escapes below.
- Every run happened inside memory-capped scopes; every process stopped was one the spike started (by pid or by
  its process group); nothing was bound except `127.0.0.1` and Unix sockets.

## Measurements

| Measure | Value |
|---|---|
| Server start to healthy on the socket | 0.37–0.42 s (every start in the runs) |
| Two servers started in parallel | 0.42 s wall for both |
| Frame inserted to first computed output (cold browser cache) | 3.3 s (4.1–4.3 s with an unpooled proxy) |
| Of which: page and 355 asset requests before the WebSocket opens | 2.7 s; WS to `kernel-ready` 0.25 s; `kernel-ready` to first output 0.2 s |
| Serving marimo's assets straight from the installed package instead | no change (3.26 s): the browser's module graph, not the server, is the cost |
| Warm reload of the same frame (assets cached, session alive) | 0.52–0.62 s |
| Memory, server alone (before a frame connects; the kernel starts on connect) | 64–65 MB |
| Memory, one idle session (server, kernel, multiprocessing resource tracker) | 125–137 MB current, 138–153 MB peak |
| Memory after 30 reactive edits | 129–141 MB |
| Slider edit to recomputed output in the frame, 30 edits | median 18–23 ms, p95 24–30 ms, max 31 ms |
| The same with the frame policy enforced | median 17–28 ms, p95 25–31 ms |
| Sidecar release of a held cell to its output in the frame | 22–27 ms |
| Sidecar edit+run of a cell to the frame | 16–20 ms |
| Sidecar inspect through `/api/kernel/execute` (SSE) | 59 ms |
| Proxy-dropped WebSocket to reconnected | 3.0 s (marimo's backoff); first edit after it 24–31 ms |
| Graceful stop (marimo's `/api/kernel/shutdown` over the socket) | 0.19–0.35 s, exit 0, no process left |
| Forced stop (SIGTERM to the process group) | immediate, no process left |
| Parent SIGKILLed (the supervisor process) | every sandbox process gone within 7 ms (`--die-with-parent`) |
| Server SIGKILLed to supervised restart ready | 0.87–0.92 s |
| Open page re-instantiating on the restarted server by itself | 3.2 s after the kill, slider value kept |
| Reloaded frame after the restart, values replayed | 0.53–0.90 s |
| Kernel SIGKILLed | server stays up; the sidecar's `restart_session` makes the open page re-instantiate itself; a reload renders in 0.49–0.90 s |
| Moving the frame to another slot (remove and re-create) | rendered in 0.51–0.52 s, same kernel, counter and slider kept |

Memory is the scope's `memory.current` (anonymous memory is about 124 MB of it). The notebook imports only marimo,
numpy and wigglystuff; heavier toolbox notebooks will cost more.

## What the sandbox blocks (kernel-side attempts from the probe notebook)

| Attempt | Result |
|---|---|
| Connect to an external address | blocked: network unreachable |
| DNS lookup | blocked: no resolver |
| Connect to a listener the host bound on `127.0.0.1` | blocked: refused (the namespace has its own loopback) |
| See host network interfaces | blocked: no `/sys/class/net` |
| Connect to the host's abstract X11 socket | blocked: refused (abstract sockets are per network namespace) |
| See the host's abstract Unix sockets | blocked: 5 sockets visible, all the sandbox's own |
| Write the notebook | blocked: read-only file system |
| Write `/`, `/usr`, the Python environment | blocked: read-only file system |
| Read a file in the scratch root outside the session | blocked: not present |
| Read the other session's scratch | blocked: not present |
| Read `~/.ssh`; list the home directory | blocked: only the mount points of the bound paths exist |
| Read `/etc/passwd` | blocked: not present |
| Reach the session bus (socket or variable) | blocked: neither present |
| Reach the X11 socket directory | blocked: not present |
| See host processes | blocked: 4 pids visible (pid namespace) |
| Signal a host pid | blocked: no such process |
| Create a user namespace (threaded kernel; single-threaded child; `unshare -U -r`) | blocked: EINVAL in the threaded kernel, ENOSPC in a single-threaded child and from `unshare` (`--disable-userns`) |
| Capabilities and setuid | blocked: `CapEff=0`, `NoNewPrivs=1`; `sudo -n true` fails |
| Start 700 threads | blocked at 494 (`TasksMax=512` counts the session's tasks) |
| Allocate 1.5 GiB in a child under a 1 GiB cap | blocked: child killed (SIGKILL); with the default `OOMPolicy` the **whole session died**, with `OOMPolicy=continue` the session kept serving and its probe output rendered |
| Write `/tmp` | **not blocked, by design:** a private tmpfs, invisible to the host and gone at stop (charged to the scope's memory) |
| Write the session scratch | **not blocked, by design** |
| Write 64 MiB to the scratch | **not blocked: a gap.** Nothing caps the scratch's size; see the owner decisions |

Escapes from the frame side (model-written JavaScript in the notebook page), with the policy enforced:

| Attempt | Result |
|---|---|
| `set_cell_config` (release a held cell), `run`, `execute`, `scratchpad/run`, `document/transaction`, `save`, `shutdown`, `restart_session`, `install_missing_packages`, `files/list_files`, `api/sessions` | 403 from the proxy's allowlist |
| Open marimo's terminal WebSocket | refused at the proxy (closed 1006) |
| Fetch or open a WebSocket to the other session's port | blocked by `connect-src` |
| Fetch `ipc://localhost/...` or `http://ipc.localhost/...` (Tauri's IPC) | blocked by `connect-src` |
| Image beacon to another host | blocked by `img-src` |
| Read the parent's or the sibling frame's DOM | SecurityError (cross-origin) |
| `window.open`, `top.location = ...` | blocked by the iframe sandbox |
| Navigate the frame itself to another host | blocked by the workbench's `frame-src` (error page) |
| Register a service worker | refused (the proxy refuses `Service-Worker: script` requests) |
| Read marimo's token or a cookie | none: the token is injected upstream and every `Set-Cookie` is stripped |
| Post a bridge message the workbench doesn't know (`{ll: "run"}`) | rejected by the workbench |
| **Post a well-formed bridge message** (`{ll: "companion", text: ...}`) | **accepted**: it comes from the frame's own origin; see below |

## The design, as it now stands

- **Process model:** one sandboxed `marimo edit` server per notebook session (a pad's cells, or one lesson
  notebook), started and supervised by the sidecar, in its own scope and its own scratch. Edit mode is needed for
  the endpoints that run cells and change cell config (§6.3a). In edit mode one server holds one session per
  notebook file, and a reconnecting frame rejoins it: the kernel belongs to the server, not to the page or its
  `session_id` parameter. Moving or reloading a frame keeps the kernel whether or not the URL carries a session id
  (both measured).
- **Authentication.** Three layers, none of them a cookie, so the cross-site frame never depends on third-party
  cookies:
  - the frame URL carries a per-session secret path (`/s/<secret>/`, which is also marimo's `--base-url`); other
    paths get 403;
  - the proxy refuses any `Host` but `127.0.0.1:<its port>` (421), against DNS rebinding;
  - the proxy adds `Authorization: Bearer <marimo token>` upstream and strips `Set-Cookie`, so the page never holds
    the token. Without the token the socket answers 303 (to login) or 401. The socket is created `0666` by uvicorn,
    so its directory is `0700`.
- **The frame's API allowlist**, measured in observe mode and then enforced: `GET` of the page, `assets/`,
  `@file/` (anywidget ESM and virtual files), `health`; `POST api/kernel/instantiate`, `set_ui_element_value`,
  `set_model_value`, `function_call`; the WebSocket at `ws`. marimo's app view also asks for
  `api/datasources/discover`, `api/packages/sandbox`, `api/document/transaction` and a service worker; all four are
  refused without visible effect.
- **The frame's CSP** (set by the proxy on every response):
  `default-src 'none'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:; style-src 'self'
  'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' ws://127.0.0.1:<port>;
  worker-src 'self' blob:; frame-src 'self' blob: data:; media-src 'self' blob: data:; manifest-src 'self';
  object-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors <workbench origin>`.
  - `'wasm-unsafe-eval'` is required: marimo's frontend instantiates a WebAssembly module (Loro) and fails without
    it. The app's own CSP already allows it, and the sketch engine shows WebKitGTK honours it.
  - `'unsafe-eval'` is not needed: one `eval` probe in marimo's bundle is refused and nothing breaks.
  - `blob:` in `script-src` is not needed for the tested widget (a run without it had no new violation and the
    anywidget rendered); it stays until heavier widgets are tried.
  - `'unsafe-inline'` scripts are needed by marimo's page (its mount configuration). The CSP's job is containment
    (no other origin, no IPC, no beacons, no navigation), not stopping model JavaScript, which runs by design.
- **No Tauri IPC in the frame**, by construction: the frame's origin is `http://127.0.0.1:<port>`, not the app's;
  its `connect-src` excludes `ipc:` and `http://ipc.localhost`; the capability file grants only the `main` window's
  local origin and lists no `remote.urls`; on Linux the shell unregisters WebKit's `ipc` message handler, the one
  channel that reaches every frame (`main.rs`); and `frame_guard.rs` refuses an invoke whose Origin or Referer is
  not the app's document. Chromium confirms the first two; the packaged app must confirm the rest.
- **Held cells:** a held cell ships `disabled=True` in the notebook file, so marimo never runs it, nor anything
  downstream, before release. The sidecar releases it with `set_cell_config` over the socket and marimo runs it at
  once (22–27 ms). Re-holding a released cell leaves its last output on screen (stale), so a hold is one-way, which
  fits freeze-then-reveal. The cell names map to marimo's cell ids from the `kernel-ready` message, which the proxy
  reads in passing.
- **UI-state replay:** the proxy records each `set_ui_element_value` (object id to value). When a page instantiates
  with no values (a fresh page after a restart or an idle stop), the proxy fills `objectIds` and `values` from the
  record. Only UI element values come back: kernel state not derived from them (a `mo.state` counter) is lost on a
  kernel or server restart. Durable resume across app restarts needs the record stored by the sidecar.
- **What reaches the frame:** `kernel-ready` carries every cell's source, including hidden cells, in app view.
  Hiding code is presentation, not secrecy, which agrees with §6.3a (no key or masked value in the notebook).
- **One live frame per session.** A second frame on the same session joins as a viewer or takes it over, so the
  overview's miniatures stay placeholders (§11.4), as specified.
- **Visible marimo chrome to suppress:** after a reload, marimo shows "Reconnected — You have reconnected to an
  existing session. Restart". Its Restart button calls an endpoint the frame may not use. The paper theme or the
  bridge should hide it, and restarts go through the sidecar.
- **No GPU in the sandbox:** the hardened profile's `--dev /dev` has no `nvidia*` or `dri` nodes. §5.1's "the host
  GPU is available" does not hold for model-written notebooks under this profile.
- **Starting from a thread is safe:** a sandbox spawned from a thread that then exits keeps running (checked), so the
  runtime may live on a sidecar background thread.

### Private marimo interfaces relied on (all at 0.25.2)

| Interface | Public? | Used for |
|---|---|---|
| `marimo._cli.cli.main` | private module | the launcher's entry point |
| marimo's `start()` building `uvicorn.Config(...)` | private behaviour | the socket patch (`uds=`) |
| `--base-url`, `--token-password-file`, `--headless`, `--skip-update-check`, `--no-sandbox` | public CLI | serving under the secret path; token from a file |
| `?view-as=present`, `show-chrome=false`, `session_id`, `kiosk=true` URL parameters | undocumented frontend | app view; the sidecar's viewer connection |
| `/health`, `/api/kernel/instantiate` (`objectIds`, `values`, `autoRun`), `set_ui_element_value`, `set_cell_config`, `run` (`cellIds`, `codes`), `shutdown`, `restart_session`, `save` | private HTTP API (in marimo's OpenAPI schema, not documented as stable) | everything the sidecar does |
| `/api/kernel/execute` (SSE), `/api/sessions` | private, `include_in_schema=False` | inspect; session listing |
| `Marimo-Session-Id`, `Marimo-Server-Token` headers; `Authorization: Bearer` | private | routing; skew protection; auth |
| WebSocket `kernel-ready` (`cell_ids`, `names`, `codes`) and `cell-op` messages | private | cell name to id; observation |
| `@app.cell(disabled=True)` | public file format | shipping held cells |
| Deterministic cell ids per file | private behaviour | stable ids across restarts |
| The read-only consumer rule ("This connection is read-only for this action") | private behaviour | the sidecar's viewer connection uses its own consumer id, never the page's |

H1 already isolates marimo's private parser interfaces in one adapter (`notebook_authoring/marimo_adapter.py`);
the runtime's interfaces belong in one runtime adapter with the same version check.

## The runtime contract for the workbench (RD9b)

**What the sidecar exposes** (names are proposals; the spec's RPC style):

| RPC | Takes | Returns | Notes |
|---|---|---|---|
| `notebook.open` | `owner` (`pad:<id>` or `lesson:<id>`), `revision` (a notebook file revision the sidecar wrote), `holds` (cell names) | `session_id`, `frame_url`, `state` | starts the server if needed (0.4 s), returns at once with `state: starting` when cold |
| `notebook.status` | `session_id` | `state` (`starting`, `ready`, `restarting`, `stopped`, `failed`), restarts, memory | the window's one-line "not served" message and retry read this |
| `notebook.close` | `session_id` | — | graceful shutdown, forced after a timeout |
| `notebook.release` | `session_id`, cell names | per-cell result | host-side reveal (NA2 adds freezing and logging before it) |
| `notebook.run_cells` | `session_id`, cell names and code | — | pad cells' ⇧↵ and, later, the teacher's verbs (NA4) |

- **Session identity** is the owner key (`pad:<id>` or `lesson:<id>`), never the desk or the window (review F11).
  One server per owner. The marimo session id inside it is an implementation detail.
- **The frame URL:** `http://127.0.0.1:<session port>/s/<secret>/?view-as=present&show-chrome=false`. The proxy bakes
  the workbench's origin into the injected bridge (the spike passed it as a URL parameter).
- **Lifecycle:**
  - a frame detaches on a desk switch or a move and its kernel keeps running;
  - after N minutes with no frame attached (a design value), the sidecar stops the server gracefully;
  - reopening restarts it and replays the recorded UI values;
  - app exit stops every server (the sidecar's background owners close, and `--die-with-parent` covers a crash);
  - a crashed server is restarted with backoff; after three failures the window says so and offers a retry.
- **The main window's CSP** needs a `frame-src` entry for the notebook origins: `http://127.0.0.1:*` (a port
  wildcard; owner decision 1).
- **The four bridge messages** cross by `postMessage` from the frame to the workbench's origin. The workbench
  accepts one only when `event.source` is an iframe it created for a notebook session, `event.origin` equals that
  frame's origin, and the kind is one of the four; it translates `rect` by the frame's position. Notebook JavaScript
  shares the frame's origin and **can forge any of the four** (measured). So their payloads are untrusted notebook
  text: `companion` text is context labelled as coming from the notebook, never an instruction, and `menu`
  coordinates are clamped to the frame's box.

## Build steps from here (sizes as in the specs)

| Step | What | Size |
|---|---|---|
| B1 | Sidecar runtime package: the long-lived-server sandbox profile (hardened flags, hosts file, read-only notebook, run directory, `--remount-ro /`), the scope (`MemoryMax`, `MemorySwapMax=0`, `CPUQuota`, `TasksMax`, `OOMPolicy=continue`), the socket launcher, the supervisor (ready check, graceful and forced stop, restart with backoff, idle stop), the marimo runtime adapter with its version check. Tests with a fake server, plus one real-bubblewrap test marked slow | M |
| B2 | The frame proxy: per-session port, secret path, Host check, allowlist, token injection, cookie stripping, server-token rewrite, CSP, bridge injection, service-worker refusal, WebSocket relay, pooled upstream, the UI-value recorder and replay. ASGI-level tests without a browser | M |
| B3 | RPCs (`notebook.open`, `status`, `close`, `release`, `run_cells`), DTOs, Rust passthroughs, the `frame-src` entry, a `frame_guard` test for a `127.0.0.1` frame | S |
| B4 | Frontend `NotebookFrame`: iframe attributes, the retry (three times, 1.5 s apart), the bridge listener with source and origin checks and rect translation, detach on desk switch, the overview placeholder; the paper theme as variables only, hiding marimo's reconnect banner | M |
| B5 | Packaged-app check (with RD-spike, NA0.1, NA0.3): IPC denial in the frame, WebSockets and CSP in WebKitGTK, time to interactive and memory; sets the desktop budgets | S |
| B6 | **"A marimo cell runs in a pad":** pad `cell` blocks written by the sidecar into the pad's notebook revision (H's cell writer), the server started on the first ⇧↵, runs through `notebook.run_cells`, outputs rendered per owner decision 2, the header states | M |
| B7 | **"A lesson notebook opens in a window":** the lesson window hosts `NotebookFrame` on a read-only lesson revision; styled commit points come with NA2's commit gate | S |

"A marimo cell runs in a pad" needs B1–B4 and B6; "a lesson notebook opens in a window" needs B1–B4 and B7. B5
gates both before RD9b lands.

## Owner decisions

1. **Notebook origins in the main window's CSP:** `frame-src http://127.0.0.1:*` (simple; any loopback port could
   be framed by app code), or a fixed port range reserved for notebook sessions (collisions with other software
   possible). Recommended: the wildcard, since only the workbench creates these frames.
2. **How pad cells render.** marimo's page shows whole notebooks, not one cell. Options:
   - (a) a pad's cells form one contiguous "cell group" shown as one framed marimo document in edit view (code shown,
     since cells are the subject): one runtime path, all widgets work, text blocks sit around the group, not between
     its cells;
   - (b) each cell block renders its static outputs (text, Markdown, HTML, images, SVG) in a sandboxed frame from
     what the sidecar observes, with widgets unsupported in pads: interleaves freely but loses the toolbox.
   Recommended: (a) for RD9b.
3. **The learner's own code.** §5.1 says it runs on a native kernel under their control. Running pad cells in the
   same sandbox costs nothing measurable and keeps one runtime. Recommended: sandbox them too.
4. **Scratch size cap:** nothing caps it now. Options: `RLIMIT_FSIZE` per file (simple, per file only) or a
   size-capped tmpfs scratch (caps the total but counts against the scope's memory). Design value either way.
5. **Design values:** memory cap per session (4G in the spike), idle minutes before a stop, and the most concurrent
   sessions.
6. **GPU:** none inside the sandbox. Passing GPU device nodes into a sandbox running model-written code widens the
   attack surface. Recommended: CPU only for model-written notebooks.

## Notes for the other spikes

- **NA0.1 (packaging and CSP):** the notebook frame's CSP above. It needs `'wasm-unsafe-eval'`, no `'unsafe-eval'`,
  and `frame-ancestors` naming the workbench. The `Sec-Fetch-Dest: iframe` check (refuse a top-level load of the
  notebook URL) is optional hardening once WebKitGTK's support is confirmed. Altair and matplotlib are not in the
  pinned environment yet, so Vega's CSP needs are unknown.
- **NA0.3 (budgets):** in headless Chromium, cold time to interactive is 3.3 s, dominated by the page's 355 module
  requests (2.7 s) rather than by the server, the proxy (pooling saved about 1 s) or the kernel (0.45 s from
  WebSocket to output). Warm reloads take 0.5–0.6 s. An idle session holds about 130 MB. Prewarming candidates: keep
  the asset cache warm, start servers on pad creation or lesson suggestion.
- **Spec text to correct when NA2 starts:** §5.1's "the host GPU is available" and "the learner's own code runs
  natively" against owner decisions 3 and 6. §6.3a's list of NA0.2 items now has answers here.

## Reproduce

The spike lives in the scratch root outside the repository: the socket launcher, the runtime (sessions, supervisor,
proxy), the bridge script, the two synthetic notebooks, the Playwright scenarios (`observe`, `enforce`, `held`,
`two`, `move`, `reconnect`, `crash`, `stop`, `bridge`, `control`, `escapes`, `escapes_continue`) and their JSON
results. Each scenario runs through the scratch wrapper, inside a 3G memory-capped scope, with the worktree's Python
environment and Playwright 1.65.2's pinned headless Chromium. The marimo servers run in their own per-session
scopes.

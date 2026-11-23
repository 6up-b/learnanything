# Notebook frame B4–B5: the NotebookFrame component, the paper theme, and the packaged-app check

- **Base:** branch `notebook/frame-b4-b5`, cut from the runtime's tip plus its status commit, then merged with
  origin/main (the goal lens backend) and with `reader/rd4-fix-frontend` (the RD3 and RD4 fix rounds and the visual
  reference tool). In `SidecarContext.load` both vault-switch hooks stand, the polled jobs' `interrupt_vault` and
  the runtime's `_stop_notebooks`. Both sides' switch tests pass on the merged tree
  (`test_reader_rd3_fix_backend.py`, `test_notebook_rpcs.py`, `test_notebook_runtime*.py`; 490 passed).
- **Scope:** B4 (the frame in a window, its states, the window lifecycle, the bridge, the paper theme, a harness
  fixture) and B5 (the items the runtime record left unverified on WebKitGTK), from
  `docs/reviews/notebook-runtime-b1-b3.md`. No migration, no kill switch, no model call, no owner notebook.

## What was built

| Piece | Where | What it does |
|---|---|---|
| `NotebookFrame` | `screens/desks/notebook/NotebookFrame.tsx`, `notebook.css` | Takes an owner key (`pad:<id>` or `lesson:<id>`) and a notebook path, calls `notebook.open`, follows `notebook.status`, and shows honest states: opening, starting, ready (the frame), restarting (the frame stays and reconnects by itself), stopped with resume, failed with try again, and the runtime unavailable in the sidecar's words |
| The bridge's checks | `screens/desks/notebook/bridge.ts` | A message is accepted only from the frame's own `contentWindow`, from its frame URL's origin, with exactly one of the four shapes (no extra key, text at most 4,000 characters, finite geometry). Its geometry moves onto the page, clamped to the frame's box |
| The desks' bridge host | `DeskShell.tsx` (28 lines, additive) | `c` summons the companion at the frame's selection with its text as the chip (quoted, at most 400 characters), `shift` docks it, escape dissolves an anchored companion; `click` closes the workbench's menus. `menu` is left to B6 and B7 (the pad menu belongs to the pads) |
| The paper theme | `notebook_runtime/theme.py`, served by the proxy | marimo's own CSS variables plus one rule (prose at the mockup's 14.4 px on 24 px) (page `#f7f5f0`, surface `#fdfdfc`, ink `#1f1e1c`, rules `#e3e0d8` and `#dcd7cc`, the purple voice `#5b4a9a`), Literata for prose and headings, JetBrains Mono for code, marimo's own face for its controls, the commit-point classes, and the faces served from the frame's origin |
| Proxy changes | `notebook_runtime/proxy.py`, `adapter.py` | The theme link and the bridge go into the page's head. The bridge posts to each of the app's origins in turn, so it no longer reads `location.ancestorOrigins`. marimo's "Reconnected" banner and toast are dropped on the WebSocket |
| A runtime-directory fallback | `notebook_runtime/sandbox.py` | A runtime directory too deep for a socket's path gives way to the temporary directory instead of refusing every notebook (NBF-3, found in B5) |
| The harness | `fixtures/desks/harness.tsx` (`?notebook=1`), `fakeCore.ts`, `scripts/desk_harness/notebook.py` | The lesson frame where the mockup's Teacher lesson state draws it, a real sandboxed session behind it, and 23 checks in headless Chromium |
| The visual-reference stage | `visual_reference.py --stage notebook` | Runs the notebook harness against the private reference set |

## Frame contract (for B6 and B7)

- **Mounting.** `<NotebookFrame owner path view? title? />` in any window. It opens on mount (a paused window
  waits until it is live) and never closes on unmount: the session belongs to its owner and the sidecar stops it
  after its idle minutes. A desk switch, a move or a remount rejoins the same session, so the kernel is kept.
- **Lifecycle.**
  - Offscreen or hidden: no polling; the frame stays mounted but `inert`, with `tabIndex = -1` and no pointer
    events.
  - Preview (an overview card): a placeholder reading "◆ notebook · title", never a second live frame (§11.4).
- **Frame attributes:** `sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"`,
  `referrerPolicy="no-referrer"`, an empty `allow`.
- **Margins:** even, inside the window's paper: 10 px above, 12 px at each side and below (the mockup's lesson
  body), with a 1 px `#dcd7cc` rule round the frame. Status lines use the interface face (JetBrains Mono).
- **The bridge host** (`NotebookBridgeContext`) receives only checked messages, with page coordinates. A
  well-formed message can still come from notebook code, since it shares the frame's origin. So the host treats
  every payload as untrusted text: it is quoted, never rendered as HTML, never run as a command.

## The harness (headless Chromium, a real sandboxed session)

`scripts/desk_harness/notebook.py`: **23 of 23 checks pass.**
- **Frame and theme:**
  - the frame mounts at the session's URL only once the session is ready, sandboxed as above;
  - its box is (859, 288, 516, 518), the mockup's lesson frame;
  - margins are 12 and 12;
  - the frame has no Tauri globals;
  - the page is `#f7f5f0`; headings and prose are Literata in `#1f1e1c`;
  - a commit point is a `#fdfdfc` card with a 3 px `#5b4a9a` edge;
  - Literata and JetBrains Mono load from the frame's own origin.
- **Bridge:**
  - the four messages reach the host; a selection's text and box arrive in page coordinates;
  - refused: forged kinds, malformed shapes, oversized text, a string payload, a wrong-origin `srcdoc` frame and
    a same-page post;
  - a well-formed post from notebook code is accepted as untrusted text.
- **Kernel and states:**
  - an edit round trip takes 21–23 ms;
  - a reloaded frame keeps its kernel (square stays 16) with no Reconnected banner;
  - each forced state says so in one line in the interface face, with resume or try again where they apply;
  - a paused frame is inert, and live again when back on screen;
  - a preview shows the placeholder.
- Chromium's local-network-access checks treat a page answered by Playwright as public and refuse its frames on
  127.0.0.1. The harness turns them off. The app's own origin is not subject to them, and WebKitGTK has none (B5
  below).

**Against the mockup** (`--ref`, `#tabs=distance,pad=3` at 1440 × 900): nothing differs. Each value below was
measured the same way on both screenshots:

| Measure | Mockup | Harness |
|---|---|---|
| Frame rule x | 859 to 1374 | 859 to 1374 |
| Frame rule top | 288 | 288 |
| Margins outside the frame | 12 and 12 | 12 and 12 |
| Page inside the frame | `#f7f5f0` | `#f7f5f0` |
| Paper round the frame | `#fdfdfc` | `#fdfdfc` |
| Content column inside the frame | 18 and 18 | 18 and 18 |

The DOM confirms the content column: marimo's app column sits 17 and 19 px in, and a card at 17.98 px.

Type, measured on the mockup's pixels (its notebook is a frame its capture did not measure):
- prose: two of its lines are as wide as Literata at 14.4 px (470 and 437 px of ink against 471 and 438 px of
  advance), 24 px apart. marimo sets 14.4 px on a 25.2 px line and has no variable for either. **Follow-up
  (NBF-2):** the mockup wins on looks, so the theme is now **variables plus one rule**, which sets marimo's prose
  to 14.4 px on 24 px. The harness checks it;
- the title is 32.4 px on 40.5 px, against a 41 px pitch (within the tolerance).

## B5: the packaged app on WebKitGTK

**How it ran.**
- **Display:** a debug build of the desktop app with an embedded frontend (custom protocol, `tauri://localhost`),
  inside `kwin_wayland --virtual`, a headless compositor that never shows on a screen, under its own
  `dbus-run-session`. No owner display, no owner bus, nothing installed.
- **Engine:** WebKitGTK 2.54.3 (`webkit2gtk-4.1`).
- **Vault and notebook:** a synthetic vault made with `learnloop init` in scratch, through the scratch wrapper,
  holding one probe notebook. The probe is an anywidget whose script runs inside the frame, as model-written code
  would.
- **Reporting:** the probe page and a temporary report command lived only in a scratch copy of the app, never in
  this branch.
- **Memory:** sampled as PSS of the run's own process tree.

| Item | Verdict | Evidence |
|---|---|---|
| Tauri's init scripts or IPC reaching a 127.0.0.1 subframe | **pass** | In the frame, `__TAURI_INTERNALS__`, `__TAURI__`, `ipc` and `__TAURI_POST_MESSAGE__` are undefined and there are no `webkit.messageHandlers` at all. `fetch("ipc://localhost/…")`, `fetch("http://ipc.localhost/…")` and `fetch("tauri://localhost/…")` fail with the frame CSP's `connect-src` violations reported, so no request is sent |
| The WebSocket relay | **pass** | The page renders through the proxy's relay. A model change from the frame reaches the kernel and back in 11 ms (26 ms on a remount). A remounted frame rejoins the same kernel |
| The frame CSP as WebKitGTK applies it | **pass** | `eval` is blocked (EvalError); WebAssembly compiles (`'wasm-unsafe-eval'`); an image to another host and a fetch to another port are blocked; `frame-ancestors` accepts the `tauri://localhost` parent |
| `location.ancestorOrigins` for the bridge | **pass; no longer needed** | WebKitGTK 2.54 has it (`["tauri://localhost"]`), but the bridge no longer reads it: it posts to each of the app's origins and the browser delivers only to the parent's. The app received the frame's `companion` message from `http://127.0.0.1:<port>`, with `event.source` the frame's window, and the host got it with the selection's box moved by the frame's position (+12, +10) |
| Time to interactive | measured | From mount to `starting`: 1.24 s (the sidecar's first request in this session). To `ready`: 1.75 s. To the probe's report from inside the rendered notebook, with about 0.6 s of the probe's own work: 5.5 s cold. A remount: 1.1 s |
| Memory | measured | The session: marimo server 61 MB and kernel 60 MB. WebKit's web process: about 105 MB without the frame and 393–446 MB with it, so the frame costs 290–340 MB there (WebKitGTK keeps the frame in the page's process). Network process 33–42 MB, app shell 110 MB, sidecar 141 MB |

**WebKitGTK differences found: none functional.** The one engine difference met is Chromium's: its
local-network-access checks, which only the harness meets. The run did surface NBF-3 (a runtime directory too
deep for a socket's path), fixed here.

**Not shown by B5:**
- the user manager's scope inside the virtual session (its private bus has no systemd, so sessions ran under the
  `prlimit` fallback and `memoryBytes` read null);
- the app's real Reader windows around the frame (the probe mounted the frame alone);
- a phone.

## Tests and commands

See the report for every command and result line. In short:
- vitest for the frame's states and lifecycle and the bridge's checks: forged, wrong-origin, malformed, oversized
  and class-instance messages refused;
- the harness, 23 of 23;
- the real-sandbox tests, still passing;
- new runtime tests for the theme, the font route, the reconnect notice, the frame allowlist's theme and font
  paths, and the runtime-directory fallback (fail-first shown against the previous `sandbox.py`).

## What B6 and B7 need

- **B6** (cells in pads):
  - pick the rendering (owner decision 2);
  - mount `NotebookFrame` with `pad:<id>` on the pad's notebook revision, opened on the first ⇧↵;
  - wire the `menu` bridge message to the pad menu labelled "the lesson", which belongs to `pads/*`.
- **B7** (lesson windows): mount `NotebookFrame` with `lesson:<id>` in RD9a's lesson window. The lesson header
  (mode buttons, the made-from line) is RD9a's; the frame takes the body's place.
- **NA2:** the commit gate renders `ll-commit`, `ll-held` and `ll-verdict`, which the theme already styles.

## Settings

The runtime's six defaults are unchanged (`docs/reviews/notebook-runtime-b1-b3.md`). New here:
- `theme.FONT_PACKAGES_ENV` (`LEARNLOOP_NOTEBOOK_FONTS_DIR`): where the frame's faces are read. By default it is
  the desktop app's installed `@fontsource-variable` packages. Without them the stacks fall back to system faces.
- `bridge.BRIDGE_TEXT_MAX` / `proxy.BRIDGE_TEXT_MAX`: 4,000 characters.
- `POLL_MS`: 500 ms while a session changes, 5 s while it runs.

## Judgment calls

- **The reconnect banner** is dropped at the proxy (the WebSocket message) rather than hidden by CSS, because
  marimo gives the banner no stable class. The adapter checks that marimo still sends it as a `banner` titled
  "Reconnected".
- **The bridge targets each allowed origin** instead of reading the parent's origin. That costs three dropped
  posts per message and removes the dependency on `ancestorOrigins`.
- **Prose only is Literata.** marimo's controls keep PT Sans, the mockup's accordion label face; the spec says
  "marimo's default text styling otherwise".
- **The harness serves its page as `http://localhost:1420`** (the development origin the frame CSP already allows)
  through Playwright's routing, rather than adding a test origin to the CSP.
- **The DeskShell bridge host is additive,** and `menu` is not wired: it belongs to the pads, which this step does
  not touch.

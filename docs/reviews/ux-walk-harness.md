# UX walk harness

Built for the end-of-queue UX journey audit, whose persona walks are done by agents in a sandbox
with no sockets: each must use the real application and see only the screen. Before this step
nothing could drive the desktop frontend outside the Tauri window. How to use it:
`scripts/ux_walk/README.md`. Tests: `tests/test_ux_walk_harness.py`.

## Step 0: what the shell does, the design, and the limits

### What `commands.rs` and the frontend's Tauri uses hold

`main.rs` registers **422** commands (the brief expected about 75), all defined in `commands.rs`:

| Kind | Count | What the Rust does |
|---|---|---|
| `sidecar_passthrough!` | 348 | forwards the frontend's `{input}` to one sidecar method unchanged (many dotted: `reader.ask`) |
| hand-written forward | 72 | builds one `json!` object from its camelCase arguments and forwards it (`get_feedback` defaults `recordOpen` to true); `load_vault` also retargets the vault watcher |
| more than a forward | 2 | `select_vault` (restart the sidecar on another vault, remember it, watch it) and `run_cli_command` (`populate-goal` runs on a second, isolated sidecar, then the primary reloads) |

Beyond commands, the shell has: the `llpdf://` and `llmedia://` protocols (original PDFs and
rendered animations from the vault's content-addressed stores, media with byte ranges); one pushed
event, `learnloop://vault-files-changed` (a native recursive watcher that calls the sidecar's
`refresh_vault_files` and emits the result); the vault choice (explicit, env, remembered, a
`fixtures-local/` vault, else `~/LearnLoop` created on first launch); the frame guard (refuses
commands from the sketch compartment's frame); the CSP; and two plugins.

The frontend's `@tauri-apps/*` uses, outside tests:

| API | Sites | Use |
|---|---|---|
| `invoke` (`api/core`) | 1 module (`src/api/client.ts`) | every command |
| `convertFileSrc` (`api/core`) | 3 (`ReaderScreen`, `PreparingView`: llpdf; `AnimationPlayer`: llmedia) | original PDFs, animations |
| `listen` (`api/event`) | 1 (`App.tsx`) | vault-files-changed |
| `getCurrentWindow` (`api/window`) | 3 (`ui.tsx` titlebar, `useCloseWithFlush`, `answerExposure`) | minimize/maximize/close, the close-time draft flush, focus/resize/visibility for answer exposure |
| `getCurrentWebview` (`api/webview`) | 1 (`useSourceFileDrop`) | files dropped on the window |
| `open` (`plugin-dialog`) | 7 calls in 6 modules | folder chooser (vault switch, new vault, header), file chooser (Add, Ingest) |
| `openUrl` (`plugin-opener`) | 3 (`ConnectAI`, `ChatGPTPlanSettings`, `FeedbackScreen`) | external links |

### Design (three parts)

1. **Browser mode.** `apps/learnloop-tauri/vite.browser.config.mjs` imports the production
   `vite.config.mjs` unchanged and aliases the six `@tauri-apps/*` modules to shims in
   `apps/learnloop-tauri/browser-harness/`, plus one injected script that keeps console errors for
   the analyst. No file under `src/` changed. The bundle builds to `dist-browser/` (gitignored) in
   about 3 s and the bridge serves it, so a walk runs no Vite process (a Vite dev server measured
   ~370 MB resident just serving the entry, 550 MB peak; the built bundle costs nothing at run time).
   `scripts/ux_walk/bridge.py` (standard library plus the venv's own `learnloop`) starts one
   `python -m learnloop_sidecar` for the walk's vault and does for each command what `commands.rs`
   does. The command table is parsed from `commands.rs` and `main.rs` at bridge start
   (`walk_commands.py`); a registered command whose body is not exactly one forward (or the known
   `load_vault` shape) makes the bridge refuse to start and the test fail, so a new command with a
   native step needs an emulation before walks run again.
2. **Walk driver.** `driver.py` owns one headless Chromium through chromedriver (W3C WebDriver over
   HTTP, standard library; no Playwright) at the Tauri window's 1380×880, or 390×844 with mobile
   emulation for the phone app. The persona's directory holds only `brief.md`, `walk`
   (`walk_client.py`, standard library, files only), `files/`, `observations/` and `channel/`.
   `walk <verb>` writes one action file under the next free number (written aside, then hard-linked
   into place, so two concurrent steps get two numbers) and waits for the driver's `done` file; the
   driver runs steps strictly in order and heartbeats every second so `walk` can tell a slow step
   from a dead driver. Observations come from `walk_perceive.py`: a page script returns the rendered
   DOM with what only a browser knows (visibility inside the viewport and clipping containers,
   display kind, live form state, focus, stylesheet-drawn text); the rest (roles, accessible names,
   states, reading order, numbering, dialogs first) is plain Python and tested on static pages.
   `start.py`/`stop.py` bring a walk up and down in two `systemd-run --user --scope` units.
3. **Walk vaults.** `make_vault.py`: `empty` (nothing; the app creates the library on first launch),
   `fresh` (bootstrap's `create_vault` plus one sample web page through the app's own `add_source`),
   `established` (`tests/helpers.py`'s basic vault grown into a five-LO linear algebra course with
   readable items and three goals, four weeks of history from the simulation runner, which drives a
   synthetic student through the real attempt pipeline with frozen clocks and a fixed seed, and a
   sample page added through the app with its first section marked read). Deterministic for a given
   `--anchor` date; built inside the walk directory; only `samples/` content.

### What browser mode cannot reproduce

- **Rendering engine**: Chromium 154 here, WebKitGTK in the app. Layout, fonts, focus rings and
  scrolling can differ; a finding about pixels needs a check in the real window.
- **Native file drops** onto the window (the browser never gets a path): walks use `upload`.
- **Window controls** (minimize, maximize), the native titlebar drag, and **external links**
  (recorded and named in the observation instead).
- **The frame guard** (`frame_guard.rs`): the sketch compartment's command refusal is not
  emulated; the CSP is (below).
- **Network**: the sidecar gets proxy settings that send every outside request to the bridge,
  which refuses it (logged as `outside_request_refused`), and Chromium resolves nothing but
  127.0.0.1. A pasted web link fails with the app's own "Couldn't reach the page"; a ChatGPT sign-in
  cannot complete.
- **The isolated `populate-goal` sidecar**: it runs on the one walk sidecar, so other requests wait
  for it (a walk keeps one sidecar).
- **Time**: the sidecar runs on the wall clock; build the vault on the walk's day.

None of these blocks the main journeys: Today, a session with feedback, the Reader (web pages and
PDFs through the llpdf protocol), ingest, goals, settings and the phone app all ran in the proof
walks below. Lessons were not walked (no lesson in the established vault yet).

### How model routes are faked

No provider type fakes answers outside pytest, so the walk uses an ordinary `openai_chat` profile,
`walk_fake`, whose `base_url` is the bridge's `/fake-model/v1` on 127.0.0.1: the bridge writes it into
the walk vault's `learnloop.toml` (and into the walk config directory's `ai_defaults.toml`, which a
vault created during the walk inherits) and sets `LEARNLOOP_AI_PROVIDER=walk_fake` in the sidecar's
environment, which is otherwise built from nothing (no keys, an empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`, a working directory with no `.env`). The app's real client, routing, receipts
and validation run; only the answer is made up, from the request's JSON schema (`fake_model.py`):
echoed request fields (`attempt_id`), first enum values, mid-range numbers, minimum arrays, and
`[walk fake model: <field>]` for words no model wrote. Two recipes and overrides: a grade gives half
credit on every rubric criterion with confidence 0.9 (`fake_answers.json`); decision and forecast
schemas (`RouterLLM*`, `*Forecast*`, `*Probability*`) are declined with HTTP 400, because the first
proof walk showed a made-up router choice emptying Today's plan. Decider and embedding routes are
not faked: they have no credential in the walk and behave as on an unconfigured install.

Before the browser opens the bridge resolves every AI route in the sidecar's own environment
(`route_check.py`, kept as `analyst/routes.json`): on the proof walks 64 routes were `fake`, 9
`unreachable` (the 8 decider routes and embedding, no OpenRouter key), 1 `unset`, 0 `live`. Any
`live` route stops the bridge in fake mode. `--models live` requires `--allow-live-route` and a
`--config-dir`.

**A walk on the owner's ChatGPT-plan route** would need: the owner's approval of the spend; a
config directory used only for walks with a plan sign-in in it (`LEARNLOOP_CONFIG_DIR=<dir>
LEARNLOOP_CHATGPT_SECRET_STORE=file uv run learnloop ai signin chatgpt`, the owner's own browser
flow; file storage because the walk environment has no session bus for the keyring); then
`start.py <name> --from fresh --models live --allow-live-route --config-dir <dir>`. In live mode the
bridge sets no proxy guard and no fake profile, and sets the vault's `active_provider` back to the
template's `chatgpt`. Not run here (no live call was made).

### Memory budget

Measured from the scope units (`analyst/memory.json`, systemd's `MemoryPeak`):

| Part | Peak |
|---|---|
| bridge + sidecar (`uxwalk-<name>-bridge`) | 226–493 MB (493 after a PDF was added and opened) |
| driver + chromedriver + headless Chromium (`uxwalk-<name>-driver`) | 312–674 MB (674 with the PDF reader open) |
| phone: proxy + phone host | 241 MB |
| phone: driver + Chromium at 390×844 | 376 MB |
| browser bundle build (once per start) | ~3 s; not measured |
| `make_vault.py established` (simulation + a bridge) | ~70 s; not measured |

So one walk stays near 1.2 GB; each unit is capped at 3 GB (swap 1 GB).

## Fidelity table

Every Tauri API the frontend uses:

| API | Fidelity | What the walker sees instead, when it differs |
|---|---|---|
| `invoke` | exact for 420 commands (below); 2 emulated | — |
| `convertFileSrc` (llpdf, llmedia) | emulated: same-origin bridge paths with the Rust handlers' rules (content-addressed names only, 4 MB media ranges, 416s) | — |
| `listen("learnloop://vault-files-changed")` | emulated: the bridge polls the vault every 0.4 s for the files the Rust watcher reports (`yaml/yml/md/toml/json`, the same ignored folders), waits for 160 ms of quiet, calls `refresh_vault_files`, pushes the result over server-sent events | refreshes can arrive up to ~0.5 s later than in the app |
| `getCurrentWindow` | emulated: focus/blur/resize/visibility from the page; `onCloseRequested` and `close` run the handlers as Tauri does | minimize/maximize change nothing; a completed close is announced ("The LearnLoop window closed") and the page stays |
| `getCurrentWebview().onDragDropEvent` | unavailable | never fires; use `walk upload` |
| `plugin-dialog` `open` | emulated: a request on the bridge; the observation says "A file chooser … is open", its filters and this person's files; `upload` answers (folders too: `--folder` picks or creates one in `files/`), `upload --cancel` or Escape closes it; other actions are refused while it is open | the chooser is described, not drawn; only `files/` is reachable |
| `plugin-opener` `openUrl` | unavailable | "The app asked to open <url> in your web browser (that does not happen on this walk)" |
| `select_vault` | emulated as in `SidecarManager::select_vault`, restricted to folders inside the walk | another folder: "Opening that folder is not available in browser mode" |
| `run_cli_command` | emulated: forwards; `populate-goal` on the one sidecar, then `reload_vault` | — |
| frame guard | unavailable | — |
| CSP | emulated: the app's CSP with its custom schemes mapped to the bridge's origin and Tauri's inline-script hashes | — |

Commands (generated by `python scripts/ux_walk/walk_commands.py`):

| Command | Sidecar method | Fidelity |
|---|---|---|
| `select_vault` | — | emulated: restarts the sidecar on the chosen folder (only folders inside the walk directory), then returns the vault summary, as SidecarManager::select_vault does |
| `load_vault` | `load_vault` | exact forward; the bridge's watcher then follows the vault |
| `run_cli_command` | — | emulated: forwards to the primary sidecar; `populate-goal` runs there too (the shell uses a second, isolated sidecar) and is followed by reload_vault, as the shell does |

The other 419 are exact forwards to the sidecar method of the same name (dotted for the 177 whose
Rust name maps to `reader.*`, `workbench.*`, `curriculum.*`, `notes.*`, `lesson.*`, `figure.*`,
`practice.*`, `adjudication.*` and `adaptive_difficulty.*`); the script prints the full list. Error
shapes follow `errors.rs` (a sidecar error keeps its typed code; a dead or hung sidecar gives
`sidecar_unavailable`/`sidecar_timeout` and is restarted on the next call; a missing required
argument gives Tauri's own "invalid args … missing required key …" string).

Artefacts of the walk a persona can meet, to keep apart from findings:

- Settings shows "LEARNLOOP_AI_PROVIDER= walk_fake is set in the environment and overrides every route
  below", and the library's status line names `walk_fake`.
- Every grade is "Partly right" with half credit on each criterion, whatever the answer; its
  evidence reads `[walk fake model: half credit on every criterion]`. Diagnosis text, hints, lesson
  turns and figure briefs are schema-shaped placeholders.
- Decision routes are declined, so the plan and the router act as with no decision model.
- No network: link adds fail; nothing is fetched.

## The proof walks

All through `walk` only; observations and screenshots kept outside the repository (the orchestrator
can read them in the step's scratch directory, `proof-walks/`).

**Established vault, desktop** (14 steps, every one ok; 1.0–6.8 s each):

1. `look`: Today, "Wednesday afternoon", the minute choice (25 m checked), "About 25 minutes suggested
   today: 1 short question from earlier days, then a step further on Eigenvalues and eigenvectors and a
   step further on Dot product", the goal line "Midterm: eigenvalues to variance · Dec 9 · on track".
2. `click "Begin"`: the session's first item, "State the spectral theorem for real symmetric matrices."
   with `[13] textbox "answer" placeholder "Write what you can — $math$ works."` and Submit, Hint,
   I'm stuck, Ask, Skip.
3. `type … --into answer`; 4. `click "Submit"`: feedback "Partly right ◇ graded by AI", "You wrote …",
   "A full answer …", the two criteria (◐ / ✗), Next, "Try a similar one (t)".
5. `click "details ▸"`: "how sure the grader was: 0.90", each criterion with the fake evidence line,
   "The pattern analysis for this answer did not complete; your grade above stands.", and "THIS
   CARD: reword · split in two · retire · ↓ easier · ↑ harder · ◊ teach it" read as `clickable`
   (pointer cursor, no role: an accessibility finding for the audit, not a harness artefact).
6. `say` (logged only).
7–8. Reader: the library view, then the book, with typeset math read as TeX ("$A=QDQ^T\text{,}$"),
   the reading guide and its depth choices.
9–10. Today, the goal's details: due in 21 days, predicted recall 82% against 80%, facets examined,
   pace, "▸ plan around my week", "+ new goal" — and "LearnLoop could not confirm whether this action
   completed", a real failure (bug ledger **E-2**: `get_goal_report_series` hits
   `attempt_diagnoses`' append-only trigger once an attempt with a diagnosis exists).
11–12. "⋯" menu (Settings, Under the hood, Switch library, Keyboard & help), then the Settings
   dialog, read first with the page behind it; its model comboboxes have no accessible name.
13–14. Scroll inside Settings; Escape.

**Empty start, desktop** (9 steps): the first-run screen ("Drop a book, paper or lecture here", Choose a
file…, paste a link); Today with "Nothing to plan yet"; Library; Choose a file… opened the chooser
("Add to your library", its filters, this person's three files); clicking Today was refused while it
was open; `upload notes-that-do-not-exist.pdf` was refused with the list of files; `upload
mit-18.06-spring-2010-quiz1.pdf` added the quiz and the Reader opened it, the PDF itself served
through the llpdf emulation and read from pdf.js's text layer ("18.06 Quiz 1 March 1, 2010 Professor
Strang"). `replay.py` reran these steps on a second empty walk with the same outcomes.

**Fresh start, desktop**: the sample page in the library ("Questions wait for your OK"); pasting
`https://example.org/notes` gave the app's "Couldn't reach the page" with Try again / Remove, and the
analyst log shows the refused `CONNECT example.org:443`.

**Phone** (established vault): the pairing page as after a QR scan ("Pair this device", Pair), then
"Paired. Keep this token private…", "Open LearnLoop", then the phone's Today ("About 25 minutes
suggested today: more to choose as you go.", 10–60 min, Begin, the Today/Read/Capture/Progress bar).

Harness fixes the walks forced: the observation drew the placeholder of a contenteditable answer box
(stylesheet `::before` text), read KaTeX as TeX and PDF text layers as lines (CSS blockifies absolutely
placed spans), reads a modal dialog first, treats determinate progress bars as content not "busy",
sizes the page (not the window) to 1380×880, and keeps a heartbeat thread so a long `wait` is not
mistaken for a dead driver.

## How a sandboxed agent uses it

The orchestrator runs `start.py` outside the sandbox and gives the agent only `persona/`. The agent runs
`./walk look`, then `./walk click 7`, `./walk type "…" --into answer --enter`, `./walk upload notes.pdf`,
`./walk say "…"` and so on, reading each printed observation (and the PNG if it can see images). It never
needs a socket: `walk` writes `channel/action-NNNN.json` and reads `channel/done-NNNN.json`. The analyst
then reads `analyst/steps.jsonl` beside the persona's notes.

## Tests and checks

- `tests/test_ux_walk_harness.py`: 22 tests without a browser (the command table against
  `commands.rs`/`main.rs` and the frontend's calls; a new non-forward command stops the bridge;
  argument mapping and Tauri's missing-argument error; the observation on static pages, nothing
  imperceptible in it, modal dialogs first, math and scrolling, busy; the file protocol's order under
  concurrency, gaps, timeouts and a dead driver; the `walk` command line; replay; the fake model's
  schema answers, grade recipe and declines; the CSP, media ranges and watcher) and one browser test
  (`ux_walk_browser`, skipped unless `LEARNLOOP_UX_WALK_BROWSER=1`; it passed when run).
- `npm run typecheck`, the shims' own `tsc -p browser-harness/tsconfig.json`, `npm run frontend:build`
  with the production bundle's 84 file hashes identical before and after.
- The landing checks named in the step brief; results in the step's report.

## Not covered

- The established vault has no captured note and no finished lesson yet; the Teacher's screens and
  lessons were not walked.
- "Fresh" adds a web page, which needs no model; ingesting a PDF or building questions runs on the fake
  model's placeholders.
- No walk on the ChatGPT-plan route; no TUI, MCP or multi-device walk; native drag and drop; the Vite
  dev-server mode (`WALK_BRIDGE_PORT`) was not exercised.
- The phone walk stopped at the first screen.
- Why the feedback's "pattern analysis" did not complete on the fake model was not investigated.

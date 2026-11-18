# UX walks: the real desktop app in a browser, driven through files

A persona agent (for example a Codex worker in a sandbox with no sockets) uses
LearnLoop as one person would: it reads the screen as text and a screenshot,
and acts with a `walk` command that only writes and reads files. Everything
the person cannot perceive goes to a separate analyst log. The record of how
this was built and how faithful it is: `docs/reviews/ux-walk-harness.md`.

```
persona agent ──walk──▶ persona/channel/action-NNNN.json
                                │
                driver.py ◀─────┘  (headless Chromium via chromedriver, W3C WebDriver)
                   │  writes persona/observations/NNNN.txt + NNNN.png, then channel/done-NNNN.json
                   ▼
   browser-mode frontend (apps/learnloop-tauri, vite.browser.config.mjs)
                   │  @tauri-apps/* shims → HTTP on 127.0.0.1
                   ▼
            bridge.py ── stdio JSON-RPC ──▶ python -m learnloop_sidecar (the walk's vault)
                   └── /fake-model/v1 (the vault's walk_fake profile points here)
```

## Start and stop a walk

From the repository root, with the venv set up and `npm ci` done in
`apps/learnloop-tauri` (no download; nothing here adds a dependency):

```bash
uv run python scripts/ux_walk/start.py student-1 --from established --brief my-brief.md
uv run python scripts/ux_walk/stop.py student-1
```

- `--from empty`: no library yet; the app creates it on first launch (the first-run screen).
- `--from fresh`: a new library with one small web page from `samples/` added through Add.
- `--from established`: a small linear algebra course with four weeks of synthetic practice
  (misses, primed retries, follow-ups), three goals (a dated exam, an open goal, a paused goal), due and
  overdue items, and a web page whose first section is marked read (`make_vault.py`; build it on the walk's day).
- `--phone`: the phone app (`learnloop_mobile`) at a phone viewport, paired as if its QR code was
  scanned (needs `npm ci && npm run build` in `apps/learnloop-mobile` once).
- `--files a.pdf b.html`: this person's own files for `walk upload` (default: three samples).

The walk lives in `fixtures-local/ux-walks/<name>/` (gitignored):

| Directory  | Who reads it | What |
|---|---|---|
| `persona/` | the persona agent, and nothing else | `brief.md`, `walk`, `files/`, `observations/`, `channel/` |
| `analyst/` | the analyst only | `steps.jsonl` (each step: action, target, time, observation, failed bridge calls), `console.jsonl`, `bridge.jsonl` (every call, every fake-model request, refused outside requests), `routes.json`, `sidecar.log`, `memory.json` |
| `vault/`   | — | the walk's own synthetic vault |
| `run/`     | — | the processes' homes, config, caches |

Each long-running part runs in its own `systemd-run --user --scope` unit capped at 3 GB
(`uxwalk-<name>-bridge` holds the bridge and the sidecar; `uxwalk-<name>-driver` holds the
driver, chromedriver and Chromium). `stop.py` records their peak memory and stops exactly those.

## The `walk` verbs

```
walk look                                   what is on the screen now
walk click 7 | click "Start session" | click --role button "Next"
walk type "text" [--into 4|"label"] [--enter] [--clear]
walk key Enter | Escape | Tab | Shift+Tab | Control+k | ArrowDown
walk scroll down|up|left|right [--page | --lines N] [--in 3]
walk back                                   browser history (the desktop window has no back button)
walk hover 5
walk wait 3 | wait --for "Saved" --limit 20
walk upload notes.pdf | upload --folder my-library | upload --cancel
walk resize 1024 768 | resize desktop | resize phone
walk say "I expected a Save button here"    a note for the record; the app never sees it
```

Numbers refer to the latest observation only. `upload` answers an open file chooser (the app's
native dialog becomes a request the driver shows: "A file chooser is open over the app") with a
file from `files/`; while one is open other actions are refused, as a modal dialog would.

## What an observation contains

`observations/NNNN.txt`, printed by `walk` as well, and `NNNN.png` (the viewport):

```
Step 3: click [17] button "Begin ↵"
Took: 4.4 s
Busy: no
Window title: LearnLoop
Focus: nothing in particular
Dialog open: dialog "Settings" (modal)          (when one is)
Notice: status: Saved                            (role=status/alert, live regions)
--- screen ---
… visible text in reading order; a modal dialog first, then "--- behind the dialog ---" …
[13] textbox "answer" placeholder "Write what you can — $math$ works."
[14] button "Submit ^↵"
--- off screen ---
More below (scroll down).
```

Each element a person can act on gets a number, its role (from the element or its ARIA role;
`clickable` for something with a pointer cursor and no role), its accessible name and its state
(disabled, checked, expanded/collapsed, pressed, selected, current, focused). Typeset math reads
as its TeX. Only what is visible inside the viewport and its scroll containers is printed: no
ids, class names, test ids or hidden text. "Busy" is the bridge's calls in flight plus
indeterminate progress bars and `aria-busy` regions on screen.

## Fidelity, briefly

The frontend is the production code; only `@tauri-apps/*` is swapped. Of the 422 Tauri commands,
420 are exact forwards (the table is parsed from `commands.rs` at bridge start, and the bridge
refuses to start if a command's body is not a plain forward it knows); `select_vault` and
`run_cli_command` are emulated. Rendering is Chromium, not WebKitGTK. Not available: dropping
files from the desktop (use `upload`), window minimize/maximize, opening external links (the
observation says which URL would have opened), the frame guard for the sketch compartment, and
any network access (a pasted web link fails with the app's own "Couldn't reach the page"). The
full table is in the record.

## Model routes

Faked by default. The bridge serves an OpenAI-compatible endpoint and makes the vault's provider
`walk_fake`, an ordinary `openai_chat` profile pointing at it, with `LEARNLOOP_AI_PROVIDER=walk_fake`
in the sidecar's otherwise empty environment, so the app's real client, routing and validation run.
Answers are built from each request's JSON schema (`fake_model.py`): words no model wrote read
`[walk fake model: …]`, a grade gives half credit on every rubric criterion, and decision and
forecast routes are declined so the app takes its no-model path (`fake_answers.json`). Decider and
embedding routes have no credential in the walk and behave as on an unconfigured install. The bridge
checks every route before the browser opens (`analyst/routes.json`) and refuses to start if one would
reach a live model.

A walk on the owner's ChatGPT-plan route (the owner decides at launch; it spends plan usage):

```bash
mkdir -p ~/learnloop-walk-config
LEARNLOOP_CONFIG_DIR=~/learnloop-walk-config LEARNLOOP_CHATGPT_SECRET_STORE=file uv run learnloop ai signin chatgpt
uv run python scripts/ux_walk/start.py student-live --from fresh \
    --models live --allow-live-route --config-dir ~/learnloop-walk-config
```

The sign-in is the owner's own browser flow, into a config directory used only for walks (never
`~/.config/learnloop`); the tokens go to its file store because the walk's environment has no
session bus for the OS keyring. In live mode the bridge passes no proxy guard and no fake profile,
and sets the vault back to the template's `chatgpt` profile.

## Rerun a recorded walk

```bash
uv run python scripts/ux_walk/start.py student-1-after --from established
uv run python scripts/ux_walk/replay.py fixtures-local/ux-walks/student-1 student-1-after
```

`replay.py` sends the old walk's steps (from `analyst/steps.jsonl`) through the new walk's file
protocol; a step that named an element by number is sent by the role and name it resolved to.

## Development

Hot reload against a running bridge: `WALK_BRIDGE_PORT=<port> npx vite --config vite.browser.config.mjs`
in `apps/learnloop-tauri` (port 1421). The production build, `npm run dev`, `npm test` and the Tauri
app never read `vite.browser.config.mjs` or `browser-harness/`.

Tests: `tests/test_ux_walk_harness.py` (no browser; in the landing gate). Its one browser test runs
only with `LEARNLOOP_UX_WALK_BROWSER=1`.

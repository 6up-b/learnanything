# UX Phase 2: the shell

**Stage:** `ux-phase2-shell`, branch `ux/phase2-shell` (worktree `learnanything-ux2`), base `c80c54cbb` (main, the RW7a landing, migration head 217).
**Spec:** `docs/specs/ux_learnloop_v1.md` §5 (places, Under the hood, keys), §7.7, §7.9, §8.5 and §10 Phase 2 (items 2.1–2.5), plus the findings Phase 1's usability rounds deferred to Phase 2 (§10 "Deferred", row 2).
**Owner direction:** owner-queued 2026-10-13, re-confirmed 2026-10-21 as Track P. Frictionless by default, the glass box on demand; a live change behind a kill switch, no shadow stage.
**Codex review fix round:** `ux-phase2-shell-codex-review.md` (F1–F9 fixed). It supersedes this record where they differ: Data opens read-only behind *allow edits* and the database leaves the simple shell's file trees (Q3 answered with spec Q18's default), the writer no longer duplicates waiting error-type proposals (Q4 and its open item resolved), screens can hand the shell a structured error and a retry (D5 narrowed), and the notice, palette and Reader-ask behaviour of §2.4–2.5 is as that file describes.
**Fix round 2 (orchestrator):** §11. The whole-stage verify `20261021-114726-Jrt7sA` reopened five items, all fixed there. F6 is accepted at the writer as a workflow-persistence change, a recorded deviation from "display and navigation only".
**Fix round 3 (orchestrator):** §12. The verify `20261021-130232-Uk06Al` reopened four items; the notice and retry class is closed structurally (identity by source, self-contained retries that report a request that ran), and startup is the base shell until the snapshot names the shell.

## 0. The plan (written before the code)

**The rule of the stage.** Display and navigation only. No sidecar data contract changes beyond the one config key, no evidence, scheduling, grading or replay change, and no algorithm successor. Demoted screens mount unchanged; only their entry points move. The Reader stays as it is inside (Reader stages land in parallel); `ReaderScreen.tsx` is touched only if the nav integration strictly needs it.

**The switch.** `[ui] shell = "simple" | "classic"` (default `"simple"`, Q17). `"classic"` keeps the ten-tab shell of `c80c54cbb` exactly: the nav markup, its keys, the red in-flow toast, the palette's plain-word CLI pass-through. Vitest pins classic against snapshots recorded on the base before any change. The sidecar sends it in the app snapshot (`config.ui.shell`) next to Phase 4's `practiceFeedback`; nothing in Python reads it.

**2.1 The nav.** `LearnLoop  Today · Library · Reader · Progress   [+ Add]  ^K  ⋯`.
- Today is home and covers the old Start and Today (Start while no session is open, Today once one is; Phase 3 merges them). Library is Phase 1's place. Reader is the Reader. Progress is today's Graph screen, unchanged (Phase 5 reshapes it).
- `⋯` holds Settings, Under the hood, Switch library (the vault chip's recents and "open another library…", plus "New library…"), and Keyboard & help (a list generated from the key map).
- The settings chip and the vault chip leave the bar. One plain line, *Grading isn't working · Fix*, shows only when grading is down (not for manual grading).
- `Alt+1…4` go to the four places. The old `Alt+5…0` keep working and open the matching Under-the-hood tool. Remember the last place (and the open book) across restarts, per machine.
- One shared key map, `app/keymap.ts`: every shell-level binding as data, per shell, with its documented replacement; App's listener and `useGlobalAdd`'s `Ctrl+O` dispatch through it. Screen-level keys stay with their screens; a test enumerates the bindings and checks for conflicts, including a scan of screen sources for modifier chords the shell also binds.

**2.2 Under the hood.** A new `screens/UnderTheHoodScreen.tsx`: a left list of tools, the last tool used on the right, each under a plain title with its old name in small type and its own count. The tools mount today's components unchanged: Imports & builds (Ingest), Study-map changes (Proposals), Subjects & topics (Registry), Concept graph editor (Graph), Analyst views (the knowledge field: well, terrain, strata), Mistake history (Review), Calibration (start a full calibration session, as the palette's `calibrate`), System health (Maintain, with adjudication), Data (the SQLite browser on `state.sqlite`), Files (the Library screen's vault tree and payload editor), Inspector (open any id), Spend & AI routes (opens Settings), and Golden path only while `SHOW_GOLDEN_PATH`.

**2.3 Notices.** A notice system replacing `app/notices.ts`'s stopgap: errors red, one sentence, *Try again* when the error is `retryable` and the shell knows the action, *details ▸* with the code; notices neutral, small, at the bottom edge, auto-dismissing, and cleared once resolved (a notice can name what resolves it, such as "a session began"). While the Reader has a book open, no notice shows: notices are held and delivered at the next destination. `errors.ts` gains the `kind: "error" | "notice"` type.

**2.4 The palette.** In the simple shell it lists plain commands first (add a book, continue reading, start today's plan, check what I already know, open settings, under the hood, the places and the tools), filtered as you type. The learnloop shell grammar and the CLI pass-through need a leading `>`; plain words never run a CLI command.

**2.5 The switch** as above.

**Deferred findings carried (§10 row 2).**
- The ten-tab bar and Ingest's developer words: the bar becomes four places; Ingest moves under the hood (which keeps its terminal voice).
- The build-plan modal's Escape steps back instead of closing: Escape closes it in the simple shell; *← back* still steps back.
- Proposals grows on every practice, with duplicate error-type proposals: find out whether it is display or data. If data, record it and fix only the display, saying why.
- Notes & files opens previewing `vault.lock`: the first selection skips lock and database files.

**Tests, fail first.** Vitest component and interaction tests for the nav, the key map, Under the hood, the notices (including held in the Reader and delivered at the destination), the palette and the classic switch; Python tests for the config key and the app snapshot. Then a real-UI look through the usability harness (fake AI, a backup-API copy), with screenshots described here.

## 1. The switch, and why there is no successor

`[ui] shell = "simple" | "classic"` (on the existing `UiConfig`, default `"simple"`). The sidecar sends it in the app snapshot next to Phase 4's switch (`config.ui = {practiceFeedback, shell}`); the desktop reads it through `app/algoConfig.ts` (`algoConfig().shell`) and `app/shell.ts` (`shellMode()`, `simpleShell()`). A test pins `learnloop_sidecar/context.py` as the only Python module that names `ui.shell`. No grading, scheduling, evidence, projection or replay path reads it, so under the owner's ruling (live changes behind kill switches) there is **no algorithm successor**. The 20 defaults snapshots in `config/template.py` were recomputed only because the effective config gains the key (template `.pyc` cleared first; one comment block on mvp-0.9, one line on every other entry). A change takes effect on the next vault load.

`"classic"` keeps the base shell (`c80c54cbb`) exactly. The nav's markup is pinned by two snapshots recorded on the base before any change (`components/__snapshots__/ShellNav.test.tsx.snap`, `app/__snapshots__/App.shell.test.tsx.snap`); its keys are the key map's classic rows, which reproduce the base listener's predicates (Ctrl+P and Alt+S even while typing, `:` and Alt+digit only outside text, Alt+8 unbound while Golden Path is hidden); its single red in-flow toast, the session-first stopgap and the palette (plain words run learnloop commands) are unchanged; and each carried finding's fix is gated to the simple shell, so classic shows those three screens as before (tests pin each). Two invisible differences: the app writes `learnloop.shell` to localStorage (so the window opens in the last shell before the library loads), and the app snapshot carries the new key.

## 2. What was built

| Commit | What |
|---|---|
| `f97b3ad13` | The plan (§0), before any code. |
| `c215d00a0` | Fail-first tests. On the base: vitest 11 files, **36 failed and 7 passed** (the 7 are the classic pins, which must pass on the base, and recorded the two snapshots there); `tests/test_ux_phase2_shell.py` **4 failed**. |
| `955ee375d` | The shell, the key map, Under the hood, the notices, the palette, the carried findings, the sidecar key and the recomputed snapshots. |
| `19c6b0a72` | Five fixes from the usability-harness walk (§6), each pinned by a test. |
| `d44597470` | The references regenerated (`Config - ui`; 945 → 946 leaves in the prose counts); 0 validator errors. |

### 2.1 The nav (`components/ShellNav.tsx`, `components/ui.tsx`, `app/shell.ts`, `app/App.tsx`)

`LearnLoop  Today · Library · Reader · Progress   [+ Add]  ^K  ⋯` with plain labels; each place's Alt key is in its tooltip (Q10), the current place has `aria-current`. No badge, no vault chip and no settings chip in the bar (§5.2, §7.8).
- **Places over tabs.** A place is a view over the shell's existing tabs, so every existing `setTab("ingest")` (Quick add, the new-library wizard, the book card's *details*) keeps working and lands under the hood. Today is Start while no session is open and Today once one is (Phase 3 merges them); Library is Phase 1's place; Reader is the Reader; Progress is today's Graph screen, unchanged (Phase 5 reshapes it).
- **⋯** holds *Settings* (Ctrl+,), *Under the hood*, *Switch library* (the recents the vault chip listed, *Open another library…*, *New library…*, which opens the existing wizard) and *Keyboard & help* (generated from the key map). Escape closes it without reaching the screen beneath; Enter and Space stay in the menu (screens bind them on the window).
- **One plain line, only when it matters** (§7.8): *Grading isn't working · Fix* (opens Settings) appears only when an AI is connected, grading isn't manual, and the grading provider isn't ready. A fresh library with no AI shows nothing there (its Library already says *Connect an AI*).
- **Remember the last place** (per machine, best effort, every storage access in try/catch): the place, the Under-the-hood tool, and the book open in the Reader (per library; the Reader's own per-book reading position does the rest). On launch, an open practice question still wins, and an empty library still lands on the Library's welcome.
- **Wrap-up offer** (RW6a): in the simple shell Start is Today, so leaving the Reader for it shows the offer there too.

### 2.2 One key map (`app/keymap.ts`)

Every shell-level binding is data, per shell: id, keys, label, action, chord, whether it fires while typing, and which listener owns it. App's one window listener dispatches through `matchShellKey`; `useGlobalAdd` reads its Ctrl+O chord from the map (its paste listener and enabling rules stay); Keyboard & help lists the rows; `keymap.test.ts` enumerates them.

| Keys | Simple shell | Classic (as the base) |
|---|---|---|
| Alt+1 … Alt+4 | Today · Library · Reader · Progress (also from inside an answer box) | Start · Today · Graph · Ingest |
| Alt+5 · 6 · 7 · 9 · 0 | Study-map changes · Subjects & topics · Library · Reader · System health (the old tabs, under the hood where they went) | Proposals · Registry · Library · Reader · Maintain |
| Ctrl+K | the palette (new) | — |
| Ctrl+P, `:` | the palette | the palette |
| Ctrl+, | Settings (new) | — |
| Alt+S | Settings | Settings |
| Ctrl+O, Ctrl+V | Add (useGlobalAdd) | Add |

Every classic shortcut either works unchanged or has a documented replacement (`CLASSIC_REPLACEMENTS`, shown under *Keys that moved* in Keyboard & help); a test fails if one has neither. No two bindings share a chord in either shell. A source scan fails if any screen binds a Ctrl chord the shell also binds unless it is a listed scoped override: the one today is the Reader workbench's Ctrl+K (*Check my work*, with help on), whose element-level handler stops the event, so the palette stays shut there (Ctrl+P and `:` still open it). The simple listener also leaves alone any key a screen already handled (`defaultPrevented`). Screen keys stay with their screens ("replacing scattered listeners where practical": the two shell-level listeners moved; the 50-odd screen listeners are each screen's own and stay).

### 2.3 Under the hood (`screens/UnderTheHoodScreen.tsx`, `screens/underhood/tools.tsx`)

A left list of tools (each with its own count: Study-map changes shows the pending proposals, System health the Maintain badge), and on the right the tool under its plain title with *was …* in small type (the old name is also the row's tooltip). The App mounts each screen with the props it always had:

| Tool | Was | Mounts |
|---|---|---|
| Imports & builds | Ingest | `IngestScreen` |
| Study-map changes | Proposals | `ProposalsScreen` (+ the repeat marks, §2.6) |
| Subjects & topics | Registry | `RegistryReviewScreen` |
| Concept graph editor | Graph · edit | `GraphScreen` unchanged (it opens in view mode; its own *edit* toggle) |
| Analyst views | Graph · knowledge field | `KnowledgeMapView` (terrain, well, strata) |
| Mistake history | Review · learnloop diff | the `ReviewScreen` overlay: opens when the tool is picked, not when Under the hood is reopened on it |
| Calibration | calibrate | a *start calibration* button (the palette's `calibrate` over all open episodes; needs a session); `> calibrate <goal_id>` still takes a goal |
| System health | Maintain | `MaintenanceScreen` (adjudication from it, as before) |
| Data | SQLite browser | `SqliteBrowser` on the library's `state.sqlite`, found in the vault tree |
| Files | Library · Notes & files | `LibraryScreen` (the vault tree and the proposal payload editor; Proposals' ⤢ hand-off lands here) |
| Inspector | learnloop show | an id box, plus the ids on screen recently; opens `InspectorOverlay` |
| Spend & AI routes | Settings · AI | a pointer to Settings (Phase 6 gives it a page) |
| Golden path | Golden Path | listed only while `SHOW_GOLDEN_PATH` |

The old tabs are their own tools (`setTab("ingest")` shows Under the hood on Imports & builds); the error boundary resets per tool.

### 2.4 Notices (`app/notices.ts`, `components/NoticeHost.tsx`, `errors.ts`)

- **Two kinds** (`errors.ts` `MessageKind`). An error is red (`role="alert"`), one sentence, *Try again* when the sidecar said `retryable` **and** the shell knows the action (opening today's plan reading, *back to where you studied this*, changing the grading provider), *details ▸* with the error code, and stays until dismissed or retried. A notice is neutral (`role="status"`), small, at the bottom edge, and leaves 5 s after it is first on screen. At most three at once; a repeated message shows once.
- **Cleared once resolved.** A notice can name what resolves it. Every "Start a session first" notice (`sessionNotice`) is dropped the moment a session begins, shown or still held. This replaces Phase 1's stopgap, which classic keeps.
- **Held during reading, delivered at the destination.** While the Reader has a book open (and no exam or calibration pre-empts it), no notice shows: it waits, unaged, and its 5 s start at the next place. Errors still show.
- **Where they come from.** The App's `onError` is the error path (every screen's error string); grading-provider changes, *Already in your library*, the ask-tutor refusals, Settings', Ask's and the wizard's toasts and Quick add's "Study map building" are notices. While Settings is open its own notification line shows the latest one, as before.

### 2.5 The palette (`components/CommandPalette.tsx`)

In the simple shell it opens on plain commands, filtered by every word typed (labels, hints and old names: "proposals" finds *Study-map changes*): *Add a book, paper or video* (Ctrl+O) · *Continue reading* (the open book, else the shelf) · *Start today's plan* · *Check what I already know* (Progress, where a topic's inspector offers it) · *Open settings* (Ctrl+,) · *Under the hood* · *Go to* each place (Alt+1…4) · *Ask the tutor about this* · *Keyboard & help* · *Open another library…* · *New library…* · then each Under-the-hood tool. ↑↓ choose, ↵ runs. Plain words that match nothing run nothing: the line says *No command matches "doctor". To run it as a learnloop command, start with >: > doctor*. After `>` it is the learnloop shell exactly as before (grammar, completions, history, CLI pass-through), and it stays in the shell after a command so the output stays on screen. Classic keeps the palette as it was.

### 2.6 The carried findings (§10 "Deferred", row 2)

| Finding (round 1) | What was done |
|---|---|
| The ten-tab bar (M-e) | Four places; the four demoted tabs are under the hood. |
| Ingest's developer words ("learnloop[pdf]", "chatgpt_plan") (M-e) | Ingest is *Imports & builds* under the hood, which keeps its terminal voice (§7.7, Phase 7.3); the learner no longer meets it on the way to reading. Its copy is unchanged. |
| The build-plan modal's Escape steps back instead of closing (M-e) | `OutlinePlanFlow`: in the simple shell Escape closes the modal from either step (the hint reads *esc close*); *← back* still steps back. Classic keeps the stepping. |
| Proposals grows on every practice, with duplicate error-type proposals (M-h) | **A data issue, recorded; display fixed.** `persist_unknown_error_type_proposals` (`diagnosis/error_taxonomy.py`, called from grading in `attempts.py` and `regrade.py`) checks the vault's accepted error types and the built-ins, not the proposals still waiting, so every grading that names the same new error type writes another batch for it. The harness copy of the tracked `linear_algebra` fixture shows it: `local_slip` waits 4 times, `representation_notation_error` twice. Fixing it at the source changes what grading writes, which this display-only stage may not do; it is queued as an open item (§9). In the simple shell the list now marks it: the first waiting proposal of an entity says *proposed 4×*, each later one *repeat*. The nav badge that made the growth visible on every practice is gone (Study-map changes carries its count under the hood). |
| Notes & files opens previewing `vault.lock` (m8) | `LibraryScreen`: in the simple shell the first selection is the first Markdown note, else the first file that isn't a lock or a database (`initialFilePath`). The harness copy opens on `profile/goals.md`. |
| The notice that clears once resolved (2.3) | §2.4. |

## 3. Deviations

| # | Spec says | Built | Why |
|---|---|---|---|
| D1 | Today = Start + Today merged. | Today shows Start while no session is open, Today once one is. | The merge is Phase 3.1. |
| D2 | Progress opens on the well. | Progress is the Graph screen, unchanged (it opens on the concept map; the well is its *knowledge field*). | Phase 5.1/5.3. |
| D3 | The vault tree, payload editor and SQLite leave the Library (§5.3). | Under the hood has Files and Data; the Library's *Notes & files* tab (Phase 1) is still the same screen. | Splitting `LibraryScreen` changes a demoted screen inside; both entry points work meanwhile. Q2. |
| D4 | Inside the Reader no notice appears; errors show on the action's control. | Notices are held; errors still show (red, bottom edge). | Errors on the Reader's own controls are the Reader stages' work; hiding an error would lose it. Q6. |
| D5 | Errors offer *Try again* when `retryable`. | For the shell's own actions (plan reading, *back to where you studied this*, the grading provider). Screens report a string through `onError`, and keep their own retry controls. | Retrying a screen's action needs the screen; screens are unchanged. |
| D6 | Spend & AI routes: spend by route, caps, latency. | A pointer to Settings. | Phase 6 (Settings, Advanced). |
| D7 | The health indicator only when something the learner uses is broken (grading or tutoring). | Grading only, and only with an AI connected. | Tutoring readiness isn't in the snapshot; Phase 6.1. |
| D8 | ⋯ → New library… is a two-field dialog. | It opens the existing wizard. | §7.8 / Phase 6. |
| D9 | — | The place keys work while typing in the simple shell. | Harness walk: practice keeps the focus in its answer box. Alt+digit types no text on Linux/Windows, and Option+digit on a Mac gives another key, so it never matches. |
| D10 | Demoted screens unchanged. | Three of them change a few lines each, simple shell only: the build-plan modal's Escape, the Notes & files first selection, the Proposals repeat marks. | The stage carries those findings; gating them keeps classic exact. |
| D11 | Plain commands: *check what I already know*. | It goes to Progress, where a topic's inspector offers the quick check. | The learner card on a bead is Phase 5.2. |

## 4. Before and after, per workflow touched (friction notes)

| Workflow | Before (`c80c54cbb`) | After (simple) | Friction left |
|---|---|---|---|
| **Move between places** | Ten tabs, `[n]` labels that are really Alt chords; Alt+digit dead inside an answer box. | Four places, plain labels; Alt+1…4 from anywhere, an answer box included. | Today is two screens under one name until Phase 3 (Start's *ready to practice?* without a session, the old Today with one). |
| **Reach an owner tool** | One click on its tab. | ⋯ → Under the hood (opens on the last tool) → tool: 2 clicks, or Alt+5/6/0, or the palette ("imports"). | Imports & builds is one click further for the owner; the old Alt+4 now means Progress. |
| **Switch library** | Vault chip → recents (2 clicks). | ⋯ → a recent (2 clicks). | The current library's name is no longer visible in the bar (only in ⋯). |
| **Open settings** | Settings chip or Alt+S. | ⋯ → Settings, Alt+S or Ctrl+,. | The always-green/red dot is gone; only grading trouble shows. |
| **Run a command** | Plain words could run a CLI command. | Plain commands first; CLI behind `>`; output stays on screen. | "check what I already know" can only take the learner to Progress. |
| **Read a message** | One red, persistent toast in the page flow for errors, notices and successes alike. | Errors red with *Try again* where possible; notices neutral, 5 s; none while reading; session notices gone once a session begins. | Screen-level errors are still raw backend text (the §7.9 copy module is Phase 7). |
| **Leave the build plan** | Escape stepped back; the modal held the tabs. | Escape closes it. | The modal still covers the nav while open. |
| **Open Files / Notes & files** | Opened previewing `vault.lock`. | Opens on the first note. | `state.sqlite` and `vault.lock` are still in the tree (Q3). |
| **Review proposals** | 39 waiting, duplicates unmarked; the bar badge grew after every practice. | Repeats marked; no bar badge. | The duplicates are still written (§9). |

## 5. Tests

**Vitest, new (11 files):** `app/keymap.test.ts` (8), `app/notices.shell.test.ts` (10), `app/shell.test.ts` (10), `components/ShellNav.test.tsx` (8, with the classic snapshot), `components/NoticeHost.test.tsx` (4), `screens/UnderTheHoodScreen.test.tsx` (3), `components/CommandPalette.shell.test.tsx` (8), `app/App.shell.test.tsx` (11, with the classic snapshot), `components/OutlineAndPlan.escape.test.tsx` (2), `screens/ProposalsScreen.repeats.test.tsx` (3), `screens/LibraryScreen.firstFile.test.ts` (3). `testNodeShims.d.ts` gains `readdirSync`/`statSync` for the key-map source scan.

**Python:** new `tests/test_ux_phase2_shell.py` (4: the default reaches the app, classic, only two values, display only); `tests/test_ux_phase4_feedback.py`'s snapshot pin gains the new key.

## 6. Real UI look (usability harness, fake AI)

The stage's own copy of the persona harness (scratchpad `phase2/usability/`): ports 1481/1482, bridges 18881/18882, CDP 9281/9282, its own Chromium tmp, the command mapping regenerated from this worktree's `commands.rs` (415 commands), and `CODEX_HOME` set inside the instance's scratch HOME. Every `ui.mjs` call ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; the sidecar ran in its own network namespace (`unshare -cn`) with a scrubbed environment and no API-key variable. Instance **b** used a backup-API copy (`learnloop.db.copies.copy_tree_with_databases`) of the worktree's tracked `fixtures/linear_algebra` into the worktree's gitignored `fixtures-local/ux2-harness-b/` with the scripted fake AI; instance **a** a fresh, empty HOME with `--ai none`. **No paid call, no real provider, no network; the owner's working vaults were never opened.** The fake AI log shows only background routes it refused locally (21 `approach_map` from `build_on_serve`, 12 `passage_cue_judge` in the Reader). Both instances were stopped and their ports are free.

Screenshots: `docs/ux/screenshots/phase2/`.
- **01** launch on the open practice question: the four places, *+ Add*, *^K*, *⋯*; no chips, no badges.
- **02** ⋯: Settings Ctrl+, · Under the hood · Switch library (linear-algebra current, Open another library…, New library…) · Keyboard & help.
- **03** Progress from Alt+4 pressed inside the answer box (after fix 1): the Graph screen as before.
- **04** Under the hood → Imports & builds, *was Ingest*: the Ingest screen unchanged beside the tool list (Study-map changes 39, System health 3).
- **05** Study-map changes: *proposed 2×* on `representation_notation_error`, *proposed 4×* on `local_slip` and *repeat* on its later copy.
- **06** Files opens on `profile/goals.md`, not `.learnloop/vault.lock`.
- **07** Data: the SQLite browser on `state.sqlite` (342 tables).
- **08** Analyst views: the knowledge field (terrain, well, strata) unchanged.
- **09** System health: the Maintain screen unchanged.
- **10** The palette: plain commands first, *Type to find a command · type > for learnloop commands*.
- **11** "doctor" typed plainly: *No command matches "doctor". To run it as a learnloop command, start with >: > doctor*; nothing ran.
- **12** `> doctor` (after fix 2): the shell's checks stay on screen, the prompt back at `>`.
- **13** Keyboard & help: the bindings, Esc, and *Keys that moved*.
- **14** In the Reader (Axler, 72 %), *Ask the tutor about this* from the palette: no notice over the page.
- **15** Alt+2 to the Library: the held notice arrives at the bottom edge, neutral.
- **16–17** The build-plan step says *esc close*; Escape closes it to Imports & builds.
- **18** After finishing the session, going to Progress and restarting: the app opens on Progress.
- **19** `[ui] shell = "classic"` in the copy's `learnloop.toml`, restarted: the ten tabs, the vault chip, the settings chip and the badges exactly; Alt+4 opened Ingest.
- **20–21** A brand-new library (no AI): the Library's welcome under the four places; Alt+1 shows Start as Today.

What the walk found, each fixed with a test (`19c6b0a72`):
1. Alt+4 did nothing on a practice question (its answer box keeps the focus): the place keys now work while typing in the simple shell (D9).
2. After `> doctor` the palette emptied its line, left the shell and hid the output: it now stays in the shell.
3. The palette's Escape also reached the practice screen beneath ("esc back" left the question): it now closes only the palette (simple shell; classic's leak is the base's).
4. *Ask the tutor about this* in the Reader said "Nothing here to ask about" with a book open: it now points at the Reader's Ask tab.
5. Reopening Under the hood on Mistake history reopened the diff overlay every time: it now opens only when the tool is picked.
Also fixed on sight: ⋯'s Settings row picked up the classic nav's dim key-hint span style.

Seen, and not this stage's: the practice card's *Work in steps* toggle wraps one word per line (01, 03; Phase 4's screen); the Reader's key bar wraps to two lines at 1380 px (Reader doc); `> doctor` reports "sqlite migrations 202/217 applied" on the copy (the doctor's own count; parity checks are the landing's); the Start screen's key bar still says *alt+1..8 tabs* (Phase 3 retires Start).

## 7. Gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp` after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`. Targeted only (owner rule 2026-10-17: the full suite, the whole durability lane and the whole vitest run happen once, in the landing gate). The targeted pytest waited for `/tmp/learnloop-fullsuite.lock` (another stage's full suite held it) and then ran.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| `uv run pytest -n auto` on 52 files (below) | **1192 passed**, 0 failed (5 min 33 s) |
| durability lane | not run: no migration, no DB or connection code changed |
| `npm install` · `npm run typecheck` · `npm run frontend:build` | typecheck clean; build succeeds (the usual chunk-size warning) |
| `npx vitest run` on 68 files (below) | **68 files, 556 passed** |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` · `db_validate_reference.py` · `validate_vault.py` | regenerated (946 leaves in 68 sections, 337 table notes, head 217); **0 errors**; vault validation passed (1139 notes) |
| defaults snapshots | the 20 recomputed (template `.pyc` cleared); `tests/test_config_refactor.py` passes in the run above |

**Pytest files** (every new or changed test file; every file that exercises `config_dto`, the defaults snapshots, `UiConfig`/`config.ui` or the parameter registry; and the contract pins): `test_ux_phase2_shell.py`, `test_ux_phase4_feedback.py`, `test_config_refactor.py`, `test_ad1_attempt_columns.py`, `test_ad1_codex_review_fixes.py`, `test_adaptive_difficulty_ad1.py`, `test_architecture.py`, `test_constraint_engine.py`, `test_diagnosis_input_provenance.py`, `test_grading_cli.py`, `test_hint_kill_switch.py`, `test_intent_codex_rereview.py`, `test_kinship_feature.py`, `test_library_exercises.py`, `test_method_explicit_upgrade.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_plan_determinism.py`, `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_rw2b_review.py`, `test_reader_wrap_up.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_source_roles.py`, `test_table_roles.py`, `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`. The CLI help snapshot, the serializer snapshot, the desktop RPC contract and the mobile allow-list needed no change (no CLI, serializer or RPC change).

**Vitest files:** the eleven new ones, every existing test that imports a changed module (`App`, `algoConfig`, `notices`, `useGlobalAdd`, `components/ui`, `CommandPalette`, `OutlineAndPlan`, `LibraryScreen`/`LibraryPlace`, `ProposalsScreen`, `errors`, `IngestScreen`), and the CSS lints (`styles/navBar.test.ts`, `screens/attentionBudget.test.tsx`, `screens/reader/paletteContrast.test.ts`) and `copy/denyList.test.tsx`. The 68 files (the Reader tests among them pass untouched): `app/App.shell.test.tsx`, `app/App.wrapUpSkim.test.tsx`, `app/keymap.test.ts`, `app/notices.shell.test.ts`, `app/notices.test.ts`, `app/practiceFeedback.test.ts`, `app/shell.test.ts`, `app/useGlobalAdd.test.tsx`, `components/CommandPalette.shell.test.tsx`, `components/DialogueProbe.test.tsx`, `components/InspectorOverlay.phase4.test.tsx`, `components/NoticeHost.test.tsx`, `components/OutlineAndPlan.escape.test.tsx`, `components/SessionFinishHud.phase4.test.tsx`, `components/ShellNav.test.tsx`, `copy/denyList.phase4.test.tsx`, `copy/denyList.test.tsx`, `screens/attentionBudget.test.tsx`, `screens/DiagnosticReviewScreen.phase4.test.tsx`, `screens/FeedbackScreen.liveQueue.test.tsx`, `screens/FeedbackScreen.phase4.test.tsx`, `screens/FeedbackScreen.test.tsx`, `screens/GoldenPathScreen.test.tsx`, `screens/LibraryPlace.reread.test.tsx`, `screens/LibraryScreen.firstFile.test.ts`, `screens/practice/HelpStyleSettings.test.tsx`, `screens/PracticeScreen.adaptiveDifficulty.test.tsx`, `screens/PracticeScreen.adaptiveHandoff.test.tsx`, `screens/PracticeScreen.adaptiveHints.test.tsx`, `screens/PracticeScreen.adaptiveOff.test.tsx`, `screens/PracticeScreen.firstHintRestore.test.tsx`, `screens/PracticeScreen.hintTelemetry.test.tsx`, `screens/PracticeScreen.intentCheck.test.tsx`, `screens/PracticeScreen.phase4.test.tsx`, `screens/PracticeScreen.test.tsx`, `screens/PracticeScreen.workbench.test.tsx`, `screens/ProposalsScreen.repeats.test.tsx`, `screens/reader/compareKeepSwitchOff.test.tsx`, `screens/reader/compareKeep.test.tsx`, `screens/reader/IntentBox.test.tsx`, `screens/reader/intentSwitchOff.test.tsx`, `screens/reader/libraryAskSwitchOff.test.tsx`, `screens/reader/libraryAsk.test.tsx`, `screens/reader/libraryExercisesReader.test.tsx`, `screens/reader/libraryRoles.test.tsx`, `screens/reader/nextStepFold.test.tsx`, `screens/reader/paletteContrast.test.ts`, `screens/reader/readingPathsReader.test.tsx`, `screens/reader/readingPathsSwitchOff.test.tsx`, `screens/reader/recapReview.test.tsx`, `screens/reader/recapSwitchOff.test.tsx`, `screens/reader/rw1bReview.test.tsx`, `screens/ReaderScreen.recapReview.test.tsx`, `screens/ReaderScreen.recap.test.tsx`, `screens/ReaderScreen.workbench.test.tsx`, `screens/reader/tutorBoundAsk.test.tsx`, `screens/reader/tutorExercises.test.tsx`, `screens/reader/tutorReader.test.tsx`, `screens/reader/tutorSwitchOff.test.tsx`, `screens/reader/WrapUp.test.tsx`, `screens/RepairOverFeedback.phase4.test.tsx`, `screens/RepairScreen.phase4.test.tsx`, `screens/UnderTheHoodScreen.test.tsx`, `screens/workbench/HelpLadder.test.tsx`, `screens/workbench/reviewFixes.test.tsx`, `screens/workbench/switchOff.test.tsx`, `screens/workbench/symbolicOff.test.tsx`, `styles/navBar.test.ts`.

## 8. Files

- **New:** `app/keymap.ts`, `app/shell.ts`, `components/ShellNav.tsx`, `components/NoticeHost.tsx`, `components/KeyboardHelp.tsx`, `screens/UnderTheHoodScreen.tsx`, `screens/underhood/tools.tsx` (all under `apps/learnloop-tauri/src/`), the eleven test files and two snapshots above, `tests/test_ux_phase2_shell.py`, `docs/ux/screenshots/phase2/` (21 images).
- **Changed:** `app/App.tsx` (places, Under the hood, notices, keys, palette commands, memory), `app/algoConfig.ts` (`shell`, the cached shell), `app/notices.ts` (the notice list; the stopgap kept for classic), `app/useGlobalAdd.ts` (its chord from the key map), `components/ui.tsx` (`TerminalFrame` draws either nav; `TopTab` gains `underhood`), `components/CommandPalette.tsx`, `components/OutlineAndPlan.tsx`, `screens/LibraryScreen.tsx`, `screens/ProposalsScreen.tsx`, `errors.ts` (`MessageKind`), `styles/app.css` (new rules only), `testNodeShims.d.ts`; `src/learnloop/config/schema.py` (`UiConfig.shell`), `src/learnloop/config/template.py` (20 snapshots), `src/learnloop_sidecar/context.py`, `tests/test_ux_phase4_feedback.py`, `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py` (the `ui` section's function) and the regenerated references.
- **Untouched:** `ReaderScreen.tsx` and everything under `screens/reader/`; no migration; nothing under `src-tauri`; no RPC added or changed.

## 9. Open questions for the owner (defaults applied) and open items

| Q | Question | Default applied |
|---|---|---|
| Q1 | Today without a session shows Start until Phase 3. | As built (D1). |
| Q2 | Keep the Library's *Notes & files* tab beside Under the hood → Files until `LibraryScreen` is split? | Keep both (D3). |
| Q3 | Hide `state.sqlite` and lock files from the trees (spec Q18), and open Data read-only with *allow edits*? | Not in Phase 2: Under the hood keeps the screens as they are. Phase 6 or a Q18 follow-up. |
| Q4 | Fix the duplicate error-type proposals at the source: skip writing a new `error_type:<id>` proposal while one waits (or append the attempt to the waiting one)? | Queued for a grading-path stage; this stage marks them only. |
| Q5 | Place keys while typing (D9). | On in the simple shell. |
| Q6 | Errors raised while reading still show (D4). | Yes, until the Reader shows them on its own controls. |
| Q7 | Notice timing: 5 s once on screen, at most three. | As built. |
| Q8 | Retire `"classic"` a month after Phase 2 lands (spec Q17). | Keep the switch; removing it is a later, owner-approved change. |
| Q9 | The health line covers grading only (D7). | As built; Phase 6 adds tutoring. |

**Open items.**
- **The duplicate error-type proposals** (Q4): `persist_unknown_error_type_proposals` should consult waiting proposals. A grading-path write change; it needs its own stage and tests (replay never reads proposals, so likely no successor, but that is that stage's call).
- **Rule notes.** (1) Three trivial `python3` invocations ran outside `env -i` early in the stage (a string replacement on a test file, an empty heredoc, `python3 -c 1`). None imported learnloop, read a vault or a credential, or touched the network. Every later Python run outside pytest (the snapshot recompute, the reference scripts, the harness's setup and sidecar) ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. (2) One read-only `git stash list` ran in this worktree, appended by mistake to the vault-validation command; it changed nothing, but the stage rules forbid every stash command, so it is recorded here.

## 10. Friction notes for Phases 3 and 5

**Phase 3 (Today).**
- Today is two screens under one name. Without a session it is Start: the epigraph typewriter ("Escape will make me motivated"), "0 concepts in scope · 0 active learning_objects · 3 error types", *+ create a new vault*, the backdrop chip, and a key bar that still says *alt+1..8 tabs* (only Alt+1…4 are places now). With a session it is the old Today: "session 025", "Today: 41 retrieval reps", the decay-pressure panel of facet slugs, *finish session*.
- The session-first notices still say "Begin today's plan on Start first." while the nav says Today; implicit sessions (3.2) remove them.
- *finish session* lands on Start; the session finish card shows over it.
- The palette's *Start today's plan* can only go to Today; with implicit sessions it could begin the plan.

**Phase 5 (Progress).**
- Progress opens on the concept map ("concept-graph vector-spaces · 23 concepts · 72 edges · 0 misconceptions"), with the well behind *knowledge field*; the detail pane lists raw ids (`concept_linear_independence_and_basis`).
- The Graph screen appears twice (Progress, and Under the hood → Concept graph editor) until 5.3 splits the read-only map from the editor; Analyst views shows the same knowledge field Progress has a tab for.
- Analyst views' terrain overlaps facet slugs into unreadable stacks (owner surface, but the same view is one tab away from the learner on Progress).
- *Check what I already know* has no learner surface yet; the palette sends the learner to Progress, where only a topic's inspector offers it (5.2's learner card).

**Others seen (Phases 4, 6, 7, Reader doc).** The practice card's *Work in steps* toggle wraps a word per line; Data opens editable; Spend & AI routes is a pointer; the Reader's key bar wraps at 1380 px; screen errors are still raw backend text.

## 11. Fix round 2 (orchestrator)

**Input.** The orchestrator's whole-stage verify of `c80c54cbb..04be64378` (Codex job `20261021-114726-Jrt7sA`, read-only, verdict REOPENED): five findings, items 1–4 High and item 5 Medium. The same verify confirmed that the Reader `askRequest` edit is minimal and inert, that Data's read-only gate has no bypass (cell edits, row insert and delete, SQL, keyboard entry), and that `UiConfig.shell`, its snapshot field and the registry classification are right.

**Ruling on F6: accepted at the writer, as a workflow-persistence change.** This is a deviation from §0's "display and navigation only", recorded here. The verify's evidence: F6's changed writes touch only proposal batches, their items and their batches' source references (`proposed_patches.source_refs_json`). Grading and regrade ignore its return value. Nothing changes grades, evidence, mastery, scheduling or derived projections, and replay and rebuild do not read proposals as semantic inputs. Workflow exports and backups can carry those rows. The write lock and the reference membership check make a repeated call idempotent while the matching proposal stays pending and unchanged. Proposal tables are `WORKFLOW` in `db/table_roles.py`, so there is no algorithm successor. The stage's rule otherwise stands: no other backend behaviour or contract changed.

| # | Severity | Finding | Fix | Test (failed on `04be64378`) |
|---|---|---|---|---|
| 1 | High | Classic's SQLite browser lost Ctrl+K / Ctrl+ArrowUp row movement: F8's modifier guard applied in both shells | The guard in `SqliteBrowser`'s grid handler runs only when `simpleShell()`. Classic takes Ctrl/Cmd/Alt + its keys exactly as the base did | `screens/SqliteBrowser.readOnly.test.tsx` "classic keeps the grid's modified keys": Ctrl+K, Ctrl+ArrowUp, Cmd+K and Alt+ArrowUp move up from the second row; Ctrl+J and Ctrl+ArrowDown move down (5 failed before). F8's simple-shell test is unchanged and passes |
| 2 | High | Closing Settings, or clicking its message, cleared the whole simple-shell queue, including errors and notices never shown | `App` dismisses only the id of the message Settings shows (the newest), on close and on click. Classic still clears its one toast (`setToast(null)`), as at base | `app/App.fixRound2.test.tsx` with the real `SettingsOverlay`: three errors, a notice waiting behind them (never delivered), a fourth error; Settings shows the fourth; after close the first three remain and the waiting notice arrives once a row frees up. Clicking the message in Settings drops only it (2 failed before). A classic pin (toast cleared on close) passes before and after |
| 3 | High | Try again after leaving the screen that raised the error lost a second failure: `NoticeHost` dismissed the error first, the screen's retry swallowed the rejection, and the unmounted screen could not report it | The shell owns the retry (`notices.ts` `runNoticeRetry`, run by `NoticeHost`). It marks the error *Trying again…* (button disabled) and keeps it until the retry settles. Success drops it. A failure replaces it with the new failure: same `source`, the new code, and a new Try again when that failure is retryable (none when it is not, per §7.9). `ErrorReport` gains `source`, and `retry` may return a promise. `KnowledgeMapView` and `LibraryScreen` (the only screens wired with retries) now pass the failed query's own `refetch`, bound when the error is reported, plus a `source` naming that query (`knowledge-map:get_knowledge_map`, `library:get_vault_tree`, …). `addNotice` replaces an error with the same `source`, so the screen's report (while mounted) and the shell's are one error. The shell's own three `reportError` retries keep working: their actions report their own failures from `App`, which never unmounts | `app/App.fixRound2.test.tsx`, real `KnowledgeMapView` and real `LibraryScreen`: fail, navigate away (Library or Progress), Try again, fail again: the error is visible with its code and Try again; Try again succeeds: it is gone (2 failed before). Also one error, not two, when the retry fails with the screen still mounted. `components/NoticeHost.test.tsx`: the error stays while retrying and goes on success; a failed retry is shown with its code and a new Try again; a non-retryable failure has no Try again (3 failed before). `screens/KnowledgeMapScreen.retry.test.tsx`: the report names its source and the retry returns the read, which rejects (1 failed before) |
| 4 | High | Shell chords leaked into screens' window listeners. Alt+2 went to the Library and Today also read "2" as "practise item 2" (with the plan on, `planLearnerPick` wrote the pick and practice opened) | `keymap.ts` `screenLeavesKey(event)`: in the simple shell, true for any event with Ctrl, Cmd or Alt held, or already `defaultPrevented`; in classic always false. Today's, Proposals' and Feedback's window listeners return on it first. The Library's returns on it after its own Ctrl+S save and Escape. Classic's screens are byte-for-byte as at base. **Why the screens check rather than the shell calling `stopImmediatePropagation`:** window listeners run in the order they were added, and nothing fixes that order. A screen listener added before the shell's still sees the chord first, and its `preventDefault` then makes the simple shell skip the chord altogether, so Alt+2 would not even navigate. The screen-side check holds in any order, and the scan below enforces it. Stopping the event would also hide it from listeners that only track modifier state | `app/App.fixRound2.test.tsx`, real `TodayScreen` in the App: plan off, Alt+2 opens the Library, practice does not open, and a plain `2` still picks item 2; plan on with the full list shown, Alt+2 opens the Library and `planLearnerPick` is never called (2 failed before). `app/keymap.test.ts`: the extended conflict scan, below (1 failed before), and `screenLeavesKey` in both shells (2 failed before) |
| 5 | Medium | F6 matched waiting proposals by the stale `client_item_id` after the payload editor changed the item's `id` | `persist_proposal_batch(..., join_pending=…)` matches waiting items of the same `item_type` and `operation` by their effective identity (`_proposal_item_identity`: the edited payload's `id` when edited, else the payload's, else the client id), read under the same `BEGIN IMMEDIATE` as the insert | `tests/test_ux_phase2_error_type_proposals.py`: a waiting `local_slip` renamed through `edit_proposal_item` to `notation_slip`. A grading naming `notation_slip` joins it (one batch, both attempts). A grading naming `local_slip` proposes `local_slip` afresh, and the renamed proposal keeps only its own attempt (2 failed before; the other 5 pass before and after) |

**The extended conflict scan** (`app/keymap.test.ts`). It reads every window-level `keydown` listener in `src` (outside the shell files). It collects the keys each handler takes (`key === "x"`, `["j", "k"].includes(event.key)`, `case "x":`, `/^[1-9]$/.test(...)`), keeps those that are the key of a shell chord in either shell (the digits of Alt+1…0, the letters of Ctrl+K, P, O, V and Alt+S, the comma of Ctrl+,), and fails unless the handler calls `screenLeavesKey(event)`, returns early on a modifier, or checks a modifier on the line that takes the key. An inline listener, or one whose handler it cannot find, fails too, so a new listener cannot hide from it. On `04be64378` it reports Feedback "o", Library "k", Proposals "k", and Today "p", "k" and the digits 1–7 and 9. A synthetic old-Today listener is also pinned: caught without the guard, clean with it. The listeners that already checked modifiers (Calibration's `s`, the Library's Ctrl+S, the PDF pane's Ctrl+0) pass as they are.

**Fail-before method.** Vitest: `git archive 04be64378 apps/learnloop-tauri` into a scratch directory, with the worktree's `node_modules` linked in and the five new or changed test files copied over. 18 tests failed across all five files; the 21 that pass there are the unchanged cases and the two pins (`fixtures-local/failfirst-round2-vitest.txt`). Pytest: `git archive 04be64378 src migrations` into a scratch directory, run with `-o pythonpath=<scratch>/src`: 2 failed, 5 passed (`fixtures-local/failfirst-round2-pytest.txt`).

**Changed existing tests (the contract changed on purpose).** `NoticeHost.test.tsx`'s first case expected the error to vanish the moment Try again was clicked; it now waits for the retry to settle. `KnowledgeMapScreen.retry.test.tsx` called the retry without handling the rejection the retry now returns.

**Files.** `apps/learnloop-tauri/src/`: `app/App.tsx`, `app/keymap.ts`, `app/notices.ts`, `components/NoticeHost.tsx`, `errors.ts`, `screens/SqliteBrowser.tsx`, `screens/KnowledgeMapScreen.tsx`, `screens/LibraryScreen.tsx`, `screens/TodayScreen.tsx`, `screens/ProposalsScreen.tsx`, `screens/FeedbackScreen.tsx`. Tests: new `app/App.fixRound2.test.tsx`, plus `app/keymap.test.ts`, `components/NoticeHost.test.tsx`, `screens/SqliteBrowser.readOnly.test.tsx`, `screens/KnowledgeMapScreen.retry.test.tsx`. Python: `src/learnloop/db/repositories.py`, `tests/test_ux_phase2_error_type_proposals.py`. No migration, nothing under `src-tauri`, no RPC, CLI or config key.

**Gate** (targeted, per the owner's 2026-10-17 rule; in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`; pytest ran under `flock /tmp/learnloop-fullsuite.lock`, after another worktree's full suite released it).

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| `uv run pytest -n auto` on the round-1 89 files (the same selection rule; every proposal, `edit_proposal_item` and regrade test is already in it) | **1946 passed**, 0 failed (6 min 27 s; round 1 had 1944, plus the 2 new F6 cases) |
| `uv run pytest --durable-sqlite` on `test_ux_phase2_error_type_proposals.py`, `test_codex_attempt_flow.py`, `test_proposal_dependencies.py` (the F6 change reads under `BEGIN IMMEDIATE`) | **20 passed** |
| `npm run typecheck` · `npm run frontend:build` | clean · built (the usual chunk-size warning) |
| `npx vitest run` on the round-1 88 files plus `app/App.fixRound2.test.tsx`, `screens/TodayScreen.plan.test.tsx` and `screens/FeedbackScreen.plan.test.tsx` (importers of the changed screens) | **91 files: 746 passed, 3 failed under load, each passing on rerun** (load average 57–64 while another worktree's full suite ran): `PracticeScreen.firstHintRestore` case 4 (4/4 alone; it failed the same way on the `04be64378` extract under the same load), `ReaderScreen.review` and `readingPathsReader` (timeouts; 16/16 alone, twice). One unhandled timer rejection in `libraryExercisesReader.test.tsx` (`ReaderScreen.tsx:730`, an unmocked `readerSearchSources`). It shows up on the `04be64378` extract too, so it is not this round's; it is listed as an open item for the landing gate |
| `db_generate_reference.py` · `db_validate_reference.py` (under `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`) | The regeneration changed only the 407 notes' commit labels. No cited line moved, so it was not kept. Validation on the committed references: **0 errors** |
| `cargo check` | not run: nothing under `src-tauri` changed |

**Open items.** The `libraryExercisesReader.test.tsx` unhandled timer rejection (pre-existing, above). The round-1 open items stand: the RW7a ordering leak, `ui.practice_feedback`'s missing registry rule, write retries, and existing duplicate proposals. Write retries are now simpler to wire: a write's `ErrorReport.retry` can return its promise, and must still pass the original idempotency key.

**Rule notes.** One `python3 -` ran outside `env -i` in this round. It was a stray command with no script (stdin empty). It imported nothing, read no file, vault or credential, and touched no network. Every other Python run outside pytest (the two reference scripts) ran under `env -i` as above. The fail-before trees were `git archive` extracts in the session scratchpad. No `git stash` of any kind, no model call, no network, no vault opened or copied, and no process killed. A vitest cache directory (`apps/node_modules/.vite`) that a mis-rooted `npx vitest` created was removed; nothing else outside `apps/learnloop-tauri` was written.


## 12. Fix round 3 (orchestrator)

**Input.** The whole-stage verify of `c80c54cbb..e951e85c3` (Codex job `20261021-130232-Uk06Al`, read-only, verdict REOPENED): items 1–3 High, item 4 Medium. The verify accepted F6 (effective-identity matching inside the write transaction; workflow rows only; grading ignores the return value; replay and rebuild do not consume proposals). It also confirmed the Data mutation gates, the round-2 modifier guards, the palette reset and the `askRequest` path.

**Orchestrator rulings (binding).** This is the third round with notice and retry defects, so the class is closed structurally. (1) Every actionable error has a stable identity and a self-contained retry. (2) Startup is the base shell until the config is authoritative. (3) The palette's ask works from any Reader posture.

| # | Severity | Finding | Fix | Test (failed on `e951e85c3`) |
|---|---|---|---|---|
| 1 | High | A retry could clear an unresolved error without making a request. Round 2 bound the hook's `refetch`. Once the view that enabled the query changed (Strata's history after switching to Terrain, Well's decay pressure), `refetch` resolved without fetching, and the shell dropped the error as fixed | **A retry is an explicit fetch of the failed query.** `useCachedQuery` gains `retryReport()`, which binds the key, fetcher and options of that render. Its retry calls the cache's `getOrFetch(key, …, { force: true })` directly, whatever the hook's enabled state, the view, or whether the screen is mounted. **Success means a request ran and succeeded.** A retry resolves `RETRY_RAN` (`errors.ts`) only after its request succeeded. `runNoticeRetry` drops the error only on `RETRY_RAN`. Any other resolution (`undefined`, a no-op, a skipped or disabled read) keeps the error and its Try again. **One wiring path.** `useReportQueryError(query, onError)` reports one error per failed query, with that query's identity and retry. `KnowledgeMapView` (the map, the history and the decay pressure) and `LibraryScreen` (the tree, the proposals and the source sets) use it for every feed; each feed is now its own error, where round 2 reported only the first. The shell's own three retries (grading provider, plan reading, *back to where you studied*) are now split into the action, which throws, and its reporting wrapper. Their Try again runs the action and resolves `RETRY_RAN` | `screens/retryWiring.test.tsx` uses the shared helper `fixtures/retryRequests.ts` `expectRetryIssuesRequest`: the retry issues the failed request again, rejects while it fails and resolves `RETRY_RAN` once it succeeds. Covered: Terrain after unmount; Strata, then Terrain (the verify's case); Well, then Terrain, then unmount; each Files feed after unmount; and a scan pinning that the only screens wiring a read's retry are these two, and that no retry is built from a hook's `refetch` (8 failed before). On the old tree, Strata and Well "resolved undefined instead of rejecting", with no request. `app/App.fixRound3.test.tsx`, real `KnowledgeMapView` in the App: Strata, Terrain, Try again (the request ran; the error stays while it fails and goes when it succeeds); Well, Terrain, Alt+2 away, Try again (the same) (2 failed before). `components/NoticeHost.test.tsx`: a retry that resolves without `RETRY_RAN` keeps the error and an enabled Try again (1 failed before) |
| 2 | High | Identical error text deleted a different action's error and its retry. The bridge's generic sentence is shared, and `addNotice` de-duplicated errors by text | **Identity is the source.** An error that carries a retry must name its `source`: `ErrorReport` and `NoticeInput` are typed so a retry without a source does not compile, and `addNotice` also drops a retry that comes without one. Errors are de-duplicated **only** by source, never by text; plain notices keep text de-duplication. A successful retry drops every error of its source; a failed one replaces it under the same source | `app/App.fixRound3.test.tsx`: Analyst views and Files fail with the same `sidecar_unavailable` sentence. Both errors show; retrying Files reads only the tree and leaves the Analyst error with its Try again, which then reads the map (1 failed before). `app/notices.shell.test.ts` "error identity": two sources with the same sentence are both kept with their retries; same source, new sentence replaces; sourceless errors are never merged by text; a retry without a source is dropped (3 failed before) |
| 3 | High | Classic startup could use simple navigation and keys. Until `loadVault` resolved, a per-machine cache of the last shell (or its absence) made the app simple, so Alt+2 opened the Library where base opens Today, and that destination survived loading | **No cache.** Until the snapshot names the current library's shell, `App` is the base shell exactly (`snapshot ? algoConfig().shell : "classic"`): the base nav, keys and toast. The per-machine cache (`cachedShell`, `SHELL_CACHE_KEY`, `cacheShell`) is removed, not kept as a skeleton: nothing interactive or visible depends on it. During a library switch the app is classic until the new snapshot arrives. A simple-shell learner briefly sees the base nav while the library loads; that is the cost of never acting on a stale value | `app/App.fixRound3.test.tsx`, a deferred `loadVault`: with a stale `"simple"` cache and a classic library, with nothing stored, and with storage that cannot be read, Alt+2 pressed before loading lands on Today (base). No simple nav before loading. With a simple library, the pre-load Alt+2 is still base's and Today is the current place after loading (4 failed before). `app/shell.test.ts`: setting the config writes nothing to storage (1 failed before). The simple keys after loading are pinned too |
| 4 | Medium | *Ask the tutor about this* silently failed while comparing (and while working): Ask was selected behind the hidden rail | `ReaderScreen` closes the comparison first (`closeLibrary`), then expands the rail, selects Ask and focuses it. **Working:** leaving is the learner's call, since *Leave for now* saves the steps and can be refused. So nothing is left or discarded: the workbench shows a visible line, "Ask the tutor is beside the book. Leave for now (your steps are kept) and Ask opens." (dismissable), and Ask opens as soon as the learner leaves. **Reading:** unchanged | `screens/reader/paletteAskPostures.test.tsx`: reading opens Ask. Comparing (Ctrl+Shift+F): the compose box goes, Ask shows, nothing is sent. Working: the problem stays open with the line, no leave or abandon call is made, and after *Leave for now* Ask shows (2 failed before; reading passes before and after) |

**Changed existing tests (the contract changed on purpose).** NoticeHost's and `notices.shell`'s retries now resolve `RETRY_RAN` and name a source. `App.shell.test.tsx`'s Analyst stub passes a source with its retry. `KnowledgeMapScreen.retry.test.tsx` expects the query's identity (`query:get_knowledge_map:[]`). `shell.test.ts`'s two cache cases became the no-cache case.

**Fail-before method.** `git archive e951e85c3 apps/learnloop-tauri` into the session scratchpad, with the worktree's `node_modules` linked and the new and changed test files (and the helper) copied in. **22 failed** across 6 files (`fixtures-local/failfirst-round3-vitest.txt`). The 33 passing there are the unchanged cases and the pins (reading posture, simple keys after loading, the palette, same-source replacement).

**Files.** `apps/learnloop-tauri/src/`: `errors.ts`, `api/useCachedQuery.ts`, `app/notices.ts`, `app/App.tsx`, `app/shell.ts`, `app/algoConfig.ts`, `screens/KnowledgeMapScreen.tsx`, `screens/LibraryScreen.tsx`, `screens/ReaderScreen.tsx` (the ask effect and one prop), `screens/reader/ReaderWorkingPosture.tsx`. New: `fixtures/retryRequests.ts`, `screens/retryWiring.test.tsx`, `app/App.fixRound3.test.tsx`, `screens/reader/paletteAskPostures.test.tsx`. No Python, no migration, nothing under `src-tauri`, no RPC, CLI or config key.

**Gate** (the round-2 gate; `TMPDIR=<worktree>/fixtures-local/tmp`; pytest under `flock /tmp/learnloop-fullsuite.lock`).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` · `uv run lint-imports --no-cache` | ok · 28 kept, 0 broken |
| `uv run pytest -n auto` on the round-2 89 files | **1946 passed** (7 min 44 s; no Python changed this round) |
| `uv run pytest --durable-sqlite` on the 3 F6 files | **20 passed** |
| `npm run typecheck` · `npm run frontend:build` | clean · built |
| `npx vitest run --maxWorkers=6` on the round-2 91 files, the 3 new test files, and every test importing `useCachedQuery`, `ReaderWorkingPosture`, `app/shell` or `algoConfig` (95 files) | **95 files, 776 passed**, no unhandled errors. Two earlier runs at the default worker count, at load average 34–56 (one while this round's pytest ran beside it), had 10 and 16 timeouts of 5 s in Reader, Practice and Feedback files, plus round 2's two Settings cases. The 8 failing files then passed alone (56/56) before the clean run. One of the loaded runs also wrote a stray `… 2` entry into `reader/__snapshots__/libraryAskSwitchOff.test.tsx.snap` (a timed-out test's late `toMatchSnapshot`). It was reverted, and that file passes with no write |
| `db_validate_reference.py` (under `env -i`) | **0 errors**. No Python line moved, so there was nothing to regenerate |
| `cargo check` | not run: nothing under `src-tauri` changed |

**Open items.** Round 2's open items stand. Write retries now have the contract to plug into: a write's retry must name a source, rerun the request with the original idempotency key, and resolve `RETRY_RAN` only after it succeeded. The 5 s vitest timeouts under machine load are environmental, but they recur in Reader files at the default worker count; the landing gate may want `--maxWorkers` set.

**Rule notes.** Every Python run outside pytest this round (the one reference validation) ran under `env -i` with `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` pointing into an empty scratch folder. The paths it picked had no subfolders yet, so they did not exist, which is still empty. The same applies to round 2's second validation run. No `git stash`, no model call, no network, no vault opened, no process killed. The fail-before tree was a `git archive` extract in the session scratchpad.


# UX Phase 2: the shell

**Stage:** `ux-phase2-shell`, branch `ux/phase2-shell` (worktree `learnanything-ux2`), base `c80c54cbb` (main, the RW7a landing, migration head 217).
**Spec:** `docs/specs/ux_learnloop_v1.md` §5 (places, Under the hood, keys), §7.7, §7.9, §8.5 and §10 Phase 2 (items 2.1–2.5), plus the findings Phase 1's usability rounds deferred to Phase 2 (§10 "Deferred", row 2).
**Owner direction:** owner-queued 2026-10-13, re-confirmed 2026-10-21 as Track P. Frictionless by default, the glass box on demand; a live change behind a kill switch, no shadow stage.

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

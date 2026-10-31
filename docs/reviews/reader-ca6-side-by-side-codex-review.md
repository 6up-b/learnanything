# Reader CA6 (side by side): Codex review and fixes

Stage `reader-ca6-side-by-side`, branch `reader/ca6-side-by-side`, worktree `learnanything-merge2`.
Codex reviewed `3a96d90b4..8f16f4201` (job `20261031-192756-ETGGqP`) and reported eight findings: seven
Medium and one Low, with no High. Seven are fixed. F1 is fixed in part: the second pane now has
highlight, note and its own margin marks, but the intent box is still missing there (open question below).
No finding was rejected. Each one was reproduced first with the regression test that now guards it, or
with a mutation check that reverts the fix and watches that test fail (listed per row). No migration, no
successor, no config key, no model call, no paid or live call.

Owner decisions in force (2026-10-12): the spec's recommended defaults; frictionless defaults (honest
labels, generous defaults, live changes behind kill switches).

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The second pane omits required reader interactions | **fixed in part** | `61453ccb2` | A selection in the second pane now offers *highlight* and *note* even with CA3 off. Both go to that pane's own book: `reader.side_by_side_section` names the reading's `revision_id`, and the save is the ordinary `reader.capture` on it. The learner's own highlights and notes in that book show as margin marks (`reader.source_annotations` for that book). Tests: `sideBySideReader.test.tsx` "F1: with CA3 off, …" (it fails at `8f16f4201`, which has no buttons) and `test_reader_ca6_side_by_side.py::test_a_highlight_made_in_the_second_pane_goes_to_its_own_book` (no `revisionId` at `8f16f4201`). **Not built:** the intent box (typed intentions routed to the palette's actions) and RW3a's density-governed cue marks in the second pane. The palette's handlers are bound to the main render and its selection, so they need per-pane intent routing in `ReaderScreen`. See open question 1. |
| F2 | Medium | Keyboard scrolling does not make the main pane lead | fixed | `42fc3a995`, test `bea8e7e9d` | The main pane's `onKeyDown` treats scroll keys (`SIDE_BY_SIDE_SCROLL_KEYS`, outside fields and buttons) as the learner's touch. Reader-level test "F2: after F6, PageDown in the main pane makes it lead" uses wheel on the side pane, then F6, then PageDown. Mutation: dropping the `touchMain()` call fails it. |
| F3 | Medium | Switching leaders twice revives a stale follow request | fixed | `42fc3a995` | `touch()` advances the crossing generation whenever leadership changes. Hook test "F3: switching leaders twice …" (main crossing deferred, then side, then main, then the answer lands, and the side pane is unmoved). Mutation fails it. |
| F4 | Medium | A pending open can reopen side by side after it becomes disabled | fixed | `42fc3a995` | Ctrl+\'s read has a generation token (`pendingOpen`). Another open, a close, another book or the switch going off (working posture, offline) invalidates it. `open()` reads the current eligibility (`enabledRef`), and `panes`, `sheet` and `target` are gated on the current `enabled`. Hook tests "F4: … becomes ineligible …" and "F4: … superseded by an open the learner made meanwhile" (the mutation that drops the token check fails the second). |
| F5 | Medium | Source navigation destroys side-by-side history | fixed | `42fc3a995` | The pair now lives in its return-stack entry (`ReturnEntry.sideBySide`), not in a per-source map, so it survives source detours and goes when the entry is discarded. Walking onto a `side_by_side` entry reopens it once the main pane holds the book it was opened beside. A pair ends on a main-source change only if the new book is not that book. Hook test "F5: a source detour keeps the pair; walking back onto the crumb reopens it". Mutation (dropping the main source from the reopen effect's dependencies) fails it. |
| F6 | Medium | Opening another target can leave an orphan crumb | fixed | `42fc3a995`, test `bea8e7e9d` | Opening another section while side by side is open on its crumb replaces the pair in place (`replaceSideBySide` with `returnStack.replaceCurrent`), keeping the entry id, so the crumb names the new book and closing removes it. `pushDetour` identity now includes the second pane's target, so a pair never deduplicates into another pair's crumb. Tests: hook "F6: … replaces the pair on the same crumb" (mutation fails it) and `returnStack.test.ts` "Reader CA6 (Codex review F6) …". |
| F7 | Medium | Comparing a right-pane passage loses its reading position | fixed | `42fc3a995`, `bea8e7e9d` | The hook keeps the second pane's scroll position per section, so it survives the pane unmounting during a comparison, and the pane restores it on remount. A new section still starts at its top. Fixing this exposed a related bug: Esc during a comparison closed the hidden side by side (its window listener runs first). Esc, F6 and Ctrl+Shift+L now act only on side by side as shown (`sbsShownRef`), so Esc closes the comparison and side by side comes back. Reader-level test "F7: comparing a passage of the second pane keeps its reading position; Esc ends the comparison, not side by side". Mutations of the restore and of the Esc guard each fail it. |
| F8 | Low | The recorded events cannot support the specified evaluation | fixed | `42fc3a995` | Each opening is a session: `side_by_side_opened` carries `side_by_side_id`, the crumb's `detour_id` and the visit (`visitPayload`). The new `side_by_side_closed` carries `seconds_open` and `via` (close, walked_off, replaced, source, switch_off). `follow_along_moved` carries the session and visit. The new `follow_along_undone` is recorded when the learner takes the moved pane back to the section follow along took it from, before moving it anywhere else (`seconds_after`). Salience only. Both events join `CLIENT_ACTION_EVENTS`, and `side_by_side_id` and `seconds_open` join `ACTIVITY_FIELDS` (ids and timings). Tests: hook "F8: a session records …" (mutation fails it) and "F8: moving the followed pane on elsewhere is not an undo"; backend `test_a_side_by_side_session_keeps_its_id_and_minutes_for_the_evaluation`, plus the two new events in the parametrized salience-only test. |

## Open questions for the owner

1. **The intent box in the second pane (F1 remainder).** Spec §6.4 says "Selecting in either pane shows the
   intent box". The second pane now has highlight, note, its own margin marks and CA3's verb, but not the
   typed intent box or RW3a's density cue marks. Building them means routing the palette's actions (Ask,
   explain, worked example, test me later, …) per pane, which is a refactor of `ReaderScreen`'s handlers.
   The proposal is to accept this for CA6 and queue it as a follow-up (CA6b), or to do it before landing
   if the owner prefers.

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`), 34 files: **6351 passed**. The files: `test_reader_ca6_side_by_side.py` (18,
  including 2 new tests and 2 new parametrized cases), `test_compare_keep_switch_off.py`, `test_figures_rpc.py`,
  `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_library_ask.py`, `test_mobile_allowlist.py`,
  `test_plan_first_transport.py`, `test_reader_activity.py`, `test_reader_branches.py`, `test_reader_cues.py`,
  `test_reader_inquiry_kill_switch.py`, `test_reader_inquiry_status.py`, `test_reader_intent.py`,
  `test_reader_passage_check.py`, `test_reader_recap_review.py`, `test_reader_reconnect.py`,
  `test_reader_reconstruct.py`, `test_reader_report.py`, `test_reader_rw3b_protection.py`,
  `test_reader_tutor_offers.py`, `test_reader_tutor_switch_off.py`, `test_reader_workbench_rw2a.py`,
  `test_reading_paths.py`, `test_rw4_kill_switches.py`, `test_salience_firewall.py`, `test_ux_phase1_landing.py`,
  `test_ux_phase3_today.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`,
  `test_architecture.py`, `test_sidecar_reader.py`, `test_cli_help_snapshot.py`, `test_tracked_fixture_databases.py`.
  These are every test file that names `reader_inquiry`, `side_by_side`, `log_activity` or `record_activity`,
  plus the RPC, serializer, architecture, CLI and fixture pins.
- No migration, no DB or connection code, no config key and no schema change: no durability run, no DB
  reference regeneration, no default-snapshot change.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean. Vitest
  (`--maxWorkers=4`), 39 files: **357 passed**. The files: `reader/sideBySideReader` (14), `reader/useSideBySide` (20),
  `reader/findSectionSideBySide`, `reader/findSection`, `reader/findSectionByPoint`, `reader/findSectionReader`,
  `reader/returnStack` (8), `reader/inquiryComponents`, `reader/readerHooks.parity`, `reader/IntentBox`,
  `reader/compareScope`, `reader/compareScopeCodexReview`, `reader/libraryAsk`, `reader/libraryAskSwitchOff`,
  `app/keymap`, `app/classicIsBase`, `app/shellChrome`, and every `screens/ReaderScreen.*.test.tsx` (22 files).
  `npm run frontend:build`: ok.
- `src-tauri` unchanged: no cargo check needed.
- No paid or live call, no vault opened, no GUI launched.

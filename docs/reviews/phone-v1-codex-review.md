# Phone v2, stage V1: Codex review and fixes

**Stage:** phone frontend v2, V1 (shell and plumbing), branch `phone/v1-shell`. **Review:** Codex on gpt-6.1-sol, job `20261106-154136-FYrXSj`, over `7b11b0d67c..1ca3ef7c83` (the stage's own review is `docs/reviews/phone-v2-v1-shell.md`). **Fix commit:** `40f8a00d68`. No Python, migration, RPC, allowlist or model request changed. Nothing in the fix calls a paid route.

## Review

Each finding was reproduced with a failing test before it was fixed. The new tests failed on `1ca3ef7c83`: 8 tests for F1-F3, and the reconnect test once the old unawaited sequence was put back temporarily.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | New Back controls bypass the in-flight submission guard | **Fixed** | `40f8a00d68` | `Shell.test.tsx` "Back while a submit or a skip is on its way": a held `submit_attempt` and a held `skip_practice_item`. The chevron is disabled, a click and an edge swipe stay on `#/today/question/i1`, and the submit's reply opens its own feedback. After a refused skip, Back works again. `ScreenFrame.test.tsx` "a back held for now", which includes a swipe that starts allowed and ends held |
| F2 | Medium | Database upgrade can leave the phone on a blank screen | **Fixed** | `40f8a00d68` | `Shell.test.tsx` "a database upgrade another tab holds up": an M2a version-1 connection is left open in another tab. The App shows *LearnLoop is open in another tab. Close the other LearnLoop tabs to continue.*, and **Retry** reloads. Once the tab closes, the App reaches Today by itself. `displayCache.test.ts`: `dbBlocked()` reads true and then false while the old connection stays open and then closes, and this build's connection closes when a version-3 open asks |
| F3 | Low | Practice screens still display raw stale-app refusals | **Fixed** | `40f8a00d68` | `Shell.test.tsx` "on the practice screens too": `method_not_allowed` while opening a question, submitting and reading feedback. Each case shows *LearnLoop was updated.*, never the refusal text. Try again and Back (or Next) remain, and a typed answer is kept |
| R1 | (claim) | Reconnect "in this order" was not sequenced | **Fixed** | `40f8a00d68` | `Shell.test.tsx` "each step of the reconnect waits for the one before it to finish, with replies held back": the second capture's reply is held. No `get_session` is sent until that reply arrives, and no `queue-revision` read until `get_session` answers. This test fails when the old `void` calls are put back |

The other two claims under "Claims that don't hold" (*today's behaviour unchanged*, *never the raw refusal*) were the F1 and F3 findings themselves, and both now hold. Codex's `systemd-run` failure (the user scope bus was unreachable from its sandbox) does not affect this run: every command below ran inside the mandated scope.

### What changed

- **F1** (`practice/QuestionScreen.tsx`, `shell/ScreenFrame.tsx`, `App.tsx`):
  - The question reports `submitting || skipping` through `onBusy`, and stops on unmount.
  - The App passes it to the frame as `backDisabled`.
  - The chevron renders disabled, as the question's own Back always has. The edge swipe checks the hold again when the touch ends.
  - Grading and Feedback had no frame Back before this fix and still have none.
- **F2** (`store/db.ts`, the new `shell/DbBlocked.tsx`, `App.tsx`, `main.tsx`):
  - `openDb` sets `onblocked`. A small store (`dbBlocked()`, `subscribeDbBlocked`) reports the blocked state, and the App renders the blocked screen while it holds.
  - The pending open completes by itself when the other tab closes. Retry is `reloader.reload()`.
  - Each connection closes on `versionchange`, so this build never blocks a later one. The next open then meets the newer version, and the meta check offers the reload.
  - `main.tsx` no longer waits on a pairing link's token save before the first render while the database is blocked.
  - Limitation: an M2a tab cannot be changed. It holds the upgrade until it is closed, and the blocked screen is how that shows.
- **F3** (`api/http.ts` `staleRefusal`, `practice/QuestionScreen.tsx`, `practice/FeedbackScreen.tsx`):
  - A `method_not_allowed` leaves the screen's error text empty. The question's load, its submit failure, the feedback's load and the follow-up answer's send all follow this rule.
  - The App's `reportError` already ignored the code, so the connection line is the only thing shown.
  - The load screens keep Try again and Back (or Next), so no screen is stranded.
- **R1** (`App.tsx`):
  - `flushNow()` returns the flush, and the reconnect awaits it, then awaits the session read, then reads the token.
  - The token read is gated on the screen in view at that point, not when the reconnect started.
  - `flushOutbox` already shares one flush in flight, so the reconnect's flush waits for every intent the `online` flush is sending.
- **Plain words:** `a11y.test.tsx` now also audits the blocked screen against the desktop's jargon deny-list and the named-controls rule.

Today's practice requests are unchanged: `App.test.tsx`'s 99 tests (M2a's journeys through the fake host) and `api/contract.test.ts` pass without edits.

## Gate

Setup: `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile` (no lockfile change). Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`. `TMPDIR` was the stage's scratch directory, outside the worktree.

| Command | Result |
|---|---|
| `uv run lint-imports --no-cache` (under `env -i`, empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`) | 43 kept, 0 broken, including the frozen-cycles contract |
| `npm run typecheck` (apps/learnloop-mobile) | clean |
| `npx vitest run --maxWorkers=4` on 10 files: `src/App.test.tsx`, `src/shell/Shell.test.tsx`, `src/shell/ScreenFrame.test.tsx`, `src/shell/a11y.test.tsx`, `src/store/displayCache.test.ts`, `src/api/http.test.ts`, `src/api/timing.test.ts`, `src/api/contract.test.ts`, `src/desktopImports.test.ts`, `src/store/outbox.test.ts` | 206 passed, 0 failed (10 files) |
| `npm run build` (apps/learnloop-mobile) | built (output in the gitignored `src/learnloop_mobile/static/app/`) |
| `uv run pytest -n 6` on 10 files: `tests/test_sidecar_measurement.py` (display-label audit), `tests/test_measurement_state_labels.py`, `tests/test_cli_help_snapshot.py`, `tests/test_codex_lockdown_round3.py` (process-launch allowlist), `tests/test_codex_lockdown_frozen.py`, `tests/test_architecture.py`, `tests/test_mobile_allowlist.py`, `tests/test_mobile_phone_contract.py`, `tests/test_mobile_meta_timing.py`, `tests/test_public_tip_guards.py` | 437 passed, 0 failed |

Not run, and why:
- No Python, schema or migration changed, so there was no durability lane and no DB reference regeneration.
- `apps/learnloop-tauri` and `src-tauri` did not change, so there was no `frontend:build` or `cargo check` there.
- The full suites wait for the landing gate (owner rule, Oct 17).

## Left open

- **Checks still to run on a real iPhone:**
  - The blocked screen when Safari has an old LearnLoop tab open. A home-screen app has its own storage, so it is not affected.
  - That a disabled chevron reads as dimmed under VoiceOver.
  - These join the iPhone checks already listed in `phone-v2-v1-shell.md`.

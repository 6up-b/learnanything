# UX Phase 1 finishing pass: Codex review fixes

**Branch:** `ux/phase1-first-run` (worktree `learnanything-ux-impl`, not rebased onto main and main not merged in; the orchestrator merges). The review covered `3d259303d..1531dad82`: the finishing pass's `f74797d66` (F8, F9), `23ec08aea` (re-test #2–#10) and `1531dad82` (its record, `docs/reviews/ux-phase1-finish.md`).

**Codex job:** `~/.cache/codex-agent/jobs/20261013-143739-aKfD7v`.

**Findings:** two Medium (F1, F2), no High. Both were reproduced with a test that failed first, and both are fixed. None is rejected. Codex's three "claims that don't hold" each rested on one of them and hold now (C1–C3 below). Codex confirmed the prior F9 fixed and found no other invariant violation in migration 187, replay, evidence, grading, embedding, spend, verdict or network paths.

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. No real provider and no network were used, and no app or server was started.

**Migration:** none. **Schema:** unchanged. **Config:** unchanged. **Algorithm version:** unchanged. `src-tauri` is untouched (no `cargo check` needed). The DB and configuration references need no regeneration.

## Review

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The worker can exit just as a reading retry becomes due | fixed | `58d34dbd5` | `tests/test_ux_phase1_finish.py::test_f8_the_worker_stays_for_a_retry_that_falls_due_between_its_scan_and_its_exit` (the real worker loop on a scripted clock) |
| F2 | Medium | Delayed PDF loading bypasses the resumed-check guard | fixed | `ed960392b` | `apps/learnloop-tauri/src/screens/ReaderScreen.followsLearner.test.tsx` "#2: a resume offers no leftover check while the original PDF is still loading (guide first)", with the guard "#2: a resume offers no leftover check when the original PDF arrives before the guide" |
| C1 | (claim) | "F8 … fixed": the worker retries until settlement or exhaustion | holds now (F1) | `58d34dbd5` | A request is either seen due by the round's scan or keeps the worker for its later deadline |
| C2 | (claim) | "A resume never offers [the check]" (D22) | holds now (F2) | `ed960392b` | True in both response orders |
| C3 | (claim) | "Items 2–10 are fixed" | holds now (F2) | `ed960392b` | Item 2 was the incomplete one |

**Fail-first.**
- **F1:** the new test was run against `1531dad82` before the fix and failed with `assert 'u3' is None`. The worker exited, cleared its handle, and left the request due with no retry attempted. That is Codex's reproduction: zero retry attempts, worker handle cleared, one due request remaining.
- **F2, guide first:** the test failed against `ReaderScreen.tsx` at `1531dad82`. With the PDF manifest still held back, "A quick check on this section is ready, just below." was already showing. With that first assertion removed, it failed where Codex said it would: "quick check →" appeared once the PDF loaded, with no reading.
- **F2, PDF first:** this ordering passed both before and after the fix. It guards the ordering Codex asked to be tested.

### F1: one clock reading per worker round

**Reproduced.** Each idle round of `_worker_loop` read the wall clock twice:
1. `retry_reading_advances()` scanned for requests with `wanted_retry_at <= now₁`.
2. After three idle rounds, `_reading_retry_waiting()` looked for `wanted_retry_at > now₂`.

A deadline in `(now₁, now₂]` was missed by both. The worker stepped aside with a due request and nothing to wake it.

The test drives the real `_worker_loop` on a thread, on the real repository. Its clock is scripted: `jobs._iso` reads a value the test controls. The deadline passes between the round's scan and its exit check. The hook that moves the clock is the active-job lookup, which the exit check evaluates first.

**Fixed** (`src/learnloop/content/pipeline/jobs.py`). The round reads the clock once (`now = _iso(None)`). It passes that instant to both the due scan (`_retry_reading_due(now)`, which `retry_reading_advances` now delegates to) and the exit check (`_reading_retry_waiting(now)`). So every request with a retry deadline falls into one of three cases:
- **Due by that instant:** the scan acted on it. It was settled, failed again with a new future deadline or none (retries ran out), or deferred.
- **Later than that instant:** it keeps the worker.
- **Failed again during the round:** its new deadline (`now` + 2 s or more, at second resolution) is later than the round's instant, so it keeps the worker too.

**Not taken: Codex's literal remedy**, "keep the worker alive while any pending request has a non-null retry deadline, including overdue requests". After the round's scan, the only overdue requests left are deferred ones. These wait behind the book's own work (`_source_work_active`: a job of the book's queued, running or waiting for input). That work is in one of two states:
- **On this worker:** the worker runs it, then scans again. Keeping the worker for the request adds nothing.
- **Waiting on the learner** (`waiting_for_input`, which holds no lease): the answer wakes the worker (`resume_batch` → `_ensure_worker`). Keeping the worker for the request would make it poll and re-plan the request every second for as long as the learner takes.

The one-instant check closes the race that was found without adding that loop. See Q-F1 for the one case it leaves as before.

### F2: the Reader knows the original is still loading

**Reproduced** with the real component and a held `reader_pdf_view` answer:
1. The guide answered first.
2. While the manifest was pending, `pdfSurfaceActive` was false, so the text view's 70 % rule judged the resumed position (the section's last passage). It made the check due and pinned it (`stickyQuestionSections`).
3. Once the original loaded, `readingMoved` was still false, but the pinned check stayed open and the original offered it.

**Fixed** (`apps/learnloop-tauri/src/screens/ReaderScreen.tsx`):
- **The Reader tracks the pending manifest.** `pdfViewPending` is set when `openSource` asks for the manifest and cleared when that request settles. A request counter (`pdfViewRequestRef`, bumped by `resetSourceState`) lets only the newest request settle the state. A late answer for a book already left no longer lands on the next one.
- **No check while the original is on its way.** `pdfSurfaceLoading` (manifest pending, original chosen, not the offline fixture) holds the check back:
  - no check becomes due (`currentQuestionDue` is false), so nothing is pinned;
  - the section being read has no written check open, as in the original.
- **Once the manifest settles, the rules apply as before.** If the original is there, D22's rule applies: the check waits for the learner's own reading at the section's last page. If there is no original, the text view's rules apply, unchanged.

**Tests.** Both orderings hold back one answer (`holdBack`) and release it once the other has landed. After release, the Reader settles before the learner reads, since the original's arrival places the page and placing is not reading. In each ordering:
- nothing is offered on arrival (neither "quick check →" nor the ready line);
- the learner's own scroll to the section's last page then offers the check.

## Open question

- **Q-F1** (low; behaviour unchanged by this pass; *settled by `reading-hardening.md`, part 1: a cancel settles the book's reading request, and a periodic sweep replaces every wake-up*). A request deferred behind work the learner then cancels is not acted on until one of these happens: the Reader reaches the next section, the next start, or anything else wakes the worker. `cancel_batch` does not wake it. Waking it there would immediately re-plan the chapter whose work the learner just cancelled. So this pass leaves it alone. Recommended default: keep as is.

## Gate

All run in this worktree at `ed960392b` (the fixes), with `TMPDIR` set to the worktree's `fixtures-local/tmp`. Only review docs changed after that.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8805 passed**, 0 failed, 0 skipped (4 min 53 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8711 deselected, 0 failed (1 min 35 s) |
| `npm install` (apps/learnloop-tauri) | ok, lockfile unchanged |
| `npm run typecheck` | ok |
| `npm test` (vitest) | **351 passed** in 53 files |
| `npm run frontend:build` | ok (the existing chunk-size notice only) |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| DB / configuration references | not needed: schema and config unchanged |

Targeted runs before the gate: `tests/test_ux_phase1_finish.py` + `tests/test_ux_phase1_round2_rereview.py` 22 passed; `ReaderScreen.followsLearner.test.tsx` 33 passed; `src/screens` 158 passed in 24 files.

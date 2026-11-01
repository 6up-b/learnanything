# Follow-ups Oct 31: Codex review fix round

Branch `fix/followups-oct31`, worktree `learnanything-astrafix`. Codex review
job `20261101-000553-dDLPBK` (gpt-6.1-sol). It reported one finding. Codex could
not run tests, because its sandbox denied the systemd user scope. The stage
record is in `docs/reviews/followups-oct31.md`.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Zero-hit comparisons still allow invisible paid tutor requests | fixed | 0d3a5b4235 | `findSectionReader.test.tsx`: "Ctrl+↵ asks the tutor about the two sections and its pending line, cancel and answer show", "a tutor answer that fails says so beside the comparison", "a cancelled comparison keeps the tutor over its pins on screen" |

### F1

**Reproduction.** Setup: CA3 off, a find-section comparison, and a section
question that returns no hits. Ctrl+Enter on the comparison pane called
`readerLibraryAskTutor` with the two sections' pins. The tutor's pending line,
cancel button, answer and failure were drawn only inside
`ask.hits.length > 0`, so nothing appeared on screen. On the old render, the
two new tests reached the tutor call and then failed their visibility
assertions.

**Related gap.** Cancelling the comparison sets its phase back to `idle`. The
pane was gated on `pinsCompare`, so it disappeared while the pins stayed. Ctrl+Enter
from another focused element in the answer, such as close or the personalization
toggle, still ran the tutor with nothing on screen. The third test covers this
case. It fails if only the condition change is reverted.

**Fix** (`apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx`).
- The pinned tutor is now a single element, `pinsTutor`: the "ask the tutor
  about pinned" box, then its `ModelActionState` (pending line, cancel, answer,
  failure, retry).
- It renders in the same place as before under the hits, and also inside the
  zero-hit `[data-sections-compare]` pane.
- That pane now shows while a comparison is running or while pins exist
  (`pinsCompare || state.pinned.length > 0`).
- Nothing changed in the CA3-on path, the hook (`useLibraryAsk.ts`), the backend
  or the RPC contract.

## Gate

No Python changed, so no pytest run was needed. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`.

| command | result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `npm install` (apps/learnloop-tauri) | ok |
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=4 <16 files below>` | 16 files, 190 passed, 0 failed |
| `npx vitest run --maxWorkers=4 src/screens/reader/findSectionReader.test.tsx` (after the fix) | 11 passed |
| `npm run frontend:build` | built |

Vitest files run (`apps/learnloop-tauri/src/screens/reader/`):
- findSectionReader
- alsoInBooksReader
- alsoInBooks
- libraryAsk
- libraryAskJobs
- libraryAskSwitchOff
- libraryRoles
- libraryExercises
- libraryExercisesReader
- compareKeep
- comparePointTable
- comparePointTableCodexReview
- compareScope
- compareScopeCodexReview
- figures/advancedPanels
- figures/libraryOfferSettle

Each name stands for `<name>.test.tsx`. These are every vitest file that
imports `LibraryAnswer` or `useLibraryAsk`, or renders the comparison pane.

Not run: `cargo check`, because nothing under `src-tauri` changed. Also not run:
the durability tests and the DB reference scripts, because there is no migration
and no schema change.

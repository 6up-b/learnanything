# Notebook lesson B7: a lesson notebook in a lesson window

- **Base:** branch `notebook/frame-b4-b5`, on top of the pad cells step (`e18d3ed3b0`). Merged first: origin/main
  at `f040982873`, then `reader/rd9a-lesson-windows` at `f3635b9b50`.
- **Scope:** spec §11 (§11.1's lesson window, §11.2–§11.4) and §16's RD9b row, for a lesson whose medium is a
  marimo notebook. No migration, no kill switch, no model call, no owner notebook, no prompt, no authoring path.

## The merges

- **origin/main:**
  - Generated vault notes taken from main's side.
  - `tests/test_mobile_allowlist.py`: both sides' pins kept (the notebook RPCs and RD4's fix round).
- **The lesson windows branch:**
  - `fakeCore.ts`: both sides' cases kept (notebook RPCs, the goal lens and the lessons).
  - `harness.tsx`: our two fixtures kept, followed by RD9a's `HarnessShell`.
  - `DeskShell.tsx`: our `NotebookBridgeContext` wrapper kept, with RD9a's `has-goal` class.
  - `visual_reference.py`: the stage choices are now the union (rd6, rd9, notebook).
  - `test_mobile_allowlist.py`: the notebook and RD9a pins both kept, and both lists are in the parametrize list.
  - `desktop_validate.py` counts recomputed. They are now 397 TS sources, 378 entry-reachable and 403 ACTIVE, which includes this step's one new file.
- **Both sides' tests after the merges:**
  - RD9a's vitest and the notebook vitest pass: 20 files, 251 tests.
  - The desk harness passes every run, including RD9a's `lesson` run: 131 passed, 0 failed.
  - The notebook harness passes: 36 of 36 checks.
  - The notebook sidecar and real-sandbox tests pass.

## Where a lesson's notebook comes from

**No production path produces a notebook lesson yet.**
- Teacher v2 §10.3 makes the medium a second logged draw ("a notebook lesson": the same lesson row and brief, with
  the `notebooks` capability on and a planned section).
- NA §9.9 and §9.13 have the notebook written by a durable authoring job (the teacher's `nb_request`). That job is NA4's teacher half and is not built.
- The `lessons` table (migration 234) has no medium column, and `lesson_turn_payloads` carries no notebook.

What this step builds is the hosting path, end to end, against a stated location:
- **A lesson's notebook is the vault file `notebooks/lessons/<lesson id>.py`.** NA §5.3 puts notebooks in the vault as `.py` files.
- Its presence is the lesson's medium: `lesson.view` adds `medium: "notebook"` and `notebookPath` when the file
  exists, and nothing otherwise, so every existing view is byte-for-byte unchanged.
- `view.medium` stays the window's switch (RD9a's seam).
- What would produce such a lesson: NA4's teacher half (the `nb_request` action and its durable job), writing that
  file for the lesson it plans. It could also record the medium on the lesson row through the playbook, if the owner prefers a column to a file's presence.
- Nothing here writes the file. The fixtures and tests write it themselves.

## What was built

| Piece | Where | What it does |
|---|---|---|
| The lesson's notebook and its commit points | `notebook_runtime/lessons.py` | `lesson_notebook_path` returns the vault file or None. `lesson_contract` reads the notebook's cells statically (Python's `ast`): a cell whose name starts with `commit` is a commit point, a cell shipped `disabled=True` is held, and each held cell belongs to the nearest commit point above it. Held cells above every commit point are released by none |
| A commit, seen by the host | `supervisor.note_commits`, `proxy.py` | marimo names a control `<cell id>-<n>`. A non-empty value set on a commit point's own control (a `set_ui_element_value` on its way to the kernel) marks that point committed. In a review nothing is marked |
| Release only at a commit, never in a review | `runtime._release`, `ReleaseRefused`; handler error `notebook_release_refused` | For a lesson's session the sidecar refuses any cell the learner's commits have not unlocked, and refuses everything in a review. A new server process clears `released` (the notebook loads held again), and the client releases again from the session's commits |
| The session says so | `Session.lesson_view()` in `notebook.status` / `notebook.open` | Gives `lesson: {review, released, commitPoints: [{name, held, committed}]}`, for lesson sessions only |
| `notebook.open` for a lesson | `handlers/notebooks.py` (`lesson_notebook`) | `lesson:<id>` with no path opens the lesson's own notebook, with its contract, `review` = the lesson is closed. A path that differs from the lesson's own is refused. A lesson without a notebook is refused. An owner key with no lesson still opens a named path (the frame's fixtures) |
| `lesson.view` names the medium | `handlers/lesson.py` | `medium` and `notebookPath` are added when the lesson's notebook exists |
| The frame in the lesson window | `screens/desks/notebook/LessonNotebook.tsx`, `notebook.css` | Shows `NotebookFrame` (owner `lesson:<id>`, app view, so read-only as the teacher made it) inside the lesson paper's frame (its rule and margins; the frame adds neither). It fills the window as the mockup's does. It releases what an answered commit point holds through `notebook.release`, once. While a commit point waits it reads the session every 750 ms (`NotebookFrame`'s new `readyPoll`), and otherwise every 5 s. A review shows the line "review · the notebook as the teacher made it · nothing new is revealed or recorded" and releases nothing |
| The desks' default | `DeskShell.tsx` | `lessons.notebookFrame` defaults to `lessonNotebookFrame`; a caller may still pass its own |
| Additions | `pads/PadStackWindow.tsx` (3 lines) | `writeUnderLesson(lessonId, block)` takes the menu's block, defaulting to a text line as before. A block from the menu is written to the lesson's additions pad, never into the notebook |
| A bug in the runtime's release (NBF-4) | `runtime._release` | marimo runs an enabled cell only when it went stale while held. A held reveal whose inputs never changed stayed blank after its release. The runtime now runs the released cells after enabling them |
| Harness | `fixtures/desks/fakeCore.ts` (`?nblesson=open\|review`, `notebook_release` forwarded), `scripts/desk_harness/notebook.py` | The desks' real lesson window with the fixture lesson as a notebook lesson, served by a real sandboxed session |

## Commit points as the paper theme styles them

- The theme's `ll-commit`, `ll-held` and `ll-verdict` classes (the paper card with the purple voice edge, the held
  state dashed, the verdict line) are what the lesson notebook's commit and reveal cells render.
- NA's commit-gate widget, which would render them from `ll.commit`, is not built. The fixture's notebook writes the classes itself.
- **Not built:** the host-owned commit of NA §6.3 (authenticated, frozen and logged before the reveal, with a state machine).
- A commit here is not evidence: nothing about it is written anywhere. Any control value on the commit point's cell counts (the frame's own code could set one too), so this is display gating, not integrity. The notebook's own code can also enable or run its held cells
  directly (it runs in the kernel beside the server, NBF-16), so a reveal is never protected from the notebook.

## Lifecycle

- **Paused window:** no open and no polling, and the frame is inert (B4's `NotebookFrame`). Tested in vitest.
- **Desk move or remount:** the same owner key and revision rejoin the same session and process. The harness reloads the lesson page and finds the same process with the reveal kept.
- **Vault switch:** stops the session (the runtime's switch hook, unchanged from B1–B3).

## The right-click menu (follow-up for the integration)

`notebookMenuRequest(message, "lesson:<id>")` returns `{ lessonId, padId: null, label: "the lesson",
insertLabel: "add under this lesson (the notebook stays as the teacher made it)", text, x, y }`, and `DeskShell`
already calls `openNotebookMenu(request)` for every checked `menu` message. Once the menus branch is in:

1. Enable the pad menu's marimo row (B6's follow-up). In `PadOverlays.tsx`, replace
   `{ key: "m", glyph: "◆", label: "marimo cell · arrives with notebooks", disabled: true }` with
   `{ ...MARIMO_CELL_ROW, run: close(() => onInsert(MARIMO_CELL_INSERT)) }`, importing both from `../notebook/menuBridge`.
2. Register the opener once. `DeskShell` should hold `setNotebookMenuOpener((request) => openPadMenuFor(request))` in an
   effect, with `setNotebookMenuOpener(null)` on cleanup. `openPadMenuFor` opens the pad menu at `(request.x, request.y)`
   with `request.label` as its head, in the stack window that shows `request.padId`, or the lesson `request.lessonId`.
3. In that stack window, the menu's `onInsert` for a lesson request is
   `(block) => writeUnderLesson(request.lessonId!, block)`, and its insert row reads `request.insertLabel`. For a pad
   request it inserts at the end of `request.padId`. `request.text` is untrusted notebook text: quote it, never render it.

## Fidelity: the mockup's Teacher lesson state with the notebook in the lesson tab

The notebook harness opens the desks' lesson window (`?lesson=1&nblesson=open`), scrolls the stack as the rd9
stage does, and compares at both viewports. It compares RD9a's `LESSON` regions, the whole box of `lesson_frame`,
and, sampled inside the frame on both screenshots, the page colour and the notebook's content margins.

- **What matches:**
  - The frame's height: 528 px at design and 428 px at laptop, within 2 px of the reference's.
  - The page inside the frame (`#f7f5f0`).
  - The notebook's content margins.
  - Every lesson head, mode and mode-line region.
  - The open tab's title and meta.
- **What differs (identical at both viewports):**
  - **The stack's paper is narrower.** The lesson body is 519 px against the reference's 542 (535 against 558 at
    laptop), so the frame is 493 against 516 (509 against 532) and starts 19 px further right (878 against 859; 702
    against 683). This is RD4's stack margins, shared by every pad, and RD9a's record lists it for the parity round.
  - **The paper's and tab's border colour:** `#4a4740` here, `#2a2825` in the reference. Also RD4's stack, also listed by RD9a.
  - **The stack window's head:** text `#d8d8e0` against `#a8a8b8`, background `#151517` against `#161618f0`, and a
    bottom rule `#26262a` against `#000000`. RD4's again.
  - **The frame sits 28 px higher (32 px at laptop):** 259.7 against 288.1 (240.5 against 272.5). The fixture's stack
    has two pads above the lesson where the mockup has three, so the lesson's tab and everything under it sit one tab higher.
  - **The modes:** the mockup has label-only "review · redo · augment", while ours has "lesson · your additions". This is RD9a's honest staging (§11.1), and the comparison doesn't measure it.
  - **The notebook content:** the reference serves the owner's exported `08_softmax_cross_entropy` notebook, ours a
    synthetic project-authored lesson, so headings, prose and cells differ. The reference also shows marimo's "⋯"
    app menu at the frame's top right; ours hides marimo's chrome (`show-chrome=false`, B4).
  - **Below the frame:** the fixture lesson has an additions pad, so "your additions under this lesson" shows under the frame. The mockup's lesson has none in view.
- Pixel share changed: 19.7 % at design, 21.5 % at laptop. This is mostly the book and the notebook's different content.

## Tests

- `tests/test_notebook_lessons.py` (8, new):
  - The vault location.
  - The contract read from the cells (two commit points, held cells above every point, `hide_code`, an unparsable notebook).
  - A commit on a commit point's own control only; a review commits nothing.
  - `lesson.view` with and without a notebook (otherwise identical).
  - A lesson opening on its own notebook with its contract.
  - Refusals: no notebook, an unknown lesson without a path, another path.
  - A finished lesson's notebook opened as a review, with no row written (every table counted).
  - `notebook_release_refused`.
  - The inputs refuse extra fields.
  - Desktop only: the notebook RPCs stay pinned in `test_mobile_allowlist.py`, and no new RPC was added.
- `tests/test_notebook_runtime_sandbox.py` (+2, real bubblewrap):
  - A lesson's held cell is refused before the commit and released after it.
  - The held cell above every commit point is refused.
  - A review commits nothing and releases nothing, and the reveal never shows.
- vitest: `LessonNotebook.test.tsx` (5):
  - What to release and when.
  - The lesson's own session (owner, no path); fast reads while a commit point waits, then the slow reading.
  - Release at the commit, once.
  - A review releasing nothing.
  - A paused window opening nothing.
  - The right-click labelled for the lesson.
- **Harness (`notebook.py`, 36 checks; 5 new for the lesson window):**
  - The lesson's own session, with no path.
  - The head and modes above the notebook.
  - Answering the commit point releases its held cell: 203 ms from the answer to the reveal.
  - A reload rejoins the same kernel.
  - A review says so, and an answer releases nothing.
- **Fail-first:** the real-sandbox release test timed out waiting for the reveal before NBF-4's fix, and passes after it.

## Not verified

- The packaged app (WebKitGTK) with a lesson notebook.
- A lesson notebook produced by a real teacher turn (none can be).
- The menu opening from the frame's right-click (waits on the menus branch).
- A desk move driven by keys: the harness reloads the page instead, and the session is kept the same way by owner key and revision.

## Fix round (adversarial review of the notebook work on main, 2026-11-23)

| Finding | Ledger | What changed | Proof |
|---|---|---|---|
| A lesson closed elsewhere kept accepting commits and releases | NBF-13 | `notebook.status` and `notebook.release` re-read `lessons.closed_at` for a lesson's session and call `runtime.mark_review` when it is closed; `LessonNotebook` releases only while the session is not a review, so it stops at the next reading | Closing the lesson between two releases: the status reads `review: true` and the second release is refused (`notebook_release_refused`) |

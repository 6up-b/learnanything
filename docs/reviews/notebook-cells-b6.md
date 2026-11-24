# Notebook cells B6: marimo cells in pads

- **Base:** branch `notebook/frame-b4-b5`, on top of the frame step (B4–B5), with `reader/rd4-fix-frontend` merged
  again at `8344e01da6` (NBF-1).
- **Scope:** spec §9.2's pad-menu row "◆ marimo cell (m)", §10.4's block kind `cell`, §11.5, and §16's RD9b items
  "marimo `cell` blocks with runtime identity per pad", "moving a pad keeps its kernel" and "two simultaneous
  sessions". No migration, no kill switch, no model call, no owner notebook.
- **Decisions built on (defaults the owner may change):** all of a pad's cells render as **one live framed group
  per pad** (owner key `pad:<id>`) with live widgets, and the learner's cells run in the sandbox like model-written
  ones. §11.5 puts each cell's output under its own code; here the group sits under the pad's last cell, and each
  cell's header carries its own state.

## What was built

| Piece | Where | What it does |
|---|---|---|
| The pad's cells | `pads/cells.py` | The standing `cell` blocks of one pad, in pad order: block id, version id, code, provenance |
| The generated notebook | `notebook_runtime/adapter.py` (`cell_name`, `notebook_from_cells`) | One marimo cell function per block, named `c_<block id>` (a short hash is added when the id has other characters), with marimo's empty signature (marimo reads refs and defs from the body). Tabs are expanded. Code that does not parse becomes marimo's own unparsable cell, so the learner sees marimo's error and not a refused notebook. The same cells always give the same bytes |
| `notebook.open` for a pad | `learnloop_sidecar/handlers/notebooks.py` | `path` may be left out for `pad:<id>`: the handler generates the notebook from the pad's cells, writes the derived copy, and opens it under a revision made from the cells' names in order. The reply carries `padCells` (block id to cell name). A pad with no cells is `notebook_no_cells`, an unknown pad `pad_not_found`, a lesson without a path `notebook_path_invalid` |
| Revision by shape | `notebook_runtime/runtime.py` (`open(..., revision=)`) | A pad's session is kept while the same cells stand in the same order, whatever their code. A stopped session restarts on the code it is reopened with. An inserted, removed or moved cell is a new revision, which replaces the session as before |
| Each cell's run | `supervisor.py` (`note_cell_progress`, `cell_runs`), `proxy.py`, `adapter.cell_progress` | The proxy reads marimo's `cell-op` messages on their way to the frame: running starts a cell's clock, idle stops it (`ms`), an error output marks it. `notebook.status` returns `cellRuns` per cell name |
| The cell in a pad | `screens/desks/notebook/PadCell.tsx`, `notebook.css` | The header "marimo · reactive · runs when you press ⇧↵" (with "· the tutor's" for the tutor's cells) and its state: "kernel not started", "starting kernel…", "running…", "ran in N ms", "raised an error in N ms", "kernel paused · ⇧↵ resumes it". The code is in JetBrains Mono; a click edits it in place (⇧↵ runs, tab indents, esc puts it back, leaving the cell commits the edit). Under the pad's last cell, once started, the one `NotebookFrame` for the pad |
| The pad's shared state | `screens/desks/notebook/padNotebooks.ts` | Per pad: started, the frame's generation, the last session reading, each block's cell name, the shape the session was made from, pending runs. It lives as long as the app, so a pad that moves or remounts finds its kernel started |
| The pad's one case | `pads/PadStackWindow.tsx` (17 lines) | `case "cell"` renders `PadCell` with the ◆ gutter mark; the pad's Markdown editor skips `cell` as it skips `sketch` |
| The menu hooks | `screens/desks/notebook/menuBridge.ts`, `DeskShell.tsx` | `MARIMO_CELL_INSERT` (the row's insert) and `MARIMO_CELL_ROW`; `notebookMenuRequest` labels a frame's right-click for its owner; `setNotebookMenuOpener` / `openNotebookMenu`. The desks' bridge host now sends `menu` there |
| The theme's prose rule | `notebook_runtime/theme.py` | The one non-variable rule now also names `.paragraph`: marimo renders a Markdown paragraph as `span.paragraph`, so the rule's first selectors (`p`, `li`) missed it. The theme is still variables plus that one rule (NBF-2) |

## How a run goes

1. The first ⇧↵ (or the cell's ▶) commits the cell's edit as an `edit_block` through the pad's write protocol,
   waits for the desk store to settle (the sidecar generates the notebook from what is saved), and starts the
   pad's kernel: the framed group mounts under the last cell and calls `notebook.open` for `pad:<id>`. marimo runs
   every cell when it loads.
2. A later ⇧↵ on a cell whose code changed commits the edit and sends the code to the live kernel
   (`notebook.run_cells` under the cell's name); marimo's reactive graph reruns what depends on it. The header
   reads "running…" until a status reading shows the cell idle.
3. A ⇧↵ after the pad's cells changed shape (inserted, removed, moved), or after the session stopped or failed,
   bumps the frame's generation: the frame remounts and opens the new revision, and the sidecar replaces the session.
4. Moving the pad (another desk, another window) remounts the frame with the same owner key and the same revision:
   the frame rejoins the same session and process, and marimo replays its outputs and control values.

## Decisions and why

- **No migration.** `cell` is already in `BlockKind`, in `EDITABLE_KINDS` and in the pad block CHECK constraint
  (migration 262), so insert, edit, move and remove are the ops every block uses: versions append-only,
  provenance kept (an edit of the tutor's cell keeps `tutor`). 269 was not taken.
- **Emission.** The contract already leaves cells out: `pads.emission.EMITTED` emits `text`, `note` and `ink` only,
  so a cell's code is never learner text for the gap pipeline. Cells stay out; nothing in persisted meaning moves,
  and no owner question arises. `tests/test_notebook_pad_cells.py` pins it.
- **Where the generated notebook lives.** `.learnloop/notebooks/pads/<pad id>.py` under the vault. `.learnloop/` is
  machine-local state that the loader and the vault watcher leave alone, so the file never reads as a source or a
  note. It is not a table, so `table_roles` and the rebuild orchestrator have nothing to classify or replay: the
  pad's block versions are the only source, the file is rewritten (atomically) on every open, and deleting it
  loses nothing. The runtime still runs its own snapshot of the bytes in the session's run directory; the vault
  copy is there to inspect and to open in marimo by hand.
- **Revision by shape, edits through the live kernel.** A revision made from the bytes would replace the session on
  every edit and lose the learner's control values and state. Keyed on the cells' names in order, the session
  follows the pad's structure, and an edit reaches the kernel the way marimo's own editor sends one.
- **Cell names are generated from block ids**, not stored: the same pad always gives the same notebook, and the
  open's `padCells` gives the client the mapping.
- **The menu row stays disabled here.** The menus are on `reader/rd5b-menus-ui`, which this branch does not merge.
  The follow-up is below.

## Follow-ups once the menus branch is in

1. **Enable the marimo row** in `screens/desks/pads/PadOverlays.tsx`: replace the disabled row
   `{ key: "m", glyph: "◆", label: "marimo cell · arrives with notebooks", disabled: true }` with
   `{ ...MARIMO_CELL_ROW, run: close(() => onInsert(MARIMO_CELL_INSERT)) }` and import both from
   `../notebook/menuBridge`. (If the menu now lives in `screens/desks/menu`, the same two lines go where its pad
   rows are listed, with that menu's own insert callback in place of `onInsert`.)
2. **Open the pad menu from a frame's right-click**: where the menu mounts, call
   `setNotebookMenuOpener((request) => openPadMenu({ x: request.x, y: request.y, padId: request.padId,
   lessonId: request.lessonId, label: request.label, insertLabel: request.insertLabel, text: request.text }))` in an
   effect, and `setNotebookMenuOpener(null)` on cleanup. `request.text` is untrusted notebook text: quote it, never
   render it. For a lesson (`lessonId`), the menu's inserts go to the lesson's additions pad, labelled "add under
   this lesson (the notebook stays as the teacher made it)".

## Tests

- `tests/test_notebook_pad_cells.py` (8, new): cells as pad blocks with append-only versions and their provenance;
  the notebook generated in pad order, `padCells` and `cellRuns` keys kept as they are, the derived file written;
  the same cells give the same bytes and revision; an edit keeps the revision, an insert, a move and a remove each
  change it (back to the first revision once the shape is the same again); refusals (no cells, no pad, a lesson
  without a path); a cell's code is never learner text; the generated notebook loads in marimo with the right
  refs (tab-indented code included) and an unparsable cell as marimo's error cell; cell names.
- `tests/test_notebook_runtime.py` (+3): a named revision keeps the session while its code changes, a new one
  replaces it; a stopped session restarts on the reopened code; a cell's run timed from marimo's messages.
  The theme test now pins the rule's completed selectors.
- `tests/test_notebook_runtime_sandbox.py` (+2, real bubblewrap): two pads' cells run in isolated sessions (other
  processes, run directories and control values; a control moved in one leaves the other); moving a pad keeps its
  kernel (same session and process after a reopen with edited code), an edited cell runs in that kernel
  (`run_cells`, timed in `cellRuns`), and a new cell makes a new session and stops the old process.
- vitest: `padNotebooks.test.ts` (8) and `PadCell.test.tsx` (4).
- The notebook harness (`scripts/desk_harness/notebook.py`) adds a pad fixture (`?padcells=1`) holding a line and
  two cells (a slider and a wigglystuff `Slider2D` anywidget, and a softmax computed from the slider), run in a real
  sandboxed session through the page's RPCs. Its checks: no kernel before ⇧↵; the first ⇧↵ starts one framed
  group under the last cell (4.1 s to output); each header reads "ran in N ms"; the slider reruns the dependent
  cell and the anywidget renders; an edited cell runs in the live kernel (108 ms to output, same session and
  process); the edit is the pad's `edit_block`; moving the pad's window keeps its kernel and output.
  31 of 31 checks pass.

## Visual reference

The reference set's states that would show a cell in a pad (`s11=run`; also `s11=menu` and `s11=sketchqk`) show
none: in the `arxiv_v2` variant `s11=run` was not applied, and in `arxiv_v2_goal`, where it was, the running pad
holds no cell in view (the companion covers the pad's lower half). Every capture also records the mockup's
pyodide import failing. So no mockup state shows a cell in a pad and there is nothing to compare; the cell's
look follows §11.5's words and the pad's existing tutor-voice card. A recapture with a cell in view would let
the notebook stage compare it.

## Not verified

- The packaged app (WebKitGTK) with a pad's cells; B5 checked the frame itself there.
- The menu row and the frame's right-click opening the pad menu (both wait on the menus branch).
- Two windows showing the same pad at once: both mount a frame on the same session, which marimo allows, but the
  harness shows one.

## Fix round (adversarial review of the notebook work on main, 2026-11-23)

| Finding | Ledger | What changed | Proof |
|---|---|---|---|
| Derived notebook writes followed links out of the vault (`.learnloop/notebooks/pads` as a link; a link at the fixed temporary name) | NBF-6 | `hostfiles.write_beneath` opens every directory below the vault without following links, writes an unpredictable temporary created exclusively, and replaces through the directory's descriptor; a refusal is `notebook_path_invalid` | `test_the_derived_notebook_never_follows_a_link_out_of_the_vault`: a link at the folder is refused with nothing written outside; links at the temporary and target names leave their target untouched |
| A crash restart ran obsolete pad code | NBF-14 | `notebook.open` passes the pad's cells to the runtime; `run_cells` writes the code that ran into the snapshot a restart loads (through `hostfiles`), and a reopen of the same revision always rewrites the snapshot | After running `x = 2` the snapshot holds `x = 2`, not `x = 1`; a live reopen with `x = 3` keeps the session and refreshes the snapshot |
| Frontend notebook state crossed vaults (registry keyed by pad id only) | NBF-15 | `PadCell` keys the shared state by `padNotebookKey(store.clientId, padId)`: the desk store is one per vault, and so is its client id. A frame of the old vault unmounts with it, so a late reading lands under the old key | A run in vault A leaves the same pad id in vault B at "kernel not started" |
| Generated notebooks bypassed the 2 MiB limit; ids differing only in case shared a cell name (and a derived file name) | NBF-17, NBF-18 | `pad_notebook` refuses generated bytes over `NOTEBOOK_MAX_BYTES` and duplicate names before writing; `cell_name` hashes the exact id whenever it differs from its lower-case identifier (ULID block ids now carry the hash; nothing persists a name) | A cell past the limit is refused with nothing written or opened; `A`/`a` and `blk_01ABC`/`blk_01abc` get distinct names |

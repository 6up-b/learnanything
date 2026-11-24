// The pad menu and notebooks. The bridge's `menu` message (spec §11.3): a right-click inside a notebook frame opens the pad menu, labelled for
// what the notebook belongs to. The desks hand every checked `menu` message here; the menu (screens/desks/menu)
// registers its opener with `setNotebookMenuOpener`, and until it does nothing opens (the frame keeps its own
// shift+right-click). See docs/reviews/notebook-cells-b6.md for the wiring.
import type { NotebookOwner } from "../../../api/dto";
import type { BridgeMessage } from "./bridge";

// What the pad menu's marimo row inserts (spec §9.2: "◆ marimo cell (m)", "Python that runs beside your notes,
// reactive"): an empty `cell` block, the learner's, run in the sandbox like every cell. The menu's row calls the
// menu's own insert with this; docs/reviews/notebook-cells-b6.md has the two lines that enable it.
export const MARIMO_CELL_INSERT = { kind: "cell", provenance: "learner", bodyMd: "", payload: {} } as const;
export const MARIMO_CELL_ROW = { key: "m", glyph: "◆", label: "marimo cell", note: "Python that runs beside your notes, reactive" } as const;

export interface NotebookMenuRequest {
  owner: NotebookOwner;
  /** The pad the menu's inserts go to: the pad itself, or the lesson's additions pad (found by the lesson id). */
  padId: string | null;
  lessonId: string | null;
  /** The selection in the frame, as untrusted notebook text. */
  text: string;
  /** Page coordinates, inside the frame's box. */
  x: number;
  y: number;
  /** The menu's header label and its insert row's label (spec §11.3). */
  label: string;
  insertLabel: string;
}

export function notebookMenuRequest(message: BridgeMessage, owner: NotebookOwner): NotebookMenuRequest | null {
  if (message.ll !== "menu") return null;
  const [kind, ...rest] = owner.split(":");
  const id = rest.join(":");
  if (kind === "lesson") {
    return { owner, padId: null, lessonId: id, text: message.text, x: message.x, y: message.y, label: "the lesson",
      insertLabel: "add under this lesson (the notebook stays as the teacher made it)" };
  }
  return { owner, padId: id, lessonId: null, text: message.text, x: message.x, y: message.y, label: "your pad",
    insertLabel: "insert at the end of this pad" };
}

let opener: ((request: NotebookMenuRequest) => void) | null = null;

/** The menu registers how it opens (and clears it with null). */
export function setNotebookMenuOpener(next: ((request: NotebookMenuRequest) => void) | null): void {
  opener = next;
}

/** Open the pad menu for a frame's right-click; false while no menu is registered. */
export function openNotebookMenu(request: NotebookMenuRequest): boolean {
  if (!opener) return false;
  opener(request);
  return true;
}

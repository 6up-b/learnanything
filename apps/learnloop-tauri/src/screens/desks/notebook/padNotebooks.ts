// A pad's marimo cells and the one live session they share (spec §11.5).
//
// The pad is the source of truth: its `cell` blocks are written, edited, moved and removed with the pad ops every
// block uses, and the sidecar generates the notebook from them on each open. The session belongs to the pad
// (`pad:<id>`), never to its desk or window, so moving the pad keeps its kernel. The kernel starts on the pad's
// first ⇧↵; a cell whose code changed runs in the live kernel (`notebook.run_cells`, the reactive graph reruns
// what depends on it), while a cell added, removed or moved makes a new notebook revision, which the frame
// reopens (the sidecar replaces the session; marimo runs every cell on load).
//
// This module holds, per pad, what the pad's cell blocks and its framed group share: whether the kernel was
// started, the session's last reading, and each cell block's marimo name. It lives as long as the app does, so a
// pad that moves or remounts finds its kernel started.
import type { NotebookCellRunDto, NotebookSessionDto } from "../../../api/dto";

export interface PadNotebook {
  /** The pad's kernel was started (its first ⇧↵); the framed group shows from then on. */
  started: boolean;
  /** Bumped when the pad's cells change shape (added, removed, moved): the frame reopens the new revision. */
  generation: number;
  session: NotebookSessionDto | null;
  /** Each cell block's marimo name in the session's notebook. */
  names: Record<string, string>;
  /** The cell blocks (in pad order) the session's notebook was generated from. */
  shape: string[];
  /** A run asked for and not yet seen idle, by block id (its header reads "running…"). */
  pending: Record<string, true>;
  error: string | null;
}

const EMPTY: PadNotebook = { started: false, generation: 0, session: null, names: {}, shape: [], pending: {}, error: null };
const pads = new Map<string, PadNotebook>();
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

export function padNotebook(padId: string): PadNotebook {
  return pads.get(padId) ?? EMPTY;
}

function update(padId: string, change: (now: PadNotebook) => PadNotebook): void {
  pads.set(padId, change(padNotebook(padId)));
  emit();
}

export function subscribePadNotebooks(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The pad's shape: its cell blocks in pad order. */
export function cellShape(blocks: { blockId: string; kind: string }[]): string[] {
  return blocks.filter((block) => block.kind === "cell").map((block) => block.blockId);
}

/** Whether a ⇧↵ needs the frame (re)opened: the kernel not started yet, the pad's cells changed shape since the
 * session's notebook was made, or the session stopped (idle) or failed. Otherwise the cell runs in the live kernel. */
export function needsOpen(state: PadNotebook, shape: string[]): boolean {
  const session = state.session;
  return !state.started || state.shape.join("|") !== shape.join("|") || session?.state === "stopped" || session?.state === "failed";
}

/** Start the pad's kernel (its first ⇧↵), or reopen it (a new shape, a stopped or failed session). */
export function startPadNotebook(padId: string, shape: string[]): void {
  update(padId, (now) => ({ ...now, started: true, generation: now.started ? now.generation + 1 : now.generation, shape,
    session: now.started ? null : now.session, error: null }));
}

/** A reading of the pad's session (the frame's open or status). An open carries each cell block's name. */
export function notePadSession(padId: string, session: NotebookSessionDto): void {
  update(padId, (now) => {
    const names = session.padCells ?? now.names;
    const pending = { ...now.pending };
    for (const [blockId, name] of Object.entries(names)) {
      const run = session.cellRuns?.[name];
      if (run && run.status === "idle") delete pending[blockId];
    }
    return { ...now, session, names, pending };
  });
}

export function noteRunPending(padId: string, blockId: string, error: string | null = null): void {
  update(padId, (now) => ({ ...now, pending: error ? now.pending : { ...now.pending, [blockId]: true }, error }));
}

/** A cell block's last run, or null before its kernel ran it. */
export function cellRun(state: PadNotebook, blockId: string): NotebookCellRunDto | null {
  const name = state.names[blockId];
  return name ? state.session?.cellRuns?.[name] ?? null : null;
}

/** The header's state line (spec §11.5): kernel not started, starting kernel…, ran in N ms. */
export function cellStateLine(state: PadNotebook, blockId: string): string {
  if (!state.started) return "kernel not started";
  if (state.error) return state.error;
  const session = state.session;
  if (!session || session.state === "starting" || session.state === "restarting" || !state.names[blockId]) return "starting kernel…";
  if (session.state === "stopped") return "kernel paused · ⇧↵ resumes it";
  if (session.state === "failed") return `the kernel couldn't run: ${session.error ?? "it stopped"}`;
  const run = cellRun(state, blockId);
  if (state.pending[blockId] || run?.status === "running" || run?.status === "queued") return "running…";
  if (run?.error) return run.ms === null ? "raised an error" : `raised an error in ${Math.round(run.ms)} ms`;
  if (run?.ms !== null && run?.ms !== undefined) return `ran in ${Math.round(run.ms)} ms`;
  return "ran";
}

/** Tests only: forget every pad. */
export function resetPadNotebooksForTests(): void {
  pads.clear();
  emit();
}

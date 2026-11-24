// A marimo cell in a pad (spec §10.4 `cell`, §11.5): its header ("marimo · reactive · runs when you press ⇧↵")
// with the cell's state, its code (the learner's, or the tutor's with its provenance shown), and, under the pad's
// last cell, the one live framed group that shows every cell's output (widgets live), served by the pad's
// sandboxed session. The pad renders this for its `cell` blocks; everything else about cells lives here.
import { useCallback, useEffect, useRef, useState, useSyncExternalStore, type KeyboardEvent } from "react";
import { api } from "../../../api/client";
import type { PadBlockDto } from "../../../api/dto";
import { usePadsHost } from "../pads/host";
import { NotebookFrame } from "./NotebookFrame";
import {
  cellShape,
  cellStateLine,
  needsOpen,
  notePadSession,
  noteRunPending,
  padNotebook,
  padNotebookKey,
  startPadNotebook,
  subscribePadNotebooks,
} from "./padNotebooks";

/** How often, and how long, a cell's state is read after ⇧↵ sends its code (its "ran in N ms" arrives with
 * marimo's report of the run). keep: display polling, not a parameter. */
export const RUN_POLL = { everyMs: 250, forMs: 6000 } as const;
/** The framed group's height in the pad. */
export const GROUP_HEIGHT_PX = 380;

export interface PadCellProps {
  padId: string;
  block: PadBlockDto;
  /** The pad's blocks in order (the cells' shape, and which cell is last). */
  blocks: PadBlockDto[];
  /** False while the pad window is paused: the code shows, nothing edits or runs. */
  editable: boolean;
  /** Write the cell's new code (an `edit_block` through the pad's write protocol). */
  onCommit: (code: string) => void;
}

function message(error: unknown): string {
  return error && typeof error === "object" && typeof (error as { message?: unknown }).message === "string"
    ? (error as { message: string }).message
    : String(error);
}

export function PadCell({ padId, block, blocks, editable, onCommit }: PadCellProps) {
  const host = usePadsHost();
  // The shared state is the pad's in this vault: another vault (a copy) may hold a pad of the same id, and its
  // kernel is its own. The desk store is one per vault, and so is its client id.
  const key = padNotebookKey(host?.store.clientId ?? "", padId);
  const state = useSyncExternalStore(subscribePadNotebooks, () => padNotebook(key));
  const [draft, setDraft] = useState<string | null>(null);
  const area = useRef<HTMLTextAreaElement | null>(null);
  const shape = cellShape(blocks);
  const last = shape[shape.length - 1] === block.blockId;

  useEffect(() => {
    if (draft !== null) area.current?.focus();
  }, [draft !== null]);

  const run = useCallback(async (code: string) => {
    if (code !== block.bodyMd) onCommit(code);
    const now = padNotebook(key);
    noteRunPending(key, block.blockId);
    if (needsOpen(now, shape)) {
      // The sidecar generates the notebook from the pad as it is saved: its writes land first.
      await host?.store.settled();
      startPadNotebook(key, shape);
      return;
    }
    const name = now.names[block.blockId];
    if (!name || !now.session) return;
    try {
      await api.notebookRunCells({ sessionId: now.session.sessionId, cells: [{ name, code }] });
    } catch (error) {
      noteRunPending(key, block.blockId, `couldn't run: ${message(error)}`);
      return;
    }
    const sessionId = now.session.sessionId;
    const until = Date.now() + RUN_POLL.forMs;
    while (Date.now() < until && padNotebook(key).pending[block.blockId]) {
      await new Promise((resolve) => setTimeout(resolve, RUN_POLL.everyMs));
      try {
        notePadSession(key, await api.notebookStatus({ sessionId }));
      } catch {
        return;
      }
    }
  }, [block.blockId, block.bodyMd, host, onCommit, key, shape.join("|")]);

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && event.shiftKey) {
      event.preventDefault();
      void run(draft ?? block.bodyMd);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setDraft(null);
      return;
    }
    if (event.key === "Tab") {
      // Code indents; focus stays in the cell.
      event.preventDefault();
      const target = event.currentTarget;
      const { selectionStart, selectionEnd, value } = target;
      const next = `${value.slice(0, selectionStart)}    ${value.slice(selectionEnd)}`;
      setDraft(next);
      requestAnimationFrame(() => target.setSelectionRange(selectionStart + 4, selectionStart + 4));
    }
  };

  const tutor = block.provenance === "tutor";
  return (
    <div className="ll-cell" data-cell-block={block.blockId}>
      <div className="ll-cell-head">
        <span className="what">marimo · reactive · runs when you press ⇧↵{tutor ? " · the tutor's" : ""}</span>
        <span className="state" data-cell-state="">{cellStateLine(state, block.blockId)}</span>
        {editable ? (
          <button type="button" className="run" aria-label="run this cell" onClick={() => void run(draft ?? block.bodyMd)}>▶</button>
        ) : null}
      </div>
      {draft !== null && editable ? (
        <div className="ll-cell-editor" data-desk-typing="">
          <textarea
            ref={area}
            value={draft}
            spellCheck={false}
            aria-label="edit this cell's code"
            rows={Math.max(2, draft.split("\n").length)}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            onBlur={() => {
              if (draft !== block.bodyMd) onCommit(draft);
              setDraft(null);
            }}
          />
          <div className="hintline">python · ⇧↵ runs · tab indents · esc puts it back</div>
        </div>
      ) : (
        <pre className="ll-cell-code" onClick={() => editable && setDraft(block.bodyMd)}>{block.bodyMd || "# Python, run beside your notes"}</pre>
      )}
      {last && state.started ? (
        <div className="ll-cell-group" data-cell-group="">
          <NotebookFrame
            key={state.generation}
            owner={`pad:${padId}`}
            title="your marimo cells"
            style={{ height: GROUP_HEIGHT_PX }}
            onSession={(session) => notePadSession(key, session)}
          />
        </div>
      ) : null}
    </div>
  );
}

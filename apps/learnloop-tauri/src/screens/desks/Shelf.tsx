// The shelf (spec §5.6): the strip's minimap, one row per window, with what is in view, how far the
// learner has read, and where. A click focuses the row's window; dragging a row more than 5 px
// reorders the strip. Below 1400 px it folds to a 44 px rail whose ☰ overlays it.
import { useRef, useState, type PointerEvent as ReactPointerEvent } from "react";

export interface ShelfRow {
  windowId: string;
  slot: number;
  glyph: string;
  kind: string;
  title: string;
  state: "focus" | "in view" | null;
  /** 0..1 through the source, when known. */
  progress: number | null;
  where: string | null;
}

/** Drag farther than this before a press becomes a reorder (spec §5.2). */
const DRAG_THRESHOLD_PX = 5;

export function Shelf({
  rows,
  folded,
  undo,
  onFocus,
  onReorder,
  onSearch,
  carried = [],
  carriedMore = 0,
}: {
  rows: ShelfRow[];
  folded: boolean;
  /** CARRIED (spec §10.12): at most the attention limit, each "since <date>"; the rest are in the library. */
  carried?: Array<{ carriedId: string; text: string; since: string }>;
  carriedMore?: number;
  undo: { title: string; onUndo: () => void } | null;
  onFocus: (windowId: string) => void;
  onReorder: (windowId: string, toSlot: number) => void;
  /** "/ switch": search in context (spec §9.3). */
  onSearch?: () => void;
}) {
  const [open, setOpen] = useState(false);
  if (folded && !open) {
    return (
      <aside className="desk-shelf-rail" aria-label="this desk's windows">
        <button type="button" aria-label="show the strip" title="the strip" onClick={() => setOpen(true)}>☰</button>
      </aside>
    );
  }
  const body = (
    <>
      <ShelfBody rows={rows} undo={undo} onFocus={(id) => { onFocus(id); if (folded) setOpen(false); }} onReorder={onReorder} onSearch={onSearch ? () => { onSearch(); if (folded) setOpen(false); } : undefined} />
      {carried.length ? (
        <div className="desk-carried" data-shelf-carried="">
          <h4><span>Carried</span></h4>
          {carried.map((question) => (
            <div key={question.carriedId} className="q" title={question.text}>
              <span className="t">? {question.text}</span>
              <span className="s">since {new Date(question.since).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span>
            </div>
          ))}
          {carriedMore > 0 ? <div className="more">three shown (an attention limit) · {carriedMore} more in the library</div> : null}
        </div>
      ) : null}
    </>
  );
  if (folded) {
    return (
      <>
        <aside className="desk-shelf-rail" aria-label="this desk's windows">
          <button type="button" aria-label="hide the strip" onClick={() => setOpen(false)}>☰</button>
        </aside>
        <div className="desk-shelf desk-shelf-overlay">{body}</div>
      </>
    );
  }
  return <aside className="desk-shelf" aria-label="this desk's windows">{body}</aside>;
}

function ShelfBody({
  rows,
  undo,
  onFocus,
  onReorder,
  onSearch,
}: {
  rows: ShelfRow[];
  undo: { title: string; onUndo: () => void } | null;
  onFocus: (windowId: string) => void;
  onReorder: (windowId: string, toSlot: number) => void;
  onSearch?: () => void;
}) {
  const press = useRef<{ windowId: string; y: number; dragging: boolean } | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);

  const slotAt = (clientY: number): number => {
    const list = listRef.current;
    if (!list) return 0;
    const items = [...list.querySelectorAll<HTMLElement>("[data-shelf-slot]")];
    let target = 0;
    for (const item of items) {
      const box = item.getBoundingClientRect();
      if (clientY > box.top + box.height / 2) target = Number(item.dataset.shelfSlot);
    }
    return target;
  };

  const onPointerDown = (row: ShelfRow) => (event: ReactPointerEvent<HTMLButtonElement>) => {
    press.current = { windowId: row.windowId, y: event.clientY, dragging: false };
  };
  const onPointerMove = (event: ReactPointerEvent<HTMLButtonElement>) => {
    const current = press.current;
    if (!current || current.dragging) return;
    if (Math.abs(event.clientY - current.y) > DRAG_THRESHOLD_PX) {
      current.dragging = true;
      setDragging(current.windowId);
      event.currentTarget.setPointerCapture?.(event.pointerId);
    }
  };
  const onPointerUp = (row: ShelfRow) => (event: ReactPointerEvent<HTMLButtonElement>) => {
    const current = press.current;
    press.current = null;
    setDragging(null);
    if (current?.dragging) {
      const to = slotAt(event.clientY);
      if (to !== row.slot) onReorder(current.windowId, to);
      return;
    }
    onFocus(row.windowId);
  };

  return (
    <>
      <h4><span>Strip</span><span className="grow" />{onSearch ? <button type="button" className="switch" title="search in context (/)" onClick={onSearch}>/ switch</button> : null}</h4>
      <div className="rows ll-scroll" ref={listRef}>
        {rows.map((row) => (
          <button
            key={row.windowId}
            type="button"
            data-shelf-slot={row.slot}
            data-shelf-window={row.windowId}
            className={`desk-src${row.state ? " open" : ""}${row.state === "focus" ? " prim" : ""}${dragging === row.windowId ? " dragging" : ""}`}
            onPointerDown={onPointerDown(row)}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp(row)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onFocus(row.windowId);
              }
            }}
          >
            <div className="k">
              <span>{row.glyph} {row.kind}</span>
              {row.state ? <span>· {row.state}</span> : null}
            </div>
            <div className="n">{row.title}</div>
            {row.progress !== null ? (
              <div className="bar" aria-label={`${Math.round(row.progress * 100)}% through`}>
                <span className="ln" />
                <span className="rd" style={{ width: `${Math.max(0, Math.min(1, row.progress)) * 100}%` }} />
              </div>
            ) : null}
            {row.where ? <div className="w">{row.where}</div> : null}
          </button>
        ))}
      </div>
      <div className="lower">
        {undo ? (
          <button type="button" className="undo" onClick={undo.onUndo}>↺ undo close {undo.title}</button>
        ) : null}
      </div>
    </>
  );
}

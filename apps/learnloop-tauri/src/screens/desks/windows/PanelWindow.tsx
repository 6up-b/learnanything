// Panel windows (spec §5.2, §21.1): the v1 Reader's surfaces that have no workbench home yet, hosted
// unchanged inside desk windows until their replacements land.
//
// - guide, notes: the source window of that book renders its rail (Guide, Ask, Notes) into this
//   window's body, so the rail keeps the one Reader state it belongs to; this window opens it on its tab.
// - path: the reading-path card, its jumps going to the book's window on the desk.
// - library, compare: the library pane (ask across the library, compare), its hits opening beside.
import { useCallback, useState } from "react";
import { useCachedQuery } from "../../../api/useCachedQuery";
import { api } from "../../../api/client";
import type { ContentRefDto, LibraryHitDto } from "../../../api/dto";
import { ReadingPathCard } from "../../reader/ReadingPathCard";
import { LibraryPane } from "../../reader/LibraryPane";
import { useLibraryAsk } from "../../reader/useLibraryAsk";

type PanelContent = Extract<ContentRefDto, { kind: "panel" }>;

export const PANEL_TITLES: Record<PanelContent["panel"], string> = {
  guide: "Guide",
  notes: "Notes",
  path: "Reading path",
  library: "Library",
};

/** The body a source window's rail moves into. */
export function RailHostPanel({
  panel,
  bound,
  claimed,
  onNode,
  onClaim,
}: {
  panel: "guide" | "notes";
  /** A source window of this book is on the desk. */
  bound: boolean;
  /** Another panel window on this desk already shows this book's rail. */
  claimed: boolean;
  onNode: (node: HTMLElement | null) => void;
  onClaim: () => void;
}) {
  if (!bound) {
    return <div className="desk-panel desk-quiet">Open this book on the desk to see its {panel === "guide" ? "guide" : "notes"} here.</div>;
  }
  if (claimed) {
    return (
      <div className="desk-panel desk-quiet">
        This book’s sidebar is in another window on this desk. <button type="button" onClick={onClaim}>show it here</button>
      </div>
    );
  }
  return <div ref={onNode} data-rail-host={panel} style={{ display: "flex", flexDirection: "column", minHeight: 0, height: "100%" }} />;
}

export function PathPanel({ extractionId, onJump, onError }: { extractionId: string | null; onJump: (spanId: string) => void; onError: (message: string) => void }) {
  if (!extractionId) return <div className="desk-panel desk-quiet">A reading path belongs to a book: open one beside it.</div>;
  return (
    <div className="desk-panel ll-scroll">
      <ReadingPathCard extractionId={extractionId} onJump={onJump} onTryExercise={null} onError={onError} />
    </div>
  );
}

/** The library pane in a window: ask across the library and compare; a hit opens beside. With a query
 * (a Compare window), the box starts with it; nothing runs until the learner asks. A Compare window opened from a
 * passage keeps its anchor: asking there runs the comparison anchored on that passage (the selection's door). */
export function LibraryPanel({
  query,
  anchor = null,
  onOpenHit,
  onClose,
  onError,
}: {
  query: string | null;
  anchor?: { extractionId: string; spanIds: string[]; sourceId: string; revisionId: string | null } | null;
  onOpenHit: (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">) => void;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const contractQuery = useCachedQuery(["reader_prompt_contract"], () => api.readerPromptContract(), {});
  const ctl = useLibraryAsk({ contract: contractQuery.data ?? null, openSourceId: null, onError });
  const [compose, setCompose] = useState<string | null>(query ?? "");
  const ask = useCallback((text: string) => {
    setCompose(null);
    if (anchor && ctl.scopeOn) {
      ctl.compareFrom({ door: "selection", question: text, extractionId: anchor.extractionId, anchorSpanIds: anchor.spanIds,
        openSourceId: anchor.sourceId, identity: { sourceId: anchor.sourceId, revisionId: anchor.revisionId, extractionId: anchor.extractionId } });
      return;
    }
    ctl.ask(anchor
      ? { query: text, entry: "library_search", extractionId: anchor.extractionId, spanIds: anchor.spanIds,
        identity: { sourceId: anchor.sourceId, revisionId: anchor.revisionId, extractionId: anchor.extractionId } }
      : { query: text, entry: "library_search", extractionId: null, spanIds: [], identity: null });
  }, [ctl, anchor]);
  if (!contractQuery.data) return <div className="desk-panel desk-quiet">◐ {contractQuery.error ? "Couldn’t load library settings. Reopen this window to try again." : "Loading library settings…"}</div>;
  if (!ctl.enabled) return <div className="desk-panel desk-quiet">Asking across the library is off. Open a source to keep reading.</div>;
  return (
    <div style={{ display: "flex", minHeight: 0, height: "100%" }}>
      <LibraryPane
        ctl={ctl}
        compose={compose}
        onCompose={setCompose}
        onAsk={ask}
        onOpenHit={onOpenHit}
        onPracticePick={null}
        onClose={onClose}
        stacked
      />
    </div>
  );
}

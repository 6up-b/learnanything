// Panel windows (spec §5.2, §21.1): the v1 Reader's surfaces that have no workbench home yet, hosted
// unchanged inside desk windows until their replacements land.
//
// - guide, notes: the source window of that book renders its rail (Guide, Ask, Notes) into this
//   window's body, so the rail keeps the one Reader state it belongs to; this window opens it on its tab.
// - path: no longer a window (the reading's path is the book window's own, `p`); a stored one is restored there
//   (model/restore.ts). Its title stays for that line.
// - library, compare: the library pane (ask across the library, compare, keep, roles), its hits opening beside;
//   a practice pick or a textbook exercise chosen there opens in its book's window beside.
import { useCallback, useState } from "react";
import { useCachedQuery } from "../../../api/useCachedQuery";
import { api } from "../../../api/client";
import type { ContentRefDto, LibraryHitDto, ProposedItemDto, SourceLibraryCard } from "../../../api/dto";
import { algoConfig } from "../../../app/algoConfig";
import { LibraryPane } from "../../reader/LibraryPane";
import { useLibraryAsk } from "../../reader/useLibraryAsk";
import { CompareKeepContext } from "../../reader/compareKeepContext";
import { NotesContext } from "../../reader/notesContext";
import { useKeptComparisons } from "../../reader/useKeptComparisons";
import { useNoteMarks } from "../../reader/ReaderNotes";
import { exerciseOpenRequest, type ExerciseCandidate } from "../../reader/exerciseCandidates";
import type { LibraryExercisesProps } from "../../reader/ProposalExercises";
import type { ReaderPassThrough } from "./SourceWindow";

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

/** The library pane in a window: ask across the library and compare; a hit opens beside. With a query
 * (a Compare window), the box starts with it; nothing runs until the learner asks. A Compare window opened from a
 * passage keeps its anchor: asking there runs the comparison anchored on that passage (the selection's door). */
export function LibraryPanel({
  query,
  anchor = null,
  onOpenHit,
  onClose,
  onError,
  library = null,
  reader = null,
}: {
  query: string | null;
  anchor?: { extractionId: string; spanIds: string[]; sourceId: string; revisionId: string | null } | null;
  onOpenHit: (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">) => void;
  onClose: () => void;
  onError: (message: string) => void;
  /** The library's books (a pick opens in its book's window). */
  library?: SourceLibraryCard[] | null;
  /** The shell's practice hand-offs (a check, a textbook exercise), as a source window has them. */
  reader?: ReaderPassThrough | null;
}) {
  const contractQuery = useCachedQuery(["reader_prompt_contract"], () => api.readerPromptContract(), {});
  const contract = contractQuery.data ?? null;
  const ctl = useLibraryAsk({ contract, openSourceId: anchor?.sourceId ?? null, onError });
  // Keep and the learner's take work here as on a book's library pane: a keep marks the passages it touched in
  // every book window (each reads its marks again), and the take goes to the learner's notes.
  const kept = useKeptComparisons({ contract, extractionId: anchor?.extractionId ?? null, sourceId: anchor?.sourceId ?? null, offline: false });
  const notes = useNoteMarks({ settings: contract?.notes, extractionId: anchor?.extractionId ?? null, offline: false });
  const cardOf = (sourceId: string | null | undefined) => (sourceId ? (library ?? []).find((card) => card.sourceId === sourceId) : undefined);
  // "practice this ▸": a learner pick at the passage asked on (else the answer's first), in that book; the book
  // opens (or is focused) beside, where the check opens, as the library page did with the workbench on.
  const pickPractice = (item: ProposedItemDto, proposalId: string | null) => {
    const asked = ctl.state?.request;
    const hit = ctl.state?.ask.value?.hits[0];
    const at = asked?.identity
      ? { sourceId: asked.identity.sourceId, revisionId: asked.identity.revisionId, extractionId: asked.identity.extractionId, spanId: asked.spanIds[0] ?? "" }
      : hit ? { sourceId: hit.sourceId, revisionId: null, extractionId: hit.extractionId, spanId: hit.spanId } : null;
    const card = cardOf(at?.sourceId);
    if (!at || !card || !reader?.onCheckMe) return;
    reader.onCheckMe({ practiceItemId: item.practiceItemId, proposalId, spanId: at.spanId, card,
      reading: { sourceId: card.sourceId, revisionId: at.revisionId, extractionId: at.extractionId } });
    onOpenHit({ sourceId: card.sourceId, extractionId: at.extractionId, spanId: at.spanId });
  };
  // A textbook exercise (RW4b): "use this one" hands the shell the exercise and opens its book beside, whose window
  // opens the problem; "open in the book" opens the book there.
  const [opening, setOpening] = useState<string | null>(null);
  const useExercise = (candidate: ExerciseCandidate) => {
    const card = cardOf(candidate.sourceId);
    if (!card || !reader?.onUseExercise) return;
    setOpening(candidate.key);
    window.setTimeout(() => setOpening((current) => (current === candidate.key ? null : current)), 1500);
    reader.onUseExercise({ ...exerciseOpenRequest(candidate), sourceId: card.sourceId, card });
    onOpenHit({ sourceId: card.sourceId, extractionId: candidate.extractionId, spanId: candidate.spanIds[0] ?? "" });
  };
  const exerciseSettings = ctl.enabled ? contract?.libraryExercises ?? null : null;
  const exercises: LibraryExercisesProps | null = exerciseSettings
    ? {
        settings: exerciseSettings,
        onUse: algoConfig().workbench && reader?.onUseExercise ? useExercise : null,
        onOpenInBook: (candidate) => {
          if (candidate.sourceId) onOpenHit({ sourceId: candidate.sourceId, extractionId: candidate.extractionId, spanId: candidate.spanIds[0] ?? "" });
        },
        opening,
      }
    : null;
  const [compose, setCompose] = useState<string | null>(query ?? "");
  const ask = useCallback((text: string) => {
    setCompose(null);
    if (anchor && ctl.scopeOn) {
      ctl.compareFrom({ door: "selection", question: text, extractionId: anchor.extractionId, anchorSpanIds: anchor.spanIds,
        openSourceId: anchor.sourceId, identity: { sourceId: anchor.sourceId, revisionId: anchor.revisionId, extractionId: anchor.extractionId } });
      return;
    }
    // Typed words are the ask box's (review fix round, major 19): books named in them are read first ("Compare A and B
    // on X"), as the old library page and a book's own ask box do.
    void ctl.askBox(anchor
      ? { query: text, entry: "library_search", extractionId: anchor.extractionId, spanIds: anchor.spanIds,
        identity: { sourceId: anchor.sourceId, revisionId: anchor.revisionId, extractionId: anchor.extractionId } }
      : { query: text, entry: "library_search", extractionId: null, spanIds: [], identity: null });
  }, [ctl, anchor]);
  if (!contractQuery.data) return <div className="desk-panel desk-quiet">◐ {contractQuery.error ? "Couldn’t load library settings. Reopen this window to try again." : "Loading library settings…"}</div>;
  if (!ctl.enabled) return <div className="desk-panel desk-quiet">Asking across the library is off. Open a source to keep reading.</div>;
  return (
    <NotesContext.Provider value={notes.context}>
      <CompareKeepContext.Provider value={kept.context}>
        <div style={{ display: "flex", minHeight: 0, height: "100%" }}>
          <LibraryPane
            ctl={ctl}
            compose={compose}
            onCompose={setCompose}
            onAsk={ask}
            onReword={ctl.scopeOn ? (words) => { ctl.close(); setCompose(words); } : null}
            onOpenHit={onOpenHit}
            onPracticePick={reader?.onCheckMe ? pickPractice : null}
            onClose={onClose}
            exercises={exercises}
            stacked
          />
        </div>
      </CompareKeepContext.Provider>
    </NotesContext.Provider>
  );
}

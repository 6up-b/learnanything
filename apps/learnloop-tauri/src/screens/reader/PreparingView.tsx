// Reading while LearnLoop gets the book ready (docs/specs/ux_learnloop_v1.md
// §6.3, wireframe W2; coordination item K2). The Reader opens on the original
// PDF at once; one quiet line in the header says what is happening; the
// features that need the book's text say when, in place. As soon as the text
// is ready the full Reader takes over at the same book.

import { convertFileSrc } from "@tauri-apps/api/core";
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReaderPdfViewDto, SourceActionKind, SourceActionResultDto, SourceLibraryCard } from "../../api/dto";
import { readableTitle, StatusLine } from "../../components/BookCard";
import { PdfReaderPane } from "../../components/PdfReaderPane";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { readingPositionIn, type ReadingPosition } from "./readingPosition";

const POLL_MS = 3000;
const NO_SPANS = new Set<string>();
// The actions a status line can offer that run on the book itself; the ones
// that open another place (connect, settings, changes) stay on its card.
const BOOK_ACTIONS: ReadonlySet<SourceActionKind> = new Set<SourceActionKind>([
  "retry", "text_recognition", "allow_upload", "build_now", "restore_reading", "mark_exam_material"
]);

export function PreparingView({
  card,
  onBack,
  onReady,
  onError
}: {
  card: SourceLibraryCard;
  onBack: () => void;
  /** The text is ready: open the full Reader on this (refreshed) card, at
   *  the page and place the learner has scrolled to (review F8). */
  onReady: (card: SourceLibraryCard, position: ReadingPosition | null) => void;
  onError: (message: string) => void;
}) {
  const [manifest, setManifest] = useState<ReaderPdfViewDto | null>(null);
  const [manifestLoaded, setManifestLoaded] = useState(false);
  const [current, setCurrent] = useState<SourceLibraryCard>(card);
  const readyRef = useRef(onReady);
  readyRef.current = onReady;
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .readerPdfView({ extractionId: card.sourceId })
      .then((view) => {
        if (alive) setManifest(view.available ? view : null);
      })
      .catch(() => {
        if (alive) setManifest(null);
      })
      .finally(() => {
        if (alive) setManifestLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, [card.sourceId]);

  useEffect(() => {
    let alive = true;
    const check = () => {
      api
        .getSourceLibrary()
        .then((library) => {
          if (!alive) return;
          const next = library.sources.find((entry) => entry.sourceId === card.sourceId);
          if (!next) return;
          setCurrent(next);
          if (next.readiness === "ready") readyRef.current(next, readingPositionIn(scrollRef.current));
        })
        .catch(() => undefined);
    };
    const timer = window.setInterval(check, POLL_MS);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [card.sourceId]);

  const noun = current.kindNoun ?? card.kindNoun ?? "book";
  const line = current.statusLine?.text ?? `Getting this ${noun} ready`;
  // Still being prepared, or stopped (a scan, a failed import): a stopped book
  // says so with its one action and promises nothing (usability round 1, U7).
  const working = !current.statusLine || current.statusLine.tone === "working";
  const statusLine = current.statusLine;
  const runAction = (kind: SourceActionKind) => {
    // A book with study state is read again only after the learner says so,
    // with the pages and cost named (re-read safety). Marking exam material
    // sends back the reading and the proposal it showed; if either changed
    // meanwhile the sidecar marks nothing and returns a fresh confirmation,
    // which is asked again (exam protection by extraction identity, F4).
    const ask = (result: SourceActionResultDto): Promise<unknown> | undefined => {
      const confirmation = result.needsConfirmation ? result.confirmation : undefined;
      if (!confirmation || !window.confirm([confirmation.title, ...confirmation.lines].join("\n"))) return undefined;
      const binding = confirmation.proposalHash
        ? { confirmedExtractionId: confirmation.extractionId, confirmedProposalHash: confirmation.proposalHash }
        : {};
      return api.sourceAction({ sourceId: current.sourceId, action: kind, confirmed: true, ...binding }).then(ask);
    };
    void api
      .sourceAction({ sourceId: current.sourceId, action: kind })
      .then(ask)
      .catch((error: unknown) => onError(errorMessage(error)));
  };
  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "16px 32px", display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={onBack}
            style={{ background: "none", border: "none", padding: 0, color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
          >
            ← Library
          </button>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>{readableTitle(card.title)}</span>
        </div>
        {working || !statusLine ? (
          <>
            <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.cyan }}>
              ◐ {line}
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>
              Highlights, notes, Ask and questions on each section — available in a minute or two, when the text is ready.
            </div>
          </>
        ) : (
          <>
            <div role="status">
              <StatusLine
                line={statusLine.action && BOOK_ACTIONS.has(statusLine.action.kind) ? statusLine : { ...statusLine, action: null }}
                onAction={runAction}
              />
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>
              You can look through the pages here. Highlights, notes, Ask and questions need its text.
            </div>
          </>
        )}
      </div>
      <div
        ref={scrollRef}
        data-testid="preparing-scroll"
        className="ll-scroll"
        style={{ flex: 1, minHeight: 0, overflowY: "auto", display: "flex", flexDirection: "column", padding: manifest ? "18px 32px" : "40px 32px" }}
      >
        {manifest ? (
          <PdfReaderPane
            fileUrl={convertFileSrc(manifest.fileName ?? "", "llpdf")}
            blocks={manifest.blocks}
            guidanceSpans={NO_SPANS}
            activeSpan={null}
            onTextSelection={() => undefined}
            onTagMenu={() => undefined}
            onError={onError}
          />
        ) : manifestLoaded ? (
          <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>It opens here as soon as it is ready.</div>
        ) : (
          <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>Opening…</div>
        )}
      </div>
    </div>
  );
}

// The Library place (docs/specs/ux_learnloop_v1.md §7.2): "Books" is the shelf
// of what you are learning from, one card each, the first-run welcome when
// empty; "Notes & files" is today's Library screen, unchanged (the vault tree,
// notes and the data browser move fully under the hood in Phase 2).

import { lazy, Suspense, useCallback, useEffect, useRef, useState, type CSSProperties, type ComponentProps } from "react";
import { api } from "../api/client";
import type { AiConnectionDto, PendingAddDto, SourceActionConfirmationDto, SourceActionKind, SourceLibraryCard } from "../api/dto";
import { TAG } from "../api/queryTags";
import { useCachedQuery } from "../api/useCachedQuery";
import type { AddOptions } from "../components/AddSource";
import { BookShelf } from "../components/BookShelf";
import { COLOR, FONT_MONO } from "../components/term";
import { plainError } from "../copy/ingestErrors";

const LibraryScreen = lazy(() => import("./LibraryScreen").then((module) => ({ default: module.LibraryScreen })));

const POLL_MS = 3000;

export type LibraryView = "books" | "files";

function tabStyle(active: boolean): CSSProperties {
  return {
    background: "none",
    border: "none",
    borderBottom: `2px solid ${active ? COLOR.amber : "transparent"}`,
    color: active ? COLOR.text : COLOR.textDim,
    fontFamily: FONT_MONO,
    fontSize: 12,
    padding: "6px 2px",
    cursor: "pointer"
  };
}

const confirmButton: CSSProperties = {
  background: "transparent",
  border: `1px solid ${COLOR.borderStrong}`,
  borderRadius: 3,
  color: COLOR.text,
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: "4px 12px",
  cursor: "pointer"
};

const cancelButton: CSSProperties = {
  background: "none",
  border: "none",
  padding: 0,
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2
};

function busyShelf(sources: SourceLibraryCard[] | undefined, pending: PendingAddDto[] | undefined): boolean {
  return (pending?.length ?? 0) > 0 || (sources ?? []).some((card) => card.statusLine?.tone === "working");
}

export function LibraryPlace({
  view,
  onViewChange,
  filesProps,
  aiConnection,
  onOpenBook,
  onConnectAi,
  onOpenImports,
  onOpenChanges,
  onOpenSettings,
  onAdd,
  addBusy,
  addMessage,
  dragging,
  openWhenReady,
  onOpenedWhenReady,
  booksOnly = false
}: {
  view: LibraryView;
  onViewChange: (view: LibraryView) => void;
  filesProps: ComponentProps<typeof LibraryScreen>;
  aiConnection: AiConnectionDto | null;
  onOpenBook: (card: SourceLibraryCard) => void;
  onConnectAi: () => void;
  onOpenImports: () => void;
  onOpenChanges: () => void;
  onOpenSettings: () => void;
  onAdd: (sources: string[], options: AddOptions) => void;
  addBusy: boolean;
  addMessage: string | null;
  dragging: boolean;
  /** A link just added: open it in the Reader as soon as its text is ready. */
  openWhenReady: string | null;
  onOpenedWhenReady: () => void;
  /** The shelf alone, without Books | Notes & files: the Reader with no book
   *  open shows it (spec K5). */
  booksOnly?: boolean;
}) {
  const library = useCachedQuery(["get_source_library"], () => api.getSourceLibrary(), { tags: [TAG.sources] });
  const [notice, setNotice] = useState<string | null>(null);
  const sources = library.data?.sources;
  const pending = library.data?.pending ?? [];
  const refetchRef = useRef(library.refetch);
  refetchRef.current = library.refetch;

  // While a book is being prepared (or a link fetched) the shelf keeps up.
  const working = busyShelf(sources, pending) || openWhenReady !== null;
  useEffect(() => {
    if (view !== "books" || !working) return;
    const timer = window.setInterval(() => void refetchRef.current().catch(() => undefined), POLL_MS);
    return () => window.clearInterval(timer);
  }, [view, working]);

  useEffect(() => {
    if (!openWhenReady || !sources) return;
    const card = sources.find((entry) => entry.canonicalUri === openWhenReady);
    if (card && card.readiness === "ready") {
      onOpenedWhenReady();
      onOpenBook(card);
    }
  }, [openWhenReady, sources, onOpenBook, onOpenedWhenReady]);

  // Re-read safety: reading a book again that has study state (or that z.ai
  // would read at a cost no OK line shows) asks first, naming the pages, the
  // cost and what moves to the new reading. Marking exam material on a
  // held-back reading asks the same way, naming what it will hold out.
  const [confirming, setConfirming] = useState<{
    sourceId: string;
    action: SourceActionKind;
    confirmation: SourceActionConfirmationDto;
  } | null>(null);

  const run = useCallback(async (input: {
    sourceId?: string | null;
    batchId?: string | null;
    action: SourceActionKind;
    confirmed?: boolean;
    confirmedExtractionId?: string | null;
    confirmedProposalHash?: string | null;
  }) => {
    setNotice(null);
    try {
      const result = await api.sourceAction(input);
      if (result.needsConfirmation && result.confirmation && input.sourceId) {
        setConfirming({ sourceId: input.sourceId, action: input.action, confirmation: result.confirmation });
        return;
      }
      await refetchRef.current().catch(() => undefined);
    } catch (error) {
      setNotice(plainError(error).line);
    }
  }, []);

  const onAction = useCallback(
    (kind: SourceActionKind, card: SourceLibraryCard) => {
      if (kind === "connect_ai") onConnectAi();
      else if (kind === "open_changes") onOpenChanges();
      else if (kind === "open_settings") onOpenSettings();
      else void run({ sourceId: card.sourceId, action: kind });
    },
    [onConnectAi, onOpenChanges, onOpenSettings, run]
  );

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      {booksOnly ? null : (
      <div role="tablist" aria-label="Library" style={{ flexShrink: 0, display: "flex", gap: 18, padding: "10px 32px 0", borderBottom: `1px solid ${COLOR.border}` }}>
        <button type="button" role="tab" aria-selected={view === "books"} style={tabStyle(view === "books")} onClick={() => onViewChange("books")}>
          Books
        </button>
        <button type="button" role="tab" aria-selected={view === "files"} style={tabStyle(view === "files")} onClick={() => onViewChange("files")}>
          Notes & files
        </button>
      </div>
      )}
      {view === "files" && !booksOnly ? (
        <Suspense fallback={<div role="status">Loading…</div>}>
          <LibraryScreen {...filesProps} />
        </Suspense>
      ) : (
        <>
          {notice ? (
            <div role="status" style={{ padding: "10px 32px 0", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amber }}>
              {notice}
            </div>
          ) : null}
          {confirming ? (
            <div
              role="alertdialog"
              aria-label={confirming.confirmation.title}
              style={{
                margin: "10px 32px 0",
                padding: "10px 14px",
                border: `1px solid ${COLOR.borderStrong}`,
                borderRadius: 4,
                display: "flex",
                flexDirection: "column",
                gap: 5,
                fontFamily: FONT_MONO,
                fontSize: 11,
                color: COLOR.textDim
              }}
            >
              <div style={{ fontSize: 12, color: COLOR.text }}>{confirming.confirmation.title}</div>
              {confirming.confirmation.lines.map((line) => (
                <div key={line}>{line}</div>
              ))}
              <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
                <button
                  type="button"
                  style={confirmButton}
                  onClick={() => {
                    const chosen = confirming;
                    setConfirming(null);
                    // The marking's confirmation is bound to the reading and
                    // the proposal it showed: if either changed meanwhile the
                    // sidecar marks nothing and asks again.
                    const binding = chosen.confirmation.proposalHash
                      ? {
                          confirmedExtractionId: chosen.confirmation.extractionId,
                          confirmedProposalHash: chosen.confirmation.proposalHash
                        }
                      : {};
                    void run({ sourceId: chosen.sourceId, action: chosen.action, confirmed: true, ...binding });
                  }}
                >
                  {confirming.confirmation.confirmLabel}
                </button>
                <button type="button" style={cancelButton} onClick={() => setConfirming(null)}>
                  {confirming.confirmation.cancelLabel}
                </button>
              </div>
            </div>
          ) : null}
          <BookShelf
            sources={sources ?? (library.error ? [] : null)}
            pending={pending}
            aiConnection={aiConnection}
            onOpen={onOpenBook}
            onAction={onAction}
            onConnectAi={onConnectAi}
            onAdd={onAdd}
            addBusy={addBusy}
            addMessage={addMessage}
            dragging={dragging}
            loadError={library.error && !sources ? library.error.message : null}
            onRetryLoad={() => void library.refetch().catch(() => undefined)}
            onOpenImports={onOpenImports}
            onRetryPending={(entry) =>
              void run({
                batchId: entry.batchId,
                // A link whose file waits for the OK to send it out gets that OK.
                action: entry.statusLine?.action?.kind === "allow_upload" ? "allow_upload" : "retry"
              })
            }
            onRemovePending={(entry) => {
              api
                .cancelIngestBatch(entry.batchId)
                .then(() => refetchRef.current())
                .catch((error: unknown) => setNotice(plainError(error).line));
            }}
          />
        </>
      )}
    </div>
  );
}

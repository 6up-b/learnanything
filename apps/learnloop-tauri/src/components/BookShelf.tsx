// The Library shelf (docs/specs/ux_learnloop_v1.md §6.1 W1, §7.2 W3). Empty, it
// is the first-run welcome: one place to drop a book and, only when no AI can
// write questions, one line to connect one. Otherwise one card per book, links
// still being fetched included, and Add again at the foot.

import type { AiConnectionDto, PendingAddDto, SourceActionKind, SourceLibraryCard } from "../api/dto";
import { AddSourceBox, type AddOptions } from "./AddSource";
import { BookCard, PendingCard } from "./BookCard";
import { COLOR, FONT_MONO } from "./term";

export function BookShelf({
  sources,
  pending,
  aiConnection,
  onOpen,
  onAction,
  onConnectAi,
  onAdd,
  addBusy = false,
  addMessage = null,
  dragging = false,
  loadError = null,
  onRetryLoad,
  onOpenImports,
  onRetryPending,
  onRemovePending
}: {
  sources: SourceLibraryCard[] | null;
  pending: PendingAddDto[];
  aiConnection: AiConnectionDto | null;
  onOpen: (card: SourceLibraryCard) => void;
  onAction: (kind: SourceActionKind, card: SourceLibraryCard) => void;
  onConnectAi: () => void;
  onAdd: (sources: string[], options: AddOptions) => void;
  addBusy?: boolean;
  addMessage?: string | null;
  dragging?: boolean;
  loadError?: string | null;
  onRetryLoad?: () => void;
  onOpenImports?: () => void;
  onRetryPending?: (entry: PendingAddDto) => void;
  onRemovePending?: (entry: PendingAddDto) => void;
}) {
  if (loadError) {
    return (
      <div role="alert" style={{ padding: "32px", fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, display: "flex", gap: 10, alignItems: "baseline" }}>
        LearnLoop couldn't read your library.
        {onRetryLoad ? (
          <button type="button" onClick={onRetryLoad} style={{ background: "none", border: "none", color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", fontFamily: FONT_MONO, fontSize: 12 }}>
            Try again
          </button>
        ) : null}
      </div>
    );
  }
  if (sources === null) {
    // Loading: the shelf frame with card outlines, no spinner title.
    return (
      <div aria-busy="true" style={{ padding: "24px 32px", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}>
        {[0, 1].map((index) => (
          <div key={index} style={{ height: 110, border: `1px solid ${COLOR.border}`, borderRadius: 4, opacity: 0.4 }} />
        ))}
      </div>
    );
  }
  const empty = sources.length === 0 && pending.length === 0;
  const aiLine = aiConnection && aiConnection.needs === "connect" ? (
    <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
      <span>○ Connect an AI to get questions —</span>
      <button
        type="button"
        onClick={onConnectAi}
        style={{ background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", fontFamily: FONT_MONO, fontSize: 12 }}
      >
        Continue with ChatGPT · other…
      </button>
    </div>
  ) : null;

  if (empty) {
    return (
      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 22, padding: "40px 24px" }}>
        <div style={{ width: "min(640px, 100%)" }}>
          <AddSourceBox onAdd={onAdd} busy={addBusy} message={addMessage} size="hero" dragging={dragging} />
        </div>
        <div style={{ maxWidth: 560, textAlign: "center", fontFamily: FONT_MONO, fontSize: 12, lineHeight: 1.7, color: COLOR.textDim }}>
          LearnLoop opens it right away. While you read, it builds questions on what you've just read and brings them
          back when they'll help.
        </div>
        {aiLine}
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "20px 32px", display: "flex", flexDirection: "column", gap: 18 }} className="ll-scroll">
      {aiLine}
      <ul
        aria-label="Your books"
        style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}
      >
        {pending.map((entry) => (
          <li key={entry.batchId}>
            <PendingCard entry={entry} onRetry={(item) => onRetryPending?.(item)} onRemove={onRemovePending} />
          </li>
        ))}
        {sources.map((card) => (
          <li key={card.sourceId}>
            <BookCard
              card={card}
              onContinue={onOpen}
              onAction={onAction}
              onOpenImports={onOpenImports}
              aiReady={aiConnection ? aiConnection.canAuthor : undefined}
            />
          </li>
        ))}
      </ul>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 640 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>Drop more books here, or add one:</span>
        <AddSourceBox onAdd={onAdd} busy={addBusy} message={addMessage} dragging={dragging} />
      </div>
    </div>
  );
}

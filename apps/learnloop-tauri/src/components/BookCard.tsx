// A book on the Library shelf (docs/specs/ux_learnloop_v1.md §7.2, W3): title,
// kind, one quiet status line with at most one action, Continue, and details ▸
// for the receipts and the choices Add never asked for.

import { useState, type CSSProperties } from "react";
import type { PendingAddDto, SourceActionKind, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";
import { IntentControl } from "./IntentControl";
import { CONSENT_ACTION, SIDECAR_CONSENT_LABEL, readableTitle } from "../app/todayCause";

// The card's OK words and its title net live with Today's cause line, which the
// phone shares: this module imports the desktop's client, the phone may not.
export { CONSENT_ACTION, SIDECAR_CONSENT_LABEL, readableTitle };

/** What a card's action reads: the OK's says what pressing it does at that
 *  moment (it asks for the OK; the sheet, and when it is asked, are as they
 *  were). Every other label is the sidecar's own: "Review" on changes to look
 *  at opens those changes, and "Connect" with no AI connects one. */
export function cardActionLabel(action: { kind: SourceActionKind; label: string }): string {
  return action.kind === "connect_ai" && action.label === SIDECAR_CONSENT_LABEL ? CONSENT_ACTION : action.label;
}

/** UX-5 (audit student-1 #35-39): what "for practice only" means, in details. */
export const PAST_EXAM_DETAILS = "A past exam or problem set, kept in your Library. It doesn't open in the Reader, and LearnLoop doesn't write questions from it.";

const linkButton: CSSProperties = {
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

const primaryButton: CSSProperties = {
  background: "transparent",
  border: `1px solid ${COLOR.borderStrong}`,
  borderRadius: 3,
  color: COLOR.text,
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: "4px 12px",
  cursor: "pointer"
};


function toneColor(tone: SourceStatusLineDto["tone"]): string {
  if (tone === "working") return COLOR.cyan;
  if (tone === "problem") return COLOR.amber;
  return COLOR.textDim;
}

export function StatusLine({
  line,
  onAction
}: {
  line: SourceStatusLineDto;
  onAction: (kind: SourceActionKind) => void;
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11 }}>
      <span style={{ color: toneColor(line.tone) }}>
        {line.tone === "working" ? "◐ " : ""}
        {line.text}
      </span>
      {line.action ? (
        <button type="button" style={linkButton} onClick={() => onAction(line.action!.kind)}>
          {cardActionLabel(line.action)}
        </button>
      ) : null}
    </div>
  );
}

export function BookCard({
  card,
  onContinue,
  onAction,
  onOpenImports,
  aiReady
}: {
  card: SourceLibraryCard;
  onContinue: (card: SourceLibraryCard) => void;
  onAction: (kind: SourceActionKind, card: SourceLibraryCard) => void;
  /** How it was added and built: today's Ingest screen (Under the hood →
   *  Imports & builds from Phase 2). */
  onOpenImports?: () => void;
  /** Whether an AI can write questions now; false shows a line's no-AI
   *  version (usability round 2). Unknown keeps the line as it is. */
  aiReady?: boolean;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const ready = card.readiness === "ready";
  const readable = card.readerEnabled !== false;
  const line = (aiReady === false ? card.statusLine?.withoutAi : null) ?? card.statusLine ?? null;
  const noun = card.kindNoun ?? "book";
  return (
    <article
      style={{
        border: `1px solid ${COLOR.border}`,
        borderRadius: 4,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        minWidth: 0
      }}
    >
      <div
        title={readableTitle(card.title)}
        style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
      >
        {readableTitle(card.title)}
      </div>
      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>
        {readable ? noun : `${noun} · for practice only`}
      </div>
      {line ? <StatusLine line={line} onAction={(kind) => onAction(kind, card)} /> : null}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 2 }}>
        {readable ? (
          <button type="button" style={primaryButton} onClick={() => onContinue(card)}>
            {ready ? "Continue" : "Open"}
          </button>
        ) : null}
        <button type="button" style={linkButton} aria-expanded={detailsOpen} onClick={() => setDetailsOpen((open) => !open)}>
          {detailsOpen ? "details ▾" : "details ▸"}
        </button>
      </div>
      {detailsOpen ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 5, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
          {line?.details ? <div style={{ color: COLOR.textFaint, wordBreak: "break-word" }}>{line.details}</div> : null}
          {readable ? null : <div>{PAST_EXAM_DETAILS}</div>}
          {card.subjectId ? <div>Subject: {card.subjectTitle ?? card.subjectId}</div> : null}
          {/* The words match what each does and what this is (UX Phase 1
              re-test #6): "the whole book" for a paper, beside a line whose
              own action builds as you read. The press gets every chapter's
              topics ready; it writes no question to practise (a section's
              are written when it is finished), so it promises none. */}
          {ready && readable ? (
            <button type="button" style={linkButton} onClick={() => onAction("build_whole_book", card)}>
              Get the whole {noun} ready for questions at once
            </button>
          ) : null}
          {card.subjectId ? (
            <button type="button" style={linkButton} onClick={() => onAction("undo_questions", card)}>
              Undo this {noun}'s questions
            </button>
          ) : null}
          {/* Only where it can run (usability round 2: offered everywhere, it
              ended in "Something went wrong"). */}
          {ready && card.acquisitionKind === "pdf" && card.textRecognitionAvailable === true ? (
            <button type="button" style={linkButton} onClick={() => onAction("text_recognition", card)}>
              Read it again with text recognition
            </button>
          ) : null}
          {onOpenImports ? (
            <button type="button" style={linkButton} onClick={onOpenImports}>
              See how it was added and built
            </button>
          ) : null}
          {/* Daily-loop DL2: the single intent control over the topics this
              source teaches (spec §5.2); it shows only once topics exist. */}
          {ready ? (
            <IntentControl scopeKind="source" scopeId={card.sourceId} heading={`What you want from this ${noun}`} />
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

/** A link an Add is still fetching: no card yet, one line, maybe Try again. */
export function PendingCard({
  entry,
  onRetry,
  onRemove
}: {
  entry: PendingAddDto;
  onRetry: (entry: PendingAddDto) => void;
  /** Take a link that could not be fetched off the shelf (cancels its add). */
  onRemove?: (entry: PendingAddDto) => void;
}) {
  const failed = entry.statusLine?.tone === "problem";
  return (
    <article style={{ border: `1px dashed ${COLOR.border}`, borderRadius: 4, padding: "12px 14px", display: "flex", flexDirection: "column", gap: 6, minWidth: 0 }}>
      <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={entry.title}>
        {entry.title}
      </div>
      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>{entry.kindNoun}</div>
      {entry.statusLine ? <StatusLine line={entry.statusLine} onAction={() => onRetry(entry)} /> : null}
      {failed && onRemove ? (
        <button type="button" style={{ ...linkButton, alignSelf: "flex-start", color: COLOR.textDim }} onClick={() => onRemove(entry)}>
          Remove
        </button>
      ) : null}
    </article>
  );
}

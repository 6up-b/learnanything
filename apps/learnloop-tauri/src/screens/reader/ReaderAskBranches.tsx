// The Ask rail's clarification threads (ported from
// origin/feat/reader-clarification-branches, cf2cbe77; reader workbench RW1a).
//
// Exchanges render as a tree from their durable parent links; missing or
// corrupt links read as roots and cycles are never followed. RW1a adds, on
// top of the branch's contract: the three voices (your question ›, the
// model's answer ◇, cited passages §), inquiry status chips on each root
// (open · resolved · revisit once · make it something I can do · dismissed,
// and reopen), "done" on a branch, the inquiry's reconnect line and quick
// check at its top, and the inquiry keys (↑ ↓ move · ↵ expand · f follow-up ·
// r resolved / done · o reopen · p show passage).
import type { KeyboardEvent, ReactNode } from "react";
import type { InquiryResolution, ReaderAnswerMode, ReaderTutorViewDto, TutorCitationDto } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import { answerModeLabel } from "./readerShared";
import { TutorAnswer, type ExchangeOffers, type TutorRailProps } from "./TutorAnswer";
import { LearnerVoice, MeaningLabel, SourceVoice } from "./voices";

export interface ReaderExchange {
  id: string;
  parentExchangeId: string | null;
  extractionId: string;
  spanId: string;
  selectionSpanIds: string[];
  selectionQuoteMd: string | null;
  /** Set only when the learner edited the capture: the source's own wording
   *  (selectionQuoteMd is then the learner's). */
  selectionSourceQuoteMd?: string | null;
  question: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: TutorCitationDto[];
  createdAt: string | null;
  /** RW1a: the exchange's tutor question and its learner-owned resolution. */
  questionEventId?: string | null;
  resolution?: InquiryResolution | null;
  /** RW1c: the answer's modes (absent while reader_tutor.retrieval_enabled is off). */
  tutor?: ReaderTutorViewDto | null;
  /** RW1c: the offers a freshly landed answer carries (never restored from history). */
  offers?: ExchangeOffers | null;
}

export type InquiryCommitment = "test_me_later" | "help_me_remember";

interface Props {
  exchanges: ReaderExchange[];
  collapsedIds: Set<string>;
  query: string;
  busy: boolean;
  onToggle: (id: string) => void;
  onFollowUp: (exchange: ReaderExchange) => void;
  onShowPassage: (spanId: string) => void;
  /** RW1a: set a root's inquiry status (reopen is "open"). */
  onSetStatus?: (root: ReaderExchange, resolution: InquiryResolution) => void;
  /** RW1a: mark a branch done (its own question resolved); asks the reconnect line. */
  onBranchDone?: (branch: ReaderExchange) => void;
  /** RW1a: "revisit once" (test_me_later) or "make it something I can do" (help_me_remember) on the root's anchor. */
  onCommit?: (root: ReaderExchange, preset: InquiryCommitment) => void;
  committed?: (root: ReaderExchange) => Set<InquiryCommitment>;
  /** RW1a: what shows at the top of an inquiry (its reconnect line and quick check). */
  renderInquiryTop?: (root: ReaderExchange) => ReactNode;
  /** RW1c: another way, that didn't help and the offers (absent while reader_tutor is off). */
  tutor?: TutorRailProps;
}

const STATUS_WORDS: Record<InquiryResolution, string> = { open: "open", resolved: "resolved", dismissed: "dismissed" };

export function ReaderAskBranches({
  exchanges,
  collapsedIds,
  query,
  busy,
  onToggle,
  onFollowUp,
  onShowPassage,
  onSetStatus,
  onBranchDone,
  onCommit,
  committed,
  renderInquiryTop,
  tutor,
}: Props) {
  const byId = new Map(exchanges.map((exchange) => [exchange.id, exchange]));
  const children = new Map<string | null, ReaderExchange[]>();
  const parents = new Map<string, string | null>();
  // Treat missing/corrupt links as roots so old or partially restored histories
  // stay readable. Never recurse through a cycle.
  for (const exchange of exchanges) {
    let parent = exchange.parentExchangeId;
    const seen = new Set([exchange.id]);
    let cursor = parent;
    while (cursor) {
      const ancestor = byId.get(cursor);
      if (!ancestor || seen.has(cursor) || ancestor.extractionId !== exchange.extractionId || ancestor.spanId !== exchange.spanId) {
        parent = null;
        break;
      }
      seen.add(cursor);
      cursor = ancestor.parentExchangeId;
    }
    parents.set(exchange.id, parent);
    children.set(parent, [...(children.get(parent) ?? []), exchange]);
  }
  const search = query.trim().toLowerCase();
  const visible = new Set<string>();
  for (const exchange of exchanges) {
    if (!search || `${exchange.question}\n${exchange.answerMd}`.toLowerCase().includes(search)) {
      let id: string | null = exchange.id;
      while (id && !visible.has(id)) {
        visible.add(id);
        id = parents.get(id) ?? null;
      }
    }
  }
  const buttonStyle = { border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 };

  const onHeaderKey = (event: KeyboardEvent<HTMLButtonElement>, exchange: ReaderExchange, isRoot: boolean) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const resolution = exchange.resolution ?? "open";
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      const scope = event.currentTarget.closest("[data-ask-threads]") ?? document;
      const headers = Array.from(scope.querySelectorAll<HTMLButtonElement>("[data-exchange-header]"));
      const next = headers[headers.indexOf(event.currentTarget) + (event.key === "ArrowDown" ? 1 : -1)];
      if (next) {
        event.preventDefault();
        next.focus();
      }
    } else if (event.key === "f" && !busy) {
      event.preventDefault();
      onFollowUp(exchange);
    } else if (event.key === "p") {
      event.preventDefault();
      onShowPassage(exchange.spanId);
    } else if (event.key === "r") {
      event.preventDefault();
      if (isRoot && onSetStatus && resolution === "open") onSetStatus(exchange, "resolved");
      else if (!isRoot && onBranchDone && resolution === "open") onBranchDone(exchange);
    } else if (event.key === "o" && isRoot && onSetStatus && resolution !== "open") {
      event.preventDefault();
      onSetStatus(exchange, "open");
    }
  };

  function statusChips(root: ReaderExchange) {
    if (!onSetStatus || !root.questionEventId) return null;
    const resolution = root.resolution ?? "open";
    const done = committed?.(root) ?? new Set<InquiryCommitment>();
    return (
      <div role="group" aria-label="Inquiry status" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "baseline" }}>
        <MeaningLabel>status: {STATUS_WORDS[resolution]}</MeaningLabel>
        {resolution === "open" ? (
          <>
            <button type="button" disabled={busy} onClick={() => onSetStatus(root, "resolved")} style={buttonStyle}>resolved</button>
            {onCommit ? (
              <>
                <button type="button" disabled={busy || done.has("test_me_later")} onClick={() => onCommit(root, "test_me_later")} style={buttonStyle}>
                  {done.has("test_me_later") ? "revisit once ✓" : "revisit once"}
                </button>
                <button type="button" disabled={busy || done.has("help_me_remember")} onClick={() => onCommit(root, "help_me_remember")} style={buttonStyle}>
                  {done.has("help_me_remember") ? "make it something I can do ✓" : "make it something I can do"}
                </button>
              </>
            ) : null}
            <button type="button" disabled={busy} onClick={() => onSetStatus(root, "dismissed")} style={buttonStyle}>dismiss</button>
          </>
        ) : (
          <button type="button" disabled={busy} onClick={() => onSetStatus(root, "open")} style={buttonStyle}>reopen</button>
        )}
      </div>
    );
  }

  function branch(exchange: ReaderExchange, depth: number) {
    if (!visible.has(exchange.id)) return null;
    const expanded = Boolean(search) || !collapsedIds.has(exchange.id);
    const replies = children.get(exchange.id) ?? [];
    const isRoot = depth === 0;
    const resolution = exchange.resolution ?? "open";
    return (
      <li key={exchange.id} data-exchange-id={exchange.id} data-ask-id={exchange.id} style={{ listStyle: "none" }}>
        <Card status="running" style={{ display: "flex", flexDirection: "column", gap: 8, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, overflowWrap: "anywhere" }}>
          <button
            type="button"
            data-exchange-header=""
            aria-expanded={expanded}
            onClick={() => onToggle(exchange.id)}
            onKeyDown={(event) => onHeaderKey(event, exchange, isRoot)}
            style={{ ...buttonStyle, textAlign: "left", color: COLOR.text }}
          >
            {expanded ? "▾" : "▸"} {exchange.question.length > 130 ? `${exchange.question.slice(0, 130)}…` : exchange.question}
            {replies.length > 0 ? <Faint> · {replies.length} follow-up{replies.length === 1 ? "" : "s"}</Faint> : null}
          </button>
          {isRoot && renderInquiryTop ? renderInquiryTop(exchange) : null}
          {expanded ? <>
            <LearnerVoice label="your question">
              <MarkdownMath value={exchange.question} />
            </LearnerVoice>
            <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
              <Pill color="cyan">{answerModeLabel(exchange.answerMode)}</Pill>
              {exchange.createdAt ? <Faint style={{ fontSize: 9 }}>{new Date(exchange.createdAt).toLocaleString()}</Faint> : null}
            </div>
            {exchange.selectionSourceQuoteMd ? (
              <>
                <SourceVoice>
                  <blockquote style={{ margin: 0, fontSize: 11, color: COLOR.textDim }}>{exchange.selectionSourceQuoteMd}</blockquote>
                </SourceVoice>
                {exchange.selectionQuoteMd ? (
                  <LearnerVoice label="your edited capture">
                    <blockquote style={{ margin: 0, fontSize: 11, color: COLOR.textDim }}>{exchange.selectionQuoteMd}</blockquote>
                  </LearnerVoice>
                ) : null}
              </>
            ) : exchange.selectionQuoteMd ? (
              <SourceVoice>
                <blockquote style={{ margin: 0, fontSize: 11, color: COLOR.textDim }}>{exchange.selectionQuoteMd}</blockquote>
              </SourceVoice>
            ) : null}
            <TutorAnswer exchange={exchange} tutor={tutor} />
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button type="button" onClick={() => onShowPassage(exchange.spanId)} style={buttonStyle}>show passage</button>
              <button type="button" disabled={busy} onClick={() => onFollowUp(exchange)} style={buttonStyle}>ask follow-up</button>
              {!isRoot && onBranchDone && exchange.questionEventId ? (
                resolution === "open" ? (
                  <button type="button" disabled={busy} onClick={() => onBranchDone(exchange)} style={buttonStyle}>done</button>
                ) : (
                  <MeaningLabel>done</MeaningLabel>
                )
              ) : null}
              {exchange.citations.map((citation, index) => citation.extractionId === exchange.extractionId ? (
                <button type="button" key={index} onClick={() => onShowPassage(citation.spanId)} style={buttonStyle}>
                  <span aria-hidden="true">§ </span>source: {citation.label || citation.spanId}
                </button>
              ) : <span key={index}>{citation.label || citation.spanId}</span>)}
            </div>
            {isRoot ? statusChips(exchange) : null}
          </> : null}
        </Card>
        {expanded && replies.length > 0 ? (
          <ul aria-label={`Follow-ups to ${exchange.question}`} style={{ margin: "8px 0", paddingLeft: depth < 5 ? 12 : 0, borderLeft: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 8 }}>
            {replies.map((reply) => branch(reply, depth + 1))}
          </ul>
        ) : null}
      </li>
    );
  }
  return <ul data-ask-threads="" aria-label="Clarification threads" style={{ margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
    {(children.get(null) ?? []).map((root) => branch(root, 0))}
  </ul>;
}

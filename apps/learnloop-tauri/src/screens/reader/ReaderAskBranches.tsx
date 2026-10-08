import type { ReaderAnswerMode, TutorCitationDto } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";

export interface ReaderExchange {
  id: string;
  parentExchangeId: string | null;
  extractionId: string;
  spanId: string;
  selectionSpanIds: string[];
  selectionQuoteMd: string | null;
  question: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: TutorCitationDto[];
  createdAt: string | null;
}

interface Props {
  exchanges: ReaderExchange[];
  collapsedIds: Set<string>;
  query: string;
  busy: boolean;
  onToggle: (id: string) => void;
  onFollowUp: (exchange: ReaderExchange) => void;
  onShowPassage: (spanId: string) => void;
}

export function ReaderAskBranches({ exchanges, collapsedIds, query, busy, onToggle, onFollowUp, onShowPassage }: Props) {
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
  function branch(exchange: ReaderExchange, depth: number) {
    if (!visible.has(exchange.id)) return null;
    const expanded = Boolean(search) || !collapsedIds.has(exchange.id);
    const replies = children.get(exchange.id) ?? [];
    return (
      <li key={exchange.id} data-exchange-id={exchange.id} style={{ listStyle: "none" }}>
        <Card status="running" style={{ display: "flex", flexDirection: "column", gap: 8, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, overflowWrap: "anywhere" }}>
          <button type="button" aria-expanded={expanded} onClick={() => onToggle(exchange.id)} style={{ ...buttonStyle, textAlign: "left", color: COLOR.text }}>
            {expanded ? "▾" : "▸"} {exchange.question.length > 130 ? `${exchange.question.slice(0, 130)}…` : exchange.question}
            {replies.length > 0 ? <Faint> · {replies.length} follow-up{replies.length === 1 ? "" : "s"}</Faint> : null}
          </button>
          {expanded ? <>
            <MarkdownMath value={exchange.question} />
            <Pill color="cyan">{exchange.answerMode}</Pill>
            {exchange.createdAt ? <Faint style={{ fontSize: 9 }}>{new Date(exchange.createdAt).toLocaleString()}</Faint> : null}
            {exchange.selectionQuoteMd ? <blockquote style={{ margin: 0, fontSize: 11, color: COLOR.textDim }}>{exchange.selectionQuoteMd}</blockquote> : null}
            <MarkdownMath value={exchange.answerMd} />
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button type="button" onClick={() => onShowPassage(exchange.spanId)} style={buttonStyle}>show passage</button>
              <button type="button" disabled={busy} onClick={() => onFollowUp(exchange)} style={buttonStyle}>ask follow-up</button>
              {exchange.citations.map((citation, index) => citation.extractionId === exchange.extractionId ? (
                <button type="button" key={index} onClick={() => onShowPassage(citation.spanId)} style={buttonStyle}>source: {citation.label || citation.spanId}</button>
              ) : <span key={index}>{citation.label || citation.spanId}</span>)}
            </div>
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
  return <ul aria-label="Clarification threads" style={{ margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
    {(children.get(null) ?? []).map((root) => branch(root, 0))}
  </ul>;
}

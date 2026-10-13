// The Reader rail's Ask tab (RW1a split of ReaderScreen; a move, not a
// redesign): the composer with its answer mode, and the saved exchanges, as
// clarification threads (reader_inquiry on) or today's flat list (off).
import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import type { ReaderAnswerMode, ReaderRenderBlockDto } from "../../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, Pill, SectionHeader, TermSelect } from "../../components/term";
import { AffectTap, PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import { ReaderAskBranches, type ReaderExchange } from "./ReaderAskBranches";
import { clip, type ReaderSelection } from "./readerShared";

export const ANSWER_MODE_OPTIONS = [
  { value: "answer_directly", label: "answer directly" },
  { value: "help_me_reason", label: "help me reason" },
  { value: "ask_me_first", label: "ask me first" },
];

export interface AskRailProps {
  visible: boolean;
  enabled: boolean;
  inquiry: boolean;
  offline: boolean;
  busy: boolean;
  blocks: ReaderRenderBlockDto[];
  activeSpan: string | null;
  activeBlock: ReaderRenderBlockDto | null;
  selection: ReaderSelection | null;
  parentExchange: ReaderExchange | null;
  setParentExchange: Dispatch<SetStateAction<ReaderExchange | null>>;
  answerMode: ReaderAnswerMode;
  changeAnswerMode: (next: string) => void | Promise<void>;
  question: string;
  setQuestion: Dispatch<SetStateAction<string>>;
  askComposerVersion: number;
  askComposerRef: MutableRefObject<HTMLTextAreaElement | null>;
  ask: () => void | Promise<void>;
  history: ReaderExchange[];
  visibleAskHistory: ReaderExchange[];
  normalizedAskFind: string;
  collapsedAskIds: Set<string>;
  setCollapsedAskIds: Dispatch<SetStateAction<Set<string>>>;
  askFindOpen: boolean;
  setAskFindOpen: Dispatch<SetStateAction<boolean>>;
  askFindQuery: string;
  setAskFindQuery: Dispatch<SetStateAction<string>>;
  askFindInputRef: MutableRefObject<HTMLInputElement | null>;
  jumpToSpan: (spanId: string) => void;
}

export function AskRail({
  visible,
  enabled,
  inquiry,
  offline,
  busy,
  blocks,
  activeSpan,
  activeBlock,
  selection,
  parentExchange,
  setParentExchange,
  answerMode,
  changeAnswerMode,
  question,
  setQuestion,
  askComposerVersion,
  askComposerRef,
  ask,
  history,
  visibleAskHistory,
  normalizedAskFind,
  collapsedAskIds,
  setCollapsedAskIds,
  askFindOpen,
  setAskFindOpen,
  askFindQuery,
  setAskFindQuery,
  askFindInputRef,
  jumpToSpan,
}: AskRailProps) {
  return (
    <div style={{ display: visible ? "block" : "none" }}>
      <SectionHeader style={{ marginTop: 0 }}>Ask</SectionHeader>
      <Faint style={{ fontSize: 10, display: "block", margin: "2px 0 8px" }}>
        answers now, grounded in the selected passage · background requests live under notes
      </Faint>
      {!enabled ? (
        <Card style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", gap: 6 }}>
          <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
            the reader Ask is disabled in this vault's config (on by default for new vaults). Set <Dim>tutor_qa.reader_enabled = true</Dim> to ask span-grounded questions.
          </Faint>
        </Card>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {(inquiry && parentExchange) || activeSpan ? (
            <>
              {/* The Ask grounding is the SAME selection Capture uses —
                  the learner never targets extraction blocks directly. */}
              {inquiry && parentExchange ? (
                <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <Faint>FOLLOW-UP TO: {clip(parentExchange.question, 120)}</Faint>
                  <Faint>{clip(parentExchange.selectionQuoteMd ?? blocks.find((block) => block.spanId === parentExchange.spanId)?.markdown ?? "Saved passage", 300)}</Faint>
                  <SecondaryButton onClick={() => jumpToSpan(parentExchange.spanId)}>show inherited passage</SecondaryButton>
                  <SecondaryButton disabled={busy} onClick={() => setParentExchange(null)}>new thread from current passage</SecondaryButton>
                </Card>
              ) : selection ? (
                <Card style={{ display: "flex", flexDirection: "column", gap: 4, background: COLOR.bgElev }}>
                  <Faint style={{ fontSize: 10 }}>ASKING ABOUT YOUR SELECTION</Faint>
                  <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                    <MarkdownMath value={clip((selection.editedText ?? selection.quote).replace(/\s+/g, " ").trim(), 300)} />
                  </div>
                </Card>
              ) : activeBlock ? (
                <Card style={{ display: "flex", flexDirection: "column", gap: 4, background: COLOR.bgElev }}>
                  <Faint style={{ fontSize: 10 }}>ASKING ABOUT</Faint>
                  <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                    <MarkdownMath value={clip(activeBlock.markdown.replace(/\s+/g, " "), 150)} />
                  </div>
                </Card>
              ) : null}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Faint style={{ fontSize: 11 }}>mode</Faint>
                <TermSelect
                  value={answerMode}
                  options={ANSWER_MODE_OPTIONS}
                  onChange={changeAnswerMode}
                  width={160}
                />
              </div>
              <textarea
                key={`${activeSpan}:${askComposerVersion}`}
                ref={askComposerRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="ask about this passage…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 70, resize: "vertical" }}
              />
              <PrimaryButton onClick={ask} disabled={busy || (inquiry && offline) || !question.trim()}>{inquiry && parentExchange ? "ask follow-up ↵" : "ask ↵"}</PrimaryButton>
            </>
          ) : (
            <Faint style={{ fontSize: 12 }}>select a passage (drag, or ctrl+drag boxes) to ask about it.</Faint>
          )}

          <SectionHeader>{inquiry ? "Clarification threads" : "Previous asks"}</SectionHeader>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Faint style={{ fontSize: 10 }}>{history.length} saved</Faint>
            {!askFindOpen ? (
              <button
                type="button"
                onClick={() => { setAskFindOpen(true); window.setTimeout(() => askFindInputRef.current?.focus(), 0); }}
                title="find in previous asks (ctrl+f)"
                aria-label="find in previous asks"
                style={{ marginLeft: "auto", width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
              >
                ⌕
              </button>
            ) : (
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
                <input
                  ref={askFindInputRef}
                  value={askFindQuery}
                  onChange={(event) => setAskFindQuery(event.target.value)}
                  placeholder="find in asks…"
                  style={{ width: 170, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, fontFamily: FONT_MONO, fontSize: 11, padding: "4px 6px" }}
                />
                <Faint style={{ fontSize: 10 }}>{visibleAskHistory.length}/{history.length}</Faint>
                <button type="button" onClick={() => { setAskFindOpen(false); setAskFindQuery(""); }} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer", padding: 0 }}>×</button>
              </div>
            )}
          </div>
          {history.length === 0 ? (
            <Faint style={{ fontSize: 11 }}>No saved asks for this source yet.</Faint>
          ) : visibleAskHistory.length === 0 ? (
            <Faint style={{ fontSize: 11 }}>No questions or answers match “{askFindQuery}”.</Faint>
          ) : inquiry ? (
            <ReaderAskBranches
              exchanges={history}
              collapsedIds={collapsedAskIds}
              query={askFindQuery}
              busy={busy || offline}
              onToggle={(id) => setCollapsedAskIds((ids) => {
                const next = new Set(ids);
                if (next.has(id)) next.delete(id); else next.add(id);
                return next;
              })}
              onFollowUp={(exchange) => {
                setParentExchange(exchange);
                // A search can expose a descendant of collapsed ancestors.
                // Keep the chosen path visible when the search is cleared.
                setCollapsedAskIds((ids) => {
                  const next = new Set(ids);
                  const seen = new Set<string>();
                  let cursor: ReaderExchange | undefined = exchange;
                  while (cursor && !seen.has(cursor.id)) {
                    seen.add(cursor.id);
                    next.delete(cursor.id);
                    cursor = history.find((item) => item.id === cursor?.parentExchangeId);
                  }
                  return next;
                });
                window.requestAnimationFrame(() => {
                  askComposerRef.current?.scrollIntoView({ block: "nearest" });
                  askComposerRef.current?.focus();
                });
              }}
              onShowPassage={jumpToSpan}
            />
          ) : visibleAskHistory.map((exchange) => {
            const expanded = normalizedAskFind.length > 0 || !collapsedAskIds.has(exchange.id);
            return (
              <Card key={exchange.id} status="running" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <button
                  type="button"
                  onClick={() => setCollapsedAskIds((ids) => {
                    const next = new Set(ids);
                    if (next.has(exchange.id)) next.delete(exchange.id); else next.add(exchange.id);
                    return next;
                  })}
                  aria-expanded={expanded}
                  style={{ display: "flex", alignItems: "baseline", gap: 7, width: "100%", border: 0, background: "transparent", color: COLOR.text, fontFamily: FONT_MONO, padding: 0, textAlign: "left", cursor: "pointer" }}
                >
                  <span style={{ color: COLOR.purpleText, flexShrink: 0 }}>{expanded ? "▼" : "▶"}</span>
                  <span style={{ fontSize: 11, flex: 1 }}>{clip(exchange.question, 130)}</span>
                </button>
                {expanded ? (
                  <>
                    {/* Expanded question renders its LaTeX (the collapsed
                        header stays plain text — clipping mid-$ would
                        break KaTeX). */}
                    <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                      <MarkdownMath value={exchange.question} />
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
                      <Pill color="cyan">{exchange.answerMode}</Pill>
                      <button type="button" onClick={() => jumpToSpan(exchange.spanId)} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}>show passage</button>
                      {exchange.createdAt ? <Faint style={{ fontSize: 9, marginLeft: "auto" }}>{new Date(exchange.createdAt).toLocaleString()}</Faint> : null}
                    </div>
                    <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                      <MarkdownMath value={exchange.answerMd} />
                    </div>
                  </>
                ) : null}
              </Card>
            );
          })}
          <AffectTap />
        </div>
      )}
    </div>
  );
}

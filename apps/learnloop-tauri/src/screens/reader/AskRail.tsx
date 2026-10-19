// The Reader rail's Ask tab (RW1a split of ReaderScreen; a move, not a
// redesign): the composer with its answer mode, and the saved exchanges, as
// clarification threads (reader_inquiry on) or today's flat list (off).
import type { Dispatch, MutableRefObject, ReactNode, SetStateAction } from "react";
import type { ReaderAnswerMode, ReaderRenderBlockDto } from "../../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, Pill, SectionHeader, TermSelect } from "../../components/term";
import { AffectTap, PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import type { InquiryResolution } from "../../api/dto";
import { ModelActionState, type ModelActionPhase } from "./ModelActionState";
import { ReaderAskBranches, type InquiryCommitment, type ReaderExchange } from "./ReaderAskBranches";
import { TutorAnswer, type TutorRailProps } from "./TutorAnswer";
import { ANSWER_MODE_OPTIONS, answerModeLabel, clip, type ReaderSelection } from "./readerShared";
import { LearnerVoice, MeaningLabel } from "./voices";

export { ANSWER_MODE_OPTIONS, answerModeLabel };

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
  // RW1a (reader_inquiry on): a peek is a detour; the Ask's model states; the
  // inquiry's status, commitments, branch "done" and its reconnect line.
  peekPassage?: (spanId: string) => void;
  askPhase?: ModelActionPhase;
  cancelAsk?: () => void;
  onSetStatus?: (root: ReaderExchange, resolution: InquiryResolution) => void;
  onBranchDone?: (branch: ReaderExchange) => void;
  onCommit?: (root: ReaderExchange, preset: InquiryCommitment) => void;
  committed?: (root: ReaderExchange) => Set<InquiryCommitment>;
  renderInquiryTop?: (root: ReaderExchange) => ReactNode;
  /** What an Ask would send now (an inherited thread's passage, the
   *  selection, or the active passage) touches material held out of
   *  LearnLoop's models, or the whole reading is held back (exam protection
   *  decides): the reason, and no Ask is offered. */
  protectionMessage?: string | null;
  /** RW1c: the tutor looks things up (its pending line says so) and its
   *  controls under answers; absent while reader_tutor is off. */
  lookingUp?: boolean;
  tutor?: TutorRailProps;
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
  peekPassage,
  askPhase = "idle",
  cancelAsk,
  onSetStatus,
  onBranchDone,
  onCommit,
  committed,
  renderInquiryTop,
  protectionMessage = null,
  lookingUp = false,
  tutor,
}: AskRailProps) {
  const peek = inquiry && peekPassage ? peekPassage : jumpToSpan;
  return (
    <div style={{ display: visible ? "block" : "none" }}>
      <SectionHeader style={{ marginTop: 0 }}>Ask</SectionHeader>
      <MeaningLabel style={{ display: "block", margin: "2px 0 8px" }}>
        answers now, grounded in the selected passage · background requests live under notes
      </MeaningLabel>
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
                  <SecondaryButton onClick={() => peek(parentExchange.spanId)}>show inherited passage</SecondaryButton>
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
              {protectionMessage ? (
                <span data-ask-protected="" style={{ color: COLOR.textFaint, fontSize: 11, lineHeight: 1.6 }}>
                  {protectionMessage} You can still highlight it and keep notes.
                </span>
              ) : (
              <>
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
                onKeyDown={(e) => {
                  // A keyboard path to Ask (RW1a), on either rail: Enter is a
                  // new line, ctrl+Enter sends (UX Phase 1 usability round 1, U6).
                  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                    e.preventDefault();
                    void ask();
                  }
                }}
                placeholder="ask about this passage…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 70, resize: "vertical" }}
              />
              <PrimaryButton onClick={ask} disabled={busy || (inquiry && offline) || !question.trim()}>{inquiry && parentExchange ? "ask follow-up · ctrl+↵" : "ask · ctrl+↵"}</PrimaryButton>
              {inquiry ? (
                <ModelActionState
                  phase={askPhase}
                  verb={lookingUp ? "looking in your books, then writing an answer" : "writing an answer"}
                  failure="Couldn't get an answer."
                  kept="Your question is kept."
                  capRoute="tutor"
                  fallback="Your saved threads and the passage"
                  onCancel={cancelAsk}
                  onRetry={() => void ask()}
                />
              ) : null}
              </>
              )}
            </>
          ) : protectionMessage ? (
            <span data-ask-protected="" style={{ color: COLOR.textFaint, fontSize: 11, lineHeight: 1.6 }}>
              {protectionMessage} You can still highlight it and keep notes.
            </span>
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
              onShowPassage={peek}
              onSetStatus={onSetStatus}
              onBranchDone={onBranchDone}
              onCommit={onCommit}
              committed={committed}
              renderInquiryTop={renderInquiryTop}
              {...(tutor ? { tutor } : {})}
            />
          ) : visibleAskHistory.map((exchange) => {
            const expanded = normalizedAskFind.length > 0 || !collapsedAskIds.has(exchange.id);
            return (
              <div key={exchange.id} data-ask-id={exchange.id}>
              <Card status="running" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <button
                  type="button"
                  onClick={() => setCollapsedAskIds((ids) => {
                    const next = new Set(ids);
                    if (next.has(exchange.id)) next.delete(exchange.id); else next.add(exchange.id);
                    return next;
                  })}
                  aria-expanded={expanded}
                  aria-label={expanded ? "hide this ask" : undefined}
                  style={{ display: "flex", alignItems: "baseline", gap: 7, width: "100%", border: 0, background: "transparent", color: COLOR.text, fontFamily: FONT_MONO, padding: 0, textAlign: "left", cursor: "pointer" }}
                >
                  <span style={{ color: COLOR.purpleText, flexShrink: 0 }}>{expanded ? "▼" : "▶"}</span>
                  {/* The question once (UX Phase 1 usability round 2: it was
                      printed twice): plain and clipped while collapsed --
                      clipping mid-$ would break KaTeX -- and in full, with its
                      maths, in the learner's voice below when open. */}
                  {expanded ? null : <span style={{ fontSize: 11, flex: 1 }}>{clip(exchange.question, 130)}</span>}
                </button>
                {expanded ? (
                  <>
                    <LearnerVoice label="your question">
                      <MarkdownMath value={exchange.question} />
                    </LearnerVoice>
                    <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
                      <Pill color="cyan">{answerModeLabel(exchange.answerMode)}</Pill>
                      <button type="button" onClick={() => jumpToSpan(exchange.spanId)} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}>show passage</button>
                      {exchange.createdAt ? <Faint style={{ fontSize: 9, marginLeft: "auto" }}>{new Date(exchange.createdAt).toLocaleString()}</Faint> : null}
                    </div>
                    <TutorAnswer exchange={exchange} tutor={tutor ? { ...tutor, anotherWay: false } : undefined} />
                  </>
                ) : null}
              </Card>
              </div>
            );
          })}
          <AffectTap />
        </div>
      )}
    </div>
  );
}

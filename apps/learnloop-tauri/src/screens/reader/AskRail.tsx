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
import { LearnerQuote, LearnerVoice, MeaningLabel } from "./voices";
import type { FigurePassageDto, FigureViewDto } from "../../api/dto";
import { isShowMeKey, passageChip, SHOW_ME_COPY, showMeSourceLine, type ShowMeLine } from "./figures/showMe";
import { frameBadge } from "./figures/FigureInline";

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
  /** Reader CA2 (§7.4, §15 Q5): the per-source mode select retires into the
   *  help style (one vocabulary, one stored preference) while the panel is
   *  on; this control replaces it. Absent: the mode select, as before. */
  helpStyleControl?: ReactNode;
  /** Reader CA2 (§7.1; Codex review F11): the one Ask panel's keys while it
   *  is on: ↵ sends, ⇧↵ a new line, ^↵ sends too. Off: ↵ is a new line and
   *  ^↵ sends, as before. */
  enterSends?: boolean;
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
  /** RW1c (Codex review F8): the visible personalized chip while the tutor
   *  looks things up; absent: no chip (retrieval off). */
  personalized?: { on: boolean; onToggle: (on: boolean) => void } | null;
  /** RW5d P1: "show me ▸" (Alt+↵) sends the box's words as a figure goal, and
   *  the thread's show-me lines; absent while figures.show_me_enabled is off. */
  showMe?: {
    lines: ShowMeLine[];
    onShowMe: () => void;
    /** "open": expands the figure under its passage and goes there with a
     *  "back to where I was" crumb (spec §6.2). */
    onOpen: (figure: FigureViewDto) => void;
    /** A cited passage's `§` chip: peeks in this book, opens another as a detour
     *  (RW1c's citations; Codex review F8). Absent: the chips are text. */
    onPeekPassage?: ((passage: FigurePassageDto) => void) | null;
    onDismiss: (key: string) => void;
  } | null;
}

export const PERSONALIZED_COPY = {
  on: "personalized ●",
  off: "personalized ○",
  why: "On: the tutor may connect its answer to your open questions and recent work on this passage. Off: nothing about you is sent.",
} as const;

function ShowMeThreadLine({ line, showMe }: { line: ShowMeLine; showMe: NonNullable<AskRailProps["showMe"]> }) {
  const link = { border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0,
    cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 } as const;
  return (
    <div data-show-me-line={line.state} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "baseline" }}>
      <span>› <LearnerQuote>{clip(line.goal, 120)}</LearnerQuote></span>
      {line.state === "pending" ? <span>{SHOW_ME_COPY.pending}</span> : null}
      {line.state === "landed" && line.figure && !["verified", "illustrative"].includes(line.figure.verification) ? (
        <span>{frameBadge(line.figure.verification)} ·</span>
      ) : null}
      {line.state === "landed" && line.figure ? (
        <>
          {line.figure.grounding === "retrieved" && (line.figure.passages ?? []).length && showMe.onPeekPassage ? (
            // The cited passages are § chips that peek, as RW1c's citations do (spec §6.2).
            <span>
              {SHOW_ME_COPY.landed} · {SHOW_ME_COPY.fromYourBooks}{" "}
              {(line.figure.passages ?? []).map((passage, index) => (
                <span key={`${passage.extractionId}:${passage.spanId}`}>
                  {index ? " · " : null}
                  <button type="button" style={link} data-show-me-passage={`${passage.extractionId}:${passage.spanId}`}
                    onClick={() => showMe.onPeekPassage?.(passage)}>{passageChip(passage)}</button>
                </span>
              ))}{" "}·
            </span>
          ) : (
            <span>{SHOW_ME_COPY.landed} · {showMeSourceLine(line.figure)} ·</span>
          )}
          <button type="button" style={link} onClick={() => line.figure && showMe.onOpen(line.figure)}>{SHOW_ME_COPY.open}</button>
        </>
      ) : null}
      {line.state === "failed" ? <MeaningLabel style={{ fontSize: 11 }}>{SHOW_ME_COPY.failed} (its line under the passage says why)</MeaningLabel> : null}
      {line.state !== "pending" ? (
        <button type="button" aria-label="dismiss" style={{ ...link, textDecoration: "none" }} onClick={() => showMe.onDismiss(line.key)}>{SHOW_ME_COPY.dismiss}</button>
      ) : null}
    </div>
  );
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
  helpStyleControl,
  enterSends = false,
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
  personalized = null,
  showMe = null,
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
                {helpStyleControl ?? (
                  <>
                    <Faint style={{ fontSize: 11 }}>mode</Faint>
                    <TermSelect
                      value={answerMode}
                      options={ANSWER_MODE_OPTIONS}
                      onChange={changeAnswerMode}
                      width={160}
                    />
                  </>
                )}
                {personalized ? (
                  <button
                    type="button"
                    data-ask-personalized=""
                    aria-pressed={personalized.on}
                    title={PERSONALIZED_COPY.why}
                    onClick={() => personalized.onToggle(!personalized.on)}
                    style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
                  >
                    {personalized.on ? PERSONALIZED_COPY.on : PERSONALIZED_COPY.off}
                  </button>
                ) : null}
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
                  } else if (enterSends && e.key === "Enter" && !e.shiftKey && !e.altKey) {
                    e.preventDefault();
                    void ask();
                  } else if (showMe && isShowMeKey(e)) {
                    // RW5d P1: the words go as a figure goal instead of a question.
                    e.preventDefault();
                    if (question.trim()) showMe.onShowMe();
                  }
                }}
                placeholder="ask about this passage…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 70, resize: "vertical" }}
              />
              <PrimaryButton onClick={ask} disabled={busy || (inquiry && offline) || !question.trim()}>{inquiry && parentExchange ? `ask follow-up · ${enterSends ? "↵" : "ctrl+↵"}` : `ask · ${enterSends ? "↵" : "ctrl+↵"}`}</PrimaryButton>
              {showMe ? (
                <div data-show-me="" style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
                  <SecondaryButton onClick={showMe.onShowMe} disabled={offline || !question.trim()}>{SHOW_ME_COPY.send}</SecondaryButton>
                  <Faint style={{ fontSize: 10 }}>{SHOW_ME_COPY.keys}</Faint>
                  <span title={SHOW_ME_COPY.where} style={{ marginLeft: "auto" }}>
                    <MeaningLabel style={{ fontSize: 10 }}>{SHOW_ME_COPY.whereLabel}</MeaningLabel>
                  </span>
                </div>
              ) : null}
              {showMe && showMe.lines.length ? (
                <div data-show-me-lines="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {showMe.lines.map((line) => <ShowMeThreadLine key={line.key} line={line} showMe={showMe} />)}
                </div>
              ) : null}
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

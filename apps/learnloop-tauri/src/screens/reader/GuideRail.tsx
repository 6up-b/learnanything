// The Reader rail's Guide tab (RW1a split of ReaderScreen; a move, not a
// redesign): the reading guide, contents, "worth a second look", the section
// quick checks, and the offline demo's fixture question.
import { useCallback, useEffect, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import { api } from "../../api/client";
import type {
  ReaderDisposition,
  ReaderGuidePlanDto,
  ReaderGuideSectionDto,
  ReaderRenderBlockDto,
} from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill, SectionHeader } from "../../components/term";
import { DispositionPicker, PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import { errorMessage } from "../../errors";
import type { PassageAlign } from "../../components/PdfReaderPane";
import { clip } from "./readerShared";
import { LearnerVoice, MeaningLabel, ModelVoice, SourceVoice } from "./voices";

export const QUESTION_CONTROLS: Array<{ value: string; label: string }> = [
  { value: "too_easy", label: "too easy" },
  { value: "too_intrusive", label: "bad moment" },
  { value: "ask_me_differently", label: "ask differently" },
  { value: "dont_bring_this_back", label: "don’t ask this again" },
  { value: "i_dont_understand", label: "I don’t understand" },
];

export interface GuideRailProps {
  visible: boolean;
  extractionId: string;
  offline: boolean;
  guidePlan: ReaderGuidePlanDto | null;
  guideLoading: boolean;
  currentGuideSection: ReaderGuideSectionDto | null;
  currentSectionProgress: number;
  /** How much of the current section the learner has read (UX Phase 1): the
   *  bar under its name, not where the reading marker stands. */
  currentSectionRead?: number;
  /** Passages read per section (monotone): Contents ticks a section only
   *  when it was read through (UX Phase 1 usability round 1, U3). */
  sectionSeen?: Record<string, number>;
  /** Whether the learner has moved the page themselves since the book opened
   *  or their last jump (UX Phase 1 usability round 2). */
  readingMoved?: boolean;
  currentQuestionOpen: boolean;
  boundaryChecksAvailable: boolean;
  authoringSections: string[];
  /** Sections whose check took too long to write: they say so, with Try
   *  again (UX Phase 1, §10 item 1.10). */
  timedOutSections?: string[];
  retryQuickCheck?: (sectionId: string) => void;
  revealedSections: string[];
  completedSections: string[];
  dismissedSections?: string[];
  /** Quick checks the learner answered this visit (UX Phase 1 round 2). */
  answeredSections?: string[];
  setAnsweredSections?: Dispatch<SetStateAction<string[]>>;
  /** The check a section break asked to open: started at once (U5). */
  focusQuickCheck?: string | null;
  annotatedSpans: Set<string>;
  openQuestionSections: ReaderGuideSectionDto[];
  setDismissedSections: Dispatch<SetStateAction<string[]>>;
  /** Ordinary reading navigation (Contents): moves the page, no detour. */
  jumpToSpan: (spanId: string, align?: PassageAlign) => void;
  /** An investigative jump (a passage worth a second look, a question's
   *  passage): a detour with a way back while reader_inquiry is on. */
  peekPassage?: (spanId: string) => void;
  revealSection: (sectionId: string) => void;
  completeSection: (sectionId: string) => void;
  onError: (message: string) => void;
  // The offline demo's fixture question (never shown over a real source).
  boundaryBlock: ReaderRenderBlockDto | null;
  boundarySkipped: boolean;
  setBoundarySkipped: Dispatch<SetStateAction<boolean>>;
  boundaryAnswered: boolean;
  setBoundaryAnswered: Dispatch<SetStateAction<boolean>>;
  boundaryResponse: string;
  setBoundaryResponse: Dispatch<SetStateAction<string>>;
  boundarySubmitted: boolean;
  setBoundarySubmitted: Dispatch<SetStateAction<boolean>>;
  questionControl: string | null;
  sendQuestionControl: (control: string) => void | Promise<void>;
  disposition: ReaderDisposition | null;
  chooseDisposition: (d: ReaderDisposition) => void | Promise<void>;
  /** RW3a: the margin marks' density control, legend and receipt (absent when cues are off). */
  footer?: ReactNode;
}

export function GuideRail({
  visible,
  extractionId,
  offline,
  guidePlan,
  guideLoading,
  currentGuideSection,
  currentSectionProgress,
  currentSectionRead,
  sectionSeen = {},
  readingMoved = true,
  currentQuestionOpen,
  boundaryChecksAvailable,
  authoringSections,
  timedOutSections = [],
  retryQuickCheck,
  revealedSections,
  completedSections,
  dismissedSections = [],
  answeredSections = [],
  setAnsweredSections,
  focusQuickCheck = null,
  annotatedSpans,
  openQuestionSections,
  setDismissedSections,
  jumpToSpan,
  peekPassage,
  revealSection,
  completeSection,
  onError,
  boundaryBlock,
  boundarySkipped,
  setBoundarySkipped,
  boundaryAnswered,
  setBoundaryAnswered,
  boundaryResponse,
  setBoundaryResponse,
  boundarySubmitted,
  setBoundarySubmitted,
  questionControl,
  sendQuestionControl,
  disposition,
  chooseDisposition,
  footer = null,
}: GuideRailProps) {
  const peek = peekPassage ?? jumpToSpan;
  // Without a read count (an older caller) the bar follows the reading marker.
  const sectionRead = currentSectionRead ?? currentSectionProgress;
  return (
    <div style={{ display: visible ? "block" : "none" }}>
      <SectionHeader style={{ marginTop: 0 }}>Reading guide</SectionHeader>
      {guidePlan?.goalContext ? (
        <Card style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 10, background: COLOR.washCyan }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>YOUR PATH</Faint>
          <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{guidePlan.goalContext.title}</span>
          <Faint style={{ fontSize: 10 }}>
            Reading toward your active goal
          </Faint>
        </Card>
      ) : null}
      {currentGuideSection ? (
        <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Pill color="slate">section</Pill>
            <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{currentGuideSection.label}</span>
          </div>
          <div
            role="progressbar"
            aria-label="Read of this section"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(sectionRead * 100)}
            style={{ height: 3, background: COLOR.border }}
          >
            <div style={{ height: "100%", width: `${sectionRead * 100}%`, background: COLOR.cyan }} />
          </div>
          <Faint style={{ fontSize: 10 }}>
            {boundaryChecksAvailable && currentGuideSection.question && currentQuestionOpen
              ? answeredSections.includes(currentGuideSection.id)
                ? "You answered this section's quick check: compare below, then keep reading."
                : currentGuideSection.question.placement === "auto_authored"
                ? "A quick check on this section is ready, just below."
                : currentGuideSection.question.readingPhase === "before_section"
                  ? "There’s an optional question before you begin this section."
                  : currentGuideSection.question.readingPhase === "during_section"
                    ? "There’s an optional question at this point in the section."
                    : "You’re near the section break. Take a quick check or keep reading."
              : authoringSections.includes(currentGuideSection.id)
                ? "◐ writing a quick check for this section…"
                : timedOutSections.includes(currentGuideSection.id)
                  ? (
                    <>
                      Couldn't write a check for this section ·{" "}
                      <button
                        type="button"
                        onClick={() => retryQuickCheck?.(currentGuideSection.id)}
                        style={{ background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", fontFamily: FONT_MONO, fontSize: 10 }}
                      >
                        Try again
                      </button>
                    </>
                  )
                : readingMoved && currentSectionProgress >= 0.7
                  ? "You’re near the section break. Keep going, or revisit a useful passage."
                  : "Keep reading at your own pace."}
          </Faint>
        </Card>
      ) : guideLoading ? (
        <Faint style={{ fontSize: 12 }}>◐ connecting this source to your learning path…</Faint>
      ) : guidePlan === null ? (
        <Faint style={{ fontSize: 12 }}>No personalized guide is available for this source yet.</Faint>
      ) : null}

      {/* Open quick checks come first, right under the section they are about,
          never below the whole Contents list (UX Phase 1 usability round 1, U5). */}
      {boundaryChecksAvailable
        ? openQuestionSections.map((section) => (
            <div key={section.id} data-quick-check={section.id}>
              {section.question?.placement === "auto_authored" ? (
                <AuthoredQuestionCard
                  section={section}
                  autoStart={focusQuickCheck === section.id}
                  onJump={peek}
                  onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                  onComplete={() => completeSection(section.id)}
                  onAnswered={() => setAnsweredSections?.((ids) => [...new Set([...ids, section.id])])}
                  onError={onError}
                />
              ) : (
                <SectionQuestionCard
                  section={section}
                  autoStart={focusQuickCheck === section.id}
                  extractionId={extractionId}
                  onReveal={() => revealSection(section.id)}
                  onJump={peek}
                  onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                  onComplete={() => completeSection(section.id)}
                  onAnswered={() => setAnsweredSections?.((ids) => [...new Set([...ids, section.id])])}
                  onError={onError}
                />
              )}
            </div>
          ))
        : null}

      {(guidePlan?.sections.length ?? 0) > 1 ? (
        <>
          <SectionHeader>Contents</SectionHeader>
          {/* The rail owns vertical scrolling. A nested Contents scroller
              traps wheel events at its edges in WebKitGTK/Tauri. */}
          <div style={{ display: "flex", flexDirection: "column", marginBottom: 4 }}>
            {guidePlan!.sections.map((section) => {
              // Ticked only when read through (or its check done), never
              // because the learner jumped past it (usability round 1, U3).
              const readThrough = completedSections.includes(section.id)
                || (sectionSeen[section.id] ?? 0) >= section.spanIds.length;
              const state = section.id === currentGuideSection?.id ? "current" : readThrough ? "read" : "upcoming";
              const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·";
              return (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => jumpToSpan(section.startSpanId, "start")}
                  title={section.question ? `${section.label} · quick check available` : section.label}
                  style={{
                    display: "flex", alignItems: "baseline", gap: 8, textAlign: "left",
                    border: 0, borderLeft: `3px solid ${state === "current" ? COLOR.amber : "transparent"}`,
                    background: state === "current" ? COLOR.washAmber : "transparent",
                    padding: "3px 8px", cursor: "pointer", fontFamily: FONT_MONO,
                  }}
                >
                  <span style={{ flexShrink: 0, fontSize: 10, color: state === "read" ? COLOR.green : state === "current" ? COLOR.amber : COLOR.textFaint }}>
                    {glyph}
                  </span>
                  <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 11, color: state === "current" ? COLOR.text : COLOR.textDim }}>
                    {section.label}
                  </span>
                  {/* Said in words, and only while the check is still to do
                      (usability round 2: an unexplained "?" sat after ✓). */}
                  {section.question && !completedSections.includes(section.id) && !dismissedSections.includes(section.id)
                    && !answeredSections.includes(section.id) ? (
                    <span style={{ flexShrink: 0, fontSize: 9, color: COLOR.purpleText }}>quick check</span>
                  ) : null}
                </button>
              );
            })}
          </div>
        </>
      ) : null}

      {currentGuideSection && revealedSections.includes(currentGuideSection.id) ? (
        <>
          <SectionHeader>Worth a second look</SectionHeader>
          {currentGuideSection.suggestedPassages.length === 0 ? (
            <Faint style={{ fontSize: 11 }}>No missed passages were identified in this section.</Faint>
          ) : currentGuideSection.suggestedPassages
              .filter((passage) => !annotatedSpans.has(passage.spanId))
              .map((passage) => (
                <Card key={passage.spanId} onClick={() => peek(passage.spanId)} style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 7, cursor: "pointer", background: COLOR.washPurple }}>
                  <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                    <Pill color={passage.learnerSignal === "recent_misunderstanding" ? "pink" : "purple"}>
                      {passage.learnerSignal === "recent_misunderstanding" ? "repair" : "important"}
                    </Pill>
                    <Faint style={{ fontSize: 10 }}>{passage.learningObjectTitle}</Faint>
                  </div>
                  <SourceVoice locator={currentGuideSection.label}>“{clip(passage.quote, 150)}”</SourceVoice>
                  <MeaningLabel style={{ lineHeight: 1.45 }}>{passage.reason}</MeaningLabel>
                </Card>
              ))}
        </>
      ) : null}

      {currentGuideSection && completedSections.includes(currentGuideSection.id) ? (
        <Card style={{ marginTop: 10, background: COLOR.washGreen }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.green }}>✓ quick check complete — keep going.</span>
        </Card>
      ) : null}

      {/* The boundary question below is fixture content (its text is authored for
          the demo chapter) — it renders only in the offline demo, never over a
          real source it does not belong to. */}
      {offline && boundaryBlock ? (
        <>
          <SectionHeader>Quick check</SectionHeader>
          <Card status="probe" style={{ background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 8 }}>
            <MeaningLabel style={{ fontSize: 11 }}>optional · not a test</MeaningLabel>
            <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
              Before executing: which decomposition reads off the variance here, and why?
            </span>
            {boundarySkipped ? (
              <Faint style={{ fontSize: 11 }}>Skipped. Keep reading.</Faint>
            ) : !boundaryAnswered ? (
              <>
                <div style={{ display: "flex", gap: 8 }}>
                  <PrimaryButton onClick={() => setBoundaryAnswered(true)}>respond ↵</PrimaryButton>
                  <SecondaryButton onClick={() => { setBoundarySkipped(true); void sendQuestionControl("skip"); }}>skip</SecondaryButton>
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {QUESTION_CONTROLS.map((option) => (
                    <SecondaryButton key={option.value} onClick={() => sendQuestionControl(option.value)}>{option.label}</SecondaryButton>
                  ))}
                </div>
                {questionControl === "i_dont_understand" ? (
                  <Faint style={{ fontSize: 11 }}>Let’s return to the passage that supports this question.</Faint>
                ) : questionControl ? (
                  <Faint style={{ fontSize: 11 }}>Got it. This changes how quick checks appear for you.</Faint>
                ) : null}
              </>
            ) : !boundarySubmitted ? (
              <>
                <textarea
                  autoFocus
                  value={boundaryResponse}
                  onChange={(event) => setBoundaryResponse(event.target.value)}
                  onKeyDown={(event) => {
                    if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && boundaryResponse.trim()) {
                      setBoundarySubmitted(true);
                    }
                  }}
                  placeholder="Answer in your own words…"
                  style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 76, resize: "vertical" }}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <PrimaryButton onClick={() => setBoundarySubmitted(true)} disabled={!boundaryResponse.trim()}>record answer · ctrl+↵</PrimaryButton>
                  <SecondaryButton onClick={() => setBoundaryAnswered(false)}>back</SecondaryButton>
                </div>
              </>
            ) : (
              <DispositionPicker value={disposition} onChoose={chooseDisposition} />
            )}
          </Card>
        </>
      ) : null}
      {footer}
    </div>
  );
}

export function SectionBoundaryOffer({
  section,
  allowQuestion,
  onOpen,
  onReveal,
  onDismiss,
}: {
  section: ReaderGuideSectionDto;
  allowQuestion: boolean;
  onOpen: () => void;
  onReveal: () => void;
  onDismiss: () => void;
}) {
  return (
    <Card status="probe" style={{ margin: "8px 0 18px", padding: 14, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Pill color="purple">section break</Pill>
        <MeaningLabel>optional · usually under a minute</MeaningLabel>
      </div>
      <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
        {allowQuestion && section.question
          ? `Before moving on, would you like to check what landed from “${section.label}”?`
          : `A few passages from “${section.label}” may be worth another look.`}
      </span>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {allowQuestion && section.question ? <PrimaryButton onClick={onOpen}>quick check →</PrimaryButton> : null}
        {section.suggestedPassages.length > 0 ? (
          <SecondaryButton onClick={onReveal}>
            show {section.suggestedPassages.length} passage{section.suggestedPassages.length === 1 ? "" : "s"} I may have missed
          </SecondaryButton>
        ) : null}
        <SecondaryButton onClick={onDismiss}>keep reading</SecondaryButton>
      </div>
    </Card>
  );
}

function AuthoredQuestionCard({
  section,
  autoStart = false,
  onJump,
  onDismiss,
  onComplete,
  onAnswered,
  onError,
}: {
  section: ReaderGuideSectionDto;
  /** Opened from a section break: start at once, ready to answer. */
  autoStart?: boolean;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
  /** The learner compared their answer (the guide stops calling it waiting). */
  onAnswered?: () => void;
  onError: (message: string) => void;
}) {
  const question = section.question;
  const [started, setStarted] = useState(false);
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [escalatedItemId, setEscalatedItemId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const questionId = question?.authoredQuestionId ?? null;
  const sourceSpan = question?.spanIds?.[0] ?? null;
  useEffect(() => {
    if (autoStart) setStarted(true);
  }, [autoStart]);

  const submit = useCallback(async () => {
    if (!questionId || !response.trim()) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "answered", response: response.trim() });
      setSubmitted(true);
      onAnswered?.();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, response, onError, onAnswered]);

  const dismissForever = useCallback(async () => {
    if (!questionId) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "dismissed" });
      onDismiss();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, onDismiss, onError]);

  const escalate = useCallback(async () => {
    if (!questionId || !question?.escalationLearningObjectId) return;
    setBusy(true);
    try {
      const result = await api.readerEscalateAuthoredQuestion({
        questionId,
        learningObjectId: question.escalationLearningObjectId,
      });
      setEscalatedItemId(result.practiceItemId);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, question, onError]);

  if (!question) return null;

  return (
    <Card status="probe" style={{ marginTop: 10, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 9 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
        <Pill color="purple">quick check</Pill>
        <MeaningLabel>optional · self-check, never a grade</MeaningLabel>
      </div>
      <MeaningLabel style={{ lineHeight: 1.5 }}>{question.reason}</MeaningLabel>
      {/* An AI-written question: LearnLoop's model's voice (W2). */}
      <ModelVoice first note="a quick check from this section">
        <MarkdownMath value={question.prompt} />
      </ModelVoice>
      {!started ? (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <PrimaryButton onClick={() => setStarted(true)}>think it through →</PrimaryButton>
          <SecondaryButton onClick={onDismiss}>keep reading</SecondaryButton>
        </div>
      ) : !submitted ? (
        <>
          <textarea
            autoFocus
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Answer in your own words…"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void submit();
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 82, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {/* Enter is a new line (answers can need several); the button
                names the key that really sends (usability round 1, U6). */}
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>compare with the source · ctrl+↵</PrimaryButton>
            <SecondaryButton onClick={onDismiss} disabled={busy}>skip</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          {/* The learner's own answer stays beside the intended one: there is
              something to compare (UX Phase 1 usability round 1, U6). */}
          <LearnerVoice label="your answer">
            <div style={{ whiteSpace: "pre-wrap" }}>{response.trim()}</div>
          </LearnerVoice>
          <ModelVoice note="the intended answer · compare, don’t grade">
            <MarkdownMath value={question.expectedAnswer ?? ""} />
          </ModelVoice>
          {escalatedItemId ? (
            <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ Added to your practice collection.</Faint>
          ) : null}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {!escalatedItemId && question.escalationLearningObjectId ? (
              <PrimaryButton onClick={() => void escalate()} disabled={busy}>add to practice →</PrimaryButton>
            ) : null}
            <SecondaryButton onClick={onComplete}>done for now</SecondaryButton>
          </div>
        </>
      )}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 2 }}>
        {sourceSpan ? (
          <button
            type="button"
            onClick={() => onJump(sourceSpan)}
            disabled={busy}
            style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
          >
            show me the passage
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => void dismissForever()}
          disabled={busy}
          style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
        >
          don’t bring this back
        </button>
      </div>
    </Card>
  );
}

function SectionQuestionCard({
  section,
  autoStart = false,
  extractionId,
  onReveal,
  onJump,
  onDismiss,
  onComplete,
  onAnswered,
  onError,
}: {
  section: ReaderGuideSectionDto;
  /** Opened from a section break: start at once, ready to answer. */
  autoStart?: boolean;
  extractionId: string;
  onReveal: () => void;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
  /** The learner's answer was recorded (the guide stops calling it waiting). */
  onAnswered?: () => void;
  onError: (message: string) => void;
}) {
  const question = section.question;
  const [administrationId, setAdministrationId] = useState<string | null>(null);
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [disposition, setDisposition] = useState<ReaderDisposition | null>(null);
  const [busy, setBusy] = useState(false);
  const [controlMessage, setControlMessage] = useState<string | null>(null);

  const begin = useCallback(async () => {
    if (!question?.practiceItemId || administrationId) return;
    setBusy(true);
    try {
      const opened = await api.readerPresentQuestion({
        practiceItemId: question.practiceItemId,
        readingPhase: question.readingPhase,
        goalId: question.goalId,
        targetContractVersionId: question.targetContractVersionId,
      });
      setAdministrationId(String(opened.administrationId ?? ""));
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [question, administrationId, onError]);

  useEffect(() => {
    if (autoStart) void begin();
    // Only the request to open it starts it; begin() itself is idempotent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart]);

  const submit = useCallback(async () => {
    if (!administrationId || !response.trim()) return;
    setBusy(true);
    try {
      await api.readerSubmitQuestion({
        administrationId,
        response: response.trim(),
        targetKey: question?.targetContractVersionId ?? undefined,
        outcomeClass: "unknown",
      });
      setSubmitted(true);
      onAnswered?.();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [administrationId, response, question, onError, onAnswered]);

  const skip = useCallback(async () => {
    try {
      if (administrationId) {
        await api.readerSkipQuestion(administrationId);
      } else if (question?.placementEventId) {
        await api.readerQuestionControl({
          control: "skip",
          subjectId: question.placementEventId,
          subjectType: "reader_question_placement",
        });
      }
    } catch (error) {
      onError(errorMessage(error));
      return;
    }
    onDismiss();
  }, [administrationId, question, onDismiss, onError]);

  const control = useCallback(async (value: string) => {
    if (!question?.placementEventId) return;
    setBusy(true);
    try {
      await api.readerQuestionControl({
        control: value,
        administrationId,
        subjectId: question.placementEventId,
        subjectType: "reader_question_placement",
      });
      if (value === "i_dont_understand") {
        setControlMessage("Let’s return to the passage that best supports this question.");
        if (section.suggestedPassages[0]) {
          await api.readerRestoreSource({
            extractionId,
            spanId: section.suggestedPassages[0].spanId,
          });
          onReveal();
          onJump(section.suggestedPassages[0].spanId);
        }
      } else if (value === "ask_me_differently") {
        setControlMessage("Got it. We’ll vary the wording next time; you can keep reading now.");
      } else {
        setControlMessage("Got it. This only changes how checks appear for you.");
      }
      if (["too_easy", "too_intrusive", "dont_bring_this_back"].includes(value)) onDismiss();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [question, administrationId, section.suggestedPassages, extractionId, onReveal, onJump, onDismiss, onError]);

  const choose = useCallback(async (next: ReaderDisposition) => {
    if (!question?.learningObjectId) return;
    setDisposition(next);
    try {
      await api.readerChooseDisposition({
        disposition: next,
        subjectId: question.learningObjectId,
        subjectType: "learning_object",
        goalId: question.goalId,
      });
      onComplete();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [question, onComplete, onError]);

  if (!question) {
    return section.suggestedPassages.length > 0 ? (
      <Card status="probe" style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8, background: COLOR.washPurple }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>Take a quick second pass before moving on?</span>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <PrimaryButton onClick={onReveal}>show important passages</PrimaryButton>
          <SecondaryButton onClick={onDismiss}>not now</SecondaryButton>
        </div>
      </Card>
    ) : null;
  }

  return (
    <Card status="probe" style={{ marginTop: 10, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 9 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
        <Pill color="purple">quick check</Pill>
        {question.goalTitle ? <Pill color="cyan">for {question.goalTitle}</Pill> : null}
        <MeaningLabel>optional · not a test</MeaningLabel>
      </div>
      <Faint style={{ fontSize: 10, lineHeight: 1.5 }}>{question.reason}</Faint>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>
        <MarkdownMath value={question.prompt} />
      </div>
      {!administrationId ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => void begin()} disabled={busy}>think it through →</PrimaryButton>
            <SecondaryButton onClick={() => void skip()} disabled={busy}>keep reading</SecondaryButton>
          </div>
          {section.suggestedPassages.length > 0 ? (
            <SecondaryButton onClick={() => {
              onReveal();
              onJump(section.suggestedPassages[0].spanId);
            }}>
              show the most relevant passage first
            </SecondaryButton>
          ) : null}
        </div>
      ) : !submitted ? (
        <>
          <textarea
            autoFocus
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Answer in your own words…"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void submit();
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 82, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>record answer · ctrl+↵</PrimaryButton>
            <SecondaryButton onClick={() => void skip()} disabled={busy}>skip</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ Answer recorded. This was for understanding, not a grade.</Faint>
          <Faint style={{ fontSize: 10 }}>What should LearnLoop do with this idea?</Faint>
          <DispositionPicker value={disposition} onChoose={(next) => void choose(next)} />
          <SecondaryButton onClick={onComplete}>done for now</SecondaryButton>
        </>
      )}
      {!submitted ? (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 2 }}>
          {QUESTION_CONTROLS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => void control(option.value)}
              disabled={busy}
              style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}
      {controlMessage ? <Faint style={{ fontSize: 10 }}>{controlMessage}</Faint> : null}
    </Card>
  );
}

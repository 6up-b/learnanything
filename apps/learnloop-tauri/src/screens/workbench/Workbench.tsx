// Reader workbench RW2a: the resumable scratchpad (spec §5.1; UX §5.1-5.3,
// §5.9, §5.10, wireframes W5, W8, W15).
//
//   header   WORKING · Exercise 5.14 · from the book, verbatim   (setup line)
//   problem  the verbatim stem, in the book's voice when it came from one
//   book     one line before step 1: open (counts as one hint) or hidden
//   work     numbered steps, each a LiveMarkdownEditor, saved as typed;
//            stuck steps in the learner's voice; deleted · undo
//   record   what the attempt will record, before Submit (G62)
//   actions  I'm stuck · Submit · Leave for now, and ⋯ Abandon (never one
//            stray key away, no confirmation)
//
// Keys (UX §3.5): ↵ at a step's end a new step, ⇧↵ a new line, Alt+↑/↓
// between steps, Ctrl+Backspace in an empty step deletes it, Ctrl+D I'm
// stuck, Ctrl+↵ submit, Ctrl+Shift+B the book, Esc leaves the editor and a
// second Esc is Leave for now. LiveMarkdownEditor binds none of these
// chords itself, so none clash (Ctrl+K stays free for RW2b's check).
// Nothing a save, a poll or a result does moves focus or opens a dialog.
import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent } from "react";
import type { WorkbenchSessionDto, WorkbenchSubmitDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { ItemPresentation } from "../../components/ItemPresentation";
import { LiveMarkdownEditor, type LiveMarkdownKeyInfo } from "../../render/LiveMarkdownEditor";
import { MarkdownMath } from "../../render/MarkdownMath";
import { errorMessage, getCommandError } from "../../errors";
import { LearnerVoice, MeaningLabel, SourceVoice } from "../reader/voices";
import { keyStatusLine } from "../reader/exerciseCandidates";
import { WORKBENCH_COPY, liveSteps, problemTitle, savedLabel, stepChain } from "./stepModel";
import { useWorkbenchSession } from "./useWorkbenchSession";
import { algoConfig } from "../../app/algoConfig";
import { CheckSummary, QuestionableNote, VerdictCell } from "./CheckColumn";
import { HelpLadder } from "./HelpLadder";
import { HelpStyleControl } from "./HelpStyleControl";
import { HintCard, type StepOption } from "./StepHints";
import { WhereThisGoes } from "./WhereThisGoes";
import { HELP_COPY, verdictFor, withLocalEdits } from "./helpModel";
import { useWorkbenchHelp } from "./useWorkbenchHelp";

export type WorkbenchLayout = "split" | "stacked" | "full";

export interface WorkbenchProps {
  initial: WorkbenchSessionDto;
  layout: WorkbenchLayout;
  /** A submitted problem, shown with its steps and what it recorded (UX S6). */
  readOnly?: boolean;
  /** The app's open practice session, when there is one. */
  practiceSessionId?: string | null;
  /** The serve this answers (the practice screen, the plan, a "check me"),
   *  as one pair; left undefined, the submit answers the serve the problem kept. */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
  /** The learner opened it just now: step 1 takes the caret. */
  autoFocus?: boolean;
  /** The book's visibility or the binding changed (the Reader covers its pane). */
  onSession?: (session: WorkbenchSessionDto) => void;
  onLeave: (session: WorkbenchSessionDto) => void;
  onAbandoned: (session: WorkbenchSessionDto) => void;
  onSubmitted: (result: WorkbenchSubmitDto) => void;
  /** Stacked layout: open the book in a sheet. */
  onShowInBook?: () => void;
  /** Practice screen: back to the plain answer box (the session carries the
   *  hints it holds back to it). */
  onAnswerBox?: (session: WorkbenchSessionDto) => void;
  /** The practice card already shows the item's own presentation above. */
  hideProblem?: boolean;
  /** RW2b: peek a passage of the book ("compare with the book"). */
  onPeekPassage?: (spanId: string) => void;
  onError: (message: string) => void;
}

const linkStyle: CSSProperties = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11,
  padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
};
const actionStyle: CSSProperties = {
  border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.text, fontFamily: FONT_MONO,
  fontSize: 11, padding: "5px 10px", cursor: "pointer",
};

function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select") !== null);
}

export function Workbench(props: WorkbenchProps) {
  const { initial, layout, readOnly = false, practiceSessionId = null, onError } = props;
  const wb = useWorkbenchSession(initial, { readOnly, onSession: props.onSession, onError });
  const { session, steps, record } = wb;
  const regionRef = useRef<HTMLElement | null>(null);
  const [focus, setFocus] = useState<{ key: string; n: number } | null>(() => {
    const first = steps[0];
    return props.autoFocus && first && !readOnly ? { key: first.key, n: 1 } : null;
  });
  const [menuOpen, setMenuOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showVersions, setShowVersions] = useState<string | null>(null);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const openedAt = useRef(Date.now());

  // "saved · 2 min ago" ages quietly (a text change, never a motion).
  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 30000);
    return () => clearInterval(timer);
  }, []);

  const title = problemTitle(session.stemMd);
  const fromBook = session.origin === "reader";
  const bound = session.practiceItemId !== null;
  const open = session.status === "open";
  const live = liveSteps(steps);
  // Leave or "answer box instead" is under way (round 4, F8): the steps and
  // their actions are read-only, and say so, until it goes or is held.
  const leaving = wb.leaving;
  // RW2b: checks and the help ladder, only while workbench.help_enabled is
  // on (null: the workbench is exactly RW2a's); its hints need the hint
  // service too (adaptive hints).
  const helpConfig = algoConfig().workbenchHelp;
  const hintsConfig = algoConfig().adaptiveHints;
  const help = useWorkbenchHelp({
    sessionId: session.sessionId,
    enabled: helpConfig !== null,
    hintsEnabled: helpConfig !== null && hintsConfig !== null,
    storedHelpStyle: hintsConfig?.helpStyle ?? "balanced",
    readOnly: readOnly || !open,
    beforeRequest: async () => {
      wb.flushEdits();
      return wb.drained();
    },
    onRecord: wb.applyRecord,
  });
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const helpOn = helpConfig !== null;
  const canHelp = helpOn && open && !readOnly && bound && !leaving;
  const focusedChain = (() => {
    const step = live.find((candidate) => candidate.key === focusedKey) ?? live[live.length - 1];
    return step ? stepChain(step) : null;
  })();
  const stepOptions: StepOption[] = live.flatMap((step, index) => {
    const chain = stepChain(step);
    return chain ? [{ chainId: chain, number: index + 1 }] : [];
  });
  // Review F6: the last check against the steps on screen now (an edit dims
  // its marker at once, with no save or model call).
  const check = helpOn ? withLocalEdits(help.check, live.map((step) => ({ chainId: stepChain(step), body: step.body }))) : null;
  // Review F5: help aimed at no saved step (a fresh problem's first move, a
  // step deleted since) is placed under the problem's steps, never dropped.
  const liveChains = new Set(stepOptions.map((option) => option.chainId));
  const onAStep = (stepId: string | null) => stepId !== null && liveChains.has(stepId);
  const ladderLoose = helpOn && help.ladder.open && !onAStep(help.ladder.focusedStepId ?? focusedChain);
  const pendingLoose = Boolean(helpOn && help.hintPending && !onAStep(help.hintPending.stepId ?? focusedChain));
  const noticeLoose = Boolean(helpOn && help.notice && !onAStep(help.notice.stepId ?? focusedChain));
  const looseHints = helpOn ? help.hints.filter((hint) => !onAStep(hint.aboutStepId)) : [];

  function runCheck() {
    if (canHelp) void help.runCheck();
  }

  function openHelp() {
    if (canHelp && help.hintsEnabled) help.openHelp(focusedChain);
  }

  function smallerStep() {
    const waypoint = [...help.hints].reverse().find((hint) => hint.kind === "waypoint" && hint.replies.includes("smaller_step"));
    if (canHelp && waypoint) void help.smallerStep(waypoint);
  }

  function peek(spanId: string) {
    if (fromBook && open && !session.sourceVisible) void wb.setBook(true);
    props.onPeekPassage?.(spanId);
  }

  function requestFocus(key: string) {
    setFocus((previous) => ({ key, n: (previous?.n ?? 0) + 1 }));
  }

  async function submit() {
    if (readOnly || !open || submitting || leaving) return;
    if (!bound) {
      setSubmitError(null);
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      // The serve is one pair (review F15): the surface's own, both
      // identifiers, or neither, and the server answers the one it kept.
      const named = props.schedulerCandidateId !== undefined || props.planPresentationId !== undefined;
      const result = await wb.submit({
        practiceSessionId,
        ...(named ? { schedulerCandidateId: props.schedulerCandidateId ?? null, planPresentationId: props.planPresentationId ?? null } : {}),
        latencySeconds: Math.max(0, Math.round((Date.now() - openedAt.current) / 1000)),
        ...(helpOn && confidence !== null ? { answerConfidence: confidence } : {}),
      });
      props.onSubmitted(result);
    } catch (error) {
      const command = getCommandError(error);
      setSubmitError(command?.code === "not_saved" ? command.message : `Couldn't submit: ${errorMessage(error)}`);
    } finally {
      setSubmitting(false);
    }
  }

  // Leave for now and "answer box instead" wait for the steps to save
  // (final verification F8): a step not saved holds the first press here,
  // with why; a second goes anyway, and the screen is told what was lost.
  const [leaveNote, setLeaveNote] = useState<string | null>(null);
  const departing = useRef(false);
  async function depart(then: (session: WorkbenchSessionDto) => void) {
    // A press while the departure is under way is that departure, not a
    // second one: it neither leaves twice nor counts as the second press.
    if (departing.current) return;
    departing.current = true;
    let result: { left: boolean; note: string | null };
    try {
      result = await wb.leave();
    } finally {
      departing.current = false;
    }
    if (!result.left) {
      setLeaveNote(result.note);
      return;
    }
    setLeaveNote(null);
    if (result.note) onError(result.note);
    then(wb.session);
  }
  async function leave() {
    await depart(props.onLeave);
  }

  async function abandon() {
    setMenuOpen(false);
    if (leaving) return;
    const closed = await wb.abandon();
    if (closed) props.onAbandoned(closed);
  }

  function stuck() {
    if (readOnly || !open || leaving) return;
    const key = wb.addStep(null, "stuck");
    requestFocus(key);
  }

  function toggleBook() {
    if (readOnly || !open || !fromBook || leaving) return;
    void wb.setBook(!session.sourceVisible);
  }

  function moveFocus(fromKey: string | null, delta: number) {
    const keys = live.map((step) => step.key);
    const index = fromKey ? keys.indexOf(fromKey) : -1;
    const target = keys[Math.min(keys.length - 1, Math.max(0, index + delta))];
    if (target) requestFocus(target);
  }

  function onRegionKeyDown(event: ReactKeyboardEvent<HTMLElement>) {
    const ctrl = event.ctrlKey || event.metaKey;
    const key = event.key;
    const handled = () => {
      event.preventDefault();
      event.stopPropagation();
    };
    if (key === "Escape") {
      handled();
      if (isTyping(event.target)) {
        (event.target as HTMLElement).blur();
        regionRef.current?.focus();
        return;
      }
      if (readOnly || !open) props.onLeave(session);
      else void leave();
      return;
    }
    if (readOnly) return;
    if (ctrl && key === "Enter") {
      handled();
      void submit();
    } else if (ctrl && !event.shiftKey && key.toLowerCase() === "d") {
      handled();
      stuck();
    } else if (ctrl && event.shiftKey && key.toLowerCase() === "b") {
      handled();
      toggleBook();
    } else if (helpOn && ctrl && !event.shiftKey && key.toLowerCase() === "k") {
      handled();
      runCheck();
    } else if (helpOn && ctrl && !event.shiftKey && key.toLowerCase() === "h") {
      handled();
      openHelp();
    } else if (helpOn && ctrl && event.shiftKey && key.toLowerCase() === "h") {
      handled();
      smallerStep();
    } else if (event.altKey && (key === "ArrowUp" || key === "ArrowDown")) {
      handled();
      const current = steps.find((step) => (event.target as HTMLElement).closest?.(`[data-step-key="${step.key}"]`));
      moveFocus(current?.key ?? null, key === "ArrowUp" ? -1 : 1);
    }
  }

  function onStepKeyDown(stepKey: string, event: ReactKeyboardEvent<HTMLTextAreaElement>, info: LiveMarkdownKeyInfo) {
    if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey && info.atEnd) {
      event.preventDefault();
      const key = wb.addStep(stepKey, "step");
      requestFocus(key);
    } else if (event.key === "Backspace" && (event.ctrlKey || event.metaKey) && info.empty) {
      event.preventDefault();
      event.stopPropagation();
      const index = live.findIndex((step) => step.key === stepKey);
      wb.deleteStep(stepKey);
      const previous = live[index - 1];
      if (previous) requestFocus(previous.key);
    }
  }

  const header = (
    <div data-testid="workbench-header" style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
      <span style={{ letterSpacing: "0.14em", color: COLOR.textFaint }}>
        {readOnly || session.status === "submitted" ? "SUBMITTED" : "WORKING"}
      </span>
      <span>
        {" · "}{title}
        {fromBook && session.sourceVisible ? " · from the book, verbatim" : ""}
      </span>
      {layout === "stacked" && fromBook && props.onShowInBook ? (
        <button type="button" onClick={props.onShowInBook} style={{ ...linkStyle, marginLeft: "auto" }}>show in the book ▾</button>
      ) : null}
      {layout === "full" && props.onAnswerBox && !readOnly ? (
        <button type="button" onClick={() => void depart((left) => props.onAnswerBox?.(left))} style={{ ...linkStyle, marginLeft: "auto" }}>answer box instead</button>
      ) : null}
      {helpOn && help.hintsEnabled && open && !readOnly ? (
        <span style={{ marginLeft: layout === "full" && props.onAnswerBox ? 8 : "auto" }}>
          <HelpStyleControl value={help.helpStyle} stored={help.storedHelpStyle} disabled={leaving}
            onChange={(style) => void help.setHelpStyle(style)} />
        </span>
      ) : null}
    </div>
  );

  const setup = !readOnly && session.status !== "submitted" ? (
    session.importStatus === "pending" && session.parts && session.parts.length > 1 ? (
      <div role="group" aria-label="which part" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <MeaningLabel style={{ fontSize: 11 }}>{WORKBENCH_COPY.partsAsk}</MeaningLabel>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {session.parts.map((part) => (
            <button key={part.practiceItemId} type="button" style={actionStyle} onClick={() => void wb.bind(part.practiceItemId)}>
              {part.title || part.prompt.slice(0, 60)}
            </button>
          ))}
        </div>
      </div>
    ) : session.importStatus === "pending" ? (
      <div role="status" aria-live="polite">
        <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {WORKBENCH_COPY.setup}</MeaningLabel>
      </div>
    ) : session.importStatus === "failed" ? (
      <div role="status" aria-live="polite">
        <MeaningLabel style={{ fontSize: 11 }}>
          {WORKBENCH_COPY.setupDidNotFinish} {session.importError ?? ""} {WORKBENCH_COPY.kept}{" "}
          <button type="button" style={linkStyle} onClick={() => void wb.retryImport()}>try again ↵</button>
        </MeaningLabel>
      </div>
    ) : session.importStatus === "bound" && session.sourceExercise ? (
      // RW4b: a textbook exercise from a proposal says what is verbatim, who
      // wrote the answer, and the key's honest status (the sources service's).
      <div data-testid="workbench-key-status">
        <MeaningLabel style={{ fontSize: 11 }}>
          {keyStatusLine(session.sourceExercise.keyStatus, session.sourceExercise.keyLabel)}
        </MeaningLabel>
      </div>
    ) : null
  ) : null;

  // Bound, the problem is the item's whole frozen presentation (a required
  // method's instruction, a shared setup, an error hunt's worked solution),
  // exactly what the grader is sent (review F9); before binding, the
  // verbatim selection is the provisional display.
  const problem = (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.14em", color: COLOR.textFaint }}>PROBLEM</span>
      {session.presentation && session.presentation.blocks.length > 0 ? (
        <div data-testid="workbench-presentation" style={{ fontSize: 13, color: COLOR.text, lineHeight: 1.6 }}>
          <ItemPresentation presentation={session.presentation} />
        </div>
      ) : fromBook ? (
        <SourceVoice locator="verbatim">
          <MarkdownMath value={session.stemMd} />
        </SourceVoice>
      ) : (
        <div style={{ fontSize: 13, color: COLOR.text, lineHeight: 1.6 }}>
          <MarkdownMath value={session.stemMd} />
        </div>
      )}
    </div>
  );

  const bookLine = fromBook && open && !readOnly && !wb.started ? (
    <div role="radiogroup" aria-label="the book while you work" style={{ display: "flex", flexDirection: "column", gap: 2, fontFamily: FONT_MONO, fontSize: 11 }}>
      {([true, false] as const).map((visible) => {
        const checked = session.sourceVisible === visible;
        return (
          <button
            key={String(visible)}
            type="button"
            role="radio"
            aria-checked={checked}
            aria-disabled={leaving}
            onClick={() => {
              if (!checked && !leaving) void wb.setBook(visible);
            }}
            style={{ ...linkStyle, textDecoration: "none", color: checked ? COLOR.text : COLOR.textDim, textAlign: "left" }}
          >
            {checked ? "●" : "○"} {visible ? WORKBENCH_COPY.bookOpen : WORKBENCH_COPY.bookHidden}
          </button>
        );
      })}
    </div>
  ) : null;

  let number = 0;
  const work = (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.14em", color: COLOR.textFaint }}>YOUR WORK</span>
        {!readOnly ? (
          <span style={{ marginLeft: "auto" }}>
            <MeaningLabel style={{ color: wb.save.state === "saved" || wb.save.state === "saving" ? COLOR.textDim : COLOR.amber }}>
              {savedLabel(wb.save, nowMs)}
            </MeaningLabel>
            {leaving ? (
              <span role="status" aria-live="polite">
                <MeaningLabel style={{ color: COLOR.textDim }}>{" · "}{WORKBENCH_COPY.leavingPaused}</MeaningLabel>
              </span>
            ) : null}
          </span>
        ) : null}
      </div>
      <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
        {steps.map((step) => {
          number += 1;
          const label = `Step ${number}${step.kind === "stuck" ? " (stuck)" : ""}`;
          if (step.deleted) {
            return (
              <li key={step.key} data-step-key={step.key} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                <span>{`step ${number} deleted ·`}</span>{" "}
                <button type="button" style={linkStyle} aria-disabled={leaving} onClick={() => wb.undoDelete(step.key)}>undo</button>
              </li>
            );
          }
          const editor = readOnly ? (
            <div style={{ fontSize: 13, color: COLOR.text }}><MarkdownMath value={step.body} /></div>
          ) : (
            <LiveMarkdownEditor
              value={step.body}
              onChange={(body) => wb.setBody(step.key, body)}
              readOnly={leaving}
              ariaLabel={label}
              placeholder={step.kind === "stuck" ? WORKBENCH_COPY.stuckPrompt : "your next step — $math$ renders as you move off it"}
              focusable
              compact
              focusSignal={focus?.key === step.key ? focus.n : 0}
              onKeyDown={(event, info) => onStepKeyDown(step.key, event, info)}
              onBlur={wb.flushEdits}
            />
          );
          const chain = stepChain(step);
          const verdict = helpOn && chain ? verdictFor(check, chain) : null;
          const stepHints = helpOn && chain ? help.hints.filter((hint) => hint.aboutStepId === chain) : [];
          const ladderHere = helpOn && help.ladder.open && chain !== null && (help.ladder.focusedStepId ?? focusedChain) === chain;
          const pendingHere = helpOn && help.hintPending && chain !== null && (help.hintPending.stepId ?? focusedChain) === chain;
          const noticeHere = helpOn && help.notice && chain !== null && (help.notice.stepId ?? focusedChain) === chain;
          // UX §5.2: focusing a step lightly outlines the steps it depends on (the last check's graph).
          const focusedVerdict = helpOn && focusedKey ? verdictFor(check, stepChain(live.find((entry) => entry.key === focusedKey) ?? step) ?? "") : null;
          const outlined = Boolean(chain && focusedVerdict?.dependsOn.includes(chain));
          return (
            <li key={step.key} data-step-key={step.key} data-depended-on={outlined ? "true" : undefined}
              style={{ display: "flex", gap: 8, alignItems: "flex-start", ...(outlined ? { outline: `1px dotted ${COLOR.border}` } : {}) }}
              onFocusCapture={helpOn ? () => setFocusedKey(step.key) : undefined}>
              <span aria-hidden="true" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber, paddingTop: 4, minWidth: 28 }}>{number} ›</span>
              <div style={{ flex: 1, minWidth: 0, opacity: step.kind === "stuck" ? 0.8 : 1 }}>
                {step.kind === "stuck" ? <LearnerVoice label="you · stuck">{editor}</LearnerVoice> : editor}
                {helpOn && step.kind === "stuck" && !readOnly ? <WhereThisGoes box="stuck" /> : null}
                {helpOn && check && chain ? <QuestionableNote check={check} chainId={chain} /> : null}
                {stepHints.map((hint) => (
                  <HintCard key={hint.assistId} hint={hint} steps={stepOptions} pending={Boolean(help.hintPending) || !canHelp}
                    bridge={help.bridges[hint.assistId]}
                    onReply={(reply) => void help.reply(hint, reply)} onBookWay={() => void help.bookWay(hint)}
                    onSmallerStep={() => void help.smallerStep(hint)}
                    onAnswer={(text) => void help.answerDiscriminating(hint, text)}
                    onSkip={() => help.openHelp(hint.aboutStepId)} onPeek={props.onPeekPassage ? peek : undefined} />
                ))}
                {pendingHere ? (
                  <div role="status" aria-live="polite">
                    <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {HELP_COPY.writing}</MeaningLabel>{" "}
                    <button type="button" style={{ ...linkStyle, fontSize: 10 }} onClick={() => void help.cancelHint()}>cancel</button>
                  </div>
                ) : null}
                {noticeHere && help.notice ? (
                  <div role="status" aria-live="polite"><MeaningLabel style={{ fontSize: 11 }}>{help.notice.message}</MeaningLabel></div>
                ) : null}
                {ladderHere ? (
                  <HelpLadder ladder={help.ladder} onChoose={help.choose}
                    onTake={(level) => {
                      void help.take(level);
                      requestFocus(step.key);
                    }}
                    onClose={() => {
                      help.closeHelp();
                      requestFocus(step.key);
                    }} />
                ) : null}
                {step.versions.length > 0 ? (
                  <div style={{ marginTop: 2 }}>
                    <button type="button" style={{ ...linkStyle, fontSize: 10 }} onClick={() => setShowVersions((key) => (key === step.key ? null : step.key))}>
                      ↺ your earlier versions
                    </button>
                    {showVersions === step.key ? (
                      <div style={{ opacity: 0.6 }}>
                        {step.versions.map((version) => (
                          <LearnerVoice key={version.stepId} label="you · earlier"><MarkdownMath value={version.bodyMd} /></LearnerVoice>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
              {helpOn && check ? <VerdictCell verdict={verdict} symbolicEnabled={check.symbolicEnabled} /> : null}
              {!readOnly ? (
                <button type="button" aria-label={`delete step ${number}`} aria-disabled={leaving} style={{ ...linkStyle, fontSize: 10, color: COLOR.textDim }} onClick={() => wb.deleteStep(step.key)}>
                  delete
                </button>
              ) : null}
            </li>
          );
        })}
      </ol>
      {looseHints.length || pendingLoose || noticeLoose || ladderLoose ? (
        <div data-testid="workbench-problem-help" style={{ display: "flex", flexDirection: "column", gap: 4, marginLeft: 36 }}>
          {looseHints.map((hint) => (
            <HintCard key={hint.assistId} hint={hint} steps={stepOptions} pending={Boolean(help.hintPending) || !canHelp}
              bridge={help.bridges[hint.assistId]}
              onReply={(reply) => void help.reply(hint, reply)} onBookWay={() => void help.bookWay(hint)}
              onSmallerStep={() => void help.smallerStep(hint)}
              onAnswer={(text) => void help.answerDiscriminating(hint, text)}
              onSkip={() => help.openHelp(hint.aboutStepId)} onPeek={props.onPeekPassage ? peek : undefined} />
          ))}
          {pendingLoose ? (
            <div role="status" aria-live="polite">
              <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {HELP_COPY.writing}</MeaningLabel>{" "}
              <button type="button" style={{ ...linkStyle, fontSize: 10 }} onClick={() => void help.cancelHint()}>cancel</button>
            </div>
          ) : null}
          {noticeLoose && help.notice ? (
            <div role="status" aria-live="polite"><MeaningLabel style={{ fontSize: 11 }}>{help.notice.message}</MeaningLabel></div>
          ) : null}
          {ladderLoose ? (
            <HelpLadder ladder={help.ladder} onChoose={help.choose}
              onTake={(level) => void help.take(level)}
              onClose={() => help.closeHelp()} />
          ) : null}
        </div>
      ) : null}
      {!readOnly && open ? (
        <button type="button" aria-disabled={leaving} style={{ ...linkStyle, alignSelf: "flex-start", fontSize: 10 }} onClick={() => { if (!leaving) requestFocus(wb.addStep(live[live.length - 1]?.key ?? null, "step")); }}>
          + a step
        </button>
      ) : null}
    </div>
  );

  const confidenceRow = helpOn && open && !readOnly && bound ? (
    <div role="radiogroup" aria-label={HELP_COPY.confidence} data-testid="workbench-confidence"
      style={{ display: "flex", gap: 6, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
      <span>{HELP_COPY.confidence}</span>
      {[1, 2, 3, 4, 5].map((value) => (
        <button key={value} type="button" role="radio" aria-checked={confidence === value}
          onClick={() => setConfidence((current) => (current === value ? null : value))}
          style={{ ...linkStyle, textDecoration: "none", color: confidence === value ? COLOR.text : COLOR.textDim }}>
          {confidence === value ? `[${value}]` : value}
        </button>
      ))}
    </div>
  ) : null;

  const recordLine = (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {record.stuckNote && !readOnly ? <MeaningLabel style={{ fontSize: 11 }}>{record.stuckNote}</MeaningLabel> : null}
      {!readOnly ? <MeaningLabel style={{ fontSize: 11 }}><span data-testid="workbench-record">{record.line}</span></MeaningLabel> : null}
    </div>
  );

  const actions = !readOnly && open ? (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", position: "relative" }}>
      <div role="group" aria-label="workbench actions" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {helpOn ? (
          <button type="button" style={{ ...actionStyle, color: bound ? COLOR.text : COLOR.textDim }} aria-disabled={!bound || leaving || help.checkPending}
            onClick={runCheck}>
            {bound ? `${HELP_COPY.check} · ${HELP_COPY.checkKey}` : `${HELP_COPY.check} · ${WORKBENCH_COPY.waitsForSetup}`}
          </button>
        ) : null}
        {helpOn && help.hintsEnabled ? (
          <button type="button" style={{ ...actionStyle, color: bound ? COLOR.text : COLOR.textDim }} aria-disabled={!bound || leaving}
            aria-expanded={help.ladder.open} onClick={openHelp}>
            {bound ? `${HELP_COPY.help} · ${HELP_COPY.helpKey}` : `${HELP_COPY.help} · ${WORKBENCH_COPY.waitsForSetup}`}
          </button>
        ) : null}
        <button type="button" style={actionStyle} aria-disabled={leaving} onClick={stuck}>I'm stuck · ctrl+d</button>
        <button
          type="button"
          style={{ ...actionStyle, borderColor: bound ? COLOR.borderFocus : COLOR.border, color: bound ? COLOR.text : COLOR.textDim }}
          aria-disabled={!bound || submitting || leaving}
          onClick={() => void submit()}
        >
          {bound ? (submitting ? "submit · sending…" : "submit · ctrl+↵") : `submit · ${WORKBENCH_COPY.waitsForSetup}`}
        </button>
        <button type="button" style={actionStyle} aria-disabled={leaving} onClick={() => void leave()}>
          {leaving ? WORKBENCH_COPY.leaving : "leave for now · esc esc"}
        </button>
        <button type="button" aria-label="more actions" aria-haspopup="menu" aria-expanded={menuOpen} aria-disabled={leaving} style={actionStyle} onClick={() => { if (!leaving) setMenuOpen((value) => !value); }}>⋯</button>
      </div>
      {menuOpen ? (
        <div role="menu" aria-label="more actions" style={{ position: "absolute", bottom: "100%", right: 0, background: COLOR.bgElev, border: `1px solid ${COLOR.border}`, padding: 6, zIndex: 5 }}>
          <button type="button" role="menuitem" style={{ ...linkStyle, textDecoration: "none", color: COLOR.text }} onClick={() => void abandon()}>
            Abandon this problem
          </button>
          <div><MeaningLabel>your steps are kept; reopen it any time</MeaningLabel></div>
        </div>
      ) : null}
    </div>
  ) : null;

  const reopenLine = !readOnly && session.status === "abandoned" ? (
    <MeaningLabel style={{ fontSize: 11 }}>
      {WORKBENCH_COPY.abandoned}{" "}
      <button type="button" style={linkStyle} onClick={() => void wb.reopen()}>reopen</button>
    </MeaningLabel>
  ) : null;

  return (
    <section
      ref={regionRef}
      role="region"
      aria-label="workbench"
      tabIndex={-1}
      onKeyDown={onRegionKeyDown}
      style={{ display: "flex", flexDirection: "column", gap: 12, padding: layout === "full" ? "4px 0" : "16px 20px", outline: "none", minWidth: 0 }}
    >
      {header}
      {setup}
      {props.hideProblem ? null : problem}
      {bookLine}
      {work}
      {submitError ? (
        <div role="status" aria-live="polite">
          <MeaningLabel style={{ fontSize: 11, color: COLOR.amber }}>
            {`${submitError} ${WORKBENCH_COPY.kept}`}
          </MeaningLabel>{" "}
          <button type="button" style={linkStyle} onClick={() => void submit()}>try again ↵</button>
        </div>
      ) : null}
      {leaveNote ? (
        <div role="status" aria-live="polite">
          <MeaningLabel style={{ fontSize: 11, color: COLOR.amber }}>{leaveNote}</MeaningLabel>
        </div>
      ) : null}
      {helpOn ? <CheckSummary check={check} pending={help.checkPending} notice={help.checkNotice} /> : null}
      {confidenceRow}
      {recordLine}
      {actions}
      {reopenLine}
      <div style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 6, display: "flex", gap: 10, alignItems: "baseline" }}>
        <MeaningLabel>{record.footer}</MeaningLabel>
        {readOnly ? (
          <button type="button" style={{ ...linkStyle, marginLeft: "auto" }} onClick={() => props.onLeave(session)}>esc · back to reading</button>
        ) : null}
      </div>
    </section>
  );
}

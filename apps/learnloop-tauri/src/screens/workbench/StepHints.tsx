// Reader workbench RW2b: hints under the step they are about (UX §5.6-5.8,
// W6-W7; spec §5.2 rules 1-3, G33, G37, G60). Each hint in the model's voice,
// its label naming its kind, rung, the step it is about and the step it
// continues from; under it a goal's *a smaller step toward this goal*, *this
// doesn't connect to my work…* (four shortcuts, each saying what it does, a
// step picker, a one-line box) and *show me the book's way*; a question
// before a hint has its own answer box, never a step; the bridge to the book
// lands later beneath. Earlier hints stay where they landed. Nothing here
// moves focus, animates or opens a modal.
import { useState, type KeyboardEvent, type ReactNode } from "react";
import type { HintShortcut, WorkbenchHintViewDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { quietLine, quietLink } from "../../components/PlainParts";
import { MarkdownMath } from "../../render/MarkdownMath";
import { MeaningLabel, ModelVoice } from "../reader/voices";
import { HELP_COPY, WORKBENCH_SHORTCUTS, claimLine, hintLabel } from "./helpModel";
import type { BridgeState } from "./useWorkbenchHelp";
import { WhereThisGoes } from "./WhereThisGoes";

const chip = (on: boolean) => ({
  border: `1px solid ${on ? COLOR.borderFocus : COLOR.border}`,
  background: on ? COLOR.washAmber : "transparent",
  color: on ? COLOR.amberLink : COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: "2px 6px",
  cursor: "pointer",
  textAlign: "left" as const,
});

export interface StepOption {
  chainId: string;
  number: number;
}

export function FeedbackBox({
  hint,
  steps,
  disabled,
  onSend,
}: {
  hint: WorkbenchHintViewDto;
  steps: StepOption[];
  disabled: boolean;
  onSend: (reply: { shortcut?: HintShortcut; text?: string; stepId?: string | null }) => void;
}) {
  const [shortcut, setShortcut] = useState<HintShortcut | null>(null);
  const [text, setText] = useState("");
  const [stepId, setStepId] = useState<string | null>(hint.aboutStepId);
  const send = () => {
    if (!disabled) onSend({ shortcut: shortcut ?? undefined, text, stepId });
  };
  const onKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      send();
    }
  };
  return (
    <div data-testid="workbench-feedback" style={{ display: "grid", gap: 4, marginTop: 4 }}>
      <div role="group" aria-label="what didn't connect" style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {WORKBENCH_SHORTCUTS.map((entry) => (
          <button key={entry.value} type="button" aria-pressed={shortcut === entry.value} title={entry.does}
            onClick={() => setShortcut((current) => (current === entry.value ? null : entry.value))} style={chip(shortcut === entry.value)}>
            {entry.label}
          </button>
        ))}
      </div>
      {shortcut ? <MeaningLabel>{WORKBENCH_SHORTCUTS.find((entry) => entry.value === shortcut)?.does}</MeaningLabel> : null}
      <label style={{ ...quietLine, fontFamily: FONT_MONO, fontSize: 11 }}>
        {HELP_COPY.aboutStep}{" "}
        <select aria-label="about step" value={stepId ?? ""} onChange={(event) => setStepId(event.target.value || null)}
          style={{ fontFamily: FONT_MONO, fontSize: 11 }}>
          {steps.map((step) => <option key={step.chainId} value={step.chainId}>{step.number}</option>)}
        </select>
      </label>
      <MeaningLabel>{HELP_COPY.sameRung}</MeaningLabel>
      <input type="text" className="text-input" aria-label={HELP_COPY.sayMore} placeholder={HELP_COPY.sayMore}
        value={text} onChange={(event) => setText(event.target.value)} onKeyDown={onKey} style={{ width: "100%", fontSize: 12 }} />
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <button type="button" style={quietLink} disabled={disabled} onClick={send}>{HELP_COPY.nextHint}</button>
        <WhereThisGoes box="doesntConnect" />
      </div>
    </div>
  );
}

function DiscriminatingBox({ hint, disabled, onAnswer, onSkip }: {
  hint: WorkbenchHintViewDto;
  disabled: boolean;
  onAnswer: (text: string) => void;
  onSkip: () => void;
}) {
  const [text, setText] = useState("");
  if (hint.discriminatingAnswer) {
    return <div data-testid="workbench-discriminating-settled"><MeaningLabel style={{ fontSize: 11 }}>{hint.discriminatingAnswer.message}</MeaningLabel></div>;
  }
  return (
    <div style={{ display: "grid", gap: 3, marginTop: 4 }}>
      <input type="text" className="text-input" aria-label={HELP_COPY.answerBox} value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            if (text.trim()) onAnswer(text);
          }
        }}
        style={{ width: "100%", fontSize: 12 }} />
      <div style={{ ...quietLine, display: "flex", gap: 8, alignItems: "baseline" }}>
        <button type="button" style={quietLink} disabled={!text.trim()} onClick={() => onAnswer(text)}>{HELP_COPY.answer}</button>
        <span aria-hidden="true">·</span>
        <button type="button" style={quietLink} disabled={disabled} onClick={onSkip}>{HELP_COPY.skip}</button>
        <WhereThisGoes box="discriminating" />
      </div>
    </div>
  );
}

export function HintCard({
  hint,
  steps,
  pending,
  bridge,
  onReply,
  onBookWay,
  onSmallerStep,
  onAnswer,
  onSkip,
  onPeek,
}: {
  hint: WorkbenchHintViewDto;
  steps: StepOption[];
  pending: boolean;
  bridge: BridgeState | undefined;
  onReply: (reply: { shortcut?: HintShortcut; text?: string; stepId?: string | null }) => void;
  onBookWay: () => void;
  onSmallerStep: () => void;
  onAnswer: (text: string) => void;
  onSkip: () => void;
  onPeek?: (spanId: string) => void;
}) {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const asking = hint.kind === "discriminating";
  const authored = hint.labels?.origin === "from the item";
  // The item's own hints are labelled "from the item" (G-H12), never the
  // model's voice; every other hint is AI-written, in the model's voice.
  const Voice = authored ? ItemVoice : ModelVoice;
  return (
    <div data-testid="workbench-hint" data-hint-kind={hint.kind} data-level={hint.level} style={{ marginTop: 4 }}>
      <Voice note={hintLabel(hint).replace(/^◇ model · /, "")}>
        <MarkdownMath value={hint.hintMd} />
        {hint.claims?.length ? (
          // Reader §5.3 (review F14): what the hint claims about a step, each
          // labelled checked or the model's reading.
          <div data-testid="workbench-hint-claims" style={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {hint.claims.map((claim, index) => (
              <MeaningLabel key={index} style={{ fontSize: 11 }}>
                <span data-claim-status={claim.status}>{claimLine(claim)}</span>
              </MeaningLabel>
            ))}
          </div>
        ) : null}
        {asking ? (
          <DiscriminatingBox hint={hint} disabled={pending} onAnswer={onAnswer} onSkip={onSkip} />
        ) : null}
        <div style={{ ...quietLine, fontSize: 11, display: "flex", gap: 6, flexWrap: "wrap" }} data-testid="workbench-hint-replies">
          {hint.replies.includes("smaller_step") ? (
            <button type="button" style={quietLink} disabled={pending} onClick={onSmallerStep}>{HELP_COPY.smallerStep}</button>
          ) : null}
          {hint.replies.includes("doesnt_connect") ? (
            <button type="button" style={quietLink} aria-expanded={feedbackOpen} title={HELP_COPY.doesntConnectTitle}
              onClick={() => setFeedbackOpen((open) => !open)}>{HELP_COPY.doesntConnect}</button>
          ) : null}
          {hint.replies.includes("book_way") ? (
            <button type="button" style={quietLink} disabled={pending} onClick={onBookWay}>{HELP_COPY.bookWay}</button>
          ) : null}
        </div>
        {feedbackOpen ? (
          <FeedbackBox hint={hint} steps={steps} disabled={pending} onSend={(reply) => {
            setFeedbackOpen(false);
            onReply(reply);
          }} />
        ) : null}
        {bridge?.status === "pending" ? <MeaningLabel>{HELP_COPY.bridging}</MeaningLabel> : null}
        {bridge?.status === "ready" && bridge.line ? (
          <button type="button" data-testid="workbench-bridge" style={{ ...quietLink, fontSize: 11 }}
            onClick={() => (bridge.spanId && onPeek ? onPeek(bridge.spanId) : undefined)}>
            {bridge.line}
          </button>
        ) : null}
      </Voice>
    </div>
  );
}

function ItemVoice({ note, children }: { note: string; children: ReactNode }) {
  return (
    <div data-voice="item" style={{ borderLeft: `1px solid ${COLOR.border}`, paddingLeft: 8, display: "flex", flexDirection: "column", gap: 3 }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>{note}</span>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>{children}</div>
    </div>
  );
}

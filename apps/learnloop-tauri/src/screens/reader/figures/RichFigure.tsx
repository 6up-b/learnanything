// Reader RW5d P2b: rich figures, the Manim half (spec_reader_show_me_figures_v1 §6.8, §9b.3, §9b.4).
//
// A Manim figure plays its content-addressed mp4 through the shared blob-URL
// player, with its transcript (the narration) on demand and the check lines
// code ran on its declared functions, always ending "the video itself is not
// checked frame by frame". Its badge is code-owned (RICH_FRAME): never
// "checked against the book".
//
// Progressive delivery: a quick figure shows at once; its fuller version is
// one dim line inside the same frame, under the figure ("◌ a fuller animation
// is being written", then "◇ a fuller animation is ready · open ▸"); open
// swaps the frame's content and "◂ the quick version" swaps back: one figure
// line, two versions. A rich build with no quick figure is a pending line under
// its passage naming the job's real phase. Nothing here is a toast, a count or
// a badge elsewhere, and nothing takes focus or plays by itself (SM10, W12).
import { useState } from "react";
import type { ReactNode } from "react";
import type { FigureFullerDto, FigureManimCheckDto, FigureRichPendingDto, FigureViewDto } from "../../../api/dto";
import { AnimationPlayer } from "../../../components/AnimationPlayer";
import { COLOR, FONT_MONO } from "../../../components/term";
import { MeaningLabel, ModelVoice } from "../voices";
import { FIGURE_FRAME, linkStyle } from "./FigureInline";

/** The code-owned words of rich figures (badge slot, check lines, cues). */
export const RICH_FRAME = {
  manim: "AI-made video · not checked against the book",
  manimUnchecked: "AI-made video · not checked",
  manimNotFromBooks: "AI-made video · not from your books",
  cantShow: "can't show this kind here",
  collapsed: "animation",
  notCovered: "the video itself is not checked frame by frame",
  info: "Written by LearnLoop's model as a short animation script and rendered on this computer in a sealed "
    + "sandbox, with no network and no access to your files.",
  transcript: "transcript ▸",
  hideTranscript: "transcript ▾",
  fullerPending: "◌ a fuller animation is being written · keep reading",
  fullerReady: "◇ a fuller animation is ready",
  open: "open ▸",
  quick: "◂ the quick version",
  fullerFailed: "the fuller animation couldn't be built",
  why: "why ▸",
  fullerWaiting: "the fuller animation is waiting for the ChatGPT plan",
  collapsedReady: "a fuller animation is ready",
  cancel: "cancel",
  tryAgain: "try again",
  richFailed: "the animation couldn't be built",
  notRight: "not right?",
  notRightPlaceholder: "what should change? (optional)",
  notRightWhere: "Goes to the animation writer with this version; the new version is checked and rendered like this "
    + "one, and this one is kept.",
  differentKind: "try a different kind of figure",
  askBetter: "ask for a better version",
  richWaiting: "◐ the animation is waiting for the ChatGPT plan",
  optIn: "LearnLoop can make narrated animations by running AI-written animation code in a sealed sandbox on this "
    + "computer (no network, no access to your files)",
  allow: "allow",
  notNow: "not now",
} as const;

/** The pending line's phases, in plain words (the job's report heartbeat; no percentages). */
export const RICH_PHASES: Readonly<Record<string, string>> = Object.freeze({
  writing: "◐ writing an animation for this passage",
  checking: "◐ checking it",
  rendering: "◐ rendering the video (manim)",
});

export function manimBadge(figure: FigureViewDto): string {
  if (figure.verification === "unsupported") return RICH_FRAME.cantShow;
  if (figure.verification === "failed") return FIGURE_FRAME.failed;
  if (figure.grounding === "none") return RICH_FRAME.manimNotFromBooks;
  return figure.manim?.checks.length ? RICH_FRAME.manim : RICH_FRAME.manimUnchecked;
}

/** One check line, written here from closed fields (the function and expression are identifiers and a formula). */
export function manimCheckLine(check: FigureManimCheckDto): string {
  const settings = `at ${check.settings} tested setting${check.settings === 1 ? "" : "s"}`;
  if (check.kind === "equals") {
    return check.plotted
      ? `the curve is drawn from ${check.function}, which matches ${check.expr ?? ""} ${settings}`
      : `${check.function} matches ${check.expr ?? ""} ${settings}`;
  }
  const property = check.property === "nonnegative" ? "is never negative"
    : check.property === "bounded" ? `stays within ±${check.bound ?? ""}` : "stays finite";
  return `${check.function} ${property} ${settings}`;
}

/** "Not right?" on an animation (spec §8.5): the note (and, unless "try a different kind
 * of figure" is ticked, this version's program) goes to the animation writer. */
export function ManimNotRight({ onRevise }: { onRevise: (note: string, differentKind: boolean) => void }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [differentKind, setDifferentKind] = useState(false);
  if (!open) {
    return <button type="button" style={linkStyle} onClick={() => setOpen(true)}>{RICH_FRAME.notRight}</button>;
  }
  return (
    <form data-manim-not-right="" style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}
      onSubmit={(event) => {
        event.preventDefault();
        onRevise(note, differentKind);
        setOpen(false);
        setNote("");
        setDifferentKind(false);
      }}>
      <input value={note} onChange={(event) => setNote(event.target.value)} maxLength={600} aria-label={RICH_FRAME.notRight}
        placeholder={RICH_FRAME.notRightPlaceholder}
        style={{ fontFamily: FONT_MONO, fontSize: 11, width: 300, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
      <label style={{ fontFamily: FONT_MONO, fontSize: 11 }}>
        <input type="checkbox" checked={differentKind} onChange={(event) => setDifferentKind(event.target.checked)} /> {RICH_FRAME.differentKind}
      </label>
      <button type="submit" style={linkStyle}>{RICH_FRAME.askBetter}</button>
      <MeaningLabel>{RICH_FRAME.notRightWhere}</MeaningLabel>
    </form>
  );
}

/** A shown Manim figure's body: what it shows, the video, the transcript and the checks. */
export function ManimFigureBody({ figure, notRight }: { figure: FigureViewDto; notRight?: ReactNode }) {
  const [transcript, setTranscript] = useState(false);
  const manim = figure.manim;
  if (!manim || !manim.mediaFileName) return <MeaningLabel>couldn't play this version here</MeaningLabel>;
  return (
    <div data-manim-figure={figure.figureId} style={{ display: "flex", flexDirection: "column", gap: 6, margin: "2px 0 0 15px" }}>
      {figure.demonstrates ? (
        <div style={{ fontSize: 12 }}>
          <MeaningLabel style={{ fontSize: 11 }}>◇ shows:</MeaningLabel> <ModelVoice>{figure.demonstrates}</ModelVoice>
        </div>
      ) : null}
      <AnimationPlayer fileName={manim.mediaFileName} label={manim.title || "animation"} />
      <div style={{ display: "flex", gap: 10, fontFamily: FONT_MONO, fontSize: 11 }}>
        <button type="button" style={linkStyle} aria-expanded={transcript} onClick={() => setTranscript((value) => !value)}>
          {transcript ? RICH_FRAME.hideTranscript : RICH_FRAME.transcript}
        </button>
        <span title={RICH_FRAME.info} aria-label={RICH_FRAME.info} style={{ color: COLOR.textDim }}>ⓘ</span>
        {notRight ?? null}
      </div>
      {transcript ? (
        <div data-manim-transcript="" style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>
          <ModelVoice>{manim.narrationMd || "(no narration)"}</ModelVoice>
        </div>
      ) : null}
      <div data-manim-checks="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
        {manim.checks.length ? <div>{FIGURE_FRAME.checksLead}</div> : null}
        {manim.checks.map((check, index) => <div key={index}>· {manimCheckLine(check)}</div>)}
        <div>· {manim.notCovered[0] ?? RICH_FRAME.notCovered}</div>
      </div>
    </div>
  );
}

/** The fuller version's one line inside a quick figure's frame (spec §6.8). */
export function FullerLine({ fuller, showing, onOpen, onBack, onCancel }: {
  fuller: FigureFullerDto;
  showing: boolean;
  onOpen: () => void;
  onBack: () => void;
  onCancel: (richJobId: string) => void;
}) {
  const [why, setWhy] = useState(false);
  const style = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "2px 0 0 15px", flexWrap: "wrap" as const };
  if (fuller.state === "ready" && fuller.figure) {
    return (
      <div data-fuller-line="ready" style={style}>
        {showing
          ? <button type="button" style={linkStyle} onClick={onBack}>{RICH_FRAME.quick}</button>
          : <><span>{RICH_FRAME.fullerReady}</span><button type="button" style={linkStyle} onClick={onOpen}>{RICH_FRAME.open}</button></>}
      </div>
    );
  }
  if (fuller.state === "pending") {
    return (
      <div data-fuller-line="pending" style={style}>
        <span>{RICH_FRAME.fullerPending}</span>
        {fuller.richJobId ? <button type="button" style={linkStyle} onClick={() => onCancel(fuller.richJobId as string)}>{RICH_FRAME.cancel}</button> : null}
      </div>
    );
  }
  if (fuller.state === "waiting_for_plan") {
    return (
      <div data-fuller-line="waiting" style={style}>
        <span>{RICH_FRAME.fullerWaiting}</span>
        {fuller.richJobId ? <button type="button" style={linkStyle} onClick={() => onCancel(fuller.richJobId as string)}>{RICH_FRAME.cancel}</button> : null}
      </div>
    );
  }
  if (fuller.state === "failed") {
    return (
      <div data-fuller-line="failed" style={style}>
        <span>{RICH_FRAME.fullerFailed}</span>
        <button type="button" style={linkStyle} aria-expanded={why} onClick={() => setWhy((value) => !value)}>{RICH_FRAME.why}</button>
        {why && fuller.reason ? <MeaningLabel style={{ fontSize: 11 }}>{fuller.reason}</MeaningLabel> : null}
      </div>
    );
  }
  return null;
}

/** A rich build with no quick figure: its pending line under the passage, naming the job's phase.
 * Codex review F9: one that ended with no figure (interrupted, or stopped) says so, with code's
 * reason behind "why" and "try again". */
export function RichPendingLine({ line, onCancel, onRetry }: {
  line: FigureRichPendingDto;
  onCancel: (richJobId: string) => void;
  onRetry?: (richJobId: string) => void;
}) {
  const [why, setWhy] = useState(false);
  if (line.state === "failed") {
    return (
      <div data-rich-pending={line.richJobId ?? ""} data-rich-failed="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px", flexWrap: "wrap" }}>
        <span>{RICH_FRAME.richFailed}</span>
        <button type="button" style={linkStyle} aria-expanded={why} onClick={() => setWhy((value) => !value)}>{RICH_FRAME.why}</button>
        {line.richJobId && onRetry ? <button type="button" style={linkStyle} onClick={() => onRetry(line.richJobId as string)}>{RICH_FRAME.tryAgain}</button> : null}
        {why && line.reason ? <MeaningLabel style={{ fontSize: 11 }}>{line.reason}</MeaningLabel> : null}
      </div>
    );
  }
  const text = line.state === "waiting_for_plan" ? RICH_FRAME.richWaiting : (RICH_PHASES[line.phase ?? "writing"] ?? RICH_PHASES.writing);
  return (
    <div data-rich-pending={line.richJobId ?? ""} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px" }}>
      <span>{text} · keep reading</span>
      {line.richJobId ? <button type="button" style={linkStyle} onClick={() => onCancel(line.richJobId as string)}>{RICH_FRAME.cancel}</button> : null}
    </div>
  );
}

/** The standing Manim opt-in, asked once inline after a press (spec §9b.3): allow · not now. */
export function ManimOptInLine({ onAnswer }: { onAnswer: (choice: "allow" | "decline") => void }) {
  return (
    <div data-manim-opt-in="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px", flexWrap: "wrap" }}>
      <span>{RICH_FRAME.optIn}</span>
      <button type="button" style={linkStyle} onClick={() => onAnswer("allow")}>{RICH_FRAME.allow}</button>
      <button type="button" style={linkStyle} onClick={() => onAnswer("decline")}>{RICH_FRAME.notNow}</button>
    </div>
  );
}

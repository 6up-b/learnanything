// Reader workbench RW5a: an explorable figure, inline under its passage (spec §8.1; UX §4.7, Moment 9, W11, S9).
//
// Collapsed to one line once built, its code-owned badge always visible
// (G23; FIGURE_FRAME below); expands in place at the text column's full measure, one at a time.
// Open: what it demonstrates and assumes (AI-written, quoted where the book
// says it), one prediction before the first change (formative; the readout
// before and after; "what changed? (optional)"), sliders with numeric fields,
// the panels, "play" on an animated parameter (the same evaluation as the
// slider; step buttons under reduced motion; nothing moves until pressed,
// D39), the values table (`t`) and "not right?". Nothing here takes focus,
// animates by itself or opens a modal (W12, G54).
import { useEffect, useId, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import type { FigurePredictionDto, FigureViewDto } from "../../../api/dto";
import { COLOR, FONT_MONO } from "../../../components/term";
import { errorMessage } from "../../../errors";
import { logReaderAction } from "../activity";
import { LearnerQuote, MeaningLabel, ModelVoice, SourceVoice } from "../voices";
import { CheckedBadge, CheckedLines, FigureLabelsProvider, FigureSourceInfo, labelElements, LabelText, useFigureLabels } from "./figureLabels";
import { FigurePanel, formatValue } from "./FigurePanels";
import { compileSpec, evaluateFigure, type CompiledFigure, type FigureParameter } from "./figureSpec";

// The code-owned frame (RW5a final round, High 1). A figure's header badge and
// its property checks are written here, from closed values only: the
// verification status and the closed keys of the checks code ran (spec §8.3
// steps 1-2). Model-authored labels and text (series and readout labels, what
// it shows, a failure's reason, an unsupported request's kind) render inside
// the frame and never in its badge slot. RW5c's "matches the book's equation
// (checked)" comes only from an element's closed role (figureLabels.tsx).
export const FIGURE_FRAME = {
  illustration: "AI-built illustration of an interpretation · not checked against the book",
  /** RW5d P1: built with nothing from the learner's books (grounding "none", code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book",
  failed: "couldn't build a reliable version of this",
  unsupported: "can't draw this yet · noted",
  checksLead: "checked by LearnLoop:",
  // RW5c (spec §7.3): drawn only from an element's closed role, beside the book's own left-hand side.
  bookChecked: "matches the book's equation (checked)",
  restIllustration: "the rest is an illustration",
  derivedFrom: "computed by LearnLoop from it",
  limitedToPlot: "limited to the plotted range",
  noTerms: "no terms in this range",
  aiElement: "AI-built · not checked against the book",
  aiDefined: "AI-defined",
  aiBuilt: "AI-built",
} as const;

// RW5c (spec §7.3): why nothing on a figure carries the claim, one phrase per closed reason key.
// An unknown key is dropped, as PROPERTY_CHECK_COPY drops one.
const UNREADABLE = "LearnLoop couldn't read the book's equation exactly";
export const SOURCE_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze({
  phi: `${UNREADABLE}: it uses Φ`,
  binom: `${UNREADABLE}: it uses a binomial coefficient`,
  factorial: `${UNREADABLE}: it uses a factorial`,
  gamma: `${UNREADABLE}: it uses Γ`,
  integral: `${UNREADABLE}: it uses an integral`,
  sum: `${UNREADABLE}: it uses a sum`,
  product: `${UNREADABLE}: it uses a product`,
  limit: `${UNREADABLE}: it uses a limit`,
  derivative: `${UNREADABLE}: it uses a derivative`,
  matrix: `${UNREADABLE}: it uses a matrix`,
  indicator: `${UNREADABLE}: it uses indicator notation`,
  set: `${UNREADABLE}: it uses set notation`,
  log_base: `${UNREADABLE}: log's base differs between books`,
  text: `${UNREADABLE}: it has words in it`,
  unicode_math: `${UNREADABLE}: the page's math isn't in LaTeX here`,
  not_equation: "the passage has no equation LearnLoop can read",
  relation: `${UNREADABLE}: it is not an equality`,
  multiple_relations: `${UNREADABLE}: it has more than one equals sign`,
  application: `${UNREADABLE}: a name is applied like a function`,
  ambiguous_e: `${UNREADABLE}: e may not be Euler's number there`,
  ambiguous_slash: `${UNREADABLE}: a slash could group two ways`,
  name_collision: `${UNREADABLE}: two symbols share one name`,
  reserved_name: `${UNREADABLE}: a symbol's name is taken`,
  nth_root: `${UNREADABLE}: it uses an n-th root`,
  subscript: `${UNREADABLE}: it uses a long subscript`,
  function_arg: `${UNREADABLE}: a function's argument is unclear`,
  function_power: `${UNREADABLE}: it uses a function's power`,
  cases_condition: `${UNREADABLE}: a case's condition is out of reach`,
  cases_cover: `${UNREADABLE}: its cases don't cover the line`,
  inexact_literal: "a number isn't exact in floating point, so nothing can be proved about it",
  too_long: `${UNREADABLE}: it is too long`,
  syntax: `${UNREADABLE}: its LaTeX is out of reach`,
  macro_definition: `${UNREADABLE}: it defines its own macro`,
  not_rendered: `${UNREADABLE}: the page can't render its LaTeX`,
  engine_unavailable: "reading the book's equations needs a part this install doesn't have",
  unsupported_command: `${UNREADABLE}: it uses a command outside the table`,
  unsupported_environment: `${UNREADABLE}: it uses a layout outside the table`,
  unsupported_function: `${UNREADABLE}: it uses a function outside the table`,
  block_health: "the page this equation is on may be misread",
  block_withheld: "that passage is held out",
  no_book_source: "this figure isn't from your books",
  no_readable_candidate: "the figure's passages have no equation LearnLoop can read",
  not_bare: "no curve draws a definition as it stands",
  names: "the figure's names aren't the book's",
  inexact_condition: "a branch's condition isn't exact",
  inexact_construct: "the figure uses something exact math can't reproduce",
  no_proof: "LearnLoop could neither prove nor disprove a match",
  domain: "LearnLoop couldn't prove the two are defined at the same points",
  parametric_breakpoint: "the branches move with a slider, which this version doesn't decide",
  control_accepted: "the check's own controls failed, so it decided nothing",
  control_inconclusive: "the check's own controls failed, so it decided nothing",
  display_disagrees: "what's shown doesn't match the equation to the digits shown",
  sandbox_unavailable: "checks need the sandbox, which this computer doesn't have",
  sandbox_failed: "the check couldn't run",
  timeout: "the check ran out of time",
  quote_across_blocks: "the quoted passage runs across two blocks",
});

/** The reasons' words, for the closed keys only (anything else is dropped). */
export function sourceCheckReasons(keys: readonly string[] | null | undefined): string[] {
  return [...new Set((keys ?? []).filter((key) => Object.prototype.hasOwnProperty.call(SOURCE_CHECK_COPY, key))
    .map((key) => SOURCE_CHECK_COPY[key]))];
}

export const PROPERTY_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze({
  values_finite: "every value finite on the parameter grid",
  integrates_to_one: "a declared density integrates to 1",
  sums_to_one: "a declared PMF sums to 1",
  nonnegative: "a declared quantity is never negative",
  bounded: "a declared quantity stays bounded",
  finite: "a declared quantity stays finite",
  monotone_nondecreasing: "a declared curve never decreases",
  shaded_areas: "shaded areas match an independent integration",
});

/** The badge slot's text: from the status alone (a stored "verified" is shown as the illustration it is). */
export function frameBadge(verification: FigureViewDto["verification"], grounding?: FigureViewDto["grounding"]): string {
  if (verification === "failed") return FIGURE_FRAME.failed;
  if (verification === "unsupported") return FIGURE_FRAME.unsupported;
  // RW5d P1: the grounding is a closed, code-written value; never the model's words.
  return grounding === "none" ? FIGURE_FRAME.notFromBooks : FIGURE_FRAME.illustration;
}

/** RW5d P1: the figure's goal on its collapsed line, in its author's voice
 *  (the learner's words quoted; a tutor's goal marked AI-written). Outside the
 *  badge slot. Nothing for a figure with no goal. */
export function FigureGoal({ figure }: { figure: FigureViewDto }) {
  const goal = figure.goalText?.trim();
  if (!goal) return null;
  if (figure.goalAuthor === "tutor" || figure.goalAuthor === "teacher") {
    // RW5d P4b: a lesson figure's goal is the teacher's, AI-written as the tutor's is.
    return (
      <span data-figure-goal={figure.goalAuthor}>
        <span style={{ color: COLOR.purpleText }}>◇ “{goal}”</span> <MeaningLabel style={{ fontSize: 10 }}>(AI-written)</MeaningLabel>
      </span>
    );
  }
  return <span data-figure-goal="learner">› <LearnerQuote>{goal}</LearnerQuote></span>;
}

/** RW5d P1: the passages from the learner's books a figure was built from (grounding "retrieved"). */
export function FigurePassages({ figure }: { figure: FigureViewDto }) {
  if (figure.grounding !== "retrieved" || !figure.passages?.length) return null;
  return (
    <span data-figure-passages="">
      <MeaningLabel style={{ fontSize: 10 }}>{FIGURE_COPY.fromYourBooks}</MeaningLabel>{" "}
      {figure.passages.map((passage) => (
        <span key={`${passage.extractionId}:${passage.spanId}`} data-figure-passage={`${passage.extractionId}:${passage.spanId}`}
          style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim, marginRight: 6 }}>
          § {[passage.sourceTitle, passage.section].filter(Boolean).join(" ") || passage.spanId}
        </span>
      ))}
    </span>
  );
}

/** The property checks' words, for the closed keys only (anything else is dropped). */
export function frameChecks(keys: readonly string[] | null | undefined): string[] {
  return (keys ?? []).filter((key) => Object.prototype.hasOwnProperty.call(PROPERTY_CHECK_COPY, key))
    .map((key) => PROPERTY_CHECK_COPY[key]);
}

import { figurePlacementKey, type FigureHome, type FigurePending, type FiguresCtl, type FollowedFigure } from "./useFigures";
import { checksStand, SketchFigure, sketchBadge, SKETCH_FRAME } from "./sketch/SketchFigure";
import { useChecksWithdrawn } from "./sketch/checksWithdrawn";
import { parseProgram } from "./sketch/sketchScene";
import { FullerLine, ManimFigureBody, ManimNotRight, ManimOptInLine, manimBadge, RICH_FRAME, RichPendingLine } from "./RichFigure";

export const FIGURE_COPY = {
  collapsed: "interactive version",
  pending: "◐ building an interactive version — keep reading",
  tryAgain: "try again",
  /** RW5c (§6.6). */
  rebuild: "rebuild",
  cancel: "cancel",
  close: "✕ close",
  predictionLead: "Before you move anything:",
  answer: "↵ answer",
  skip: "skip",
  whatChanged: "what changed? (optional)",
  whatChangedWhere: "Kept with your prediction as a formative note; a missed one may name a belief worth a look. Never a grade.",
  save: "keep",
  notRight: "not right?",
  notRightPlaceholder: "what should change? (optional)",
  notRightWhere: "Goes to the figure author with this version; the new version is checked like this one and this one is kept.",
  askBetter: "ask for a better version",
  table: "t values table",
  play: "▶ play",
  stop: "■ stop",
  stepBack: "◂ step",
  stepForward: "step ▸",
  shows: "what it shows",
  assumes: "what it assumes",
  unreadable: "couldn't draw this version here",
  /** RW5d P1. */
  fromYourBooks: "from your books:",
  /** RW5d P4a: a figure followed here from another book names its home. */
  fromYourReading: "from your reading of",
} as const;

const PLAY_STEPS = 40;
const PLAY_MS = 150;
const REDUCED_STEPS = 20;

export const linkStyle: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
};

export function prefersReducedMotion(): boolean {
  try {
    return typeof window !== "undefined" && typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

function defaultsOf(compiled: CompiledFigure): Record<string, number> {
  return Object.fromEntries(compiled.parameters.map((parameter) => [parameter.name, Number(parameter.default)]));
}

function clamp(parameter: FigureParameter, value: number): number {
  if (!Number.isFinite(value)) return Number(parameter.default);
  return Math.min(parameter.max, Math.max(parameter.min, value));
}

/** A build in flight or one that could not run, as a dim line under the passage. */
export function FigurePendingLine({ pending }: { pending: FigurePending }) {
  if (pending.state === "pending") {
    return (
      <div data-figure-pending="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px" }}>
        <span>{FIGURE_COPY.pending}</span>
        <button type="button" style={linkStyle} onClick={pending.cancel}>{FIGURE_COPY.cancel}</button>
      </div>
    );
  }
  return (
    <div data-figure-failed="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px", flexWrap: "wrap" }}>
      <MeaningLabel style={{ fontSize: 11 }}>{pending.message ?? "couldn't build an interactive version"}</MeaningLabel>
      <button type="button" style={linkStyle} onClick={pending.retry}>{FIGURE_COPY.tryAgain}</button>
      <button type="button" style={linkStyle} onClick={pending.cancel}>✕</button>
    </div>
  );
}

export function PredictionBlock({
  figure,
  prediction,
  ctl,
  onApplied,
  onSkip,
}: {
  figure: FigureViewDto;
  prediction: FigurePredictionDto;
  ctl: FiguresCtl;
  onApplied: (change: Record<string, number>) => void;
  onSkip: () => void;
}) {
  const [choice, setChoice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Each mounted control is its own radio group (Codex re-review F10): two
  // placements of one figure never share a native group, so what shows
  // selected is what is sent. The answer itself is the figure's.
  const group = `prediction-${figure.figureId}-${prediction.index}-${useId()}`;
  const submit = async () => {
    if (!choice || busy) return;
    setBusy(true);
    setError(null);
    try {
      await ctl.predict(figure, prediction.index, choice);
      onApplied({});
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  };
  return (
    <fieldset data-figure-prediction={prediction.index} style={{ border: 0, padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 4 }}>
      <legend style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, padding: 0 }}>
        {FIGURE_COPY.predictionLead} {prediction.prompt}
      </legend>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 11 }}>
        {prediction.choices.map((option) => (
          <label key={option.value} style={{ display: "flex", gap: 4, alignItems: "center", color: COLOR.text }}>
            <input type="radio" name={group} value={option.value}
              checked={choice === option.value} onChange={() => setChoice(option.value)}
              onKeyDown={(event) => { if (event.key === "Enter") void submit(); }} />
            {option.label}
          </label>
        ))}
        <button type="button" style={linkStyle} disabled={!choice || busy} onClick={() => void submit()}>{FIGURE_COPY.answer}</button>
        <button type="button" style={linkStyle} onClick={onSkip}>{FIGURE_COPY.skip}</button>
      </div>
      <MeaningLabel>A prediction is for you: it is never graded.</MeaningLabel>
      {error ? <MeaningLabel style={{ color: COLOR.red }}>{error}</MeaningLabel> : null}
    </fieldset>
  );
}

export function PredictionResult({ figure, prediction, ctl, format }: { figure: FigureViewDto; prediction: FigurePredictionDto; ctl: FiguresCtl; format: "number" | "percent" }) {
  const answered = prediction.answered;
  const [text, setText] = useState("");
  const [saved, setSaved] = useState(false);
  if (!answered) return null;
  const choiceLabel = (value: string | null) => prediction.choices.find((option) => option.value === value)?.label ?? value ?? "";
  return (
    <div data-figure-prediction-result="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
        {prediction.kind === "direction" ? (
          <span data-figure-before-after="">{formatValue(answered.before, format)} → {formatValue(answered.after, format)}</span>
        ) : (
          <span data-figure-before-after="">{formatValue(answered.before, format)}</span>
        )}
        <span style={{ color: COLOR.textDim }}>
          {" · "}you said {choiceLabel(answered.learnerAnswer)}; the figure shows {choiceLabel(answered.answer)}
          {answered.matched ? " (as you predicted)" : " (not what you predicted: worth a second look)"}
        </span>
      </div>
      {ctl.contract?.predictions ? (
        answered.explanationText || saved ? (
          <MeaningLabel>› {answered.explanationText ?? text}</MeaningLabel>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!text.trim()) return;
              void ctl.explain(figure, answered.predictionId, text).then(() => setSaved(true)).catch(() => undefined);
            }}
            style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}
          >
            <label style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
              {FIGURE_COPY.whatChanged} ›{" "}
              <input value={text} onChange={(event) => setText(event.target.value)} maxLength={600}
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 320, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
            </label>
            <button type="submit" style={linkStyle} disabled={!text.trim()}>{FIGURE_COPY.save}</button>
            <MeaningLabel>{FIGURE_COPY.whatChangedWhere}</MeaningLabel>
          </form>
        )
      ) : null}
    </div>
  );
}

function ParameterControl({
  parameter,
  value,
  disabled,
  playing,
  reduced,
  onChange,
  onPlay,
}: {
  parameter: FigureParameter;
  value: number;
  disabled: boolean;
  playing: boolean;
  reduced: boolean;
  onChange: (value: number) => void;
  onPlay: () => void;
}) {
  const step = (parameter.max - parameter.min) / REDUCED_STEPS;
  const labels = useFigureLabels();
  const spoken = labels ? labels.plain(parameter.label) : parameter.label;
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
      <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
        <LabelText id={parameter.label} />
        <input type="range" min={parameter.min} max={parameter.max} step={parameter.step} value={value} disabled={disabled}
          aria-label={spoken} onChange={(event) => onChange(Number(event.target.value))} />
      </label>
      <input type="number" min={parameter.min} max={parameter.max} step={parameter.step} value={Number(value.toPrecision(6))}
        disabled={disabled} aria-label={`${spoken} value`} onChange={(event) => onChange(Number(event.target.value))}
        style={{ width: 70, fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
      {parameter.animate ? (
        reduced ? (
          <>
            <button type="button" style={linkStyle} disabled={disabled} onClick={() => onChange(value - step)}>{FIGURE_COPY.stepBack}</button>
            <button type="button" style={linkStyle} disabled={disabled} onClick={() => onChange(value + step)}>{FIGURE_COPY.stepForward}</button>
          </>
        ) : (
          <button type="button" style={linkStyle} disabled={disabled} onClick={onPlay} data-figure-play={parameter.name}>
            {playing ? FIGURE_COPY.stop : FIGURE_COPY.play}
          </button>
        )
      ) : null}
    </span>
  );
}

function FigureBody({ figure, ctl, compiled }: { figure: FigureViewDto; ctl: FiguresCtl; compiled: CompiledFigure }) {
  const [params, setParams] = useState<Record<string, number>>(() => defaultsOf(compiled));
  const [showTable, setShowTable] = useState(false);
  const [skipped, setSkipped] = useState(false);
  const [playing, setPlaying] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const reduced = useMemo(prefersReducedMotion, []);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  // The one evaluation: a slider, a typed value and play all set params.
  const data = useMemo(() => evaluateFigure(compiled, params), [compiled, params]);
  // One prediction per figure (spec §8.4): the first, before the first change.
  const answeredPrediction = figure.predictions.find((prediction) => prediction.answered !== null) ?? null;
  const openPrediction = ctl.contract?.predictions && !skipped && !answeredPrediction ? figure.predictions[0] ?? null : null;
  const readoutFormat = (data.panels.find((panel) => panel.kind === "readout") as { format?: "number" | "percent" } | undefined)?.format ?? "number";

  useEffect(() => () => {
    if (timer.current) clearInterval(timer.current);
  }, []);

  const setParam = (name: string, raw: number) => {
    const parameter = compiled.parameters.find((item) => item.name === name);
    if (!parameter) return;
    setParams((current) => ({ ...current, [name]: clamp(parameter, raw) }));
  };

  const stopPlay = () => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    setPlaying(null);
  };

  const play = (parameter: FigureParameter) => {
    if (playing === parameter.name) {
      stopPlay();
      return;
    }
    stopPlay();
    logReaderAction("figure_animated", { figure_id: figure.figureId, extraction_id: figure.extractionId, parameter: parameter.name });
    let index = 0;
    setPlaying(parameter.name);
    timer.current = setInterval(() => {
      const value = parameter.min + ((parameter.max - parameter.min) * index) / PLAY_STEPS;
      setParam(parameter.name, value);
      index += 1;
      if (index > PLAY_STEPS) stopPlay();
    }, PLAY_MS);
  };

  const applyPrediction = (prediction: FigurePredictionDto) => {
    const change = compiled.spec.predictions?.[prediction.index]?.change ?? {};
    setParams((current) => {
      const next = { ...current };
      for (const [name, value] of Object.entries(change)) {
        const parameter = compiled.parameters.find((item) => item.name === name);
        if (parameter) next[name] = clamp(parameter, Number(value));
      }
      return next;
    });
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) && (target as HTMLInputElement).type !== "range") return;
    if (event.key === "t" && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      setShowTable((value) => !value);
    }
  };

  const assumptions = figure.assumptions ?? [];
  const controlsLocked = openPrediction !== null;
  return (
    <div data-figure-body="" onKeyDown={onKeyDown} style={{ display: "flex", flexDirection: "column", gap: 8, border: `1px solid ${COLOR.border}`, padding: "8px 10px", background: COLOR.bgElev }}>
      {figure.demonstrates ? (
        <ModelVoice first note={FIGURE_COPY.shows}>{figure.demonstrates}</ModelVoice>
      ) : null}
      {assumptions.length ? (
        <div data-figure-assumptions="" style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <MeaningLabel>{FIGURE_COPY.assumes} · AI-written{assumptions.some((item) => item.quote) ? ", quoting the book where it says so" : ""}</MeaningLabel>
          {assumptions.map((assumption, index) => (
            <div key={index} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}><span aria-hidden="true">◇ </span>{assumption.text}</span>
              {assumption.quote ? <SourceVoice><span>{assumption.quote}</span></SourceVoice> : null}
            </div>
          ))}
        </div>
      ) : null}
      {openPrediction ? (
        <PredictionBlock figure={figure} prediction={openPrediction} ctl={ctl}
          onApplied={() => applyPrediction(openPrediction)} onSkip={() => setSkipped(true)} />
      ) : null}
      {answeredPrediction && !openPrediction ? (
        <PredictionResult figure={figure} prediction={answeredPrediction} ctl={ctl} format={readoutFormat} />
      ) : null}
      <FigureSourceInfo figure={figure} ctl={ctl} />
      <FigureLabelsProvider figure={figure} compiled={compiled} params={params}>
        {data.panels.map((panel, index) => (
          <FigurePanel key={index} data={panel} showTable={showTable} model={compiled.spec.panels[index]}
            label={compiled.spec.panels[index]?.kind === "linear_map_2d" ? (compiled.spec.panels[index] as { label?: string }).label : undefined} />
        ))}
        {compiled.parameters.length ? (
          <div data-figure-controls="" style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
            {compiled.parameters.map((parameter) => (
              <ParameterControl key={parameter.name} parameter={parameter} value={params[parameter.name] ?? parameter.default}
                disabled={controlsLocked} playing={playing === parameter.name} reduced={reduced}
                onChange={(value) => setParam(parameter.name, value)} onPlay={() => play(parameter)} />
            ))}
          </div>
        ) : null}
        {compiled.spec.annotations?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {compiled.spec.annotations.map((annotation, index) => (
              <MeaningLabel key={index} style={{ fontSize: 11 }}>
                {/* The model's line stays in the model's voice (§8.2): its target is code's name for the element, with no claim. */}
                ◇ {labelElements(figure).length ? (annotation.target ? <><LabelText id={annotation.target} bare />: </> : null) : <>{annotation.target}: </>}{annotation.text}
              </MeaningLabel>
            ))}
          </div>
        ) : null}
      </FigureLabelsProvider>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline" }}>
        <button type="button" style={linkStyle} aria-pressed={showTable} onClick={() => setShowTable((value) => !value)}>{FIGURE_COPY.table}</button>
        {ctl.contract?.revisions ? (
          noteOpen ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                ctl.revise(figure, note);
                setNoteOpen(false);
                setNote("");
              }}
              style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}
            >
              <input value={note} onChange={(event) => setNote(event.target.value)} maxLength={600} aria-label={FIGURE_COPY.notRight}
                placeholder={FIGURE_COPY.notRightPlaceholder}
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 300, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
              <button type="submit" style={linkStyle}>{FIGURE_COPY.askBetter}</button>
              <MeaningLabel>{FIGURE_COPY.notRightWhere}</MeaningLabel>
            </form>
          ) : (
            <button type="button" style={linkStyle} onClick={() => setNoteOpen(true)}>{FIGURE_COPY.notRight}</button>
          )
        ) : null}
        {figure.versions > 1 ? <MeaningLabel>version {figure.versions}</MeaningLabel> : null}
      </div>
    </div>
  );
}

/** One figure under its passage: the collapsed line and, when expanded, the figure. */
/** RW5d P4a: the line naming a followed figure's home ("from your reading of Lay § 5.1 …"). */
export function figureHomeLine(home: FigureHome): string {
  return `${FIGURE_COPY.fromYourReading} ${home.sourceTitle} § ${home.sectionTitle}`;
}

export function FigureInline({ figure, ctl, home = null }: { figure: FigureViewDto; ctl: FiguresCtl; home?: FigureHome | null }) {
  const shown = figure.verification === "verified" || figure.verification === "illustrative";
  const expanded = shown && ctl.expandedKey === figurePlacementKey(figure);
  // RW5d P2: a sketch's specJson is its SketchProgramV1, drawn by SketchFigure.
  const isSketch = figure.tier === "sketch";
  // RW5d P2b: a Manim figure plays its video (no spec to compile); a quick
  // figure may carry its fuller version, swapped in within the same frame.
  const isManim = figure.tier === "manim";
  const [showingFuller, setShowingFuller] = useState(false);
  const fuller = figure.fuller ?? null;
  const fullerReady = fuller?.state === "ready" && fuller.figure ? fuller.figure : null;
  const compiled = useMemo(() => {
    if (!shown || !figure.specJson || isSketch || isManim) return null;
    try {
      return compileSpec(figure.specJson);
    } catch {
      return null;
    }
  }, [shown, figure.specJson, isSketch, isManim]);
  const program = useMemo(() => (shown && isSketch ? parseProgram(figure.specJson) : null), [shown, isSketch, figure.specJson]);
  // Fix round 4: a sketch whose page run disagreed with the verified run has its checks withdrawn here too.
  const withdrawn = useChecksWithdrawn(figure.figureId);
  if (!shown) {
    return (
      <div data-figure={figure.figureId} data-figure-verification={figure.verification}
        style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px", flexWrap: "wrap" }}>
        <FigureGoal figure={figure} />
        <span data-figure-badge=""><MeaningLabel style={{ fontSize: 11 }}>{figure.label === RICH_FRAME.cantShow ? RICH_FRAME.cantShow : isManim ? manimBadge(figure) : frameBadge(figure.verification)}</MeaningLabel></span>
        {figure.verification === "unsupported" && figure.unsupportedKind && figure.label !== RICH_FRAME.cantShow ? (
          <span data-figure-detail="">needs {figure.unsupportedKind}</span>
        ) : null}
        {figure.verification === "failed" && figure.reason ? <span data-figure-detail="">({figure.reason})</span> : null}
        {figure.sourceCheck?.status === "differs" ? (
          // RW5c (§6.6): asking again would reuse this figure; a rebuild is a new version, told the difference.
          figure.sourceCheck.rebuild && ctl.rebuild ? (
            <button type="button" style={linkStyle} data-figure-rebuild="" onClick={() => ctl.rebuild?.(figure)}>{FIGURE_COPY.rebuild}</button>
          ) : null
        ) : figure.verification === "failed" ? (
          <button type="button" style={linkStyle} onClick={() => ctl.request(figure.goalText && figure.origin !== "tutor"
            // RW5d: a show-me figure asks again with its words (a tutor's goal is pressed from its answer).
            ? { spanIds: figure.spanIds, region: figure.region, goalText: figure.goalText, origin: "show_me",
                readingAt: figure.anchorSpanId ? { spanId: figure.anchorSpanId } : null }
            : { spanIds: figure.spanIds, region: figure.region })}>
            {FIGURE_COPY.tryAgain}
          </button>
        ) : null}
      </div>
    );
  }
  const checks = isManim
    ? (figure.manim?.checks.length ? [`${figure.manim.checks.length} check${figure.manim.checks.length === 1 ? "" : "s"}, listed inside`] : [])
    : isSketch
    ? (figure.sketch && checksStand(figure.sketch, withdrawn) ? [`${figure.sketch.checks.length} check${figure.sketch.checks.length === 1 ? "" : "s"}, listed inside`] : [])
    : frameChecks(figure.propertyChecks);
  const toggle = () => {
    if (!expanded) logReaderAction("figure_opened", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    // RW5c (§10.4): no check at the current certification version: code rechecks it, and it upgrades in place.
    if (!expanded && figure.sourceCheck?.recheckDue) ctl.recheck?.(figure);
    ctl.setExpanded(expanded ? null : figure);
  };
  const openFuller = () => {
    if (!fullerReady) return;
    logReaderAction("fuller_version_opened", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    setShowingFuller(true);
  };
  const openQuick = () => {
    logReaderAction("quick_version_opened", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    setShowingFuller(false);
  };
  // RW5d P2b (spec §8.5, Codex review F11): "not right?" on the animation shown.
  const notRightOn = (target: FigureViewDto) => (ctl.contract?.revisions
    ? <ManimNotRight onRevise={(note, differentKind) => ctl.revise(target, note, differentKind)} /> : null);
  const body = showingFuller && fullerReady
    ? <ManimFigureBody figure={fullerReady} notRight={notRightOn(fullerReady)} />
    : isManim
    ? <ManimFigureBody figure={figure} notRight={notRightOn(figure)} />
    : isSketch
    ? (program ? <SketchFigure figure={figure} ctl={ctl} program={program} /> : <MeaningLabel>{FIGURE_COPY.unreadable}</MeaningLabel>)
    : compiled ? <FigureBody figure={figure} ctl={ctl} compiled={compiled} /> : <MeaningLabel>{FIGURE_COPY.unreadable}</MeaningLabel>;
  return (
    <div data-figure={figure.figureId} data-figure-verification={figure.verification} style={{ margin: "4px 0 8px 0", display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
        <button type="button" aria-expanded={expanded} onClick={toggle}
          style={{ ...linkStyle, fontSize: 11, color: COLOR.text, textDecoration: "none" }}>
          <span aria-hidden="true">{expanded ? "▾" : "▸"}</span> {isManim ? RICH_FRAME.collapsed : FIGURE_COPY.collapsed} ·{" "}
          {figure.goalText ? <><FigureGoal figure={figure} /> ·{" "}</> : null}
          <span data-figure-badge="">{isManim ? manimBadge(figure) : isSketch ? sketchBadge(figure, withdrawn)
            : labelElements(figure).length ? <CheckedBadge figure={figure} /> : frameBadge(figure.verification, figure.grounding)}</span>
          {!expanded && fullerReady ? <span data-fuller-collapsed=""> · {RICH_FRAME.collapsedReady}</span> : null}
        </button>
        {home ? (
          // RW5d P4a: a figure from another book says so, always (collapsed or open).
          <span data-figure-home=""><MeaningLabel style={{ fontSize: 11 }}>{figureHomeLine(home)}</MeaningLabel></span>
        ) : null}
        <FigurePassages figure={figure} />
        {checks.length ? (
          <span data-figure-checks=""><MeaningLabel style={{ fontSize: 11 }}>{isSketch ? SKETCH_FRAME.checksLead : FIGURE_FRAME.checksLead} {checks.join("; ")}</MeaningLabel></span>
        ) : null}
        {labelElements(figure).length ? <span data-figure-source-checks=""><MeaningLabel style={{ fontSize: 11 }}>{FIGURE_FRAME.checksLead} <CheckedLines figure={figure} /></MeaningLabel></span> : null}
        {expanded ? <button type="button" style={linkStyle} onClick={() => ctl.setExpanded(null)}>{FIGURE_COPY.close}</button> : null}
      </div>
      {expanded ? body : null}
      {expanded && fuller ? (
        <FullerLine fuller={fuller} showing={showingFuller} onOpen={openFuller} onBack={openQuick}
          onCancel={(richJobId) => ctl.cancelRich(richJobId)} />
      ) : null}
    </div>
  );
}

/** Everything figure-related under one passage (figures and their pending lines). */
export function FiguresUnder({ ctl, spanId }: { ctl: FiguresCtl; spanId: string | null | undefined }) {
  if (!ctl.enabled || !spanId) return null;
  const { figures, pending, richPending, followed } = ctl.under(spanId);
  const askOptIn = ctl.optInSpanId === spanId && ctl.manimOptIn === "ask";
  if (!figures.length && !pending.length && !richPending.length && !followed.length && !askOptIn) return null;
  return (
    <div data-figures-under={spanId}>
      {pending.map((item) => <FigurePendingLine key={item.key} pending={item} />)}
      {askOptIn ? <ManimOptInLine onAnswer={(choice) => ctl.answerManimOptIn(choice)} /> : null}
      {richPending.map((line) => <RichPendingLine key={line.richJobId ?? line.requestId ?? ""} line={line} onCancel={(id) => ctl.cancelRich(id)} onRetry={(id) => ctl.retryRich(id)} />)}
      {figures.map((figure) => <FigureInline key={figure.figureId} figure={figure} ctl={ctl} />)}
      {followed.map((entry) => <FollowedFigureInline key={`followed:${entry.figure.figureId}`} entry={entry} ctl={ctl} />)}
    </div>
  );
}

/** RW5d P4a: a figure followed here from another book: shown as its own book shows it,
 *  its home named, with no "not right?" (a new version belongs to its own book). */
function FollowedFigureInline({ entry, ctl }: { entry: FollowedFigure; ctl: FiguresCtl }) {
  const followCtl = useMemo<FiguresCtl>(
    () => ({ ...ctl, contract: ctl.contract ? { ...ctl.contract, revisions: false } : null }), [ctl]);
  return <FigureInline figure={entry.figure} ctl={followCtl} home={entry.home} />;
}

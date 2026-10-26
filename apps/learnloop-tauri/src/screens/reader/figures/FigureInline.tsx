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
import { useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import type { FigurePredictionDto, FigureViewDto } from "../../../api/dto";
import { COLOR, FONT_MONO } from "../../../components/term";
import { errorMessage } from "../../../errors";
import { logReaderAction } from "../activity";
import { LearnerQuote, MeaningLabel, ModelVoice, SourceVoice } from "../voices";
import { FigurePanel, formatValue } from "./FigurePanels";
import { compileSpec, evaluateFigure, type CompiledFigure, type FigureParameter } from "./figureSpec";

// The code-owned frame (RW5a final round, High 1). A figure's header badge and
// its property checks are written here, from closed values only: the
// verification status and the closed keys of the checks code ran (spec §8.3
// steps 1-2). Model-authored labels and text (series and readout labels, what
// it shows, a failure's reason, an unsupported request's kind) render inside
// the frame and never in its badge slot. RW5a makes no "matches the book"
// claim; that label is RW5c's.
export const FIGURE_FRAME = {
  illustration: "AI-built illustration of an interpretation · not checked against the book",
  /** RW5d P1: built with nothing from the learner's books (grounding "none", code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book",
  failed: "couldn't build a reliable version of this",
  unsupported: "can't draw this yet · noted",
  checksLead: "checked by LearnLoop:",
} as const;

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
  if (figure.goalAuthor === "tutor") {
    return (
      <span data-figure-goal="tutor">
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

import type { FigurePending, FiguresCtl } from "./useFigures";

export const FIGURE_COPY = {
  collapsed: "interactive version",
  pending: "◐ building an interactive version — keep reading",
  tryAgain: "try again",
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
} as const;

const PLAY_STEPS = 40;
const PLAY_MS = 150;
const REDUCED_STEPS = 20;

const linkStyle: CSSProperties = {
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

function prefersReducedMotion(): boolean {
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

function PredictionBlock({
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
            <input type="radio" name={`prediction-${figure.figureId}-${prediction.index}`} value={option.value}
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

function PredictionResult({ figure, prediction, ctl, format }: { figure: FigureViewDto; prediction: FigurePredictionDto; ctl: FiguresCtl; format: "number" | "percent" }) {
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
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
      <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
        {parameter.label}
        <input type="range" min={parameter.min} max={parameter.max} step={parameter.step} value={value} disabled={disabled}
          aria-label={parameter.label} onChange={(event) => onChange(Number(event.target.value))} />
      </label>
      <input type="number" min={parameter.min} max={parameter.max} step={parameter.step} value={Number(value.toPrecision(6))}
        disabled={disabled} aria-label={`${parameter.label} value`} onChange={(event) => onChange(Number(event.target.value))}
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
            <MeaningLabel key={index} style={{ fontSize: 11 }}>◇ {annotation.target}: {annotation.text}</MeaningLabel>
          ))}
        </div>
      ) : null}
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
export function FigureInline({ figure, ctl }: { figure: FigureViewDto; ctl: FiguresCtl }) {
  const shown = figure.verification === "verified" || figure.verification === "illustrative";
  const expanded = shown && ctl.expandedId === figure.figureId;
  const compiled = useMemo(() => {
    if (!shown || !figure.specJson) return null;
    try {
      return compileSpec(figure.specJson);
    } catch {
      return null;
    }
  }, [shown, figure.specJson]);
  if (!shown) {
    return (
      <div data-figure={figure.figureId} data-figure-verification={figure.verification}
        style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 10, margin: "4px 0 4px 15px", flexWrap: "wrap" }}>
        <FigureGoal figure={figure} />
        <span data-figure-badge=""><MeaningLabel style={{ fontSize: 11 }}>{frameBadge(figure.verification)}</MeaningLabel></span>
        {figure.verification === "unsupported" && figure.unsupportedKind ? (
          <span data-figure-detail="">needs {figure.unsupportedKind}</span>
        ) : null}
        {figure.verification === "failed" && figure.reason ? <span data-figure-detail="">({figure.reason})</span> : null}
        {figure.verification === "failed" ? (
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
  const checks = frameChecks(figure.propertyChecks);
  const toggle = () => {
    if (!expanded) logReaderAction("figure_opened", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    ctl.setExpanded(expanded ? null : figure.figureId);
  };
  return (
    <div data-figure={figure.figureId} data-figure-verification={figure.verification} style={{ margin: "4px 0 8px 0", display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
        <button type="button" aria-expanded={expanded} onClick={toggle}
          style={{ ...linkStyle, fontSize: 11, color: COLOR.text, textDecoration: "none" }}>
          <span aria-hidden="true">{expanded ? "▾" : "▸"}</span> {FIGURE_COPY.collapsed} ·{" "}
          {figure.goalText ? <><FigureGoal figure={figure} /> ·{" "}</> : null}
          <span data-figure-badge="">{frameBadge(figure.verification, figure.grounding)}</span>
        </button>
        <FigurePassages figure={figure} />
        {checks.length ? (
          <span data-figure-checks=""><MeaningLabel style={{ fontSize: 11 }}>{FIGURE_FRAME.checksLead} {checks.join("; ")}</MeaningLabel></span>
        ) : null}
        {expanded ? <button type="button" style={linkStyle} onClick={() => ctl.setExpanded(null)}>{FIGURE_COPY.close}</button> : null}
      </div>
      {expanded ? (
        compiled ? <FigureBody figure={figure} ctl={ctl} compiled={compiled} /> : <MeaningLabel>{FIGURE_COPY.unreadable}</MeaningLabel>
      ) : null}
    </div>
  );
}

/** Everything figure-related under one passage (figures and their pending lines). */
export function FiguresUnder({ ctl, spanId }: { ctl: FiguresCtl; spanId: string | null | undefined }) {
  if (!ctl.enabled || !spanId) return null;
  const { figures, pending } = ctl.under(spanId);
  if (!figures.length && !pending.length) return null;
  return (
    <div data-figures-under={spanId}>
      {pending.map((item) => <FigurePendingLine key={item.key} pending={item} />)}
      {figures.map((figure) => <FigureInline key={figure.figureId} figure={figure} ctl={ctl} />)}
    </div>
  );
}

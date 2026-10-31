// Reader RW5d P2: a sketch, open under its passage (spec_reader_show_me_figures_v1 §6.6, §9).
//
// The program runs in its sealed engine (a Web Worker in the app, through
// SketchRunnerContext); every result is validated (sketchScene.ts) before
// SketchSceneView draws it. The host owns every interaction: sliders and
// numeric fields from the declared parameters, draggable handles bound to
// them, "play" driving the program's clock (step buttons under reduced
// motion; nothing moves until pressed), "new sample" for a seeded program,
// and the values table (`t`). Changing a parameter or the seed restarts the
// run, so what is drawn is always "init, then n steps", the shape that was
// verified. A call that outlives the watchdog pauses the sketch (the Worker is
// terminated); an error at the learner's settings says so and prefills
// "not right?" with code's words and the settings. The badge and the check
// lines are code-owned, worded here from closed fields; nothing the program
// draws can reach them. Nothing here takes focus or opens a modal.
import { useCallback, useContext, useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { FigurePredictionDto, FigureSketchDto, FigureViewDto } from "../../../../api/dto";
import { COLOR, FONT_MONO } from "../../../../components/term";
import { logReaderAction } from "../../activity";
import { MeaningLabel, ModelVoice, SourceVoice } from "../../voices";
import { formatValue } from "../FigurePanels";
import { linkStyle, PredictionBlock, PredictionResult, prefersReducedMotion } from "../FigureInline";
import type { FiguresCtl } from "../useFigures";
import { SketchRunError, type Params } from "./sketchEngine";
import { SketchRunnerContext, withWatchdog, type SketchRunner } from "./sketchRunner";
import { SketchSceneView } from "./SketchScene";
import { clockSteps, probeProblems, sceneProblems, type Scene, type SketchParameter, type SketchProgram } from "./sketchScene";

export const SKETCH_FRAME = {
  badge: "AI-written simulation · sandboxed · not checked against the book",
  unchecked: "AI-written simulation · nothing in it checked",
  notFromBooks: "AI-written simulation · sandboxed · not from your books",
  checksLead: "checked by LearnLoop:",
} as const;

export const SKETCH_COPY = {
  howItRunsLink: "ⓘ how this runs",
  howItRuns:
    "Written by LearnLoop's model as a small program. It runs in a sealed sandbox inside LearnLoop: it can't see your files, your notes, the network or the rest of the app — it only computes what's drawn here.",
  paused: "paused — this simulation is too slow here",
  resume: "step ▸",
  error: "this simulation hit an error at these settings",
  newSample: "↻ new sample",
  play: "▸ play",
  stop: "■ stop",
  step: "step ▸",
  restart: "↺ restart",
  table: "t values as a table",
  notRight: "not right?",
  askBetter: "ask for a better version",
  notRightWhere: "Goes to the figure author with this version; the new version is checked like this one and this one is kept.",
  shows: "shows",
  assumes: "assumes",
  loading: "starting the simulation…",
} as const;

/** The badge slot for a sketch, from closed values only. */
export function sketchBadge(figure: Pick<FigureViewDto, "grounding" | "sketch">): string {
  if (figure.grounding === "none") return SKETCH_FRAME.notFromBooks;
  return figure.sketch?.checks?.length ? SKETCH_FRAME.badge : SKETCH_FRAME.unchecked;
}

const quote = (name: string) => `‘${name}’`;

/** The check lines, worded by code from each check's closed fields (spec §9.5). */
export function sketchCheckLines(sketch: FigureSketchDto | null | undefined): string[] {
  if (!sketch) return [];
  const lines = sketch.checks.map((check) => {
    const subject = check.elements.length ? `the drawn ${check.elements.map(quote).join(", ")}` : `the value ${quote(check.probe)}`;
    const settings = `at ${check.settings} tested settings`;
    if (check.kind === "follows") return `${subject} follows ${check.statement} (AI-stated) ${settings}`;
    if (check.kind === "invariant") return `${subject} is ${check.statement} ${settings}`;
    if (check.kind === "distribution") return `${subject} agrees with ${check.statement} (AI-stated) within sampling error ${settings}`;
    return `${subject} is ${check.statement} (AI-stated) ${settings}`;
  });
  const unnamed = sketch.unnamedElements;
  if (sketch.notCovered.length || unnamed) {
    const named = sketch.notCovered.map(quote).join(", ");
    const others = unnamed ? `${named ? " and " : ""}${unnamed} other drawn element${unnamed === 1 ? "" : "s"}` : "";
    lines.push(`not covered: ${named}${others} (drawn, not checked)`);
  }
  return lines;
}

function defaultsOf(program: SketchProgram): Params {
  return Object.fromEntries(program.parameters.map((parameter) => [parameter.name, Number(parameter.default)]));
}

function clampStep(parameter: SketchParameter, raw: number): number {
  if (!Number.isFinite(raw)) return Number(parameter.default);
  const clamped = Math.min(parameter.max, Math.max(parameter.min, raw));
  const steps = Math.round((clamped - parameter.min) / parameter.step);
  return Math.min(parameter.max, Number((parameter.min + steps * parameter.step).toPrecision(12)));
}

function settingsText(params: Params): string {
  return Object.entries(params).map(([name, value]) => `${name}=${Number(value.toPrecision(6))}`).join(", ") || "the defaults";
}

function probeValue(value: unknown, shape: string): string {
  if (shape === "scalar") return formatValue(typeof value === "number" ? value : null);
  if (!Array.isArray(value)) return "—";
  if (shape === "series") {
    const head = value.slice(0, 8).map((item) => formatValue(typeof item === "number" ? item : null)).join(", ");
    return `${value.length} values: ${head}${value.length > 8 ? ", …" : ""}`;
  }
  const last = value[value.length - 1] as [number, number] | undefined;
  return `${value.length} points${last ? `; last (${formatValue(last[0])}, ${formatValue(last[1])})` : ""}`;
}

/** keep (display): how often play advances, and how many ticks a run to t_max takes. */
const PLAY_MS = 60;
const PLAY_TICKS = 100;

/** A random 32-bit seed for "new sample" (the host's, never the program's). */
function freshSeed(): number {
  const cryptoObject = (globalThis as { crypto?: Crypto }).crypto;
  if (cryptoObject?.getRandomValues) return cryptoObject.getRandomValues(new Uint32Array(1))[0];
  return Math.floor(Math.random() * 0xffffffff) >>> 0;
}

type RunState =
  | { kind: "loading" }
  | { kind: "ready" }
  | { kind: "paused" }
  | { kind: "error"; message: string; errorKind: string; params: Params };

export function SketchFigure({ figure, ctl, program }: { figure: FigureViewDto; ctl: FiguresCtl; program: SketchProgram }) {
  const factory = useContext(SketchRunnerContext);
  const [params, setParams] = useState<Params>(() => defaultsOf(program));
  const [seed, setSeed] = useState<number>(() => figure.sketch?.seed ?? 1);
  const [step, setStep] = useState(0);
  const [scene, setScene] = useState<Scene | null>(null);
  const [probes, setProbes] = useState<Record<string, unknown> | null>(null);
  const [state, setState] = useState<RunState>({ kind: "loading" });
  const [playing, setPlaying] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [showHow, setShowHow] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);
  const [note, setNote] = useState("");
  const [skipped, setSkipped] = useState(false);
  const [generation, setGeneration] = useState(0);
  const reduced = useMemo(prefersReducedMotion, []);
  const runner = useRef<SketchRunner | null>(null);
  const loaded = useRef<Promise<unknown> | null>(null);
  const busy = useRef(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const live = useRef({ params, seed, step });
  live.current = { params, seed, step };
  const total = clockSteps(program);
  const perTick = Math.max(1, Math.ceil(total / PLAY_TICKS));
  const names = useMemo(() => program.parameters.map((parameter) => parameter.name), [program]);

  const stopPlay = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    setPlaying(false);
  }, []);

  const fail = useCallback((caught: unknown, at: Params) => {
    stopPlay();
    if (caught instanceof SketchRunError && caught.kind === "paused") {
      setState({ kind: "paused" });
      return;
    }
    const message = caught instanceof Error ? caught.message : String(caught);
    const errorKind = caught instanceof SketchRunError ? caught.kind : "error";
    logReaderAction("sketch_error", { figure_id: figure.figureId, extraction_id: figure.extractionId, error_kind: errorKind });
    setState({ kind: "error", message, errorKind, params: at });
  }, [figure.figureId, figure.extractionId, stopPlay]);

  // One runner per open sketch (and per resume after a pause), disposed on close.
  useEffect(() => {
    const created = withWatchdog(factory(), undefined, () => {
      logReaderAction("sketch_paused", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    });
    runner.current = created;
    loaded.current = created.load(program.code);
    return () => {
      if (timer.current) clearInterval(timer.current);
      created.dispose();
      runner.current = null;
    };
  }, [factory, program.code, generation, figure.figureId, figure.extractionId]);

  const read = useCallback(async (active: SketchRunner, at: Params, index: number) => {
    const result = await active.read(at, index);
    const sceneIssues = sceneProblems(result.scene, names);
    if (sceneIssues.length) throw new SketchRunError("scene", `the scene ${sceneIssues[0]}`);
    const probeIssues = probeProblems(result.probes, program.probes);
    if (probeIssues.length) throw new SketchRunError("probe", probeIssues[0]);
    setScene(result.scene as Scene);
    setProbes(result.probes as Record<string, unknown>);
  }, [names, program.probes]);

  // Restart the run whenever the parameters or the seed change: init, then read step 0.
  useEffect(() => {
    const active = runner.current;
    if (!active || !loaded.current) return;
    let cancelled = false;
    const at = params;
    busy.current = true;
    loaded.current
      .then(() => active.init(at, seed))
      .then(() => (cancelled ? undefined : read(active, at, 0)))
      .then(() => {
        if (cancelled) return;
        setStep(0);
        setState({ kind: "ready" });
      })
      .catch((caught) => { if (!cancelled) fail(caught, at); })
      .finally(() => { busy.current = false; });
    return () => { cancelled = true; };
  }, [params, seed, generation, read, fail]);

  const advance = useCallback(async () => {
    const active = runner.current;
    if (!active || busy.current || !program.clock) return;
    const { params: at, step: from } = live.current;
    if (from >= total) {
      stopPlay();
      return;
    }
    const count = Math.min(perTick, total - from);
    busy.current = true;
    try {
      await active.step(at, program.clock.dt, from, count);
      await read(active, at, from + count);
      setStep(from + count);
      if (from + count >= total) stopPlay();
    } catch (caught) {
      fail(caught, at);
    } finally {
      busy.current = false;
    }
  }, [program.clock, total, perTick, read, fail, stopPlay]);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  const play = () => {
    if (playing) {
      stopPlay();
      return;
    }
    if (live.current.step >= total) {
      // At t_max: play starts over (the run restarts at step 0; press again to play).
      setParams((current) => ({ ...current }));
      return;
    }
    logReaderAction("figure_animated", { figure_id: figure.figureId, extraction_id: figure.extractionId, parameter: "t" });
    setPlaying(true);
    timer.current = setInterval(() => { void advance(); }, PLAY_MS);
  };

  const setParam = (name: string, raw: number) => {
    const parameter = program.parameters.find((item) => item.name === name);
    if (!parameter) return;
    stopPlay();
    setParams((current) => (current[name] === clampStep(parameter, raw) ? current : { ...current, [name]: clampStep(parameter, raw) }));
  };

  const onHandle = (id: string, x: number, y: number) => {
    const handle = scene?.elements.find((element) => element.type === "handle" && element.id === id);
    if (!handle || handle.type !== "handle") return;
    if (handle.binds.x) setParam(handle.binds.x, x);
    if (handle.binds.y) setParam(handle.binds.y, y);
  };

  const applyPrediction = (prediction: FigurePredictionDto) => {
    const change = program.predictions?.[prediction.index]?.change ?? {};
    if ("run_to" in change && program.clock) {
      setPlaying(true);
      timer.current = setInterval(() => {
        if (live.current.step >= Math.min(total, Math.round(change.run_to / program.clock!.dt))) stopPlay();
        else void advance();
      }, PLAY_MS);
      return;
    }
    setParams((current) => {
      const next = { ...current };
      for (const [name, value] of Object.entries(change)) {
        const parameter = program.parameters.find((item) => item.name === name);
        if (parameter) next[name] = clampStep(parameter, Number(value));
      }
      return next;
    });
  };

  const resume = () => {
    setState({ kind: "loading" });
    setGeneration((value) => value + 1);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) && (target as HTMLInputElement).type !== "range") return;
    if (event.key === "t" && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      setShowTable((value) => !value);
    }
  };

  const openPrediction = ctl.contract?.predictions && !skipped
    && !figure.predictions.some((prediction) => prediction.answered !== null) ? figure.predictions[0] ?? null : null;
  const answeredPrediction = figure.predictions.find((prediction) => prediction.answered !== null) ?? null;
  const locked = openPrediction !== null;
  const checkLines = sketchCheckLines(figure.sketch);
  const prefill = state.kind === "error" ? `${SKETCH_COPY.error}: ${settingsText(state.params)} (${state.message})`.slice(0, 600) : "";

  return (
    <div data-sketch-body="" onKeyDown={onKeyDown} style={{ display: "flex", flexDirection: "column", gap: 8, border: `1px solid ${COLOR.border}`, padding: "8px 10px", background: COLOR.bgElev }}>
      {figure.demonstrates ? <ModelVoice first note={SKETCH_COPY.shows}>{figure.demonstrates}</ModelVoice> : null}
      {figure.assumptions?.length ? (
        <div data-figure-assumptions="" style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <MeaningLabel>{SKETCH_COPY.assumes} · AI-written</MeaningLabel>
          {figure.assumptions.map((assumption, index) => (
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
        <PredictionResult figure={figure} prediction={answeredPrediction} ctl={ctl} format="number" />
      ) : null}
      {program.parameters.length ? (
        <div data-sketch-controls="" style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          {program.parameters.map((parameter) => {
            const value = params[parameter.name] ?? parameter.default;
            return (
              <span key={parameter.name} style={{ display: "inline-flex", gap: 6, alignItems: "center", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                  {parameter.label}
                  <input type="range" min={parameter.min} max={parameter.max} step={parameter.step} value={value} disabled={locked}
                    aria-label={parameter.label} onChange={(event) => setParam(parameter.name, Number(event.target.value))} />
                </label>
                <input type="number" min={parameter.min} max={parameter.max} step={parameter.step} value={Number(value.toPrecision(6))}
                  disabled={locked} aria-label={`${parameter.label} value`} onChange={(event) => setParam(parameter.name, Number(event.target.value))}
                  style={{ width: 70, fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
              </span>
            );
          })}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11 }}>
        {program.clock ? (
          reduced ? (
            <button type="button" style={linkStyle} disabled={locked || state.kind !== "ready"} data-sketch-step="" onClick={() => void advance()}>{SKETCH_COPY.step}</button>
          ) : (
            <button type="button" style={linkStyle} disabled={locked || state.kind !== "ready"} data-sketch-play="" onClick={play}>{playing ? SKETCH_COPY.stop : SKETCH_COPY.play}</button>
          )
        ) : null}
        {program.clock ? <span data-sketch-time="" style={{ color: COLOR.textDim }}>t = {formatValue(step * program.clock.dt)} / {formatValue(program.clock.t_max)}</span> : null}
        {program.clock && step > 0 ? <button type="button" style={linkStyle} onClick={() => { stopPlay(); setParams((current) => ({ ...current })); }}>{SKETCH_COPY.restart}</button> : null}
        {program.seeded ? (
          <button type="button" style={linkStyle} disabled={locked} data-sketch-new-sample="" onClick={() => { stopPlay(); setSeed(freshSeed()); }}>{SKETCH_COPY.newSample}</button>
        ) : null}
        <button type="button" style={linkStyle} aria-expanded={showHow} onClick={() => setShowHow((value) => !value)}>{SKETCH_COPY.howItRunsLink}</button>
      </div>
      {showHow ? <MeaningLabel data-sketch-how="">{SKETCH_COPY.howItRuns}</MeaningLabel> : null}
      {state.kind === "paused" ? (
        <div data-sketch-paused="" style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
          <MeaningLabel>{SKETCH_COPY.paused}</MeaningLabel>
          <button type="button" style={linkStyle} onClick={resume}>{SKETCH_COPY.resume}</button>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <div data-sketch-error={state.errorKind} style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
          <MeaningLabel style={{ color: COLOR.red }}>{SKETCH_COPY.error} ({settingsText(state.params)})</MeaningLabel>
          {ctl.contract?.revisions ? (
            <button type="button" style={linkStyle} data-sketch-error-not-right="" onClick={() => { setNote(prefill); setNoteOpen(true); }}>{SKETCH_COPY.notRight}</button>
          ) : null}
        </div>
      ) : null}
      {state.kind === "loading" && !scene ? <MeaningLabel>{SKETCH_COPY.loading}</MeaningLabel> : null}
      {scene && state.kind !== "error" ? <SketchSceneView scene={scene} onHandle={locked ? undefined : onHandle} label={figure.demonstrates ?? undefined} /> : null}
      {showTable && probes ? (
        <table data-sketch-values="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, borderCollapse: "collapse" }}>
          <thead>
            <tr><th style={{ textAlign: "left", paddingRight: 12 }}>value</th><th style={{ textAlign: "left" }}>at t = {program.clock ? formatValue(step * program.clock.dt) : "—"}</th></tr>
          </thead>
          <tbody>
            {program.probes.map((probe) => (
              <tr key={probe.name} data-sketch-probe={probe.name}>
                <td style={{ paddingRight: 12, fontStyle: "italic", color: COLOR.textItalic }}>{probe.label}</td>
                <td>{probeValue(probes[probe.name], probe.shape)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {checkLines.length ? (
        <div data-sketch-checks="" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {figure.sketch?.checks.length ? <MeaningLabel style={{ fontSize: 11 }}>{SKETCH_FRAME.checksLead}</MeaningLabel> : null}
          {checkLines.map((line, index) => (
            <span key={index} data-sketch-check-line="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>· {line}</span>
          ))}
        </div>
      ) : null}
      {program.annotations?.length ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {program.annotations.map((annotation, index) => (
            <MeaningLabel key={index} style={{ fontSize: 11 }}>◇ {annotation.target}: {annotation.text}</MeaningLabel>
          ))}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline" }}>
        <button type="button" style={linkStyle} aria-pressed={showTable} onClick={() => setShowTable((value) => !value)}>{SKETCH_COPY.table}</button>
        {ctl.contract?.revisions ? (
          noteOpen ? (
            <form onSubmit={(event) => { event.preventDefault(); ctl.revise(figure, note); setNoteOpen(false); setNote(""); }}
              style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}>
              <input value={note} onChange={(event) => setNote(event.target.value)} maxLength={600} aria-label={SKETCH_COPY.notRight}
                data-sketch-note=""
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 360, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
              <button type="submit" style={linkStyle}>{SKETCH_COPY.askBetter}</button>
              <MeaningLabel>{SKETCH_COPY.notRightWhere}</MeaningLabel>
            </form>
          ) : (
            <button type="button" style={linkStyle} onClick={() => setNoteOpen(true)}>{SKETCH_COPY.notRight}</button>
          )
        ) : null}
        {figure.versions > 1 ? <MeaningLabel>version {figure.versions}</MeaningLabel> : null}
      </div>
    </div>
  );
}

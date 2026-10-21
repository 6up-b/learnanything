// InteractiveFigureSpecV1 in the Reader (reader workbench RW5a; spec §8.2).
//
// The sidecar validated and verified the spec before sending it (the strict
// schema, the caps, §8.3's checks); the Reader compiles it again with the
// TypeScript grammar and draws nothing it cannot compile (fail closed).
// evaluateFigure is the Python twin's evaluate_figure (src/learnloop/figures/
// spec.py): the same samples, the same shaded-area and highlight readouts,
// the same unit square. It is the only evaluation the renderer runs, whether
// a slider moves or "play" sweeps a parameter.

import {
  CONSTANTS,
  FigureGrammarError,
  MAX_SAFE_INTEGER,
  RESERVED,
  adaptiveSimpson,
  canonical,
  checkNames,
  evaluate,
  exactSum,
  isName,
  newEnv,
  parseExpression,
  walk,
  type Definitions,
  type Env,
  type FigureNode,
} from "./figureGrammar";

export const SPEC_VERSION = "ifs-v1";
export const SAMPLES = 120;
export const DIRECTIONS = ["rises", "falls", "same"] as const;
export const SAME_TOLERANCE = 1e-6;
// At most this many PMF bars (the Python twin's MAX_BARS).
export const MAX_BARS = 200;
// The widest a function plot's x range may be: its samples must not overflow (fix round 4; the Python twin's MAX_DOMAIN_SPAN).
export const MAX_DOMAIN_SPAN = 1e12;

export interface FigureParameter { name: string; label: string; min: number; max: number; step: number; default: number; animate?: boolean }
export interface FigureAxis { var: string; min: number; max: number }
export interface FigureSeries { expr: string; label: string }
export interface FigureShade { series: string; from: string; to: string; label: string }
export interface FigureMarker { x: string; label: string }
export interface FunctionPlotPanel { kind: "function_plot"; x: FigureAxis; series: FigureSeries[]; markers?: FigureMarker[]; shade?: FigureShade[] }
export interface PmfBarsPanel { kind: "pmf_bars"; k: FigureAxis; series: FigureSeries[]; highlight?: { from: string; to: string; label: string } | null }
export interface LinearMapPanel { kind: "linear_map_2d"; matrix: string[][]; label?: string }
export interface ReadoutPanel { kind: "readout"; label: string; expr: string; format?: "number" | "percent" }
export type FigurePanel = FunctionPlotPanel | PmfBarsPanel | LinearMapPanel | ReadoutPanel;
export interface FigureInvariant { kind: string; expr?: string; var?: string | null; from?: number | null; to?: number | null; bound?: number | null; name?: string | null }
export interface FigurePrediction { prompt: string; change?: Record<string, number>; observe: { kind: "direction" | "area"; expr: string } }

export interface FigureSpec {
  spec_version: string;
  kind: "reconstructed" | "illustrative";
  source_claims?: Array<{ span_id: string; quote: string }>;
  region?: { span_id: string; bbox: number[] } | null;
  demonstrates: string;
  assumptions?: Array<{ text: string; span_id?: string | null; quote?: string | null }>;
  parameters?: FigureParameter[];
  definitions?: Array<{ name: string; expr: string }>;
  panels: FigurePanel[];
  invariants?: FigureInvariant[];
  predictions?: FigurePrediction[];
  annotations?: Array<{ target: string; text: string }>;
}

export interface CompiledPanel { kind: FigurePanel["kind"]; model: FigurePanel; nodes: Record<string, unknown> }

export interface CompiledFigure {
  spec: FigureSpec;
  parameters: FigureParameter[];
  definitions: Definitions;
  panels: CompiledPanel[];
  predictions: Array<{ prediction: FigurePrediction; node: FigureNode }>;
  variables: Set<string>;
}

export class FigureSpecError extends Error {
  constructor(readonly problems: string[]) {
    super(problems.join("; ") || "invalid figure spec");
  }
}

export function defaults(compiled: CompiledFigure): Env {
  const env: Env = newEnv();
  for (const parameter of compiled.parameters) env[parameter.name] = Number(parameter.default);
  return env;
}

/** The variables and parameters node needs, definitions expanded where used; iterative (fix round 4). */
export function expandedFree(node: FigureNode, defs: Definitions, bound: Set<string> = new Set(), seen: string[] = []): Set<string> {
  const found = new Set<string>();
  const stack: Array<[FigureNode, Set<string>, string[]]> = [[node, bound, seen]];
  while (stack.length) {
    const [current, scope, chain] = stack.pop() as [FigureNode, Set<string>, string[]];
    if (current.kind === "name") {
      const name = current.text;
      if (scope.has(name) || Object.prototype.hasOwnProperty.call(CONSTANTS, name)) continue;
      if (defs.has(name) && !chain.includes(name)) stack.push([defs.get(name) as FigureNode, scope, [...chain, name]]);
      else found.add(name);
    } else if (current.kind === "integral" || current.kind === "sum") {
      const [body, lower, upper] = current.args;
      stack.push([body, new Set([...scope, current.text]), chain], [lower, scope, chain], [upper, scope, chain]);
    } else {
      for (const child of current.args) stack.push([child, scope, chain]);
    }
  }
  return found;
}


function boundVariables(node: FigureNode): string[] {
  return [...walk(node)].filter((child) => child.kind === "integral" || child.kind === "sum").map((child) => child.text);
}

/** Compile a spec: every expression parsed, every name resolved; FigureSpecError otherwise. */
export function compileSpec(raw: FigureSpec | string): CompiledFigure {
  try {
    return compileChecked(raw);
  } catch (error) {
    // A safety net only: the iterative passes and the expanded-depth cap keep
    // compilation inside the stack (fix round 4).
    if (error instanceof RangeError) throw new FigureSpecError(["an expression nests too deeply to check"]);
    throw error;
  }
}

function compileChecked(raw: FigureSpec | string): CompiledFigure {
  const spec: FigureSpec = typeof raw === "string" ? (JSON.parse(raw) as FigureSpec) : raw;
  const problems: string[] = [];
  const problem = (text: string) => {
    if (problems.length < 20) problems.push(text);
  };
  if (!spec || spec.spec_version !== SPEC_VERSION || !Array.isArray(spec.panels) || !spec.panels.length) {
    throw new FigureSpecError(["not an ifs-v1 figure spec"]);
  }
  const parameters = spec.parameters ?? [];
  const params = new Set(parameters.map((parameter) => parameter.name));
  const parse = (where: string, source: string): FigureNode | null => {
    try {
      return parseExpression(source);
    } catch (error) {
      problem(`${where}: ${(error as Error).message}`);
      return null;
    }
  };
  for (const parameter of parameters) {
    if (!isName(parameter.name) || RESERVED.has(parameter.name)) problem(`parameter ${parameter.name} is not a usable name`);
    const values = [parameter.min, parameter.max, parameter.step, parameter.default];
    if (!values.every((value) => Number.isFinite(value))) problem(`parameter ${parameter.name} has a value that is not finite`);
    else if (!(parameter.min < parameter.max) || !(parameter.min <= parameter.default && parameter.default <= parameter.max) || !(parameter.step > 0)) {
      problem(`parameter ${parameter.name} has an unusable range`);
    }
  }
  if (params.size !== parameters.length) problem("a parameter is defined twice");
  const variables = new Set<string>();
  for (const panel of spec.panels) {
    if (panel.kind === "function_plot") variables.add(panel.x.var);
    else if (panel.kind === "pmf_bars") variables.add(panel.k.var);
  }
  for (const invariant of spec.invariants ?? []) if (invariant.var) variables.add(invariant.var);
  const parsedDefs: Array<[string, FigureNode | null]> = (spec.definitions ?? []).map((definition) => {
    const node = parse(`definition ${definition.name}`, definition.expr);
    if (node) boundVariables(node).forEach((name) => variables.add(name));
    return [definition.name, node];
  });
  for (const source of allExpressions(spec)) {
    const node = parse("expression", source);
    if (node) boundVariables(node).forEach((name) => variables.add(name));
  }
  for (const name of [...variables]) {
    if (!isName(name) || RESERVED.has(name) || params.has(name)) {
      problem(`variable ${name} is a reserved word or a parameter's name`);
      variables.delete(name);
    }
  }
  const definitions: Definitions = new Map();
  const needs = (where: string, node: FigureNode | null, allowed: Set<string>): FigureNode | null => {
    if (!node) return null;
    try {
      checkNames(node, new Set([...allowed, ...variables]), definitions);
    } catch (error) {
      problem(`${where}: ${(error as Error).message}`);
      return null;
    }
    const missing = [...expandedFree(node, definitions)].filter((name) => !allowed.has(name));
    if (missing.length) {
      problem(`${where}: needs ${missing.sort().join(", ")}, which is not defined here`);
      return null;
    }
    return node;
  };
  for (const [name, node] of parsedDefs) {
    if (!isName(name) || RESERVED.has(name) || params.has(name) || variables.has(name) || definitions.has(name)) {
      problem(`definition ${name} is not a usable name`);
      continue;
    }
    const checked = needs(`definition ${name}`, node, new Set([...params, ...variables]));
    if (checked) definitions.set(name, checked);
  }
  const expr = (where: string, source: string, allowed: Set<string>) => needs(where, parse(where, source), allowed);
  const panels: CompiledPanel[] = spec.panels.map((panel, index) => {
    const where = `panel ${index + 1} (${panel.kind})`;
    const nodes: Record<string, unknown> = {};
    if (panel.kind === "function_plot" || panel.kind === "pmf_bars") {
      const axis = panel.kind === "function_plot" ? panel.x : panel.k;
      if (!(Number.isFinite(axis.min) && Number.isFinite(axis.max) && axis.min < axis.max)) problem(`${where}: its range must be finite with min below max`);
      else if (panel.kind === "function_plot" && axis.max - axis.min > MAX_DOMAIN_SPAN) problem(`${where}: its range may span at most ${MAX_DOMAIN_SPAN}`);
      if (panel.kind === "pmf_bars" && Number.isFinite(axis.min) && Number.isFinite(axis.max)) {
        // The Python twin's checks, in its order (fix round 2): past the safe
        // integers k + 1 === k, so the bars' loop would never end.
        if (axis.min !== Math.floor(axis.min) || axis.max !== Math.floor(axis.max)) problem(`${where}: k's range must be whole numbers`);
        else if (Math.abs(axis.min) > MAX_SAFE_INTEGER || Math.abs(axis.max) > MAX_SAFE_INTEGER) problem(`${where}: k's range must lie within ±${MAX_SAFE_INTEGER}`);
        else if (axis.max - axis.min + 1 > MAX_BARS) problem(`${where}: at most ${MAX_BARS} bars`);
      }
      const allowed = new Set([...params, axis.var]);
      const labels = panel.series.map((series) => series.label);
      nodes.series = panel.series.map((series) => expr(`${where} series ${series.label}`, series.expr, allowed));
      if (panel.kind === "function_plot") {
        nodes.markers = (panel.markers ?? []).map((marker) => expr(`${where} marker`, marker.x, params));
        nodes.shades = (panel.shade ?? []).map((shade) => {
          if (!labels.includes(shade.series)) problem(`${where}: shaded area ${shade.label} names no series`);
          return [expr(`${where} shade`, shade.from, params), expr(`${where} shade`, shade.to, params)];
        });
      } else if (panel.highlight) {
        nodes.highlight = [expr(`${where} highlight`, panel.highlight.from, params), expr(`${where} highlight`, panel.highlight.to, params)];
      }
    } else if (panel.kind === "linear_map_2d") {
      nodes.matrix = panel.matrix.map((row) => row.map((cell) => expr(`${where} matrix`, cell, params)));
    } else {
      nodes.expr = expr(`${where} ${panel.label}`, panel.expr, params);
    }
    return { kind: panel.kind, model: panel, nodes };
  });
  for (const [index, invariant] of (spec.invariants ?? []).entries()) {
    if (invariant.kind === "equals_source" || !invariant.expr) continue;
    expr(`invariant ${index + 1}`, invariant.expr, new Set([...params, ...(invariant.var ? [invariant.var] : [])]));
  }
  const predictions = (spec.predictions ?? []).map((prediction, index) => ({
    prediction,
    node: expr(`prediction ${index + 1}`, prediction.observe.expr, params) as FigureNode,
  }));
  if (problems.length) throw new FigureSpecError(problems);
  return { spec, parameters, definitions, panels, predictions, variables };
}

function allExpressions(spec: FigureSpec): string[] {
  const sources: string[] = [];
  for (const panel of spec.panels) {
    if (panel.kind === "function_plot") {
      sources.push(...panel.series.map((series) => series.expr), ...(panel.markers ?? []).map((marker) => marker.x));
      for (const shade of panel.shade ?? []) sources.push(shade.from, shade.to);
    } else if (panel.kind === "pmf_bars") {
      sources.push(...panel.series.map((series) => series.expr));
      if (panel.highlight) sources.push(panel.highlight.from, panel.highlight.to);
    } else if (panel.kind === "linear_map_2d") {
      for (const row of panel.matrix) sources.push(...row);
    } else {
      sources.push(panel.expr);
    }
  }
  for (const invariant of spec.invariants ?? []) if (invariant.expr) sources.push(invariant.expr);
  for (const prediction of spec.predictions ?? []) sources.push(prediction.observe.expr);
  return sources;
}

// ---------------------------------------------------------------------------
// Evaluation: the panels' data (the golden corpus's parity unit)
// ---------------------------------------------------------------------------

// A shown value: null when not finite, never -0 (fix round 3).
const num = (value: number): number | null => (Number.isFinite(value) ? canonical(value) : null);
const value = (node: FigureNode | null | undefined, env: Env, defs: Definitions): number => (node ? evaluate(node, env, defs) : NaN);

export function plotXs(axis: FigureAxis): number[] {
  return Array.from({ length: SAMPLES + 1 }, (_, i) => canonical(axis.min + ((axis.max - axis.min) * i) / SAMPLES));
}

/** The bars' k values: counted from the support's start, at most MAX_BARS of them (compileSpec refuses more). */
export function barKs(axis: FigureAxis): number[] {
  const low = Math.trunc(axis.min);
  const count = Math.max(0, Math.min(Math.trunc(axis.max) - low + 1, MAX_BARS));
  const ks: number[] = [];
  for (let index = 0; index < count; index += 1) ks.push(low + index);
  return ks;
}

export function shadeValue(compiled: CompiledFigure, panel: CompiledPanel, shadeIndex: number, env: Env): [number, number, number] {
  const model = panel.model as FunctionPlotPanel;
  const shade = (model.shade ?? [])[shadeIndex];
  const [lowerNode, upperNode] = (panel.nodes.shades as Array<[FigureNode | null, FigureNode | null]>)[shadeIndex];
  let lower = value(lowerNode, env, compiled.definitions);
  let upper = value(upperNode, env, compiled.definitions);
  lower = Number.isFinite(lower) ? Math.min(Math.max(lower, model.x.min), model.x.max) : NaN;
  upper = Number.isFinite(upper) ? Math.min(Math.max(upper, model.x.min), model.x.max) : NaN;
  const seriesIndex = model.series.map((series) => series.label).indexOf(shade.series);
  const node = (panel.nodes.series as Array<FigureNode | null>)[seriesIndex];
  const variable = model.x.var;
  const scope: Env = newEnv(env);
  const at = (t: number): number => {
    scope[variable] = t;
    return value(node, scope, compiled.definitions);
  };
  return [lower, upper, adaptiveSimpson(at, lower, upper)];
}

function highlightValue(compiled: CompiledFigure, panel: CompiledPanel, env: Env): [number, number, number] {
  const model = panel.model as PmfBarsPanel;
  const [lowerNode, upperNode] = panel.nodes.highlight as [FigureNode | null, FigureNode | null];
  let lower = value(lowerNode, env, compiled.definitions);
  let upper = value(upperNode, env, compiled.definitions);
  const node = (panel.nodes.series as Array<FigureNode | null>)[0];
  const variable = model.k.var;
  const scope: Env = newEnv(env);
  const at = (k: number): number => {
    scope[variable] = k;
    return value(node, scope, compiled.definitions);
  };
  lower = Number.isFinite(lower) ? Math.max(lower, model.k.min) : NaN;
  upper = Number.isFinite(upper) ? Math.min(upper, model.k.max) : NaN;
  return [lower, upper, exactSum(at, lower, upper)];
}

export interface FunctionPlotData { kind: "function_plot"; x: number[]; series: Array<{ label: string; y: Array<number | null> }>; shades: Array<{ label: string; series: string; from: number | null; to: number | null; value: number | null }>; markers: Array<{ label: string; x: number | null }> }
export interface PmfBarsData { kind: "pmf_bars"; k: number[]; series: Array<{ label: string; p: Array<number | null> }>; highlight: { label: string; from: number | null; to: number | null; value: number | null } | null }
export interface LinearMapData { kind: "linear_map_2d"; matrix: Array<Array<number | null>>; square: Array<[number | null, number | null]>; determinant: number | null }
export interface ReadoutData { kind: "readout"; label: string; format: "number" | "percent"; value: number | null }
export type PanelData = FunctionPlotData | PmfBarsData | LinearMapData | ReadoutData;

export function evaluatePanel(compiled: CompiledFigure, panel: CompiledPanel, env: Env): PanelData {
  const defs = compiled.definitions;
  if (panel.kind === "function_plot") {
    const model = panel.model as FunctionPlotPanel;
    const xs = plotXs(model.x);
    const series = model.series.map((item, index) => {
      const node = (panel.nodes.series as Array<FigureNode | null>)[index];
      const scope: Env = newEnv(env);
      return {
        label: item.label,
        y: xs.map((x) => {
          scope[model.x.var] = x;
          return num(value(node, scope, defs));
        }),
      };
    });
    const shades = (model.shade ?? []).map((shade, index) => {
      const [lower, upper, area] = shadeValue(compiled, panel, index, env);
      return { label: shade.label, series: shade.series, from: num(lower), to: num(upper), value: num(area) };
    });
    const markers = (model.markers ?? []).map((marker, index) => ({
      label: marker.label,
      x: num(value((panel.nodes.markers as Array<FigureNode | null>)[index], env, defs)),
    }));
    return { kind: "function_plot", x: xs, series, shades, markers };
  }
  if (panel.kind === "pmf_bars") {
    const model = panel.model as PmfBarsPanel;
    const ks = barKs(model.k);
    const series = model.series.map((item, index) => {
      const node = (panel.nodes.series as Array<FigureNode | null>)[index];
      const scope: Env = newEnv(env);
      return {
        label: item.label,
        p: ks.map((k) => {
          scope[model.k.var] = k;
          return num(value(node, scope, defs));
        }),
      };
    });
    let highlight: PmfBarsData["highlight"] = null;
    if (model.highlight) {
      const [lower, upper, total] = highlightValue(compiled, panel, env);
      highlight = { label: model.highlight.label, from: num(lower), to: num(upper), value: num(total) };
    }
    return { kind: "pmf_bars", k: ks, series, highlight };
  }
  if (panel.kind === "linear_map_2d") {
    const m = (panel.nodes.matrix as Array<Array<FigureNode | null>>).map((row) => row.map((node) => value(node, env, defs)));
    const [a, b] = m[0];
    const [c, d] = m[1];
    const corners: Array<[number, number]> = [[0, 0], [a, c], [a + b, c + d], [b, d]];
    return {
      kind: "linear_map_2d",
      matrix: m.map((row) => row.map(num)),
      square: corners.map(([x, y]) => [num(x), num(y)] as [number | null, number | null]),
      determinant: num(a * d - b * c),
    };
  }
  const model = panel.model as ReadoutPanel;
  return { kind: "readout", label: model.label, format: model.format ?? "number", value: num(value(panel.nodes.expr as FigureNode, env, defs)) };
}

export interface FigureData { params: Env; panels: PanelData[] }

/** Every panel's data at params (defaults for the rest): the slider's and play's one evaluation. */
export function evaluateFigure(compiled: CompiledFigure, params: Env = {}): FigureData {
  const env = defaults(compiled);
  for (const [name, raw] of Object.entries(params)) if (Object.prototype.hasOwnProperty.call(env, name)) env[name] = Number(raw);
  return { params: { ...env }, panels: compiled.panels.map((panel) => evaluatePanel(compiled, panel, env)) };
}

export function observedValue(compiled: CompiledFigure, index: number, params: Env = {}): number {
  const env = defaults(compiled);
  for (const [name, raw] of Object.entries(params)) if (Object.prototype.hasOwnProperty.call(env, name)) env[name] = Number(raw);
  return value(compiled.predictions[index].node, env, compiled.definitions);
}

export { FigureGrammarError };

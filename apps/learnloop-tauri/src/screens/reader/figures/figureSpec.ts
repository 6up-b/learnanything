// InteractiveFigureSpecV1 in the Reader (reader workbench RW5a; spec §8.2).
//
// The sidecar validated and verified the spec before sending it (the strict
// schema, the caps, §8.3's checks); the Reader compiles it again with the
// TypeScript grammar and draws nothing it cannot compile (fail closed).
// evaluateFigure is the Python twin's evaluate_figure (src/learnloop/figures/
// spec.py): the same samples, the same shaded-area and highlight readouts,
// the same unit square. It is the only evaluation the renderer runs, whether
// a slider moves or "play" sweeps a parameter.
//
// RW5b (spec §8.7) adds heatmap_2d, vector_field_2d, trajectory_2d (fixed-step
// RK4) and iterate_2d to the same grammar. Their compile checks, computation
// caps and evaluation are the Python twin's operation for operation (the
// golden panels corpus pins both, RK4 step for step).

import {
  CONSTANTS,
  FigureGrammarError,
  MAX_SAFE_INTEGER,
  MAX_SUM_TERMS,
  RESERVED,
  adaptiveSimpson,
  canonical,
  checkNames,
  evaluate,
  exactSum,
  expansion,
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
// RW5b's panels and their code-owned caps on computation (the Python twin's).
export const ADVANCED_KINDS = ["heatmap_2d", "vector_field_2d", "trajectory_2d", "iterate_2d"] as const;
export const MAX_HEATMAP_CELLS = 40;
export const DEFAULT_HEATMAP_CELLS = 40;
export const MAX_FIELD_CELLS = 20;
export const DEFAULT_FIELD_CELLS = 12;
export const MAX_TRAJECTORY_STEPS = 2000;
export const DEFAULT_TRAJECTORY_STEPS = 400;
export const MAX_ITERATIONS = 500;
export const DEFAULT_ITERATIONS = 50;
export const MAX_CONTOURS = 8;
export const MAX_PANEL_WORK = 250000;
export const ESCAPE_MARGIN = 0.25;
export const STOP_LEFT = "left_plot";
export const STOP_NOT_FINITE = "not_finite";
export const STOP_OUTSIDE = "starts_outside";

export interface FigureParameter { name: string; label: string; min: number; max: number; step: number; default: number; animate?: boolean }
export interface FigureAxis { var: string; min: number; max: number }
export interface FigureSeries { expr: string; label: string }
export interface FigureShade { series: string; from: string; to: string; label: string }
export interface FigureMarker { x: string; label: string }
export interface FunctionPlotPanel { kind: "function_plot"; x: FigureAxis; series: FigureSeries[]; markers?: FigureMarker[]; shade?: FigureShade[] }
export interface PmfBarsPanel { kind: "pmf_bars"; k: FigureAxis; series: FigureSeries[]; highlight?: { from: string; to: string; label: string } | null }
export interface LinearMapPanel { kind: "linear_map_2d"; matrix: string[][]; label?: string }
export interface ReadoutPanel { kind: "readout"; label: string; expr: string; format?: "number" | "percent" }
export interface GridAxis extends FigureAxis { cells?: number | null }
export interface HeatmapPanel { kind: "heatmap_2d"; x: GridAxis; y: GridAxis; expr: string; contours?: string[]; label?: string }
export interface FieldHeatmap { expr: string; cells?: number | null; contours?: string[]; label?: string }
export interface VectorFieldPanel { kind: "vector_field_2d"; x: GridAxis; y: GridAxis; u: string; v: string; heatmap?: FieldHeatmap | null; label?: string }
export interface TrajectoryPanel { kind: "trajectory_2d"; x: FigureAxis; y: FigureAxis; x0: string; y0: string; dx: string; dy: string; t_max: string; steps?: number; time?: string | null; label?: string }
export interface IteratePanel { kind: "iterate_2d"; x: FigureAxis; y: FigureAxis; x0: string; y0: string; fx: string; fy: string; n?: number; label?: string }
export type AdvancedPanel = HeatmapPanel | VectorFieldPanel | TrajectoryPanel | IteratePanel;
export type FigurePanel = FunctionPlotPanel | PmfBarsPanel | LinearMapPanel | ReadoutPanel | AdvancedPanel;

export function isAdvancedKind(kind: unknown): kind is AdvancedPanel["kind"] {
  return (ADVANCED_KINDS as readonly unknown[]).includes(kind);
}
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
    else if (isAdvancedKind(panel.kind)) {
      const advanced = panel as AdvancedPanel;
      variables.add(advanced.x.var);
      variables.add(advanced.y.var);
      if (advanced.kind === "trajectory_2d" && advanced.time) variables.add(advanced.time);
    }
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
  const advanced = new AdvancedCompiler(problem, expr, parameters, definitions, params);
  const panels: CompiledPanel[] = spec.panels.map((panel, index) => {
    const where = `panel ${index + 1} (${panel.kind})`;
    let nodes: Record<string, unknown> = {};
    if (isAdvancedKind(panel.kind)) {
      nodes = advanced.panel(where, panel as AdvancedPanel);
    } else if (panel.kind === "function_plot" || panel.kind === "pmf_bars") {
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
      const readout = panel as ReadoutPanel;
      nodes.expr = expr(`${where} ${readout.label}`, readout.expr, params);
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
    } else if (isAdvancedKind(panel.kind)) {
      sources.push(...advancedExpressions(panel as AdvancedPanel));
    } else {
      sources.push((panel as ReadoutPanel).expr);
    }
  }
  for (const invariant of spec.invariants ?? []) if (invariant.expr) sources.push(invariant.expr);
  for (const prediction of spec.predictions ?? []) sources.push(prediction.observe.expr);
  return sources;
}

// ---------------------------------------------------------------------------
// RW5b's panels: compile checks and the computation caps (the Python twin's)
// ---------------------------------------------------------------------------

/** Every expression of an RW5b panel. */
export function advancedExpressions(panel: AdvancedPanel): string[] {
  if (panel.kind === "heatmap_2d") return [panel.expr, ...(panel.contours ?? [])];
  if (panel.kind === "vector_field_2d") {
    const overlay = panel.heatmap ? [panel.heatmap.expr, ...(panel.heatmap.contours ?? [])] : [];
    return [panel.u, panel.v, ...overlay];
  }
  if (panel.kind === "trajectory_2d") return [panel.x0, panel.y0, panel.dx, panel.dy, panel.t_max];
  return [panel.x0, panel.y0, panel.fx, panel.fy];
}

/** The RW5b panel kinds a spec uses, in order. */
export function advancedKinds(spec: FigureSpec): string[] {
  return (spec.panels ?? []).map((panel) => panel.kind).filter((kind) => isAdvancedKind(kind));
}

type Ranges = Map<string, [number, number]>;

function cellsOf(panel: HeatmapPanel | VectorFieldPanel, axis: GridAxis): number {
  const heat = panel.kind === "heatmap_2d";
  const fallback = heat ? DEFAULT_HEATMAP_CELLS : DEFAULT_FIELD_CELLS;
  const cap = heat ? MAX_HEATMAP_CELLS : MAX_FIELD_CELLS;
  return Math.min(Math.trunc(axis.cells ?? fallback), cap);
}

function overlayCells(overlay: FieldHeatmap): number {
  return Math.min(Math.trunc(overlay.cells ?? DEFAULT_HEATMAP_CELLS), MAX_HEATMAP_CELLS);
}

function boundRange(node: FigureNode, parameters: FigureParameter[], ranges: Ranges): [number, number] | null {
  if (node.kind === "num") return [node.value, node.value];
  if (node.kind === "neg" && node.args[0].kind === "num") return [-node.args[0].value, -node.args[0].value];
  if (node.kind === "name") {
    const parameter = parameters.find((item) => item.name === node.text);
    if (parameter) return [Number(parameter.min), Number(parameter.max)];
    const range = ranges.get(node.text);
    if (range) return range;
  }
  return null;
}

/** The most terms a sum can have, or null when its bounds are not countable (sum_terms). */
function sumTerms(node: FigureNode, parameters: FigureParameter[], ranges: Ranges): number | null {
  const lower = boundRange(node.args[1], parameters, ranges);
  const upper = boundRange(node.args[2], parameters, ranges);
  if (!lower || !upper || ![...lower, ...upper].every((value) => Number.isFinite(value))) return null;
  const low = Math.ceil(lower[0] - 1e-9);
  const high = Math.floor(upper[1] + 1e-9);
  return Math.max(0, Math.min(high - low + 1, MAX_SUM_TERMS));
}

/** How many nodes one evaluation of node visits at most (expression_work). */
export function expressionWork(node: FigureNode, defs: Definitions, parameters: FigureParameter[], ranges: Ranges, seen: string[] = []): number {
  if (node.kind === "name" && defs.has(node.text) && !seen.includes(node.text)) {
    return expressionWork(defs.get(node.text) as FigureNode, defs, parameters, ranges, [...seen, node.text]);
  }
  if (node.kind === "sum") {
    const terms = sumTerms(node, parameters, ranges) ?? 0;
    const [body, lower, upper] = node.args;
    return 1 + expressionWork(lower, defs, parameters, ranges, seen) + expressionWork(upper, defs, parameters, ranges, seen)
      + terms * expressionWork(body, defs, parameters, ranges, seen);
  }
  let total = 1;
  for (const child of node.args) total += expressionWork(child, defs, parameters, ranges, seen);
  return total;
}

const integerIn = (value: unknown, low: number, high: number): boolean =>
  typeof value === "number" && Number.isInteger(value) && value >= low && value <= high;

class AdvancedCompiler {
  work = 0;

  constructor(
    private readonly problem: (text: string) => void,
    private readonly expr: (where: string, source: string, allowed: Set<string>) => FigureNode | null,
    private readonly parameters: FigureParameter[],
    private readonly definitions: Definitions,
    private readonly params: Set<string>,
  ) {}

  private window(where: string, axes: FigureAxis[]): void {
    for (const axis of axes) {
      if (!(Number.isFinite(axis.min) && Number.isFinite(axis.max) && axis.min < axis.max)) this.problem(`${where}: its ${axis.var} range must be finite with min below max`);
      else if (axis.max - axis.min > MAX_DOMAIN_SPAN) this.problem(`${where}: its ${axis.var} range may span at most ${MAX_DOMAIN_SPAN}`);
    }
    if (new Set(axes.map((axis) => axis.var)).size !== axes.length) this.problem(`${where}: its x and y variables must differ`);
  }

  /** The schema's caps (pydantic's, in the Python twin) on counts the computation reads. */
  private shape(where: string, panel: AdvancedPanel): void {
    const cellsOk = (value: unknown) => value === undefined || value === null || integerIn(value, 1, MAX_HEATMAP_CELLS);
    if (panel.kind === "heatmap_2d" || panel.kind === "vector_field_2d") {
      if (!cellsOk(panel.x.cells) || !cellsOk(panel.y.cells)) this.problem(`${where}: cells must be a whole number from 1 to ${MAX_HEATMAP_CELLS}`);
      const contours = panel.kind === "heatmap_2d" ? panel.contours : panel.heatmap?.contours;
      if ((contours ?? []).length > MAX_CONTOURS) this.problem(`${where}: at most ${MAX_CONTOURS} contour levels`);
      if (panel.kind === "vector_field_2d" && panel.heatmap && !cellsOk(panel.heatmap.cells)) this.problem(`${where}: cells must be a whole number from 1 to ${MAX_HEATMAP_CELLS}`);
    } else if (panel.kind === "trajectory_2d") {
      if (panel.steps !== undefined && !integerIn(panel.steps, 1, MAX_TRAJECTORY_STEPS)) this.problem(`${where}: steps must be a whole number from 1 to ${MAX_TRAJECTORY_STEPS}`);
    } else if (panel.n !== undefined && !integerIn(panel.n, 1, MAX_ITERATIONS)) {
      this.problem(`${where}: n must be a whole number from 1 to ${MAX_ITERATIONS}`);
    }
  }

  /** A per-point expression: resolved, no integral, every sum's bounds countable (point_expr). */
  private pointExpr(where: string, source: string, allowed: Set<string>, ranges: Ranges): FigureNode | null {
    const node = this.expr(where, source, allowed);
    if (!node) return null;
    for (const [child] of expansion(node, this.definitions)) {
      if (child.kind === "integral") {
        this.problem(`${where}: an integral at every point is too much computation for this panel (use sum, or a readout)`);
        return null;
      }
      if (child.kind === "sum" && sumTerms(child, this.parameters, ranges) === null) {
        this.problem(`${where}: a sum's bounds here must each be a number, a parameter or the grid's own axis, so its terms can be counted`);
        return null;
      }
    }
    return node;
  }

  private cost(node: FigureNode | null, ranges: Ranges): number {
    return node ? expressionWork(node, this.definitions, this.parameters, ranges) : 0;
  }

  panel(where: string, panel: AdvancedPanel): Record<string, unknown> {
    this.shape(where, panel);
    const params = this.params;
    this.window(where, [panel.x, panel.y]);
    const grid = new Set([panel.x.var, panel.y.var]);
    const withGrid = new Set([...params, ...grid]);
    const nodes: Record<string, unknown> = {};
    let work = 0;
    if (panel.kind === "vector_field_2d") {
      for (const axis of [panel.x, panel.y]) {
        if (axis.cells !== undefined && axis.cells !== null && axis.cells > MAX_FIELD_CELLS) this.problem(`${where}: at most ${MAX_FIELD_CELLS} arrows' cells per axis`);
      }
    }
    if (panel.kind === "heatmap_2d" || panel.kind === "vector_field_2d") {
      const ranges: Ranges = new Map([[panel.x.var, [panel.x.min, panel.x.max]], [panel.y.var, [panel.y.min, panel.y.max]]]);
      const points = (cellsOf(panel, panel.x) + 1) * (cellsOf(panel, panel.y) + 1);
      if (panel.kind === "heatmap_2d") {
        nodes.expr = this.pointExpr(`${where} value`, panel.expr, withGrid, ranges);
        nodes.contours = (panel.contours ?? []).map((level) => this.expr(`${where} contour`, level, params));
        work = points * this.cost(nodes.expr as FigureNode | null, ranges);
      } else {
        nodes.u = this.pointExpr(`${where} u`, panel.u, withGrid, ranges);
        nodes.v = this.pointExpr(`${where} v`, panel.v, withGrid, ranges);
        work = points * (this.cost(nodes.u as FigureNode | null, ranges) + this.cost(nodes.v as FigureNode | null, ranges));
        if (panel.heatmap) {
          const side = overlayCells(panel.heatmap);
          nodes.heatmap = this.pointExpr(`${where} heat map`, panel.heatmap.expr, withGrid, ranges);
          nodes.contours = (panel.heatmap.contours ?? []).map((level) => this.expr(`${where} contour`, level, params));
          work += (side + 1) * (side + 1) * this.cost(nodes.heatmap as FigureNode | null, ranges);
        }
      }
    } else {
      const state = new Set(grid);
      if (panel.kind === "trajectory_2d" && panel.time) {
        if (grid.has(panel.time)) this.problem(`${where}: the time variable must differ from x and y`);
        state.add(panel.time);
      }
      const withState = new Set([...params, ...state]);
      const none: Ranges = new Map();
      nodes.x0 = this.expr(`${where} x0`, panel.x0, params);
      nodes.y0 = this.expr(`${where} y0`, panel.y0, params);
      if (panel.kind === "trajectory_2d") {
        nodes.dx = this.pointExpr(`${where} dx`, panel.dx, withState, none);
        nodes.dy = this.pointExpr(`${where} dy`, panel.dy, withState, none);
        nodes.t_max = this.expr(`${where} t_max`, panel.t_max, params);
        // Four stages a step, each reading dx and dy.
        work = 4 * (panel.steps ?? DEFAULT_TRAJECTORY_STEPS) * (this.cost(nodes.dx as FigureNode | null, none) + this.cost(nodes.dy as FigureNode | null, none));
      } else {
        nodes.fx = this.pointExpr(`${where} fx`, panel.fx, withState, none);
        nodes.fy = this.pointExpr(`${where} fy`, panel.fy, withState, none);
        work = (panel.n ?? DEFAULT_ITERATIONS) * (this.cost(nodes.fx as FigureNode | null, none) + this.cost(nodes.fy as FigureNode | null, none));
      }
    }
    this.work += work;
    if (this.work > MAX_PANEL_WORK) {
      this.problem(`${where}: the figure's panels need more computation than a figure may do (about ${this.work} expression steps; at most ${MAX_PANEL_WORK})`);
    }
    return nodes;
  }
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
export interface HeatmapGridData { label: string; x: number[]; y: number[]; z: Array<Array<number | null>>; contours: Array<{ level: number | null }> }
export interface HeatmapData extends HeatmapGridData { kind: "heatmap_2d" }
export interface VectorFieldData { kind: "vector_field_2d"; label: string; x: number[]; y: number[]; u: Array<Array<number | null>>; v: Array<Array<number | null>>; heatmap: HeatmapGridData | null }
export type PathStop = typeof STOP_LEFT | typeof STOP_NOT_FINITE | typeof STOP_OUTSIDE | null;
export interface TrajectoryData { kind: "trajectory_2d"; label: string; t: number[]; x: number[]; y: number[]; stopped: PathStop }
export interface IterateData { kind: "iterate_2d"; label: string; k: number[]; x: number[]; y: number[]; stopped: PathStop }
export type PanelData = FunctionPlotData | PmfBarsData | LinearMapData | ReadoutData | HeatmapData | VectorFieldData | TrajectoryData | IterateData;

/** cells + 1 samples from axis.min to axis.max (grid_points). */
export function gridPoints(axis: FigureAxis, cells: number): number[] {
  return Array.from({ length: cells + 1 }, (_, i) => canonical(axis.min + ((axis.max - axis.min) * i) / cells));
}

/** Rows by y, columns by x. */
function gridValues(node: FigureNode | null, xs: number[], ys: number[], xv: string, yv: string, env: Env, defs: Definitions): Array<Array<number | null>> {
  const scope: Env = newEnv(env);
  return ys.map((y) => {
    scope[yv] = y;
    return xs.map((x) => {
      scope[xv] = x;
      return num(value(node, scope, defs));
    });
  });
}

function heatmapData(node: FigureNode | null, contours: Array<FigureNode | null>, xs: number[], ys: number[], xv: string, yv: string, label: string, env: Env, defs: Definitions): HeatmapGridData {
  return { label, x: xs, y: ys, z: gridValues(node, xs, ys, xv, yv, env, defs), contours: contours.map((level) => ({ level: num(value(level, env, defs)) })) };
}

/** The window a path may stay in: the axis range padded by ESCAPE_MARGIN of its span. */
export function escapeBox(axis: FigureAxis): [number, number] {
  const pad = (axis.max - axis.min) * ESCAPE_MARGIN;
  return [axis.min - pad, axis.max + pad];
}

/** A trajectory (fixed-step RK4) or an iterated map, cut where it leaves its padded window or stops being finite. */
function pathData(model: TrajectoryPanel | IteratePanel, nodes: Record<string, unknown>, env: Env, defs: Definitions): TrajectoryData | IterateData {
  const xv = model.x.var;
  const yv = model.y.var;
  const [xLow, xHigh] = escapeBox(model.x);
  const [yLow, yHigh] = escapeBox(model.y);
  const trajectory = model.kind === "trajectory_2d";
  const time = model.kind === "trajectory_2d" ? model.time ?? null : null;
  const scope: Env = newEnv(env);
  const xs: number[] = [];
  const ys: number[] = [];
  const steps: number[] = [];
  let x = value(nodes.x0 as FigureNode | null, env, defs);
  let y = value(nodes.y0 as FigureNode | null, env, defs);
  const label = model.label ?? "";
  const done = (stopped: PathStop): TrajectoryData | IterateData => (trajectory
    ? { kind: "trajectory_2d", label, t: steps, x: xs, y: ys, stopped }
    : { kind: "iterate_2d", label, k: steps, x: xs, y: ys, stopped });
  if (!(Number.isFinite(x) && Number.isFinite(y))) return done(STOP_NOT_FINITE);
  if (!(xLow <= x && x <= xHigh && yLow <= y && y <= yHigh)) return done(STOP_OUTSIDE);
  xs.push(canonical(x));
  ys.push(canonical(y));
  steps.push(0);
  const rates = (px: number, py: number, pt: number, first: FigureNode | null, second: FigureNode | null): [number, number] => {
    scope[xv] = px;
    scope[yv] = py;
    if (time) scope[time] = pt;
    return [value(first, scope, defs), value(second, scope, defs)];
  };
  if (model.kind === "trajectory_2d") {
    const dx = nodes.dx as FigureNode | null;
    const dy = nodes.dy as FigureNode | null;
    const count = Math.trunc(model.steps ?? DEFAULT_TRAJECTORY_STEPS);
    const h = value(nodes.t_max as FigureNode | null, env, defs) / count;
    if (!(Number.isFinite(h) && h > 0)) return done(STOP_NOT_FINITE);
    const half = h / 2;
    let t = 0;
    for (let i = 0; i < count; i += 1) {
      const [k1x, k1y] = rates(x, y, t, dx, dy);
      const [k2x, k2y] = rates(x + half * k1x, y + half * k1y, t + half, dx, dy);
      const [k3x, k3y] = rates(x + half * k2x, y + half * k2y, t + half, dx, dy);
      const [k4x, k4y] = rates(x + h * k3x, y + h * k3y, t + h, dx, dy);
      const nx = x + (h / 6) * (k1x + 2 * k2x + 2 * k3x + k4x);
      const ny = y + (h / 6) * (k1y + 2 * k2y + 2 * k3y + k4y);
      t = h * (i + 1);
      if (!(Number.isFinite(nx) && Number.isFinite(ny))) return done(STOP_NOT_FINITE);
      if (!(xLow <= nx && nx <= xHigh && yLow <= ny && ny <= yHigh)) return done(STOP_LEFT);
      x = nx;
      y = ny;
      xs.push(canonical(x));
      ys.push(canonical(y));
      steps.push(canonical(t));
    }
    return done(null);
  }
  const fx = nodes.fx as FigureNode | null;
  const fy = nodes.fy as FigureNode | null;
  const count = Math.trunc(model.n ?? DEFAULT_ITERATIONS);
  for (let k = 0; k < count; k += 1) {
    const [nx, ny] = rates(x, y, 0, fx, fy);
    if (!(Number.isFinite(nx) && Number.isFinite(ny))) return done(STOP_NOT_FINITE);
    if (!(xLow <= nx && nx <= xHigh && yLow <= ny && ny <= yHigh)) return done(STOP_LEFT);
    x = nx;
    y = ny;
    xs.push(canonical(x));
    ys.push(canonical(y));
    steps.push(k + 1);
  }
  return done(null);
}

function evaluateAdvanced(panel: CompiledPanel, env: Env, defs: Definitions): PanelData {
  const model = panel.model as AdvancedPanel;
  const nodes = panel.nodes;
  if (model.kind === "heatmap_2d") {
    const xs = gridPoints(model.x, cellsOf(model, model.x));
    const ys = gridPoints(model.y, cellsOf(model, model.y));
    return { kind: "heatmap_2d", ...heatmapData(nodes.expr as FigureNode | null, (nodes.contours as Array<FigureNode | null>) ?? [], xs, ys, model.x.var, model.y.var, model.label ?? "", env, defs) };
  }
  if (model.kind === "vector_field_2d") {
    const xs = gridPoints(model.x, cellsOf(model, model.x));
    const ys = gridPoints(model.y, cellsOf(model, model.y));
    let overlay: HeatmapGridData | null = null;
    if (model.heatmap) {
      const side = overlayCells(model.heatmap);
      overlay = heatmapData(nodes.heatmap as FigureNode | null, (nodes.contours as Array<FigureNode | null>) ?? [], gridPoints(model.x, side), gridPoints(model.y, side), model.x.var, model.y.var, model.heatmap.label ?? "", env, defs);
    }
    return {
      kind: "vector_field_2d", label: model.label ?? "", x: xs, y: ys,
      u: gridValues(nodes.u as FigureNode | null, xs, ys, model.x.var, model.y.var, env, defs),
      v: gridValues(nodes.v as FigureNode | null, xs, ys, model.x.var, model.y.var, env, defs),
      heatmap: overlay,
    };
  }
  return pathData(model, nodes, env, defs);
}

export function evaluatePanel(compiled: CompiledFigure, panel: CompiledPanel, env: Env): PanelData {
  const defs = compiled.definitions;
  if (isAdvancedKind(panel.kind)) return evaluateAdvanced(panel, env, defs);
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

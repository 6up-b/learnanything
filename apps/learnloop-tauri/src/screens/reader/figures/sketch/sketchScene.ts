// Reader RW5d P2: SketchProgramV1 and the Scene, the desktop's half of both validators
// (spec_reader_show_me_figures_v1 §9.1; learnloop.figures.sketch is the sidecar's).
//
// Every view() result is validated here before anything is drawn (closed
// element kinds, a closed style palette, finite numbers everywhere, ids, the
// caps); the shared scene corpus (sketchSceneCorpus.json) keeps this and the
// Python validator agreeing on what can be drawn. Nothing in a Scene can be
// HTML, CSS, a URL or an image: the renderer draws SVG primitives and text
// nodes from these fields only.

export const SKETCH_MAX_ELEMENTS = 4_000;
export const SKETCH_MAX_POINTS = 40_000;
export const SKETCH_MAX_CELLS = 4_096;
export const SKETCH_MAX_SERIES = 4_000;
export const MAX_LABEL = 80;
export const MAX_VIEWPORT_SPAN = 1e12;
export const COLORS = ["series0", "series1", "series2", "series3", "muted", "accent"] as const;
export const ELEMENT_KINDS = ["polyline", "polygon", "points", "segment", "arrow", "circle", "rect", "text", "heat_cells", "handle"] as const;
/** The wording rule: an identifier that reaches a code-owned line can't carry a check word (sketch.py CHECK_WORDS). */
export const CHECK_WORDS = ["check", "verif", "learnloop", "sandbox", "book", "tested", "proof", "correct"] as const;
const ID = /^[A-Za-z][A-Za-z0-9_-]{0,39}$/;

export type SketchColor = (typeof COLORS)[number];
export type SketchStyle = { color?: SketchColor; dash?: boolean; width?: number; fill?: boolean; opacity?: number };
export type SketchElement =
  | { type: "polyline" | "polygon"; id?: string; x: number[]; y: number[]; style?: SketchStyle }
  | { type: "points"; id?: string; x: number[]; y: number[]; r?: number; style?: SketchStyle }
  | { type: "segment" | "arrow"; id?: string; x1: number; y1: number; x2: number; y2: number; style?: SketchStyle }
  | { type: "circle"; id?: string; cx: number; cy: number; r: number; style?: SketchStyle }
  | { type: "rect"; id?: string; x: number; y: number; w: number; h: number; style?: SketchStyle }
  | { type: "text"; id?: string; x: number; y: number; text: string; style?: SketchStyle }
  | { type: "heat_cells"; id?: string; x: [number, number]; y: [number, number]; cols: number; rows: number; values: number[]; style?: SketchStyle }
  | { type: "handle"; id: string; x: number; y: number; binds: { x?: string; y?: string } };
export type Scene = {
  viewport: { x: [number, number]; y: [number, number] };
  axes?: { x_label?: string; y_label?: string };
  elements: SketchElement[];
};

export type SketchParameter = { name: string; label: string; min: number; max: number; step: number; default: number; animate?: boolean };
export type SketchProbe = { name: string; label: string; shape: "scalar" | "series" | "pairs" };
export type SketchPrediction = {
  prompt: string;
  change: Record<string, number>;
  observe: { kind: "direction" | "choice"; probe: string; choices?: string[] };
};
export type SketchProgram = {
  program_version: "sketch-v1";
  demonstrates: string;
  parameters: SketchParameter[];
  clock?: { dt: number; t_max: number } | null;
  seeded?: boolean;
  code: string;
  probes: SketchProbe[];
  predictions?: SketchPrediction[];
  annotations?: Array<{ target: string; text: string }>;
};

/** The program as the server stored and verified it (its JSON text); null when unreadable. */
export function parseProgram(specJson: string | null | undefined): SketchProgram | null {
  if (!specJson) return null;
  try {
    const data = JSON.parse(specJson) as SketchProgram;
    if (data?.program_version !== "sketch-v1" || typeof data.code !== "string") return null;
    return { ...data, parameters: Array.isArray(data.parameters) ? data.parameters : [], probes: Array.isArray(data.probes) ? data.probes : [] };
  } catch {
    return null;
  }
}

/** How many clock steps reach t_max (0 without a clock). */
export function clockSteps(program: SketchProgram): number {
  const clock = program.clock;
  if (!clock) return 0;
  return Math.max(1, Math.ceil(clock.t_max / clock.dt - 1e-9));
}

export function impersonates(name: string): boolean {
  const folded = String(name).toLowerCase();
  return CHECK_WORDS.some((word) => folded.includes(word));
}

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function describe(value: unknown): string {
  if (value === "NaN" || value === "Infinity" || value === "-Infinity") return value;
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value === "number") return String(value);
  if (value === null || value === undefined) return "NoneType";
  if (Array.isArray(value)) return "list";
  if (typeof value === "string") return "str";
  return typeof value === "object" ? "dict" : "object";
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function keys(value: Record<string, unknown>): string[] {
  return Object.keys(value);
}

class Problems {
  readonly items: string[] = [];
  add(text: string) {
    if (this.items.length < 12) this.items.push(text);
  }
}

function numbers(problems: Problems, where: string, value: unknown, limit: number): number[] | null {
  if (!Array.isArray(value)) {
    problems.add(`${where} must be a list of numbers`);
    return null;
  }
  if (value.length > limit) {
    problems.add(`${where} has ${value.length} values, more than ${limit}`);
    return null;
  }
  for (let index = 0; index < value.length; index += 1) {
    if (!finite(value[index])) {
      problems.add(`${where}[${index}] is not a finite number (${describe(value[index])})`);
      return null;
    }
  }
  return value as number[];
}

const STYLE_KEYS = new Set(["color", "dash", "width", "fill", "opacity"]);
const COMMON = ["type", "id", "style"];
const ELEMENT_KEYS: Record<string, Set<string>> = {
  polyline: new Set([...COMMON, "x", "y"]),
  polygon: new Set([...COMMON, "x", "y"]),
  points: new Set([...COMMON, "x", "y", "r"]),
  segment: new Set([...COMMON, "x1", "y1", "x2", "y2"]),
  arrow: new Set([...COMMON, "x1", "y1", "x2", "y2"]),
  circle: new Set([...COMMON, "cx", "cy", "r"]),
  rect: new Set([...COMMON, "x", "y", "w", "h"]),
  text: new Set([...COMMON, "x", "y", "text"]),
  heat_cells: new Set([...COMMON, "x", "y", "cols", "rows", "values"]),
  handle: new Set(["type", "id", "x", "y", "binds"]),
};

/** Why a view() result can't be drawn (none: drawable). Mirrors sketch.py's scene_problems. */
export function sceneProblems(scene: unknown, parameters: readonly string[] = []): string[] {
  const problems = new Problems();
  if (!isPlainObject(scene)) return ["view() must return an object {viewport, elements}"];
  const extra = keys(scene).filter((key) => !["viewport", "elements", "axes"].includes(key)).sort();
  if (extra.length) problems.add(`the scene has unknown keys ${JSON.stringify(extra)}`);
  const viewport = scene.viewport;
  if (!isPlainObject(viewport) || keys(viewport).length !== 2 || !("x" in viewport) || !("y" in viewport)) {
    problems.add("viewport must be {x: [min, max], y: [min, max]}");
  } else {
    for (const axis of ["x", "y"] as const) {
      const pair = numbers(problems, `viewport.${axis}`, viewport[axis], 2);
      if (pair !== null && (pair.length !== 2 || !(pair[0] < pair[1]) || pair[1] - pair[0] > MAX_VIEWPORT_SPAN)) {
        problems.add(`viewport.${axis} must be [min, max] with min < max`);
      }
    }
  }
  const axes = scene.axes;
  if (axes !== undefined) {
    if (!isPlainObject(axes) || keys(axes).some((key) => key !== "x_label" && key !== "y_label")) {
      problems.add("axes may have only x_label and y_label");
    } else {
      for (const [key, value] of Object.entries(axes)) {
        if (typeof value !== "string" || value.length > MAX_LABEL) problems.add(`axes.${key} must be text of at most ${MAX_LABEL} characters`);
      }
    }
  }
  const elements = scene.elements;
  if (!Array.isArray(elements)) {
    problems.add("elements must be a list");
    return problems.items;
  }
  if (elements.length > SKETCH_MAX_ELEMENTS) {
    problems.add(`the scene has ${elements.length} elements, more than ${SKETCH_MAX_ELEMENTS}`);
    return problems.items;
  }
  const known = new Set(parameters);
  const ids = new Set<string>();
  let points = 0;
  for (let index = 0; index < elements.length; index += 1) {
    if (problems.items.length >= 12) break;
    const element = elements[index];
    let where = `element ${index}`;
    if (!isPlainObject(element)) {
      problems.add(`${where} is not an object`);
      continue;
    }
    const kind = element.type;
    if (typeof kind !== "string" || !Object.prototype.hasOwnProperty.call(ELEMENT_KEYS, kind)) {
      problems.add(`${where}: type '${(kind === undefined || kind === null ? "None" : String(kind)).slice(0, 40)}' is not one of ${ELEMENT_KINDS.join(", ")}`);
      continue;
    }
    where = `element ${index} (${kind})`;
    const extraKeys = keys(element).filter((key) => !ELEMENT_KEYS[kind].has(key)).sort();
    if (extraKeys.length) {
      problems.add(`${where}: unknown keys ${JSON.stringify(extraKeys)}`);
      continue;
    }
    const id = element.id;
    if (id !== undefined || kind === "handle") {
      if (typeof id !== "string" || !ID.test(id) || impersonates(id)) {
        problems.add(`${where}: id must be letters, digits, - and _ (at most 40), and may not use LearnLoop's check words`);
      } else if (ids.has(id)) {
        problems.add(`${where}: id '${id}' is used twice`);
      } else {
        ids.add(id);
      }
    }
    const style = element.style;
    if (style !== undefined) {
      if (!isPlainObject(style) || keys(style).some((key) => !STYLE_KEYS.has(key))) {
        problems.add(`${where}: style may have only color, dash, fill, opacity, width`);
      } else {
        if ("color" in style && !(COLORS as readonly unknown[]).includes(style.color)) problems.add(`${where}: color must be one of ${COLORS.join(", ")}`);
        if ("width" in style && !(finite(style.width) && style.width > 0 && style.width <= 3)) problems.add(`${where}: width must be in (0, 3]`);
        if ("opacity" in style && !(finite(style.opacity) && style.opacity >= 0 && style.opacity <= 1)) problems.add(`${where}: opacity must be in [0, 1]`);
        for (const flag of ["dash", "fill"]) {
          if (flag in style && typeof style[flag] !== "boolean") problems.add(`${where}: ${flag} must be true or false`);
        }
      }
    }
    const need = (...names: string[]) => {
      for (const name of names) {
        if (!finite(element[name])) problems.add(`${where}.${name} is not a finite number (${describe(element[name])})`);
      }
    };
    if (kind === "polyline" || kind === "polygon" || kind === "points") {
      const xs = numbers(problems, `${where}.x`, element.x, SKETCH_MAX_POINTS);
      const ys = numbers(problems, `${where}.y`, element.y, SKETCH_MAX_POINTS);
      if (xs && ys) {
        if (xs.length !== ys.length) problems.add(`${where}: x and y have different lengths`);
        points += xs.length;
      }
      if (kind === "points" && "r" in element && !(finite(element.r) && element.r > 0 && element.r <= 12)) {
        problems.add(`${where}: r must be in (0, 12] (pixels)`);
      }
    } else if (kind === "segment" || kind === "arrow") {
      need("x1", "y1", "x2", "y2");
      points += 2;
    } else if (kind === "circle") {
      need("cx", "cy", "r");
      if (finite(element.r) && element.r < 0) problems.add(`${where}: r must not be negative`);
      points += 1;
    } else if (kind === "rect") {
      need("x", "y", "w", "h");
      if ((finite(element.w) && element.w < 0) || (finite(element.h) && element.h < 0)) problems.add(`${where}: w and h must not be negative`);
      points += 2;
    } else if (kind === "text") {
      need("x", "y");
      const text = element.text;
      if (typeof text !== "string" || !text || text.length > MAX_LABEL) problems.add(`${where}: text must be 1-${MAX_LABEL} characters`);
      points += 1;
    } else if (kind === "heat_cells") {
      for (const axis of ["x", "y"]) {
        const pair = numbers(problems, `${where}.${axis}`, element[axis], 2);
        if (pair !== null && (pair.length !== 2 || !(pair[0] < pair[1]))) problems.add(`${where}.${axis} must be [min, max]`);
      }
      const cols = element.cols;
      const rows = element.rows;
      if (!(Number.isInteger(cols) && Number.isInteger(rows) && (cols as number) >= 1 && (rows as number) >= 1
        && (cols as number) * (rows as number) <= SKETCH_MAX_CELLS)) {
        problems.add(`${where}: cols and rows must be whole numbers with at most ${SKETCH_MAX_CELLS} cells`);
      } else {
        const values = numbers(problems, `${where}.values`, element.values, SKETCH_MAX_CELLS);
        if (values && values.length !== (cols as number) * (rows as number)) problems.add(`${where}: values must have cols * rows entries`);
        points += (cols as number) * (rows as number);
      }
    } else {
      need("x", "y");
      const binds = element.binds;
      if (!isPlainObject(binds) || !keys(binds).length || keys(binds).some((key) => key !== "x" && key !== "y")) {
        problems.add(`${where}: binds must be {x?: parameter, y?: parameter}`);
      } else {
        for (const [axis, name] of Object.entries(binds)) {
          if (typeof name !== "string" || !known.has(name)) problems.add(`${where}: binds.${axis} must name a parameter`);
        }
      }
      points += 1;
    }
    if (points > SKETCH_MAX_POINTS) {
      problems.add(`the scene draws more than ${SKETCH_MAX_POINTS} points`);
      break;
    }
  }
  return problems.items;
}

/** Why a probes() result does not match the declared probes (undeclared names are ignored, never shown). */
export function probeProblems(values: unknown, probes: readonly SketchProbe[]): string[] {
  const problems = new Problems();
  if (!isPlainObject(values)) return ["probes() must return an object of the declared probes"];
  for (const probe of probes) {
    if (!Object.prototype.hasOwnProperty.call(values, probe.name)) {
      problems.add(`probe '${probe.name}' is missing`);
      continue;
    }
    const value = values[probe.name];
    if (probe.shape === "scalar") {
      if (!finite(value)) problems.add(`probe '${probe.name}' is not a finite number (${describe(value)})`);
    } else if (probe.shape === "series") {
      numbers(problems, `probe '${probe.name}'`, value, SKETCH_MAX_SERIES);
    } else if (!Array.isArray(value) || value.length > SKETCH_MAX_SERIES) {
      problems.add(`probe '${probe.name}' must be a list of [x, y] pairs (at most ${SKETCH_MAX_SERIES})`);
    } else {
      for (let index = 0; index < value.length; index += 1) {
        const pair = value[index];
        if (!(Array.isArray(pair) && pair.length === 2 && finite(pair[0]) && finite(pair[1]))) {
          problems.add(`probe '${probe.name}'[${index}] is not a pair of finite numbers`);
          break;
        }
      }
    }
  }
  return problems.items;
}

// Reader RW5d P2: the sketch Worker's protocol, validated at runtime on both
// sides (spec_reader_show_me_figures_v1 §9.3; fix round 4, the independent
// sandbox review's finding 3).
//
// Four operations and nothing else: load, init, step, read. The Worker
// refuses an unknown operation, a malformed argument or an out-of-bounds
// count before the engine is touched (never a fallback to a read); the client
// (sketchRunner.portRunner) refuses a reply whose shape is not the one its
// request expects. The hostile sketch can't send these messages at all (its
// realm is inside wasm, and a Worker's postMessage answers only its owner):
// this bounds a future caller's mistakes, and it is the shape a private
// channel to an opaque-origin frame would use (G-SM14's fallback).
import { sceneDigest, SketchRunError, STATUS_NAMES, type SketchEngineHost, type SketchErrorKind } from "./sketchEngine";

/** keep (machine safety): the program's size cap (sketch.py SKETCH_MAX_SOURCE_BYTES). */
export const SKETCH_MAX_SOURCE_BYTES = 32_768;
/** keep (operational): the most clock steps (sketch.py SKETCH_MAX_CLOCK_STEPS). */
export const SKETCH_MAX_CLOCK_STEPS = 2_000;
/** keep (schema): the most parameters a figure declares (spec.py MAX_PARAMETERS). */
export const SKETCH_MAX_PARAMETERS = 4;
/** keep (display): the longest error message a reply may carry. */
export const REPLY_MESSAGE_MAX = 600;

export const WORKER_OPS = ["load", "init", "step", "read"] as const;
export type WorkerOp = (typeof WORKER_OPS)[number];
export type WorkerRequest = { id: number; op: WorkerOp; args: unknown[] };
export type SketchRead = { scene: unknown; probes: unknown; digest: string };
export type WorkerResponse =
  | { id: number; ok: true; result: unknown }
  | { id: number; ok: false; error: { kind: SketchErrorKind; message: string } };

const PARAMETER_NAME = /^[A-Za-z][A-Za-z0-9_]{0,31}$/;
const DIGEST = /^[0-9a-f]{32}$/;
const KINDS = new Set<string>([...STATUS_NAMES, "trap", "scene", "probe", "paused"]);
const ENTRY_POINTS = ["init", "step", "view", "probes"] as const;

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
const isId = (value: unknown): value is number => Number.isSafeInteger(value) && (value as number) >= 1;
const isIndex = (value: unknown): value is number =>
  Number.isSafeInteger(value) && (value as number) >= 0 && (value as number) <= SKETCH_MAX_CLOCK_STEPS;

function paramsProblem(value: unknown): string | null {
  if (!isObject(value)) return "the parameters are not an object";
  const names = Object.keys(value);
  if (names.length > SKETCH_MAX_PARAMETERS) return `more than ${SKETCH_MAX_PARAMETERS} parameters`;
  for (const name of names) {
    if (!PARAMETER_NAME.test(name)) return "a parameter name is not a name";
    const item = value[name];
    if (typeof item !== "number" || !Number.isFinite(item)) return `parameter ${name} is not a finite number`;
  }
  return null;
}

function argsProblem(op: WorkerOp, args: unknown[]): string | null {
  if (op === "load") {
    if (args.length !== 1 || typeof args[0] !== "string") return "load takes the program's text";
    if (new TextEncoder().encode(args[0]).length > SKETCH_MAX_SOURCE_BYTES) return "the program is too long";
    return null;
  }
  if (op === "init") {
    if (args.length !== 2) return "init takes the parameters and a seed";
    const seed = args[1];
    if (!Number.isSafeInteger(seed) || (seed as number) < 0 || (seed as number) > 0xffffffff) return "the seed is not a 32-bit whole number";
    return paramsProblem(args[0]);
  }
  if (op === "step") {
    if (args.length !== 4) return "step takes the parameters, dt, an index and a count";
    const [, dt, index, count] = args;
    if (typeof dt !== "number" || !Number.isFinite(dt) || dt <= 0) return "dt is not a positive number";
    if (!isIndex(index)) return "the step index is out of bounds";
    if (!Number.isSafeInteger(count) || (count as number) < 1 || (index as number) + (count as number) > SKETCH_MAX_CLOCK_STEPS) {
      return "the step count is out of bounds";
    }
    return paramsProblem(args[0]);
  }
  if (args.length !== 2) return "read takes the parameters and a step index";
  if (!isIndex(args[1])) return "the step index is out of bounds";
  return paramsProblem(args[0]);
}

/** A request as the Worker accepts it, or why not (and the id to answer, 0 when it has none). */
export function parseWorkerRequest(data: unknown): { ok: true; request: WorkerRequest } | { ok: false; id: number; message: string } {
  if (!isObject(data)) return { ok: false, id: 0, message: "the request is not an object" };
  const id = isId(data.id) ? data.id : 0;
  if (!id) return { ok: false, id, message: "the request has no id" };
  if (typeof data.op !== "string" || !(WORKER_OPS as readonly string[]).includes(data.op)) {
    return { ok: false, id, message: "unknown operation" };
  }
  if (!Array.isArray(data.args)) return { ok: false, id, message: "the arguments are not a list" };
  const op = data.op as WorkerOp;
  const problem = argsProblem(op, data.args);
  if (problem) return { ok: false, id, message: problem };
  return { ok: true, request: { id, op, args: data.args } };
}

/** The Worker's side: validate, run on the engine host, answer (never throws). */
export async function answerRequest(host: () => Promise<SketchEngineHost>, data: unknown): Promise<WorkerResponse> {
  const parsed = parseWorkerRequest(data);
  if (!parsed.ok) return { id: parsed.id, ok: false, error: { kind: "input", message: parsed.message } };
  const { id, op, args } = parsed.request;
  try {
    const sketch = await host();
    const params = args[0] as Record<string, number>;
    if (op === "load") return { id, ok: true, result: sketch.load(args[0] as string) };
    if (op === "init") {
      sketch.init(params, args[1] as number);
      return { id, ok: true, result: null };
    }
    if (op === "step") {
      sketch.step(params, args[1] as number, args[2] as number, args[3] as number);
      return { id, ok: true, result: null };
    }
    const { sceneText, probesText } = sketch.readText(params, args[1] as number);
    const read: SketchRead = { scene: JSON.parse(sceneText), probes: JSON.parse(probesText), digest: sceneDigest(sceneText, probesText) };
    return { id, ok: true, result: read };
  } catch (caught) {
    const error = caught instanceof SketchRunError
      ? { kind: caught.kind, message: caught.message }
      : { kind: "error" as const, message: caught instanceof Error ? caught.message : String(caught) };
    return { id, ok: false, error: { kind: error.kind, message: error.message.slice(0, REPLY_MESSAGE_MAX) } };
  }
}

/** The client's side: a reply's id, and its result or error checked against the request's operation;
 *  null when it can't be routed (not an object, or no id). */
export function parseWorkerReply(data: unknown, expected: (id: number) => WorkerOp | undefined):
  { id: number; ok: true; result: unknown } | { id: number; ok: false; error: SketchRunError } | null {
  if (!isObject(data) || !isId(data.id)) return null;
  const id = data.id;
  const op = expected(id);
  if (!op) return null;
  const malformed = { id, ok: false as const, error: new SketchRunError("error", "the sketch engine's reply was malformed") };
  if (data.ok === false) {
    if (!isObject(data.error)) return malformed;
    const kind = typeof data.error.kind === "string" && KINDS.has(data.error.kind) ? (data.error.kind as SketchErrorKind) : "error";
    const message = typeof data.error.message === "string" ? data.error.message.slice(0, REPLY_MESSAGE_MAX) : "error";
    return { id, ok: false, error: new SketchRunError(kind, message) };
  }
  if (data.ok !== true) return malformed;
  const result = data.result;
  if (op === "init" || op === "step") return result === null || result === undefined ? { id, ok: true, result: undefined } : malformed;
  if (op === "load") {
    if (!isObject(result) || Object.keys(result).some((key) => !(ENTRY_POINTS as readonly string[]).includes(key))
      || ENTRY_POINTS.some((key) => typeof result[key] !== "boolean")) return malformed;
    return { id, ok: true, result };
  }
  if (!isObject(result) || !("scene" in result) || !("probes" in result) || typeof result.digest !== "string" || !DIGEST.test(result.digest)) {
    return malformed;
  }
  return { id, ok: true, result: { scene: result.scene, probes: result.probes, digest: result.digest } };
}

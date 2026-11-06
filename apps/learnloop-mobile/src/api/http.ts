// The phone's transport (spec §3.4, §6.2): every request is one `POST /rpc` or a status GET, and a
// refusal is the `CommandError` the desktop client already works with. No Tauri anywhere.
//
// Mobile v2 §4.4, §4.5, §5.2: each exchange also tells the connection line what it showed, and
// each `/rpc` round trip is measured. This phone's time and the host's `Server-Timing` total go
// back to the host on the next `/rpc`, for `learnloop-mobile report`. Nothing else changes here:
// the retry policy, the 202, the 401 rule and `OFFLINE` are M2a's.
import type { CommandError } from "@desktop/api/dto";
import { markGradingDown, markGradingUp, markOffline, markReachable, markStale } from "../shell/connection";
import { deleteCredential, readCredential } from "../store/credential";
import { clearDisplayCache } from "../store/displayCache";
import { clearSessionCache } from "../store/sessionCache";
import type { PhoneMethod } from "./phoneMethods";
import policy from "./retryPolicy.json";

export interface AcceptedJob {
  readonly jobId: string;
  readonly requestId: string;
  readonly state: string;
}

export type RpcOutcome<T> = { readonly kind: "result"; readonly result: T } | { readonly kind: "accepted"; readonly accepted: AcceptedJob };

const RETRY_SAFE = new Set<string>(policy.retrySafe);
/** §6.2's automatic retry: only a retryable error on a retry-safe method. A `keep` bound: past this, the learner sees it. */
const MAX_RETRIES = 3;
const RETRY_BASE_MS = 500;

export function isRetrySafe(method: string): boolean {
  return RETRY_SAFE.has(method);
}

export const OFFLINE: CommandError = {
  code: "desktop_offline",
  message: "The desktop isn't reachable.",
  retryable: true
};

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/** The two statuses Serve answers itself when the host behind it is down. */
const GATEWAY_DOWN = new Set([502, 504]);
/** The host's own "busy, try again" answers (§4.4's *Desktop is busy*). */
const BUSY_CODES = new Set(["host_busy", "database_busy"]);
/** The answers that carry a fresh grade: one of them means grading is back (§4.4). */
const GRADING_METHODS = new Set<string>(["submit_attempt", "submit_dont_know", "answer_grading_clarification"]);

/** The header the host reads a round trip from (`learnloop_mobile.host.CLIENT_TIMING_HEADER`). */
export const CLIENT_TIMING_HEADER = "LearnLoop-Client-Timing";

interface TimingSample {
  readonly method: string;
  readonly status: number;
  readonly ms: number;
  readonly hostMs: number | null;
}

/** The last measured round trip, sent on the next `/rpc` and then forgotten: one at a time, by design. */
let pendingSample: TimingSample | null = null;

/** `total;dur=…` from a `Server-Timing` header, in ms, or null. */
export function serverTimingTotal(header: string | null): number | null {
  if (!header) return null;
  for (const part of header.split(",")) {
    const [name, ...params] = part.trim().split(";");
    if (name.trim() !== "total") continue;
    for (const param of params) {
      const [key, value] = param.trim().split("=");
      if (key === "dur" && value !== undefined && Number.isFinite(Number(value))) return Number(value);
    }
  }
  return null;
}

function sampleHeader(sample: TimingSample): string {
  const ms = (value: number) => Math.max(0, value).toFixed(1);
  return `${sample.method};status=${sample.status};dur=${ms(sample.ms)}${sample.hostMs !== null ? `;host=${ms(sample.hostMs)}` : ""}`;
}

/** What the next request will carry, for tests. */
export function pendingTimingSample(): TimingSample | null {
  return pendingSample;
}

export function resetTimingForTests(): void {
  pendingSample = null;
}

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

async function authorizedFetch(input: string, init: RequestInit): Promise<Response> {
  const credential = await readCredential();
  if (!credential) throw { code: "not_paired", message: "This phone isn't paired yet.", retryable: false } satisfies CommandError;
  let response: Response;
  try {
    response = await fetch(input, {
      ...init,
      credentials: "omit",
      cache: "no-store",
      headers: { ...(init.headers ?? {}), Authorization: `Bearer ${credential.token}` }
    });
  } catch {
    markOffline();
    throw OFFLINE;
  }
  if (GATEWAY_DOWN.has(response.status)) {
    markOffline();
    throw OFFLINE;
  }
  if (response.status !== 503) markReachable();
  if (response.status === 401) {
    // §4.4: the token, the session cache and the display cache go; the outbox stays for the next token.
    await deleteCredential();
    clearSessionCache();
    await clearDisplayCache().catch(() => undefined);
    throw { code: "unauthorized", message: "This phone needs to be paired again.", retryable: false } satisfies CommandError;
  }
  return response;
}

async function errorFrom(response: Response): Promise<CommandError> {
  try {
    const body = await response.json();
    if (body && typeof body === "object" && body.error && typeof body.error.code === "string") {
      return body.error as CommandError;
    }
  } catch {
    /* a body that is not ours */
  }
  return { code: "internal", message: "The desktop answered with something unexpected.", retryable: false };
}

/** What an error says about the connection line, as it passes. */
function noteError(error: CommandError, status: number): void {
  if (status === 503) markReachable(BUSY_CODES.has(error.code));
  if (error.code === "grading_fallback_required") markGradingDown();
  // A method this build names and the host does not: the host moved on (§5.2).
  if (error.code === "method_not_allowed") markStale();
}

/** One `/rpc` exchange, with no retry. A 202 is a job to poll, never a result (§3.4). */
export async function rpcOnce<T>(method: PhoneMethod, params: unknown, requestId?: string): Promise<RpcOutcome<T>> {
  const sample = pendingSample;
  pendingSample = null;
  const started = now();
  const response = await authorizedFetch("/rpc", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(sample ? { [CLIENT_TIMING_HEADER]: sampleHeader(sample) } : {}) },
    body: JSON.stringify({ method, params: params ?? {}, ...(requestId ? { request_id: requestId } : {}) })
  });
  pendingSample = { method, status: response.status, ms: now() - started, hostMs: serverTimingTotal(response.headers.get("Server-Timing")) };
  if (!response.ok) {
    const error = await errorFrom(response);
    noteError(error, response.status);
    throw error;
  }
  const body = await response.json();
  if (response.status === 202) {
    const accepted = body.accepted as { job_id: string; request_id: string; state: string };
    return { kind: "accepted", accepted: { jobId: accepted.job_id, requestId: accepted.request_id, state: accepted.state } };
  }
  if (GRADING_METHODS.has(method)) markGradingUp();
  return { kind: "result", result: body.result as T };
}

/** `rpcOnce` under §6.2's retry policy. */
export async function rpcOutcome<T>(method: PhoneMethod, params: unknown, requestId?: string): Promise<RpcOutcome<T>> {
  for (let attempt = 0; ; attempt += 1) {
    try {
      return await rpcOnce<T>(method, params, requestId);
    } catch (error) {
      const command = error as CommandError;
      if (!command.retryable || !RETRY_SAFE.has(method) || attempt >= MAX_RETRIES) throw error;
      // A provider outage waits for the learner, not for this loop.
      if (command.code === "grading_fallback_required") throw error;
      await sleep(RETRY_BASE_MS * 2 ** attempt);
    }
  }
}

/** A short method: `call(command, args)`, the desktop's shape. Only an allowlisted name type-checks. */
export async function call<T>(method: PhoneMethod, params: unknown = {}): Promise<T> {
  const outcome = await rpcOutcome<T>(method, params);
  if (outcome.kind === "accepted") throw new Error(`${method} is not a short method.`);
  return outcome.result;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await authorizedFetch(path, { method: "GET" });
  if (!response.ok) {
    const error = await errorFrom(response);
    noteError(error, response.status);
    throw error;
  }
  return (await response.json()) as T;
}

/** §6.3's polling interval, and a terminal state ends it. */
export const JOB_POLL_MS = 2000;

/**
 * `failed`: no attempt committed under this key, so it may be replaced. `recorded`: the attempt
 * committed and its completion hasn't finished, so its key is spent and `attempt_id` opens its feedback.
 */
export interface JobState<T> {
  readonly state: "accepted" | "running" | "completed" | "failed" | "recorded" | "unknown";
  readonly result?: T;
  readonly error?: CommandError;
  readonly attempt_id?: string;
}

/**
 * Did the host say it refused this write, or could it have gone through? No reply, a reply that isn't
 * ours and the host's own `internal` don't say. Every other typed error is a refusal.
 */
export function refusedOutright(error: unknown): boolean {
  const code = (error as CommandError | undefined)?.code;
  return typeof code === "string" && code !== "desktop_offline" && code !== "internal";
}

/** The attempt a `submission_committed` refusal names: `/rpc`'s word, and a polled job's, for `recorded`. */
export function committedAttempt(error: unknown): string | null {
  const command = error as CommandError | undefined;
  if (command?.code !== "submission_committed") return null;
  const attempt = (command.details as { attempt_id?: unknown } | undefined)?.attempt_id;
  return typeof attempt === "string" ? attempt : null;
}

/**
 * Poll one job to its end. A phone that loses the desktop keeps polling: a backgrounded or offline
 * phone resumes when it comes back, which is the point of the job (A4). Only a terminal state or
 * `isCancelled` ends this.
 */
export async function pollJob<T>(jobId: string, isCancelled: () => boolean = () => false): Promise<T> {
  for (;;) {
    if (isCancelled()) throw { code: "cancelled", message: "Stopped waiting.", retryable: false } satisfies CommandError;
    try {
      const job = await getJson<JobState<T>>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);
      if (job.state === "completed") return job.result as T;
      if (job.state === "failed" || job.state === "recorded") {
        if (job.error?.code === "grading_fallback_required") markGradingDown();
        throw job.error ?? ({ code: "internal", message: "The request failed.", retryable: false } satisfies CommandError);
      }
    } catch (error) {
      const code = (error as CommandError).code;
      if (code !== "desktop_offline" && code !== "database_busy" && code !== "host_busy") throw error;
    }
    await sleep(JOB_POLL_MS);
  }
}

/** A long method to its end: the 15 s wait, then the job. `onAccepted` is told before polling starts. */
export async function runLong<T>(
  method: PhoneMethod,
  params: unknown,
  requestId: string,
  options: { onAccepted?: (job: AcceptedJob) => void; isCancelled?: () => boolean } = {}
): Promise<T> {
  const outcome = await rpcOutcome<T>(method, params, requestId);
  if (outcome.kind === "result") return outcome.result;
  options.onAccepted?.(outcome.accepted);
  const result = await pollJob<T>(outcome.accepted.jobId, options.isCancelled);
  if (GRADING_METHODS.has(method)) markGradingUp();
  return result;
}

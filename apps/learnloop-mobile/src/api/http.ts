// The phone's transport (spec §3.4, §6.2): every request is one `POST /rpc` or a status GET, and a
// refusal is the `CommandError` the desktop client already works with. No Tauri anywhere.
import type { CommandError } from "@desktop/api/dto";
import { deleteCredential, readCredential } from "../store/credential";
import { clearSessionCache } from "../store/sessionCache";
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
    throw OFFLINE;
  }
  if (GATEWAY_DOWN.has(response.status)) throw OFFLINE;
  if (response.status === 401) {
    // §4.4: the token and the session cache go; the outbox stays for the next token.
    await deleteCredential();
    clearSessionCache();
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

/** One `/rpc` exchange, with no retry. A 202 is a job to poll, never a result (§3.4). */
export async function rpcOnce<T>(method: string, params: unknown, requestId?: string): Promise<RpcOutcome<T>> {
  const response = await authorizedFetch("/rpc", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method, params: params ?? {}, ...(requestId ? { request_id: requestId } : {}) })
  });
  if (!response.ok) throw await errorFrom(response);
  const body = await response.json();
  if (response.status === 202) {
    const accepted = body.accepted as { job_id: string; request_id: string; state: string };
    return { kind: "accepted", accepted: { jobId: accepted.job_id, requestId: accepted.request_id, state: accepted.state } };
  }
  return { kind: "result", result: body.result as T };
}

/** `rpcOnce` under §6.2's retry policy. */
export async function rpcOutcome<T>(method: string, params: unknown, requestId?: string): Promise<RpcOutcome<T>> {
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

/** A short method: `call(command, args)`, the desktop's shape. */
export async function call<T>(method: string, params: unknown = {}): Promise<T> {
  const outcome = await rpcOutcome<T>(method, params);
  if (outcome.kind === "accepted") throw new Error(`${method} is not a short method.`);
  return outcome.result;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await authorizedFetch(path, { method: "GET" });
  if (!response.ok) throw await errorFrom(response);
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
      if (job.state === "failed" || job.state === "recorded") throw job.error ?? ({ code: "internal", message: "The request failed.", retryable: false } satisfies CommandError);
    } catch (error) {
      const code = (error as CommandError).code;
      if (code !== "desktop_offline" && code !== "database_busy" && code !== "host_busy") throw error;
    }
    await sleep(JOB_POLL_MS);
  }
}

/** A long method to its end: the 15 s wait, then the job. `onAccepted` is told before polling starts. */
export async function runLong<T>(
  method: string,
  params: unknown,
  requestId: string,
  options: { onAccepted?: (job: AcceptedJob) => void; isCancelled?: () => boolean } = {}
): Promise<T> {
  const outcome = await rpcOutcome<T>(method, params, requestId);
  if (outcome.kind === "result") return outcome.result;
  options.onAccepted?.(outcome.accepted);
  return pollJob<T>(outcome.accepted.jobId, options.isCancelled);
}

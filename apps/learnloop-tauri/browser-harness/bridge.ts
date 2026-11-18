// The walk bridge's HTTP surface, shared by the shims. The bridge serves this
// bundle itself, so every path is same-origin and relative.

export const BRIDGE = "/__bridge";

export type BridgeError = { code: string; message: string; retryable: boolean; details?: unknown };

export async function post<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BRIDGE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
  } catch (error) {
    // The bridge itself is gone: the same words the shell uses for a dead sidecar.
    throw {
      code: "sidecar_unavailable",
      message: "LearnLoop's local service is unavailable. Retry the action; if it keeps failing, restart the app.",
      retryable: true,
      details: { harness: "bridge_unreachable", diagnostic: String(error) },
    } satisfies BridgeError;
  }
  const envelope = (await response.json()) as { ok: boolean; result?: T; error?: BridgeError };
  if (!envelope.ok) throw envelope.error;
  return envelope.result as T;
}

/** A harness-only refusal, worded for the person at the screen. */
export function unavailable(what: string): BridgeError {
  return {
    code: "browser_mode_unavailable",
    message: `${what} is not available in browser mode (the UX walk harness).`,
    retryable: false,
  };
}

/** Tell the bridge about a shell call that has no sidecar method (logged for the analyst). */
export function note(kind: string, detail: Record<string, unknown> = {}): void {
  void post("/note", { kind, ...detail }).catch(() => undefined);
}

// Plan-first transport T1 (owner decision 2026-10-21): when the ChatGPT plan
// can't serve a feature (signed out, paused, usage limit, a refused token),
// the feature shows its own "unavailable" state AND LearnLoop asks whether to
// use OpenRouter instead. The sidecar attaches a typed hint to the RPC's
// error details (`fallback_available: "openrouter"`, `fallback_tasks`,
// `fallback_profile`) or to a degraded result (camelCase). This store keeps
// the latest offer so one shell banner can show it; nothing is sent to
// OpenRouter until the learner chooses "Use OpenRouter instead".

export interface PlanFallbackOffer {
  provider: "openrouter";
  profile: string;
  tasks: string[];
  /** The plan needs a sign-in: "Continue with ChatGPT" is offered too. */
  planSignedOut: boolean;
}

type Listener = (offer: PlanFallbackOffer | null) => void;

let current: PlanFallbackOffer | null = null;
const listeners = new Set<Listener>();

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === "string" && entry !== "") : [];
}

function fromRecord(record: Record<string, unknown>): PlanFallbackOffer | null {
  const kind = record.fallback_available ?? record.fallbackAvailable;
  if (kind !== "openrouter") return null;
  const tasks = stringList(record.fallback_tasks ?? record.fallbackTasks);
  if (tasks.length === 0) return null;
  const profile = record.fallback_profile ?? record.fallbackProfile;
  const signedOut = (record.plan_signed_out ?? record.planSignedOut) === true;
  return {
    provider: "openrouter",
    profile: typeof profile === "string" && profile ? profile : "openrouter",
    tasks,
    planSignedOut: signedOut
  };
}

/** The offer an RPC error (its details) or result carries, or null. */
export function extractFallbackOffer(value: unknown): PlanFallbackOffer | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  const details = record.details;
  if (details && typeof details === "object") {
    const fromDetails = fromRecord(details as Record<string, unknown>);
    if (fromDetails) return fromDetails;
  }
  return fromRecord(record);
}

/** Publish the offer an RPC response carries (no-op without one). */
export function noteFallbackOffer(value: unknown): void {
  const offer = extractFallbackOffer(value);
  if (!offer) return;
  if (current) {
    // Several features may ask during one outage: one banner names them all.
    const tasks = Array.from(new Set([...current.tasks, ...offer.tasks])).sort();
    current = { ...offer, tasks, planSignedOut: current.planSignedOut || offer.planSignedOut };
  } else {
    current = offer;
  }
  for (const listener of listeners) listener(current);
}

export function currentFallbackOffer(): PlanFallbackOffer | null {
  return current;
}

export function clearFallbackOffer(): void {
  current = null;
  for (const listener of listeners) listener(null);
}

export function subscribeFallbackOffer(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

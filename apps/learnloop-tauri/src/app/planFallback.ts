// Plan-first transport T1 (owner decision 2026-10-21): when the ChatGPT plan
// can't serve a feature (signed out, paused, usage limit, a refused token),
// the feature shows its own "unavailable" state AND LearnLoop asks whether to
// use OpenRouter instead. The sidecar attaches a typed hint to the RPC's
// error details (`fallback_available: "openrouter"`, `fallback_tasks`,
// `fallback_profile`) or to a degraded result (camelCase). This store keeps
// the latest offer so one shell banner can show it; nothing is sent to
// OpenRouter until the learner chooses "Use OpenRouter instead".
//
// Redesign D (owner Q1-Q3, 2026-10-23): the offer is the grant. Each offer
// carries its id (`fallback_offer_id`, what the banner answers) and the action
// that asked (`fallback_origin`, the RPC method). A yes covers that action for
// the session; "Not now" mutes that action's question for the session (each
// action asks once), and other actions still ask.

export interface PlanFallbackOffer {
  provider: "openrouter";
  profile: string;
  tasks: string[];
  /** The plan needs a sign-in: "Continue with ChatGPT" is offered too. */
  planSignedOut: boolean;
  /** The offer the banner answers (redesign D). */
  offerId: string | null;
  /** The action that asked (an RPC method); "Not now" mutes it. */
  origin: string | null;
}

type Listener = (offer: PlanFallbackOffer | null) => void;

let current: PlanFallbackOffer | null = null;
const listeners = new Set<Listener>();
/** Actions whose question the learner muted with "Not now" (this session). */
const declinedOrigins = new Set<string>();

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
  const offerId = record.fallback_offer_id ?? record.fallbackOfferId;
  const origin = record.fallback_origin ?? record.fallbackOrigin;
  return {
    provider: "openrouter",
    profile: typeof profile === "string" && profile ? profile : "openrouter",
    tasks,
    planSignedOut: signedOut,
    offerId: typeof offerId === "string" && offerId ? offerId : null,
    origin: typeof origin === "string" && origin ? origin : null
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

/** Publish the offer an RPC response carries (no-op without one).
 *
 * The banner answers the feature that asked last, and only it (review F4):
 * a newer offer replaces the shown one instead of merging every feature
 * that asked during an outage, so one click never grants another feature's
 * tasks. */
export function noteFallbackOffer(value: unknown): void {
  const offer = extractFallbackOffer(value);
  if (!offer) return;
  // Q2: an action the learner answered "Not now" asks no more this session.
  if (offer.origin && declinedOrigins.has(offer.origin)) return;
  current = offer;
  for (const listener of listeners) listener(current);
}

export function currentFallbackOffer(): PlanFallbackOffer | null {
  return current;
}

/** "Not now": mute this action's question for the session, and close the banner. */
export function declineFallbackOffer(origin: string | null): void {
  if (origin) declinedOrigins.add(origin);
  clearFallbackOffer();
}

/** Tests: forget the muted actions (a new session). */
export function resetDeclinedFallbackOrigins(): void {
  declinedOrigins.clear();
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

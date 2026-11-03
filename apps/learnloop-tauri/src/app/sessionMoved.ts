// Mobile M2a (spec_mobile_tailnet_v1 §6.5): the open session has left this desktop.
//
// A store with no import of the API client, because the client reports here too: a write
// the sidecar refuses with `session_moved` says so at once, before the poll's next read.
// `useQueueRevisionPoll` fills it from re-reads of the open session, on every screen.
// `SessionMovedBanner` reads it and offers to take the session back.
import { useSyncExternalStore } from "react";
import type { SessionSnapshot } from "../api/dto";

export interface SessionMoved {
  readonly sessionId: string;
  /** `adopted`: another device holds it. `ended`: it ended elsewhere (a phone's start fresh). */
  readonly reason: "adopted" | "ended";
  readonly ownerLabel: string | null;
  readonly ownerGeneration: number | null;
}

/** How a re-read session differs from the one this desktop has open; null when it is still ours. */
export function sessionMovedFrom(snapshot: SessionSnapshot): SessionMoved | null {
  const ownership = { ownerLabel: snapshot.ownerLabel ?? null, ownerGeneration: snapshot.ownerGeneration ?? null };
  if (snapshot.ownerDeviceId) return { sessionId: snapshot.sessionId, reason: "adopted", ...ownership };
  if (snapshot.endedAt) return { sessionId: snapshot.sessionId, reason: "ended", ...ownership };
  return null;
}

let moved: SessionMoved | null = null;
const movedListeners = new Set<() => void>();

export function setSessionMoved(next: SessionMoved | null): void {
  if (moved === next || (moved !== null && next !== null && JSON.stringify(moved) === JSON.stringify(next))) return;
  moved = next;
  for (const listener of movedListeners) listener();
}

function subscribeSessionMoved(listener: () => void): () => void {
  movedListeners.add(listener);
  return () => movedListeners.delete(listener);
}

/** The open session's move, if the desktop has seen one. */
export function useSessionMoved(): SessionMoved | null {
  return useSyncExternalStore(subscribeSessionMoved, () => moved);
}

/** A write the sidecar refused with `session_moved`: its details name the owner and the generation. */
export function noteSessionMovedError(error: unknown): void {
  const candidate = error as { code?: unknown; details?: Record<string, unknown> } | null;
  if (candidate?.code !== "session_moved") return;
  const details = candidate.details ?? {};
  const sessionId = details.session_id;
  if (typeof sessionId !== "string" || !sessionId) return;
  setSessionMoved({
    sessionId,
    reason: "adopted",
    ownerLabel: typeof details.owner_label === "string" ? details.owner_label : null,
    ownerGeneration: typeof details.owner_generation === "number" ? details.owner_generation : null
  });
}

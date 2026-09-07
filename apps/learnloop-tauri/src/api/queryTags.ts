/**
 * Invalidation vocabulary for the query cache.
 *
 * A cached read is tagged with the areas of vault/learner state it depends
 * on; a mutation invalidates the tags it can affect (see the `mutating`
 * helpers in client.ts). Tags are coarse on purpose: a stale paint after a
 * missed tag is brief (every mount revalidates), while a wrong "fresh" claim
 * would be invisible.
 */
export const TAG = {
  /** The application snapshot (vault summary, subjects, counts). */
  vault: "vault",
  /** Today's queue, question queue, queue items. */
  queue: "queue",
  /** Goals, goal reports, forecasts, decay/re-entry summaries. */
  goals: "goals",
  /** Concept graph, knowledge map, facets, mastery. */
  graph: "graph",
  /** Authoring proposals (accept/reject/edit). */
  proposals: "proposals",
  /** Vault tree and file bodies. */
  library: "library",
  /** Source library, source sets, coverage, outlines, recent ingests. */
  sources: "sources",
  /** Subject registry (facet merges). */
  registry: "registry",
  /** Settings, learner profile, animation runtime. */
  settings: "settings",
  /** Maintenance feed, conflicts, exam readiness, measurement health. */
  maintenance: "maintenance",
  /** Review log and answer calibration. */
  review: "review",
  /** Reader surfaces that are not tied to one source (prompt contract). */
  reader: "reader"
} as const;

export type KnownTag = (typeof TAG)[keyof typeof TAG];

/** Prefix of the per-source reader tags; invalidated as a group by reader mutations. */
export const READER_PREFIX = "reader:";

export function readerTag(sourceId: string): string {
  return `${READER_PREFIX}${sourceId}`;
}

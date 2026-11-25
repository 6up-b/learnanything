import { api } from "../api/client";
import type { GetNextProbeItemDto } from "../api/dto";

/** How long the first re-read of something the probe router has not decided yet waits, and how many re-reads follow
 *  (each waiting twice as long as the one before: about half a minute in all). The router decides in the sidecar's
 *  worker, off its request loop. */
export const ROUTER_DECISION_POLL_FIRST_MS = 500;
export const ROUTER_DECISION_POLL_TRIES = 6;

/** The question that continues a learning object's diagnostic (G2-R26): the sidecar's one resolver. When the probe
 *  router owns the episode it answers with the router's own question (`standing`), or `pending` until its decision job
 *  has run; it is asked again then, backing off, and never replaced by another question. `episodeId`: the episode a
 *  block end reported. */
export async function nextDiagnosticItem(
  learningObjectId: string,
  episodeId?: string | null,
  cancelled: () => boolean = () => false,
): Promise<GetNextProbeItemDto> {
  let next = await api.getNextProbeItem(learningObjectId, episodeId);
  for (let tries = 0; next.routerState === "pending" && tries < ROUTER_DECISION_POLL_TRIES; tries += 1) {
    if (cancelled()) return next;
    await new Promise((resolve) => setTimeout(resolve, ROUTER_DECISION_POLL_FIRST_MS * 2 ** tries));
    if (cancelled()) return next;
    next = await api.getNextProbeItem(learningObjectId, episodeId);
  }
  return next;
}

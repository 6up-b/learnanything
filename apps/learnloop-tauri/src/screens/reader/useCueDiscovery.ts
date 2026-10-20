// Reader workbench RW3b: discovered cues, found in the background (spec §6.2
// item 5, W12; in-session updates §5.2).
//
// When the guide plan says discovery is on, the Reader asks the sidecar to
// look for the open source's missing cue links (`reader.cue_discovery`): the
// cue judge runs on a worker (Codex by default), never on the request path,
// and the answer is a job read back with growing pauses
// (`reader.cue_discovery_job`, which never waits). When the job found
// something, the plan is re-read so the new marks are placed with the rest
// (placement happens at layout, never while scrolling). The Reader asks again
// only when the plan's `targetsKey` changes -- a new or resolved hypothesis in
// the session -- so only that target's links are computed. Nothing here
// shows anything by itself, and a failure is quiet: the marks the plan has stay.
import { useEffect, useRef } from "react";
import { api } from "../../api/client";
import type { ReaderCueDiscoveryDto, ReaderCueDiscoveryJobDto } from "../../api/dto";

/** Pauses between reads of a running job (the last repeats). */
export const DISCOVERY_POLL_MS: readonly number[] = [1_500, 3_000, 5_000, 10_000];
/** A job not done after this many reads is left; the next open asks again. */
export const DISCOVERY_MAX_READS = 60;

export interface CueDiscoveryInput {
  extractionId: string | null;
  discovery: ReaderCueDiscoveryDto | null;
  offline: boolean;
  /** Re-read the plan (its cues) once the job found something. */
  reloadGuidePlan: () => Promise<void>;
}

function foundSomething(job: ReaderCueDiscoveryJobDto): boolean {
  return Boolean(job.result && (job.result.links > 0 || job.result.calls > 0));
}

export function useCueDiscovery({ extractionId, discovery, offline, reloadGuidePlan }: CueDiscoveryInput): void {
  // The targets each source was asked about (per source, once per key).
  const askedRef = useRef<Map<string, string>>(new Map());
  const reloadRef = useRef(reloadGuidePlan);
  reloadRef.current = reloadGuidePlan;
  const targetsKey = discovery?.targetsKey ?? null;

  useEffect(() => {
    if (!extractionId || targetsKey === null || offline) return;
    if (askedRef.current.get(extractionId) === targetsKey) return;
    askedRef.current.set(extractionId, targetsKey);
    let cancelled = false;
    let done = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const finish = (job: ReaderCueDiscoveryJobDto) => {
      done = true;
      if (!cancelled && foundSomething(job)) void reloadRef.current();
    };
    const read = (jobId: string, reads: number) => {
      if (cancelled || reads >= DISCOVERY_MAX_READS) return;
      const pause = DISCOVERY_POLL_MS[Math.min(reads, DISCOVERY_POLL_MS.length - 1)];
      timer = setTimeout(() => {
        void api.readerCueDiscoveryJob({ jobId })
          .then((job) => (job.state === "done" ? finish(job) : read(jobId, reads + 1)))
          .catch(() => undefined);
      }, pause);
    };
    void api.readerCueDiscovery({ extractionId })
      .then((job) => (job.state === "done" ? finish(job) : read(job.jobId, 0)))
      // Quiet: the plan's marks stay; the next change of targets asks again.
      .catch(() => undefined);
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
      // Left before the job was read to its end: the next mount asks again
      // (the sidecar answers with the job already running for this source).
      if (!done && askedRef.current.get(extractionId) === targetsKey) askedRef.current.delete(extractionId);
    };
  }, [extractionId, targetsKey, offline]);
}

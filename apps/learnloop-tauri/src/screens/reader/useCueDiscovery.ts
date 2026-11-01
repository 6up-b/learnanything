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
// when the plan's `targetsKey` changes -- a new or resolved target in the
// session -- so only that target's links are computed.
//
// Codex review F7: what was asked and what was answered are kept apart. A
// job that answers for other targets than the ones the Reader now has (the
// sidecar joined a search already running for older targets), or that was
// cancelled (a reload), is asked again for the current ones, a few times at
// most. F8: while the plan says background work can still name a target (a
// learner-text gap being read), the plan is re-read with growing pauses, so
// a gap that lands asks for discovery in the same session. Nothing here shows
// anything by itself, and a failure is quiet: the marks the plan has stay.
//
// Codex verify F16: every request names this open of the source, an id
// minted once per open. The sidecar keeps one judge call budget per open, so a
// re-ask or a new target mid-open draws on what the open's earlier jobs left.
//
// Reader CA6b (final verify F11, F12): the open's lifetime is tracked apart
// from whether a reading is shown. A new open -- a new id, with nothing asked
// yet and a fresh budget -- comes only when the open source's identity
// changes (another source, including a direct replacement: A, then B, then A
// is three opens) or the open ends (closed: the identity goes to null). A
// reading that is briefly not there within the same open (side by side's
// second pane loading another section of its book, by hand or by follow
// along, or hidden by a comparison) pauses discovery: no new ask, but the
// open id, what was asked and a job already running are kept, so a section
// change never asks again for the same targets nor draws a new budget.
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReaderCueDiscoveryDto, ReaderCueDiscoveryJobDto } from "../../api/dto";
import { newActivityId } from "./activity";

/** Pauses between reads of a running job (the last repeats). */
export const DISCOVERY_POLL_MS: readonly number[] = [1_500, 3_000, 5_000, 10_000];
/** A job not done after this many reads is left; the next open asks again. */
export const DISCOVERY_MAX_READS = 60;
/** Asks again for the same targets at most this many times (F7). */
export const DISCOVERY_MAX_REASKS = 3;
/** While targets are pending: the first plan re-read, then growing to the cap (F8). */
export const TARGETS_PENDING_POLL_MS = 4_000;
export const TARGETS_PENDING_POLL_MAX_MS = 60_000;

export interface CueDiscoveryInput {
  /** The reading discovery runs on now; null while none is shown (a pause
   *  while `openKey` still names an open, else no open). */
  extractionId: string | null;
  /** Reader CA6b: the identity of the source open (side by side's second
   *  pane: its book while side by side is open). A change, or null, ends the
   *  open. Absent: `extractionId` (the main pane, whose reading is its open). */
  openKey?: string | null;
  discovery: ReaderCueDiscoveryDto | null;
  offline: boolean;
  /** Re-read the plan (its cues) once the job found something. */
  reloadGuidePlan: () => Promise<void>;
}

function foundSomething(job: ReaderCueDiscoveryJobDto): boolean {
  return Boolean(job.result && (job.result.links > 0 || job.result.calls > 0));
}

export function useCueDiscovery({ extractionId, openKey: openKeyInput, discovery, offline, reloadGuidePlan }: CueDiscoveryInput): void {
  // The targets each source was asked about (requested), per source, this open.
  const askedRef = useRef<Map<string, string>>(new Map());
  // How often each (source, targets) was asked again because the answer was for others.
  const reasksRef = useRef<Map<string, number>>(new Map());
  const [reask, setReask] = useState(0);
  const reloadRef = useRef(reloadGuidePlan);
  reloadRef.current = reloadGuidePlan;
  const targetsKey = discovery?.targetsKey ?? null;
  const targetsPending = Boolean(discovery?.targetsPending);
  const openKey = openKeyInput === undefined ? extractionId : openKeyInput;
  // This open of the source (F16; CA6b F11): a new one only when the open's
  // identity changes or the open ends, never while a reading is briefly away.
  const openRef = useRef<{ key: string; id: string } | null>(null);
  if ((openRef.current?.key ?? null) !== openKey) {
    openRef.current = openKey ? { key: openKey, id: `copen_${newActivityId()}` } : null;
    askedRef.current.clear();
    reasksRef.current.clear();
  }
  const openId = openRef.current?.id ?? null;
  // Paused (CA6b F12): the open goes on, but no reading is shown just now.
  const paused = openId !== null && !extractionId;
  const pausedRef = useRef(paused);
  pausedRef.current = paused;
  // The jobs being read, each with its cancel: a pause keeps them running;
  // the open ending (or the Reader closing) stops them.
  const runningRef = useRef<Set<() => void>>(new Set());
  useEffect(() => {
    const running = runningRef.current;
    return () => {
      for (const stop of [...running]) stop();
      running.clear();
    };
  }, [openId]);

  useEffect(() => {
    if (!extractionId || !openId || targetsKey === null || offline) return;
    if (askedRef.current.get(extractionId) === targetsKey) return;
    askedRef.current.set(extractionId, targetsKey);
    let cancelled = false;
    let done = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const stop = () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
      runningRef.current.delete(stop);
    };
    runningRef.current.add(stop);
    const finish = (job: ReaderCueDiscoveryJobDto) => {
      done = true;
      runningRef.current.delete(stop);
      if (cancelled) return;
      if (foundSomething(job)) void reloadRef.current();
      // Answered for other targets (a joined job) or cancelled: not this ask's answer.
      const answered = job.result?.targetsKey ?? null;
      const stale = job.result?.status === "cancelled" || (answered !== null && answered !== targetsKey);
      const key = `${extractionId}\n${targetsKey}`;
      const asked = reasksRef.current.get(key) ?? 0;
      if (stale && asked < DISCOVERY_MAX_REASKS) {
        reasksRef.current.set(key, asked + 1);
        if (askedRef.current.get(extractionId) === targetsKey) askedRef.current.delete(extractionId);
        setReask((value) => value + 1);
      }
    };
    const read = (jobId: string, reads: number) => {
      if (cancelled || reads >= DISCOVERY_MAX_READS) {
        runningRef.current.delete(stop);
        return;
      }
      const pause = DISCOVERY_POLL_MS[Math.min(reads, DISCOVERY_POLL_MS.length - 1)];
      timer = setTimeout(() => {
        void api.readerCueDiscoveryJob({ jobId })
          .then((job) => (job.state === "done" ? finish(job) : read(jobId, reads + 1)))
          .catch(() => runningRef.current.delete(stop));
      }, pause);
    };
    // Minted at render for this open: the same id for every ask of it.
    void api.readerCueDiscovery({ extractionId, sourceOpenId: openId })
      .then((job) => (job.state === "done" ? finish(job) : read(job.jobId, 0)))
      // Quiet: the plan's marks stay; the next change of targets asks again.
      .catch(() => runningRef.current.delete(stop));
    return () => {
      // A pause within the same open (CA6b F12): the job goes on being read
      // and stays asked, so the reading coming back asks nothing again. The
      // open ending stops it (the effect above).
      if (pausedRef.current && openRef.current?.id === openId) return;
      stop();
      // Left before the job was read to its end: the next mount asks again
      // (the sidecar answers with the job already running for this source).
      if (!done && askedRef.current.get(extractionId) === targetsKey) askedRef.current.delete(extractionId);
    };
  }, [extractionId, openId, targetsKey, offline, reask]);

  // F8: background work can still name a target: re-read the plan until it cannot.
  useEffect(() => {
    if (!extractionId || !targetsPending || offline) return;
    let cancelled = false;
    let delay = TARGETS_PENDING_POLL_MS;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const poll = () => {
      timer = null;
      void reloadRef.current()
        .catch(() => undefined)
        .finally(() => {
          if (cancelled) return;
          delay = Math.min(TARGETS_PENDING_POLL_MAX_MS, Math.round(delay * 1.5));
          timer = setTimeout(poll, delay);
        });
    };
    timer = setTimeout(poll, delay);
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [extractionId, targetsPending, offline]);
}

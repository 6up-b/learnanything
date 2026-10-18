// Adaptive hints H2b: the practice screen's hint requests (spec_adaptive_hints_v1
// §4.1, §4.8, §5; H2a's RPC contract, docs/reviews/adaptive-hints-H2a.md §9).
//
// A Hint press flushes the draft, calls practice.request_hint and paces
// practice.hint_job polls; the read that returns a ready hint is the one that
// showed it (`result.shown`), and exactly that result is rendered. `disabled`
// hands the press back to the screen's own authored path, unchanged. While a
// hint is still being written, after `authoredOfferAfterSeconds` an item with
// an authored hint left offers it instead: practice.cancel_hint first, then
// the client's own reveal (practice.record_hint_reveal, client-counted); a
// cancel answering `already_shown` keeps the adaptive hint. Only one hint is
// ever recorded for one press (G-H3).
//
// Nothing here steals focus, animates or opens a modal; nothing is requested
// unless the learner pressed Hint, replied to a hint or took a pick (G-H15).
//
// H2b review F2: a hint is shown only where the learner can see it. Before
// the panel's surface is hidden ("Work in steps"), `hold()` refuses new
// requests, waits for the ones in flight (polls' reads too) and cancels a
// hint still being written (a job is only ever delivered by a read, so an
// unread job is never shown); a hint delivered before the cancel stays shown
// and counted, and when the cancel cannot be established the hold fails and
// the surface stays (re-review F2). The
// authored offer is claimed synchronously, so a double click reveals one
// hint (F3).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  HelpStyle,
  HintDiscriminateAnswerDto,
  HintJobDto,
  HintRequestInput,
  HintResultDto,
  HintShortcut
} from "../../api/dto";
import { errorMessage } from "../../errors";
import { HINT_COPY } from "./hintCopy";

/** One hint the panel shows, in the order shown. */
export interface HintEntry {
  key: string;
  /** "service": a hint the service showed; "client": an item hint the screen
   *  revealed itself (the authored offer), client-counted as before. */
  source: "service" | "client";
  result: HintResultDto;
  /** The discriminating question's answer, once given (its own box). */
  answered?: { text: string; message: string };
}

export interface HintNotice {
  status: "withheld" | "unavailable";
  message: string;
  picks: HintResultDto["picks"];
}

interface Pending {
  jobId: string | null;
  startedAt: number;
}

/** Poll pacing (latency bounds, never a judgment): quick at first, then
 *  steadier while the writer works. */
const POLL_DELAYS_MS = [350, 600, 900, 1200, 1500];

export interface AdaptiveHintsOptions {
  enabled: boolean;
  sessionId: string;
  practiceItemId: string;
  submissionId: () => string;
  answer: () => string;
  flushDraft: () => Promise<void>;
  secondsOnItem: () => number;
  authoredHints: readonly string[];
  /** The screen's client count (authored hints it revealed itself). */
  hintsUsed: number;
  authoredOfferAfterSeconds: number;
  /** The screen's own authored path, exactly as before (status `disabled`). */
  onDisabled: () => void;
  /** Reveal authored hint `index` through the client path; resolves to its
   *  telemetry row's id (null when none was written). */
  onAuthoredReveal: (index: number) => Promise<string | null>;
  onHelpStyleSaved?: (style: HelpStyle) => void;
  onError: (message: string) => void;
}

export function useAdaptiveHints(options: AdaptiveHintsOptions) {
  const [entries, setEntries] = useState<HintEntry[]>([]);
  const [pending, setPending] = useState<Pending | null>(null);
  const [notice, setNotice] = useState<HintNotice | null>(null);
  const [offerReady, setOfferReady] = useState(false);
  const opts = useRef(options);
  opts.current = options;
  const pendingRef = useRef<Pending | null>(null);
  // Bumped on every item change and unmount: a late answer of an earlier
  // item's request never reaches this one.
  const generation = useRef(0);
  const timers = useRef<number[]>([]);
  // H2b review F2: while held, nothing is requested and no job is read.
  const suspended = useRef(false);
  // Requests and authored offers still answering (what `hold()` waits for).
  const inflight = useRef(new Set<Promise<unknown>>());
  // The live chain of polls: a hold that fails starts a new one, and the
  // chain it replaces stops at its next timer.
  const pollChain = useRef(0);
  // H2b review F3: the authored offer, claimed before its cancel is awaited.
  const offerClaim = useRef<string | null>(null);
  const [offerBusy, setOfferBusy] = useState(false);
  const track = <T,>(work: Promise<T>): Promise<T> => {
    inflight.current.add(work);
    const done = () => { inflight.current.delete(work); };
    work.then(done, done);
    return work;
  };

  const clearTimers = () => {
    for (const timer of timers.current) window.clearTimeout(timer);
    timers.current = [];
  };

  useEffect(() => {
    generation.current += 1;
    clearTimers();
    pendingRef.current = null;
    offerClaim.current = null;
    setOfferBusy(false);
    setPending(null);
    setEntries([]);
    setNotice(null);
    setOfferReady(false);
    return () => {
      generation.current += 1;
      clearTimers();
    };
  }, [options.practiceItemId, options.sessionId]);

  const settle = useCallback(() => {
    clearTimers();
    pendingRef.current = null;
    setPending(null);
    setOfferReady(false);
  }, []);

  const handleDone = useCallback((result: HintResultDto | null) => {
    if (!result) return;
    switch (result.status) {
      case "ready":
        if (result.shown === false) return;
        setNotice(null);
        setEntries((current) =>
          result.assistId && current.some((entry) => entry.result.assistId === result.assistId)
            ? current
            : [...current, { key: result.assistId ?? `hint-${current.length}`, source: "service", result }]
        );
        return;
      case "withheld":
      case "unavailable":
        setNotice({ status: result.status, message: result.message ?? "", picks: result.picks ?? [] });
        return;
      case "disabled":
        opts.current.onDisabled();
        return;
      case "refused":
        opts.current.onError(result.message ?? "Hints are off during a diagnostic check.");
        return;
      default:
        return;
    }
  }, []);

  const poll = useCallback((jobId: string, attempt: number, mine: number, chain: number = pollChain.current) => {
    const delay = POLL_DELAYS_MS[Math.min(attempt, POLL_DELAYS_MS.length - 1)];
    const timer = window.setTimeout(async () => {
      if (chain !== pollChain.current) return;
      if (generation.current !== mine || pendingRef.current?.jobId !== jobId) return;
      // Held (the panel's surface is hidden): `hold()` settles the job.
      if (suspended.current) return;
      let job: HintJobDto;
      try {
        // Re-review F2: a read in flight is one `hold()` waits for (the read
        // is what delivers a hint).
        job = await track(api.hintJob(jobId));
      } catch (error) {
        if (generation.current !== mine) return;
        // Held meanwhile: whether it was delivered is `hold()`'s to establish.
        if (suspended.current) return;
        settle();
        opts.current.onError(errorMessage(error));
        return;
      }
      if (generation.current !== mine) return;
      const current = pendingRef.current?.jobId === jobId;
      if (job.state === "pending") {
        if (current) poll(jobId, attempt + 1, mine, chain);
        return;
      }
      if (current) settle();
      // A hint this read delivered is shown whatever settled the request
      // meanwhile (re-review F2): never delivered and dropped.
      if (job.state === "done") handleDone(job.result);
    }, delay);
    timers.current.push(timer);
  }, [handleDone, settle]);

  const request = useCallback((input: Omit<HintRequestInput, "sessionId" | "practiceItemId" | "submissionId">) => {
    const o = opts.current;
    if (!o.enabled || pendingRef.current || suspended.current) return Promise.resolve();
    return track(send(input));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const send = async (input: Omit<HintRequestInput, "sessionId" | "practiceItemId" | "submissionId">) => {
    const o = opts.current;
    const mine = generation.current;
    const started: Pending = { jobId: null, startedAt: Date.now() };
    pendingRef.current = started;
    setPending(started);
    setNotice(null);
    setOfferReady(false);
    try {
      // The service reads the draft from the session checkpoint when none is
      // sent; it is sent too, so the hint is for exactly what is on screen.
      await o.flushDraft();
      const job = await api.requestHint({
        sessionId: o.sessionId,
        practiceItemId: o.practiceItemId,
        submissionId: o.submissionId(),
        answerMd: o.answer(),
        secondsOnItem: o.secondsOnItem(),
        ...input
      });
      if (generation.current !== mine) return;
      if (job.state !== "pending" || !job.jobId) {
        settle();
        if (job.state === "done") handleDone(job.result);
        return;
      }
      const live: Pending = { jobId: job.jobId, startedAt: started.startedAt };
      pendingRef.current = live;
      setPending(live);
      // Held meanwhile: `hold()` cancels it; it is never read here.
      if (suspended.current) return;
      const offerTimer = window.setTimeout(() => {
        if (generation.current === mine && pendingRef.current?.jobId === live.jobId) setOfferReady(true);
      }, Math.max(0, o.authoredOfferAfterSeconds * 1000 - (Date.now() - started.startedAt)));
      timers.current.push(offerTimer);
      poll(job.jobId, 0, mine);
    } catch (error) {
      if (generation.current !== mine) return;
      settle();
      o.onError(errorMessage(error));
    }
  };

  // -- the authored hints, whoever showed them -------------------------------

  const clientCount = entries.filter((entry) => entry.source === "client").length;
  const nextAuthoredIndex = useMemo(() => {
    const shown = new Set<number>();
    // The screen's own reveals before or outside the panel: a prefix, as today.
    for (let index = 0; index < options.hintsUsed - clientCount; index += 1) shown.add(index);
    for (const entry of entries) {
      if (typeof entry.result.authoredIndex === "number") shown.add(entry.result.authoredIndex);
    }
    for (let index = 0; index < options.authoredHints.length; index += 1) if (!shown.has(index)) return index;
    return null;
  }, [clientCount, entries, options.authoredHints.length, options.hintsUsed]);

  const takeAuthoredInstead = useCallback(() => {
    const live = pendingRef.current;
    const index = nextAuthoredIndex;
    // H2b review F3: claimed synchronously, once per request: a second click
    // while the cancel is answering does nothing.
    if (!live?.jobId || index === null || suspended.current || offerClaim.current !== null) {
      return Promise.resolve();
    }
    offerClaim.current = live.jobId;
    setOfferBusy(true);
    const release = () => {
      if (offerClaim.current === live.jobId) {
        offerClaim.current = null;
        setOfferBusy(false);
      }
    };
    return track(revealInstead(live, index).finally(release));
  }, [nextAuthoredIndex]); // eslint-disable-line react-hooks/exhaustive-deps

  const revealInstead = async (live: Pending, index: number) => {
    const jobId = live.jobId as string;
    const mine = generation.current;
    let cancelled = false;
    try {
      const answer = await api.cancelHint(jobId);
      cancelled = answer.cancelled;
    } catch (error) {
      opts.current.onError(errorMessage(error));
      return;
    }
    if (generation.current !== mine) return;
    if (!cancelled) {
      // already_shown: the written hint was delivered meanwhile and stays;
      // the next poll brings it, and nothing else is revealed.
      setOfferReady(false);
      return;
    }
    // The request this offer was for must still be the one pending (a poll
    // or a hold may have settled it meanwhile): nothing is revealed twice.
    if (pendingRef.current !== live) return;
    settle();
    const text = opts.current.authoredHints[index] ?? "";
    const key = `client-${index}`;
    setEntries((current) => [...current, {
      key,
      source: "client",
      result: {
        status: "ready", hintMd: text, kind: "authored", level: 3, authoredIndex: index, assistId: null,
        labels: { origin: HINT_COPY.fromTheItem, kind: HINT_COPY.fromTheItem }, replies: [], picks: []
      }
    }]);
    const assistId = await opts.current.onAuthoredReveal(index);
    if (assistId && generation.current === mine) {
      // Its telemetry row is a shown hint of this attempt, so a reply can name it.
      setEntries((current) => current.map((entry) => entry.key === key
        ? { ...entry, result: { ...entry.result, assistId, replies: ["doesnt_connect", "book_way"] } }
        : entry));
    }
  };

  /** H2b review F2: before the panel's surface is hidden. Refuses new
   *  requests, waits for the ones answering (polls' reads included), and
   *  cancels a hint still being written (never read, so never shown); one
   *  delivered first is read once and kept. Resolves true when nothing is
   *  pending; false (re-review F2) when the cancel could not be established:
   *  the request stays pending and is polled again, so the screen keeps the
   *  answer box, where it is delivered, open. */
  const hold = useCallback(async (): Promise<boolean> => {
    suspended.current = true;
    while (inflight.current.size) {
      await Promise.allSettled([...inflight.current]);
    }
    const live = pendingRef.current;
    if (!live) return true;
    const mine = generation.current;
    if (!live.jobId) {
      settle();
      return true;
    }
    const jobId = live.jobId;
    const release = (error?: unknown) => {
      // Not held: requests and polls go on where the hint can be seen.
      suspended.current = false;
      if (error !== undefined) opts.current.onError(errorMessage(error));
      if (pendingRef.current === live) {
        pollChain.current += 1; // one chain of polls, never two
        poll(jobId, 0, mine);
      }
      return false;
    };
    try {
      const answer = await track(api.cancelHint(jobId));
      if (generation.current !== mine) return true;
      if (answer.cancelled) {
        if (pendingRef.current === live) settle();
        return true;
      }
      // already_shown: delivered before the cancel; its result is read again.
      const job = await track(api.hintJob(jobId));
      if (generation.current !== mine) return true;
      if (job.state !== "done") return release();
      if (pendingRef.current === live) settle();
      handleDone(job.result);
      return true;
    } catch (error) {
      if (generation.current !== mine) return true;
      return release(error);
    }
  }, [handleDone, poll, settle]);

  /** The panel's surface is shown again: requests are accepted. */
  const resume = useCallback(() => {
    suspended.current = false;
  }, []);

  // -- the learner's replies and picks ---------------------------------------

  const press = useCallback(() => request({ request: "more" }), [request]);
  const reply = useCallback((entry: HintEntry, reply: {
    shortcut?: HintShortcut; text?: string; selection?: string;
  }) => {
    if (!entry.result.assistId) return;
    void request({
      request: "feedback",
      answeredAssistId: entry.result.assistId,
      ...(reply.shortcut ? { feedbackShortcut: reply.shortcut } : {}),
      ...(reply.text?.trim() ? { feedbackText: reply.text.trim() } : {}),
      ...(reply.selection?.trim() ? { feedbackSelection: reply.selection.trim() } : {})
    });
  }, [request]);
  const bookWay = useCallback((entry: HintEntry) => {
    if (entry.result.assistId) void request({ request: "book_way", answeredAssistId: entry.result.assistId });
  }, [request]);
  const smallerStep = useCallback((entry: HintEntry) => {
    if (entry.result.assistId) void request({ request: "smaller_step", answeredAssistId: entry.result.assistId });
  }, [request]);
  const takeWorked = useCallback((level: 4 | 5) => request({ request: "more", takenLevel: level }), [request]);

  const answerDiscriminating = useCallback(async (entry: HintEntry, text: string) => {
    const o = opts.current;
    if (!entry.result.assistId || !text.trim() || entry.answered) return;
    const mine = generation.current;
    let answer: HintDiscriminateAnswerDto;
    try {
      answer = await api.answerDiscriminating({
        sessionId: o.sessionId, practiceItemId: o.practiceItemId, submissionId: o.submissionId(),
        questionAssistId: entry.result.assistId, answerMd: text.trim()
      });
    } catch (error) {
      o.onError(errorMessage(error));
      return;
    }
    if (generation.current !== mine || !answer.recorded) return;
    setEntries((current) => current.map((candidate) => candidate.key === entry.key
      ? { ...candidate, answered: { text: text.trim(), message: answer.message ?? "" } }
      : candidate));
  }, []);

  const saveHelpStyle = useCallback(async (style: HelpStyle) => {
    try {
      const saved = await api.setHelpStyle(style);
      opts.current.onHelpStyleSaved?.(saved.helpStyle);
    } catch (error) {
      opts.current.onError(errorMessage(error));
    }
  }, []);

  // The picks are the service's own (consequence stated before they are
  // taken); the latest hint that carries them.
  const picks = useMemo(() => {
    for (let index = entries.length - 1; index >= 0; index -= 1) {
      const found = entries[index].result.picks;
      if (found && found.length) return found;
    }
    // A withheld hint offers worked help instead ("take a worked piece?").
    return notice?.status === "withheld" ? notice.picks ?? [] : [];
  }, [entries, notice]);

  return {
    entries,
    pending: pending !== null,
    notice,
    offer: pending !== null && pending.jobId !== null && offerReady && nextAuthoredIndex !== null,
    offerBusy,
    clientRevealCount: clientCount,
    picks,
    press,
    reply,
    bookWay,
    smallerStep,
    takeWorked,
    takeAuthoredInstead,
    answerDiscriminating,
    saveHelpStyle,
    hold,
    resume
  };
}

export type AdaptiveHints = ReturnType<typeof useAdaptiveHints>;

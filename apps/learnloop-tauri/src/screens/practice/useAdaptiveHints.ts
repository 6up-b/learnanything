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

  const clearTimers = () => {
    for (const timer of timers.current) window.clearTimeout(timer);
    timers.current = [];
  };

  useEffect(() => {
    generation.current += 1;
    clearTimers();
    pendingRef.current = null;
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

  const poll = useCallback((jobId: string, attempt: number, mine: number) => {
    const delay = POLL_DELAYS_MS[Math.min(attempt, POLL_DELAYS_MS.length - 1)];
    const timer = window.setTimeout(async () => {
      if (generation.current !== mine || pendingRef.current?.jobId !== jobId) return;
      let job: HintJobDto;
      try {
        job = await api.hintJob(jobId);
      } catch (error) {
        if (generation.current !== mine) return;
        settle();
        opts.current.onError(errorMessage(error));
        return;
      }
      if (generation.current !== mine || pendingRef.current?.jobId !== jobId) return;
      if (job.state === "pending") {
        poll(jobId, attempt + 1, mine);
        return;
      }
      settle();
      if (job.state === "done") handleDone(job.result);
    }, delay);
    timers.current.push(timer);
  }, [handleDone, settle]);

  const request = useCallback(async (input: Omit<HintRequestInput, "sessionId" | "practiceItemId" | "submissionId">) => {
    const o = opts.current;
    if (!o.enabled || pendingRef.current) return;
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
  }, [handleDone, poll, settle]);

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

  const takeAuthoredInstead = useCallback(async () => {
    const live = pendingRef.current;
    const index = nextAuthoredIndex;
    if (!live?.jobId || index === null) return;
    const mine = generation.current;
    let cancelled = false;
    try {
      const answer = await api.cancelHint(live.jobId);
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
  }, [nextAuthoredIndex, settle]);

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
    clientRevealCount: clientCount,
    picks,
    press,
    reply,
    bookWay,
    smallerStep,
    takeWorked,
    takeAuthoredInstead,
    answerDiscriminating,
    saveHelpStyle
  };
}

export type AdaptiveHints = ReturnType<typeof useAdaptiveHints>;

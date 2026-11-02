// Reader workbench RW5a: the open source's explorable figures (spec §8.1; UX §4.7).
//
// Loads the figures the Reader shows for the open source, runs "make this
// explorable" and "not right?" as build jobs (the sidecar answers at once; the
// job is read here, paced, never waited on), and keeps which one figure is
// expanded. Nothing here moves focus or starts anything on its own: every
// build is a learner's press, every result lands where its passage is (W12).
// With the contract's `figures` absent (figures.enabled off) the hook is inert:
// no RPC is ever called and nothing renders (U13).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../../api/client";
import type { CorrespondentFigureDto, FigureBuildResultDto, FigurePredictionResultDto, FigureRichPendingDto, FigureViewDto, LibraryJobDto } from "../../../api/dto";
import { errorMessage, getCommandError } from "../../../errors";
import { frameBadge } from "./FigureInline";
import { passageKeys } from "../readerShared";

/** How often a running build is read (a background job: no hurry). */
export const FIGURE_POLL_MS = 1500;
/** RW5d P2b: how often the source's figures are read again while a rich build
 *  runs (minutes long; the fuller line and the pending line follow it). */
export const RICH_POLL_MS = 5000;

export interface FigureRequestInput {
  spanIds: string[];
  region?: { spanId: string; bbox: number[] } | null;
  /** RW5b: an offered figure (the organizer's or the tutor's judgment named in `offerRef`);
   *  RW5d P1: "show_me" (the intent box with words, the Ask rail). */
  origin?: "selection" | "library" | "tutor" | "show_me";
  offerRef?: string | null;
  /** RW5d P1: what the figure should show, in the learner's words (or the tutor's goal). */
  goalText?: string | null;
  /** RW5d P1: where the learner was reading (the home of a figure with no passage). */
  readingAt?: { spanId: string } | null;
  /** RW5d P1: hears the figure once it lands (the Ask rail's thread line). */
  onLanded?: (figure: FigureViewDto) => void;
}

/** How a request ended (fix round 2, F9: an offer's press settles on this, not
 *  on its dispatch): `shown` a figure landed under its passage; `not_shown`
 *  the build was refused, failed, or did not verify (its line under the
 *  passage says why); `cancelled` the learner stopped it or the source
 *  changed; `skipped` nothing was sent (figures or offers are off). */
export type FigureRequestOutcome = "shown" | "not_shown" | "cancelled" | "skipped";

/** A build in flight or one that could not run, shown as a line under its passage. */
export interface FigurePending {
  key: string;
  anchorSpanId: string;
  state: "pending" | "failed";
  /** The learner's line when it could not run (capped, unreachable, held out, ...). */
  message: string | null;
  code: string | null;
  /** What "try again" sends. */
  retry: () => void;
  /** Stop waiting for it (the build is cancelled; a paid call already sent keeps its receipt). */
  cancel: () => void;
}

export interface FiguresContract {
  predictions: boolean;
  region: boolean;
  revisions: boolean;
  /** RW5b: "make this explorable" offers (present only while figures.offers_enabled is on). */
  offers?: boolean;
  /** RW5d P1: "show me" in the learner's words (present only while figures.show_me_enabled is on). */
  showMe?: boolean;
  /** RW5d P2: the sketch tier. */
  sketch?: boolean;
  /** RW5d P2b: the rich tiers (present only while figures.rich_tiers_enabled is on), with the
   *  Manim opt-in's state ("ask": ready here and never asked; shown once after a press). */
  rich?: { manimOptIn: "ask" | "standing" | "declined" | "unavailable" };
}

/** RW5d P4a (figures follow the section): where a figure from another book lives. */
export interface FigureHome {
  sourceTitle: string;
  sectionTitle: string;
}

/** RW5d P4a: a figure of another book's corresponding section, opened from "also
 *  in your books" and shown under the passage the learner is reading here, its
 *  home named. Only this view of it: nothing is copied, and it goes with the book. */
export interface FollowedFigure {
  /** The figure as its own book lists it, placed under the passage here. */
  figure: FigureViewDto;
  home: FigureHome;
}

export interface FiguresCtl {
  enabled: boolean;
  contract: FiguresContract | null;
  figures: FigureViewDto[];
  pending: FigurePending[];
  /** The one open placement (Codex re-review F10: a figure reused under
   * several paragraphs opens at the one pressed), as {@link figurePlacementKey}. */
  expandedKey: string | null;
  setExpanded: (figure: FigureViewDto | null) => void;
  /** Resolves once the build has ended (never rejects). */
  request: (input: FigureRequestInput) => Promise<FigureRequestOutcome>;
  /** "Not right?". RW5d P2b: on an animation, ``differentKind`` re-runs the tier choice
   * with the note instead of sending it and the earlier program to the rich author. */
  revise: (figure: FigureViewDto, note: string, differentKind?: boolean) => void;
  predict: (figure: FigureViewDto, index: number, answer: string) => Promise<FigurePredictionResultDto | null>;
  explain: (figure: FigureViewDto, predictionId: string, text: string) => Promise<FigurePredictionResultDto | null>;
  /** The figures and pending lines under one passage (RW5d P2b: and its rich builds with no quick figure;
   *  RW5d P4a: and the figures followed here from another book). */
  under: (spanId: string | null | undefined) => {
    figures: FigureViewDto[]; pending: FigurePending[]; richPending: FigureRichPendingDto[]; followed: FollowedFigure[];
  };
  /** RW5d P4a: the figures followed here from other books' corresponding sections. */
  followed: FollowedFigure[];
  /** RW5d P4a: open a figure of another book's corresponding section under the passage
   *  `at` here, expanded, its home named. Resolves false when it may not be shown now
   *  (its own book no longer lists it: held out, switched off, gone). */
  follow: (ref: CorrespondentFigureDto, home: FigureHome, at: string) => Promise<boolean>;
  /** RW5d P2b: rich builds with no quick figure (pending lines). */
  richPending: FigureRichPendingDto[];
  /** RW5d P2b: cancel a rich build (only it: a quick figure stays). */
  cancelRich: (richJobId: string) => void;
  /** RW5d P2b (Codex review F9): try a rich build again that ended with no row. */
  retryRich: (richJobId: string) => void;
  /** RW5d P2b: the Manim opt-in's state, and the passage its one inline ask sits under (after a press). */
  manimOptIn: "ask" | "standing" | "declined" | "unavailable" | null;
  optInSpanId: string | null;
  answerManimOptIn: (choice: "allow" | "decline") => void;
}

/** One placement of a figure: the figure and the paragraph it is listed under
 * (a goal-only figure may be placed under several; RW5d Codex review F3). */
export function figurePlacementKey(figure: Pick<FigureViewDto, "figureId" | "anchorSpanId">): string {
  return `${figure.figureId}@${figure.anchorSpanId ?? ""}`;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useFigures({
  extractionId,
  contract,
  onBuilt,
  followEnabled = false,
}: {
  extractionId: string | null | undefined;
  contract: FiguresContract | null | undefined;
  onBuilt?: (figure: FigureViewDto) => void;
  /** RW5d P4a (Codex review F2): CA5's correspondence switch as the prompt contract
   *  names it. Off (or absent): no figure is followed here, a followed one is
   *  cleared and a follow still in flight never lands. */
  followEnabled?: boolean;
}): FiguresCtl {
  const enabled = Boolean(contract && extractionId);
  const followOn = enabled && followEnabled;
  const [figures, setFigures] = useState<FigureViewDto[]>([]);
  const [pending, setPending] = useState<FigurePending[]>([]);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [richPending, setRichPending] = useState<FigureRichPendingDto[]>([]);
  // RW5d P5 (Codex review F11): a figure for this source is being built ahead of need.
  const [prefetchPending, setPrefetchPending] = useState(false);
  const [followed, setFollowed] = useState<FollowedFigure[]>([]);
  const followedRef = useRef(followed);
  followedRef.current = followed;
  const [manimOptIn, setManimOptIn] = useState<FiguresCtl["manimOptIn"]>(contract?.rich?.manimOptIn ?? null);
  const [optInSpanId, setOptInSpanId] = useState<string | null>(null);
  useEffect(() => { setManimOptIn(contract?.rich?.manimOptIn ?? null); }, [contract?.rich?.manimOptIn]);
  const setExpanded = useCallback((figure: FigureViewDto | null) => setExpandedKey(figure ? figurePlacementKey(figure) : null), []);
  // A build that lands after the source changed never shows on the new one.
  const generation = useRef(0);
  // RW5d P4a (Codex review F2): bumped when following switches off, so a
  // follow whose listing is still in flight is dropped when it lands.
  const followGeneration = useRef(0);
  const runs = useRef(new Map<string, object>());
  const onBuiltRef = useRef(onBuilt);
  onBuiltRef.current = onBuilt;

  useEffect(() => {
    generation.current += 1;
    setFigures([]);
    setPending([]);
    setRichPending([]);
    setPrefetchPending(false);
    setFollowed([]);
    setExpandedKey(null);
    if (!enabled || !extractionId) return;
    const mine = generation.current;
    void Promise.resolve(api.readerFigures({ extractionId }))
      .then((found) => {
        if (generation.current === mine && found) {
          setFigures(found.figures ?? []);
          setRichPending(found.richPending ?? []);
          setPrefetchPending(found.prefetchPending === true);
        }
      })
      .catch(() => undefined);
  }, [enabled, extractionId]);

  // RW5d P4a (Codex review F2): correspondence switched off with the same book
  // open clears every followed figure (and its open state) here.
  useEffect(() => {
    if (followOn) return;
    followGeneration.current += 1;
    const keys = new Set(followedRef.current.map((entry) => figurePlacementKey(entry.figure)));
    if (!keys.size) return;
    setFollowed([]);
    setExpandedKey((key) => (key && keys.has(key) ? null : key));
  }, [followOn]);

  // RW5d P2b: while a rich build runs (a fuller line pending or waiting, or a
  // rich-only pending line), the source's figures are read again, paced; the
  // lines change in place under their passage, nothing else moves. RW5d P5
  // (Codex review F11): likewise while a figure for this source is being built
  // ahead of need, so its quiet line appears with the Reader open; the read
  // stops once the sidecar says nothing more is coming.
  const richRunning = (
    prefetchPending
    || richPending.some((line) => line.state === "pending" || line.state === "waiting_for_plan")
    || figures.some((figure) => figure.fuller?.state === "pending" || figure.fuller?.state === "waiting_for_plan"));
  useEffect(() => {
    if (!enabled || !extractionId || !richRunning) return;
    const mine = generation.current;
    const timer = setTimeout(() => {
      void Promise.resolve(api.readerFigures({ extractionId }))
        .then((found) => {
          if (generation.current === mine && found) {
            setFigures(found.figures ?? []);
            setRichPending(found.richPending ?? []);
            setPrefetchPending(found.prefetchPending === true);
          }
        })
        .catch(() => undefined);
    }, RICH_POLL_MS);
    return () => clearTimeout(timer);
  }, [enabled, extractionId, richRunning, figures, richPending, prefetchPending]);

  const land = useCallback((figure: FigureViewDto) => {
    const sameRequest = (item: FigureViewDto) => item.spanIds.join(",") === figure.spanIds.join(",")
      && JSON.stringify(item.region) === JSON.stringify(figure.region)
      && (item.goalText ?? null) === (figure.goalText ?? null) && item.anchorSpanId === figure.anchorSpanId;
    setFigures((list) => {
      // RW5d (Codex review F3): a figure with no passage may be placed under
      // several paragraphs (the same goal asked at each); a placement is the
      // figure and its anchor. A new version takes every placement of the one
      // it supersedes; a reuse adds this placement and keeps the others.
      const goalOnly = figure.spanIds.length === 0 && figure.region === null;
      const anchors = goalOnly
        ? [...new Set([figure.anchorSpanId, ...list.filter((item) => item.figureId === figure.supersedesId).map((item) => item.anchorSpanId)])]
        : [figure.anchorSpanId];
      const placed = anchors.map((anchorSpanId) => (anchorSpanId === figure.anchorSpanId ? figure : { ...figure, anchorSpanId }));
      return [
        // A new version replaces the one it supersedes; a new build replaces an
        // earlier failed or unsupported line for the same request.
        ...list.filter((item) => !(item.figureId === figure.figureId && (!goalOnly || anchors.includes(item.anchorSpanId)))
          && item.figureId !== figure.supersedesId
          && !(sameRequest(item) && (item.verification === "failed" || item.verification === "unsupported"))),
        ...placed,
      ];
    });
  }, []);

  const run = useCallback(
    (key: string, anchorSpanId: string, start: () => Promise<LibraryJobDto<FigureBuildResultDto>>,
     onLanded?: (figure: FigureViewDto) => void): Promise<FigureRequestOutcome> => {
      const mine = generation.current;
      const token = {};
      runs.current.set(key, token);
      const live = () => generation.current === mine && runs.current.get(key) === token;
      let jobId: string | null = null;
      const retry = () => { void run(key, anchorSpanId, start, onLanded); };
      const cancel = () => {
        runs.current.delete(key);
        setPending((list) => list.filter((item) => item.key !== key));
        if (jobId) void Promise.resolve(api.readerFigureJobCancel({ jobId })).catch(() => undefined);
      };
      setPending((list) => [...list.filter((item) => item.key !== key), { key, anchorSpanId, state: "pending", message: null, code: null, retry, cancel }]);
      return (async (): Promise<FigureRequestOutcome> => {
        try {
          let job = await start();
          jobId = job.jobId;
          while (job.state === "pending") {
            await sleep(FIGURE_POLL_MS);
            if (!live()) return "cancelled";
            job = await api.readerFigureJob({ jobId: job.jobId });
          }
          if (!live()) return "cancelled";
          setPending((list) => list.filter((item) => item.key !== key));
          const rich = job.state === "done" ? job.result?.rich ?? null : null;
          if (rich && !job.result?.figure) {
            // RW5d P2b: only a rich figure is being built: its pending line under the passage.
            setRichPending((list) => [...list.filter((line) => line.richJobId !== rich.richJobId), rich]);
            return "shown";
          }
          const figure = job.state === "done" ? job.result?.figure ?? null : null;
          const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative");
          if (figure && figure.supersedesId && !shown) {
            // A "not right?" version that did not verify: the earlier one stays.
            setPending((list) => [...list, { key, anchorSpanId, state: "failed", message: figure.reason ? `${frameBadge(figure.verification)} (${figure.reason})` : frameBadge(figure.verification), code: figure.verification, retry, cancel }]);
          } else if (figure) {
            land(figure);
            onBuiltRef.current?.(figure);
            onLanded?.(figure);
          }
          return shown ? "shown" : "not_shown";
        } catch (error) {
          if (!live()) return "cancelled";
          const command = getCommandError(error);
          setPending((list) => list.map((item) => item.key === key
            ? { ...item, state: "failed", message: errorMessage(error), code: command?.code ?? null }
            : item));
          return "not_shown";
        }
      })();
    },
    [land],
  );

  const request = useCallback(
    (input: FigureRequestInput): Promise<FigureRequestOutcome> => {
      if (!enabled || !extractionId) return Promise.resolve("skipped");
      const spanIds = [...new Set(input.spanIds)];
      const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? input.readingAt?.spanId ?? "";
      // RW5d P2b: the Manim opt-in is asked once, inline, under the first press's passage.
      if (manimOptIn === "ask" && anchor) setOptInSpanId((current) => current ?? anchor);
      const region = input.region && contract?.region ? input.region : null;
      const goal = input.goalText?.trim() ? input.goalText.trim() : null;
      const key = `req:${anchor}:${spanIds.join(",")}:${region ? region.bbox.join(",") : ""}${goal ? `:goal:${goal}` : ""}`;
      const origin = input.origin ?? (goal ? "show_me" : "selection");
      if (goal) {
        // RW5d P1: "show me" in the learner's words (or a tutor's goal), with
        // or without a passage, through figure.request (the server derives who
        // wrote it and the policy; held-out material is refused there).
        if (!contract?.showMe) return Promise.resolve("skipped");
        if (origin === "tutor" && !contract?.offers) return Promise.resolve("skipped");
        const anchored = spanIds.length > 0 || region !== null;
        const readingAt = input.readingAt?.spanId ? { extractionId, spanId: input.readingAt.spanId } : null;
        if (!anchored && !readingAt) return Promise.resolve("skipped");
        return run(key, anchor, () => api.figureRequest({
          goalText: goal, origin,
          anchor: anchored ? { extractionId, spanIds, region, spanKeys: passageKeys(extractionId, [...spanIds, region?.spanId]) } : null,
          readingAt, offerRef: input.offerRef ?? null,
        }), input.onLanded);
      }
      if (origin === "show_me") return Promise.resolve("skipped"); // show me needs words
      if (origin !== "selection") {
        // RW5b: an offer builds only while offers are on (the server checks the offer too).
        if (!contract?.offers) return Promise.resolve("skipped");
        return run(key, anchor, () => api.readerFigureRequest({ extractionId, spanIds, origin: origin as "library" | "tutor", offerRef: input.offerRef ?? null,
          spanKeys: passageKeys(extractionId, spanIds) }), input.onLanded);
      }
      return run(key, anchor, () => api.readerFigureRequest({ extractionId, spanIds, region, spanKeys: passageKeys(extractionId, [...spanIds, region?.spanId]) }), input.onLanded);
    },
    [enabled, extractionId, contract, run, manimOptIn],
  );

  const refresh = useCallback(() => {
    if (!enabled || !extractionId) return;
    const mine = generation.current;
    void Promise.resolve(api.readerFigures({ extractionId }))
      .then((found) => {
        if (generation.current === mine && found) {
          setFigures(found.figures ?? []);
          setRichPending(found.richPending ?? []);
        }
      })
      .catch(() => undefined);
  }, [enabled, extractionId]);

  const cancelRich = useCallback((richJobId: string) => {
    setRichPending((list) => list.filter((line) => line.richJobId !== richJobId));
    void Promise.resolve(api.figureRichCancel({ richJobId })).then(refresh, refresh);
  }, [refresh]);

  const retryRich = useCallback((richJobId: string) => {
    setRichPending((list) => list.map((line) => line.richJobId !== richJobId ? line
      : { ...line, state: "pending", phase: "writing", reason: null }));
    void Promise.resolve(api.figureRichRetry({ richJobId })).then(refresh, refresh);
  }, [refresh]);

  const answerManimOptIn = useCallback((choice: "allow" | "decline") => {
    setOptInSpanId(null);
    setManimOptIn(choice === "allow" ? "standing" : "declined");
    void Promise.resolve(api.figureManimOptIn({ choice }))
      .then((found) => { if (found?.manimOptIn) setManimOptIn(found.manimOptIn); })
      .catch(() => setManimOptIn("ask"));
  }, []);

  const revise = useCallback(
    (figure: FigureViewDto, note: string, differentKind?: boolean) => {
      if (!enabled || !contract?.revisions) return;
      void run(`rev:${figure.figureId}`, figure.anchorSpanId ?? "", () => api.readerFigureRevise(differentKind
        ? { figureId: figure.figureId, note, differentKind: true } : { figureId: figure.figureId, note }));
    },
    [enabled, contract, run],
  );

  const patchPrediction = useCallback((found: FigurePredictionResultDto) => {
    const patch = (figure: FigureViewDto): FigureViewDto => figure.figureId !== found.figureId ? figure : {
      ...figure,
      predictions: figure.predictions.map((prediction) => prediction.index === found.predictionIndex
        ? { ...prediction, answered: found } : prediction),
    };
    setFigures((list) => list.map(patch));
    setFollowed((list) => list.map((entry) => ({ ...entry, figure: patch(entry.figure) })));
  }, []);

  const follow = useCallback(
    async (ref: CorrespondentFigureDto, home: FigureHome, at: string): Promise<boolean> => {
      if (!followOn || !extractionId || !at || ref.extractionId === extractionId) return false;
      const mine = generation.current;
      const mineFollow = followGeneration.current;
      const current = () => generation.current === mine && followGeneration.current === mineFollow;
      // Codex review F1: refused now (held out, switched off, gone, unreadable),
      // a copy already shown here from an earlier press leaves with it.
      const refuse = () => {
        if (current()) {
          const keys = new Set(followedRef.current.filter((entry) => entry.figure.figureId === ref.figureId)
            .map((entry) => figurePlacementKey(entry.figure)));
          setFollowed((list) => list.filter((entry) => entry.figure.figureId !== ref.figureId));
          setExpandedKey((key) => (key && keys.has(key) ? null : key));
        }
        return false;
      };
      let found: FigureViewDto | undefined;
      try {
        // Its own book's listing, read now: protection and the switches are checked again there.
        const listed = await api.readerFigures({ extractionId: ref.extractionId });
        found = (listed?.figures ?? []).find((figure) => figure.figureId === ref.figureId && figure.anchorSpanId === ref.anchorSpanId)
          ?? (listed?.figures ?? []).find((figure) => figure.figureId === ref.figureId);
      } catch {
        return refuse();
      }
      if (!current()) return false;
      if (!found || (found.verification !== "verified" && found.verification !== "illustrative")) return refuse();
      // Shown here, under the passage the learner is reading; a fuller version still
      // being built stays with its own book (only a ready one comes along).
      const figure: FigureViewDto = { ...found, anchorSpanId: at,
        ...(found.fuller !== undefined ? { fuller: found.fuller?.state === "ready" ? found.fuller : null } : {}) };
      setFollowed((list) => [...list.filter((entry) => entry.figure.figureId !== figure.figureId), { figure, home }]);
      setExpandedKey(figurePlacementKey(figure));
      return true;
    },
    [followOn, extractionId],
  );

  const predict = useCallback(
    async (figure: FigureViewDto, index: number, answer: string) => {
      if (!contract?.predictions) return null;
      const found = await api.readerFigurePredict({ figureId: figure.figureId, predictionIndex: index, answer });
      patchPrediction(found);
      return found;
    },
    [contract, patchPrediction],
  );

  const explain = useCallback(
    async (_figure: FigureViewDto, predictionId: string, text: string) => {
      if (!contract?.predictions || !text.trim()) return null;
      const found = await api.readerFigureExplain({ predictionId, text });
      patchPrediction(found);
      return found;
    },
    [contract, patchPrediction],
  );

  // Gated as it renders (Codex review F2): nothing followed shows once the switch is off.
  const shownFollowed = useMemo(() => (followOn ? followed : []), [followOn, followed]);

  const under = useCallback(
    (spanId: string | null | undefined) => {
      if (!spanId) return { figures: [], pending: [], richPending: [], followed: [] };
      return {
        figures: figures.filter((figure) => figure.anchorSpanId === spanId),
        pending: pending.filter((item) => item.anchorSpanId === spanId),
        richPending: richPending.filter((line) => line.anchorSpanId === spanId),
        followed: shownFollowed.filter((entry) => entry.figure.anchorSpanId === spanId),
      };
    },
    [figures, pending, richPending, shownFollowed],
  );

  return useMemo(
    () => ({
      enabled,
      contract: contract ?? null,
      figures,
      pending,
      expandedKey,
      setExpanded,
      request,
      revise,
      predict,
      explain,
      under,
      followed: shownFollowed,
      follow,
      richPending,
      cancelRich,
      retryRich,
      manimOptIn,
      optInSpanId,
      answerManimOptIn,
    }),
    [enabled, contract, figures, pending, expandedKey, setExpanded, request, revise, predict, explain, under,
     shownFollowed, follow, richPending, cancelRich, retryRich, manimOptIn, optInSpanId, answerManimOptIn],
  );
}

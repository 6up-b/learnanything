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
import type { FigureBuildResultDto, FigurePredictionResultDto, FigureViewDto, LibraryJobDto } from "../../../api/dto";
import { errorMessage, getCommandError } from "../../../errors";
import { frameBadge } from "./FigureInline";

/** How often a running build is read (a background job: no hurry). */
export const FIGURE_POLL_MS = 1500;

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
  revise: (figure: FigureViewDto, note: string) => void;
  predict: (figure: FigureViewDto, index: number, answer: string) => Promise<FigurePredictionResultDto | null>;
  explain: (figure: FigureViewDto, predictionId: string, text: string) => Promise<FigurePredictionResultDto | null>;
  /** The figures and pending lines under one passage. */
  under: (spanId: string | null | undefined) => { figures: FigureViewDto[]; pending: FigurePending[] };
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
}: {
  extractionId: string | null | undefined;
  contract: FiguresContract | null | undefined;
  onBuilt?: (figure: FigureViewDto) => void;
}): FiguresCtl {
  const enabled = Boolean(contract && extractionId);
  const [figures, setFigures] = useState<FigureViewDto[]>([]);
  const [pending, setPending] = useState<FigurePending[]>([]);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const setExpanded = useCallback((figure: FigureViewDto | null) => setExpandedKey(figure ? figurePlacementKey(figure) : null), []);
  // A build that lands after the source changed never shows on the new one.
  const generation = useRef(0);
  const runs = useRef(new Map<string, object>());
  const onBuiltRef = useRef(onBuilt);
  onBuiltRef.current = onBuilt;

  useEffect(() => {
    generation.current += 1;
    setFigures([]);
    setPending([]);
    setExpandedKey(null);
    if (!enabled || !extractionId) return;
    const mine = generation.current;
    void Promise.resolve(api.readerFigures({ extractionId }))
      .then((found) => {
        if (generation.current === mine && found) setFigures(found.figures ?? []);
      })
      .catch(() => undefined);
  }, [enabled, extractionId]);

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
          anchor: anchored ? { extractionId, spanIds, region } : null,
          readingAt, offerRef: input.offerRef ?? null,
        }), input.onLanded);
      }
      if (origin === "show_me") return Promise.resolve("skipped"); // show me needs words
      if (origin !== "selection") {
        // RW5b: an offer builds only while offers are on (the server checks the offer too).
        if (!contract?.offers) return Promise.resolve("skipped");
        return run(key, anchor, () => api.readerFigureRequest({ extractionId, spanIds, origin: origin as "library" | "tutor", offerRef: input.offerRef ?? null }), input.onLanded);
      }
      return run(key, anchor, () => api.readerFigureRequest({ extractionId, spanIds, region }), input.onLanded);
    },
    [enabled, extractionId, contract, run],
  );

  const revise = useCallback(
    (figure: FigureViewDto, note: string) => {
      if (!enabled || !contract?.revisions) return;
      void run(`rev:${figure.figureId}`, figure.anchorSpanId ?? "", () => api.readerFigureRevise({ figureId: figure.figureId, note }));
    },
    [enabled, contract, run],
  );

  const patchPrediction = useCallback((found: FigurePredictionResultDto) => {
    setFigures((list) => list.map((figure) => figure.figureId !== found.figureId ? figure : {
      ...figure,
      predictions: figure.predictions.map((prediction) => prediction.index === found.predictionIndex
        ? { ...prediction, answered: found } : prediction),
    }));
  }, []);

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

  const under = useCallback(
    (spanId: string | null | undefined) => {
      if (!spanId) return { figures: [], pending: [] };
      return {
        figures: figures.filter((figure) => figure.anchorSpanId === spanId),
        pending: pending.filter((item) => item.anchorSpanId === spanId),
      };
    },
    [figures, pending],
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
    }),
    [enabled, contract, figures, pending, expandedKey, setExpanded, request, revise, predict, explain, under],
  );
}

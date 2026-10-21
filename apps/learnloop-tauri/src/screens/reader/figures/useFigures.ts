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
}

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
}

export interface FiguresCtl {
  enabled: boolean;
  contract: FiguresContract | null;
  figures: FigureViewDto[];
  pending: FigurePending[];
  expandedId: string | null;
  setExpanded: (figureId: string | null) => void;
  request: (input: FigureRequestInput) => void;
  revise: (figure: FigureViewDto, note: string) => void;
  predict: (figure: FigureViewDto, index: number, answer: string) => Promise<FigurePredictionResultDto | null>;
  explain: (figure: FigureViewDto, predictionId: string, text: string) => Promise<FigurePredictionResultDto | null>;
  /** The figures and pending lines under one passage. */
  under: (spanId: string | null | undefined) => { figures: FigureViewDto[]; pending: FigurePending[] };
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
  const [expandedId, setExpandedId] = useState<string | null>(null);
  // A build that lands after the source changed never shows on the new one.
  const generation = useRef(0);
  const runs = useRef(new Map<string, object>());
  const onBuiltRef = useRef(onBuilt);
  onBuiltRef.current = onBuilt;

  useEffect(() => {
    generation.current += 1;
    setFigures([]);
    setPending([]);
    setExpandedId(null);
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
      && JSON.stringify(item.region) === JSON.stringify(figure.region);
    setFigures((list) => [
      // A new version replaces the one it supersedes; a new build replaces an
      // earlier failed or unsupported line for the same request.
      ...list.filter((item) => item.figureId !== figure.figureId && item.figureId !== figure.supersedesId
        && !(sameRequest(item) && (item.verification === "failed" || item.verification === "unsupported"))),
      figure,
    ]);
  }, []);

  const run = useCallback(
    (key: string, anchorSpanId: string, start: () => Promise<LibraryJobDto<FigureBuildResultDto>>) => {
      const mine = generation.current;
      const token = {};
      runs.current.set(key, token);
      const live = () => generation.current === mine && runs.current.get(key) === token;
      let jobId: string | null = null;
      const retry = () => run(key, anchorSpanId, start);
      const cancel = () => {
        runs.current.delete(key);
        setPending((list) => list.filter((item) => item.key !== key));
        if (jobId) void Promise.resolve(api.readerFigureJobCancel({ jobId })).catch(() => undefined);
      };
      setPending((list) => [...list.filter((item) => item.key !== key), { key, anchorSpanId, state: "pending", message: null, code: null, retry, cancel }]);
      void (async () => {
        try {
          let job = await start();
          jobId = job.jobId;
          while (job.state === "pending") {
            await sleep(FIGURE_POLL_MS);
            if (!live()) return;
            job = await api.readerFigureJob({ jobId: job.jobId });
          }
          if (!live()) return;
          setPending((list) => list.filter((item) => item.key !== key));
          const figure = job.state === "done" ? job.result?.figure ?? null : null;
          const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative");
          if (figure && figure.supersedesId && !shown) {
            // A "not right?" version that did not verify: the earlier one stays.
            setPending((list) => [...list, { key, anchorSpanId, state: "failed", message: figure.reason ? `${frameBadge(figure.verification)} (${figure.reason})` : frameBadge(figure.verification), code: figure.verification, retry, cancel }]);
          } else if (figure) {
            land(figure);
            onBuiltRef.current?.(figure);
          }
        } catch (error) {
          if (!live()) return;
          const command = getCommandError(error);
          setPending((list) => list.map((item) => item.key === key
            ? { ...item, state: "failed", message: errorMessage(error), code: command?.code ?? null }
            : item));
        }
      })();
    },
    [land],
  );

  const request = useCallback(
    (input: FigureRequestInput) => {
      if (!enabled || !extractionId) return;
      const spanIds = [...new Set(input.spanIds)];
      const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? "";
      const region = input.region && contract?.region ? input.region : null;
      const key = `req:${anchor}:${spanIds.join(",")}:${region ? region.bbox.join(",") : ""}`;
      run(key, anchor, () => api.readerFigureRequest({ extractionId, spanIds, region }));
    },
    [enabled, extractionId, contract, run],
  );

  const revise = useCallback(
    (figure: FigureViewDto, note: string) => {
      if (!enabled || !contract?.revisions) return;
      run(`rev:${figure.figureId}`, figure.anchorSpanId ?? "", () => api.readerFigureRevise({ figureId: figure.figureId, note }));
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
      expandedId,
      setExpanded: setExpandedId,
      request,
      revise,
      predict,
      explain,
      under,
    }),
    [enabled, contract, figures, pending, expandedId, request, revise, predict, explain, under],
  );
}

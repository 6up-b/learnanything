// Reader workbench RW4b: the state behind the candidate view (spec §7.4).
//
// Given a landed `find_practice` result, it asks the server which of the
// proposal's textbook exercises may be shown and how each is offered (the
// sources service's exposure rule; exam and held-out material left out),
// then records the impressions of the ones it showed (the service's §6.5).
// A check that fails shows none of them (fail closed); the items are
// unaffected. "Find an exercise in my sources" runs only when the learner
// asks, and only while the fallback is on. Off (no `libraryExercises` in the
// prompt contract), it asks nothing. Both answer with a library job (never
// on the sidecar's request path): it is read, paced, until done, and a job
// whose answer is no longer wanted (another proposal, the pane closed) is
// cancelled and never read again.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ExerciseCandidatesDto, FindExercisesDto, FindPracticeResultDto, LibraryJobDto } from "../../api/dto";
import { fromFallback, fromProposal, proposalKeys, type ExerciseCandidate } from "./exerciseCandidates";
import { phaseForError, type ModelActionPhase } from "./ModelActionState";
import { JOB_POLL_MS } from "./useLibraryAsk";

/** Read a library job until it is done; null once no longer wanted (cancelled). */
async function finish<T>(started: Promise<LibraryJobDto<T>>, wanted: () => boolean): Promise<T | null> {
  let job = await started;
  while (job.state === "pending") {
    if (!wanted()) {
      void api.readerLibraryJobCancel({ jobId: job.jobId }).catch(() => undefined);
      return null;
    }
    await new Promise((resolve) => setTimeout(resolve, JOB_POLL_MS));
    if (!wanted()) {
      void api.readerLibraryJobCancel({ jobId: job.jobId }).catch(() => undefined);
      return null;
    }
    job = await api.readerLibraryJob<T>({ jobId: job.jobId });
  }
  return job.state === "done" && wanted() ? job.result : null;
}

export interface LibraryExercisesSettings {
  fallback: boolean;
}

export interface LibraryExercisesState {
  /** The proposal's exercises the learner may see now. */
  candidates: ExerciseCandidate[];
  /** The view's check: idle (nothing to check), pending, landed or failed. */
  viewPhase: "idle" | "pending" | "landed" | "failed";
  fallbackPhase: ModelActionPhase;
  fallbackCandidates: ExerciseCandidate[];
  fallbackFailure: string | null;
  findInSources: () => void;
}

export function useLibraryExercises({
  settings,
  practice,
  query,
  learningObjectIds,
  extractionId,
}: {
  settings: LibraryExercisesSettings | null;
  practice: FindPracticeResultDto | null;
  query: string;
  learningObjectIds: string[];
  extractionId: string | null;
}): LibraryExercisesState {
  const proposalId = practice?.proposalId ?? null;
  const [view, setView] = useState<{ proposalId: string; phase: "pending" | "landed" | "failed"; value: ExerciseCandidatesDto | null } | null>(null);
  const [fallback, setFallback] = useState<{ proposalId: string | null; phase: ModelActionPhase; value: FindExercisesDto | null; failure: string | null } | null>(null);
  const currentProposal = useRef<string | null>(null);
  currentProposal.current = proposalId;
  const mounted = useRef(true);
  useEffect(() => () => {
    mounted.current = false;
  }, []);

  useEffect(() => {
    setFallback(null);
    if (!settings || !practice || !proposalId) {
      setView(null);
      return undefined;
    }
    const keys = proposalKeys(practice);
    if (keys.length === 0) {
      setView(null);
      return undefined;
    }
    let live = true;
    setView({ proposalId, phase: "pending", value: null });
    finish(api.readerExerciseCandidates({ proposalId, keys }), () => live)
      .then((value) => {
        if (!live || value === null) return;
        setView({ proposalId, phase: "landed", value });
        const shown = fromProposal(practice, value);
        if (shown.length > 0) {
          // What the Reader showed (the sources service's impressions, §6.5).
          void api.recordProposalImpressions({
            proposalId, surface: "reader",
            keys: shown.map((candidate) => ({ kind: "source_exercise" as const, extractionId: candidate.extractionId, spanIds: candidate.spanIds })),
          }).catch(() => undefined);
        }
      })
      .catch(() => {
        if (live) setView({ proposalId, phase: "failed", value: null });
      });
    return () => {
      live = false;
    };
    // The proposal is immutable once landed: check it once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings?.fallback, Boolean(settings), proposalId]);

  const findInSources = useCallback(() => {
    if (!settings?.fallback || !query.trim()) return;
    const asked = currentProposal.current;
    setFallback({ proposalId: asked, phase: "pending", value: null, failure: null });
    finish(api.readerFindExercises({ query, learningObjectIds, extractionId }), () => mounted.current && currentProposal.current === asked)
      .then((value) => {
        if (value !== null && currentProposal.current === asked) setFallback({ proposalId: asked, phase: "landed", value, failure: null });
      })
      .catch((error) => {
        if (currentProposal.current === asked) {
          setFallback({ proposalId: asked, phase: phaseForError(error), value: null, failure: "Couldn't look for exercises in your books." });
        }
      });
  }, [settings?.fallback, query, learningObjectIds, extractionId]);

  const landed = view && view.proposalId === proposalId ? view : null;
  return {
    candidates: practice && landed?.phase === "landed" ? fromProposal(practice, landed.value) : [],
    viewPhase: landed ? landed.phase : "idle",
    fallbackPhase: fallback?.phase ?? "idle",
    fallbackCandidates: fromFallback(fallback?.value ?? null),
    fallbackFailure: fallback?.failure ?? null,
    findInSources,
  };
}

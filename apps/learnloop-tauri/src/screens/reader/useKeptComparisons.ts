// RW4d (spec §7.8; UX §3.4): the ⇄ marks of the open reading — each passage
// with a comparison the learner kept. The learner's own mark, outside the cue
// budget (it is never counted by the density setting). Read when the reading
// opens and again after a keep or a remove; off (no `compareKeep` in the
// contract) nothing is read and there are no marks.
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { KeptMarkDto, ReaderPromptContractDto } from "../../api/dto";
import { announceKeptChange, onKeptChange, type CompareKeepContextValue } from "./compareKeepContext";

const NO_MARKS: ReadonlyMap<string, KeptMarkDto> = new Map();

export function useKeptComparisons({
  contract,
  extractionId,
  sourceId,
  offline,
}: {
  contract: ReaderPromptContractDto | null | undefined;
  extractionId: string | null;
  sourceId: string | null;
  offline: boolean;
}) {
  const settings = contract?.compareKeep ?? null;
  const settingsKey = settings ? JSON.stringify(settings) : "";
  const [marks, setMarks] = useState<ReadonlyMap<string, KeptMarkDto>>(NO_MARKS);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!settingsKey || !extractionId || offline) {
      setMarks(NO_MARKS);
      return;
    }
    let cancelled = false;
    void api.readerKeptComparisons({ extractionId })
      .then((result) => {
        if (!cancelled) setMarks(new Map(result.marks.map((mark) => [mark.spanId, mark] as const)));
      })
      .catch(() => {
        // Marks are a convenience: an unreadable list shows none, quietly.
        if (!cancelled) setMarks(NO_MARKS);
      });
    return () => {
      cancelled = true;
    };
  }, [settingsKey, extractionId, offline, tick]);

  const reload = useCallback(() => setTick((value) => value + 1), []);
  // A keep made in another window (a Compare window beside this book) reads these marks again too.
  useEffect(() => onKeptChange(reload), [reload]);
  const context = useMemo<CompareKeepContextValue | null>(
    // eslint-disable-next-line react-hooks/exhaustive-deps
    () => (settings ? { settings, onChanged: announceKeptChange, openSourceId: sourceId } : null), [settingsKey, sourceId],
  );
  return { enabled: Boolean(settings), marks, reload, context };
}

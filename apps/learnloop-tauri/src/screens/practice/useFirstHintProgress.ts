// Adaptive difficulty AD1 (spec_adaptive_difficulty_v1 §5.3, §11.2): whether an
// answer had been started when the first hint of this attempt was revealed.
//
// The marker is the one the screen already sends with a tutor question
// (`no_draft` / `draft_started`), read at the first hint the learner sees of
// either kind: an item's own hint revealed on the answer box, or a hint the
// H2b panel delivered. It is set once and never moves; a restored draft keeps
// it (the sidecar stores it with the draft's retry key) and submit sends it.
// Off (the sidecar says `forecast_receipts` is off), it is never set and
// nothing is sent. Logged only: it changes nothing the learner sees.
import { useCallback, useRef, useState } from "react";
import type { FirstHintProgress } from "../../api/dto";

export interface FirstHintProgressMarker {
  /** The marker, once a first hint was revealed; null before (or when off). */
  value: FirstHintProgress | null;
  /** Set it from the progress at this reveal, if it is not set yet. */
  mark: (progress: FirstHintProgress) => void;
}

export function useFirstHintProgress(options: {
  enabled: boolean;
  restored?: FirstHintProgress | null;
}): FirstHintProgressMarker {
  const initial = options.enabled ? options.restored ?? null : null;
  const [value, setValue] = useState<FirstHintProgress | null>(initial);
  // Claimed synchronously, so two reveals in one tick keep the first.
  const claimed = useRef<FirstHintProgress | null>(initial);
  const enabled = options.enabled;
  const mark = useCallback((progress: FirstHintProgress) => {
    if (!enabled || claimed.current !== null) return;
    claimed.current = progress;
    setValue(progress);
  }, [enabled]);
  return { value: enabled ? value : null, mark };
}

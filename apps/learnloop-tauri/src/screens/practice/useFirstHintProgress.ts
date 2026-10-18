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
//
// AD1 fix round 4 (V4; §5.3's unknown-timing rule, G-AD1-10): a restored
// draft can carry hints whose timing was never saved (a draft from before
// AD1, or a book counted on the problem). The hook cannot tell "no hint yet"
// from "an earlier hint, timing unknown" by the marker alone, so the screen
// says whether a hint already happened (`hintsBefore`). With one and no
// saved marker, the first hint of this attempt is already behind it: the
// marker stays null (unknown) for the attempt, and a later reveal is never
// recorded as the first.
import { useCallback, useRef, useState } from "react";
import type { FirstHintProgress } from "../../api/dto";

export interface FirstHintProgressMarker {
  /** The marker, once a first hint was revealed; null before (or when off). */
  value: FirstHintProgress | null;
  /** Set it from the progress at this reveal, if it is not set yet. */
  mark: (progress: FirstHintProgress) => void;
  /** A hint whose timing is unknown happened (a book counted on the
   *  problem): with no marker claimed yet, none is recorded for the attempt. */
  noteUntimedHint: () => void;
}

export function useFirstHintProgress(options: {
  enabled: boolean;
  restored?: FirstHintProgress | null;
  /** A hint of either kind already happened (used or carried) before any
   *  marker was claimed: its timing is unknown, so none is recorded. */
  hintsBefore?: boolean;
}): FirstHintProgressMarker {
  const initial = options.enabled ? options.restored ?? null : null;
  const [value, setValue] = useState<FirstHintProgress | null>(initial);
  // Claimed synchronously, so two reveals in one tick keep the first.
  const claimed = useRef<FirstHintProgress | null>(initial);
  // Latched: once an earlier hint is known with no marker, this attempt's
  // first hint has passed unrecorded (V4).
  const unknown = useRef(false);
  if (options.hintsBefore && claimed.current === null) unknown.current = true;
  const enabled = options.enabled;
  const mark = useCallback((progress: FirstHintProgress) => {
    if (!enabled || claimed.current !== null || unknown.current) return;
    claimed.current = progress;
    setValue(progress);
  }, [enabled]);
  const noteUntimedHint = useCallback(() => {
    if (claimed.current === null) unknown.current = true;
  }, []);
  return { value: enabled ? value : null, mark, noteUntimedHint };
}

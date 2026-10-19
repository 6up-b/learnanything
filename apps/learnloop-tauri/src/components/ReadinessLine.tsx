// Adaptive difficulty AD2+AD3 (spec_adaptive_difficulty_v1 §9.5, §12, A4): an
// LO's readiness line from the subject view, always labelled as a prediction
// ("Top level for this goal: not yet shown · likely ready (a prediction)"). A
// cell with no answer of its own reads "untested" whatever the shared terms,
// couplings or reading predict; with `promoted_predictor` off the line reads
// "exam level: not yet predicted". A label beside the map, never a second depth
// (A9): it changes neither well depth nor the demonstrated beads.
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AdaptiveReadinessDto } from "../api/dto";
import { COLOR } from "./term";

export function ReadinessLine({ learningObjectId }: { learningObjectId: string }) {
  const [readiness, setReadiness] = useState<AdaptiveReadinessDto | null>(null);
  useEffect(() => {
    let alive = true;
    setReadiness(null);
    // A test double or an older client without the call: nothing shows.
    if (typeof api.adaptiveDifficultyReadiness !== "function") return;
    api
      .adaptiveDifficultyReadiness({ learningObjectId })
      .then((result) => {
        if (alive) setReadiness(result ?? null);
      })
      .catch(() => {
        // An older sidecar: no line.
      });
    return () => {
      alive = false;
    };
  }, [learningObjectId]);
  if (!readiness?.line) return null;
  return (
    <div data-testid="readiness-line" title={readiness.predicted ? "A prediction from your answers across this subject; demonstrated levels come only from answers at that level." : undefined}
         style={{ fontSize: 11, color: COLOR.textDim, margin: "4px 0" }}>
      {readiness.line}
    </div>
  );
}

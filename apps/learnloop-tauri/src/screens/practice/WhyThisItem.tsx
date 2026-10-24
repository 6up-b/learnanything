// Adaptive difficulty AD2+AD3 (spec_adaptive_difficulty_v1 §12, §6.1): "why
// this item", one quiet line by the draw that chose the served plan item:
//   band:      "Picked to be challenging but doable for you (about a 3 in 4 chance)"
//   overlap:   "A different kind of question, to keep LearnLoop's picture of you accurate"
//   calibrate: "A question to find your level here"
// The sidecar names the line (`adaptive_difficulty.why_item`); with no AD draw
// behind the item (below the successor, `selection` off, a predecessor serve,
// an older sidecar) nothing is shown. A read only: it changes nothing served.
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { COLOR } from "../../components/term";

export function WhyThisItem({ planPresentationId }: { planPresentationId: string | null | undefined }) {
  const [why, setWhy] = useState<string | null>(null);
  useEffect(() => {
    setWhy(null);
    if (!planPresentationId) return;
    let alive = true;
    // A test double or an older client without the call: nothing shows.
    if (typeof api.adaptiveDifficultyWhyItem !== "function") return;
    api
      .adaptiveDifficultyWhyItem({ planPresentationId })
      .then((result) => {
        if (alive) setWhy(result?.why ?? null);
      })
      .catch(() => {
        // An older sidecar, or no draw: the line simply does not show.
      });
    return () => {
      alive = false;
    };
  }, [planPresentationId]);
  if (!why) return null;
  return (
    <div data-testid="why-this-item" style={{ fontSize: 11, color: COLOR.textFaint, marginTop: 2 }}>
      {why}
    </div>
  );
}

// The phone's one waiting indicator (docs/reviews/ux-waiting.md), the desktop's
// (learnloop-tauri/src/components/Waiting.tsx) in the phone's own look: after a
// short delay a turning mark and one plain line saying what is happening, and
// for a usually long wait a second line saying what is normal. Mount it for as
// long as the wait lasts; unmounting is "done". The words are the desktop's
// (`@desktop/copy/waiting`), so both apps say the same thing about the same wait.
//
// - Nothing for the first WAIT_DELAY_MS: a fast tap must not flash a line.
// - The role="status" region is there from the first moment, empty, so a
//   screen reader announces the line when it is filled in.
// - The mark is hidden from assistive technology, and still under
//   prefers-reduced-motion (the CSS rule and the data-motion read below).
// - It holds no control: Back, Cancel and the tab bar stay where they are.
import { useEffect, useState } from "react";

export const WAIT_DELAY_MS = 350;
/** The phone's own true sentence about a grade (a closed app finds its result again, A4): said after the shared one. */
export const CAN_LEAVE = "You can leave; the result will be here when you come back.";
export const WAIT_LATER_MS = 5000;

function reducedMotion(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function Waiting({ line, later = null, testId = "waiting" }: { line: string; later?: string | null; testId?: string }) {
  const [stage, setStage] = useState<0 | 1 | 2>(0);
  const hasLater = Boolean(later);
  useEffect(() => {
    const shown = window.setTimeout(() => setStage((value) => (value === 0 ? 1 : value)), WAIT_DELAY_MS);
    const longer = hasLater ? window.setTimeout(() => setStage(2), WAIT_LATER_MS) : undefined;
    return () => {
      window.clearTimeout(shown);
      if (longer !== undefined) window.clearTimeout(longer);
    };
  }, [hasLater]);
  return (
    <div className="waiting" role="status" aria-live="polite" data-testid={testId}>
      {stage >= 1 ? (
        <>
          <p className="dim">
            <span className="wait-mark" data-motion={reducedMotion() ? "still" : "moving"} aria-hidden="true">◐</span> <span>{line}</span>
          </p>
          {stage === 2 && later ? <p className="dim wait-later" data-testid={`${testId}-later`}>{later}</p> : null}
        </>
      ) : null}
    </div>
  );
}

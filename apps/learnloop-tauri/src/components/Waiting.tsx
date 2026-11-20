// The one waiting indicator (docs/reviews/ux-waiting.md): wherever the learner
// waits more than a moment, a moving mark and one plain line saying what is
// happening, and for a usually long wait a quieter second line saying what is
// normal. Mount it for exactly as long as the wait lasts; unmounting is "done".
//
// - Nothing for the first WAIT_DELAY_MS: a fast step must not flash a line.
// - role="status" with a polite live region is rendered from the first moment,
//   empty, so a screen reader announces the line when it is filled in (a live
//   region inserted together with its text is often not announced).
// - The mark is hidden from assistive technology; the words are the message.
// - Still under prefers-reduced-motion, and wherever `still` is passed: the
//   Reader and the workbench never animate (G54, attentionBudget.test.tsx).
// - It holds no control and covers nothing: the controls that work during the
//   wait stay where they are, around it.
import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { COLOR, FONT_MONO } from "./term";

/** Long enough that a step answered at once never shows the line. */
export const WAIT_DELAY_MS = 350;
/** When a usually long wait adds its second line. */
export const WAIT_LATER_MS = 5000;

export interface WaitingProps {
  /** What is happening, in the learner's words ("Checking your answer…"). */
  line: string;
  /** The quieter second line for a usually long wait; omitted where nothing true can be said. */
  later?: string | null;
  /** The Reader posture: the mark does not move (G54). */
  still?: boolean;
  /** Controls that work during the wait and belong on its line (a hint's "use the item's hint instead"):
   *  shown from the first moment, never held back by the delay, and never remounted when the words appear. */
  children?: ReactNode;
  style?: CSSProperties;
  testId?: string;
}

function reducedMotion(): boolean {
  // jsdom and older webviews have no matchMedia: then the mark moves, as CSS also stills it under the media query.
  return typeof window !== "undefined" && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The moving mark alone, for a line that keeps its own layout and timing (the Reader's model actions):
 *  one mark for every wait in the app. Hidden from assistive technology; the words carry the message. */
export function WaitMark({ still = false }: { still?: boolean }) {
  const moving = !still && !reducedMotion();
  return <span className="ll-wait-mark" data-motion={moving ? "moving" : "still"} aria-hidden="true">◐</span>;
}

export function Waiting({ line, later = null, still = false, children, style, testId = "waiting" }: WaitingProps) {
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
  const moving = !still && !reducedMotion();
  return (
    <div role="status" aria-live="polite" data-testid={testId} data-waiting={stage === 0 ? "pending" : "shown"} style={style}>
      {stage >= 1 || children ? (
        <>
          <div style={{ color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 12, lineHeight: 1.6 }}>
            {stage >= 1 ? (
              <>
                <WaitMark still={!moving} /> <span>{line}</span>
              </>
            ) : null}
            {children}
          </div>
          {stage === 2 && later ? (
            // Quieter by size, not by colour: --faint is under WCAG's 4.5:1 for small text (voices.tsx).
            <div data-testid={`${testId}-later`} style={{ color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, lineHeight: 1.6, paddingLeft: "1.6em" }}>
              {later}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

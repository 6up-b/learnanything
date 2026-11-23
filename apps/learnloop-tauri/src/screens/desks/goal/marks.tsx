// Criticality marks, dimming and callouts on a reading's passages (spec §12.3, §12.4), laid over the Reader's
// passages through its lens hook: a 3 px bar 11 px left of the text, its why card on hover (120 ms) or tap,
// skippable and later text dimmed (never hidden), and a short dark callout at a section start on the path.
import { useEffect, useLayoutEffect, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import type { GoalBandDto } from "../../../api/dto";
import type { ReaderLens } from "../../ReaderScreen";
import type { WhyState } from "./controller";
import { calloutFor, goalShort, isDimmed, markKind, whyLevelLine, type LensIndex } from "./model";

/** The why card opens after a 120 ms hover (spec §12.3) and hides 160 ms after leaving (the mockup's). */
export const WHY_OPEN_MS = 120;
export const WHY_HIDE_MS = 160;

export interface MarkHandlers {
  /** Hover in (null: hover out), or a tap (toggle). */
  hover: (why: WhyState | null) => void;
  tap: (why: WhyState) => void;
}

function rectOf(event: ReactMouseEvent<HTMLElement>): WhyState["rect"] {
  const box = event.currentTarget.getBoundingClientRect();
  return { left: box.left, top: box.top, right: box.right, bottom: box.bottom };
}

/** The lens for one window's reading, or none (no goal, a paused window, a reading not read yet). */
export function readerLens({ index, dimOn, windowId, handlers, paper = false, openSpan = null }: {
  index: LensIndex | null;
  dimOn: boolean;
  windowId: string;
  handlers: MarkHandlers;
  /** A paper's section heads take the light one-line form. */
  paper?: boolean;
  /** The passage whose why card is open here: its mark stays lit. */
  openSpan?: string | null;
}): ReaderLens | null {
  if (!index) return null;
  return {
    className: (spanId) => {
      const section = index.bySpan.get(spanId);
      if (!section) return undefined;
      const kind = markKind(section.level);
      return [kind ? `g-${kind}` : "g-none", isDimmed(section, dimOn) ? "gl-dim" : ""].filter(Boolean).join(" ");
    },
    mark: (spanId) => {
      const section = index.bySpan.get(spanId);
      const kind = section ? markKind(section.level) : null;
      if (!section || !kind) return null;
      const why = (event: ReactMouseEvent<HTMLElement>): WhyState => ({ section, spanId, extractionId: index.extractionId, windowId, rect: rectOf(event) });
      return (
        <i
          className={`gm gl-${kind}${paper ? " gl-paper" : ""}${openSpan === spanId ? " on" : ""}`}
          data-gm={`${index.extractionId}:${spanId}`}
          aria-label={section.level.replace("_", " ")}
          role="button"
          tabIndex={-1}
          onMouseEnter={(event) => handlers.hover(why(event))}
          onMouseLeave={() => handlers.hover(null)}
          onClick={(event) => { event.stopPropagation(); handlers.tap(why(event)); }}
        />
      );
    },
    before: (spanId) => {
      const section = index.starts.get(spanId);
      const callout = section ? calloutFor(section) : null;
      if (!section || !callout) return null;
      if (paper) {
        return (
          <div className="gpcall" data-gcall={section.sectionId}>
            <span className="gg">◎</span> <b>{callout.label}:</b> {callout.body}
          </div>
        );
      }
      return (
        <div className="callout gcall" data-gcall={section.sectionId}>
          <span className="lab">◎ {callout.label}</span>
          {callout.body}
        </div>
      );
    },
  };
}

/** The why card (one at a time, at the shell): the level, "For <goal>: <why>.", the learner's part and the
 *  coverage line it comes from. While a check is due on its LO the backend sends only the neutral line. */
export function WhyCard({ why, band }: { why: WhyState; band: GoalBandDto | null }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [place, setPlace] = useState<{ left: number; top: number } | null>(null);
  const [shown, setShown] = useState(false);
  const { section } = why;
  useLayoutEffect(() => {
    const card = ref.current;
    if (!card) return;
    const width = card.offsetWidth;
    const height = card.offsetHeight;
    let left = why.rect.right + 10;
    if (left + width > window.innerWidth - 8) left = Math.max(8, why.rect.left - width - 10);
    const top = Math.max(46, Math.min(why.rect.top - 6, window.innerHeight - height - 34));
    setPlace({ left, top });
  }, [why]);
  useEffect(() => {
    if (!place) return;
    const frame = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(frame);
  }, [place]);
  const kind = markKind(section.level);
  const legend = kind === "later" || kind === "shown" ? "skip" : kind === "partial" ? "partial" : kind;
  const reason = section.reasonMd.replace(/\.?\s*$/, ".");
  return (
    <div
      ref={ref}
      className={`gwhy lv-${kind ?? "none"}${shown ? " on" : ""}`}
      role="tooltip"
      data-gwhy={section.sectionId}
      style={place ? { left: place.left, top: place.top } : { left: -9999, top: 0 }}
    >
      <div className="gwh"><i className={`b ${legend ?? ""}`} />{whyLevelLine(section, band)}<span className="grow" /></div>
      <div className="gwr"><b>For {goalShort(band)}:</b> {reason}{section.learnerLine ? ` ${section.learnerLine}` : ""}</div>
      {section.coverageLine || section.judgedPer ? (
        <div className="gwc">
          {section.coverageLine ?? ""}
          {section.coverageLine ? " · " : ""}judged per section
        </div>
      ) : null}
    </div>
  );
}

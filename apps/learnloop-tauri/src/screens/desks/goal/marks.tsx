// Criticality marks, dimming and callouts on a reading's passages (spec §12.3, §12.4), laid over the Reader's
// passages through its lens hook: a 3 px bar 11 px left of the text, its why card on hover (120 ms) or tap,
// skippable and later text dimmed (never hidden), and a short dark callout at a section start on the path.
import { useEffect, useLayoutEffect, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import type { GoalBandDto } from "../../../api/dto";
import type { ReaderLens } from "../../ReaderScreen";
import type { WatchLens } from "../../reader/YouTubeWatchPanel";
import type { WhyState } from "./controller";
import { calloutFor, goalShort, isDimmed, markKind, mostNeededSpan, noneNeeded, whyLevelLine, type LensIndex } from "./model";

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
  const markFor = (spanId: string, extra = "") => {
    const section = index.bySpan.get(spanId);
    const kind = section ? markKind(section.level) : null;
    if (!section || !kind) return null;
    const why = (event: ReactMouseEvent<HTMLElement>): WhyState => ({ section, spanId, extractionId: index.extractionId, windowId, rect: rectOf(event) });
    return (
        <i
          className={`gm gl-${kind}${paper ? " gl-paper" : ""}${extra}${openSpan === spanId ? " on" : ""}`}
          data-gm={`${index.extractionId}:${spanId}`}
          aria-label="Why this is suggested" title="Why this is suggested"
          role="button"
          tabIndex={-1}
          onMouseEnter={(event) => handlers.hover(why(event))}
          onMouseLeave={() => handlers.hover(null)}
          onClick={(event) => { event.stopPropagation(); handlers.tap(why(event)); }}
        />
    );
  };
  const classFor = (spanId: string, keep: boolean) => {
    const section = index.bySpan.get(spanId);
    if (!section) return undefined;
    const kind = markKind(section.level);
    // The learner's own highlight and the passage being read keep full colour (§12.3).
    return [kind ? `g-${kind}` : "g-none", isDimmed(section, dimOn) && !keep ? "gl-dim" : ""].filter(Boolean).join(" ");
  };
  return {
    className: (spanId, state) => classFor(spanId, Boolean(state?.annotated || state?.active || state?.reading)),
    mark: (spanId) => markFor(spanId),
    watch: watchLens(index, classFor, markFor),
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

function clock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** The lens over a video's transcript (§12.3 point 5, §12.4): each passage group by its most needed cue's section
 *  (a group crossing from a skippable section into a core one is core, never dimmed), the mark in the text column,
 *  the path's ranges as segments on the track, and a head saying where the video sits. */
function watchLens(index: LensIndex, classFor: (spanId: string, keep: boolean) => string | undefined,
                   markFor: (spanId: string, extra?: string) => ReturnType<NonNullable<ReaderLens["mark"]>>): WatchLens {
  const onPath = index.sections.filter((section) => section.mapping === "mapped" && (section.level === "core" || section.level === "supporting"));
  return {
    className: (spanIds) => {
      const spanId = mostNeededSpan(index, spanIds);
      const classes = spanId ? classFor(spanId, false) : undefined;
      return classes ? `tp ${classes}` : undefined;
    },
    mark: (spanIds) => {
      const spanId = mostNeededSpan(index, spanIds);
      return spanId ? markFor(spanId, " gl-tx") : null;
    },
    segments: onPath.map((section) => section.spanIds),
    head: (timeOf) => {
      const first = onPath[0];
      // "The rest" is called not needed only when every section off the path is known not needed now.
      const rest = noneNeeded(index.sections.filter((section) => !onPath.includes(section)));
      if (first) {
        // Every range on the path, not only the first (touching ranges read as one).
        const ranges: Array<{ start: number; end: number }> = [];
        for (const range of onPath.map((section) => timeOf(section.spanIds))) {
          if (!range) continue;
          const last = ranges[ranges.length - 1];
          if (last && range.start <= last.end) last.end = Math.max(last.end, range.end);
          else ranges.push({ ...range });
        }
        const times = ranges.map((range) => `${clock(range.start)}–${clock(range.end)}`).join(", ");
        const lo = first.learningObjects.find((entry) => entry.learningObjectId === first.determiningLoId);
        const role = first.reasonKey === "primary" ? "main reading for" : first.reasonKey === "alternate" ? "another explanation of"
          : first.reasonKey === "prerequisite" ? "background for" : "supporting";
        return (
          <div className="gtcall" data-goal-head="">
            <span className="gg">◎</span> <b>on your path{times ? ` · ${times}` : ""}</b>
            {first.held ? ` · ${first.reasonMd}` : ` · ${role}${lo?.title ? ` \u201c${lo.title}\u201d` : ""}: ${first.reasonMd.replace(/\.?\s*$/, "")}.`}
            {rest && index.sections.some((section) => section.level === "skippable") ? " The rest is not needed for your goal." : ""}
          </div>
        );
      }
      const skippable = index.sections.find((section) => section.level === "skippable" || section.level === "later");
      if (!skippable || !rest) return null;
      return (
        <div className="gtcall off" data-goal-head="">
          <span className="gg">◎</span> <b>Not needed for your goal</b> · {skippable.reasonMd.replace(/\.?\s*$/, "")}. Read it anyway, if you like.
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
          {section.coverageLine ? " · " : ""}Based on this section
        </div>
      ) : null}
    </div>
  );
}

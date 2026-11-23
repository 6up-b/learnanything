// Marks beside passages in the desk's source windows (spec §10.7, §10.12): ✎ where a pad block is linked to
// the passage (a click scrolls the pad to the block and flashes it), and a quiet ◌ where a carried question was
// carried from ("you carried: <the question> · since <date>"), never a nudge. A mark is placed at its passage's
// right edge in the stage's coordinates and follows scrolling; a paused window shows none.
import { useEffect, useState } from "react";
import type { CarriedQuestionDto } from "../../../api/dto";
import { WINDOW_ATTRIBUTE } from "../keys/listeners";

export interface PadLink {
  padId: string;
  blockId: string;
  extractionId: string;
  spanId: string;
  /** From the passage union: `needs_reanchor` when the link was made on another reading and its place here is a
   * guess to confirm. */
  alias?: "exact" | "needs_reanchor";
}

/** The passages showing in a window: its first and last spans in view (what the union read covers). */
export function visibleSpanRange(stage: HTMLElement, windowId: string): { from: string; to: string } | null {
  const host = stage.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"]`);
  if (!host) return null;
  const frame = host.getBoundingClientRect();
  const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")];
  const inView = spans.filter((element) => {
    const box = element.getBoundingClientRect();
    return box.bottom >= frame.top && box.top <= frame.bottom;
  });
  const shown = inView.length ? inView : spans;
  const id = (element: HTMLElement | undefined) => element?.getAttribute("data-span-id") ?? element?.getAttribute("data-transcript-span") ?? null;
  const from = id(shown[0]);
  const to = id(shown[shown.length - 1]);
  return from && to ? { from, to } : null;
}

interface Placed {
  key: string;
  kind: "pad" | "carried";
  top: number;
  left: number;
  link?: PadLink;
  carried?: CarriedQuestionDto;
}

/** A span id inside a quoted attribute selector. */
function quoted(value: string): string {
  return value.replace(/["\\]/g, "\\$&");
}

/** The windows' passages a mark belongs to, read from the DOM: [data-span-id] under each source window. */
export function placeMarks(stage: HTMLElement, windows: Array<{ windowId: string; extractionId: string }>, links: PadLink[], carried: CarriedQuestionDto[]): Placed[] {
  const origin = stage.getBoundingClientRect();
  const out: Placed[] = [];
  for (const { windowId, extractionId } of windows) {
    const host = stage.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"]`);
    if (!host || host.getAttribute("data-window-state") === "hidden" || host.getAttribute("data-window-state") === "offscreen") continue;
    const frame = host.getBoundingClientRect();
    const at = (spanId: string) => {
      const element = host.querySelector(`[data-span-id="${quoted(spanId)}"], [data-transcript-span="${quoted(spanId)}"]`);
      if (!element) return null;
      const box = element.getBoundingClientRect();
      if (box.bottom < frame.top || box.top > frame.bottom) return null;
      return { top: box.top - origin.top, left: Math.min(box.right, frame.right - 22) - origin.left + 4 };
    };
    for (const link of links) {
      if (link.extractionId !== extractionId) continue;
      const place = at(link.spanId);
      if (place) out.push({ key: `pad:${windowId}:${link.blockId}:${link.alias ?? ""}`, kind: "pad", ...place, link });
    }
    for (const question of carried) {
      const anchor = question.anchor as { extraction_id?: string; span_id?: string } | null;
      if (!question.carried || anchor?.extraction_id !== extractionId || !anchor.span_id) continue;
      const place = at(anchor.span_id);
      if (place) out.push({ key: `carried:${windowId}:${question.carriedId}:${question.version}`, kind: "carried", top: place.top + 18, left: place.left, carried: question });
    }
  }
  return out;
}

function sameMarks(a: Placed[], b: Placed[]): boolean {
  return a.length === b.length && a.every((mark, i) => mark.key === b[i].key && mark.top === b[i].top && mark.left === b[i].left);
}

export function PassageMarks({ stage, windows, links, carried, onOpenLink, onSurfaced, onMarkCarried }: {
  stage: HTMLElement | null;
  windows: Array<{ windowId: string; extractionId: string }>;
  links: PadLink[];
  carried: CarriedQuestionDto[];
  onOpenLink: (link: PadLink) => void;
  onSurfaced: (question: CarriedQuestionDto) => void;
  onMarkCarried: (question: CarriedQuestionDto, event: "fruitful" | "not_now" | "let_go") => void;
}) {
  const [placed, setPlaced] = useState<Placed[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const windowsKey = windows.map((each) => `${each.windowId}:${each.extractionId}`).join("|");
  useEffect(() => {
    if (!stage) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const next = placeMarks(stage, windows, links, carried);
      // Re-rendered only when a mark moved, came or went (the look-again timer must cost nothing at rest).
      setPlaced((now) => (sameMarks(now, next) ? now : next));
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    stage.addEventListener("scroll", schedule, { capture: true, passive: true });
    // The Reader renders its passages after this does: look again for a little while.
    const timer = setInterval(schedule, 1000);
    return () => {
      stage.removeEventListener("scroll", schedule, { capture: true });
      clearInterval(timer);
      if (frame) cancelAnimationFrame(frame);
    };
    // windowsKey stands for the windows' identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, windowsKey, links, carried]);
  // A carried question shown beside a passage is logged once (`surfaced`, a notice).
  useEffect(() => {
    for (const mark of placed) if (mark.carried) onSurfaced(mark.carried);
  }, [placed, onSurfaced]);
  return (
    <>
      {placed.map((mark) => mark.kind === "pad" ? (
        <button key={mark.key} type="button" className={`desk-pmark pad${mark.link?.alias === "needs_reanchor" ? " reanchor" : ""}`} style={{ top: mark.top, left: mark.left }}
          title={mark.link?.alias === "needs_reanchor" ? "your pad links here, from another reading of this book: its place may need re-anchoring" : "your pad links here"}
          aria-label="go to your pad's block" onClick={() => mark.link && onOpenLink(mark.link)}>✎</button>
      ) : (
        <div key={mark.key} className="desk-pmark carried" style={{ top: mark.top, left: mark.left }}>
          <button type="button" aria-label="a question you carried" onClick={() => setOpen((now) => (now === mark.key ? null : mark.key))}>◌</button>
          {open === mark.key && mark.carried ? (
            <div className="pop">
              <div>you carried: {mark.carried.text} · since {new Date(mark.carried.since).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</div>
              <div className="acts">
                <button type="button" onClick={() => { onMarkCarried(mark.carried as CarriedQuestionDto, "fruitful"); setOpen(null); }}>fruitful</button>
                <button type="button" onClick={() => { onMarkCarried(mark.carried as CarriedQuestionDto, "not_now"); setOpen(null); }}>not now</button>
                <button type="button" onClick={() => { onMarkCarried(mark.carried as CarriedQuestionDto, "let_go"); setOpen(null); }}>let it go</button>
              </div>
            </div>
          ) : null}
        </div>
      ))}
    </>
  );
}

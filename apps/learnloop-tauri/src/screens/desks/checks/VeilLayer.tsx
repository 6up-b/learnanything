// The veils of an open inline check (spec §12.6.3; RD7's frontend half). While a check is open everything on the page
// is held unless it is on the short list of safe things (`hold.ts`): the server's veils (its standing set) say which
// source passages stay held, and anything else no one listed is held by default. Each target keeps its place (nothing
// moves), its text turns transparent behind a blur, it takes no input and no focus, and a pill over it reads "hidden
// during this check · back when you answer". The pill is the one way through: "show it anyway" says what opening can
// cost, then records the exposure at once (`check.expose`) before the hold lifts; a refusal keeps it held.
//
// The page is held again on every change before it paints (a mutation observer, for as long as the check is open,
// whatever the veils): a new passage, window, tooltip or panel is held the moment it appears.
import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";
import type { CheckVeilRefDto } from "../../../api/dto";
import type { CheckDesk } from "./controller";
import { Holder, SAFE_ATTR, printOf, type HeldRegion, type HoldResult, type HoldWindow } from "./hold";
import { VEIL_LABEL, costOf, refKey, veilSelector } from "./model";

interface Pill {
  key: string;
  ref: CheckVeilRefDto | null;
  region: HeldRegion | null;
  left: number;
  top: number;
  arriving: boolean;
}

/** What can cover a held element from above (the companion, the card centred near the top, search, the goal band). */
const OCCLUDERS = "[data-companion-dock], [data-check-card='overlay'], [data-desk-search], .goalband";

/** The part of an element that shows (inside its window, its scroller and the viewport), or null. */
function shownBox(element: Element): DOMRect | null {
  const box = element.getBoundingClientRect();
  if (!box.width || !box.height) return null;
  const frames = [element.parentElement?.closest("[data-desk-pane-body]"), element.closest("[data-desk-window]")]
    .filter((each): each is Element => Boolean(each)).map((each) => each.getBoundingClientRect());
  if (typeof window !== "undefined") frames.push(new DOMRect(0, 0, window.innerWidth, window.innerHeight));
  const left = Math.max(box.left, ...frames.map((f) => f.left));
  const right = Math.min(box.right, ...frames.map((f) => f.right));
  const top = Math.max(box.top, ...frames.map((f) => f.top));
  const bottom = Math.min(box.bottom, ...frames.map((f) => f.bottom));
  if (right - left < 1 || bottom - top < 1) return null;
  return new DOMRect(left, top, right - left, bottom - top);
}

/** Where a pill goes: the middle of the part that shows (at most 120 px down), or nowhere when none of it shows or
 *  something covers that point. */
function placeOf(element: Element, root: ParentNode): { left: number; top: number } | null {
  const shown = shownBox(element);
  if (!shown) return null;
  const at = { left: shown.left + shown.width / 2, top: shown.top + Math.min(shown.height / 2, 120) };
  for (const cover of root.querySelectorAll(OCCLUDERS)) {
    if (cover.contains(element)) continue;
    const r = cover.getBoundingClientRect();
    if (at.left >= r.left && at.left <= r.right && at.top >= r.top && at.top <= r.bottom) return null;
  }
  return at;
}

function pillsOf(result: HoldResult, root: ParentNode, laidOut: boolean, judging: boolean): Pill[] {
  const pills: Pill[] = [];
  for (const { element, ref } of result.named) {
    // A page with no layout at all (jsdom) gives every held element its pill at the origin.
    const at = laidOut ? placeOf(element, root) : { left: 0, top: 0 };
    if (!at) continue;
    pills.push({ key: `${refKey(ref)}#${pills.length}`, ref, region: null, ...at, arriving: false });
  }
  for (const region of result.regions) {
    // One pill per region (its own opening: what the server does not describe, measured by nothing).
    if (region.quiet) continue;
    let best: { at: { left: number; top: number }; area: number } | null = null;
    for (const element of region.elements) {
      if (!laidOut) {
        best = { at: { left: 0, top: 0 }, area: 1 };
        break;
      }
      const shown = shownBox(element);
      if (!shown || (best && shown.width * shown.height <= best.area)) continue;
      const at = placeOf(element, root);
      if (at) best = { at, area: shown.width * shown.height };
    }
    if (!best) continue;
    pills.push({ key: `region:${region.region}#${pills.length}`, ref: null, region, ...best.at, arriving: region.unjudged && judging });
  }
  return pills;
}

function samePills(a: readonly Pill[], b: readonly Pill[]): boolean {
  return a.length === b.length && a.every((pill, i) => pill.key === b[i].key && pill.left === b[i].left && pill.top === b[i].top
    && pill.arriving === b[i].arriving && pill.region?.print === b[i].region?.print);
}

/** What a named veil's elements show now (the print an opening is kept against). */
function printsOf(root: Element | null, ref: CheckVeilRefDto): string {
  const selector = veilSelector(ref);
  return root && selector ? [...root.querySelectorAll(selector)].map(printOf).join("#") : "";
}

/** The desks' windows, as the hold reads them (only a passages window's text can show). */
export type HoldWindows = ReadonlyMap<string, HoldWindow>;

/** `onChange`: the page changed under an open check (new windows or passages may be in view); the desks ask the
 *  server to judge them (check.protect_more, which sends nothing when nothing in view changed). */
export function VeilLayer({ desk, root, windows, onChange }: { desk: CheckDesk; root: Element | null; windows: HoldWindows; onChange?: () => void }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const holding = desk.holding();
  const version = desk.getVersion();
  const [pills, setPills] = useState<Pill[]>([]);
  const [asking, setAsking] = useState<Pill | null>(null);
  const holder = useRef<Holder | null>(null);
  holder.current ??= new Holder();
  const frame = useRef(0);
  const changed = useRef(onChange);
  changed.current = onChange;
  const windowsRef = useRef(windows);
  windowsRef.current = windows;

  const hold = useRef<() => HoldResult | null>(() => null);
  hold.current = () => {
    if (!root || !desk.holding()) return null;
    const result = holder.current!.apply(root, {
      named: desk.veils(), opened: desk.openedRefs(), openedRegions: desk.openedRegions(), windows: windowsRef.current,
      passageJudged: (windowId, extractionId, spanId) => desk.passageJudged(windowId, extractionId, spanId),
    });
    for (const { key, print } of result.printed) desk.notePrint(key, print);
    for (const key of result.changed) desk.rehold(key);
    return result;
  };
  const place = useRef<() => void>(() => undefined);
  place.current = () => {
    const result = hold.current();
    if (!result || !root) return;
    const laidOut = root.ownerDocument.documentElement.getBoundingClientRect().width > 0;
    const next = pillsOf(result, root, laidOut, desk.judging());
    setPills((now) => (samePills(now, next) ? now : next));
  };

  useLayoutEffect(() => {
    if (!root || !holding) {
      holder.current?.releaseAll();
      setPills((now) => (now.length ? [] : now));
      setAsking(null);
      return;
    }
    const run = () => {
      frame.current = 0;
      changed.current?.();
      place.current();
    };
    run();
    const schedule = () => {
      if (!frame.current) frame.current = requestAnimationFrame(run);
    };
    // Anything new is held before it paints (the observer's callback runs before the next frame; holding what is
    // already held changes nothing, so it settles). It stays connected for the whole check, veils or none.
    const observer = new MutationObserver(() => {
      hold.current();
      schedule();
    });
    observer.observe(root, { subtree: true, childList: true, characterData: true, attributes: true,
      attributeFilter: ["class", "inert", "aria-hidden", "title", "aria-label", "data-check-content", SAFE_ATTR, "data-passage-text", "data-block"] });
    addEventListener("scroll", schedule, { capture: true, passive: true });
    addEventListener("resize", schedule);
    // A panel that slides in (the companion) moves without changing the page: its pill is placed again when it lands.
    addEventListener("transitionend", schedule, { capture: true });
    addEventListener("animationend", schedule, { capture: true });
    return () => {
      observer.disconnect();
      removeEventListener("scroll", schedule, { capture: true });
      removeEventListener("resize", schedule);
      removeEventListener("transitionend", schedule, { capture: true });
      removeEventListener("animationend", schedule, { capture: true });
      if (frame.current) cancelAnimationFrame(frame.current);
      frame.current = 0;
    };
  }, [root, holding, desk]);

  // Every change in the store (a reply's standing set, an opening, a judged passage) is held again at once.
  useLayoutEffect(() => {
    if (holding) place.current();
  }, [version, holding]);

  // Every hold lifted when the layer goes (answered, not now, the desks closed).
  useEffect(() => () => holder.current?.releaseAll(), []);

  if (!holding || !pills.length) return null;
  return (
    <div className="ck-veil-layer" data-check-veils="" {...{ [SAFE_ATTR]: "" }}>
      {pills.map((pill) => (
        pill.arriving ? (
          // What just came into view: held until the server has judged it, and not openable before.
          <button key={pill.key} type="button" className="ck-pill" style={{ left: pill.left, top: pill.top }}
            data-veil-ref={pill.ref ? refKey(pill.ref) : `region:${pill.region?.region}`} data-veil-arriving="" disabled title="checking what this shows">{VEIL_LABEL}</button>
        ) : (
          <button key={pill.key} type="button" className="ck-pill" style={{ left: pill.left, top: pill.top }}
            data-veil-ref={pill.ref ? refKey(pill.ref) : `region:${pill.region?.region}`}
            {...(pill.region ? { "data-veil-region": pill.region.region } : {})}
            title="show it anyway" onClick={() => setAsking(pill)}>{VEIL_LABEL}</button>
        )
      ))}
      {asking ? (
        <div className="ck-ask" role="dialog" aria-label="show it anyway?" style={{ left: asking.left, top: asking.top + 18 }}>
          <b>show it anyway?</b> <span className="faint">{asking.ref?.group ?? (asking.region?.windowId ? "this window's other parts" : asking.region?.region)}</span>
          <p>{costOf(asking.ref)}</p>
          <div className="ck-ask-b">
            <button type="button" className="act" onClick={() => setAsking(null)}>keep it hidden</button>
            <button type="button" className="act pri" onClick={() => {
              const pill = asking;
              setAsking(null);
              if (pill.ref) void desk.expose(pill.ref, printsOf(root, pill.ref));
              else if (pill.region) void desk.exposeRegion(pill.region.region, pill.region.windowId, pill.region.print);
            }}>show it</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

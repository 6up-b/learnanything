// The veils of an open inline check (spec §12.6.3; RD7's frontend half), laid over whatever the server named: each
// target keeps its place (nothing moves), its text turns transparent behind a blur and takes no input, and a pill over
// it reads "hidden during this check · back when you answer". The pill is the one way through: "show it anyway" says
// what opening can cost, then records the exposure at once (`check.expose`) before the veil lifts.
//
// The targets are found in the page by the server's refs (`veilSelector`) and marked with a class; a re-render that
// rewrites an element's class is marked again before it paints (a mutation observer), so no component has to know.
import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";
import type { CheckVeilRefDto } from "../../../api/dto";
import type { CheckDesk } from "./controller";
import { SHOW_ANYWAY_COST, SHOW_NOTE_COST, VEIL_LABEL, refKey, veilIsNote, veilSelector } from "./model";

const MARK = "ck-veiled";
const UNVEIL_MS = 700;

interface Pill {
  key: string;
  ref: CheckVeilRefDto;
  left: number;
  top: number;
}

/** What can cover a veiled element from above (the companion, the card centred near the top, search, the goal band). */
const OCCLUDERS = "[data-companion-dock], [data-check-card='overlay'], [data-desk-search], .goalband";

/** Where a veil's pill goes: the middle of the part of the element that shows (inside its window and the viewport, at
 *  most 120 px down), or nowhere when none of it shows (a hidden desk, scrolled away, under the companion). */
function placeOf(element: Element, root: ParentNode): { left: number; top: number } | null {
  const box = element.getBoundingClientRect();
  if (!box.width || !box.height) return null;
  // Clipped by the window's scroller (a passage scrolled away shows nothing), the window and the viewport.
  const frames = [element.parentElement?.closest("[data-desk-pane-body]"), element.closest("[data-desk-window]")]
    .filter((each): each is Element => Boolean(each)).map((each) => each.getBoundingClientRect());
  if (typeof window !== "undefined") frames.push(new DOMRect(0, 0, window.innerWidth, window.innerHeight));
  const left = Math.max(box.left, ...frames.map((f) => f.left));
  const right = Math.min(box.right, ...frames.map((f) => f.right));
  const top = Math.max(box.top, ...frames.map((f) => f.top));
  const bottom = Math.min(box.bottom, ...frames.map((f) => f.bottom));
  if (right - left < 1 || bottom - top < 1) return null;
  const at = { left: (left + right) / 2, top: top + Math.min((bottom - top) / 2, 120) };
  for (const cover of root.querySelectorAll(OCCLUDERS)) {
    if (cover.contains(element)) continue;
    const r = cover.getBoundingClientRect();
    if (at.left >= r.left && at.left <= r.right && at.top >= r.top && at.top <= r.bottom) return null;
  }
  return at;
}

function element0(wanted: Map<Element, CheckVeilRefDto>): Element | null {
  for (const element of wanted.keys()) return element;
  return null;
}

/** Mark what the veils cover and say where their pills go (one per covered element). */
export function applyVeils(root: ParentNode, veils: readonly CheckVeilRefDto[]): Pill[] {
  const wanted = new Map<Element, CheckVeilRefDto>();
  for (const ref of veils) {
    const selector = veilSelector(ref);
    if (!selector) continue;
    for (const element of root.querySelectorAll(selector)) if (!wanted.has(element)) wanted.set(element, ref);
  }
  for (const element of [...root.querySelectorAll(`.${MARK}`)]) {
    if (wanted.has(element)) continue;
    element.classList.remove(MARK, "veiled");
    element.removeAttribute("data-veil");
    element.classList.add("unveil");
    setTimeout(() => element.classList.remove("unveil"), UNVEIL_MS);
  }
  const pills: Pill[] = [];
  const laidOut = (element0(wanted)?.ownerDocument.documentElement.getBoundingClientRect().width ?? 0) > 0;
  for (const [element, ref] of wanted) {
    if (!element.classList.contains(MARK)) element.classList.add(MARK, "veiled");
    if (element.getAttribute("data-veil") !== VEIL_LABEL) element.setAttribute("data-veil", VEIL_LABEL);
    // A page with no layout at all (jsdom) gives every covered element its pill at the origin.
    const at = laidOut ? placeOf(element, root) : { left: 0, top: 0 };
    if (at) pills.push({ key: `${refKey(ref)}#${pills.length}`, ref, ...at });
  }
  return pills;
}

/** `onChange`: the page changed under an open check (new windows or passages may be in view); the desks ask the
 *  server to judge them (check.protect_more, which sends nothing when nothing in view changed). */
export function VeilLayer({ desk, root, onChange }: { desk: CheckDesk; root: ParentNode | null; onChange?: () => void }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const veils = desk.veils();
  const veilsKey = veils.map(refKey).join("|");
  const [pills, setPills] = useState<Pill[]>([]);
  const [asking, setAsking] = useState<Pill | null>(null);
  const frame = useRef(0);
  const current = useRef(veils);
  current.current = veils;
  const changed = useRef(onChange);
  changed.current = onChange;

  useLayoutEffect(() => {
    if (!root) return;
    const run = () => {
      frame.current = 0;
      changed.current?.();
      const next = applyVeils(root, current.current);
      setPills((now) => (JSON.stringify(now) === JSON.stringify(next) ? now : next));
    };
    run();
    if (!veils.length) return;
    const schedule = () => {
      if (!frame.current) frame.current = requestAnimationFrame(run);
    };
    // A re-render that rewrote a veiled element's class, or new content, is marked again before it paints (the
    // observer's callback runs before the next frame; marking what is already marked changes nothing, so it settles).
    const observer = new MutationObserver(() => {
      applyVeils(root, current.current);
      schedule();
    });
    observer.observe(root instanceof Document ? root.body : (root as Node), { subtree: true, childList: true, attributes: true, attributeFilter: ["class"] });
    addEventListener("scroll", schedule, { capture: true, passive: true });
    addEventListener("resize", schedule);
    return () => {
      observer.disconnect();
      removeEventListener("scroll", schedule, { capture: true });
      removeEventListener("resize", schedule);
      if (frame.current) cancelAnimationFrame(frame.current);
      frame.current = 0;
    };
    // veilsKey stands for the veils' identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [root, veilsKey]);

  // Every veil lifted (answered, not now): nothing is left marked.
  useEffect(() => () => { if (root) applyVeils(root, []); }, [root]);

  if (!pills.length) return null;
  return (
    <div className="ck-veil-layer" data-check-veils="">
      {pills.map((pill) => (
        desk.arrivingVeil(pill.ref) ? (
          // A window that just came into view: veiled whole until the server has judged it, and not openable before.
          <button key={pill.key} type="button" className="ck-pill" style={{ left: pill.left, top: pill.top }} data-veil-ref={refKey(pill.ref)}
            data-veil-arriving="" disabled title="checking what this shows">{VEIL_LABEL}</button>
        ) : (
          <button key={pill.key} type="button" className="ck-pill" style={{ left: pill.left, top: pill.top }} data-veil-ref={refKey(pill.ref)}
            title="show it anyway" onClick={() => setAsking(pill)}>{VEIL_LABEL}</button>
        )
      ))}
      {asking ? (
        <div className="ck-ask" role="dialog" aria-label="show it anyway?" style={{ left: asking.left, top: asking.top + 18 }}>
          <b>show it anyway?</b> <span className="faint">{asking.ref.group}</span>
          <p>{veilIsNote(asking.ref) ? SHOW_NOTE_COST : SHOW_ANYWAY_COST}</p>
          <div className="ck-ask-b">
            <button type="button" className="act" onClick={() => setAsking(null)}>keep it hidden</button>
            <button type="button" className="act pri" onClick={() => { const ref = asking.ref; setAsking(null); void desk.expose(ref); }}>show it</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

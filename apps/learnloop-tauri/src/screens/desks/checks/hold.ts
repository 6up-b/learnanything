// What an open inline check holds (spec §12.6.3): everything on the page, unless it is on a short list of things that
// are safe to show. A surface nobody thought of (a new window kind, a tooltip, a portal, a panel, an overlay) is held
// by default; a missed surface is the costly direction, so nothing has to opt in to being covered.
//
// Safe, and so left as it is:
// - an element marked `data-check-safe`: the check's card and markers, the veils' pills, the windows' heads (which
//   show neutral titles while a check is open), the desk tabs and header buttons, the app's places, a toast that
//   says why something waits. A component marks itself safe only for what it shows while a check is open;
// - a source's own text (`data-passage-text`) in a passage the server has judged for this check and does not veil
//   (the server's standing set). A passage not judged yet (new, or on a desk not visited) stays held until a
//   protect request's reply covers it;
// - what the learner opened through "show it anyway": a named veil (by the server's ref) or a region (the shelf, a
//   band, a window's other parts), each as it showed then. If it shows something else later (`data-check-content`,
//   a pad's blocks), it is held again.
//
// Everything else is held in place: nothing moves; its text turns transparent behind a blur; canvases, players and
// frames are not painted; it takes no pointer, no focus (`inert`) and is hidden from assistive technology
// (`aria-hidden`); its title and accessible labels are taken off while held and put back after. A container of
// something safe is not held itself (its other children are), but loses its title and labels the same way.
import type { CheckVeilRefDto } from "../../../api/dto";
import { VEIL_LABEL, passagesCanShow, refKey, veilSelector } from "./model";

export const SAFE_ATTR = "data-check-safe";
export const PASSAGE_TEXT_ATTR = "data-passage-text";
/** A part of the page with its own "show it anyway" (the shelf, the goal band, the companion, the pen layer). */
export const REGION_ATTR = "data-check-region";
/** A region whose held parts have no pill (static chrome nobody needs to open). */
export const QUIET_ATTR = "data-check-region-quiet";
/** What a component shows (a tab, a page, the exchanges in view): an opening covers only what it showed then. */
export const CONTENT_ATTR = "data-check-content";

/** Attributes that can carry content and are taken off a held element or a container while a check is open. */
const LABELS = ["title", "aria-label", "aria-description", "aria-roledescription", "aria-valuetext", "placeholder", "alt"] as const;

const HELD = "ck-held";
const NAMED = "ck-veiled";
const NAMED_LOOK = "veiled";
const UNVEIL_MS = 700;

/** The region every element outside a named region belongs to. */
export const DESK_REGION = "the desk";

export interface HoldWindow {
  kind: string;
  extractionId: string | null;
}

export interface HoldInput {
  /** The server's standing veils the learner has not opened. */
  named: readonly CheckVeilRefDto[];
  /** The named veils the learner opened, with what they showed then ("" when not known: taken as it is now). */
  opened: ReadonlyArray<{ ref: CheckVeilRefDto; print: string }>;
  /** The regions the learner opened, with what they showed then. */
  openedRegions: ReadonlyMap<string, string>;
  /** The desks' windows by id (only a source or video window's passages can be safe). */
  windows: ReadonlyMap<string, HoldWindow>;
  passageJudged(windowId: string, extractionId: string | null, spanId: string): boolean;
}

export interface HeldNamed {
  element: Element;
  ref: CheckVeilRefDto;
  region: string;
}

export interface HeldRegion {
  region: string;
  windowId: string | null;
  quiet: boolean;
  elements: Element[];
  /** Whether everything held here is a passage the server has not judged yet. */
  unjudged: boolean;
  print: string;
}

export interface HoldResult {
  named: HeldNamed[];
  regions: HeldRegion[];
  /** Openings (a named veil's key, a region) that show something else than when opened: held again. */
  changed: string[];
  /** Named openings whose print was not known (after a restart): what they show now. */
  printed: Array<{ key: string; print: string }>;
}

interface Stash {
  labels: Map<string, string | null>;
  inert: string | null;
  hidden: string | null;
  key: string;
}

/** What an element shows, for an opening's "still the same?": its content marks and pad blocks, in order. */
export function printOf(element: Element): string {
  const parts: string[] = [];
  const own = element.getAttribute(CONTENT_ATTR);
  if (own !== null) parts.push(own);
  for (const each of element.querySelectorAll(`[${CONTENT_ATTR}], [data-block]`)) {
    parts.push(each.getAttribute(CONTENT_ATTR) ?? `b:${each.getAttribute("data-block")}`);
  }
  return parts.join("|");
}

function regionHere(element: Element, outer: string): string {
  const named = element.getAttribute(REGION_ATTR);
  if (named) return named;
  const windowId = element.getAttribute("data-desk-window");
  if (windowId) return `window:${windowId}`;
  return outer;
}

/** A value inside a quoted attribute selector. */
function attr(value: string): string {
  return value.replace(/["\\]/g, "\\$&");
}

function passageOf(element: Element): Element | null {
  return element.closest("[data-span-id], [data-transcript-span]");
}

/** Holds and releases; one per page (it remembers what it took off each element to put it back). */
export class Holder {
  private held = new Map<Element, Stash>();
  private containers = new Map<Element, Map<string, string | null>>();

  apply(root: Element, input: HoldInput): HoldResult {
    const namedOf = new Map<Element, CheckVeilRefDto>();
    for (const ref of input.named) {
      const selector = veilSelector(ref);
      if (!selector) continue;
      for (const element of root.querySelectorAll(selector)) if (!namedOf.has(element)) namedOf.set(element, ref);
    }
    const changed: string[] = [];
    const printed: HoldResult["printed"] = [];
    // Opened named veils: whole, unless what they show changed. A passage or a source window's whole-window veil
    // opens its passages (judged, no longer named), never the window's other parts.
    const allowed = new Set<Element>();
    for (const { ref, print } of input.opened) {
      if (ref.kind === "span") continue;
      if (ref.kind === "window" && typeof ref.window_id === "string" && passagesCanShow(input.windows.get(ref.window_id)?.kind ?? "")) continue;
      const selector = veilSelector(ref);
      if (!selector) continue;
      const elements = [...root.querySelectorAll(selector)];
      const now = elements.map(printOf).join("#");
      const key = refKey(ref);
      if (print === "" && now !== "") printed.push({ key, print: now });
      else if (print !== now) {
        changed.push(key);
        continue;
      }
      for (const element of elements) allowed.add(element);
    }
    for (const element of root.querySelectorAll(`[${SAFE_ATTR}]`)) allowed.add(element);
    for (const element of root.querySelectorAll(`[${PASSAGE_TEXT_ATTR}]`)) if (this.passageSafe(element, namedOf, input)) allowed.add(element);
    const openRegions = new Map<string, Element>();
    for (const [region] of input.openedRegions) {
      const host = region.startsWith("window:") ? root.querySelector(`[data-desk-window="${attr(region.slice(7))}"]`)
        : root.querySelector(`[${REGION_ATTR}="${attr(region)}"]`) ?? (region === DESK_REGION ? root : null);
      const now = host ? printOf(host) : "";
      if (now !== input.openedRegions.get(region)) changed.push(region);
      else openRegions.set(region, host ?? root);
    }
    // The ancestors of what is safe are containers; of what is named, places to look inside an opened region.
    const containers = new Set<Element>();
    const markUp = (from: Element, into: Set<Element>) => {
      for (let at = from.parentElement; at && !into.has(at); at = at.parentElement) {
        into.add(at);
        if (at === root) break;
      }
    };
    for (const element of allowed) markUp(element, containers);
    const namedAbove = new Set<Element>();
    for (const element of namedOf.keys()) markUp(element, namedAbove);

    const holdNow = new Map<Element, { ref: CheckVeilRefDto | null; region: string }>();
    const containerNow = new Set<Element>();
    const walk = (element: Element, named: CheckVeilRefDto | null, outer: string) => {
      if (allowed.has(element)) return;
      const region = regionHere(element, outer);
      const own = namedOf.get(element) ?? named;
      if (!own && openRegions.has(region)) {
        // An opened region shows its own parts; a named veil inside it still holds.
        if (!namedAbove.has(element)) return;
        for (const child of element.children) walk(child, null, region);
        return;
      }
      if (containers.has(element)) {
        containerNow.add(element);
        for (const child of element.children) walk(child, own, region);
        return;
      }
      holdNow.set(element, { ref: own, region });
    };
    if (allowed.has(root)) {
      // Nothing to hold on a page that is itself safe.
    } else if (containers.has(root)) {
      containerNow.add(root);
      for (const child of root.children) walk(child, namedOf.get(root) ?? null, regionHere(root, DESK_REGION));
    } else {
      walk(root, null, DESK_REGION);
    }

    // Apply: release what is no longer held, hold what is, strip the containers.
    for (const [element, stash] of [...this.held]) {
      const next = holdNow.get(element);
      if (next && this.keyOf(next) === stash.key) continue;
      this.release(element, stash, Boolean(next));
    }
    for (const [element, at] of holdNow) this.hold(element, this.keyOf(at), at.ref !== null);
    for (const [element, labels] of [...this.containers]) {
      if (containerNow.has(element) && !holdNow.has(element)) continue;
      restoreLabels(element, labels);
      this.containers.delete(element);
    }
    for (const element of containerNow) {
      if (holdNow.has(element)) continue;
      const labels = this.containers.get(element) ?? new Map<string, string | null>();
      stripLabels(element, labels);
      this.containers.set(element, labels);
    }
    this.moveFocusOut(root);

    // What has a pill: each named element; each region's held parts (one pill), unless a named veil in it shows.
    const named: HeldNamed[] = [];
    const regions = new Map<string, HeldRegion>();
    for (const [element, at] of holdNow) {
      if (at.ref) {
        named.push({ element, ref: at.ref, region: at.region });
        continue;
      }
      const entry = regions.get(at.region) ?? {
        region: at.region, windowId: at.region.startsWith("window:") ? at.region.slice(7) : null,
        quiet: Boolean(element.closest(`[${QUIET_ATTR}]`)), elements: [], unjudged: true, print: "",
      };
      entry.elements.push(element);
      if (!this.unjudgedPassage(element, input)) entry.unjudged = false;
      regions.set(at.region, entry);
    }
    for (const entry of regions.values()) {
      const host = entry.windowId ? root.querySelector(`[data-desk-window="${attr(entry.windowId)}"]`)
        : root.querySelector(`[${REGION_ATTR}="${attr(entry.region)}"]`) ?? (entry.region === DESK_REGION ? root : null);
      entry.print = host ? printOf(host) : "";
    }
    return { named, regions: [...regions.values()], changed, printed };
  }

  /** Every hold released and every label put back (the check is answered or set aside). */
  releaseAll(): void {
    for (const [element, stash] of [...this.held]) this.release(element, stash, false);
    for (const [element, labels] of [...this.containers]) restoreLabels(element, labels);
    this.containers.clear();
  }

  private keyOf(at: { ref: CheckVeilRefDto | null; region: string }): string {
    return at.ref ? `named:${refKey(at.ref)}` : `region:${at.region}`;
  }

  private passageSafe(text: Element, namedOf: Map<Element, CheckVeilRefDto>, input: HoldInput): boolean {
    const passage = passageOf(text);
    const host = text.closest("[data-desk-window]");
    if (!passage || !host) return false;
    const windowId = host.getAttribute("data-desk-window") ?? "";
    const window = input.windows.get(windowId);
    if (!window || !passagesCanShow(window.kind)) return false;
    const spanId = passage.getAttribute("data-span-id") ?? passage.getAttribute("data-transcript-span") ?? "";
    if (!spanId || !input.passageJudged(windowId, window.extractionId, spanId)) return false;
    for (let at: Element | null = text; at && at !== host.parentElement; at = at.parentElement) if (namedOf.has(at)) return false;
    return true;
  }

  private unjudgedPassage(element: Element, input: HoldInput): boolean {
    const passage = element.matches("[data-span-id], [data-transcript-span]") ? element : null;
    if (!passage) return false;
    const host = passage.closest("[data-desk-window]");
    const windowId = host?.getAttribute("data-desk-window") ?? "";
    const window = input.windows.get(windowId);
    const spanId = passage.getAttribute("data-span-id") ?? passage.getAttribute("data-transcript-span") ?? "";
    return Boolean(window) && !input.passageJudged(windowId, window?.extractionId ?? null, spanId);
  }

  private hold(element: Element, key: string, named: boolean): void {
    let stash = this.held.get(element);
    if (stash) stash.key = key;
    else {
      stash = { labels: new Map(), inert: element.getAttribute("inert"), hidden: element.getAttribute("aria-hidden"), key };
      this.held.set(element, stash);
      // A player under a hold stops (an iframe player is told by its own window, which hears the hold).
      for (const media of element.querySelectorAll("video, audio")) (media as HTMLMediaElement).pause?.();
      if (element instanceof HTMLMediaElement) element.pause?.();
    }
    stripLabels(element, stash.labels);
    const look = named ? [NAMED, NAMED_LOOK] : [HELD];
    for (const name of look) if (!element.classList.contains(name)) element.classList.add(name);
    for (const name of named ? [HELD] : [NAMED, NAMED_LOOK]) if (element.classList.contains(name)) element.classList.remove(name);
    if (named) {
      if (element.getAttribute("data-veil") !== VEIL_LABEL) element.setAttribute("data-veil", VEIL_LABEL);
    } else if (element.hasAttribute("data-veil")) element.removeAttribute("data-veil");
    if (!element.hasAttribute("inert")) element.setAttribute("inert", "");
    if (element.getAttribute("aria-hidden") !== "true") element.setAttribute("aria-hidden", "true");
  }

  private release(element: Element, stash: Stash, keep: boolean): void {
    const wasNamed = element.classList.contains(NAMED);
    element.classList.remove(HELD, NAMED, NAMED_LOOK);
    element.removeAttribute("data-veil");
    // Held again under another key at once (by hold): only the look changes.
    if (keep) return;
    this.held.delete(element);
    restoreLabels(element, stash.labels);
    if (stash.inert === null) element.removeAttribute("inert");
    else element.setAttribute("inert", stash.inert);
    if (stash.hidden === null) element.removeAttribute("aria-hidden");
    else element.setAttribute("aria-hidden", stash.hidden);
    if (wasNamed) {
      element.classList.add("unveil");
      setTimeout(() => element.classList.remove("unveil"), UNVEIL_MS);
    }
  }

  private moveFocusOut(root: Element): void {
    const active = root.ownerDocument.activeElement;
    if (!active || active === root.ownerDocument.body) return;
    for (const element of this.held.keys()) {
      if (!element.contains(active)) continue;
      const answer = root.querySelector<HTMLElement>("[data-check-card] textarea");
      if (answer && !answer.closest(`.${HELD}, .${NAMED}`)) answer.focus();
      else (active as HTMLElement).blur?.();
      return;
    }
  }
}

function stripLabels(element: Element, stash: Map<string, string | null>): void {
  for (const name of LABELS) {
    const value = element.getAttribute(name);
    if (value === null) {
      if (!stash.has(name)) stash.set(name, null);
      continue;
    }
    stash.set(name, value);
    element.removeAttribute(name);
  }
}

function restoreLabels(element: Element, stash: Map<string, string | null>): void {
  for (const [name, value] of stash) {
    if (value === null) continue;
    if (element.getAttribute(name) === null) element.setAttribute(name, value);
  }
}

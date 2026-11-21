// `scrollIntoViewWithin` moves only the boxes the learner can scroll, by the
// amount the asked alignment needs, and never a hidden box or the page.
// jsdom lays nothing out: each box's place is given here by hand.
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { scrollIntoViewWithin } from "./scrollWithin";

type Box = { top: number; height: number; clientHeight?: number; scrollHeight?: number };
const boxes = new Map<Element, Box>();
const scrolled: { box: Element; top: number; behavior?: ScrollBehavior }[] = [];

function place(element: HTMLElement, box: Box) {
  boxes.set(element, box);
  Object.defineProperty(element, "clientHeight", { configurable: true, value: box.clientHeight ?? box.height });
  Object.defineProperty(element, "scrollHeight", { configurable: true, value: box.scrollHeight ?? box.height });
  let scrollTop = 0;
  Object.defineProperty(element, "scrollTop", { configurable: true, get: () => scrollTop, set: (value: number) => { scrollTop = value; } });
  return element;
}

beforeEach(() => {
  boxes.clear();
  scrolled.length = 0;
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const box = boxes.get(this) ?? { top: 0, height: 0 };
    return { top: box.top, bottom: box.top + box.height, height: box.height, width: 100, left: 0, right: 100, x: 0, y: box.top, toJSON: () => ({}) } as DOMRect;
  });
  HTMLElement.prototype.scrollTo = function (this: HTMLElement, options?: ScrollToOptions | number) {
    const top = typeof options === "object" ? options.top ?? 0 : 0;
    scrolled.push({ box: this, top, behavior: typeof options === "object" ? options.behavior : undefined });
    this.scrollTop = top;
  } as typeof HTMLElement.prototype.scrollTo;
});
afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

// The shell (hidden overflow, the whole window) > the rail (scrolls) > a card.
function shellRailCard(cardTop: number) {
  const shell = place(document.createElement("div"), { top: 0, height: 800, scrollHeight: 1200 });
  shell.style.overflow = "hidden";
  const rail = place(document.createElement("div"), { top: 100, height: 400, scrollHeight: 2000 });
  rail.style.overflowY = "auto";
  const card = place(document.createElement("div"), { top: cardTop, height: 50 });
  rail.append(card);
  shell.append(rail);
  document.body.append(shell);
  return { shell, rail, card };
}

it("start, center and end put the element where asked inside its own scroller", () => {
  const { rail, card } = shellRailCard(700);
  scrollIntoViewWithin(card, { block: "start" });
  expect(scrolled).toEqual([{ box: rail, top: 600, behavior: "auto" }]);

  rail.scrollTop = 0;
  scrolled.length = 0;
  scrollIntoViewWithin(card, { block: "center", behavior: "smooth" });
  expect(scrolled).toEqual([{ box: rail, top: 600 + 25 - 200, behavior: "smooth" }]);

  rail.scrollTop = 0;
  scrolled.length = 0;
  scrollIntoViewWithin(card, { block: "end" });
  expect(scrolled).toEqual([{ box: rail, top: 600 + 50 - 400 }].map((entry) => ({ ...entry, behavior: "auto" })));
});

it("nearest moves only when the element is out of view, by the least amount", () => {
  const { rail, card } = shellRailCard(200);
  scrollIntoViewWithin(card, { block: "nearest" });
  expect(scrolled).toEqual([]);

  boxes.set(card, { top: 700, height: 50 });
  scrollIntoViewWithin(card, { block: "nearest" });
  expect(scrolled).toEqual([{ box: rail, top: 600 + 50 - 400, behavior: "auto" }]);
});

it("a hidden box, body and the document are never scrolled, even when the element is outside them", () => {
  const { shell, card } = shellRailCard(1500);
  const set = vi.fn();
  Object.defineProperty(document.documentElement, "scrollTop", { configurable: true, get: () => 0, set });
  Object.defineProperty(document.body, "scrollTop", { configurable: true, get: () => 0, set });
  scrollIntoViewWithin(card, { block: "start" });
  expect(scrolled.map(({ box }) => box)).not.toContain(shell);
  expect(scrolled.map(({ box }) => box)).not.toContain(document.body);
  expect(scrolled.map(({ box }) => box)).not.toContain(document.documentElement);
  expect(shell.scrollTop).toBe(0);
  expect(set).not.toHaveBeenCalled();
});

it("an element with no scroller around it moves nothing", () => {
  const shell = place(document.createElement("div"), { top: 0, height: 800, scrollHeight: 1200 });
  shell.style.overflow = "hidden";
  const card = place(document.createElement("div"), { top: 1100, height: 50 });
  shell.append(card);
  document.body.append(shell);
  scrollIntoViewWithin(card, { block: "center" });
  scrollIntoViewWithin(null);
  expect(scrolled).toEqual([]);
  expect(shell.scrollTop).toBe(0);
});

it("a scroller inside a scroller: the outer one is moved for where the inner move leaves the element", () => {
  const outer = place(document.createElement("div"), { top: 0, height: 500, scrollHeight: 3000 });
  outer.style.overflowY = "auto";
  const inner = place(document.createElement("div"), { top: 1000, height: 300, scrollHeight: 1000 });
  inner.style.overflowY = "scroll";
  const card = place(document.createElement("div"), { top: 1500, height: 20 });
  inner.append(card);
  outer.append(inner);
  document.body.append(outer);
  scrollIntoViewWithin(card, { block: "start" });
  // The inner box puts the card at its top (500 down); the card then sits at
  // 1000 in the window, which the outer box brings to its own top.
  expect(scrolled).toEqual([
    { box: inner, top: 500, behavior: "auto" },
    { box: outer, top: 1000, behavior: "auto" },
  ]);
});

it("a scroll margin on the element is kept above it at start, as the PDF pane's passages ask", () => {
  const { rail, card } = shellRailCard(700);
  card.style.scrollMarginTop = "56px";
  scrollIntoViewWithin(card, { block: "start" });
  expect(scrolled).toEqual([{ box: rail, top: 600 - 56, behavior: "auto" }]);
});

it("a move is clamped to what the scroller can scroll", () => {
  const { rail, card } = shellRailCard(2400);
  scrollIntoViewWithin(card, { block: "start" });
  expect(scrolled).toEqual([{ box: rail, top: 2000 - 400, behavior: "auto" }]);
});

// The Reader's rail: a sticky tab bar at its top (the rail's padding 18 px, the
// bar `top: -18px`, 52 px tall), stuck over the rail's first 52 px. A target
// placed at the rail's top edge sat under it, and the first click on it landed
// on the bar (student-3 #73, expert-2 #34).
function railWithStickyBar(cardTop: number, cardHeight = 50) {
  const { shell, rail, card } = shellRailCard(cardTop);
  boxes.set(card, { top: cardTop, height: cardHeight });
  rail.style.paddingTop = "18px";
  const bar = place(document.createElement("div"), { top: 100, height: 52 });
  bar.style.position = "sticky";
  bar.style.top = "-18px";
  rail.prepend(bar);
  return { shell, rail, card, bar };
}
/** Where the card's top lands in the window once the rail has moved from `from`. */
const landedTop = (rail: HTMLElement, cardTop: number, from = 0) => cardTop - (rail.scrollTop - from);
const BAR_BOTTOM = 100 + 18 - 18 + 52;

it("start and nearest put a target clear of a sticky bar at the scroller's top, never under it", () => {
  const { rail } = railWithStickyBar(700);
  scrollIntoViewWithin(rail.lastElementChild, { block: "start" });
  expect(scrolled).toEqual([{ box: rail, top: 600 - 52, behavior: "auto" }]);
  expect(landedTop(rail, 700)).toBe(BAR_BOTTOM);

  // Above the view (the follow-up box over the thread the learner was reading).
  rail.scrollTop = 900;
  boxes.set(rail.lastElementChild!, { top: 40, height: 50 });
  scrolled.length = 0;
  scrollIntoViewWithin(rail.lastElementChild, { block: "nearest" });
  expect(scrolled).toHaveLength(1);
  expect(landedTop(rail, 40, 900)).toBe(BAR_BOTTOM);
});

it("nearest moves a target that is in the scroller's view but under its sticky bar", () => {
  // The rail scrolled down; the card's top is 10 px below the rail's top: inside the rail, under the bar.
  const { rail } = railWithStickyBar(110, 30);
  rail.scrollTop = 500;
  scrollIntoViewWithin(rail.lastElementChild, { block: "nearest" });
  expect(scrolled).toHaveLength(1);
  expect(landedTop(rail, 110, 500)).toBe(BAR_BOTTOM);
});

it("center centres the target in the part of the scroller the bar leaves clear", () => {
  const { rail } = railWithStickyBar(700);
  scrollIntoViewWithin(rail.lastElementChild, { block: "center" });
  const clear = 400 - 52;
  expect(scrolled).toEqual([{ box: rail, top: 600 + 25 - 52 - clear / 2, behavior: "auto" }]);
});

it("end and nearest keep a target above a sticky bar at the scroller's bottom", () => {
  const { rail, card } = shellRailCard(700);
  const footer = place(document.createElement("div"), { top: 460, height: 40 });
  footer.style.position = "sticky";
  footer.style.bottom = "0px";
  rail.append(footer);
  scrollIntoViewWithin(card, { block: "end" });
  expect(scrolled).toEqual([{ box: rail, top: 600 + 50 - 400 + 40, behavior: "auto" }]);
  expect(landedTop(rail, 700) + 50).toBeLessThanOrEqual(100 + 400 - 40);
});

it("a target inside the sticky bar itself is not pushed below it", () => {
  const { rail, bar } = railWithStickyBar(700);
  const tab = place(document.createElement("button"), { top: 700, height: 20 });
  bar.append(tab);
  scrollIntoViewWithin(tab, { block: "start" });
  expect(scrolled).toEqual([{ box: rail, top: 600, behavior: "auto" }]);
});

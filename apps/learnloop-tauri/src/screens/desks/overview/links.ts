// Relations between cards and the curved links that show them (spec §6.5), and the gather order they
// give (§6.6). Pure.
//
// Weights: 3, an explicit link (the window was opened beside this one; a panel bound to this book);
// 2, the same source on another desk ("same book"); 1, a shared learning object (needs the coverage the
// union read carries, which the desks do not read yet: no weight-1 link is drawn in this stage).
import type { ContentRefDto } from "../../../api/dto";
import type { Rect } from "../geometry";
import type { Workspace } from "../model/workspace";

export interface Relation {
  windowId: string;
  weight: 1 | 2 | 3;
  label: string;
}

/** At most this many relations are drawn, an attention limit (labelled where it applies). */
export const DRAWN_RELATIONS = 4;

function sourceOf(content: ContentRefDto | null): string | null {
  if (!content) return null;
  if (content.kind === "source" || content.kind === "video") return content.sourceId;
  return null;
}

function extractionOf(content: ContentRefDto | null): string | null {
  if (!content) return null;
  if (content.kind === "source" || content.kind === "video") return content.extractionId;
  if (content.kind === "panel") return content.extractionId ?? null;
  return null;
}

/** The window a window was opened beside, kept in its view (`openedBeside`). */
export function openedBeside(view: Record<string, unknown> | undefined): string | null {
  const value = view?.openedBeside;
  return typeof value === "string" ? value : null;
}

/** Every relation of one window, strongest first (ties by window id). */
export function relationsOf(ws: Workspace, windowId: string): Relation[] {
  const self = ws.windows[windowId];
  if (!self) return [];
  const out = new Map<string, Relation>();
  const add = (id: string, weight: Relation["weight"], label: string) => {
    if (id === windowId || !ws.windows[id]) return;
    const known = out.get(id);
    if (!known || known.weight < weight) out.set(id, { windowId: id, weight, label });
  };
  const mySource = sourceOf(self.content);
  const myExtraction = extractionOf(self.content);
  const beside = openedBeside(self.view);
  if (beside) add(beside, 3, "opened beside");
  for (const other of Object.values(ws.windows)) {
    if (other.windowId === windowId) continue;
    if (openedBeside(other.view) === windowId) add(other.windowId, 3, "opened beside");
    const theirExtraction = extractionOf(other.content);
    const panelPair = (self.content?.kind === "panel") !== (other.content?.kind === "panel");
    if (panelPair && myExtraction && theirExtraction === myExtraction && other.deskId === self.deskId) {
      add(other.windowId, 3, self.content?.kind === "panel" ? "its book" : "its panel");
    }
    if (mySource && sourceOf(other.content) === mySource && other.deskId !== self.deskId) add(other.windowId, 2, "same book");
  }
  return [...out.values()].sort((a, b) => b.weight - a.weight || (a.windowId < b.windowId ? -1 : 1));
}

export interface CurvedLink {
  to: string;
  weight: number;
  label: string;
  /** The SVG path, in world coordinates. */
  d: string;
  /** Where the label sits (u = .82 along the curve). */
  labelAt: { x: number; y: number };
}

/** Each link offset this far from its neighbours (world px). */
const LINK_SPREAD = 26;

function cubicAt(p0: number, p1: number, p2: number, p3: number, u: number): number {
  const v = 1 - u;
  return v * v * v * p0 + 3 * v * v * u * p1 + 3 * v * u * u * p2 + u * u * u * p3;
}

/** Cubic Béziers from the focused card's bottom centre to each target's bottom centre: on the same row
 * a dip below the cards; to another row a vertical S. */
export function curvedLinks(from: Rect, targets: Array<{ rect: Rect; relation: Relation }>): CurvedLink[] {
  return targets.map(({ rect, relation }, index) => {
    const offset = (index - (targets.length - 1) / 2) * LINK_SPREAD;
    const x0 = from.x + from.w / 2 + offset;
    const y0 = from.y + from.h;
    const x3 = rect.x + rect.w / 2 + offset;
    const y3 = rect.y + rect.h;
    let c1: [number, number];
    let c2: [number, number];
    if (Math.abs(y3 - y0) < 1) {
      const dip = 120 + Math.abs(x3 - x0) * 0.12 + Math.abs(offset);
      c1 = [x0, y0 + dip];
      c2 = [x3, y3 + dip];
    } else {
      const mid = (y0 + y3) / 2;
      c1 = [x0, mid];
      c2 = [x3, mid];
    }
    const u = 0.82;
    return {
      to: relation.windowId,
      weight: relation.weight,
      label: relation.label,
      d: `M ${x0} ${y0} C ${c1[0]} ${c1[1]}, ${c2[0]} ${c2[1]}, ${x3} ${y3}`,
      labelAt: { x: cubicAt(x0, c1[0], c2[0], x3, u), y: cubicAt(y0, c1[1], c2[1], y3, u) },
    };
  });
}

/** Gather around the focus (spec §6.6): the windows before it that are not linked, the focus, the linked
 * windows by weight (at most `limit`, an attention limit), then the rest. Returns the new order of slots
 * (by their first window) and how many linked windows stayed behind. */
export function gatherOrder(slots: string[][], focusId: string, related: Relation[], limit = DRAWN_RELATIONS): { order: string[][]; stayed: number } {
  const focusIndex = slots.findIndex((slot) => slot.includes(focusId));
  if (focusIndex < 0) return { order: slots, stayed: 0 };
  const slotOf = (id: string) => slots.findIndex((slot) => slot.includes(id));
  const linkedSlots: number[] = [];
  for (const relation of related) {
    const index = slotOf(relation.windowId);
    if (index >= 0 && index !== focusIndex && !linkedSlots.includes(index)) linkedSlots.push(index);
  }
  const moving = linkedSlots.slice(0, limit);
  const before = slots.map((_, index) => index).filter((index) => index < focusIndex && !moving.includes(index));
  const rest = slots.map((_, index) => index).filter((index) => index > focusIndex && !moving.includes(index));
  const order = [...before, focusIndex, ...moving, ...rest].map((index) => slots[index]);
  return { order, stayed: Math.max(0, linkedSlots.length - moving.length) };
}

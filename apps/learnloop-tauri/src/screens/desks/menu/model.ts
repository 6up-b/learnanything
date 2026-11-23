// The context-aware right-click, the pure half (spec §0 item 7, §9.1, §9.2): what was right-clicked (a passage, a
// transcript cue, a highlight, a margin note, a window header, a pad line), the header line, the fixed verbs for that
// object kind in their fixed positions (only the verbs that apply: none is shown disabled but marimo's), the
// promoted rows as they arrive (the cheap ones at once, the judged ones from the job), and where the menu goes.
import type { MenuObjectInput, PromotedRowDto } from "../../../api/dto";
import { WINDOW_ATTRIBUTE } from "../keys/listeners";

export type MenuObjectKind = MenuObjectInput["objectKind"];

/** What the menu is about. */
export interface MenuObject {
  kind: MenuObjectKind;
  windowId: string | null;
  /** The words it shows (a passage's or cue's text, the selection over it, a note's words, a window's title). */
  text: string;
  extractionId?: string;
  spanId?: string;
  /** The passages a selection over the object touches (a passage's own when nothing is selected). */
  spanIds?: string[];
  /** The selection's words, when there is one (Ask and Append take them). */
  selection?: string;
  /** The selection cut at each passage it touches: each passage's own words of it (a capture's node quotes). */
  slices?: Array<{ spanId: string; quote: string }>;
  t?: number;
  annotationId?: string;
  padId?: string;
  blockId?: string | null;
  /** The source of the window it sits in (Append, Note, Open beside need it). */
  sourceId?: string;
  /** Where it was opened: the pointer, or the object's own box for a key. */
  at: { x: number; y: number };
}

/** A capture's nodes for the object: each passage with its own words of the selection (none: the whole passage). */
export function captureNodes(object: MenuObject): Array<{ spanId: string; quote?: string }> {
  if (object.slices?.length) return object.slices.map((slice) => ({ spanId: slice.spanId, quote: slice.quote }));
  const ids = object.spanIds?.length ? object.spanIds : object.spanId ? [object.spanId] : [];
  return ids.map((spanId) => ({ spanId }));
}

/** The server's view of the object (passage.promoted, passage.knows). */
export function objectInput(object: MenuObject, deskId: string | null): MenuObjectInput {
  return {
    objectKind: object.kind,
    ...(object.extractionId ? { extractionId: object.extractionId } : {}),
    ...(object.spanId ? { spanId: object.spanId } : {}),
    ...(object.t !== undefined ? { t: object.t } : {}),
    ...(object.annotationId ? { annotationId: object.annotationId } : {}),
    ...(object.blockId ? { blockId: object.blockId } : {}),
    ...(object.windowId ? { windowId: object.windowId } : {}),
    ...(deskId ? { deskId } : {}),
  };
}

const KIND_LABEL: Record<MenuObjectKind, string> = {
  passage: "a passage",
  cue: "a transcript cue",
  highlight: "your highlight",
  note: "your margin note",
  window: "a window",
  pad_line: "your pad",
};

/** "<a passage | a transcript cue | your margin note | a window> · “<first 46 chars>”" (§9.1, §9.2). */
export function headerLine(object: MenuObject): string {
  const words = (object.selection || object.text).replace(/\s+/g, " ").trim();
  const clipped = words.length > 46 ? `${words.slice(0, 46)}…` : words;
  return `${KIND_LABEL[object.kind]} · “${clipped || "…"}”`;
}

/** The verbs, in their fixed positions (experts rely on them), with the object kinds each applies to (§9.1's table;
 * a verb that does not apply to a kind is left out, never shown disabled). */
export type VerbId =
  | "ask" | "note" | "append" | "carry" | "open_beside" | "find" | "compare" | "show_me" | "make_practice" | "teach_me"
  | "submit" | "new_desk" | "gather" | "share_slot" | "own_slot" | "knows";

export interface VerbSpec {
  id: VerbId;
  glyph: string;
  label: string;
  key: string;
  kinds: MenuObjectKind[];
}

export const VERBS: VerbSpec[] = [
  { id: "ask", glyph: "?", label: "Ask", key: "a", kinds: ["passage", "cue", "highlight", "note", "pad_line"] },
  { id: "note", glyph: "›", label: "Note in margin", key: "n", kinds: ["passage", "cue", "pad_line"] },
  { id: "append", glyph: "⤓", label: "Append to", key: "w", kinds: ["passage", "cue", "highlight"] },
  { id: "carry", glyph: "◌", label: "Carry", key: "c", kinds: ["passage", "cue", "highlight", "note", "pad_line"] },
  { id: "open_beside", glyph: "▸", label: "Open beside", key: "b", kinds: ["passage", "cue", "highlight"] },
  { id: "find", glyph: "⌕", label: "Find in my sources", key: "/", kinds: ["passage", "cue", "highlight", "note", "pad_line"] },
  { id: "compare", glyph: "⇄", label: "Compare", key: "=", kinds: ["passage", "cue", "highlight"] },
  { id: "show_me", glyph: "◇", label: "Show me", key: "v", kinds: ["passage", "cue", "highlight", "pad_line"] },
  { id: "make_practice", glyph: "✎", label: "Make it practice", key: "p", kinds: ["passage", "cue", "pad_line"] },
  { id: "teach_me", glyph: "◎", label: "Teach me this", key: "t", kinds: ["passage", "cue", "highlight", "pad_line"] },
  { id: "submit", glyph: "✓", label: "Submit this block as…", key: "s", kinds: ["pad_line"] },
  { id: "new_desk", glyph: "⊞", label: "New desk from these", key: "d", kinds: ["window"] },
  { id: "gather", glyph: "⇇", label: "Gather linked sources", key: "g", kinds: ["window"] },
  { id: "share_slot", glyph: "⤒", label: "Share a slot with the next", key: ",", kinds: ["window"] },
  { id: "own_slot", glyph: "⤓", label: "Own slot", key: ".", kinds: ["window"] },
  { id: "knows", glyph: "i", label: "What this knows", key: "i", kinds: ["passage", "cue", "highlight", "note", "window", "pad_line"] },
];

/** The verbs for an object kind, in their fixed order. */
export function verbsFor(kind: MenuObjectKind): VerbSpec[] {
  return VERBS.filter((verb) => verb.kinds.includes(kind));
}

/** One row of the menu as it shows. */
export interface MenuRow {
  id: string;
  glyph: string;
  label: string;
  /** Small text under the label (a promoted row's reason, an insert's note). */
  note?: string;
  /** The key that runs it (shown at the right); none for a row reached with ↑↓ ↵ only. */
  key?: string;
  disabled?: boolean;
  /** "promoted" rows sit in their own block above the verbs; "insert" rows under a small heading. */
  section: "promoted" | "verb" | "insert" | "tail";
  /** What this knows is a design aid in the mockup's colour. */
  aid?: boolean;
  /** The Append row opens its submenu on hover. */
  submenu?: boolean;
  run?: () => void;
  /** A promoted row's server row (its labels). */
  promoted?: PromotedRowDto;
}

/** The promoted rows to show: the server's ranking kept (it already put the learner's own acts first and left out
 * what was dismissed), rows dismissed here since the menu opened left out, at most the cap (an attention limit). */
export function shownPromoted(rows: PromotedRowDto[], dismissed: ReadonlySet<string>, cap = 4): PromotedRowDto[] {
  return rows.filter((row) => !dismissed.has(row.rowId)).slice(0, cap);
}

/** A promoted row's reason as the learner reads it: a judge's unchecked finding says so. */
export function promotedReason(row: PromotedRowDto): string {
  if (row.checked === false && !/not checked/.test(row.reason)) return `${row.reason} · found by search, not checked`;
  return row.reason;
}

/** The menu's design sizes (spec §4.3; measured from the mockup): 360 wide, kept 10 px inside the right and bottom
 * edges and below the 44 px of the top bar. */
export const MENU_SIZES = { width: 360, submenuWidth: 260, edge: 10, top: 44 } as const;

/** Where the menu goes: at the pointer (2 px down and right of it), moved in to fit the viewport. */
export function placeMenu(at: { x: number; y: number }, size: { w: number; h: number }, viewport: { w: number; h: number }): { left: number; top: number } {
  const left = Math.max(MENU_SIZES.edge, Math.min(at.x + 2, viewport.w - size.w - MENU_SIZES.edge));
  const top = Math.max(MENU_SIZES.top, Math.min(at.y + 2, viewport.h - size.h - MENU_SIZES.edge));
  return { left, top };
}

/** Where the Append submenu goes: right of its row, 4 px off, 6 px above, kept inside the viewport. */
export function placeSubmenu(row: { right: number; top: number }, width: number, viewport: { w: number }): { left: number; top: number } {
  return { left: Math.min(row.right + 4, viewport.w - width - 8), top: row.top - 6 };
}

// -- what was right-clicked (one listener reads it from the DOM) --------------------------------------

/** The object under a right-click, or null when the click is on nothing the menu knows (the browser's own menu
 * then stays away too, but nothing opens). `kindOf` names a window's content kind. */
export function objectAt(target: Element, kindOf: (windowId: string) => string | null, sourceOf: (windowId: string) => { sourceId: string; extractionId: string } | null, at: { x: number; y: number }, doc: Document = document): MenuObject | null {
  const host = target.closest(`[${WINDOW_ATTRIBUTE}]`);
  const windowId = host?.getAttribute(WINDOW_ATTRIBUTE) ?? null;
  const selection = selectionWithin(host, doc);
  // A window header: the window itself.
  const head = target.closest(".desk-pane-head");
  if (head && windowId) {
    return { kind: "window", windowId, text: head.textContent?.replace(/\s+/g, " ").trim() ?? "", at, ...(sourceOf(windowId) ?? {}) };
  }
  // A pad line (or the pad's body, for its inserts at the end).
  const pad = target.closest("[data-pad]");
  if (pad && windowId) {
    const line = target.closest("[data-block]");
    return {
      kind: "pad_line", windowId, padId: pad.getAttribute("data-pad") ?? undefined, blockId: line?.getAttribute("data-block") ?? null,
      text: (selection?.text || line?.textContent || "").replace(/\s+/g, " ").trim(), ...(selection ? { selection: selection.text } : {}), at,
    };
  }
  if (!windowId) return null;
  const source = sourceOf(windowId);
  // A highlight or a margin note (an annotation on the passage).
  const annotation = target.closest("[data-annotation-id]");
  const passage = target.closest("[data-span-id], [data-transcript-span]");
  // On the passage it marks, or on its card in the margin (which names its passage).
  const annotationSpan = annotation ? (passage ? spanOf(passage) : annotation.getAttribute("data-annotation-span") || undefined) : undefined;
  if (annotation && annotationSpan) {
    const isNote = annotation.getAttribute("data-annotation-kind") === "note";
    return {
      kind: isNote ? "note" : "highlight", windowId, annotationId: annotation.getAttribute("data-annotation-id") ?? undefined,
      spanId: annotationSpan, extractionId: source?.extractionId, sourceId: source?.sourceId,
      text: (annotation.textContent || passage?.textContent || "").replace(/\s+/g, " ").trim(), at,
      // A selection inside the marked passage stays the words the verbs act on.
      ...(selection ? { selection: selection.text, slices: selection.slices } : {}),
      spanIds: selection?.spanIds.length ? selection.spanIds : [annotationSpan],
    };
  }
  if (!passage) return null;
  const spanId = spanOf(passage);
  const cue = passage.hasAttribute("data-transcript-span") || kindOf(windowId) === "video";
  const tAttr = passage.getAttribute("data-t") ?? passage.closest("[data-t]")?.getAttribute("data-t");
  return {
    kind: cue ? "cue" : "passage", windowId, spanId, extractionId: source?.extractionId, sourceId: source?.sourceId,
    spanIds: selection?.spanIds.length ? selection.spanIds : spanId ? [spanId] : [],
    text: (passage.textContent ?? "").replace(/\s+/g, " ").trim(),
    ...(selection ? { selection: selection.text, slices: selection.slices } : {}),
    ...(tAttr && Number.isFinite(Number(tAttr)) ? { t: Number(tAttr) } : {}),
    at,
  };
}

function spanOf(element: Element): string | undefined {
  return element.getAttribute("data-span-id") ?? element.getAttribute("data-transcript-span") ?? undefined;
}

function selectionWithin(host: Element | null, doc: Document): { text: string; spanIds: string[]; slices: Array<{ spanId: string; quote: string }> } | null {
  const selection = doc.getSelection?.();
  if (!host || !selection || selection.isCollapsed || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!host.contains(range.commonAncestorContainer)) return null;
  const text = selection.toString().replace(/\s+/g, " ").trim();
  if (!text) return null;
  const spanIds: string[] = [];
  const slices: Array<{ spanId: string; quote: string }> = [];
  for (const element of host.querySelectorAll("[data-span-id], [data-transcript-span]")) {
    const id = spanOf(element);
    if (!id || spanIds.includes(id) || !range.intersectsNode(element)) continue;
    // The part of the selection inside this passage: a passage's capture quotes its own words, never the whole run.
    const part = doc.createRange();
    part.selectNodeContents(element);
    if (range.compareBoundaryPoints(Range.START_TO_START, part) > 0) part.setStart(range.startContainer, range.startOffset);
    if (range.compareBoundaryPoints(Range.END_TO_END, part) < 0) part.setEnd(range.endContainer, range.endOffset);
    const quote = part.toString().replace(/\s+/g, " ").trim();
    if (!quote) continue;
    spanIds.push(id);
    slices.push({ spanId: id, quote });
  }
  return { text, spanIds, slices };
}

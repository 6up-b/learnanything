// The client's model of the desks (spec §3.1, §5.1, §5.2): desks, windows, slots and pairs. Pure.
//
// `applyDeskOp` mirrors the server's `desk.apply` (src/learnloop/desks/workspace.py) op for op, so an
// op applied here optimistically leaves the same layout the server will store. Every applied op adds
// one to its desk's version, as the server does; a batch's later ops therefore expect the version the
// earlier ones leave. The intents below (`openBeside`, `closeWindow`, `pairFocused`, …) return the next
// workspace together with the ops to send, so what the learner sees and what is persisted never part.
import type {
  ContentRefDto,
  DeskDto,
  DeskOpDto,
  DeskStateDto,
  DeskWindowKind,
  PadStackEntryDto,
} from "../../../api/dto";

/** A slot holds at most two windows (spec §5.2; the server's PAIR_SIZE). */
export const PAIR_SIZE = 2;

export interface DeskWindow {
  windowId: string;
  deskId: string;
  kind: DeskWindowKind;
  content: ContentRefDto | null;
  stack: PadStackEntryDto[] | null;
  /** The pair's active pane; always true for a window alone in its slot. */
  active: boolean;
  view: Record<string, unknown>;
}

export interface Desk {
  deskId: string;
  title: string;
  position: string;
  focusWindowId: string | null;
  goalId: string | null;
  companion: { dock: DeskDto["companion"]["dock"]; shown: boolean };
  version: number;
  /** Window ids by slot; a pair is a slot of two (panes 0 and 1). */
  slots: string[][];
}

export interface ClosedWindow {
  window: DeskWindow;
  slot: number;
}

export interface Workspace {
  /** Open desks, in their stacking order (position, then id). */
  desks: Desk[];
  windows: Record<string, DeskWindow>;
  /** Windows closed on each desk, newest last: what "undo close" reopens. */
  closed: Record<string, ClosedWindow[]>;
  /** The running pads the server knows (a desk's running pad is the one of these its stacks hold). */
  runningPadIds?: string[];
}

export const EMPTY_WORKSPACE: Workspace = { desks: [], windows: {}, closed: {} };

function orderDesks(desks: Desk[]): Desk[] {
  return [...desks].sort((a, b) => (a.position < b.position ? -1 : a.position > b.position ? 1 : a.deskId < b.deskId ? -1 : a.deskId > b.deskId ? 1 : 0));
}

export function fromDeskState(state: DeskStateDto): Workspace {
  const windows: Record<string, DeskWindow> = {};
  const desks: Desk[] = state.desks.map((desk) => {
    const slots = [...desk.slots].sort((a, b) => a.slot - b.slot).map((slot) =>
      [...slot.windows].sort((a, b) => a.pane - b.pane).map((window) => {
        windows[window.windowId] = {
          windowId: window.windowId,
          deskId: desk.deskId,
          kind: window.kind,
          content: window.content ?? null,
          stack: window.stack ?? null,
          active: window.active,
          view: window.view ?? {},
        };
        return window.windowId;
      }),
    );
    return {
      deskId: desk.deskId,
      title: desk.title,
      position: desk.position,
      focusWindowId: desk.focusWindowId,
      goalId: desk.goalId,
      companion: { ...desk.companion },
      version: desk.version,
      slots,
    };
  });
  return { desks: orderDesks(desks), windows, closed: {}, runningPadIds: [...(state.runningPadIds ?? [])] };
}

// -- reads ------------------------------------------------------------------------------------------

export function deskById(ws: Workspace, deskId: string | null | undefined): Desk | null {
  return ws.desks.find((desk) => desk.deskId === deskId) ?? null;
}

export function slotIndexOf(desk: Desk, windowId: string | null | undefined): number {
  if (!windowId) return -1;
  return desk.slots.findIndex((slot) => slot.includes(windowId));
}

/** The window that has the focus: the desk's focus, else the active pane of its first slot. */
export function focusedWindowId(ws: Workspace, desk: Desk | null): string | null {
  if (!desk) return null;
  if (desk.focusWindowId && slotIndexOf(desk, desk.focusWindowId) >= 0) return desk.focusWindowId;
  const first = desk.slots[0];
  if (!first) return null;
  return first.find((id) => ws.windows[id]?.active) ?? first[0] ?? null;
}

export function focusedSlot(ws: Workspace, desk: Desk | null): number {
  if (!desk) return -1;
  return slotIndexOf(desk, focusedWindowId(ws, desk));
}

/** What makes two content references "the same thing" for the no-duplicate rule (spec §5.2). */
export function contentKey(content: ContentRefDto | null, stack?: PadStackEntryDto[] | null): string {
  if (!content) return stack ? `stack:${stack.map((entry) => contentKey(entry)).join("|")}` : "none";
  switch (content.kind) {
    case "source":
    case "video":
      // The same source in its text, PDF or web view is the same source.
      return `${content.kind === "video" ? "video" : "source"}:${content.sourceId}`;
    case "pad":
      return `pad:${content.padId}`;
    case "lesson":
      return `lesson:${content.lessonId}`;
    case "thread":
      return `thread:${content.rootExchangeId}`;
    case "compare":
      return `compare:${content.comparisonId ?? ""}:${content.query ?? ""}`;
    case "panel":
      return `panel:${content.panel}:${content.extractionId ?? ""}`;
    case "figure_notebook":
      return `figure:${content.figureId}`;
  }
}

/** Whether a source window's range covers a passage. `order` gives a passage's index in the reading;
 * without it, only a window with no range (the whole reading) or a range ending on the passage covers it. */
export function rangeCovers(
  content: ContentRefDto | null,
  spanId: string | null | undefined,
  order?: (spanId: string) => number,
): boolean {
  if (!content || content.kind !== "source" || !content.range || !spanId) return true;
  const { fromSpanId, toSpanId } = content.range;
  if (spanId === fromSpanId || spanId === toSpanId) return true;
  if (!order) return false;
  const at = order(spanId);
  const from = order(fromSpanId);
  const to = order(toSpanId);
  return at >= 0 && from >= 0 && to >= 0 && at >= from && at <= to;
}

/** The open window on this desk already showing `content` (and covering `spanId`), if any. */
export function findDuplicate(
  ws: Workspace,
  desk: Desk,
  content: ContentRefDto,
  spanId?: string | null,
  order?: (spanId: string) => number,
): string | null {
  const key = contentKey(content);
  for (const slot of desk.slots) {
    for (const id of slot) {
      const window = ws.windows[id];
      if (window && contentKey(window.content, window.stack) === key && rangeCovers(window.content, spanId, order)) return id;
    }
  }
  return null;
}

// -- applying one op (the server's semantics) -------------------------------------------------------

export class OpRefusal extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
  }
}

function replaceDesk(ws: Workspace, next: Desk): Workspace {
  return { ...ws, desks: orderDesks(ws.desks.map((desk) => (desk.deskId === next.deskId ? next : desk))) };
}

/** Recompute the active flags the way the server's layout write does: a lone window is active; a pair
 * with no active pane makes its first pane active. */
function normalizeActive(ws: Workspace, desk: Desk, activeIds: Set<string>): Record<string, DeskWindow> {
  const windows = { ...ws.windows };
  for (const slot of desk.slots) {
    if (slot.length === 1) activeIds.add(slot[0]);
    else if (!slot.some((id) => activeIds.has(id))) activeIds.add(slot[0]);
    for (const id of slot) {
      const window = windows[id];
      if (window) windows[id] = { ...window, deskId: desk.deskId, active: activeIds.has(id) };
    }
  }
  return windows;
}

function activeSet(ws: Workspace, desk: Desk): Set<string> {
  return new Set(desk.slots.flat().filter((id) => ws.windows[id]?.active));
}

function requireDesk(ws: Workspace, deskId: string): Desk {
  const desk = deskById(ws, deskId);
  if (!desk) throw new OpRefusal("desk_not_found", `No desk ${deskId}.`);
  return desk;
}

function requireOpen(desk: Desk, windowId: string): number {
  const index = slotIndexOf(desk, windowId);
  if (index < 0) throw new OpRefusal("window_not_open", "That window is not open on this desk.");
  return index;
}

function sameEntry(a: PadStackEntryDto, b: PadStackEntryDto): boolean {
  return a.kind === b.kind && (a.kind === "pad" ? a.padId === (b as { padId?: string }).padId : (a as { lessonId?: string }).lessonId === (b as { lessonId?: string }).lessonId);
}

function bump(desk: Desk, fields: Partial<Desk> = {}): Desk {
  return { ...desk, ...fields, version: desk.version + 1 };
}

/** Apply one op as the server would (versions unchecked: the server checks them). Throws OpRefusal
 * where the server refuses. */
export function applyDeskOp(ws: Workspace, op: DeskOpDto): Workspace {
  switch (op.op) {
    case "create_desk": {
      if (deskById(ws, op.deskId)) throw new OpRefusal("desk_exists", "That desk exists.");
      const desk: Desk = {
        deskId: op.deskId,
        title: op.title,
        position: op.position,
        focusWindowId: null,
        goalId: op.goalId ?? null,
        companion: { dock: op.companionDock ?? "br", shown: false },
        version: 1,
        slots: [],
      };
      return { ...ws, desks: orderDesks([...ws.desks, desk]) };
    }
    case "rename_desk":
      return replaceDesk(ws, bump(requireDesk(ws, op.deskId), { title: op.title }));
    case "archive_desk": {
      requireDesk(ws, op.deskId);
      return { ...ws, desks: ws.desks.filter((desk) => desk.deskId !== op.deskId) };
    }
    case "move_desk":
      return replaceDesk(ws, bump(requireDesk(ws, op.deskId), { position: op.position }));
    case "set_dock": {
      const desk = requireDesk(ws, op.deskId);
      return replaceDesk(ws, bump(desk, { companion: { ...desk.companion, dock: op.dock } }));
    }
    case "set_companion_shown": {
      const desk = requireDesk(ws, op.deskId);
      return replaceDesk(ws, bump(desk, { companion: { ...desk.companion, shown: op.shown } }));
    }
    case "set_goal":
      return replaceDesk(ws, bump(requireDesk(ws, op.deskId), { goalId: op.goalId }));
    case "set_focus": {
      const desk = requireDesk(ws, op.deskId);
      if (op.windowId !== null) requireOpen(desk, op.windowId);
      return replaceDesk(ws, bump(desk, { focusWindowId: op.windowId }));
    }
    case "open_window": {
      const desk = requireDesk(ws, op.deskId);
      if (ws.windows[op.windowId]) throw new OpRefusal("window_exists", "That window exists.");
      const at = op.afterWindowId ? requireOpen(desk, op.afterWindowId) + 1 : desk.slots.length;
      const slots = desk.slots.map((slot) => [...slot]);
      slots.splice(at, 0, [op.windowId]);
      const window: DeskWindow = {
        windowId: op.windowId,
        deskId: desk.deskId,
        kind: op.stack ? "pad_stack" : (op.content as ContentRefDto).kind,
        content: op.stack ? null : (op.content ?? null),
        stack: op.stack ?? null,
        active: true,
        view: op.view ?? {},
      };
      const next = bump(desk, { slots });
      const withWindow = { ...ws, windows: { ...ws.windows, [op.windowId]: window } };
      return { ...replaceDesk(withWindow, next), windows: normalizeActive(withWindow, next, activeSet(withWindow, next)) };
    }
    case "close_window": {
      const desk = requireDesk(ws, op.deskId);
      const index = requireOpen(desk, op.windowId);
      const slots = desk.slots.map((slot) => slot.filter((id) => id !== op.windowId)).filter((slot) => slot.length > 0);
      const active = activeSet(ws, desk);
      active.delete(op.windowId);
      const next = bump(desk, { slots, focusWindowId: desk.focusWindowId === op.windowId ? null : desk.focusWindowId });
      const closedWindow = ws.windows[op.windowId];
      const windows = normalizeActive(ws, next, active);
      delete windows[op.windowId];
      const closed = { ...ws.closed, [desk.deskId]: [...(ws.closed[desk.deskId] ?? []), { window: { ...closedWindow, active: true }, slot: index }] };
      return { ...replaceDesk(ws, next), windows, closed };
    }
    case "reopen_window": {
      const desk = requireDesk(ws, op.deskId);
      const list = ws.closed[desk.deskId] ?? [];
      // An open window cannot be reopened (the server refuses it with window_open).
      if (ws.windows[op.windowId]) throw new OpRefusal("window_open", "That window is already open.");
      const entry = list.find((closed) => closed.window.windowId === op.windowId);
      if (!entry) throw new OpRefusal("window_not_found", "No such closed window.");
      const at = Math.min(op.slot ?? desk.slots.length, desk.slots.length);
      const slots = desk.slots.map((slot) => [...slot]);
      slots.splice(at, 0, [op.windowId]);
      const next = bump(desk, { slots });
      const withWindow = { ...ws, windows: { ...ws.windows, [op.windowId]: { ...entry.window, deskId: desk.deskId } } };
      return {
        ...replaceDesk(withWindow, next),
        windows: normalizeActive(withWindow, next, activeSet(withWindow, next)),
        closed: { ...ws.closed, [desk.deskId]: list.filter((closed) => closed !== entry) },
      };
    }
    case "move_window": {
      const desk = requireDesk(ws, op.deskId);
      const index = requireOpen(desk, op.windowId);
      const slots = desk.slots.map((slot) => [...slot]);
      const [slot] = slots.splice(index, 1);
      slots.splice(Math.min(op.toSlot, slots.length), 0, slot);
      return replaceDesk(ws, bump(desk, { slots }));
    }
    case "move_to_desk": {
      const from = requireDesk(ws, op.deskId);
      if (op.toDeskId === from.deskId) throw new OpRefusal("same_desk", "The window is already on that desk.");
      const to = requireDesk(ws, op.toDeskId);
      requireOpen(from, op.windowId);
      const fromActive = activeSet(ws, from);
      const fromNext = bump(from, {
        slots: from.slots.map((slot) => slot.filter((id) => id !== op.windowId)).filter((slot) => slot.length > 0),
        focusWindowId: from.focusWindowId === op.windowId ? null : from.focusWindowId,
      });
      const at = op.afterWindowId ? requireOpen(to, op.afterWindowId) + 1 : to.slots.length;
      const toSlots = to.slots.map((slot) => [...slot]);
      toSlots.splice(at, 0, [op.windowId]);
      const toNext = bump(to, { slots: toSlots });
      let next = replaceDesk(replaceDesk(ws, fromNext), toNext);
      next = { ...next, windows: normalizeActive(next, fromNext, fromActive) };
      const toActive = activeSet(next, toNext);
      toActive.add(op.windowId);
      return { ...next, windows: normalizeActive(next, toNext, toActive) };
    }
    case "pair": {
      const desk = requireDesk(ws, op.deskId);
      const index = requireOpen(desk, op.windowId);
      if (desk.slots[index].length >= PAIR_SIZE) throw new OpRefusal("slot_full", PAIR_COPY.full);
      if (index + 1 >= desk.slots.length) throw new OpRefusal("nothing_to_the_right", PAIR_COPY.nothingRight);
      if (desk.slots[index + 1].length >= PAIR_SIZE) throw new OpRefusal("slot_full", PAIR_COPY.full);
      const slots = desk.slots.map((slot) => [...slot]);
      const [neighbour] = slots.splice(index + 1, 1);
      slots[index] = [...slots[index], ...neighbour];
      const active = activeSet(ws, desk);
      for (const id of slots[index]) active.delete(id);
      active.add(op.windowId);
      const next = bump(desk, { slots });
      return { ...replaceDesk(ws, next), windows: normalizeActive(ws, next, active) };
    }
    case "unpair": {
      const desk = requireDesk(ws, op.deskId);
      const index = requireOpen(desk, op.windowId);
      if (desk.slots[index].length < PAIR_SIZE) throw new OpRefusal("not_paired", "That window already has its own slot.");
      const slots = desk.slots.map((slot) => [...slot]);
      slots[index] = slots[index].filter((id) => id !== op.windowId);
      slots.splice(index + 1, 0, [op.windowId]);
      const next = bump(desk, { slots });
      return { ...replaceDesk(ws, next), windows: normalizeActive(ws, next, activeSet(ws, desk)) };
    }
    case "set_active_pane": {
      const desk = requireDesk(ws, op.deskId);
      const index = requireOpen(desk, op.windowId);
      if (desk.slots[index].length < PAIR_SIZE) throw new OpRefusal("not_paired", "Only a pane of a pair is made active.");
      const active = activeSet(ws, desk);
      for (const id of desk.slots[index]) active.delete(id);
      active.add(op.windowId);
      const next = bump(desk);
      return { ...replaceDesk(ws, next), windows: normalizeActive(ws, next, active) };
    }
    case "set_view": {
      const desk = requireDesk(ws, op.deskId);
      requireOpen(desk, op.windowId);
      const window = ws.windows[op.windowId];
      return { ...replaceDesk(ws, bump(desk)), windows: { ...ws.windows, [op.windowId]: { ...window, view: op.view } } };
    }
    case "add_to_stack":
    case "remove_from_stack": {
      // A stack's membership by one entry: a union or a removal, the same at any desk version (no expected
      // version is checked), in the window's spec apart from its view. It bumps the desk either way.
      const desk = requireDesk(ws, op.deskId);
      const window = ws.windows[op.windowId];
      if (!window || window.deskId !== desk.deskId) throw new OpRefusal("window_not_found", `No window ${op.windowId} on that desk.`);
      if (window.kind !== "pad_stack") throw new OpRefusal("not_a_stack", "That window is not a pad stack.");
      const stack = window.stack ?? [];
      const present = stack.some((entry) => sameEntry(entry, op.entry));
      let next = stack;
      if (op.op === "add_to_stack" && !present) next = [...stack, op.entry];
      if (op.op === "remove_from_stack" && present) {
        next = stack.filter((entry) => !sameEntry(entry, op.entry));
        if (next.length === 0) throw new OpRefusal("last_in_stack", "A stack holds at least one pad: close the window instead.");
      }
      return { ...replaceDesk(ws, bump(desk)), windows: { ...ws.windows, [op.windowId]: { ...window, stack: next } } };
    }
    case "ensure_running_pad": {
      // The desk's running pad, and a stack window of the desk holding it: whichever is missing is created.
      const desk = requireDesk(ws, op.deskId);
      const running = new Set(ws.runningPadIds ?? []);
      const stacks = desk.slots.flat().map((id) => ws.windows[id]).filter((window): window is DeskWindow => window?.kind === "pad_stack");
      const holding = stacks.find((window) => (window.stack ?? []).some((entry) => entry.kind === "pad" && running.has(entry.padId)));
      if (holding) return replaceDesk(ws, bump(desk));
      const runningPadIds = [...(ws.runningPadIds ?? []), op.padId];
      const entry: PadStackEntryDto = { kind: "pad", padId: op.padId };
      if (stacks.length) {
        const first = stacks[0];
        return { ...replaceDesk(ws, bump(desk)), runningPadIds, windows: { ...ws.windows, [first.windowId]: { ...first, stack: [...(first.stack ?? []), entry] } } };
      }
      if (ws.windows[op.windowId]) throw new OpRefusal("window_exists", "That window exists.");
      const window: DeskWindow = { windowId: op.windowId, deskId: desk.deskId, kind: "pad_stack", content: null, stack: [entry], active: true, view: {} };
      const next = bump(desk, { slots: [...desk.slots.map((slot) => [...slot]), [op.windowId]] });
      const withWindow = { ...ws, runningPadIds, windows: { ...ws.windows, [op.windowId]: window } };
      return { ...replaceDesk(withWindow, next), windows: normalizeActive(withWindow, next, activeSet(withWindow, next)) };
    }
  }
}

// -- intents: the next workspace and the ops that persist it ---------------------------------------

export interface Step {
  ws: Workspace;
  ops: DeskOpDto[];
  /** A one-line notice for the learner (the toast), when the intent did nothing or something to know. */
  notice?: string;
}

export const PAIR_COPY = {
  full: "a slot holds at most two windows · alt+. takes one out",
  nothingRight: "nothing to the right to share this slot with",
} as const;

/** Stamp `op` with the version its desk(s) have now, apply it, and add it to the step. */
function push(step: Step, op: DeskOpDto): Step {
  const versioned: DeskOpDto = { ...op };
  if (op.op !== "create_desk") {
    versioned.expectedVersion = requireDesk(step.ws, op.deskId).version;
  }
  if (op.op === "move_to_desk") {
    (versioned as Extract<DeskOpDto, { op: "move_to_desk" }>).toExpectedVersion = requireDesk(step.ws, op.toDeskId).version;
  }
  return { ...step, ws: applyDeskOp(step.ws, versioned), ops: [...step.ops, versioned] };
}

/** One queued op re-applied on a newer workspace (after a conflict): its expected versions stamped from
 * that workspace. Throws OpRefusal when it no longer applies there. */
export function restampOp(ws: Workspace, op: DeskOpDto): { ws: Workspace; op: DeskOpDto } {
  const step = push({ ws, ops: [] }, op);
  return { ws: step.ws, op: step.ops[0] };
}

function start(ws: Workspace): Step {
  return { ws, ops: [] };
}

export function setFocus(ws: Workspace, deskId: string, windowId: string): Step {
  const desk = requireDesk(ws, deskId);
  let step = start(ws);
  const index = slotIndexOf(desk, windowId);
  if (index < 0) return step;
  if (desk.slots[index].length >= PAIR_SIZE && !ws.windows[windowId]?.active) {
    step = push(step, { op: "set_active_pane", deskId, windowId });
  }
  if (desk.focusWindowId !== windowId) step = push(step, { op: "set_focus", deskId, windowId });
  return step;
}

/** Open beside the focus, or focus the window already showing it (spec §5.2: no duplicate opens). */
export function openBeside(
  ws: Workspace,
  deskId: string,
  content: ContentRefDto,
  mintId: () => string,
  options: { spanId?: string | null; order?: (spanId: string) => number; view?: Record<string, unknown> } = {},
): Step & { windowId: string; existed: boolean } {
  const desk = requireDesk(ws, deskId);
  const duplicate = findDuplicate(ws, desk, content, options.spanId ?? null, options.order);
  if (duplicate) return { ...setFocus(ws, deskId, duplicate), windowId: duplicate, existed: true };
  const windowId = mintId();
  const focus = focusedWindowId(ws, desk);
  let step = push(start(ws), {
    op: "open_window",
    deskId,
    windowId,
    content,
    // The window it was opened beside: an explicit relation (the overview's links, gather), kept in the
    // view so later view saves (which spread the view) carry it on.
    view: { ...(options.view ?? {}), ...(focus ? { openedBeside: focus } : {}) },
    afterWindowId: focus ? lastOfSlot(desk, focus) : null,
  });
  step = push(step, { op: "set_focus", deskId, windowId });
  return { ...step, windowId, existed: false };
}

/** A pad joins a stack window (spec §10; a union by one entry, never a whole-view write, so a tab another device
 * added, or a desk change meanwhile, cannot drop it). Already there: nothing to send. */
export function addToStack(ws: Workspace, deskId: string, windowId: string, padId: string): Step {
  const window = ws.windows[windowId];
  if (window?.stack?.some((entry) => entry.kind === "pad" && entry.padId === padId)) return start(ws);
  return push(start(ws), { op: "add_to_stack", deskId, windowId, entry: { kind: "pad", padId } });
}

/** The desk's running pad (spec §10.5), ensured: created with a stack window when the desk has none in its
 * stacks (the op is idempotent on the server; ids are used only for what it creates). */
export function ensureRunningPad(ws: Workspace, deskId: string, mintPad: () => string, mintWindow: () => string): Step {
  return push(start(ws), { op: "ensure_running_pad", deskId, padId: mintPad(), windowId: mintWindow(), title: "running" });
}

/** Whether a desk's stacks hold one of the running pads the server knows. */
export function hasRunningPad(ws: Workspace, deskId: string): boolean {
  const desk = deskById(ws, deskId);
  const running = new Set(ws.runningPadIds ?? []);
  return Boolean(desk?.slots.flat().some((id) => (ws.windows[id]?.stack ?? []).some((entry) => entry.kind === "pad" && running.has(entry.padId))));
}

/** A pad stack window opened beside the focus (alt+n away from a stack: spec §10.5). */
export function openStackBeside(ws: Workspace, deskId: string, padIds: string[], mintId: () => string, view: Record<string, unknown> = {}): Step & { windowId: string } {
  const desk = requireDesk(ws, deskId);
  const windowId = mintId();
  const focus = focusedWindowId(ws, desk);
  let step = push(start(ws), {
    op: "open_window", deskId, windowId, stack: padIds.map((padId) => ({ kind: "pad" as const, padId })), view,
    afterWindowId: focus ? lastOfSlot(desk, focus) : null,
  });
  step = push(step, { op: "set_focus", deskId, windowId });
  return { ...step, windowId };
}

function lastOfSlot(desk: Desk, windowId: string): string {
  const slot = desk.slots[slotIndexOf(desk, windowId)];
  return slot[slot.length - 1];
}

/** Close a window; the focus moves to its neighbour (the one now in its slot, else the one before). */
export function closeWindow(ws: Workspace, deskId: string, windowId: string): Step {
  const desk = requireDesk(ws, deskId);
  const index = slotIndexOf(desk, windowId);
  if (index < 0) return start(ws);
  const wasFocus = focusedWindowId(ws, desk) === windowId;
  let step = push(start(ws), { op: "close_window", deskId, windowId });
  if (wasFocus) {
    const after = requireDesk(step.ws, deskId);
    const at = Math.min(index, after.slots.length - 1);
    const next = at >= 0 ? (after.slots[at].find((id) => step.ws.windows[id]?.active) ?? after.slots[at][0]) : null;
    if (next) step = push(step, { op: "set_focus", deskId, windowId: next });
  }
  return step;
}

/** Undo the newest close on this desk: the window comes back in its slot and takes the focus. */
export function undoClose(ws: Workspace, deskId: string): Step {
  const list = ws.closed[deskId] ?? [];
  const entry = list[list.length - 1];
  // A window that is open again (its close was refused) is nothing to undo.
  if (!entry || ws.windows[entry.window.windowId]) return start(ws);
  let step = push(start(ws), { op: "reopen_window", deskId, windowId: entry.window.windowId, slot: entry.slot });
  step = push(step, { op: "set_focus", deskId, windowId: entry.window.windowId });
  return step;
}

/** alt+[ / alt+]: move the focused window's slot one place along the desk. */
export function moveFocused(ws: Workspace, deskId: string, direction: -1 | 1): Step {
  const desk = requireDesk(ws, deskId);
  const id = focusedWindowId(ws, desk);
  const index = slotIndexOf(desk, id);
  const to = index + direction;
  if (!id || index < 0 || to < 0 || to >= desk.slots.length) return start(ws);
  return push(start(ws), { op: "move_window", deskId, windowId: id, toSlot: to });
}

/** A shelf drag: a window's slot moves to `toSlot`. */
export function moveWindowTo(ws: Workspace, deskId: string, windowId: string, toSlot: number): Step {
  const desk = requireDesk(ws, deskId);
  const index = slotIndexOf(desk, windowId);
  if (index < 0 || index === toSlot || toSlot < 0 || toSlot >= desk.slots.length) return start(ws);
  return push(start(ws), { op: "move_window", deskId, windowId, toSlot });
}

/** alt+,: the focused window shares its slot with its right neighbour (top and bottom). */
export function pairFocused(ws: Workspace, deskId: string): Step {
  const desk = requireDesk(ws, deskId);
  const id = focusedWindowId(ws, desk);
  const index = slotIndexOf(desk, id);
  if (!id || index < 0) return start(ws);
  if (desk.slots[index].length >= PAIR_SIZE) return { ...start(ws), notice: PAIR_COPY.full };
  if (index + 1 >= desk.slots.length) return { ...start(ws), notice: PAIR_COPY.nothingRight };
  if (desk.slots[index + 1].length >= PAIR_SIZE) return { ...start(ws), notice: PAIR_COPY.full };
  return push(start(ws), { op: "pair", deskId, windowId: id });
}

/** alt+.: the active pane gets its own slot right after the pair, and keeps the focus. */
export function unpairFocused(ws: Workspace, deskId: string): Step {
  const desk = requireDesk(ws, deskId);
  const id = focusedWindowId(ws, desk);
  const index = slotIndexOf(desk, id);
  if (!id || index < 0 || desk.slots[index].length < PAIR_SIZE) return start(ws);
  let step = push(start(ws), { op: "unpair", deskId, windowId: id });
  if (requireDesk(step.ws, deskId).focusWindowId !== id) step = push(step, { op: "set_focus", deskId, windowId: id });
  return step;
}

/** alt+h / alt+l: the focus moves one slot along (to the neighbour slot's active pane). */
export function focusAlong(ws: Workspace, deskId: string, direction: -1 | 1): Step {
  const desk = requireDesk(ws, deskId);
  const index = focusedSlot(ws, desk);
  const to = index + direction;
  if (index < 0 || to < 0 || to >= desk.slots.length) return start(ws);
  const target = desk.slots[to].find((id) => ws.windows[id]?.active) ?? desk.slots[to][0];
  return setFocus(ws, deskId, target);
}

/** alt+j / alt+k inside a pair: the other pane. Returns null when the focus is not in a pair or is
 * already at that end, so the caller moves on to the next desk (niri's focus-window-or-workspace). */
export function focusPane(ws: Workspace, deskId: string, direction: -1 | 1): Step | null {
  const desk = requireDesk(ws, deskId);
  const id = focusedWindowId(ws, desk);
  const index = slotIndexOf(desk, id);
  if (!id || index < 0) return null;
  const slot = desk.slots[index];
  const pane = slot.indexOf(id);
  const to = pane + direction;
  if (slot.length < PAIR_SIZE || to < 0 || to >= slot.length) return null;
  return setFocus(ws, deskId, slot[to]);
}

/** A fractional position after every desk's (positions are strings that sort). */
export function positionAfter(ws: Workspace): string {
  const last = ws.desks[ws.desks.length - 1]?.position ?? "";
  return `${last}n`;
}

export function createDesk(ws: Workspace, deskId: string, title: string): Step {
  return push(start(ws), { op: "create_desk", deskId, title, position: positionAfter(ws) });
}

export function renameDesk(ws: Workspace, deskId: string, title: string): Step {
  return push(start(ws), { op: "rename_desk", deskId, title });
}

/** The companion's dock on this desk, remembered there (spec §8.2). */
export function setCompanionDock(ws: Workspace, deskId: string, dock: Desk["companion"]["dock"]): Step {
  const desk = requireDesk(ws, deskId);
  if (desk.companion.dock === dock) return start(ws);
  return push(start(ws), { op: "set_dock", deskId, dock });
}

/** Whether the companion shows on this desk, remembered there for the next time the desks open. */
export function setCompanionShown(ws: Workspace, deskId: string, shown: boolean): Step {
  const desk = requireDesk(ws, deskId);
  if (desk.companion.shown === shown) return start(ws);
  return push(start(ws), { op: "set_companion_shown", deskId, shown });
}

/** The desk's goal (spec §12.1): the band's goal label switches it; null is "no goal" (the lens off). */
export function setGoal(ws: Workspace, deskId: string, goalId: string | null): Step {
  const desk = requireDesk(ws, deskId);
  if (desk.goalId === goalId) return start(ws);
  return push(start(ws), { op: "set_goal", deskId, goalId });
}

export function setView(ws: Workspace, deskId: string, windowId: string, view: Record<string, unknown>): Step {
  const desk = requireDesk(ws, deskId);
  if (slotIndexOf(desk, windowId) < 0) return start(ws);
  return push(start(ws), { op: "set_view", deskId, windowId, view });
}

/** Swap the two windows in view (`x`): the focus slot and the slot beside it in the viewport. */
export function swapInView(ws: Workspace, deskId: string, otherSlot: number): Step {
  const desk = requireDesk(ws, deskId);
  const id = focusedWindowId(ws, desk);
  const index = slotIndexOf(desk, id);
  if (!id || index < 0 || otherSlot < 0 || otherSlot >= desk.slots.length || otherSlot === index) return start(ws);
  return push(start(ws), { op: "move_window", deskId, windowId: id, toSlot: otherSlot });
}

/** Reorder a desk's slots to `order` (the same slots, each named by its windows), as move_window ops:
 * slot by slot from the left, each moved to its place. Gather and ungather use it (spec §6.6). */
export function reorderSlots(ws: Workspace, deskId: string, order: string[][]): Step {
  let step = start(ws);
  order.forEach((slot, index) => {
    const desk = requireDesk(step.ws, deskId);
    const at = slotIndexOf(desk, slot[0]);
    if (at < 0 || at === index) return;
    step = push(step, { op: "move_window", deskId, windowId: slot[0], toSlot: index });
  });
  return step;
}

/** A window to another desk's slot `toIndex` (a drop on a card's place, alt+shift+j/k). The transfer op
 * places a window after another one or at the end, so a move to slot 0 of a desk that has slots is the
 * transfer and then a move to slot 0 at the destination's next version. */
export function moveToDeskAt(ws: Workspace, deskId: string, windowId: string, toDeskId: string, toIndex: number): Step {
  const to = requireDesk(ws, toDeskId);
  const at = Math.max(0, Math.min(toIndex, to.slots.length));
  const afterSlot = to.slots[at - 1];
  let step = moveToDesk(ws, deskId, windowId, toDeskId, afterSlot ? afterSlot[afterSlot.length - 1] : null);
  if (at === 0 && to.slots.length > 0 && step.ops.length > 0) {
    const landed = requireDesk(step.ws, toDeskId);
    if (slotIndexOf(landed, windowId) !== 0) step = push(step, { op: "move_window", deskId: toDeskId, windowId, toSlot: 0 });
  }
  return step;
}

/** A window to another desk, after `afterWindowId` there (or at the end), keeping its focus on the old
 * desk's neighbour. Its pair partner, if any, stays. */
export function moveToDesk(ws: Workspace, deskId: string, windowId: string, toDeskId: string, afterWindowId: string | null): Step {
  const desk = requireDesk(ws, deskId);
  if (deskId === toDeskId || slotIndexOf(desk, windowId) < 0) return start(ws);
  const index = slotIndexOf(desk, windowId);
  const wasFocus = focusedWindowId(ws, desk) === windowId;
  let step = push(start(ws), { op: "move_to_desk", deskId, windowId, toDeskId, toExpectedVersion: 0, afterWindowId });
  if (wasFocus) {
    const after = requireDesk(step.ws, deskId);
    const at = Math.min(index, after.slots.length - 1);
    const next = at >= 0 ? after.slots[at][0] : null;
    if (next) step = push(step, { op: "set_focus", deskId, windowId: next });
  }
  return step;
}

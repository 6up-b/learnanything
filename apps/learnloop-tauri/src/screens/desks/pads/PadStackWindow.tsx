// A pad stack window (spec §10.1–§10.9): one window, one scroller, each pad's sticky tab and paper siblings.
// Tabs of pads passed pile at the top and tabs of pads ahead wait at the bottom; the open tab merges with its
// paper, and under the `distance` grade curved fillets flare it into the paper as it is revealed. The running
// pad is a dated notebook ending in "jot · it lands here by default". Every editable block opens in place;
// each write goes through the vault's store (applied at once, sent by `pad.apply`). LearnLoop speaks only
// through gutter marks and their hover cards.
import { forwardRef, useCallback, useEffect, useImperativeHandle, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import type { PadAnchorDto, PadBlockDto, PadProposalDto, PadStackEntryDto } from "../../../api/dto";
import { MarkdownMath } from "../../../render/MarkdownMath";
import { LiveMarkdownEditor } from "../../../render/LiveMarkdownEditor";
import { FitMath } from "../fitMath";
import { useHubListener, useScopeClaim, useWindowPaused } from "../lifecycle";
import { dayHeading, usePadsHost, type PadStackHandle, type PadsHost } from "./host";
import { EDITABLE_KINDS, firstLine, isLearnersWords, keyAfter, padName, type PadState, plainLine } from "./model";
import { PadMenu, ArrangeOverlay, SubmitSheet, type MenuRequest } from "./PadOverlays";
import { SketchCanvas } from "./SketchCanvas";
import { InkBlock, InkJot } from "../pen/InkLine";
import { usePenHost } from "../pen/host";
import { PadCell } from "../notebook/PadCell";
import { ProblemPad, type ProblemInk } from "../problem/ProblemPad";
import { problemOf, problemsVersion, subscribeProblems } from "../problem/problemPads";
import { activePad, fractionalOpen, mergeAmount, paperMinHeight, scrollTargetFor, tabMargin, type PadGeometry, type TabGrade } from "./stickyTabs";
import { isLessonItem, lessonOfKey, lessonTabMeta, lessonTabTitle, stackItemKeys } from "../lesson/model";
import { LessonPaper } from "../lesson/LessonPaper";

const NO_OPENINGS: string[] = [];
const noSubscribe = () => () => undefined;
const noVersion = () => 0;

/** Hover cards (spec §10.6): open 160 ms after the pointer settles, hide 220 ms after it leaves. */
export const CARD_MS = { open: 160, hide: 220 } as const;
/** A block reached from a passage's ✎ link flashes this long (spec §10.7). */
export const FLASH_MS = 1800;
const GRADE_KEY = "learnloop.desks.tabGrade";

function readGrade(): TabGrade {
  try {
    const stored = window.localStorage.getItem(GRADE_KEY);
    return stored === "flat" || stored === "order" || stored === "distance" ? stored : "distance";
  } catch {
    return "distance";
  }
}

function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function clock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** The pads a stack shows: its entries, then pads an earlier build added through the window's view (shown, and
 * moved into the stack by add_to_stack when the desks open). */
export function stackPadIds(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined): string[] {
  const own = stack.filter((entry): entry is Extract<PadStackEntryDto, { kind: "pad" }> => entry.kind === "pad").map((entry) => entry.padId);
  const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string => typeof id === "string") : [];
  return [...own, ...added.filter((id) => !own.includes(id))];
}

/** A pad's tab meta, as the mockup reads it. */
export function tabMeta(state: PadState, today: string): string {
  const pad = state.pad;
  const updated = pad.updatedAt.slice(0, 10);
  if (pad.kind === "running") return `running · ${updated === today ? "today" : shortDate(updated)}`;
  if (pad.kind === "problem") return `a problem · ${shortDate(pad.updatedAt)}`;
  if (pad.kind === "ink") return `handwritten · ${updated === today ? "today" : shortDate(updated)}`;
  return updated === today ? "today" : shortDate(pad.updatedAt);
}

/** The words a quote block's back-link names: "§ <source> p.<page> ↩" or "▶ <video> <time> ↩". */
export function backLink(block: PadBlockDto, anchors: PadAnchorDto[] = []): { label: string; extractionId: string | null; spanId: string | null; t?: number; sourceId: string | null } {
  const p = block.payload as Record<string, unknown>;
  // The block's own link names its source (and a cue's time) even with no window of it open.
  const link = anchors.find((anchor) => anchor.blockId === block.blockId);
  const sourceId = typeof p.source_id === "string" ? p.source_id : link?.sourceId ?? null;
  const title = typeof p.source_title === "string" ? p.source_title : "the source";
  const extractionId = typeof p.extraction_id === "string" ? p.extraction_id : null;
  const spanId = typeof p.span_id === "string" ? p.span_id : null;
  const t = typeof p.t === "number" ? p.t : typeof link?.t === "number" ? link.t : undefined;
  if (t !== undefined) return { label: `▶ ${title} ${clock(t)} ↩`, extractionId, spanId, t, sourceId };
  return { label: `§ ${title}${typeof p.page === "number" ? ` p.${p.page}` : ""} ↩`, extractionId, spanId, sourceId };
}

interface Card {
  padId: string;
  blockId: string;
  kind: "source" | "tutor" | "figure" | "proposal";
  top: number;
  left: number;
  above: boolean;
}

export interface PadStackProps {
  windowId: string;
  stack: PadStackEntryDto[];
  view: Record<string, unknown>;
  /** "where your words go", opened from ⓘ in the window's title bar (the desks hold it); absent, the stack shows
   * its own ⓘ above the pads. */
  info?: boolean;
  onInfo?: (open: boolean) => void;
}

export const PadStackWindow = forwardRef<PadStackHandle, PadStackProps>(function PadStackWindow({ windowId, stack, view, info, onInfo }, ref) {
  const host = usePadsHost();
  if (!host) return <div className="desk-panel desk-quiet">Open this pad from a desk.</div>;
  return <PadStackBody ref={ref} host={host} windowId={windowId} stack={stack} view={view} info={info} onInfo={onInfo} />;
});

const PadStackBody = forwardRef<PadStackHandle, PadStackProps & { host: PadsHost }>(function PadStackBody({ host, windowId, stack, view, info: infoProp, onInfo }, ref) {
  const { store } = host;
  useSyncExternalStore(store.subscribe, store.getPadVersion);
  const paused = useWindowPaused();
  const pausedRef = useRef(paused);
  pausedRef.current = paused;
  // A stack's items are its pads and its Teacher lessons (spec §11.1), keyed as lesson/model says; a lesson's
  // additions pad is read with it.
  const lessons = host.lessons ?? null;
  const lessonsVersion = useSyncExternalStore(lessons?.desk.subscribe ?? noSubscribe, lessons?.desk.getVersion ?? noVersion);
  const openings = lessons ? lessons.desk.openingsFor(windowId) : NO_OPENINGS;
  const openingsKey = openings.join("|");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const padIds = useMemo(() => stackItemKeys(stack, view, openings), [stack, view, openingsKey]);
  useEffect(() => {
    if (paused) return;
    for (const padId of padIds) {
      if (!isLessonItem(padId)) {
        void store.loadPad(padId);
        continue;
      }
      const lessonId = lessonOfKey(padId);
      const additions = lessonId ? lessons?.desk.additionsFor(lessonId) : null;
      if (additions) void store.loadPad(additions);
      for (const older of lessonId ? lessons?.desk.olderAdditions(lessonId) ?? [] : []) void store.loadPad(older);
    }
  }, [padIds, paused, store, lessons, lessonsVersion]);
  const pads = padIds.map((padId) => store.pads[padId] ?? null);
  const today = host.today();
  // Ink (RD8a): the pads' ink lines are read once shown; their readings stop when the window closes.
  const pen = usePenHost();
  const [inkView, setInkView] = useState<Record<string, { hidden?: boolean; dotted?: boolean }>>({});
  // "type what you wrote" asked for a line (a problem pad's ladder offers it for a line it cannot see yet).
  const [fixRequests, setFixRequests] = useState<Record<string, number>>({});
  useSyncExternalStore(subscribeProblems, problemsVersion);
  /** A problem pad whose workbench is shown here: its ink lines with text are its steps, shown in the workbench. */
  const hostsProblem = (state: PadState): boolean => {
    const sessionId = state.pad.kind === "problem" ? state.pad.workbenchSessionId : null;
    const handed = sessionId && host.problems ? problemOf(sessionId) : null;
    return Boolean(handed && !handed.away);
  };
  const problemInk = (state: PadState, padId: string): ProblemInk => {
    const lines = state.blocks.filter((block) => block.kind === "ink");
    return {
      lines: lines.map((block) => {
        const text = block.bodyMd.trim();
        return { lineId: block.blockId, text, reading: Boolean(text) && block.provenance === "ink_transcription",
          refused: pen?.ink.pad(padId).readings[block.blockId]?.status === "cannot" };
      }),
      renderLine: (blockId) => {
        const block = lines.find((each) => each.blockId === blockId);
        return block ? (
          <InkBlock padId={padId} block={block} windowId={windowId} paused={paused} showTranscription={!inkView[padId]?.hidden}
            write={(ops) => write(padId, ops)} fixRequest={fixRequests[blockId]} />
        ) : null;
      },
      typeWhatYouWrote: (blockId) => setFixRequests((now) => ({ ...now, [blockId]: (now[blockId] ?? 0) + 1 })),
    };
  };
  const inkPads = pads.filter((state) => state && (state.pad.kind === "ink" || state.blocks.some((block) => block.kind === "ink"))).map((state) => state!.pad.padId).join("|");
  useEffect(() => {
    if (paused || !pen) return;
    // Read again each time the pads are shown: a pad reopened shows the ink as the server holds it now.
    for (const padId of inkPads.split("|").filter(Boolean)) void pen.ink.load(padId, true);
  }, [inkPads, paused, pen]);
  const padKey = padIds.join("|");
  useEffect(() => () => pen?.ink.cancelAll(padKey.split("|").filter(Boolean)), [pen, padKey]);

  const [grade] = useState<TabGrade>(readGrade);
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const tabEls = useRef(new Map<string, HTMLElement>());
  const paperEls = useRef(new Map<string, HTMLElement>());
  const blockEls = useRef(new Map<string, HTMLElement>());
  const [active, setActive] = useState(0);
  const [viewport, setViewport] = useState(600);
  const [editing, setEditing] = useState<{ padId: string; blockId: string; draft: string; original: string; focus: number } | null>(null);
  // The editor's box gets the focus a frame after it mounts; until then its frame holds it, so letters typed
  // right after ↵ are the editor's (a typing scope) and never reach the desks' keys.
  const editorRef = useRef<HTMLDivElement | null>(null);
  useLayoutEffect(() => {
    const frame = editorRef.current;
    if (frame && !frame.contains(document.activeElement)) frame.focus({ preventScroll: true });
  }, [editing?.blockId, editing?.focus]);
  const [card, setCard] = useState<Card | null>(null);
  const cardTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [menu, setMenu] = useState<MenuRequest | null>(null);
  const menuOpening = useRef(0);
  const [arranging, setArranging] = useState(false);
  const [submitting, setSubmitting] = useState<{ padId: string; blockId: string } | null>(null);
  const [infoOwn, setInfoOwn] = useState(false);
  const info = infoProp ?? infoOwn;
  const setInfo = (next: boolean | ((now: boolean) => boolean)) => {
    const value = typeof next === "function" ? next(info) : next;
    if (onInfo) onInfo(value);
    else setInfoOwn(value);
  };
  const [flash, setFlash] = useState<string | null>(null);
  const [proposals, setProposals] = useState<Record<string, PadProposalDto[]>>({});
  const hovered = useRef<{ padId: string; blockId: string | null; text: string; x: number; y: number } | null>(null);
  const split = readSplit(view, padIds);
  const [paneFocus, setPaneFocus] = useState(0);
  const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : [];

  // The editor takes typed keys while it is open (the desk's bare keys must not act first).
  useScopeClaim("typing", editing !== null);
  useScopeClaim("menu", menu !== null || arranging || submitting !== null);

  // -- geometry: the sticky tabs, written per tab each scroll frame ------------------------------------
  const geometry = useCallback((): PadGeometry[] => {
    const scroller = scrollerRef.current;
    if (!scroller) return [];
    const base = scroller.getBoundingClientRect().top - scroller.scrollTop;
    return padIds.map((padId) => {
      const tab = tabEls.current.get(padId);
      const paper = paperEls.current.get(padId);
      // Sticky tabs move, so their flow position is read from the paper (the tab sits right above it).
      const paperTop = paper ? paper.getBoundingClientRect().top - base : 0;
      const height = paper?.offsetHeight ?? 0;
      return { tabTop: paperTop - (tab?.offsetHeight ?? 30), paperTop, paperBottom: paperTop + height };
    });
  }, [padIds]);

  const layoutTabs = useCallback(() => {
    const scroller = scrollerRef.current;
    if (!scroller || split) return;
    const geo = geometry();
    const top = scroller.scrollTop;
    const h = scroller.clientHeight;
    const now = activePad(geo, top, h, scroller.scrollHeight);
    const open = fractionalOpen(geo, top, h, scroller.scrollHeight);
    padIds.forEach((padId, i) => {
      const tab = tabEls.current.get(padId);
      const paper = paperEls.current.get(padId);
      const m = mergeAmount(i, geo, top, h);
      const margin = tabMargin(grade, i, open);
      if (tab) {
        tab.style.marginLeft = `${margin}px`;
        tab.style.marginRight = `${margin}px`;
        tab.style.setProperty("--fillet", grade === "distance" ? m.toFixed(3) : "0");
        tab.dataset.merge = m.toFixed(2);
      }
      if (paper) {
        paper.style.marginLeft = `${margin}px`;
        paper.style.marginRight = `${margin}px`;
      }
    });
    if (now >= 0) setActive(now);
    setViewport(h);
  }, [geometry, grade, padIds, split]);

  useLayoutEffect(() => {
    layoutTabs();
  });
  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        layoutTabs();
      });
    };
    scroller.addEventListener("scroll", onScroll, { passive: true });
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(() => layoutTabs());
    observer?.observe(scroller);
    return () => {
      scroller.removeEventListener("scroll", onScroll);
      observer?.disconnect();
      if (frame) cancelAnimationFrame(frame);
    };
  }, [layoutTabs]);

  const scrollToPad = useCallback((index: number) => {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    const target = scrollTargetFor(index, geometry());
    scroller.scrollTo?.({ top: target, behavior: "smooth" });
    if (!scroller.scrollTo) scroller.scrollTop = target;
    setActive(index);
  }, [geometry]);

  // An opening whose lesson the stack now holds itself is done.
  const ownLessons = stack.filter((entry) => entry.kind === "lesson").map((entry) => (entry.kind === "lesson" ? entry.lessonId : "")).join("|");
  useEffect(() => {
    if (lessons && ownLessons) lessons.desk.landed(windowId, ownLessons.split("|"));
  }, [lessons, ownLessons, windowId]);

  // A lesson just opened here (or asked for from elsewhere) is scrolled to once the stack shows its tab.
  useEffect(() => {
    if (!lessons || split) return;
    const key = lessons.desk.takeReveal(windowId, padIds);
    if (key) scrollToPad(padIds.indexOf(key));
  });

  // -- proposals: read when a pad is shown (never while the window is paused), again after a write ------
  const proposalsFor = useCallback((padId: string) => {
    if (paused) return;
    void host.api.padProposals({ padId }).then(
      (out) => setProposals((now) => ({ ...now, [padId]: out.proposals })),
      () => undefined,
    );
  }, [host.api, paused]);
  const loadedKey = pads.map((pad) => (pad ? pad.pad.padId : "")).join("|");
  useEffect(() => {
    if (paused) return;
    for (const padId of padIds) if (store.pads[padId]) proposalsFor(padId);
    // Read once per pad shown; writes refresh their own pad.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedKey, paused]);

  // -- writing ---------------------------------------------------------------------------------------
  const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean => {
    // A paused window writes nothing (a hidden desk's pad, a card in the overview), read now: an insert that
    // waited on a read (a source piece) must not write through a closure from while it was live.
    if (pausedRef.current) return false;
    const refused = store.commitPad(padId, ops);
    if (refused) {
      host.toast(refused.code === "not_editable" ? "a quote is the source's words · add a note under it" : `couldn't change the pad · ${refused.message}`);
      return false;
    }
    return true;
  }, [host, store]);

  const insertAfter = useCallback((padId: string, after: string | null, block: { kind: PadBlockDto["kind"]; provenance: PadBlockDto["provenance"]; bodyMd?: string; payload?: Record<string, unknown> }, edit = false): string | null => {
    const state = store.pads[padId];
    if (!state) return null;
    const blockId = host.mintId("blk");
    // A piece of a source is linked to its passage in the same write: the passage shows ✎ back to it.
    const p = block.payload ?? {};
    const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string"
      ? [{ op: "link_anchor" as const, blockId, extractionId: p.extraction_id, spanId: p.span_id, eventId: host.mintId("lnk"), expectedAnchorHead: null }]
      : [];
    const ok = write(padId, [{
      op: "insert_block", blockId, versionId: host.mintId("ver"), kind: block.kind, provenance: block.provenance,
      positionKey: keyAfter(state.blocks, after), day: state.pad.kind === "running" ? today : null, bodyMd: block.bodyMd ?? "", payload: p,
    }, ...link]);
    if (ok && edit) setEditing({ padId, blockId, draft: block.bodyMd ?? "", original: block.bodyMd ?? "", focus: Date.now() });
    return ok ? blockId : null;
  }, [host, store, today, write]);

  const commitEdit = useCallback((next?: { padId: string; blockId: string; draft: string; original: string }) => {
    const current = next ?? editing;
    if (!current) return;
    const block = store.pads[current.padId]?.blocks.find((each) => each.blockId === current.blockId);
    if (block && current.draft !== block.bodyMd) {
      write(current.padId, [{ op: "edit_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver"), bodyMd: current.draft }]);
      // Proposals are computed when a block is committed: read them again shortly.
      setTimeout(() => proposalsFor(current.padId), 1200);
    }
  }, [editing, host, proposalsFor, store, write]);

  const openEditor = (padId: string, block: PadBlockDto) => {
    // A sketch, an ink line and a marimo cell edit in their own surface (an ink line's transcription in its own field).
    if (!EDITABLE_KINDS.has(block.kind) || block.kind === "sketch" || block.kind === "ink" || block.kind === "cell") return;
    // The block being edited is never reopened: that would reset the draft to the words it had when opened.
    if (editing?.blockId === block.blockId) return;
    if (window.getSelection?.()?.toString()) return;
    if (editing) commitEdit();
    setEditing({ padId, blockId: block.blockId, draft: block.bodyMd, original: block.bodyMd, focus: Date.now() });
  };

  const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null => {
    const blocks = store.pads[padId]?.blocks ?? [];
    const index = blocks.findIndex((each) => each.blockId === blockId);
    for (let i = index + direction; i >= 0 && i < blocks.length; i += direction) {
      if (EDITABLE_KINDS.has(blocks[i].kind) && blocks[i].kind !== "sketch" && blocks[i].kind !== "ink" && blocks[i].kind !== "cell") return blocks[i];
    }
    return null;
  };

  const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info: { atEnd: boolean; empty: boolean }) => {
    if (!editing) return;
    const textarea = event.currentTarget;
    if (event.key === "Enter" && !event.shiftKey) {
      // ↵ keeps the line and opens a new block below.
      event.preventDefault();
      commitEdit();
      setEditing(null);
      insertAfter(editing.padId, editing.blockId, { kind: "text", provenance: "learner" }, true);
    } else if (event.key === "Escape") {
      // esc puts it back as it was; a line just opened and never written goes away again.
      event.preventDefault();
      event.stopPropagation();
      const block = store.pads[editing.padId]?.blocks.find((each) => each.blockId === editing.blockId);
      setEditing(null);
      if (block && block.bodyMd === "" && block.kind === "text") write(editing.padId, [{ op: "remove_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver") }]);
    } else if (event.key === "Backspace" && info.empty) {
      event.preventDefault();
      const block = store.pads[editing.padId]?.blocks.find((each) => each.blockId === editing.blockId);
      const previous = editableNeighbour(editing.padId, editing.blockId, -1);
      setEditing(null);
      if (block) write(editing.padId, [{ op: "remove_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver") }]);
      if (previous) setEditing({ padId: editing.padId, blockId: previous.blockId, draft: previous.bodyMd, original: previous.bodyMd, focus: Date.now() });
    } else if ((event.key === "ArrowUp" && textarea.selectionStart === 0 && textarea.selectionEnd === 0) || (event.key === "ArrowDown" && info.atEnd)) {
      const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1);
      if (!neighbour) return;
      event.preventDefault();
      commitEdit();
      setEditing({ padId: editing.padId, blockId: neighbour.blockId, draft: neighbour.bodyMd, original: neighbour.bodyMd, focus: Date.now() });
    }
  };

  // -- hover cards -----------------------------------------------------------------------------------
  const scheduleCard = (next: Card | null) => {
    if (cardTimer.current) clearTimeout(cardTimer.current);
    cardTimer.current = setTimeout(() => setCard(next), next ? CARD_MS.open : CARD_MS.hide);
  };
  // Cards are placed in the pad window's own box, which both layouts (the tab scroller and split panes) share.
  const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement) => {
    const scroller = rootRef.current;
    if (!scroller) return null;
    const box = mark.getBoundingClientRect();
    const frame = scroller.getBoundingClientRect();
    const below = box.bottom - frame.top + 6;
    const above = below + 180 > frame.height;
    return { padId, blockId, kind, top: above ? box.top - frame.top - 6 : below, left: Math.max(6, Math.min(box.left - frame.left, frame.width - 336)), above };
  };
  useHubListener<KeyboardEvent>("window", "keydown", (event) => {
    if (event.key === "Escape") setCard(null);
  }, { enabled: card !== null });

  // A proposal's card that opened and closed with nothing chosen is labelled `ignored` (a weak "not now").
  const shownProposal = useRef<{ proposal: PadProposalDto; labelled: boolean } | null>(null);
  useEffect(() => {
    const open = card ? (proposals[card.padId] ?? []).find((each) => each.blockId === card.blockId && each.shown) ?? null : null;
    const was = shownProposal.current;
    if (was && was.proposal.proposalId !== open?.proposalId) {
      if (!was.labelled) void host.api.proposalLabel({ labelId: host.mintId("lbl"), proposalId: was.proposal.proposalId, label: "ignored" }).catch(() => undefined);
      shownProposal.current = null;
    }
    if (open && card?.kind === "proposal" && !shownProposal.current) shownProposal.current = { proposal: open, labelled: false };
  }, [card, host, proposals]);

  // "Not this" and "dismiss" are labels (wrong, and not now); the marker goes either way.
  const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored") => {
    if (shownProposal.current?.proposal.proposalId === proposal.proposalId) shownProposal.current.labelled = true;
    void host.api.proposalLabel({ labelId: host.mintId("lbl"), proposalId: proposal.proposalId, label }).catch(() => undefined);
    if (label !== "not_this" && label !== "dismiss") return;
    setProposals((now) => Object.fromEntries(Object.entries(now).map(([padId, list]) => [padId, list.map((each) => (each.proposalId === proposal.proposalId ? { ...each, shown: false } : each))])));
  };

  // -- the handle the desks' keys use ----------------------------------------------------------------
  const lastPad = padIds.length - 1;
  const impl = useRef<PadStackHandle | null>(null);
  impl.current = ({
    nextPad(direction) {
      if (split) {
        setPaneFocus((now) => (now + direction + split.pads.length) % split.pads.length);
        return;
      }
      scrollToPad(Math.max(0, Math.min(lastPad, active + direction)));
    },
    padOrDesk(direction) {
      if (split) {
        const next = paneFocus + direction;
        if (next < 0 || next >= split.pads.length) return false;
        setPaneFocus(next);
        return true;
      }
      const next = active + direction;
      if (next < 0 || next > lastPad) return false;
      scrollToPad(next);
      return true;
    },
    newPad(title) {
      const padId = host.mintId("pad");
      // In pen mode a new pad is a handwritten one (spec §10.10, "Freewrite pads").
      const byHand = Boolean(pen?.on);
      const name = byHand ? "Pad · ✎ by hand" : `Pad · ${title ? `“${title.slice(0, 40)}”` : "new notes"}`;
      if (!write(padId, [{ op: "create_pad", kind: byHand ? "ink" : "named", title: name, homeDeskId: host.deskId }])) return;
      host.addToStack(windowId, padId);
      setTimeout(() => scrollToPad(padIds.length), 50);
    },
    sketchBlock() {
      const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active];
      const state = padId ? store.pads[padId] : null;
      if (!state) return;
      insertAfter(padId, state.blocks[state.blocks.length - 1]?.blockId ?? null, { kind: "sketch", provenance: "learner", payload: { width: 480, height: 160, items: [] } });
    },
    arrange() {
      setArranging(true);
    },
    menuAtHover() {
      const at = hovered.current;
      if (!at) return false;
      menuOpening.current++;
      setMenu({ padId: at.padId, blockId: at.blockId, text: at.text, x: at.x, y: at.y });
      return true;
    },
    showPad(padId) {
      const index = padIds.indexOf(padId);
      if (index >= 0) scrollToPad(index);
    },
    openFrameMenu(request) {
      // A right-click inside a notebook frame (spec §11.3), labelled for the notebook's owner; its text is the
      // frame's selection (untrusted notebook text, shown only quoted).
      const padId = request.lessonId ? lessons?.desk.additionsFor(request.lessonId) ?? `lesson:${request.lessonId}` : request.padId ?? "";
      menuOpening.current++;
      setMenu({ padId, blockId: null, text: request.text, x: request.x, y: request.y, label: request.label, insertLabel: request.insertLabel, lessonId: request.lessonId });
    },
    openMenu(padId, blockId, at, selection, blockIds) {
      // The desks' one right-click listener hands a pad line's menu to its window (the rows are the pad's).
      const block = blockId ? store.pads[padId]?.blocks.find((each) => each.blockId === blockId) : undefined;
      menuOpening.current++;
      setMenu({ padId, blockId, blockIds, text: selection || (block ? firstLine(block.bodyMd) : ""), x: at.x, y: at.y });
    },
  });
  // The desks' keys reach this stack through a stable handle that always calls the latest render's.
  const proxy = useMemo<PadStackHandle>(() => ({
    nextPad: (d) => impl.current?.nextPad(d),
    padOrDesk: (d) => impl.current?.padOrDesk(d) ?? false,
    newPad: (t) => impl.current?.newPad(t),
    sketchBlock: () => impl.current?.sketchBlock(),
    arrange: () => impl.current?.arrange(),
    menuAtHover: () => impl.current?.menuAtHover() ?? false,
    openMenu: (padId, blockId, at, selection, blockIds) => impl.current?.openMenu(padId, blockId, at, selection, blockIds),
    openFrameMenu: (request) => impl.current?.openFrameMenu(request),
    showPad: (padId) => impl.current?.showPad(padId),
  }), []);
  useImperativeHandle(ref, () => proxy, [proxy]);
  useEffect(() => {
    host.register(windowId, proxy);
    return () => host.register(windowId, null);
  }, [host, windowId, proxy]);

  // Figures Show me finished are written while the window is live; paused, they wait for its return.
  const figureVersion = useSyncExternalStore(host.figures.subscribe, host.figures.getVersion);
  useEffect(() => {
    if (paused) return;
    for (const figure of host.figures.take(windowId)) {
      if (!store.pads[figure.padId]) continue;
      insertAfter(figure.padId, figure.afterBlockId, { kind: "figure", provenance: "learnloop", bodyMd: figure.line, payload: { figure_id: figure.figureId, parent_block_id: figure.afterBlockId, source_block_ids: figure.blockIds } });
    }
    // insertAfter reads the store as it is now.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paused, figureVersion, windowId]);

  // A passage's ✎ link scrolls the pad to its block and flashes it.
  useHubListener<CustomEvent<{ blockId: string }>>("window", "learnloop:pad-flash", (event) => {
    const element = blockEls.current.get(event.detail.blockId);
    if (!element) return;
    const blockId = event.detail.blockId;
    element.scrollIntoView?.({ block: "center", behavior: "smooth" });
    setFlash(blockId);
    setTimeout(() => setFlash((now) => (now === blockId ? null : now)), FLASH_MS);
  });

  // -- rendering -------------------------------------------------------------------------------------
  const renderBlock = (state: PadState, block: PadBlockDto): ReactNode => {
    const padId = state.pad.padId;
    const isEditing = editing?.blockId === block.blockId;
    const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each) => each.blockId === block.blockId && each.shown && each.current) ?? null;
    const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch" && block.kind !== "cell";
    const submission = block.submissions.find((each) => each.current) ?? block.submissions[0] ?? null;
    let gutter: ReactNode = null;
    let body: ReactNode;
    const markEnter = (kind: Card["kind"]) => (event: React.MouseEvent<HTMLElement>) => scheduleCard(cardFor(padId, block.blockId, kind, event.currentTarget));
    const markLeave = () => scheduleCard(null);
    const markTap = (kind: Card["kind"]) => (event: React.MouseEvent<HTMLElement>) => {
      event.stopPropagation();
      // The mark is read now: the event's currentTarget is gone by the time the state updater runs.
      const markEl = event.currentTarget;
      const next = cardFor(padId, block.blockId, kind, markEl);
      if (cardTimer.current) clearTimeout(cardTimer.current);
      setCard((now) => (now?.blockId === block.blockId && now.kind === kind ? null : next));
    };
    const mark = (kind: Card["kind"], glyph: string, className: string) => (
      <button type="button" className={`mark ${className}`} data-mark={kind} aria-label={{ source: "Show source details", tutor: "Show reply details", figure: "Show diagram details", proposal: "Show suggestion" }[kind]} title={{ source: "Show source details", tutor: "Show reply details", figure: "Show diagram details", proposal: "Show suggestion" }[kind]} onMouseEnter={markEnter(kind)} onMouseLeave={markLeave} onClick={markTap(kind)}>{glyph}</button>
    );
    switch (block.kind) {
      case "source_quote":
      case "source_piece": {
        const link = backLink(block, state.anchors);
        gutter = mark("source", "§", "src");
        body = (
          <div className={`quote${block.kind === "source_piece" ? " piece" : ""}`}>
            <FitMath><MarkdownMath value={`“${block.bodyMd}”`} /></FitMath>
            {link.extractionId ? <button type="button" className="back" title="Open source" onClick={() => host.openPassage(link.extractionId as string, link.spanId, link.t, link.sourceId)}>{link.label}</button> : null}
          </div>
        );
        break;
      }
      case "tutor_quote":
        gutter = mark("tutor", "◇", "ll");
        body = (
          <div className="tutorq">
            <span className="who">◇ the tutor{typeof (block.payload as Record<string, unknown>).asked_on === "string" ? `, on your question of ${shortDate((block.payload as Record<string, string>).asked_on)}` : ""}</span>
            <FitMath><MarkdownMath value={block.bodyMd} /></FitMath>
          </div>
        );
        break;
      case "figure":
        gutter = mark("figure", "◇ fig", "ll fig");
        body = <FitMath className="figline"><MarkdownMath value={block.bodyMd} /></FitMath>;
        break;
      case "sketch":
        gutter = <span className="mark pen" title="Sketch">✎</span>;
        body = (
          <SketchCanvas
            payload={block.payload as Record<string, unknown>}
            editable={!paused}
            onCommit={(payload) => write(padId, [{ op: "edit_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver"), payload: payload as unknown as Record<string, unknown> }])}
          />
        );
        break;
      case "ink":
        gutter = <span className="mark pen prov" title="Handwriting">✎</span>;
        body = <InkBlock padId={padId} block={block} windowId={windowId} paused={paused} showTranscription={!inkView[padId]?.hidden} write={(ops) => write(padId, ops)} fixRequest={fixRequests[block.blockId]} />;
        break;
      case "cell":
        // A marimo cell edits its own code and runs in the pad's notebook (screens/desks/notebook).
        gutter = <span className="mark ll" title="Python cell">◆</span>;
        body = (
          <PadCell
            padId={padId}
            block={block}
            blocks={state.blocks}
            editable={!paused}
            onCommit={(code) => write(padId, [{ op: "edit_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver"), bodyMd: code }])}
          />
        );
        break;
      case "lifted": {
        const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "");
        const title = store.pads[to] ? padName(store.pads[to]?.pad) : "its own pad";
        body = <div className="lifted">→ Moved to <b>{title}</b> · new pad in this stack</div>;
        gutter = <span className="mark" title={`Moved to ${title}`}>→</span>;
        break;
      }
      case "check_cell":
        gutter = mark("tutor", "◇", "ll");
        body = (
          <div className="check">
            <div className="prompt"><FitMath><MarkdownMath value={String((block.payload as Record<string, unknown>).prompt_md ?? "a check")} /></FitMath></div>
            <div className="answer">{isEditing ? null : block.bodyMd ? <FitMath><MarkdownMath value={block.bodyMd} /></FitMath> : <span className="hint">your answer…</span>}</div>
          </div>
        );
        break;
      default:
        body = isEditing ? null : <FitMath><MarkdownMath value={block.bodyMd || " "} /></FitMath>;
    }
    if (isEditing && editing) {
      body = (
        <div className="editor" data-pad-editor="" data-desk-typing="" tabIndex={-1} ref={editorRef}>
          <LiveMarkdownEditor
            value={editing.draft}
            compact
            focusable
            focusSignal={editing.focus}
            ariaLabel="edit this block"
            onChange={(next) => setEditing((now) => (now ? { ...now, draft: next } : now))}
            onKeyDown={onEditorKey}
            onBlur={() => {
              commitEdit();
              setEditing(null);
            }}
          />
          <div className="hintline">markdown · $math$ · ↵ new line · esc puts it back</div>
        </div>
      );
    }
    if (proposal && !gutter) gutter = mark("proposal", "◇", "ll proposal");
    const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?");
    return (
      <div
        key={block.blockId}
        ref={(node) => {
          if (node) blockEls.current.set(block.blockId, node);
          else blockEls.current.delete(block.blockId);
        }}
        className={`pb k-${block.kind}${editable ? " editable" : ""}${isEditing ? " editing" : ""}${flash === block.blockId ? " flash" : ""}${block.kind === "source_quote" || block.kind === "source_piece" ? " srcrow" : ""}`}
        data-block={block.blockId}
        data-emits={isLearnersWords(block) ? "yes" : "no"}
        title={isLearnersWords(block) || isEditing ? undefined : block.kind === "sketch" ? "Drawing" : block.provenance === "source" ? "From a source" : block.provenance === "tutor" || block.provenance === "learnloop" ? "From LearnLoop" : undefined}
        onMouseEnter={(event) => {
          hovered.current = { padId, blockId: block.blockId, text: firstLine(block.bodyMd), x: event.clientX, y: event.clientY };
        }}
        onMouseLeave={() => {
          // `.` opens the menu on the line under the pointer, never on one it has left.
          if (hovered.current?.blockId === block.blockId) hovered.current = null;
        }}
        onClick={(event) => {
          // A click inside the editor (moving the caret) is the editor's, not a request to open the block.
          if ((event.target as Element).closest("button, a, svg, textarea, .desk-sketch, .desk-ink, [data-pad-editor]")) return;
          openEditor(padId, block);
        }}
      >
        <div className="gut">{gutter}{proposal && gutter && block.kind !== "text" ? null : null}</div>
        <div className="bx">
          {body}
          {(block.payload as { conflict?: { label?: string } }).conflict ? <span className="conflict" data-conflict="">⇄ {(block.payload as { conflict: { label?: string } }).conflict.label || "written over an older version"}</span> : null}
          {submission ? <span className="submitted">{submission.current ? `submitted · ${submission.as === "teach_back" ? "teach-back" : `attempt, ${shortDate(submission.createdAt)}`}` : "submitted (an earlier version)"}</span> : null}
          {question && !isEditing ? <button type="button" className="carry" onClick={() => host.carry(block.bodyMd.trim(), { kind: "block", ref: block.blockId })}>? save for later</button> : null}
        </div>
        {state.pad.kind === "running" && block.kind !== "lifted" && !isEditing ? (
          <button type="button" className="lift" onClick={(event) => {
            event.stopPropagation();
            const newPadId = host.mintId("pad");
            const newBlockId = host.mintId("blk");
            const title = firstLine(block.bodyMd).slice(0, 48) || "lifted";
            if (write(padId, [{ op: "lift_out", blockId: block.blockId, expectedHead: block.headVersionId, newPadId, newBlockId, title, newVersionId: host.mintId("ver"), stubVersionId: host.mintId("ver"), positionKey: "m" }])) {
              if (block.kind === "ink") pen?.ink.lifted(padId, block.blockId, newPadId, newBlockId);
              host.addToStack(windowId, newPadId);
            }
          }}>lift out</button>
        ) : null}
      </div>
    );
  };

  // A lesson's own notes: its additions pad's blocks (every pad insert and edit, as on any pad), and a line to write
  // under it; the first write creates the pad (kind lesson_additions, naming the lesson) through the pad ops. The
  // pad menu opened inside a notebook lesson ("add under this lesson") inserts its block here too.
  const writeUnderLesson = (lessonId: string, block: Parameters<typeof insertAfter>[2] = { kind: "text", provenance: "learner" }) => {
    if (!lessons) return;
    let padId = lessons.desk.additionsFor(lessonId);
    if (padId && !store.pads[padId]) return; // still being read
    if (!padId && !lessons.desk.additionsKnown(lessonId)) {
      // Whether the lesson has notes already is not known yet (its summary still on its way, or its read failed):
      // read it, and create nothing that could split its notes in two.
      lessons.desk.refresh(lessonId);
      host.toast("reading your notes under this lesson · write again in a moment");
      return;
    }
    if (!padId) {
      padId = host.mintId("pad");
      // A lesson held for a due check names no topic: the pad's title is stored, and outlives the check.
      const summary = lessons.desk.summary(lessonId);
      const topic = summary?.held ? null : summary?.title;
      if (!write(padId, [{ op: "create_pad", kind: "lesson_additions", title: `your additions${topic ? ` · ${topic}` : ""}`, lessonId }])) return;
      lessons.desk.noteAdditions(lessonId, padId);
    }
    const state = store.pads[padId];
    insertAfter(padId, state?.blocks[state.blocks.length - 1]?.blockId ?? null, block, block.kind === "text");
  };

  const renderLesson = (key: string, index: number, minHeight: number): ReactNode => {
    const lessonId = lessonOfKey(key);
    const entry = lessons?.desk.entryFor(key) ?? null;
    const additionsId = lessonId ? lessons?.desk.additionsFor(lessonId) ?? null : null;
    const additions = additionsId ? store.pads[additionsId] ?? null : null;
    return (
      <div className={`paper k-lesson${index === active ? " open" : ""}`} ref={(node) => setRef(paperEls.current, key, node)} style={{ minHeight }} data-pad={key}>
        {lessons && entry ? (
          <LessonPaper
            host={lessons}
            itemKey={key}
            lessonId={lessonId}
            entry={entry}
            hasAdditions={Boolean(additions?.blocks.length)}
            additions={(
              <>
                {additions ? additions.blocks.map((block) => renderBlock(additions, block)) : null}
                {(lessonId ? lessons?.desk.olderAdditions(lessonId) ?? [] : []).map((older) => store.pads[older])
                  .map((pad) => (pad ? pad.blocks.map((block) => renderBlock(pad, block)) : null))}
                {lessonId ? (
                  <div className="pb jot" onClick={() => writeUnderLesson(lessonId)}>
                    <div className="gut" />
                    <div className="bx wline">write under this lesson</div>
                  </div>
                ) : null}
              </>
            )}
          />
        ) : <div className="lnone">Open the lesson from Path.</div>}
      </div>
    );
  };

  const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode => {
    if (isLessonItem(padId)) return renderLesson(padId, index, minHeight);
    if (!state) {
      const failure = store.padFailure(padId);
      return <div className="paper" ref={(node) => setRef(paperEls.current, padId, node)} style={{ minHeight }}>{failure ? "Couldn’t open this pad. Close and reopen it from the window list." : "◐ reading the pad…"}</div>;
    }
    const days: Array<{ day: string | null; blocks: PadBlockDto[] }> = [];
    for (const block of state.blocks) {
      const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null;
      const last = days[days.length - 1];
      if (last && last.day === day) last.blocks.push(block);
      else days.push({ day, blocks: [block] });
    }
    const byHand = state.pad.kind === "ink";
    const look = inkView[padId] ?? {};
    const newLine = () => insertAfter(padId, state.blocks[state.blocks.length - 1]?.blockId ?? null, { kind: "ink", provenance: "ink_transcription" });
    return (
      <div
        className={`paper k-${state.pad.kind}${byHand ? " handpad" : ""}${byHand && look.dotted ? " dotted" : ""}${index === active ? " open" : ""}`}
        ref={(node) => setRef(paperEls.current, padId, node)}
        style={{ minHeight }}
        data-pad={padId}
      >
        {byHand ? (
          <div className="handbar" data-ink-bar="">
            <span>✎ by hand</span>
            <button type="button" aria-pressed={Boolean(look.dotted)} onClick={() => setInkView((now) => ({ ...now, [padId]: { ...look, dotted: !look.dotted } }))}>{look.dotted ? "lined" : "dotted"}</button>
            <button type="button" aria-pressed={!look.hidden} onClick={() => setInkView((now) => ({ ...now, [padId]: { ...look, hidden: !look.hidden } }))}>{look.hidden ? "show" : "hide"} transcription</button>
          </div>
        ) : null}
        {state.pad.kind === "problem" && state.pad.workbenchSessionId && host.problems ? (
          // An RW2 problem's workbench, hosted here (spec §15.2); the pad's own blocks follow it.
          <ProblemPad sessionId={state.pad.workbenchSessionId} host={host.problems} ink={problemInk(state, padId)} />
        ) : null}
        {days.map((group, groupIndex) => (
          <div key={`${group.day ?? "all"}:${groupIndex}`}>
            {group.day ? <div className="day">{dayHeading(group.day, today)}</div> : null}
            {group.blocks
              // A problem's ink lines with text are its steps, shown in its workbench; a line not read yet stays here.
              .filter((block) => !(block.kind === "ink" && block.bodyMd.trim() && hostsProblem(state)))
              .map((block) => renderBlock(state, block))}
          </div>
        ))}
        <div className={`pb jot${byHand || pen?.on ? " inkjot" : ""}`} onClick={() => insertAfter(padId, state.blocks[state.blocks.length - 1]?.blockId ?? null, { kind: "text", provenance: "learner" }, true)}>
          <div className="gut" />
          {byHand || pen?.on ? (
            // The pen writes a new ink line here; a click still starts a typed line.
            <div className="bx">
              <InkJot padId={padId} windowId={windowId} paused={paused} newLine={newLine}
                hint={byHand ? "▍ Write with the pen. Starting a new line can begin handwriting conversion." : state.pad.kind === "running" ? "jot · it lands here by default · or write with the pen" : "write here · or with the pen"} />
            </div>
          ) : (
            <div className="bx wline">{state.pad.kind === "running" ? "jot · it lands here by default" : "write here"}</div>
          )}
        </div>
      </div>
    );
  };

  const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode => {
    if (isLessonItem(padId)) {
      // "Teacher lesson · <topic>" and "made <date> from your <what>" (spec §11.1).
      const lessonId = lessonOfKey(padId);
      const summary = lessonId ? lessons?.desk.summary(lessonId) ?? null : null;
      return (
        <button
          key={`tab-${padId}`}
          type="button"
          ref={(node) => setRef(tabEls.current, padId, node)}
          className={`ptab lesson${index === active ? " open" : ""}`}
          data-pad-tab={padId}
          style={{ top: index * 30, bottom: (padIds.length - 1 - index) * 30 }}
          onClick={() => scrollToPad(index)}
        >
          <span className="sheet">
            <span className="tt">{lessonTabTitle(lessonId ? summary?.title : lessons?.desk.openingTitle(padId))}</span>
            <span className="tl" />
            <span className="tm">{lessonId ? lessonTabMeta(summary) : "opening…"}</span>
          </span>
          <span className="fl l" />
          <span className="fl r" />
        </button>
      );
    }
    const title = padName(state?.pad);
    const first = state ? plainLine(state.blocks.find((block) => block.bodyMd)?.bodyMd ?? "") : "";
    return (
      <button
        key={`tab-${padId}`}
        type="button"
        ref={(node) => setRef(tabEls.current, padId, node)}
        className={`ptab${index === active ? " open" : ""}`}
        data-pad-tab={padId}
        style={{ top: index * 30, bottom: (padIds.length - 1 - index) * 30 }}
        onClick={() => scrollToPad(index)}
      >
        <span className="sheet">
          {state?.pad.kept ? <span className="kept" title="Pinned">⚲</span> : null}
          <span className="tt">{title}</span>
          <span className="tl">{first}</span>
          <span className="tm">{state ? tabMeta(state, today) : ""}</span>
        </span>
        <span className="fl l" />
        <span className="fl r" />
      </button>
    );
  };

  const minHeight = paperMinHeight(viewport, padIds.length);
  const learnerWords = pads.some((state) => state?.blocks.some(isLearnersWords));
  const cardBlock = card ? store.pads[card.padId]?.blocks.find((block) => block.blockId === card.blockId) ?? null : null;
  const cardProposal = card ? (proposals[card.padId] ?? []).find((each) => each.blockId === card.blockId && each.shown) ?? null : null;

  return (
    <div className="desk-pads" data-pad-stack={windowId} ref={rootRef}>
      {infoProp === undefined ? <div className="pbar"><button type="button" className="pinfo" aria-label="where your words go" aria-expanded={info} onClick={() => setInfo((now) => !now)}><span className="ic">ⓘ</span>yours</button></div> : null}
      {info ? (
        <div className="pinfo-pop" role="dialog" aria-label="where your words go">
          <b>where your words go.</b> LearnLoop can use text you type or text converted from your handwriting in pads to suggest help. Quotes can help LearnLoop identify your own words. Your writing counts as an attempt or a teach-back when you submit it, as shown by <span className="submitted">submitted</span>.
          {learnerWords ? null : <div className="none">These pads have no writing that counts as your own words yet.</div>}
        </div>
      ) : null}
      {split ? (
        <div className="split">
          {split.pads.map((padId, i) => {
            const state = store.pads[padId] ?? null;
            return (
              <div key={padId} className={`pane${i === paneFocus ? " focus" : ""}`} style={{ flex: `${split.ratios[i]} 1 0` }} onMouseDown={() => setPaneFocus(i)}>
                <div className="ptitle">{padName(state?.pad)}</div>
                <div className="pscroll">{renderPaper(state, padId, padIds.indexOf(padId), 0)}</div>
                {i < split.pads.length - 1 ? <Divider onDrag={(dy) => host.setView(windowId, { ...view, split: { pads: split.pads, ratios: moveDivider(split.ratios, i, dy) } })} /> : null}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="pscroller" ref={scrollerRef}>
          {padIds.map((padId, index) => (
            // An opened lesson keeps its opening's key, so the window that opened it is not remounted.
            <div key={lessons ? lessons.desk.reactKey(padId) : padId} style={{ display: "contents" }}>
              {tabLabel(pads[index], padId, index)}
              {renderPaper(pads[index], padId, index, minHeight)}
            </div>
          ))}
        </div>
      )}
      {card && cardBlock ? (
        <div className={`pcard${card.above ? " above" : ""}`} data-pad-card={card.kind} style={{ top: card.top, left: card.left }} onMouseEnter={() => scheduleCard(card)} onMouseLeave={() => scheduleCard(null)}>
          {card.kind === "source" ? (
            <>
              <div className="head">{backLink(cardBlock).label.replace(" ↩", "")} · the passage this quote came from</div>
              <FitMath><MarkdownMath value={cardBlock.bodyMd.slice(0, 320)} /></FitMath>
              {backLink(cardBlock).extractionId ? <button type="button" onClick={() => {
                const link = backLink(cardBlock, store.pads[card.padId]?.anchors ?? []);
                host.openPassage(link.extractionId as string, link.spanId, link.t, link.sourceId);
              }}>open it beside ↩</button> : null}
            </>
          ) : card.kind === "tutor" ? (
            <>
              <div className="head">◇ the tutor's words</div>
              <FitMath><MarkdownMath value={cardBlock.bodyMd} /></FitMath>
              <button type="button" onClick={() => host.askAbout(firstLine(cardBlock.bodyMd), padContext(card.padId, cardBlock, store.pads[card.padId]?.anchors))}>open the thread</button>
            </>
          ) : card.kind === "figure" ? (
            <>
              <div className="head">a figure LearnLoop made for this line · help, not a check</div>
              <FitMath><MarkdownMath value={cardBlock.bodyMd} /></FitMath>
              <button type="button" onClick={() => host.askAbout(firstLine(cardBlock.bodyMd), padContext(card.padId, cardBlock, store.pads[card.padId]?.anchors))}>open it in the companion</button>
            </>
          ) : cardProposal ? (
            <>
              <div className="head">◇ {cardProposal.reasonMd}</div>
              <FitMath><MarkdownMath value={`“${cardProposal.quote}”`} /></FitMath>
              <div className="acts">
                <button type="button" onClick={() => {
                  labelProposal(cardProposal, "opened");
                  const target = cardProposal.target as { content?: { extraction_id?: string; extractionId?: string; source_id?: string; sourceId?: string; t?: number }; target?: { span_id?: string; t?: number } };
                  const extractionId = target.content?.extraction_id ?? target.content?.extractionId;
                  if (extractionId) host.openPassage(extractionId, target.target?.span_id ?? null, target.target?.t ?? target.content?.t, target.content?.source_id ?? target.content?.sourceId ?? null);
                  setCard(null);
                }}>open beside</button>
                <button type="button" onClick={() => { labelProposal(cardProposal, "not_this"); setCard(null); }}>not this</button>
                <button type="button" onClick={() => { labelProposal(cardProposal, "dismiss"); setCard(null); }}>dismiss</button>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
      {menu ? (
        <PadMenu
          key={menuOpening.current}
          request={menu}
          host={host}
          windowId={windowId}
          state={store.pads[menu.padId] ?? null}
          muted={muted.includes(menu.padId)}
          onClose={() => setMenu(null)}
          onInsert={(block) => {
            // From a notebook frame: a lesson's inserts go under the lesson (its additions pad), a pad's at its end.
            if (menu.lessonId) writeUnderLesson(menu.lessonId, block);
            else if (menu.label) insertAfter(menu.padId, (store.pads[menu.padId]?.blocks.slice(-1)[0]?.blockId ?? null), block, block.kind === "text");
            else insertAfter(menu.padId, menu.blockId, block, block.kind === "text");
          }}
          onNote={() => menu.blockId && insertAfter(menu.padId, menu.blockId, { kind: "note", provenance: "learner", payload: { parent_block_id: menu.blockId } }, true)}
          onSubmit={() => menu.blockId && setSubmitting({ padId: menu.padId, blockId: menu.blockId })}
          onMute={() => host.setView(windowId, { ...view, mutedPads: muted.includes(menu.padId) ? muted.filter((id) => id !== menu.padId) : [...muted, menu.padId] })}
        />
      ) : null}
      {arranging ? (
        <ArrangeOverlay
          pads={padIds.filter((padId) => !isLessonItem(padId)).map((padId) => ({ padId, title: padName(store.pads[padId]?.pad), line: plainLine(store.pads[padId]?.blocks.find((block) => block.bodyMd)?.bodyMd ?? "") }))}
          split={split}
          onCancel={() => setArranging(false)}
          onConfirm={(shown) => {
            setArranging(false);
            host.setView(windowId, { ...view, split: shown.length >= 2 ? { pads: shown, ratios: shown.map(() => 1) } : null });
            setPaneFocus(0);
          }}
        />
      ) : null}
      {submitting ? (
        <SubmitSheet
          host={host}
          state={store.pads[submitting.padId] ?? null}
          blockId={submitting.blockId}
          onClose={() => setSubmitting(null)}
        />
      ) : null}
    </div>
  );
});

/** A pad block as the companion asks about it: the block, and the passage it links to (its first anchor). */
function padContext(padId: string, block: PadBlockDto, anchors: Array<{ blockId: string; extractionId: string; spanId: string }> = []) {
  const p = block.payload as Record<string, unknown>;
  const own = anchors.find((anchor) => anchor.blockId === block.blockId);
  const anchor = own ? { extractionId: own.extractionId, spanId: own.spanId }
    : typeof p.extraction_id === "string" && typeof p.span_id === "string" ? { extractionId: p.extraction_id, spanId: p.span_id } : null;
  return { padId, blockId: block.blockId, anchor };
}

function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null) {
  if (node) map.set(key, node);
  else map.delete(key);
}

/** The split mode stored in the window's view: 2–3 pads and their heights' ratios. */
export function readSplit(view: Record<string, unknown>, padIds: string[]): { pads: string[]; ratios: number[] } | null {
  const raw = view.split as { pads?: unknown; ratios?: unknown } | null | undefined;
  if (!raw || !Array.isArray(raw.pads)) return null;
  const pads = (raw.pads as unknown[]).filter((id): id is string => typeof id === "string" && padIds.includes(id));
  if (pads.length < 2) return null;
  const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r) => (Number.isFinite(r) && r > 0 ? r : 1)) : pads.map(() => 1);
  return { pads, ratios };
}

/** Dragging a divider: the panes above and below trade height, neither under 60 px (of a 600 px stack). */
export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[] {
  const sum = ratios.reduce((a, b) => a + b, 0);
  const px = ratios.map((r) => (r / sum) * total);
  const min = 60;
  const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy));
  px[index] += move;
  px[index + 1] -= move;
  return px.map((p) => p / total);
}

function Divider({ onDrag }: { onDrag: (dy: number) => void }) {
  const start = useRef<number | null>(null);
  return (
    <div
      className="divider"
      role="separator"
      onPointerDown={(event) => {
        start.current = event.clientY;
        event.currentTarget.setPointerCapture?.(event.pointerId);
      }}
      onPointerUp={(event) => {
        if (start.current !== null) onDrag(event.clientY - start.current);
        start.current = null;
      }}
    />
  );
}

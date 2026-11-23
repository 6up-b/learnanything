// The goal lens's one mount on the desks (spec §12): DeskShell hands it the desk's goal, the readings in windows
// that are not paused, the focused window's place and the pads' anchors, and places what it returns: the band
// under the top bar (or the "set a goal" chip in it), each source window's lens, a pad stack's goal line, and the
// overlays (the why card, the path view). The router's `p` toggles the path view; while it is open its keys are
// its own (a menu scope).
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { DeliverableSectionDto } from "../../../api/dto";
import type { ReaderLens } from "../../ReaderScreen";
import type { ListenerHub } from "../lifecycle";
import { WINDOW_ATTRIBUTE } from "../keys/listeners";
import type { Timers } from "../keys/router";
import { useGoalLens, type GoalTransport, type WhyState } from "./controller";
import { GoalBand, GoalTopChip, type HereView } from "./GoalBand";
import { readerLens, WhyCard, WHY_HIDE_MS, WHY_OPEN_MS, type MarkHandlers } from "./marks";
import { hereLine, markKind, type LensIndex } from "./model";
import { PathView, type NotNeeded } from "./PathView";

function readFlag(key: string | null): boolean {
  if (!key) return false;
  try {
    return window.localStorage.getItem(key) === "off";
  } catch {
    return false;
  }
}

function writeFlag(key: string | null, on: boolean): void {
  if (!key) return;
  try {
    if (on) window.localStorage.setItem(key, "off");
    else window.localStorage.removeItem(key);
  } catch {
    /* remembered per machine when storage allows */
  }
}

export interface GoalReading {
  windowId: string;
  extractionId: string;
  /** The window is hidden, out of view or a preview: it shows the lens it has and asks for nothing. */
  paused: boolean;
  book: string;
  /** A paper (its section heads take the light callout). */
  paper?: boolean;
}

export interface GoalPadAnchor {
  padId: string;
  extractionId: string;
  spanId: string;
}

export interface GoalDesk {
  /** The band (or null: no goal, or the curriculum off). */
  band: ReactNode;
  /** The top bar's "◎ set a goal", when the desk has no goal. */
  topChip: ReactNode;
  hasBand: boolean;
  lensFor: (windowId: string, extractionId: string) => ReaderLens | null;
  /** "◎ for your goal · …" over a pad stack, from its pads' anchors. */
  padLine: (padIds: readonly string[]) => ReactNode;
  overlays: ReactNode;
  pathOpen: boolean;
  togglePath: () => boolean;
}

export function useGoalDesk({ transport, deskGoalId, offKey, onSetGoal, readings, focused, padAnchors, hubFor, timers, mintId, onError, onOpen }: {
  transport: GoalTransport;
  deskGoalId: string | null | undefined;
  /** Where this desk's "no goal" is remembered on this machine (a desk with no stored goal shows the primary one). */
  offKey: string | null;
  onSetGoal: (goalId: string | null) => void;
  readings: readonly GoalReading[];
  focused: { windowId: string; extractionId: string | null; readingSpan: string | null; where: string | null } | null;
  padAnchors: readonly GoalPadAnchor[];
  hubFor: (windowId: string) => ListenerHub;
  timers: Timers;
  mintId: (prefix: string) => string;
  onError: (message: string) => void;
  /** Open a section beside on the goal's desk. */
  onOpen: (section: { extractionId: string; sourceId?: string; startSpanId: string | null }) => void;
}): GoalDesk {
  const asked = useMemo(() => [...new Set([
    ...readings.filter((reading) => !reading.paused).map((reading) => reading.extractionId),
    ...padAnchors.map((anchor) => anchor.extractionId),
  ])], [readings, padAnchors]);
  const [off, setOff] = useState(() => readFlag(offKey));
  useEffect(() => { setOff(readFlag(offKey)); }, [offKey]);
  const chooseGoal = useCallback((goalId: string | null) => {
    writeFlag(offKey, goalId === null);
    setOff(goalId === null);
    onSetGoal(goalId);
  }, [offKey, onSetGoal]);
  const goal = useGoalLens({ transport, deskGoalId, off, readings: asked, timers, mintId, onError });
  const { band, indexFor, dimOn, why, showWhy } = goal;

  // The why card: open after 120 ms of hover, hide 160 ms after leaving; a tap toggles; esc closes it.
  const pending = useRef<unknown>(null);
  const shownRef = useRef<WhyState | null>(null);
  shownRef.current = why;
  const handlers = useMemo<MarkHandlers>(() => ({
    hover: (next) => {
      if (pending.current !== null) timers.clear(pending.current);
      pending.current = timers.set(() => { pending.current = null; showWhy(next); }, next ? WHY_OPEN_MS : WHY_HIDE_MS);
    },
    tap: (next) => {
      if (pending.current !== null) timers.clear(pending.current);
      pending.current = null;
      const now = shownRef.current;
      showWhy(now && now.section.sectionId === next.section.sectionId && now.windowId === next.windowId ? null : next);
    },
  }), [timers, showWhy]);
  useEffect(() => {
    if (!why) return;
    return hubFor(why.windowId).listen<KeyboardEvent>("window", "keydown", (event) => {
      if (event.key === "Escape") showWhy(null);
    }, true);
  }, [why, hubFor, showWhy]);

  const lenses = useMemo(() => {
    const out = new Map<string, ReaderLens | null>();
    for (const reading of readings) {
      out.set(reading.windowId, band && band.status !== "not_a_deliverable"
        ? readerLens({ index: indexFor(reading.extractionId), dimOn, windowId: reading.windowId, handlers, paper: reading.paper,
          openSection: why && why.windowId === reading.windowId ? why.section.sectionId : null })
        : null);
    }
    return out;
  }, [readings, band, indexFor, dimOn, handlers, why]);
  const lensFor = useCallback((windowId: string) => lenses.get(windowId) ?? null, [lenses]);

  // "You are reading": the passage at the top of the focused window (80 px in, as the reference reads it),
  // read again as it scrolls; the Reader's own reading span when it has one.
  const [topSpan, setTopSpan] = useState<string | null>(null);
  const focusedWindowId = focused?.windowId ?? null;
  const focusedReading = focused?.extractionId ?? null;
  useEffect(() => {
    setTopSpan(null);
    if (!focusedWindowId || !focusedReading) return;
    let frame = 0;
    const read = () => {
      frame = 0;
      const host = document.querySelector(`[${WINDOW_ATTRIBUTE}="${focusedWindowId}"]`);
      if (!host) return;
      const line = host.getBoundingClientRect().top + 80;
      const passages = [...host.querySelectorAll<HTMLElement>("[data-span-id]")];
      const at = passages.find((element) => element.getBoundingClientRect().bottom > line) ?? passages[0];
      const span = at?.getAttribute("data-span-id") ?? null;
      setTopSpan((now) => (now === span ? now : span));
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(read); };
    const remove = hubFor(focusedWindowId).listen("document", "scroll", schedule, true);
    // The Reader renders its passages after the window mounts: look again once they are there.
    const handle = timers.set(schedule, 600);
    schedule();
    return () => { remove(); timers.clear(handle); if (frame) cancelAnimationFrame(frame); };
  }, [focusedWindowId, focusedReading, hubFor, timers, indexFor]);

  const focusedIndex: LensIndex | null = focused?.extractionId ? indexFor(focused.extractionId) : null;
  const here: HereView | null = focused
    ? (focused.extractionId ? hereLine(focusedIndex, topSpan ?? focused.readingSpan, topSpan ? null : focused.where, band)
      : { where: focused.where ?? "your scratchpads", lo: null, tag: null, loId: null })
    : null;

  const togglePath = useCallback(() => {
    if (!band) return false;
    goal.setPathOpen(!goal.pathOpen);
    return true;
  }, [band, goal]);

  const openLo = useCallback((learningObjectId: string) => {
    const dot = band?.learningObjects?.find((each) => each.learningObjectId === learningObjectId);
    if (dot?.primary) onOpen({ extractionId: dot.primary.extractionId, startSpanId: dot.primary.startSpanId });
  }, [band, onOpen]);

  const onNext = useCallback(() => {
    const next = band?.next;
    if (!next) return;
    if (next.kind === "section") onOpen({ extractionId: next.section.extractionId, startSpanId: next.section.startSpanId });
    if (next.kind === "checks") {
      const host = (next.check?.host ?? null) as { extractionId?: string; spanId?: string | null } | null;
      if (host?.extractionId) onOpen({ extractionId: host.extractionId, startSpanId: host.spanId ?? null });
    }
  }, [band, onOpen]);

  const notNeeded = useMemo<NotNeeded[]>(() => {
    const out: NotNeeded[] = [];
    const seen = new Set<string>();
    for (const reading of readings) {
      if (seen.has(reading.extractionId)) continue;
      seen.add(reading.extractionId);
      for (const section of indexFor(reading.extractionId)?.sections ?? []) {
        if (section.level === "skippable" || section.level === "later") out.push({ extractionId: reading.extractionId, book: reading.book, section });
      }
    }
    return out;
  }, [readings, indexFor]);

  const padLine = useCallback((padIds: readonly string[]) => {
    if (!band || band.status === "not_a_deliverable") return null;
    const wanted = new Set(padIds);
    const rank = ["core", "supporting", "later", "already_shown", "partial", "skippable", "unmapped"];
    let best: { section: NonNullable<ReturnType<LensIndex["bySpan"]["get"]>> } | null = null;
    for (const anchor of padAnchors) {
      if (!wanted.has(anchor.padId)) continue;
      const section = indexFor(anchor.extractionId)?.bySpan.get(anchor.spanId);
      if (section && (!best || rank.indexOf(section.level) < rank.indexOf(best.section.level))) best = { section };
    }
    if (!best) return null;
    const { section } = best;
    const lo = section.learningObjects.find((entry) => entry.learningObjectId === section.determiningLoId);
    const kind = markKind(section.level);
    const text = section.held ? "a cold check is due on what these pads link to"
      : section.level === "skippable" ? `not needed for your goal · ${section.reasonMd}`
      : lo?.title ? `${lo.kind === "prerequisite" ? "a prerequisite" : lo.kind === "later" ? "later" : "a goal LO"}: “${lo.title}” · ${section.reasonMd}`
      : section.reasonMd;
    return (
      <div className={`gfor g-${kind ?? "none"}`} data-goal-padline="">
        <span className="gg">◎</span> {section.level === "skippable" ? "" : "for your goal · "}{text}
      </div>
    );
  }, [band, padAnchors, indexFor]);

  const hasBand = Boolean(band);
  const bandNode = band ? (
    <GoalBand
      band={band}
      goals={goal.goals}
      here={here}
      dimOn={dimOn}
      onToggleDim={goal.toggleDim}
      onPath={() => goal.setPathOpen(!goal.pathOpen)}
      onDepth={goal.setDepth}
      onOpenLo={openLo}
      onNext={onNext}
      onChooseGoal={chooseGoal}
      onMapIt={goal.mapIt}
    />
  ) : null;
  const topChip = !goal.goalId && goal.goals !== null ? <GoalTopChip goals={goal.goals} onChooseGoal={chooseGoal} /> : null;
  const overlays = (
    <>
      {why ? <WhyCard key={`${why.windowId}:${why.section.sectionId}`} why={why} band={band} /> : null}
      {goal.pathOpen && band ? (
        <PathView
          band={band}
          here={here?.loId ?? null}
          notNeeded={notNeeded}
          onClose={() => goal.setPathOpen(false)}
          onDepth={goal.setDepth}
          onOpen={(section) => { goal.setPathOpen(false); onOpen(section); }}
          onUseInstead={(learningObjectId: string, section: DeliverableSectionDto) => goal.override(learningObjectId, "use_instead", `${section.extractionId}/${section.sectionId}`)}
          onReadAnyway={goal.readAnyway}
          onAddPhrase={goal.addPhrase}
        />
      ) : null}
    </>
  );
  return { band: bandNode, topChip, hasBand, lensFor, padLine, overlays, pathOpen: goal.pathOpen, togglePath };
}

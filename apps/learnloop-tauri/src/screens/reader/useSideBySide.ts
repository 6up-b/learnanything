// Reader CA6: side by side and follow along (ux_reader_compare_ask_v1 §6.4,
// X9, K14, C5).
//
// Two books in two panes. The second pane reads one section of the other book
// at a time (reader.side_by_side_section: protection read now, each block
// shown recorded as exposure). It is a variant of the comparing posture, so
// opening it pushes a crumb (`↩ Strang §6.1 › side by side with Axler §5.A`);
// walking the return stack off that crumb closes it, and onto it again
// reopens it.
//
// Follow along (on by default, §15 Q14; one toggle turns it off for the
// session):
// * the leading pane is the one the learner last scrolled, clicked or
//   selected in; the other follows;
// * the following pane moves only when the leading pane crosses into a new
//   section, once, to the first of its book's judged correspondents for that
//   section in the API's order (an unchecked search hit never moves a pane),
//   at its jump locator, with no animation;
// * mid-section the leader moves nothing, and the last-touched pane is never
//   moved (a late answer for a crossing the learner has since overtaken, or
//   for a pane the learner has since touched, is dropped);
// * with no correspondent in the follower's book, the follower stays put and
//   says so (dim) until the learner moves it.
//
// Records (salience only, each with the visit and the session's id):
// side_by_side_opened (corresponding_section_peeked for the narrow window's
// peek), side_by_side_closed (how long it was open, and how it ended),
// follow_along_moved, and follow_along_undone (the learner took the moved
// pane back to where it was: the pairing was wrong). No model call.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { CorrespondentsDto, SideBySideSectionDto } from "../../api/dto";
import { errorMessage } from "../../errors";
import { logReaderAction, newActivityId } from "./activity";
import { crumbLabel, firstCorrespondent, firstJudgedIn, isNarrowWindow, targetOf, type Pane, type PaneTarget } from "./sideBySide";

export const SIDE_BY_SIDE_COPY = {
  narrow: "side by side needs a wider window",
  staysPut: "no matching section here · stays put",
  unchecked: "found by search, not checked",
  nothing: "nothing in your other books matches this section yet",
  loading: "◐",
  failed: "Couldn't open this section just now.",
  followOn: "follow along ●",
  followOff: "follow along ○",
  followKey: "(^⇧L)",
  close: "close side by side",
  lead: "lead",
  previous: "‹",
  next: "›",
  keys: "F6 other pane · ^⇧L follow along · ^\\ close side by side · \\ rail",
} as const;

/** Keys that scroll a pane: pressed in a pane, the learner's hand is on it (it leads). */
export const SIDE_BY_SIDE_SCROLL_KEYS: ReadonlySet<string> = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "]);

/** The book open in the main pane, and the section in view there. */
export interface MainPane {
  sourceId: string;
  sourceTitle: string;
  extractionId: string;
  sectionId: string | null;
}

/** The return stack's current entry, as side by side reads it (a ReturnEntry fits). */
export interface CurrentEntry {
  id: string;
  kind: string;
  /** The main pane's book when the entry was pushed. */
  sourceId: string;
  /** A side_by_side entry's second pane. */
  sideBySide?: PaneTarget | null;
}

export interface SideBySideInput {
  /** The prompt contract's `sideBySide` (and not offline, not working). */
  enabled: boolean;
  main: MainPane | null;
  /** Moves the main pane to a passage (follow along; never a detour). */
  jumpMain: (spanId: string) => void;
  /** Pushes the crumb, carrying the second pane; returns its return-stack entry id (null: no return stack). */
  pushCrumb: (label: string, target: PaneTarget) => string | null;
  /** Another section opened beside the same passage: the current crumb names it (false: not the current entry). */
  replaceCrumb?: (entryId: string, label: string, target: PaneTarget) => boolean;
  /** Takes the crumb off again when the learner closes side by side. */
  dropCrumb: (entryId: string) => void;
  /** The return stack's current entry (walking off the crumb closes side by side, onto one reopens it). */
  currentEntry: CurrentEntry | null;
  /** The visit's identity for the records. */
  visitPayload?: () => Record<string, unknown>;
  onError: (message: string) => void;
}

export type SideBySideVia = "find_list" | "peek" | "key";
/** How a side-by-side session ended (side_by_side_closed's `via`). */
type EndedBy = "close" | "walked_off" | "replaced" | "source" | "switch_off";

interface Pair {
  target: PaneTarget;
  /** The crumb's entry (null: no return stack, or the narrow window's peek). */
  entryId: string | null;
  /** The narrow window's peek (a sheet; nothing follows). */
  sheet: boolean;
  /** The main pane's book this pair was opened beside. */
  mainSourceId: string;
  /** The session (side_by_side_opened … side_by_side_closed). */
  sessionId: string;
  openedAt: number;
}

/** The last follow-along move, so the learner taking that pane back is recorded. */
interface LastFollow {
  pane: Pane;
  fromSectionId: string;
  toSectionId: string;
  at: number;
  sessionId: string;
}

export interface SideBySide {
  enabled: boolean;
  narrow: boolean;
  /** Open as two panes. */
  panes: boolean;
  /** Open as the narrow window's peek sheet. */
  sheet: boolean;
  target: PaneTarget | null;
  section: SideBySideSectionDto | null;
  phase: "idle" | "loading" | "ready" | "failed";
  leader: Pane;
  follow: boolean;
  /** The pane that found no matching section and stays put (dim), or null. */
  staysPut: Pane | null;
  /** A dim line after Ctrl+\ found nothing to open. */
  notice: string | null;
  open: (target: PaneTarget, via: SideBySideVia) => void;
  /** Ctrl+\: the first correspondent of the section in view. */
  openFirst: () => Promise<void>;
  close: () => void;
  /** The learner scrolled, clicked or selected in a pane: it leads now. */
  touch: (pane: Pane) => void;
  /** The learner moves the second pane to another section of its book. */
  goSide: (sectionId: string) => void;
  toggleFollow: () => void;
  clearNotice: () => void;
  /** The second pane's reading position in a section (kept while a comparison takes the right side). */
  rememberScroll: (key: string, top: number) => void;
  scrollFor: (key: string) => number;
}

function useNarrow(active: boolean): boolean {
  const [narrow, setNarrow] = useState(() => isNarrowWindow(window.innerWidth));
  useEffect(() => {
    if (!active) return undefined;
    const onResize = () => setNarrow(isNarrowWindow(window.innerWidth));
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [active]);
  return narrow;
}

export function useSideBySide({
  enabled, main, jumpMain, pushCrumb, replaceCrumb, dropCrumb, currentEntry, visitPayload, onError,
}: SideBySideInput): SideBySide {
  const narrow = useNarrow(enabled);
  const [pair, setPairState] = useState<Pair | null>(null);
  const [section, setSection] = useState<SideBySideSectionDto | null>(null);
  const [phase, setPhase] = useState<SideBySide["phase"]>("idle");
  const [leader, setLeader] = useState<Pane>("main");
  // Follow along is on by default; one toggle turns it off for the session (Q14).
  const [follow, setFollow] = useState(true);
  const [staysPut, setStaysPut] = useState<Pane | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // Refs the async landings read: what is open, who leads, the crossing count.
  // The pair's ref moves with every change (not at the next render), so a
  // close or a landing in the same tick reads what is open now.
  const pairRef = useRef<Pair | null>(null);
  const setPair = useCallback((next: Pair | null) => {
    pairRef.current = next;
    setPairState(next);
  }, []);
  const leaderRef = useRef<Pane>("main");
  leaderRef.current = leader;
  const mainRef = useRef<MainPane | null>(main);
  mainRef.current = main;
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;
  const sectionRef = useRef<SideBySideSectionDto | null>(null);
  sectionRef.current = section;
  const currentEntryRef = useRef<CurrentEntry | null>(currentEntry);
  currentEntryRef.current = currentEntry;
  const visitRef = useRef(visitPayload);
  visitRef.current = visitPayload;
  const loadToken = useRef(0);
  const crossing = useRef(0);
  // Which opening this is (an open, a close or a reopen starts a new one; a pane moving does not).
  const opening = useRef(0);
  // Ctrl+\'s pending read: a later open, a close, another book or the switch going off supersedes it.
  const pendingOpen = useRef(0);
  const narrowRef = useRef(narrow);
  narrowRef.current = narrow;
  const lastFollow = useRef<LastFollow | null>(null);
  // The second pane's scroll position in its section (survives the pane being unmounted by a comparison).
  const sideScroll = useRef<{ key: string; top: number } | null>(null);

  const visit = () => visitRef.current?.() ?? {};

  const load = useCallback((target: PaneTarget) => {
    const mine = ++loadToken.current;
    setPhase("loading");
    api.readerSideBySideSection({ extractionId: target.extractionId, sectionId: target.sectionId }).then(({ section: shown }) => {
      if (loadToken.current !== mine) return;
      setSection(shown);
      setPhase("ready");
    }).catch((error) => {
      if (loadToken.current !== mine) return;
      setSection(null);
      setPhase("failed");
      onError(errorMessage(error));
    });
  }, [onError]);

  /** The session's end, recorded once (the narrow window's peek has no session to end). */
  const logEnded = useCallback((ended: Pair, via: EndedBy) => {
    if (ended.sheet) return;
    logReaderAction("side_by_side_closed", {
      ...(visitRef.current?.() ?? {}), side_by_side_id: ended.sessionId, detour_id: ended.entryId,
      target_source_id: ended.target.sourceId, target_extraction_id: ended.target.extractionId,
      target_section_id: ended.target.sectionId, seconds_open: Math.max(0, Math.round((Date.now() - ended.openedAt) / 1000)), via,
    });
  }, []);

  const reset = useCallback((via: EndedBy) => {
    const ended = pairRef.current;
    if (ended) logEnded(ended, via);
    loadToken.current += 1;
    crossing.current += 1;
    opening.current += 1;
    pendingOpen.current += 1;
    lastFollow.current = null;
    sideScroll.current = null;
    setPair(null);
    setSection(null);
    setPhase("idle");
    setStaysPut(null);
    leaderRef.current = "main";
    setLeader("main");
  }, [logEnded, setPair]);

  /** A new session: the pair, its section read, the main pane leading. */
  const start = useCallback((target: PaneTarget, entryId: string | null, sheet: boolean, mainSourceId: string): Pair => {
    const previous = pairRef.current;
    if (previous) logEnded(previous, "replaced");
    crossing.current += 1;
    opening.current += 1;
    lastFollow.current = null;
    sideScroll.current = null;
    const next: Pair = { target, entryId, sheet, mainSourceId, sessionId: newActivityId(), openedAt: Date.now() };
    setPair(next);
    setSection(null);
    setStaysPut(null);
    // The learner was reading the main pane: it leads until they touch the other.
    leaderRef.current = "main";
    setLeader("main");
    load(target);
    return next;
  }, [load, logEnded, setPair]);

  const open = useCallback((target: PaneTarget, via: SideBySideVia) => {
    const here = mainRef.current;
    if (!enabledRef.current || !here || target.sourceId === here.sourceId) return;
    pendingOpen.current += 1;
    setNotice(null);
    const sheet = narrowRef.current;
    const label = crumbLabel(target);
    const current = pairRef.current;
    let entryId: string | null = null;
    if (!sheet) {
      // Side by side already open on its crumb: the crumb now names the new
      // pair (the same entry, so closing still takes it off); else a new crumb.
      const onItsCrumb = current && !current.sheet && current.entryId && current.entryId === currentEntryRef.current?.id;
      entryId = onItsCrumb && replaceCrumb?.(current.entryId as string, label, target)
        ? current.entryId
        : pushCrumb(label, target);
    }
    const opened = start(target, entryId, sheet, here.sourceId);
    logReaderAction(sheet ? "corresponding_section_peeked" : "side_by_side_opened", {
      ...visit(), extraction_id: here.extractionId, source_id: here.sourceId, section_id: here.sectionId,
      target_source_id: target.sourceId, target_extraction_id: target.extractionId,
      target_section_id: target.sectionId, target_span_id: target.spanId, by: target.by, via,
      ...(sheet ? {} : { side_by_side_id: opened.sessionId, detour_id: entryId }),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pushCrumb, replaceCrumb, start]);

  const close = useCallback(() => {
    const current = pairRef.current;
    if (!current) return;
    if (current.entryId) dropCrumb(current.entryId);
    reset("close");
  }, [dropCrumb, reset]);

  const openFirst = useCallback(async () => {
    const here = mainRef.current;
    if (!enabledRef.current || !here?.sectionId) return;
    const mine = ++pendingOpen.current;
    let view: CorrespondentsDto;
    try {
      view = await api.readerCorrespondents({ extractionId: here.extractionId, sectionId: here.sectionId, searchFallback: true });
    } catch (error) {
      if (pendingOpen.current === mine) onError(errorMessage(error));
      return;
    }
    // Superseded (another open, a close, another book, the switch off or the
    // working posture), or the learner moved on while it was read.
    if (pendingOpen.current !== mine || !enabledRef.current) return;
    if (mainRef.current?.sectionId !== here.sectionId || mainRef.current?.extractionId !== here.extractionId) return;
    const first = firstCorrespondent(view);
    if (!first) {
      setNotice(SIDE_BY_SIDE_COPY.nothing);
      return;
    }
    open(targetOf(first), "key");
  }, [onError, open]);

  const touch = useCallback((pane: Pane) => {
    if (!pairRef.current || pairRef.current.sheet) return;
    if (leaderRef.current !== pane) {
      leaderRef.current = pane;
      setLeader(pane);
      // A new leader: whatever the old one's crossing asked for no longer
      // applies, even if leadership comes back before the answer lands.
      crossing.current += 1;
    }
    // The learner moved the pane that stayed put: its line goes.
    setStaysPut((current) => (current === pane ? null : current));
  }, []);

  /** The follower moves once, to the leader's new section's first judged correspondent. */
  const followFrom = useCallback(async (from: Pane, extractionId: string, sectionId: string) => {
    const current = pairRef.current;
    const here = mainRef.current;
    if (!current || current.sheet || narrowRef.current || !here) return;
    const mine = ++crossing.current;
    const openedAs = opening.current;
    const followerSource = from === "main" ? current.target.sourceId : here.sourceId;
    let view: CorrespondentsDto | null = null;
    try {
      // Judged coverage only: the quiet read, never a search.
      view = await api.readerCorrespondents({ extractionId, sectionId, searchFallback: false });
    } catch {
      view = null;
    }
    // A later crossing, a close, a change of leader (even one that came back)
    // or the switch going off overtakes this one.
    if (crossing.current !== mine || opening.current !== openedAs || leaderRef.current !== from || !enabledRef.current) return;
    const now = pairRef.current;
    if (!now) return;
    const hit = firstJudgedIn(view, followerSource);
    const follower: Pane = from === "main" ? "side" : "main";
    if (!hit || !hit.jump.spanId) {
      setStaysPut(follower);
      return;
    }
    const target = targetOf(hit);
    let fromSectionId: string | null;
    if (follower === "side") {
      if (sectionRef.current?.sectionId === target.sectionId && sectionRef.current?.extractionId === target.extractionId) {
        setStaysPut(null);
        return;
      }
      fromSectionId = now.target.sectionId;
      setPair({ ...now, target });
      load(target);
    } else {
      if (target.extractionId !== here.extractionId) {
        // Another reading of the open book: not this pane's to move.
        setStaysPut("main");
        return;
      }
      fromSectionId = mainRef.current?.sectionId ?? null;
      jumpMain(target.spanId as string);
    }
    setStaysPut(null);
    lastFollow.current = fromSectionId
      ? { pane: follower, fromSectionId, toSectionId: target.sectionId, at: Date.now(), sessionId: now.sessionId }
      : null;
    logReaderAction("follow_along_moved", {
      ...(visitRef.current?.() ?? {}), side_by_side_id: now.sessionId,
      extraction_id: extractionId, section_id: sectionId, leader: from,
      target_source_id: target.sourceId, target_extraction_id: target.extractionId,
      target_section_id: target.sectionId, target_span_id: target.spanId, by: "judged",
    });
  }, [load, jumpMain, setPair]);

  /** The learner moved ``pane`` by hand to ``sectionId``: back where follow along took it from is an undo. */
  const noteManualMove = useCallback((pane: Pane, sectionId: string) => {
    const moved = lastFollow.current;
    if (!moved || moved.pane !== pane || sectionId === moved.toSectionId) return;
    lastFollow.current = null;
    if (sectionId !== moved.fromSectionId || pairRef.current?.sessionId !== moved.sessionId) return;
    logReaderAction("follow_along_undone", {
      ...(visitRef.current?.() ?? {}), side_by_side_id: moved.sessionId, leader: pane,
      section_id: moved.toSectionId, target_section_id: moved.fromSectionId,
      seconds_after: Math.max(0, Math.round((Date.now() - moved.at) / 1000)),
    });
  }, []);

  // A crossing in the main pane (the Guide's section in view changed).
  const lastMainSection = useRef<string | null>(main?.sectionId ?? null);
  useEffect(() => {
    const sectionId = main?.sectionId ?? null;
    const previous = lastMainSection.current;
    lastMainSection.current = sectionId;
    if (!sectionId || sectionId === previous || !main) return;
    if (!pairRef.current || pairRef.current.sheet || narrowRef.current || leaderRef.current !== "main") return;
    noteManualMove("main", sectionId);
    if (!follow) return;
    void followFrom("main", main.extractionId, sectionId);
  }, [main, follow, followFrom, noteManualMove]);

  const goSide = useCallback((sectionId: string) => {
    const current = pairRef.current;
    if (!current) return;
    touch("side");
    noteManualMove("side", sectionId);
    const target: PaneTarget = { ...current.target, sectionId, extractionId: current.target.extractionId, spanId: null, by: current.target.by, title: current.target.title };
    setPair({ ...current, target });
    load(target);
    // A crossing in the side pane, which the learner just moved: it leads.
    if (follow && !current.sheet) void followFrom("side", target.extractionId, sectionId);
  }, [touch, noteManualMove, load, follow, followFrom, setPair]);

  const toggleFollow = useCallback(() => {
    setFollow((value) => !value);
    setStaysPut(null);
    crossing.current += 1;
  }, []);

  // The return stack: walking off the crumb closes side by side; walking onto
  // a side_by_side entry reopens its pair (no new crumb), once the main pane
  // holds the book it was opened beside (a source detour in between is fine:
  // the pair lives in the entry, and goes when the entry does).
  const mainSource = main?.sourceId ?? null;
  useEffect(() => {
    const current = pairRef.current;
    const entryId = currentEntry?.id ?? null;
    if (current && current.entryId === entryId) return;
    const target = currentEntry?.kind === "side_by_side" ? currentEntry.sideBySide ?? null : null;
    const onCrumb = Boolean(target && entryId && enabled && !narrow && mainSource && currentEntry?.sourceId === mainSource);
    if (onCrumb) {
      if (!current || current.entryId) {
        const opened = start(target as PaneTarget, entryId, false, mainSource as string);
        const here = mainRef.current;
        logReaderAction("side_by_side_opened", {
          ...(visitRef.current?.() ?? {}), extraction_id: here?.extractionId ?? null, source_id: mainSource,
          section_id: here?.sectionId ?? null, target_source_id: opened.target.sourceId,
          target_extraction_id: opened.target.extractionId, target_section_id: opened.target.sectionId,
          target_span_id: opened.target.spanId, by: opened.target.by, via: "crumb",
          side_by_side_id: opened.sessionId, detour_id: entryId,
        });
      }
      return;
    }
    if (current?.entryId) reset("walked_off");
  }, [currentEntry, mainSource, enabled, narrow, reset, start]);

  // Another book in the main pane (not the one this pair was opened beside):
  // side by side ends; a pending Ctrl+\ is dropped.
  useEffect(() => {
    pendingOpen.current += 1;
    const current = pairRef.current;
    if (current && current.mainSourceId !== mainSource) {
      if (current.entryId) dropCrumb(current.entryId);
      reset("source");
    }
    setNotice(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mainSource]);
  // The switch off (or the working posture, or offline): side by side ends,
  // and nothing pending can reopen it.
  useEffect(() => {
    if (enabled) return;
    pendingOpen.current += 1;
    if (pairRef.current) reset("switch_off");
  }, [enabled, reset]);

  const rememberScroll = useCallback((key: string, top: number) => {
    if (pairRef.current) sideScroll.current = { key, top };
  }, []);
  const scrollFor = useCallback((key: string) => (sideScroll.current?.key === key ? sideScroll.current.top : 0), []);

  // The side pane's section title, once read, names the pane (a moved pane's target carries the old title).
  const shownTarget: PaneTarget | null = pair
    ? { ...pair.target, title: section && section.sectionId === pair.target.sectionId ? section.title : pair.target.title }
    : null;
  // Rendered state is gated on the switch now, not only on what is open.
  const live = Boolean(enabled && pair);

  return {
    enabled,
    narrow,
    panes: Boolean(live && pair && !pair.sheet && !narrow),
    sheet: Boolean(live && pair && (pair.sheet || narrow)),
    target: live ? shownTarget : null,
    section,
    phase,
    leader,
    follow,
    staysPut,
    notice,
    open,
    openFirst,
    close,
    touch,
    goSide,
    toggleFollow,
    clearNotice: () => setNotice(null),
    rememberScroll,
    scrollFor,
  };
}

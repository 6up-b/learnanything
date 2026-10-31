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
// Records (salience only): side_by_side_opened (corresponding_section_peeked
// for the narrow window's peek) and follow_along_moved. No model call.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { CorrespondentsDto, SideBySideSectionDto } from "../../api/dto";
import { errorMessage } from "../../errors";
import { logReaderAction } from "./activity";
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

/** The book open in the main pane, and the section in view there. */
export interface MainPane {
  sourceId: string;
  sourceTitle: string;
  extractionId: string;
  sectionId: string | null;
}

export interface SideBySideInput {
  /** The prompt contract's `sideBySide` (and not offline, not working). */
  enabled: boolean;
  main: MainPane | null;
  /** Moves the main pane to a passage (follow along; never a detour). */
  jumpMain: (spanId: string) => void;
  /** Pushes the crumb; returns its return-stack entry id (null: no return stack). */
  pushCrumb: (label: string) => string | null;
  /** Takes the crumb off again when the learner closes side by side. */
  dropCrumb: (entryId: string) => void;
  /** The return stack's current entry id (walking off the crumb closes side by side). */
  currentEntryId: string | null;
  onError: (message: string) => void;
}

export type SideBySideVia = "find_list" | "peek" | "key";

interface Pair {
  target: PaneTarget;
  /** The crumb's entry (null: no return stack, or the narrow window's peek). */
  entryId: string | null;
  /** The narrow window's peek (a sheet; nothing follows). */
  sheet: boolean;
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

export function useSideBySide({ enabled, main, jumpMain, pushCrumb, dropCrumb, currentEntryId, onError }: SideBySideInput): SideBySide {
  const narrow = useNarrow(enabled);
  const [pair, setPair] = useState<Pair | null>(null);
  const [section, setSection] = useState<SideBySideSectionDto | null>(null);
  const [phase, setPhase] = useState<SideBySide["phase"]>("idle");
  const [leader, setLeader] = useState<Pane>("main");
  // Follow along is on by default; one toggle turns it off for the session (Q14).
  const [follow, setFollow] = useState(true);
  const [staysPut, setStaysPut] = useState<Pane | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // Refs the async landings read: what is open, who leads, the crossing count.
  const pairRef = useRef<Pair | null>(null);
  pairRef.current = pair;
  const leaderRef = useRef<Pane>("main");
  leaderRef.current = leader;
  const mainRef = useRef<MainPane | null>(main);
  mainRef.current = main;
  const sectionRef = useRef<SideBySideSectionDto | null>(null);
  sectionRef.current = section;
  const loadToken = useRef(0);
  const crossing = useRef(0);
  // Which opening this is (an open, a close or a reopen starts a new one; a pane moving does not).
  const opening = useRef(0);
  const narrowRef = useRef(narrow);
  narrowRef.current = narrow;
  // Crumbs this visit opened, by entry id, so Alt+→ onto one reopens it.
  const crumbs = useRef<Map<string, PaneTarget>>(new Map());

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

  const reset = useCallback(() => {
    loadToken.current += 1;
    crossing.current += 1;
    opening.current += 1;
    setPair(null);
    setSection(null);
    setPhase("idle");
    setStaysPut(null);
    setLeader("main");
  }, []);

  const open = useCallback((target: PaneTarget, via: SideBySideVia) => {
    const here = mainRef.current;
    if (!enabled || !here || target.sourceId === here.sourceId) return;
    setNotice(null);
    const sheet = narrow;
    // The crumb (a variant of the comparing posture); a peek pushes none.
    const entryId = sheet ? null : pushCrumb(crumbLabel(target));
    if (entryId) crumbs.current.set(entryId, target);
    crossing.current += 1;
    opening.current += 1;
    setPair({ target, entryId, sheet });
    setSection(null);
    setStaysPut(null);
    // The learner was reading the main pane: it leads until they touch the other.
    setLeader("main");
    load(target);
    logReaderAction(sheet ? "corresponding_section_peeked" : "side_by_side_opened", {
      extraction_id: here.extractionId, source_id: here.sourceId, section_id: here.sectionId,
      target_source_id: target.sourceId, target_extraction_id: target.extractionId,
      target_section_id: target.sectionId, target_span_id: target.spanId, by: target.by, via,
    });
  }, [enabled, narrow, pushCrumb, load]);

  const close = useCallback(() => {
    const current = pairRef.current;
    if (!current) return;
    if (current.entryId) dropCrumb(current.entryId);
    reset();
  }, [dropCrumb, reset]);

  const openFirst = useCallback(async () => {
    const here = mainRef.current;
    if (!enabled || !here?.sectionId) return;
    let view: CorrespondentsDto;
    try {
      view = await api.readerCorrespondents({ extractionId: here.extractionId, sectionId: here.sectionId, searchFallback: true });
    } catch (error) {
      onError(errorMessage(error));
      return;
    }
    // The learner may have moved on while it was read.
    if (mainRef.current?.sectionId !== here.sectionId || mainRef.current?.extractionId !== here.extractionId) return;
    const first = firstCorrespondent(view);
    if (!first) {
      setNotice(SIDE_BY_SIDE_COPY.nothing);
      return;
    }
    open(targetOf(first), "key");
  }, [enabled, onError, open]);

  const touch = useCallback((pane: Pane) => {
    if (!pairRef.current || pairRef.current.sheet) return;
    if (leaderRef.current !== pane) {
      leaderRef.current = pane;
      setLeader(pane);
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
    // A later crossing, a close, or the learner touching the follower overtakes this one.
    if (crossing.current !== mine || opening.current !== openedAs || leaderRef.current !== from) return;
    const now = pairRef.current;
    if (!now) return;
    const hit = firstJudgedIn(view, followerSource);
    const follower: Pane = from === "main" ? "side" : "main";
    if (!hit || !hit.jump.spanId) {
      setStaysPut(follower);
      return;
    }
    const target = targetOf(hit);
    if (follower === "side") {
      if (sectionRef.current?.sectionId === target.sectionId && sectionRef.current?.extractionId === target.extractionId) {
        setStaysPut(null);
        return;
      }
      setPair({ ...now, target });
      load(target);
    } else {
      if (target.extractionId !== here.extractionId) {
        // Another reading of the open book: not this pane's to move.
        setStaysPut("main");
        return;
      }
      jumpMain(target.spanId as string);
    }
    setStaysPut(null);
    logReaderAction("follow_along_moved", {
      extraction_id: extractionId, section_id: sectionId, leader: from,
      target_source_id: target.sourceId, target_extraction_id: target.extractionId,
      target_section_id: target.sectionId, target_span_id: target.spanId, by: "judged",
    });
  }, [load, jumpMain]);

  // A crossing in the main pane (the Guide's section in view changed).
  const lastMainSection = useRef<string | null>(main?.sectionId ?? null);
  useEffect(() => {
    const sectionId = main?.sectionId ?? null;
    const previous = lastMainSection.current;
    lastMainSection.current = sectionId;
    if (!sectionId || sectionId === previous || !main) return;
    if (!pairRef.current || pairRef.current.sheet || narrowRef.current || !follow || leaderRef.current !== "main") return;
    void followFrom("main", main.extractionId, sectionId);
  }, [main, follow, followFrom]);

  const goSide = useCallback((sectionId: string) => {
    const current = pairRef.current;
    if (!current) return;
    touch("side");
    const target: PaneTarget = { ...current.target, sectionId, extractionId: current.target.extractionId, spanId: null, by: current.target.by, title: current.target.title };
    setPair({ ...current, target });
    load(target);
    // A crossing in the side pane, which the learner just moved: it leads.
    if (follow && !current.sheet) void followFrom("side", target.extractionId, sectionId);
  }, [touch, load, follow, followFrom]);

  const toggleFollow = useCallback(() => {
    setFollow((value) => !value);
    setStaysPut(null);
    crossing.current += 1;
  }, []);

  // The return stack: walking off the crumb closes side by side; walking onto
  // one this visit opened reopens it (no new crumb).
  useEffect(() => {
    const current = pairRef.current;
    const onCrumb = currentEntryId && crumbs.current.has(currentEntryId) && enabled && !narrow;
    if (current?.entryId === currentEntryId && current) return;
    if (onCrumb) {
      if (!current || current.entryId) {
        const target = crumbs.current.get(currentEntryId) as PaneTarget;
        crossing.current += 1;
        opening.current += 1;
        setPair({ target, entryId: currentEntryId, sheet: false });
        setSection(null);
        setStaysPut(null);
        setLeader("main");
        load(target);
      }
      return;
    }
    if (current?.entryId) reset();
  }, [currentEntryId, enabled, narrow, reset, load]);

  // Another book in the main pane, or the switch going off: side by side ends.
  const mainSource = main?.sourceId ?? null;
  useEffect(() => {
    if (pairRef.current) close();
    crumbs.current.clear();
    setNotice(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mainSource]);
  useEffect(() => {
    if (!enabled && pairRef.current) reset();
  }, [enabled, reset]);

  // The side pane's section title, once read, names the pane (a moved pane's target carries the old title).
  const shownTarget: PaneTarget | null = pair
    ? { ...pair.target, title: section && section.sectionId === pair.target.sectionId ? section.title : pair.target.title }
    : null;

  return {
    enabled,
    narrow,
    panes: Boolean(pair && !pair.sheet && !narrow),
    sheet: Boolean(pair && (pair.sheet || narrow)),
    target: shownTarget,
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
  };
}

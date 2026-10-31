// Reader CA5: "also in your books" (ux_reader_compare_ask_v1 §6.2, §6.3, §6.5).
//
// One dim line in the Guide, directly under the section's progress: the other
// books' sections whose judged coverage (C0a/C0b's section_coverage, read
// through reader.correspondents) names one of this section's LOs, by name and
// never by count ("also in Axler §5.A, Lay §5.1 ▸", ending "and others ▸" when
// the names don't fit). It is there only when the read reports judged
// coverage: an unchecked search hit never puts it on screen (CA5a's pressed
// "find this section in my other books" stays for that case), and with nothing
// there is nothing (no ghost line, no "none found").
//
// Expanded (x from the reading posture, or a click), the list is grouped by LO
// in the API's order. Each line is the book, the section's own number and
// title, its treatment in plain words, the coverage judge's notation line in
// LearnLoop's voice, the relation the learner kept, and "read" when the
// learner has read it. A section listed under several LOs shows once, under
// the first, with "also: …" on focus. No line carries a model-written pair
// relation (the index has none; `c` runs the comparison).
//
// Keys on the list: ↑↓ move, Space peek (CA5a's protected peek RPC, each
// block shown recorded as exposure), ↵ go there (the Reader's source detour:
// return stack, crumb, Alt+←), s side by side (only while the Reader passes
// CA6's entry: a seam until then), c compare (CA3's one request anchored on
// this section, as CA5a's compare does), Esc closes the peek, then folds.
//
// Corrections in each line's ⋯: "not about this" (CA5a's one durable
// operation, naming the LOs the line is listed under, with undo) and "also
// about…" (C0b's resolver: curriculum.also_about). The block's ⋯ hides the
// line for this book or everywhere (the vault's config; Settings brings it
// back), leaving nothing behind. Shown in skim mode: a table of contents is
// what skimming across books needs. Never in the working posture (the Reader
// does not mount it there). Nothing here calls a model.
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { api } from "../../api/client";
import type { CorrespondentKeptDto, CorrespondentPeekDto, CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { logCorrespondentAct } from "./correspondenceEvents";
import { quietCorrespondents } from "./correspondentsRead";
import { FIND_COPY, hitKey, newOperationId, type FindSectionOrigin } from "./FindSection";
import { clip } from "./readerShared";
import { MeaningLabel, SourceVoice, SpokenOnly } from "./voices";

export const ALSO_COPY = {
  prefix: "also in",
  others: "and others",
  title: "also in your books",
  treatment: { introduces: "introduces it", develops: "develops it", applies: "uses it", mentions: "mentions it" } as Record<string, string>,
  linkedByYou: "you linked it",
  notationSpoken: "LearnLoop's note (AI-written)",
  kept: "you compared these",
  read: "read",
  alsoOn: "also:",
  notAbout: "not about this",
  alsoAbout: "also about…",
  alsoAboutPlaceholder: "this is really about…",
  alsoAboutSending: "◐ finding the topic…",
  alsoAboutNoted: "noted: also about",
  undo: "undo",
  whereThisGoes: FIND_COPY.whereThisGoes,
  whereThisGoesText: FIND_COPY.whereThisGoesText,
  more: "⋯",
  hideBook: "hide for this book",
  hideEverywhere: "hide everywhere",
  peekHead: "peek",
  goThere: "go there",
  compare: "compare",
  sideBySide: "side by side",
  closePeek: "esc close",
  keys: { peek: "space peek", go: "↵ go there", side: "s side by side", compare: "c compare", fix: "⋯ not about this" },
} as const;

/** The collapsed line's names, in characters (a display bound: one rail line at the Guide's size). */
const LINE_CHARS = 46;

/** The section's own number ("5.A", "5.1"), else its title clipped (the book's words). */
export function sectionShort(title: string): string {
  const trimmed = title.trim().replace(/^(section|chapter|§)\s*/i, "");
  const match = /^([0-9]+(?:[.\-–][0-9A-Za-z]+)*|[A-Z](?:\.[0-9]+)+)(?=[\s.:)]|$)/.exec(trimmed);
  return match ? match[1] : clip(trimmed, 22);
}

/** A book's name as the line shows it: its title before any subtitle, clipped. */
export function bookShort(title: string): string {
  const head = title.split(/\s[:—–-]\s|:\s/)[0]?.trim() || title.trim();
  return head.length > 20 ? `${head.slice(0, 20).trimEnd()}…` : head;
}

/** "you compared these: different notation" from what the learner kept (RW4d's fine labels). */
export function keptWords(kept: CorrespondentKeptDto[] | undefined): string | null {
  if (!kept || kept.length === 0) return null;
  const relations = [...new Set(kept.flatMap((entry) => entry.relations ?? []))].map((label) => label.replace(/_/g, " "));
  return relations.length ? `${ALSO_COPY.kept}: ${relations.join(", ")}` : ALSO_COPY.kept;
}

export interface AlsoLine {
  key: string;
  hit: CorrespondentSectionDto;
  /** The LO it is listed under (the first in the API's order) and the others it shares. */
  learningObjectId: string;
  alsoTitles: string[];
  /** The shared LOs "not about this" corrects (the line's own, then its others). */
  learningObjectIds: string[];
}

export interface AlsoGroup {
  learningObjectId: string;
  title: string;
  lines: AlsoLine[];
}

/** The judged answer as the list shows it: by LO in the API's order, each section once. */
export function alsoGroups(view: CorrespondentsDto | null): AlsoGroup[] {
  if (!view || view.status !== "judged") return [];
  const titles = new Map(view.learningObjects.map((group) => [group.learningObjectId, group.title]));
  const seen = new Set<string>();
  const groups: AlsoGroup[] = [];
  for (const group of view.learningObjects) {
    const lines: AlsoLine[] = [];
    for (const source of group.sources) {
      for (const hit of source.sections) {
        // Judged coverage only: a search hit never appears here.
        if (hit.by === "search") continue;
        const key = hitKey(hit);
        if (seen.has(key)) continue;
        seen.add(key);
        const others = (hit.alsoLearningObjectIds ?? []).filter((id) => id !== group.learningObjectId);
        lines.push({
          key, hit, learningObjectId: group.learningObjectId,
          alsoTitles: others.map((id) => titles.get(id)).filter((title): title is string => Boolean(title)),
          learningObjectIds: [group.learningObjectId, ...others],
        });
      }
    }
    if (lines.length > 0) groups.push({ learningObjectId: group.learningObjectId, title: group.title, lines });
  }
  return groups;
}

/** The collapsed line's names and whether some did not fit ("and others"). */
export function lineNames(lines: AlsoLine[]): { names: string[]; more: boolean } {
  const names: string[] = [];
  let used = 0;
  for (const line of lines) {
    const name = `${bookShort(line.hit.sourceTitle)} §${sectionShort(line.hit.title)}`;
    const cost = name.length + (names.length > 0 ? 2 : 0);
    if (names.length > 0 && used + cost > LINE_CHARS) return { names, more: true };
    names.push(name);
    used += cost;
  }
  return { names, more: false };
}

export interface AlsoPeekCrumb {
  label: string;
}

export interface AlsoInBooksProps {
  extractionId: string;
  section: FindSectionOrigin | null;
  /** The learner hid the line (everywhere, or for this book): nothing renders. */
  hidden: boolean;
  onHide: (scope: "book" | "everywhere") => void;
  /** The source detour to the section (return stack, crumb, Alt+←). */
  onGoThere: (target: { sourceId: string; extractionId: string; spanId: string }) => void;
  /** CA3's one request anchored on this section, with the other section's book (null: comparing is off). */
  onCompare: ((hit: CorrespondentSectionDto) => void) | null;
  /** Reader CA6's entry (absent until CA6 wires it: `s` does nothing and is not offered). */
  onSideBySide?: ((hit: CorrespondentSectionDto) => void) | null;
  /** The detour strip's `› peek Axler §5.A` (null when no peek is open). */
  onPeekChange?: (crumb: AlsoPeekCrumb | null) => void;
  /** Whether the line is on screen (the Reader offers `x` only then). */
  onAvailableChange?: (available: boolean) => void;
  /** A correction landed: the section's coverage changed (CA5a's action may be due). */
  onCoverageChanged?: () => void;
  onError: (message: string) => void;
  /** The Reader's `x`: each new nonzero value opens the list and focuses its first line. */
  expandToken?: number;
  /** The detour strip's crumb: each new nonzero value closes the peek. */
  closePeekToken?: number;
}

interface Peek {
  key: string;
  hit: CorrespondentSectionDto;
  view: CorrespondentPeekDto | null;
}

interface AlsoAbout {
  key: string;
  text: string;
  phase: "editing" | "sending" | "done";
  message: string | null;
}

const LINK: CSSProperties = {
  border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 10,
  color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2,
};
const DIM_LINE: CSSProperties = {
  border: 0, background: "transparent", padding: 0, cursor: "pointer", textAlign: "left", fontFamily: FONT_MONO,
  fontSize: 10, color: COLOR.textDim, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0,
};
const HEAD: CSSProperties = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim, textTransform: "uppercase" };

export function AlsoInBooks({
  extractionId, section, hidden, onHide, onGoThere, onCompare, onSideBySide = null, onPeekChange, onAvailableChange,
  onCoverageChanged, onError, expandToken = 0, closePeekToken = 0,
}: AlsoInBooksProps) {
  const sectionId = section?.id ?? null;
  const [answer, setAnswer] = useState<{ sectionId: string; view: CorrespondentsDto } | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [peek, setPeek] = useState<Peek | null>(null);
  const [gone, setGone] = useState<Map<string, { line: AlsoLine; operationId: string }>>(new Map());
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [menuKey, setMenuKey] = useState<string | null>(null);
  const [blockMenu, setBlockMenu] = useState(false);
  const [why, setWhy] = useState<string | null>(null);
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
  const [alsoAbout, setAlsoAbout] = useState<AlsoAbout | null>(null);
  const lineRefs = useRef<Map<string, HTMLButtonElement>>(new Map());
  const collapsedRef = useRef<HTMLButtonElement | null>(null);
  // The section's generation: a late answer for another section never lands.
  const token = useRef(0);
  const pendingOps = useRef<Map<string, string>>(new Map());
  const peekChange = useRef(onPeekChange);
  peekChange.current = onPeekChange;

  const read = useCallback((mine: number, id: string) => {
    quietCorrespondents(extractionId, id).then((view) => {
      if (token.current !== mine) return;
      // Judged coverage only; anything else (none, unchecked, withheld) shows nothing.
      setAnswer(view.status === "judged" ? { sectionId: id, view } : null);
    }).catch(() => {
      // Fails closed and quiet: no line rather than an error nobody asked for.
      if (token.current === mine) setAnswer(null);
    });
  }, [extractionId]);

  useEffect(() => {
    const mine = ++token.current;
    setAnswer(null);
    setExpanded(false);
    setPeek(null);
    setGone(new Map());
    setBusyKey(null);
    setMenuKey(null);
    setBlockMenu(false);
    setWhy(null);
    setFocusedKey(null);
    setAlsoAbout(null);
    if (sectionId) read(mine, sectionId);
  }, [extractionId, sectionId, read]);

  // The detour strip's crumb follows the peek; it goes with the component.
  useEffect(() => {
    peekChange.current?.(peek ? { label: `peek ${bookShort(peek.hit.sourceTitle)} §${sectionShort(peek.hit.title)}` } : null);
  }, [peek]);
  useEffect(() => () => peekChange.current?.(null), []);

  const view = answer && answer.sectionId === sectionId ? answer.view : null;
  const groups = useMemo(() => alsoGroups(view), [view]);
  const lines = useMemo(() => groups.flatMap((group) => group.lines), [groups]);
  const liveLines = lines.filter((line) => !gone.has(line.key));
  const visible = Boolean(section) && !hidden && lines.length > 0;

  // Hidden leaves nothing behind: no list, no peek, no crumb.
  useEffect(() => {
    if (!hidden) return;
    setExpanded(false);
    setPeek(null);
    setBlockMenu(false);
  }, [hidden]);
  const available = visible && liveLines.length > 0;
  const availableChange = useRef(onAvailableChange);
  availableChange.current = onAvailableChange;
  useEffect(() => {
    availableChange.current?.(available);
  }, [available]);
  useEffect(() => () => availableChange.current?.(false), []);

  const focusLine = (key: string) => window.requestAnimationFrame(() => lineRefs.current.get(key)?.focus({ preventScroll: false }));
  // Focus asked for before the element it names is drawn (x opens the list,
  // Esc folds it): applied once the render that draws it has committed.
  const pendingFocus = useRef<string | null>(null);
  useEffect(() => {
    const wanted = pendingFocus.current;
    if (wanted === null) return;
    const node = wanted === "" ? collapsedRef.current : lineRefs.current.get(wanted);
    if (node) {
      pendingFocus.current = null;
      node.focus({ preventScroll: true });
    }
  });

  // The Reader's `x`: open the list at its first line.
  const seenExpand = useRef(expandToken);
  useEffect(() => {
    if (expandToken === seenExpand.current) return;
    seenExpand.current = expandToken;
    if (!visible || liveLines.length === 0) return;
    setExpanded(true);
    pendingFocus.current = liveLines[0].key;
    // Only a new press acts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expandToken]);

  const closePeek = useCallback(() => {
    const key = peek?.key;
    setPeek(null);
    if (key) focusLine(key);
  }, [peek]);

  const seenClose = useRef(closePeekToken);
  useEffect(() => {
    if (closePeekToken === seenClose.current) return;
    seenClose.current = closePeekToken;
    if (peek) closePeek();
  }, [closePeekToken, peek, closePeek]);

  const fold = useCallback(() => {
    setExpanded(false);
    setPeek(null);
    setMenuKey(null);
    setBlockMenu(false);
    setAlsoAbout(null);
    pendingFocus.current = "";
  }, []);

  const openPeek = useCallback(async (line: AlsoLine) => {
    const { key, hit } = line;
    if (!hit.jump.spanId) return;
    const mine = token.current;
    setPeek({ key, hit, view: null });
    logCorrespondentAct("corresponding_section_peeked", extractionId, sectionId, hit, "also_list");
    try {
      // CA5a's protected peek: protection read now, the section's own blocks, each one shown recorded.
      const { peek: shown } = await api.readerCorrespondentPeek({ extractionId: hit.extractionId, sectionId: hit.sectionId });
      if (token.current !== mine) return;
      setPeek((current) => (current?.key === key ? { key, hit, view: shown } : current));
    } catch (error) {
      if (token.current !== mine) return;
      onError(errorMessage(error));
      setPeek((current) => (current?.key === key ? null : current));
    }
  }, [extractionId, sectionId, onError]);

  const goThere = useCallback((hit: CorrespondentSectionDto) => {
    if (!hit.jump.spanId) return;
    logCorrespondentAct("corresponding_section_opened", extractionId, sectionId, hit, "also_list");
    onGoThere({ sourceId: hit.sourceId, extractionId: hit.jump.extractionId, spanId: hit.jump.spanId });
  }, [extractionId, sectionId, onGoThere]);

  const sideBySide = useCallback((hit: CorrespondentSectionDto) => {
    if (!onSideBySide || !hit.jump.spanId) return;
    onSideBySide(hit);
  }, [onSideBySide]);

  /** One correction as one operation; it lands only on the section it was made from. */
  const runOperation = useCallback(async (key: string, act: string, request: (operationId: string) => Promise<unknown>, landed: () => void) => {
    if (!sectionId || busyKey) return;
    const mine = token.current;
    const opKey = `${extractionId}/${sectionId}|${key}|${act}`;
    const operationId = pendingOps.current.get(opKey) ?? newOperationId();
    pendingOps.current.set(opKey, operationId);
    setBusyKey(key);
    try {
      await request(operationId);
      pendingOps.current.delete(opKey);
      if (token.current === mine) {
        landed();
        onCoverageChanged?.();
      }
    } catch (error) {
      // Not answered: the line stays, and pressing again resends the same operation.
      if (token.current === mine) onError(errorMessage(error));
    } finally {
      if (token.current === mine) setBusyKey(null);
    }
  }, [extractionId, sectionId, busyKey, onError, onCoverageChanged]);

  const notAbout = useCallback(async (line: AlsoLine) => {
    if (!sectionId) return;
    let recorded: string | null = null;
    setMenuKey(null);
    await runOperation(line.key, "not_about", async (operationId) => {
      const { operation } = await api.readerCorrespondentDismiss({
        extractionId, sectionId, targetExtractionId: line.hit.extractionId, targetSectionId: line.hit.sectionId,
        operationId, learningObjectIds: line.learningObjectIds,
      });
      recorded = operation.operationId;
    }, () => {
      const operationId = recorded;
      if (!operationId) return;
      setGone((current) => new Map(current).set(line.key, { line, operationId }));
      setPeek((current) => (current?.key === line.key ? null : current));
    });
  }, [extractionId, sectionId, runOperation]);

  const undo = useCallback(async (key: string) => {
    const entry = gone.get(key);
    if (!entry || !sectionId) return;
    await runOperation(key, `undo:${entry.operationId}`, (operationId) => api.readerCorrespondentDismiss({
      extractionId, sectionId, targetExtractionId: entry.line.hit.extractionId, targetSectionId: entry.line.hit.sectionId,
      operationId, undoOf: entry.operationId,
    }), () => {
      setGone((current) => {
        const next = new Map(current);
        next.delete(key);
        return next;
      });
    });
  }, [extractionId, sectionId, gone, runOperation]);

  const sendAlsoAbout = useCallback(async (line: AlsoLine, text: string) => {
    const words = text.trim();
    if (!words || !sectionId) return;
    const mine = token.current;
    setAlsoAbout({ key: line.key, text: words, phase: "sending", message: null });
    try {
      // C0b's resolver: the learner's words to one LO, written as C0a's is_about correction.
      const result = await api.curriculumAlsoAbout({ extractionId: line.hit.extractionId, sectionId: line.hit.sectionId, text: words });
      if (token.current !== mine) return;
      const message = result.status === "corrected"
        ? `${ALSO_COPY.alsoAboutNoted} ${result.title ?? ""}`.trim()
        : result.message ?? null;
      setAlsoAbout({ key: line.key, text: words, phase: "done", message });
      if (result.status === "corrected") {
        onCoverageChanged?.();
        read(mine, sectionId);
      }
    } catch (error) {
      if (token.current !== mine) return;
      onError(errorMessage(error));
      setAlsoAbout({ key: line.key, text: words, phase: "editing", message: null });
    }
  }, [sectionId, onError, onCoverageChanged, read]);

  const onListKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target as HTMLElement;
    const keyOf = target.closest<HTMLElement>("[data-also-line]")?.dataset.alsoLine ?? null;
    const index = keyOf ? liveLines.findIndex((line) => line.key === keyOf) : -1;
    // Space, ↵, s and c act on the line whose title has focus; on any other
    // button (⋯, undo, a menu entry) they keep the button's own press.
    const line = index >= 0 && target.dataset.alsoTitle !== undefined ? liveLines[index] : null;
    const consume = () => {
      event.preventDefault();
      event.stopPropagation();
    };
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (liveLines.length === 0) return;
      consume();
      const next = index < 0 ? 0 : (index + (event.key === "ArrowDown" ? 1 : -1) + liveLines.length) % liveLines.length;
      focusLine(liveLines[next].key);
    } else if (event.key === " " && line) {
      consume();
      void openPeek(line);
    } else if (event.key === "Enter" && line) {
      consume();
      goThere(line.hit);
    } else if ((event.key === "s" || event.key === "S") && line && onSideBySide) {
      consume();
      sideBySide(line.hit);
    } else if ((event.key === "c" || event.key === "C") && line && onCompare) {
      consume();
      onCompare(line.hit);
    } else if (event.key === "Escape") {
      consume();
      if (peek) closePeek();
      else if (menuKey || blockMenu || alsoAbout) {
        const back = menuKey ?? alsoAbout?.key ?? null;
        setMenuKey(null);
        setBlockMenu(false);
        setAlsoAbout(null);
        if (back) focusLine(back);
      } else fold();
    }
  };

  if (!visible || !section) return null;

  const blockMenuView = blockMenu ? (
    <span role="menu" aria-label={ALSO_COPY.title} style={{ display: "inline-flex", gap: 8 }}>
      <button type="button" role="menuitem" onClick={() => { setBlockMenu(false); onHide("book"); }} style={LINK}>{ALSO_COPY.hideBook}</button>
      <button type="button" role="menuitem" onClick={() => { setBlockMenu(false); onHide("everywhere"); }} style={LINK}>{ALSO_COPY.hideEverywhere}</button>
    </span>
  ) : null;
  const blockMore = (
    <button
      type="button"
      aria-label={`${ALSO_COPY.title}: more`}
      aria-expanded={blockMenu}
      onClick={() => setBlockMenu((open) => !open)}
      style={{ ...LINK, textDecoration: "none", color: COLOR.textDim }}
    >
      {ALSO_COPY.more}
    </button>
  );

  if (!expanded) {
    const { names, more } = lineNames(liveLines);
    if (names.length === 0) return null;
    return (
      <div data-also-in-books="" style={{ display: "flex", alignItems: "baseline", gap: 6, flexWrap: "wrap" }}>
        <button
          ref={collapsedRef}
          type="button"
          data-also-collapsed=""
          onClick={() => setExpanded(true)}
          aria-expanded={false}
          title={`${ALSO_COPY.prefix} ${liveLines.map((line) => `${line.hit.sourceTitle} · ${line.hit.title}`).join("; ")}`}
          style={{ ...DIM_LINE, flex: 1 }}
        >
          {ALSO_COPY.prefix} {names.join(", ")}{more ? ` ${ALSO_COPY.others}` : ""} ▸
        </button>
        {blockMore}
        {blockMenuView}
      </div>
    );
  }

  const keyHints = [
    ALSO_COPY.keys.peek, ALSO_COPY.keys.go,
    ...(onSideBySide ? [ALSO_COPY.keys.side] : []),
    ...(onCompare ? [ALSO_COPY.keys.compare] : []),
    ALSO_COPY.keys.fix,
  ].join(" · ");

  return (
    <div data-also-in-books="" data-also-expanded="" onKeyDown={onListKey} style={{ display: "flex", flexDirection: "column", gap: 6, paddingTop: 4 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={HEAD}>{ALSO_COPY.title}</span>
        <span style={{ marginLeft: "auto", display: "inline-flex", gap: 8, alignItems: "baseline" }}>
          {blockMenuView}
          {blockMore}
          <button type="button" onClick={fold} aria-label={`${ALSO_COPY.title}: fold`} style={LINK}>esc</button>
        </span>
      </div>
      <div role="list" aria-label={ALSO_COPY.title} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {groups.map((group) => (
          <div key={group.learningObjectId} role="group" aria-label={group.title} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>{group.title}</span>
            {group.lines.map((line) => {
              const { key, hit } = line;
              const removed = gone.get(key);
              if (removed) {
                return (
                  <div key={key} role="listitem" data-also-gone={key} style={{ paddingLeft: 10, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "baseline" }}>
                    <MeaningLabel>{bookShort(hit.sourceTitle)} § {clip(hit.title, 40)} · {ALSO_COPY.notAbout}</MeaningLabel>
                    <button type="button" onClick={() => void undo(key)} disabled={busyKey === key} style={LINK}>{ALSO_COPY.undo}</button>
                    <button type="button" onClick={() => setWhy((open) => (open === key ? null : key))} aria-expanded={why === key} style={LINK}>{ALSO_COPY.whereThisGoes}</button>
                    {why === key ? <MeaningLabel style={{ flexBasis: "100%" }}>{ALSO_COPY.whereThisGoesText}</MeaningLabel> : null}
                  </div>
                );
              }
              const focused = focusedKey === key;
              const peeking = peek?.key === key;
              const kept = keptWords(hit.kept);
              const treatment = hit.linkedByYou ? ALSO_COPY.linkedByYou
                : hit.treatmentWords ?? (hit.treatment ? ALSO_COPY.treatment[hit.treatment] ?? null : null);
              const box = alsoAbout?.key === key ? alsoAbout : null;
              return (
                <div
                  key={key}
                  role="listitem"
                  data-also-line={key}
                  onFocus={() => setFocusedKey(key)}
                  onBlur={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                      setFocusedKey((current) => (current === key ? null : current));
                    }
                  }}
                  style={{ paddingLeft: 10, display: "flex", flexDirection: "column", gap: 2, borderLeft: `2px solid ${peeking ? COLOR.amber : "transparent"}` }}
                >
                  <div style={{ display: "flex", alignItems: "baseline", gap: 6, minWidth: 0 }}>
                    <button
                      type="button"
                      ref={(node) => {
                        if (node) lineRefs.current.set(key, node);
                        else lineRefs.current.delete(key);
                      }}
                      data-also-title=""
                      onClick={() => void openPeek(line)}
                      title={`${hit.sourceTitle} · ${hit.title}`}
                      style={{ border: 0, background: "transparent", padding: 0, textAlign: "left", cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, minWidth: 0 }}
                    >
                      {bookShort(hit.sourceTitle)}  § {hit.title}
                    </button>
                    <button
                      type="button"
                      aria-label={`${ALSO_COPY.more} ${hit.sourceTitle} ${hit.title}`}
                      aria-expanded={menuKey === key}
                      onClick={() => setMenuKey((open) => (open === key ? null : key))}
                      style={{ ...LINK, textDecoration: "none", color: COLOR.textDim }}
                    >
                      {ALSO_COPY.more}
                    </button>
                    <button type="button" onClick={() => goThere(hit)} aria-label={`${ALSO_COPY.goThere}: ${hit.sourceTitle} ${hit.title}`} style={{ ...LINK, textDecoration: "none" }}>▸</button>
                  </div>
                  <MeaningLabel>
                    {[treatment, kept, hit.read ? ALSO_COPY.read : null].filter(Boolean).join(" · ")}
                  </MeaningLabel>
                  {hit.notation ? (
                    // The coverage judge's line: LearnLoop's voice (◇ when focused), labelled as its note.
                    <span data-also-notation="" data-voice="model" title={hit.notationLabel ?? undefined} style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.purpleText }}>
                      <SpokenOnly>{hit.notationLabel ?? ALSO_COPY.notationSpoken}:</SpokenOnly>
                      {focused ? <span aria-hidden="true">◇ </span> : null}{hit.notation}
                    </span>
                  ) : null}
                  {focused && line.alsoTitles.length > 0 ? (
                    <span data-also-also=""><MeaningLabel>{ALSO_COPY.alsoOn} {line.alsoTitles.join(", ")}</MeaningLabel></span>
                  ) : null}
                  {menuKey === key ? (
                    <div role="menu" aria-label={`${hit.sourceTitle} ${hit.title}`} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button type="button" role="menuitem" onClick={() => void notAbout(line)} disabled={busyKey === key} style={LINK}>{ALSO_COPY.notAbout}</button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          setMenuKey(null);
                          setAlsoAbout({ key, text: "", phase: "editing", message: null });
                        }}
                        style={LINK}
                      >
                        {ALSO_COPY.alsoAbout}
                      </button>
                      <button type="button" onClick={() => setWhy((open) => (open === key ? null : key))} aria-expanded={why === key} style={LINK}>{ALSO_COPY.whereThisGoes}</button>
                    </div>
                  ) : null}
                  {why === key ? <MeaningLabel>{ALSO_COPY.whereThisGoesText}</MeaningLabel> : null}
                  {box ? (
                    box.phase === "editing" ? (
                      <input
                        autoFocus
                        aria-label={`${ALSO_COPY.alsoAbout} ${hit.title}`}
                        value={box.text}
                        placeholder={ALSO_COPY.alsoAboutPlaceholder}
                        onChange={(event) => setAlsoAbout({ ...box, text: event.target.value })}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            void sendAlsoAbout(line, box.text);
                          } else if (event.key === "Escape") {
                            event.preventDefault();
                            event.stopPropagation();
                            setAlsoAbout(null);
                            focusLine(key);
                          }
                        }}
                        style={{ fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: "3px 6px" }}
                      />
                    ) : (
                      <span data-also-about-result=""><MeaningLabel>{box.phase === "sending" ? ALSO_COPY.alsoAboutSending : box.message}</MeaningLabel></span>
                    )
                  ) : null}
                </div>
              );
            })}
          </div>
        ))}
        <MeaningLabel>{keyHints}</MeaningLabel>
      </div>
      {peek ? (
        <div data-also-peek={peek.key} style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <span style={HEAD}>{ALSO_COPY.peekHead}</span>
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>§ {peek.hit.sourceTitle} · {clip(peek.hit.title, 50)}</span>
          </div>
          {peek.view ? (
            <SourceVoice source={peek.hit.sourceTitle} locator={peek.view.page !== null ? `p.${peek.view.page}` : null}>
              {/* The blocks start at the jump locator: the first is the one outlined. */}
              {peek.view.blocks.map((block, index) => (
                <p key={block.spanId} data-peek-span={block.spanId} style={{ margin: "0 0 6px", ...(index === 0 ? { outline: `1px solid ${COLOR.borderStrong}`, outlineOffset: 2 } : {}) }}>{clip(block.text, 700)}</p>
              ))}
            </SourceVoice>
          ) : (
            <MeaningLabel>◐</MeaningLabel>
          )}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" onClick={() => goThere(peek.hit)} style={LINK}>{ALSO_COPY.goThere} ↵</button>
            {onSideBySide ? <button type="button" onClick={() => sideBySide(peek.hit)} style={LINK}>{ALSO_COPY.sideBySide} (s)</button> : null}
            {onCompare ? <button type="button" onClick={() => onCompare(peek.hit)} style={LINK}>{ALSO_COPY.compare} with {clip(section.label, 30)} (c)</button> : null}
            <button type="button" onClick={closePeek} style={LINK}>{ALSO_COPY.closePeek}</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

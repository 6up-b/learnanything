// Reader CA4: the comparison table by point (ux_reader_compare_ask_v1 §5, X3-X5; K13, K16).
//
// A row per point, a column per book, the learner's column last:
//
//   ◇ point (LearnLoop's label; › the learner's words for a requested view)
//     with its agreement chips (exactly the relations its pairs returned;
//     "only in Axler" when one book alone is quoted; never a summary)
//   § each book's verified words first, LearnLoop's one line under a dotted
//     rule, or "— not addressed here" ("— not here" on a requested view)
//   › you: the learner's take on the row
//
// The three voices never share a box. Keep, a row's take (`t`), a take on the
// whole comparison, hide row (`-`) and remove live here (CompareKeep renders
// nothing for a table by point). The keys (§5.5) are checked against the
// comparing posture's: arrows / Home / End move the roving focus (it starts on
// the first row header and moves only on the learner's key), Space peeks a
// cell's passage, `o` opens its book there, ↵ expands a quote or opens a
// chip's pairs, `t` your take, `-` hide or show a row, `v` by point / by book,
// `k` keep; `/`, `+` and Ctrl+↵ belong to the comparison's controls (refine,
// add a book, the tutor) and Esc to the posture.
//
// Narrow (below the app's 1,040 px breakpoint, or a pane too narrow for two
// columns) the grid becomes cards by point with the same keys; *by book* (`v`,
// remembered per device) is one card per book. Nothing here takes focus
// unasked, animates or counts things to read (G54-G58); the one announcement is
// "Comparison ready: N points" once the table is there (§15 Q7).
import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode, type RefObject } from "react";
import { api } from "../../api/client";
import type { CompareTableDto, ComparePointCellDto, ComparePointDto, KeptComparisonDto, KeepTakeDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import {
  POINT_COLUMN_PX, READABLE_CELL_PX, YOU_COLUMN_PX, cardsByPoint, chipPairs, columnTitles, moveCell, notFound,
  readLayout, rowChips, writeLayout, type CellPosition, type CompareLayout,
} from "./comparePoints";
import { KEEP_COPY, fineLabel } from "./CompareKeep";
import { useCompareKeep } from "./compareKeepContext";
import { MeaningLabel, SpokenOnly } from "./voices";

export const POINT_COPY = {
  header: "differences kept · each line quotes its own book",
  pointHead: "point",
  you: "you",
  firstPoint: "LearnLoop's point",
  notAddressed: "not addressed here",
  notHere: "not here",
  notFound: "not found in your library",
  whereElse: "where else is this explained? ▸",
  byPoint: "by point",
  byBook: "by book",
  hidden: (label: string) => `hidden: ${label}`,
  show: "show",
  hide: "hide row",
  more: "more",
  less: "less",
  pairsHead: "how LearnLoop reads the relations (AI-written)",
  aboutWhole: "about the whole comparison",
  takePlaceholder: "your take on this row, in your words",
  wholePlaceholder: "your take on the whole comparison",
  ready: (count: number) => `Comparison ready: ${count} point${count === 1 ? "" : "s"}`,
  keys: "←↑↓→ cells · space peek · o open · ↵ expand · t your take · - hide row · / refine · + book · v layout · k keep",
  cardKeys: "↑↓ points · ←→ books · t take · k keep · esc",
  draft: "kept with the comparison",
  alsoIn: "also discussed in",
  leftOut: "left out",
  possible: "possible match, not checked",
} as const;

/** What the host can do for a cell (absent: the key does nothing there). */
export interface CompareGridActions {
  /** Space: peek a passage beside the table (with a crumb). */
  onPeek?: (target: { spanKey: string; sourceTitle: string | null }) => void;
  /** o: open the book at this passage in the left pane (with a crumb). */
  onOpen?: (target: { sourceId: string | null; extractionId: string; spanId: string }) => void;
  /** A view no book fills: a library ask on it. */
  onWhereElse?: (words: string) => void;
  /** §5.3: re-run a v1 comparison by point (one paid comparison, named first). */
  onCompareAgain?: (table: CompareTableDto) => void;
}

export const CompareGridActionsContext = createContext<CompareGridActions | null>(null);

export function useCompareGridActions(): CompareGridActions {
  return useContext(CompareGridActionsContext) ?? {};
}

const linkStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
} as const;
const quietStyle = { ...linkStyle, color: COLOR.textDim } as const;
const headStyle = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.06em", color: COLOR.textDim, textTransform: "uppercase" as const };
const chipStyle = { border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.purpleText, fontFamily: FONT_MONO,
  fontSize: 10, padding: "0 5px", cursor: "pointer" } as const;
const sourceRule = { borderLeft: `1px solid ${COLOR.borderStrong}`, paddingLeft: 8 } as const;
const modelRule = { borderLeft: `1px dotted ${COLOR.purplePill}`, paddingLeft: 8 } as const;
const learnerRule = { borderLeft: `2px solid var(--amber-mid)`, paddingLeft: 8 } as const;
/** A quote longer than this offers "more" (two lines are shown at most). */
const CLAMP_CHARS = 140;

type Target = "comparison" | string;

function useWidth(ref: RefObject<HTMLElement | null>): number | null {
  const [width, setWidth] = useState<number | null>(null);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    const measure = () => setWidth(node.getBoundingClientRect().width || null);
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}

function useWindowWidth(): number {
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return width;
}

function splitKey(key: string): { extractionId: string; spanId: string } {
  const at = key.indexOf(":");
  return { extractionId: key.slice(0, at), spanId: key.slice(at + 1) };
}

export function ComparePointTable({ table }: { table: CompareTableDto }) {
  const keepCtx = useCompareKeep();
  const actions = useCompareGridActions();
  const points = table.points ?? [];
  const columns = table.rows;
  const titles = columnTitles(table);
  const [layout, setLayoutState] = useState<CompareLayout>(() => readLayout());
  const [kept, setKept] = useState<KeptComparisonDto | null>(table.kept ?? null);
  const [hidden, setHidden] = useState<string[]>(table.kept?.hiddenPoints ?? []);
  const [drafts, setDrafts] = useState<Record<Target, string>>({});
  const [takeOpen, setTakeOpen] = useState<Target | null>(null);
  const [takeText, setTakeText] = useState("");
  const [expanded, setExpanded] = useState<string[]>([]);
  const [pairsOpen, setPairsOpen] = useState<string[]>([]);
  const [phase, setPhase] = useState<"idle" | "pending" | "failed" | "removed">("idle");
  const [failure, setFailure] = useState<string | null>(null);
  const [why, setWhy] = useState(false);
  const [focus, setFocus] = useState<CellPosition>({ row: 0, col: 0 });
  const moved = useRef(false);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const takeRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    // `t` (or "add your take") was the learner's press: the box takes the cursor.
    if (takeOpen !== null) takeRef.current?.focus({ preventScroll: true });
  }, [takeOpen]);
  const paneWidth = useWidth(frameRef);
  const windowWidth = useWindowWidth();
  useEffect(() => {
    setKept(table.kept ?? null);
    setHidden(table.kept?.hiddenPoints ?? []);
  }, [table.kept, table.comparisonId]);
  const cards = layout === "by_point" && cardsByPoint(paneWidth, windowWidth);
  // Keep is the library answer's (or a kept comparison's), as CompareKeep's rule.
  const canKeep = Boolean(keepCtx && (keepCtx.settings.library || table.kept) && table.status === "ok" && table.comparisonId);
  const comparisonId = table.comparisonId;

  // The roving focus: rows are points (by point) or books (by book).
  const byBook = layout === "by_book";
  const shownPoints = points.filter((point) => !hidden.includes(point.id));
  const rowCount = byBook ? columns.length : points.length;
  const colsOf = (row: number) => {
    if (byBook) return 1 + shownPoints.length;
    const point = points[row];
    return point && hidden.includes(point.id) ? 1 : 2 + columns.length;
  };
  useEffect(() => {
    // Focus moves only after the learner's key (never on a table landing).
    if (!moved.current) return;
    moved.current = false;
    frameRef.current?.querySelector<HTMLElement>(`[data-cell="${focus.row}:${focus.col}"]`)?.focus({ preventScroll: false });
  }, [focus, layout, hidden]);

  const setLayout = (next: CompareLayout) => {
    setLayoutState(next);
    writeLayout(next);
  };

  const takesOf = (target: Target) => (kept?.takes ?? []).filter((take) => (target === "comparison" ? take.about === "comparison" : take.pointId === target));

  const send = async (input: { takes?: KeepTakeDto[]; hiddenPoints?: string[] }, fallback: string) => {
    if (!comparisonId) return false;
    setPhase("pending");
    setFailure(null);
    try {
      const result = await api.readerLibraryCompareKeep({ askId: table.askId, comparisonId, ...input });
      setKept(result.kept);
      if (result.kept.hiddenPoints) setHidden(result.kept.hiddenPoints);
      setPhase("idle");
      keepCtx?.onChanged();
      return true;
    } catch (error) {
      setPhase("failed");
      setFailure(errorMessage(error, fallback));
      return false;
    }
  };

  const keep = async () => {
    if (!canKeep || kept) return;
    const takes: KeepTakeDto[] = Object.entries(drafts).filter(([, text]) => text.trim()).map(([target, text]) =>
      (target === "comparison" ? { text: text.trim(), about: "comparison" as const } : { text: text.trim(), pointId: target }));
    if (await send({ takes, hiddenPoints: hidden }, "Couldn't keep this comparison. Nothing was saved; try again.")) setDrafts({});
  };

  const remove = async () => {
    if (!kept || !comparisonId) return;
    setPhase("pending");
    setFailure(null);
    try {
      await api.readerLibraryCompareRemove({ askId: kept.askId, comparisonId });
      setKept(null);
      setPhase("removed");
      keepCtx?.onChanged();
    } catch (error) {
      setPhase("failed");
      setFailure(errorMessage(error, "Couldn't remove it; it is still kept."));
    }
  };

  const toggleHidden = (pointId: string) => {
    const next = hidden.includes(pointId) ? hidden.filter((id) => id !== pointId) : [...hidden, pointId];
    if (kept && canKeep) {
      // After a keep, hiding supersedes the row's proposals; showing proposes it again.
      void send({ hiddenPoints: next }, "Couldn't change that row; the comparison is as it was.");
    } else {
      setHidden(next);
    }
  };

  const openTake = (target: Target) => {
    if (!keepCtx) return;
    setTakeOpen(target);
    setTakeText(drafts[target] ?? "");
  };

  const submitTake = async (target: Target) => {
    const text = takeText.trim();
    if (!text) {
      setTakeOpen(null);
      return;
    }
    if (kept && canKeep) {
      const take: KeepTakeDto = target === "comparison" ? { text, about: "comparison" } : { text, pointId: target };
      if (await send({ takes: [take] }, "Couldn't keep your take; it is still in the box.")) {
        setTakeOpen(null);
        setTakeText("");
      }
      return;
    }
    // Before a keep, the take waits in its row and goes with the keep.
    setDrafts((current) => ({ ...current, [target]: text }));
    setTakeOpen(null);
    setTakeText("");
  };

  const toggle = (list: string[], value: string) => (list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);

  /** What the focused cell is: a row header, a book's cell, or the learner's column. */
  const cellAt = (at: CellPosition): { point: ComparePointDto | null; column: number | null } => {
    if (byBook) {
      return { point: at.col > 0 ? shownPoints[at.col - 1] ?? null : null, column: at.col > 0 ? at.row : null };
    }
    const point = points[at.row] ?? null;
    return { point, column: at.col >= 1 && at.col <= columns.length ? at.col - 1 : null };
  };

  const quotedCell = (point: ComparePointDto | null, column: number | null): ComparePointCellDto | null => {
    if (!point || column === null) return null;
    const cell = point.cells.find((entry) => entry.key === columns[column]?.key);
    return cell && cell.status === "quoted" ? cell : null;
  };

  const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("input, textarea, select")) {
      if (event.key === "Escape" && takeOpen !== null) {
        event.preventDefault();
        event.stopPropagation();
        setTakeOpen(null);
        moved.current = true;
        setFocus({ ...focus });
      }
      return;
    }
    if (event.ctrlKey || event.metaKey || event.altKey) return; // Ctrl+↵ is the tutor's (the host's)
    const next = moveCell(focus, event.key, rowCount, colsOf);
    if (next) {
      event.preventDefault();
      event.stopPropagation();
      moved.current = true;
      setFocus(next);
      return;
    }
    const { point, column } = cellAt(focus);
    const cell = quotedCell(point, column);
    const handled = () => {
      event.preventDefault();
      event.stopPropagation();
    };
    switch (event.key) {
      case " ":
        // Space is the grid's peek: it never scrolls the pane, peekable or not.
        event.preventDefault();
        if (cell?.spanKey && actions.onPeek) {
          handled();
          actions.onPeek({ spanKey: cell.spanKey, sourceTitle: columns[column!]?.sourceTitle ?? null });
        }
        return;
      case "o":
        if (cell?.spanKey && actions.onOpen) {
          handled();
          actions.onOpen({ sourceId: columns[column!]?.sourceId ?? null, ...splitKey(cell.spanKey) });
        }
        return;
      case "Enter":
        if (cell && point) {
          handled();
          setExpanded((list) => toggle(list, `${point.id}|${cell.key}`));
        } else if (point && column === null && !byBook) {
          handled();
          setPairsOpen((list) => toggle(list, point.id));
        }
        return;
      case "t":
        if (point && keepCtx && !notFound(point) && !hidden.includes(point.id)) {
          handled();
          openTake(point.id);
        }
        return;
      case "-":
        if (point && !byBook) {
          handled();
          toggleHidden(point.id);
        }
        return;
      case "v":
        handled();
        moved.current = true;
        setFocus({ row: 0, col: 0 });
        setLayout(byBook ? "by_point" : "by_book");
        return;
      case "k":
        if (canKeep && !kept) {
          handled();
          void keep();
        }
        return;
      case "Escape":
        if (point && (pairsOpen.includes(point.id) || expanded.some((entry) => entry.startsWith(`${point.id}|`)))) {
          handled();
          setPairsOpen((list) => list.filter((id) => id !== point.id));
          setExpanded((list) => list.filter((entry) => !entry.startsWith(`${point.id}|`)));
        }
        return;
      default:
    }
  };

  const cellProps = (row: number, col: number, label: string) => ({
    "data-cell": `${row}:${col}`,
    tabIndex: focus.row === row && focus.col === col ? 0 : -1,
    "aria-label": label,
    onFocus: () => {
      if (focus.row !== row || focus.col !== col) setFocus({ row, col });
    },
    style: { outlineOffset: 1 } as const,
  });

  const question = table.scope?.question ?? table.query ?? null;
  const firstModelPoint = points.findIndex((point) => point.kind === "point");

  const quote = (point: ComparePointDto, cell: ComparePointCellDto) => {
    const open = expanded.includes(`${point.id}|${cell.key}`);
    const text = cell.quote ?? "";
    const long = text.length > CLAMP_CHARS;
    return (
      <div data-cell-voice="source" style={sourceRule}>
        <span aria-hidden="true" style={{ color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10 }}>§ </span>
        <span data-quote="" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.5,
          ...(open || !long ? {} : { display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as const, overflow: "hidden" }) }}>
          “{text}”
        </span>
        {long ? (
          <button type="button" tabIndex={-1} style={quietStyle} onClick={() => setExpanded((list) => toggle(list, `${point.id}|${cell.key}`))}>
            {open ? POINT_COPY.less : POINT_COPY.more}
          </button>
        ) : null}
      </div>
    );
  };

  const bookCell = (point: ComparePointDto, column: number): ReactNode => {
    const cell = point.cells.find((entry) => entry.key === columns[column].key);
    if (!cell || cell.status !== "quoted") {
      return <MeaningLabel style={{ fontSize: 11 }}>— {point.kind === "perspective" ? POINT_COPY.notHere : POINT_COPY.notAddressed}</MeaningLabel>;
    }
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {quote(point, cell)}
        {cell.line ? (
          <div data-cell-voice="model" style={modelRule}>
            <span aria-hidden="true" style={{ color: COLOR.purpleText, fontFamily: FONT_MONO, fontSize: 10 }}>◇ </span>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>{cell.line}</span>
          </div>
        ) : null}
      </div>
    );
  };

  const cellLabel = (point: ComparePointDto, column: number): string => {
    const title = columns[column].sourceTitle ?? "a source";
    const cell = point.cells.find((entry) => entry.key === columns[column].key);
    if (!cell || cell.status !== "quoted") {
      return `${title}, on ${point.label}: ${point.kind === "perspective" ? POINT_COPY.notHere : POINT_COPY.notAddressed}.`;
    }
    return `${title}, on ${point.label}. From the book: ${cell.quote ?? ""} LearnLoop's reading: ${cell.line ?? ""}`;
  };

  const chips = (point: ComparePointDto) => {
    const list = rowChips(point, titles);
    if (!list.length) return null;
    const pairs = chipPairs(point);
    const open = pairsOpen.includes(point.id);
    return (
      <span data-chips="" style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {list.map((chip) => (
          chip.kind === "only" || !pairs.length ? (
            <span key={chip.label} data-chip={chip.kind === "only" ? "only" : chip.relation}
              aria-label={`LearnLoop's reading of how they relate: ${chip.label}.`}
              style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.purpleText }}>{chip.label}</span>
          ) : (
            <button key={chip.label} type="button" tabIndex={-1} data-chip={chip.relation} aria-expanded={open}
              aria-label={`LearnLoop's reading of how they relate: ${chip.label}.`}
              onClick={() => setPairsOpen((current) => toggle(current, point.id))} style={chipStyle}>
              {chip.label}
            </button>
          )
        ))}
      </span>
    );
  };

  const pairsBand = (point: ComparePointDto) => {
    if (!pairsOpen.includes(point.id) || !point.relations.length) return null;
    return (
      <div data-pairs={point.id} style={{ ...modelRule, display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.purpleText }}>▾ {POINT_COPY.pairsHead}</span>
        {chipPairs(point).map((pair, index) => (
          <span key={`${pair.leftKey}|${pair.rightKey}|${index}`} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
            {titles.get(pair.leftKey) ?? "a source"} ⇄ {titles.get(pair.rightKey) ?? "a source"} · {fineLabel(pair.relation)}
            {pair.statement ? <span style={{ color: COLOR.textDim }}> · ◇ {pair.statement}</span> : null}
            {pair.leftQuote || pair.rightQuote ? (
              <span style={{ display: "block", color: COLOR.textDim, fontSize: 10 }}>§ “{pair.leftQuote ?? ""}” / § “{pair.rightQuote ?? ""}”</span>
            ) : null}
          </span>
        ))}
      </div>
    );
  };

  const rowHeader = (point: ComparePointDto, index: number) => {
    const learner = point.labelVoice === "learner";
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <div data-row-voice={learner ? "learner" : "model"} style={learner ? learnerRule : modelRule}>
          <span aria-hidden="true" style={{ color: learner ? COLOR.amber : COLOR.purpleText, fontFamily: FONT_MONO, fontSize: 10 }}>{learner ? "› " : "◇ "}</span>
          {!learner && index === firstModelPoint ? (
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.purpleText }}>{POINT_COPY.firstPoint} · </span>
          ) : null}
          <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{point.label}</span>
          {notFound(point) ? <MeaningLabel style={{ fontSize: 11 }}> · {POINT_COPY.notFound}</MeaningLabel> : null}
        </div>
        {chips(point)}
        {notFound(point) && actions.onWhereElse ? (
          <button type="button" tabIndex={-1} style={linkStyle} onClick={() => actions.onWhereElse?.(point.label)}>{POINT_COPY.whereElse}</button>
        ) : null}
        <button type="button" tabIndex={-1} style={{ ...quietStyle, alignSelf: "flex-start" }} onClick={() => toggleHidden(point.id)}
          aria-label={`${POINT_COPY.hide}: ${point.label}`}>- {POINT_COPY.hide}</button>
      </div>
    );
  };

  const takeBox = (target: Target, placeholder: string) => (
    <form onSubmit={(event) => { event.preventDefault(); void submitTake(target); }} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <input
        ref={takeRef}
        value={takeText}
        onChange={(event) => setTakeText(event.target.value)}
        placeholder={placeholder}
        aria-label={target === "comparison" ? "your take on the whole comparison" : "your take on this row"}
        maxLength={1000}
        style={{ fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "2px 6px", width: "100%", boxSizing: "border-box" }}
      />
      <span style={{ display: "flex", gap: 8 }}>
        <button type="button" tabIndex={-1} style={quietStyle} aria-expanded={why} onClick={() => setWhy((value) => !value)}>{KEEP_COPY.whereThisGoes}</button>
      </span>
      {why ? <MeaningLabel>{KEEP_COPY.whereLine}</MeaningLabel> : null}
    </form>
  );

  const youCell = (target: Target) => {
    if (takeOpen === target) return takeBox(target, target === "comparison" ? POINT_COPY.wholePlaceholder : POINT_COPY.takePlaceholder);
    const takes = takesOf(target);
    const draft = drafts[target];
    if (!takes.length && !draft) return null;
    return (
      <div data-cell-voice="learner" style={{ ...learnerRule, display: "flex", flexDirection: "column", gap: 2 }}>
        {takes.map((take) => (
          <span key={take.id} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
            <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>{take.learnerText}
          </span>
        ))}
        {draft ? (
          <span data-draft="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
            <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>{draft} <MeaningLabel>· {POINT_COPY.draft}</MeaningLabel>
          </span>
        ) : null}
      </div>
    );
  };

  const hiddenRow = (point: ComparePointDto, row: number) => (
    <div role="row" key={point.id} data-point={point.id} data-hidden="" style={{ padding: "4px 0", borderTop: `1px solid ${COLOR.border}` }}>
      <div role="rowheader" {...cellProps(row, 0, `${POINT_COPY.hidden(point.label)}. Press minus to show it.`)}>
        <MeaningLabel style={{ fontSize: 11 }}>
          {POINT_COPY.hidden(point.label)} ·{" "}
          <button type="button" tabIndex={-1} style={linkStyle} onClick={() => toggleHidden(point.id)}>{POINT_COPY.show}</button>
        </MeaningLabel>
      </div>
    </div>
  );

  const grid = () => {
    const template = `${POINT_COLUMN_PX}px repeat(${columns.length}, minmax(${READABLE_CELL_PX}px, 1fr)) ${YOU_COLUMN_PX}px`;
    const stickyHead = { position: "sticky" as const, left: 0, background: COLOR.bg, zIndex: 1 };
    return (
      <div data-grid-scroll="" style={{ overflowX: "auto", maxWidth: "100%" }}>
        <div role="grid" aria-label="how your books treat this, by point" aria-rowcount={points.length + 1}
          aria-colcount={columns.length + 2} data-compare-grid="" style={{ display: "flex", flexDirection: "column", minWidth: "max-content" }}>
          <div role="row" style={{ display: "grid", gridTemplateColumns: template, gap: 10, paddingBottom: 4 }}>
            <span role="columnheader" style={{ ...headStyle, ...stickyHead }}><span aria-hidden="true">◇ </span>{POINT_COPY.pointHead}</span>
            {columns.map((column) => (
              <span role="columnheader" key={column.key} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                <span aria-hidden="true">§ </span>{column.isOpenSource ? "your passage · " : ""}{column.sourceTitle ?? "a source"}{column.page !== null ? ` p.${column.page}` : ""}
              </span>
            ))}
            <span role="columnheader" style={headStyle}><span aria-hidden="true">› </span>{POINT_COPY.you}</span>
          </div>
          {points.map((point, row) => (hidden.includes(point.id) ? hiddenRow(point, row) : (
            <div role="row" key={point.id} data-point={point.id} style={{ borderTop: `1px solid ${COLOR.border}`, padding: "8px 0", display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "grid", gridTemplateColumns: template, gap: 10, alignItems: "start" }}>
                <div role="rowheader" {...cellProps(row, 0, point.label)} style={{ ...stickyHead, outlineOffset: 1 }}>{rowHeader(point, row)}</div>
                {columns.map((column, index) => (
                  <div role="gridcell" key={column.key} {...cellProps(row, index + 1, cellLabel(point, index))}>{bookCell(point, index)}</div>
                ))}
                <div role="gridcell" {...cellProps(row, columns.length + 1, `your take on ${point.label}`)}>{youCell(point.id)}</div>
              </div>
              {pairsBand(point)}
            </div>
          )))}
        </div>
      </div>
    );
  };

  const cardsView = () => (
    <div role="grid" aria-label="how your books treat this, by point" data-compare-cards="" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {points.map((point, row) => (hidden.includes(point.id) ? hiddenRow(point, row) : (
        <div role="row" key={point.id} data-point={point.id} style={{ border: `1px solid ${COLOR.border}`, padding: "8px 10px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div role="rowheader" {...cellProps(row, 0, point.label)}>{rowHeader(point, row)}</div>
          {pairsBand(point)}
          {columns.map((column, index) => (
            <div role="gridcell" key={column.key} {...cellProps(row, index + 1, cellLabel(point, index))} style={{ display: "flex", flexDirection: "column", gap: 3, outlineOffset: 1 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}><span aria-hidden="true">§ </span>{column.sourceTitle ?? "a source"}</span>
              {bookCell(point, index)}
            </div>
          ))}
          <div role="gridcell" {...cellProps(row, columns.length + 1, `your take on ${point.label}`)}>
            {youCell(point.id) ?? <MeaningLabel style={{ fontSize: 10 }}>› {POINT_COPY.you}</MeaningLabel>}
          </div>
        </div>
      )))}
      <MeaningLabel style={{ fontSize: 10 }}>{POINT_COPY.cardKeys}</MeaningLabel>
    </div>
  );

  const byBookView = () => (
    <div role="grid" aria-label="how your books treat this, by book" data-compare-by-book="" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {columns.map((column, row) => (
        <div role="row" key={column.key} data-book={column.key} style={{ border: `1px solid ${COLOR.border}`, padding: "8px 10px", display: "flex", flexDirection: "column", gap: 8 }}>
          <span role="rowheader" {...cellProps(row, 0, column.sourceTitle ?? "a source")} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, outlineOffset: 1 }}>
            <span aria-hidden="true">§ </span>{column.sourceTitle ?? "a source"}{column.page !== null ? ` · p.${column.page}` : ""}
          </span>
          {shownPoints.map((point, index) => (
            <div role="gridcell" key={point.id} {...cellProps(row, index + 1, cellLabel(point, row))} style={{ display: "flex", flexDirection: "column", gap: 3, outlineOffset: 1 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: point.labelVoice === "learner" ? COLOR.amber : COLOR.purpleText }}>
                <span aria-hidden="true">{point.labelVoice === "learner" ? "› " : "◇ "}</span>{point.label}
              </span>
              {bookCell(point, row)}
            </div>
          ))}
        </div>
      ))}
    </div>
  );

  const unverified = table.unverifiedSources ?? [];
  return (
    <div data-compare-points="" data-layout={byBook ? "by_book" : cards ? "cards" : "grid"} ref={frameRef} onKeyDown={onKeyDown}
      style={{ display: "flex", flexDirection: "column", gap: 10, minWidth: 0 }}>
      <span style={{ ...headStyle, letterSpacing: "0.12em" }}>
        compare · {columns.map((column) => column.sourceTitle ?? "a source").join(" · ")}{question ? ` · on: ${question}` : ""} · {POINT_COPY.header}
      </span>
      <div style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        <span role="group" aria-label="layout" style={{ display: "flex", gap: 6, fontFamily: FONT_MONO, fontSize: 10 }}>
          <button type="button" style={{ ...linkStyle, textDecoration: "none", color: byBook ? COLOR.textDim : COLOR.text }} aria-pressed={!byBook}
            onClick={() => setLayout("by_point")}>{POINT_COPY.byPoint} {byBook ? "○" : "●"}</button>
          <span aria-hidden="true" style={{ color: COLOR.textDim }}>·</span>
          <button type="button" style={{ ...linkStyle, textDecoration: "none", color: byBook ? COLOR.text : COLOR.textDim }} aria-pressed={byBook}
            onClick={() => setLayout("by_book")}>{POINT_COPY.byBook} {byBook ? "●" : "○"}</button>
        </span>
        {canKeep ? (
          kept ? (
            <>
              <span data-kept="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amber }}>{KEEP_COPY.kept}</span>
              <MeaningLabel>{KEEP_COPY.proposals}</MeaningLabel>
              <button type="button" style={quietStyle} disabled={phase === "pending"} onClick={() => void remove()}>{KEEP_COPY.remove}</button>
            </>
          ) : (
            <button type="button" style={linkStyle} disabled={phase === "pending"} onClick={() => void keep()}>{KEEP_COPY.keep}</button>
          )
        ) : null}
        {phase === "pending" ? <MeaningLabel><span aria-hidden="true">◐</span> {KEEP_COPY.keeping}…</MeaningLabel> : null}
      </div>
      {phase === "removed" && !kept ? <MeaningLabel>{KEEP_COPY.removed}</MeaningLabel> : null}
      {phase === "failed" && failure ? <span role="status"><MeaningLabel>{failure}</MeaningLabel></span> : null}
      {byBook ? byBookView() : cards ? cardsView() : grid()}
      {/* The table's foot: a take on the whole comparison, uncompared books, left-out pins. */}
      <div style={{ display: "flex", flexDirection: "column", gap: 4, borderTop: `1px solid ${COLOR.border}`, paddingTop: 6 }}>
        {keepCtx ? (
          <div data-take-whole="" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <span style={headStyle}><span aria-hidden="true">› </span>{POINT_COPY.aboutWhole}</span>
            {youCell("comparison") ?? (
              <button type="button" style={{ ...linkStyle, alignSelf: "flex-start" }} onClick={() => openTake("comparison")}>{KEEP_COPY.addTake}</button>
            )}
          </div>
        ) : null}
        {unverified.map((entry, index) => (
          <MeaningLabel key={`${entry.sourceId ?? "source"}-${index}`} style={{ fontSize: 11 }}>
            § {entry.sourceTitle ?? entry.sourceId ?? "a source"} · {POINT_COPY.possible}
          </MeaningLabel>
        ))}
        {table.alsoDiscussedIn.length ? (
          <MeaningLabel style={{ fontSize: 11 }}>
            {POINT_COPY.alsoIn}: {table.alsoDiscussedIn.map((entry) => String(entry.sourceTitle ?? entry.sourceId ?? "a source")).join(", ")}
          </MeaningLabel>
        ) : null}
        {table.droppedPins.length ? (
          <MeaningLabel style={{ fontSize: 11 }}>
            {POINT_COPY.leftOut}: {table.droppedPins.map((pin) => String(pin.reason ?? "not available")).join("; ")}
          </MeaningLabel>
        ) : null}
        {!cards || byBook ? <MeaningLabel style={{ fontSize: 10 }}>{POINT_COPY.keys}</MeaningLabel> : null}
      </div>
      <SpokenOnly><span role="status" aria-live="polite">{POINT_COPY.ready(points.length)}</span></SpokenOnly>
    </div>
  );
}

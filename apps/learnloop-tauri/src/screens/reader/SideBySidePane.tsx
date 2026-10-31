// Reader CA6: side by side's second pane, and the narrow window's peek sheet
// (ux_reader_compare_ask_v1 §6.4, X9).
//
//   § Axler · 5.C Eigenspaces…        follow along ● (^⇧L)   ✕
//   (no matching section here · stays put)
//   the section's text …
//   ‹ 5.B …                                          5.D … ›
//
// The pane says when it leads (the learner last scrolled, clicked or selected
// in it) and when it found no matching section and stays put. Nothing in it
// animates or takes focus on its own (C5): a follow-along move swaps the
// section and puts the pane at its top, instantly. Selecting in it offers
// CA3's selection verb, naming the other pane's book.
import { forwardRef, useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { COLOR, FONT_MONO } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import { clip } from "./readerShared";
import { MeaningLabel } from "./voices";
import { SIDE_BY_SIDE_COPY, type SideBySide } from "./useSideBySide";

const LINK: CSSProperties = {
  border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 10,
  color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2,
};

/** A selection inside the pane: its passages (the anchor) and its words (the question). */
export interface PaneSelection {
  spanIds: string[];
  quote: string;
}

export interface SideBySidePaneProps {
  ctl: SideBySide;
  /** The main pane's book (CA3's verb names it as the source). */
  otherTitle: string;
  /** CA3's "how do my other books treat this?" on a selection here (null: off). */
  onCompareSelection: ((selection: PaneSelection) => void) | null;
  /** The pane's share of the width (two panes, a flex grow against the main pane's); ignored by the sheet. */
  grow?: number;
}

function selectionIn(root: HTMLElement | null): PaneSelection | null {
  const sel = window.getSelection();
  if (!root || !sel || sel.isCollapsed || sel.rangeCount === 0) return null;
  const range = sel.getRangeAt(0);
  if (!root.contains(range.commonAncestorContainer)) return null;
  const quote = sel.toString().replace(/\s+/g, " ").trim();
  if (!quote) return null;
  const spans: string[] = [];
  root.querySelectorAll<HTMLElement>("[data-sbs-span]").forEach((node) => {
    if (range.intersectsNode(node) && node.dataset.sbsSpan) spans.push(node.dataset.sbsSpan);
  });
  return spans.length ? { spanIds: spans, quote } : null;
}

export const SideBySidePane = forwardRef<HTMLDivElement, SideBySidePaneProps>(function SideBySidePane(
  { ctl, otherTitle, onCompareSelection, grow = 1 },
  bodyRef,
) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [selection, setSelection] = useState<PaneSelection | null>(null);
  const target = ctl.target;
  const section = ctl.section && target && ctl.section.sectionId === target.sectionId ? ctl.section : null;
  const sheet = ctl.sheet;
  const leads = ctl.panes && ctl.leader === "side";

  // A new section starts at its top (its jump locator), instantly: no animation.
  useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = 0;
    setSelection(null);
  }, [section?.extractionId, section?.sectionId]);

  const setRefs = useCallback((node: HTMLDivElement | null) => {
    scrollRef.current = node;
    if (typeof bodyRef === "function") bodyRef(node);
    else if (bodyRef) bodyRef.current = node;
  }, [bodyRef]);

  if (!target) return null;
  const touch = () => ctl.touch("side");
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape" && !event.defaultPrevented) {
      event.preventDefault();
      event.stopPropagation();
      ctl.close();
      return;
    }
    // Scrolling the pane with the keyboard is the learner's hand on it too.
    if (["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "].includes(event.key)) touch();
  };

  const header: ReactNode = (
    <div data-sbs-header="" style={{ display: "flex", alignItems: "baseline", gap: 8, padding: "6px 14px", borderBottom: `1px solid ${COLOR.border}`, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, flexShrink: 0 }}>
      <span style={{ color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }} title={`${target.sourceTitle} · ${target.title}`}>
        § {target.sourceTitle} · {clip(target.title, 60)}
      </span>
      {leads ? <span data-sbs-lead="" style={{ color: COLOR.amber }}>{SIDE_BY_SIDE_COPY.lead}</span> : null}
      <span style={{ marginLeft: "auto", display: "inline-flex", gap: 10, alignItems: "baseline", flexShrink: 0 }}>
        {ctl.panes ? (
          <button type="button" onClick={ctl.toggleFollow} aria-pressed={ctl.follow} title="follow along (Ctrl+Shift+L)" style={LINK}>
            {ctl.follow ? SIDE_BY_SIDE_COPY.followOn : SIDE_BY_SIDE_COPY.followOff} {SIDE_BY_SIDE_COPY.followKey}
          </button>
        ) : null}
        <button type="button" onClick={ctl.close} aria-label={SIDE_BY_SIDE_COPY.close} title={`${SIDE_BY_SIDE_COPY.close} (Ctrl+\\ or Esc)`} style={{ ...LINK, textDecoration: "none", fontSize: 12 }}>✕</button>
      </span>
    </div>
  );

  return (
    <div
      data-side-by-side-pane={sheet ? "sheet" : "pane"}
      role="region"
      aria-label={`${target.sourceTitle}, ${target.title}`}
      onKeyDown={onKeyDown}
      style={sheet ? {
        position: "absolute", left: 0, right: 0, bottom: 0, height: "50%", zIndex: 30, background: COLOR.bg,
        borderTop: `1px solid ${COLOR.borderStrong}`, display: "flex", flexDirection: "column", minHeight: 0,
      } : {
        flex: `${grow} 1 0`, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column",
        borderLeft: `1px solid ${COLOR.border}`,
      }}
    >
      {header}
      {sheet ? <div style={{ padding: "4px 14px" }}><MeaningLabel>{SIDE_BY_SIDE_COPY.narrow}</MeaningLabel></div> : null}
      {ctl.staysPut === "side" ? <div data-sbs-stays-put="" style={{ padding: "4px 14px" }}><MeaningLabel>{SIDE_BY_SIDE_COPY.staysPut}</MeaningLabel></div> : null}
      {target.by === "search" ? <div style={{ padding: "4px 14px" }}><MeaningLabel>{SIDE_BY_SIDE_COPY.unchecked}</MeaningLabel></div> : null}
      <div
        ref={setRefs}
        tabIndex={-1}
        data-sbs-body=""
        className="ll-scroll"
        onWheel={touch}
        onTouchMove={touch}
        onMouseDown={touch}
        onMouseUp={() => {
          const picked = selectionIn(scrollRef.current);
          if (picked) touch();
          setSelection(picked);
        }}
        style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "14px 24px", display: "flex", flexDirection: "column", gap: 10, outline: "none" }}
      >
        {ctl.phase === "failed" ? (
          <MeaningLabel>{SIDE_BY_SIDE_COPY.failed}</MeaningLabel>
        ) : !section ? (
          <MeaningLabel>{SIDE_BY_SIDE_COPY.loading}</MeaningLabel>
        ) : (
          section.blocks.map((block) => (
            <div key={block.spanId} data-sbs-span={block.spanId} style={block.blockType === "SectionHeader" ? { fontWeight: 600 } : undefined}>
              <MarkdownMath value={block.text} />
            </div>
          ))
        )}
        {section && !sheet && (section.previous || section.next) ? (
          <div style={{ display: "flex", gap: 8, paddingTop: 8, borderTop: `1px solid ${COLOR.border}` }}>
            {section.previous ? (
              <button type="button" onClick={() => ctl.goSide(section.previous!.sectionId)} style={LINK} aria-label={`previous section: ${section.previous.title}`}>
                {SIDE_BY_SIDE_COPY.previous} {clip(section.previous.title, 40)}
              </button>
            ) : null}
            {section.next ? (
              <button type="button" onClick={() => ctl.goSide(section.next!.sectionId)} style={{ ...LINK, marginLeft: "auto" }} aria-label={`next section: ${section.next.title}`}>
                {clip(section.next.title, 40)} {SIDE_BY_SIDE_COPY.next}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      {selection && onCompareSelection && section ? (
        <div data-sbs-selection="" style={{ display: "flex", gap: 8, alignItems: "baseline", padding: "6px 14px", borderTop: `1px solid ${COLOR.border}` }}>
          <button type="button" onClick={() => { onCompareSelection(selection); setSelection(null); }} style={LINK}>
            how do my other books treat this?
          </button>
          <MeaningLabel>{otherTitle}</MeaningLabel>
        </div>
      ) : null}
      {sheet ? null : <div style={{ padding: "4px 14px", borderTop: `1px solid ${COLOR.border}` }}><MeaningLabel>{SIDE_BY_SIDE_COPY.keys}</MeaningLabel></div>}
    </div>
  );
});

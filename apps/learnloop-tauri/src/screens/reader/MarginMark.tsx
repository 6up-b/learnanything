// Reader workbench RW3a: a margin mark and its popover, and the Guide's
// footer control for the marks' density (spec §6.1; UX §3.4, §4.4, §7).
//
// A thin mark in the gutter (`◌┆`), quiet by construction: drawn with a CSS
// glyph (no text node, so a selection or a marquee never quotes it), never
// animated, never focused by LearnLoop. Hover or focus shows its fixed note
// and "because" line; Enter (or a click) opens the popover with open, check
// me, not relevant…, fewer marks like this and marks off. Esc closes it and
// returns focus to the mark. Every action is the learner's; a switched-off
// action is absent, never disabled.
//
// A mark counts as shown when the learner could see it (review F6): once at
// least half of it is in the reading area (the webview's intersection, so a
// mark below the fold, or on a page not reached, is never "shown"), or when
// the learner hovers, focuses or opens it.
import { useEffect, useRef, useState } from "react";
import type { CueDensity, ReaderCueDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { CUE_COPY, CUE_DENSITIES, DISCOVERED_COPY, markClass } from "./cues";
import { observerGeneration } from "./observerGeneration";
import { LearnerVoice, MeaningLabel, ModelVoice } from "./voices";

export type CueCheckPhase = "idle" | "finding" | "none" | "failed";

export interface MarginMarkProps {
  cue: ReaderCueDto;
  /** The popover is open (one at a time). */
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Where the mark is drawn: the text view's gutter, the original's overlay, a transcript. */
  surface: "text" | "pdf" | "watch";
  /** "Check me" can open an item (the shell provides the way there). */
  canCheckMe: boolean;
  checkPhase: CueCheckPhase;
  onOpenEarlier: () => void;
  onCheckMe: () => void;
  onNotRelevant: (text: string) => void;
  onFewer: () => void;
  onOffBook: () => void;
  onOffEverywhere: () => void;
  /** The mark came into the learner's view (or was hovered, focused or
   *  opened); the controller counts it once per visit. `planId`: the cue plan
   *  the sighting was made under (RW3b; null while discovery is off). */
  onSeen?: (planId?: string | null) => void;
  /** RW3b: the cue plan served now (absent or null while discovery is off).
   *  Its observer is rebuilt for each plan and a sighting is sent under the
   *  plan its observer was built for, never a later one (Codex verify F22). */
  planId?: string | null;
  /** RW3b: "try the next step first" on a try-first cue (RW1b's next-step
   *  question at that line); absent: no such action (W11). */
  onTryFirst?: () => void;
}

/** At least this share of the mark in view counts as seen. */
const SEEN_THRESHOLD = 0.5;

/** The label over the learner's own words a gap was named from (RW3b). */
function yourWords(kind: string | null | undefined): string {
  const labels: Record<string, string> = DISCOVERED_COPY.yourWords;
  return labels[kind ?? ""] ?? DISCOVERED_COPY.yourWords.other;
}

const ACTION_STYLE = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: "2px 0",
  cursor: "pointer",
  textAlign: "left" as const,
};

export function MarginMark({
  cue,
  open,
  onOpenChange,
  surface,
  canCheckMe,
  checkPhase,
  onOpenEarlier,
  onCheckMe,
  onNotRelevant,
  onFewer,
  onOffBook,
  onOffEverywhere,
  onSeen,
  onTryFirst,
  planId = null,
}: MarginMarkProps) {
  const markRef = useRef<HTMLButtonElement | null>(null);
  const firstActionRef = useRef<HTMLButtonElement | null>(null);
  const [noteShown, setNoteShown] = useState(false);
  const [earlierShown, setEarlierShown] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);
  const [why, setWhy] = useState("");
  const onSeenRef = useRef(onSeen);
  onSeenRef.current = onSeen;
  const planRef = useRef(planId);
  planRef.current = planId;
  const seen = () => onSeenRef.current?.(planRef.current);

  // Shown means seen: the mark's own visibility in the reading area, not its
  // placement (review F6). Without IntersectionObserver only the learner's
  // hover, focus or click counts.
  useEffect(() => {
    const node = markRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    if (planId === null) {
      // Discovery off: RW3a's observer, verbatim, a delivery the browser had
      // buffered before the disconnect included (Codex verify F23).
      const observer = new IntersectionObserver(
        (entries) => {
          if (!entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= SEEN_THRESHOLD)) return;
          observer.disconnect();
          onSeenRef.current?.();
        },
        { threshold: SEEN_THRESHOLD },
      );
      observer.observe(node);
      return () => observer.disconnect();
    }
    // RW3b, discovery on (Codex verify F22): one observer generation per cue
    // plan. Its callback is bound, in this closure, to the plan it was built
    // for and to that render's onSeen; a callback delivered after its
    // observer was disconnected is discarded, and the next plan's observer
    // measures the mark again.
    const planForGeneration = planId;
    const notify = onSeen;
    const generation = observerGeneration();
    generation.observe([node], SEEN_THRESHOLD, (entries, observer) => {
      if (!entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= SEEN_THRESHOLD)) return;
      generation.disconnect(observer);
      notify?.(planForGeneration);
    });
    return () => generation.disconnectAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cue.cueId, planId]);

  // The learner opened it: their act, so focus goes into the popover.
  useEffect(() => {
    if (open) firstActionRef.current?.focus({ preventScroll: true });
    else {
      setEarlierShown(false);
      setWhyOpen(false);
      setWhy("");
    }
  }, [open]);

  const close = () => {
    onOpenChange(false);
    markRef.current?.focus({ preventScroll: true });
  };
  const earlier = cue.earlier;
  // RW3b: a cue LearnLoop's model found (absent while discovery is off).
  const discovered = cue.foundBy === "model";
  const tryFirst = discovered && cue.kind === "try_first" && onTryFirst ? onTryFirst : null;
  const onPage = surface === "pdf";
  // The text view's gutter is the column's left padding; the original's
  // overlay and a transcript's time column place the mark themselves.
  const slot = surface === "text"
    ? { position: "absolute" as const, left: -26, top: 3 }
    : surface === "pdf"
      ? { position: "absolute" as const, left: 0, top: 0 }
      : { position: "relative" as const, display: "inline-block", verticalAlign: "top" };
  return (
    <span
      data-cue-slot={cue.cueId}
      style={{ ...slot, zIndex: open ? 30 : 4 }}
      onMouseDown={(event) => event.stopPropagation()}
      onMouseUp={(event) => event.stopPropagation()}
    >
      <button
        ref={markRef}
        type="button"
        data-cue-mark={cue.cueId}
        data-cue-span={cue.spanId}
        {...(discovered ? { "data-cue-kind": cue.kind } : {})}
        aria-label={cue.label}
        aria-expanded={open}
        className={markClass(cue)}
        onClick={() => {
          seen();
          onOpenChange(!open);
        }}
        onFocus={() => {
          seen();
          setNoteShown(true);
        }}
        onBlur={() => setNoteShown(false)}
        onMouseEnter={() => {
          seen();
          setNoteShown(true);
        }}
        onMouseLeave={() => setNoteShown(false)}
        onKeyDown={(event) => {
          if (event.key === "Escape" && open) {
            event.stopPropagation();
            close();
          }
        }}
        style={{
          width: 20,
          height: 20,
          padding: 0,
          border: onPage ? `1px solid ${COLOR.border}` : 0,
          background: onPage ? COLOR.bg : "transparent",
          color: COLOR.purpleText,
          fontFamily: FONT_MONO,
          fontSize: 13,
          lineHeight: "18px",
          cursor: "pointer",
        }}
      />
      {noteShown && !open ? (
        <span
          role="note"
          data-cue-note={cue.cueId}
          style={{
            position: "absolute",
            left: 24,
            top: 0,
            width: 280,
            display: "flex",
            flexDirection: "column",
            gap: 3,
            padding: "6px 8px",
            background: COLOR.bg,
            border: `1px solid ${COLOR.border}`,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: COLOR.text,
            lineHeight: 1.45,
          }}
        >
          <span>{cue.note}</span>
          <MeaningLabel>{cue.because}</MeaningLabel>
        </span>
      ) : null}
      {open ? (
        <span
          role="group"
          aria-label={CUE_COPY.popoverLabel}
          data-cue-popover={cue.cueId}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.stopPropagation();
              close();
            }
          }}
          style={{
            position: "absolute",
            left: 24,
            top: 0,
            width: 320,
            display: "flex",
            flexDirection: "column",
            gap: 4,
            padding: "8px 10px",
            background: COLOR.bg,
            border: `1px solid ${COLOR.borderStrong}`,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: COLOR.text,
            lineHeight: 1.45,
          }}
        >
          <span>{cue.note}</span>
          <MeaningLabel>{cue.because}</MeaningLabel>
          {tryFirst ? (
            <button ref={firstActionRef} type="button" onClick={tryFirst} style={ACTION_STYLE}>
              {DISCOVERED_COPY.tryFirst} · {DISCOVERED_COPY.tryFirstHint}
            </button>
          ) : null}
          <button
            ref={tryFirst ? undefined : firstActionRef}
            type="button"
            aria-expanded={earlierShown}
            onClick={() => {
              if (!earlierShown) onOpenEarlier();
              setEarlierShown((shown) => !shown);
            }}
            style={ACTION_STYLE}
          >
            {CUE_COPY.open} · {CUE_COPY.openTitle}
          </button>
          {earlierShown && discovered ? (
            <span data-cue-earlier="" style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 8 }}>
              {cue.quote ? (
                <span style={{ color: COLOR.textDim }}>
                  {DISCOVERED_COPY.quoteLabel}: “{cue.quote}”
                </span>
              ) : null}
              {/* The earlier work the target was read from (Codex review F12): the
                  cited answer and the question it answered, and the learner's own
                  words a gap was named from, in the learner's voice. */}
              {earlier.attemptId ? (
                <MeaningLabel>
                  {earlier.answeredOn ? `${CUE_COPY.answeredOn} ${earlier.answeredOn}.` : CUE_COPY.answeredUndated}
                </MeaningLabel>
              ) : null}
              {earlier.prompt ? (
                <span style={{ color: COLOR.textDim }}>
                  {CUE_COPY.question}: “{earlier.prompt}”
                </span>
              ) : null}
              {earlier.answer ? (
                <LearnerVoice label={CUE_COPY.yourAnswer}>
                  <span style={{ whiteSpace: "pre-wrap", fontSize: 11 }}>{earlier.answer}</span>
                </LearnerVoice>
              ) : null}
              {earlier.learnerText ? (
                <LearnerVoice label={yourWords(earlier.learnerTextKind)}>
                  <span style={{ whiteSpace: "pre-wrap", fontSize: 11 }}>{earlier.learnerText}</span>
                </LearnerVoice>
              ) : null}
              {earlier.statement ? <ModelVoice note={DISCOVERED_COPY.statementNote}>{earlier.statement}</ModelVoice> : null}
              <MeaningLabel>{DISCOVERED_COPY.foundBy}</MeaningLabel>
            </span>
          ) : null}
          {earlierShown && !discovered ? (
            <span data-cue-earlier="" style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 8 }}>
              <MeaningLabel>
                {earlier.answeredOn ? `${CUE_COPY.answeredOn} ${earlier.answeredOn}.` : CUE_COPY.answeredUndated}
              </MeaningLabel>
              {earlier.prompt ? (
                <span style={{ color: COLOR.textDim }}>
                  {CUE_COPY.question}: “{earlier.prompt}”
                </span>
              ) : null}
              {earlier.answer ? (
                <LearnerVoice label={CUE_COPY.yourAnswer}>
                  <span style={{ whiteSpace: "pre-wrap", fontSize: 11 }}>{earlier.answer}</span>
                </LearnerVoice>
              ) : null}
              {earlier.statement ? (
                <ModelVoice note={CUE_COPY.readingNote}>{earlier.statement}</ModelVoice>
              ) : earlier.statementPending ? (
                <MeaningLabel>{CUE_COPY.readingPending}</MeaningLabel>
              ) : null}
            </span>
          ) : null}
          {canCheckMe ? (
            <span style={{ display: "flex", flexDirection: "column" }}>
              <button
                type="button"
                onClick={onCheckMe}
                disabled={checkPhase === "finding"}
                style={ACTION_STYLE}
              >
                {CUE_COPY.checkMe} · {CUE_COPY.checkMeHint}
              </button>
              {checkPhase === "finding" ? <MeaningLabel>{CUE_COPY.checkMeFinding}</MeaningLabel> : null}
              {checkPhase === "none" ? <MeaningLabel>{CUE_COPY.checkMeNone}</MeaningLabel> : null}
              {checkPhase === "failed" ? (
                <MeaningLabel>
                  {CUE_COPY.checkMeFailed}{" "}
                  <button type="button" onClick={onCheckMe} style={{ ...ACTION_STYLE, fontSize: 10, display: "inline" }}>
                    {CUE_COPY.tryAgain}
                  </button>
                </MeaningLabel>
              ) : null}
            </span>
          ) : null}
          <button type="button" aria-expanded={whyOpen} onClick={() => setWhyOpen((value) => !value)} style={ACTION_STYLE}>
            {CUE_COPY.notRelevant}
          </button>
          {whyOpen ? (
            <span style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 8 }}>
              <textarea
                aria-label={CUE_COPY.notRelevantWhy}
                placeholder={CUE_COPY.notRelevantWhy}
                value={why}
                onChange={(event) => setWhy(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") onNotRelevant(why.trim());
                }}
                style={{ fontFamily: FONT_MONO, fontSize: 11, minHeight: 44, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 4, resize: "vertical" }}
              />
              <MeaningLabel>{CUE_COPY.notRelevantWhere}</MeaningLabel>
              <button type="button" onClick={() => onNotRelevant(why.trim())} style={ACTION_STYLE}>
                {CUE_COPY.send}
              </button>
            </span>
          ) : null}
          <button type="button" onClick={onFewer} style={ACTION_STYLE}>{CUE_COPY.fewer}</button>
          <span style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button type="button" onClick={onOffBook} style={ACTION_STYLE}>{CUE_COPY.offBook}</button>
            <button type="button" onClick={onOffEverywhere} style={ACTION_STYLE}>{CUE_COPY.offEverywhere}</button>
          </span>
          <button type="button" onClick={close} style={{ ...ACTION_STYLE, color: COLOR.textDim }}>
            {CUE_COPY.close} · esc
          </button>
        </span>
      ) : null}
    </span>
  );
}

export interface CueReceipt {
  /** Stable per receipt: a mark set aside is keyed by its cue. */
  id: string;
  label: string;
  /** What it was about, when the label alone would not say (a mark's topic). */
  detail?: string | null;
  onUndo: () => void;
}

/** The Guide's footer: the marks' density, the legend and the receipts, each
 *  with its undo (a mark set aside keeps its own until the learner leaves the
 *  book; a preference's is the latest one). */
export function CueFooter({
  density,
  bookOff,
  receipts,
  onDensity,
  onTurnOnBook,
  discovered,
}: {
  density: CueDensity;
  bookOff: boolean;
  receipts: readonly CueReceipt[];
  onDensity: (density: CueDensity) => void;
  onTurnOnBook: () => void;
  /** RW3b: discovered cues are on (the legend names their marks too). */
  discovered?: { tryFirst: boolean } | null;
}) {
  const [legend, setLegend] = useState(false);
  return (
    <div data-cue-footer="" style={{ marginTop: 16, paddingTop: 10, borderTop: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 4 }}>
      <div role="group" aria-label={CUE_COPY.footerLabel} style={{ display: "flex", alignItems: "baseline", gap: 6, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 11 }}>
        <span style={{ color: COLOR.textDim }}>{CUE_COPY.footerLabel}:</span>
        {CUE_DENSITIES.map((option, index) => (
          <span key={option} style={{ display: "inline-flex", gap: 6 }}>
            {index > 0 ? <span aria-hidden="true" style={{ color: COLOR.textDim }}>·</span> : null}
            <button
              type="button"
              aria-pressed={density === option}
              onClick={() => onDensity(option)}
              style={{ ...ACTION_STYLE, padding: 0, color: density === option ? COLOR.text : COLOR.amberLink, textDecoration: density === option ? "none" : "underline", textUnderlineOffset: 2 }}
            >
              {density === option ? `●${option}` : option}
            </button>
          </span>
        ))}
      </div>
      <MeaningLabel>{CUE_COPY.footerLimit}</MeaningLabel>
      {bookOff ? (
        <MeaningLabel>
          {CUE_COPY.bookOff}{" "}
          <button type="button" onClick={onTurnOnBook} style={{ ...ACTION_STYLE, fontSize: 10, display: "inline" }}>{CUE_COPY.turnOn}</button>
        </MeaningLabel>
      ) : null}
      {receipts.map((receipt) => (
        <MeaningLabel key={receipt.id}>
          <span data-cue-receipt="">{receipt.label}</span>
          {receipt.detail ? <span> · {receipt.detail}</span> : null}{" "}
          <button type="button" onClick={receipt.onUndo} style={{ ...ACTION_STYLE, fontSize: 10, display: "inline" }}>{CUE_COPY.undo}</button>
        </MeaningLabel>
      ))}
      <button type="button" aria-expanded={legend} onClick={() => setLegend((value) => !value)} style={{ ...ACTION_STYLE, fontSize: 10 }}>
        {CUE_COPY.legendToggle} {legend ? "▾" : "▸"}
      </button>
      {legend ? (
        <span style={{ display: "flex", gap: 8, fontFamily: FONT_MONO, fontSize: 11 }}>
          <span aria-hidden="true" style={{ color: COLOR.purpleText }}>{CUE_COPY.glyph}</span>
          <MeaningLabel>{CUE_COPY.legendRevisit}</MeaningLabel>
        </span>
      ) : null}
      {legend && discovered ? (
        <span data-cue-legend-discovered="" style={{ display: "flex", flexDirection: "column", gap: 2, fontFamily: FONT_MONO, fontSize: 11 }}>
          {([["distinction", DISCOVERED_COPY.legendDistinction], ["application", DISCOVERED_COPY.legendApplication],
            ...(discovered.tryFirst ? [["try_first", DISCOVERED_COPY.legendTryFirst]] : [])] as Array<[keyof typeof DISCOVERED_COPY.glyphs, string]>)
            .map(([kind, text]) => (
              <span key={kind} style={{ display: "flex", gap: 8 }}>
                <span aria-hidden="true" style={{ color: COLOR.purpleText }}>{DISCOVERED_COPY.glyphs[kind]}</span>
                <MeaningLabel>{text}</MeaningLabel>
              </span>
            ))}
        </span>
      ) : null}
    </div>
  );
}

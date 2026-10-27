// Reader CA5a: "find this section in my other books" (ux_reader_compare_ask_v1
// §6.2, §6.3, X7). A pressed action in the Guide's footer over C0a's
// reader.correspondents: for a section with no judged coverage, the live search
// hits grouped by book, each line "found by search, not checked" and never a
// treatment word. Peek opens the section's first blocks in the rail, go there
// opens the book at the section (a detour: Alt+← comes back), compare runs the
// library compare path on both sections' passages, and "not about this" is
// C0a's correction (one learner row per LO of this section, with undo).
//
// Hidden when the section already has judged coverage (its one-line entry is
// CA5's, not built yet), when it is protected, and whenever the quiet read
// fails. Pressing it is the only read that searches; nothing here calls a
// model, and the correction is the only write. Unchecked hits never appear
// unasked (§6.5). Off (no `correspondence` in the prompt contract) the Reader
// never mounts this, so the Guide is exactly as before.
import { useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { api } from "../../api/client";
import type { CorrespondentSectionDto, CorrespondentsDto, SpanViewDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { clip } from "./readerShared";
import { MeaningLabel, SourceVoice } from "./voices";

export const FIND_COPY = {
  action: "find this section in my other books ▸",
  title: "in your other books",
  looking: "◐ looking in your other books…",
  unchecked: "found by search, not checked",
  nothing: "Nothing in your other books matched this section by search.",
  failed: "Couldn't look in your other books just now.",
  retry: "try again",
  read: "read",
  peek: "peek",
  goThere: "go there",
  compare: "compare",
  notAbout: "not about this",
  notAboutDone: "not about this",
  undo: "undo",
  whereThisGoes: "ⓘ where this goes",
  whereThisGoesText: "Tells LearnLoop which sections treat what, so these lines get better. It isn't read for gaps in your understanding — and never grades you.",
  peekHead: "peek",
  closePeek: "esc close",
  keys: "↑↓ move · space peek · ↵ go there · c compare · esc close",
  fold: "close",
} as const;

export interface FindSectionOrigin {
  /** The guide section in view (its id is the unit id coverage reads). */
  id: string;
  label: string;
  startSpanId: string;
}

export interface FindSectionProps {
  extractionId: string;
  section: FindSectionOrigin | null;
  /** Opens the other book at the hit (a detour with a way back). */
  onGoThere: (target: { sourceId: string; extractionId: string; spanId: string }) => void;
  /** Compares this section's passage with the hit's (null: comparing is off). */
  onCompare: ((hit: CorrespondentSectionDto) => void) | null;
  onError: (message: string) => void;
}

type Pressed =
  | { sectionId: string; phase: "pending"; view: null }
  | { sectionId: string; phase: "landed"; view: CorrespondentsDto }
  | { sectionId: string; phase: "failed"; view: null };

interface Peek {
  key: string;
  hit: CorrespondentSectionDto;
  view: SpanViewDto | null;
}

export function hitKey(hit: Pick<CorrespondentSectionDto, "extractionId" | "sectionId">): string {
  return `${hit.extractionId}/${hit.sectionId}`;
}

const LINK: CSSProperties = {
  border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 10,
  color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2,
};
const HEAD: CSSProperties = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim, textTransform: "uppercase" };

export function FindSection({ extractionId, section, onGoThere, onCompare, onError }: FindSectionProps) {
  const sectionId = section?.id ?? null;
  // The quiet read (no search): whether the action may show for this section.
  const [quiet, setQuiet] = useState<{ sectionId: string; show: boolean } | null>(null);
  const [pressed, setPressed] = useState<Pressed | null>(null);
  const [peek, setPeek] = useState<Peek | null>(null);
  // Hits the learner said are not about this section: key → the LOs corrected (for undo).
  const [dismissed, setDismissed] = useState<Map<string, { hit: CorrespondentSectionDto; los: string[] }>>(new Map());
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [why, setWhy] = useState(false);
  const lineRefs = useRef<Map<string, HTMLButtonElement>>(new Map());
  const token = useRef(0);

  useEffect(() => {
    const mine = ++token.current;
    setPressed(null);
    setPeek(null);
    setDismissed(new Map());
    setWhy(false);
    if (!sectionId) {
      setQuiet(null);
      return;
    }
    setQuiet(null);
    api.readerCorrespondents({ extractionId, sectionId, searchFallback: false }).then((view) => {
      if (token.current !== mine) return;
      // Judged coverage is CA5's one-line entry (not built yet): no action then;
      // a protected section has none at all.
      setQuiet({ sectionId, show: view.status !== "judged" && view.status !== "withheld" });
    }).catch(() => {
      // Fails closed: no action rather than an error line nobody asked for.
      if (token.current === mine) setQuiet({ sectionId, show: false });
    });
  }, [extractionId, sectionId]);

  const press = useCallback(() => {
    if (!sectionId) return;
    const mine = token.current;
    setPressed({ sectionId, phase: "pending", view: null });
    setPeek(null);
    api.readerCorrespondents({ extractionId, sectionId, searchFallback: true }).then((view) => {
      if (token.current !== mine) return;
      if (view.status === "judged" || view.status === "withheld") {
        // Coverage was judged meanwhile (or the section is protected now): CA5's, not this list.
        setQuiet({ sectionId, show: false });
        setPressed(null);
        return;
      }
      setPressed({ sectionId, phase: "landed", view });
    }).catch(() => {
      if (token.current === mine) setPressed({ sectionId, phase: "failed", view: null });
    });
  }, [extractionId, sectionId]);

  const fold = useCallback(() => {
    setPressed(null);
    setPeek(null);
  }, []);

  const view = pressed?.phase === "landed" ? pressed.view : null;
  const correctable = view?.search?.correctableLearningObjectIds ?? [];
  const sources = (view?.search?.sources ?? []).map((source) => ({
    ...source, sections: source.sections.filter((hit) => hit.by === "search"),
  })).filter((source) => source.sections.length > 0);
  const lines = sources.flatMap((source) => source.sections);
  const liveLines = lines.filter((hit) => !dismissed.has(hitKey(hit)));

  const focusLine = (key: string) => window.requestAnimationFrame(() => lineRefs.current.get(key)?.focus({ preventScroll: false }));

  const openPeek = useCallback(async (hit: CorrespondentSectionDto) => {
    const key = hitKey(hit);
    if (!hit.jump.spanId) return;
    setPeek({ key, hit, view: null });
    try {
      const { spanView } = await api.getSpanView({ extractionId: hit.jump.extractionId, spanId: hit.jump.spanId, context: "library" });
      setPeek((current) => (current?.key === key ? { key, hit, view: spanView } : current));
    } catch (error) {
      onError(errorMessage(error));
      setPeek((current) => (current?.key === key ? null : current));
    }
  }, [onError]);

  const closePeek = useCallback(() => {
    const key = peek?.key;
    setPeek(null);
    if (key) focusLine(key);
  }, [peek]);

  const goThere = useCallback((hit: CorrespondentSectionDto) => {
    if (!hit.jump.spanId) return;
    onGoThere({ sourceId: hit.sourceId, extractionId: hit.jump.extractionId, spanId: hit.jump.spanId });
  }, [onGoThere]);

  const notAbout = useCallback(async (hit: CorrespondentSectionDto) => {
    const key = hitKey(hit);
    if (correctable.length === 0 || busyKey) return;
    setBusyKey(key);
    const done: string[] = [];
    try {
      for (const lo of correctable) {
        await api.curriculumCoverageCorrect({ extractionId: hit.extractionId, sectionId: hit.sectionId, learningObjectId: lo, choice: "not_about" });
        done.push(lo);
      }
      setDismissed((current) => new Map(current).set(key, { hit, los: done }));
      if (peek?.key === key) setPeek(null);
    } catch (error) {
      onError(errorMessage(error));
      // A correction half made is taken back, so the line means one thing.
      for (const lo of done) {
        await api.curriculumCoverageCorrect({ extractionId: hit.extractionId, sectionId: hit.sectionId, learningObjectId: lo, choice: "none" }).catch(() => undefined);
      }
    } finally {
      setBusyKey(null);
    }
  }, [correctable, busyKey, onError, peek]);

  const undo = useCallback(async (key: string) => {
    const entry = dismissed.get(key);
    if (!entry || busyKey) return;
    setBusyKey(key);
    try {
      for (const lo of entry.los) {
        await api.curriculumCoverageCorrect({ extractionId: entry.hit.extractionId, sectionId: entry.hit.sectionId, learningObjectId: lo, choice: "none" });
      }
      setDismissed((current) => {
        const next = new Map(current);
        next.delete(key);
        return next;
      });
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusyKey(null);
    }
  }, [dismissed, busyKey, onError]);

  const onListKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target as HTMLElement;
    const keyOf = target.closest<HTMLElement>("[data-find-line]")?.dataset.findLine ?? null;
    const index = keyOf ? liveLines.findIndex((hit) => hitKey(hit) === keyOf) : -1;
    // Space, ↵ and c act on the line whose title has focus; on any other
    // button (peek, not about this, undo…) they keep the button's own press.
    const hit = index >= 0 && target.dataset.findTitle !== undefined ? liveLines[index] : null;
    const consume = () => {
      event.preventDefault();
      event.stopPropagation();
    };
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (liveLines.length === 0) return;
      consume();
      const next = index < 0 ? 0 : (index + (event.key === "ArrowDown" ? 1 : -1) + liveLines.length) % liveLines.length;
      focusLine(hitKey(liveLines[next]));
    } else if (event.key === " " && hit) {
      consume();
      void openPeek(hit);
    } else if (event.key === "Enter" && hit) {
      consume();
      goThere(hit);
    } else if ((event.key === "c" || event.key === "C") && hit && onCompare) {
      consume();
      onCompare(hit);
    } else if (event.key === "Escape") {
      consume();
      if (peek) closePeek();
      else fold();
    }
  };

  if (!section || !quiet || quiet.sectionId !== section.id || !quiet.show) return null;

  if (!pressed || pressed.sectionId !== section.id) {
    return (
      <div data-find-section="" style={{ marginTop: 12 }}>
        <button type="button" onClick={press} style={{ ...LINK, fontSize: 11 }}>{FIND_COPY.action}</button>
      </div>
    );
  }

  return (
    <div data-find-section="" onKeyDown={onListKey} style={{ marginTop: 12, paddingTop: 8, borderTop: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={HEAD}>{FIND_COPY.title}</span>
        <button type="button" onClick={fold} style={{ ...LINK, marginLeft: "auto" }}>{FIND_COPY.fold}</button>
      </div>
      {pressed.phase === "pending" ? (
        <MeaningLabel>{FIND_COPY.looking}</MeaningLabel>
      ) : pressed.phase === "failed" ? (
        <MeaningLabel>
          {FIND_COPY.failed}{" "}
          <button type="button" onClick={press} style={LINK}>{FIND_COPY.retry}</button>
        </MeaningLabel>
      ) : lines.length === 0 ? (
        <MeaningLabel>{FIND_COPY.nothing}</MeaningLabel>
      ) : (
        <div role="list" aria-label={FIND_COPY.title} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {sources.map((source) => (
            <div key={source.sourceId} role="group" aria-label={source.sourceTitle} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>{source.sourceTitle}</span>
              {source.sections.map((hit) => {
                const key = hitKey(hit);
                const gone = dismissed.get(key);
                if (gone) {
                  return (
                    <div key={key} role="listitem" data-find-gone={key} style={{ paddingLeft: 10, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "baseline" }}>
                      <MeaningLabel>{clip(hit.title, 60)} · {FIND_COPY.notAboutDone}</MeaningLabel>
                      <button type="button" onClick={() => void undo(key)} disabled={busyKey === key} style={LINK}>{FIND_COPY.undo}</button>
                      <button type="button" onClick={() => setWhy((open) => !open)} aria-expanded={why} style={LINK}>{FIND_COPY.whereThisGoes}</button>
                      {why ? <MeaningLabel style={{ flexBasis: "100%" }}>{FIND_COPY.whereThisGoesText}</MeaningLabel> : null}
                    </div>
                  );
                }
                const peeking = peek?.key === key;
                return (
                  <div key={key} role="listitem" data-find-line={key} style={{ paddingLeft: 10, display: "flex", flexDirection: "column", gap: 2, borderLeft: `2px solid ${peeking ? COLOR.amber : "transparent"}` }}>
                    <button
                      type="button"
                      ref={(node) => {
                        if (node) lineRefs.current.set(key, node);
                        else lineRefs.current.delete(key);
                      }}
                      data-find-title=""
                      onClick={() => void openPeek(hit)}
                      title={`${source.sourceTitle} · ${hit.title}`}
                      style={{ border: 0, background: "transparent", padding: 0, textAlign: "left", cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    >
                      § {hit.title}
                    </button>
                    <MeaningLabel>
                      {hit.label ?? FIND_COPY.unchecked}{hit.read ? ` · ${FIND_COPY.read}` : ""}
                    </MeaningLabel>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button type="button" onClick={() => void openPeek(hit)} style={LINK} aria-label={`${FIND_COPY.peek} at ${source.sourceTitle} ${hit.title}`}>{FIND_COPY.peek}</button>
                      <button type="button" onClick={() => goThere(hit)} style={LINK} aria-label={`${FIND_COPY.goThere}: ${source.sourceTitle} ${hit.title}`}>{FIND_COPY.goThere} ↵</button>
                      {onCompare ? (
                        <button type="button" onClick={() => onCompare(hit)} style={LINK} aria-label={`${FIND_COPY.compare} with ${source.sourceTitle} ${hit.title}`}>{FIND_COPY.compare}</button>
                      ) : null}
                      {correctable.length > 0 ? (
                        <button type="button" onClick={() => void notAbout(hit)} disabled={busyKey === key} style={LINK} aria-label={`${FIND_COPY.notAbout}: ${source.sourceTitle} ${hit.title}`}>⋯ {FIND_COPY.notAbout}</button>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
          <MeaningLabel>{FIND_COPY.keys}</MeaningLabel>
        </div>
      )}
      {peek ? (
        <div data-find-peek={peek.key} style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <span style={HEAD}>{FIND_COPY.peekHead}</span>
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>§ {peek.hit.sourceTitle} · {clip(peek.hit.title, 50)}</span>
          </div>
          {peek.view ? (
            <SourceVoice source={peek.hit.sourceTitle} locator={peek.view.page !== null ? `p.${peek.view.page}` : null}>
              {[peek.view.text, ...peek.view.nextSpans.map((span) => span.text)].slice(0, 3).map((text, index) => (
                <p key={index} style={{ margin: "0 0 6px", ...(index === 0 ? { outline: `1px solid ${COLOR.borderStrong}`, outlineOffset: 2 } : {}) }}>{clip(text, 700)}</p>
              ))}
            </SourceVoice>
          ) : (
            <MeaningLabel>◐</MeaningLabel>
          )}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" onClick={() => goThere(peek.hit)} style={LINK}>{FIND_COPY.goThere} ↵</button>
            {onCompare ? <button type="button" onClick={() => onCompare(peek.hit)} style={LINK}>{FIND_COPY.compare} with {clip(section.label, 30)} (c)</button> : null}
            <button type="button" onClick={closePeek} style={LINK}>{FIND_COPY.closePeek}</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

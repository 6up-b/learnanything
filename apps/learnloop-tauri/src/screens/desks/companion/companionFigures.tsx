// Show me in the companion (spec §13.1): a figure the Show me verb built appears in the companion as
// "◇ Show me · a figure for <source> p.<page>", the live widget itself (the Reader's FigureInline, open, its
// parameters shared with every other instance of the figure), and three buttons: view source, move to scratchpad
// (a `figure` block in the running pad of the desk it was asked on) and not useful (removed, and logged). The footer
// says what it is: help, not a check. The figures live outside the companion (per vault), so hiding and showing it
// keeps them.
import { useMemo, useState, useSyncExternalStore } from "react";
import { api } from "../../../api/client";
import type { FigureViewDto } from "../../../api/dto";
import { logReaderAction } from "../../reader/activity";
import { FigureInline } from "../../reader/figures/FigureInline";
import { figurePlacementKey, type FiguresContract, type FiguresCtl } from "../../reader/figures/useFigures";

export const COMPANION_FIGURE_COPY = {
  lead: "◇ Show me",
  viewSource: "view source",
  hideSource: "hide source",
  move: "move to pad",
  notUseful: "not useful",
  footer: "◇ LearnLoop's figure, made ahead from this passage · display tier, no kernel · it is help, not a check",
  noSource: "this figure has no source to show",
  sourceNote: "the figure's source · display tier, no kernel",
} as const;

export interface CompanionFigure {
  key: string;
  figure: FigureViewDto;
  /** The passage it was asked on, and the running pad of the desk it was asked on (captured when asked). */
  anchor: { extractionId: string | null; spanId: string | null };
  destination: string | null;
  /** The book's title where the figure's passages do not name it. */
  sourceTitle: string | null;
}

const byScope = new Map<string, CompanionFigure[]>();
const listeners = new Set<() => void>();
const NONE: CompanionFigure[] = [];

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function companionFigures(scope: string): CompanionFigure[] {
  return byScope.get(scope) ?? NONE;
}

/** The scope's figures, re-rendered as they change. */
export function useCompanionFigures(scope: string): CompanionFigure[] {
  return useSyncExternalStore(subscribe, () => companionFigures(scope));
}

/** A figure Show me built, newest first. */
export function showInCompanion(scope: string, entry: CompanionFigure): void {
  byScope.set(scope, [entry, ...companionFigures(scope).filter((each) => each.figure.figureId !== entry.figure.figureId)]);
  emit();
}

export function removeCompanionFigure(scope: string, key: string): void {
  byScope.set(scope, companionFigures(scope).filter((each) => each.key !== key));
  emit();
}

/** Tests only. */
export function resetCompanionFiguresForTests(): void {
  byScope.clear();
  emit();
}

/** "a figure for <source> p.<page>" from the figure's own first passage, else the book it was asked in. */
export function figureForLine(entry: CompanionFigure): string {
  const passage = entry.figure.passages?.[0] ?? null;
  const source = passage?.sourceTitle || entry.sourceTitle || "this passage";
  const page = passage?.page;
  return `a figure for ${source}${page !== null && page !== undefined ? ` p.${page}` : ""}`;
}

export interface CompanionFigureHost {
  /** "move to scratchpad": a `figure` block in the desk's running pad. */
  moveToPad: (entry: CompanionFigure) => void | Promise<void>;
  /** "open the page" of a checked element's equation. */
  openSource?: (extractionId: string, spanId: string) => void;
}

const CONTRACT: FiguresContract = { predictions: true, region: false, revisions: false, showMe: true };

function pretty(specJson: string | null | undefined): string | null {
  if (!specJson) return null;
  try {
    return JSON.stringify(JSON.parse(specJson), null, 2);
  } catch {
    return specJson;
  }
}

function CompanionFigureItem({ scope, entry, host }: { scope: string; entry: CompanionFigure; host: CompanionFigureHost }) {
  const [figure, setFigure] = useState(entry.figure);
  const [source, setSource] = useState(false);
  const [moving, setMoving] = useState(false);
  // The widget is open in the companion; predictions are recorded as the Reader's are.
  const ctl = useMemo<FiguresCtl>(() => {
    const patch = (found: { figureId: string; predictionIndex: number }) => setFigure((now) => now.figureId !== found.figureId ? now
      : { ...now, predictions: now.predictions.map((prediction) => prediction.index === found.predictionIndex ? { ...prediction, answered: found as never } : prediction) });
    return {
      enabled: true, contract: CONTRACT, figures: [figure], pending: [], expandedKey: figurePlacementKey(figure),
      setExpanded: () => undefined,
      request: async () => "skipped",
      revise: () => undefined,
      predict: async (shown, index, answer) => {
        const found = await api.readerFigurePredict({ figureId: shown.figureId, predictionIndex: index, answer });
        patch(found);
        return found;
      },
      explain: async (_shown, predictionId, text) => {
        if (!text.trim()) return null;
        const found = await api.readerFigureExplain({ predictionId, text });
        patch(found);
        return found;
      },
      under: () => ({ figures: [], pending: [], richPending: [], followed: [] }),
      followed: [], follow: async () => false, richPending: [], cancelRich: () => undefined, retryRich: () => undefined,
      manimOptIn: null, optInSpanId: null, answerManimOptIn: () => undefined,
      ...(host.openSource ? { openSource: host.openSource } : {}),
    };
  }, [figure, host.openSource]);
  const code = pretty(figure.specJson);
  return (
    <div className="cfig" data-companion-figure={figure.figureId} role="group" aria-label={`${COMPANION_FIGURE_COPY.lead} · ${figureForLine(entry)}`}>
      <div className="cfig-head">
        <span className="cfig-lead">{COMPANION_FIGURE_COPY.lead}</span> · {figureForLine(entry)}
      </div>
      <div className="cfig-widget">
        <FigureInline figure={figure} ctl={ctl} />
      </div>
      <div className="cfig-actions">
        <button type="button" aria-expanded={source} onClick={() => setSource((open) => !open)}>
          {source ? COMPANION_FIGURE_COPY.hideSource : COMPANION_FIGURE_COPY.viewSource}
        </button>
        <button type="button" disabled={moving} onClick={() => {
          setMoving(true);
          void Promise.resolve(host.moveToPad(entry)).then(() => removeCompanionFigure(scope, entry.key), () => setMoving(false));
        }}>
          {COMPANION_FIGURE_COPY.move}
        </button>
        <button type="button" onClick={() => {
          logReaderAction("figure_not_useful", { figure_id: figure.figureId, extraction_id: figure.extractionId });
          removeCompanionFigure(scope, entry.key);
        }}>
          {COMPANION_FIGURE_COPY.notUseful}
        </button>
      </div>
      {source ? (
        <div className="cfig-source" data-figure-source="">
          <div className="cfig-source-note">{COMPANION_FIGURE_COPY.sourceNote}</div>
          {code ? <pre>{code}</pre> : <div>{COMPANION_FIGURE_COPY.noSource}</div>}
        </div>
      ) : null}
      <div className="cfig-foot">{COMPANION_FIGURE_COPY.footer}</div>
    </div>
  );
}

/** The companion's figures, newest first (nothing when there are none). */
export function CompanionFigures({ scope, host }: { scope: string; host: CompanionFigureHost }) {
  const entries = useCompanionFigures(scope);
  if (!entries.length) return null;
  return (
    <div className="cfigs" data-companion-figures="">
      {entries.map((entry) => <CompanionFigureItem key={entry.key} scope={scope} entry={entry} host={host} />)}
    </div>
  );
}

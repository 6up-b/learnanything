// Reader RW5d P3 (spec_reader_show_me_figures_v1 §6.4, §11.2-§11.4): "show me ▸"
// in the CA2 Ask panel on practice, feedback and the Reader workbench.
//
// The box says what a figure costs before it is sent, in the CA2 vocabulary:
// free on feedback; one hint on an open attempt (once per figure, however
// often it is opened again; the server counts it at Submit); on a check on
// your own, sending it is the take step: the attempt converts first (banner
// "Practice with help ◌ — you asked for a figure"), then the figure is built.
// The figure lands in the panel's thread at panel width, with "widen ↔".
// Nothing here moves focus or starts on its own (W12). Rendered only while
// the sidecar sends `ask.figures` (figures.help_kind_enabled).
//
// Ruling R1 (landing): figures here are grammar and sketch only. No rich
// (Manim) build, fuller version or rich revision is asked, polled or opened
// on an attempt host; animations stay in the Reader.
import { useCallback, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { api } from "../api/client";
import type { FigureHelpDto, FigureHostRef, FigureViewDto, LibraryJobDto, FigureBuildResultDto } from "../api/dto";
import { algoConfig } from "../app/algoConfig";
import { errorMessage } from "../errors";
import { FigureInline } from "../screens/reader/figures/FigureInline";
import { figurePlacementKey, type FiguresContract, type FiguresCtl } from "../screens/reader/figures/useFigures";
import { showMeSourceLine } from "../screens/reader/figures/showMe";
import type { AskTarget } from "./AskOverlay";
import { COLOR, FONT_MONO } from "./term";

export const PANEL_FIGURE_COPY = {
  send: "show me ▸",
  keys: "alt+↵ show me ▸",
  free: "show me is free here",
  counts: "a figure on this counts as a hint",
  cold: "a figure on this makes this practice with help ◌",
  pending: "◐ building an interactive version · keep working · it stays here in Ask",
  landed: "▸ interactive version",
  countsLine: "counts as a hint",
  freeLine: "free",
  widen: "widen ↔",
  narrow: "narrow ↔",
  failed: "couldn't build an interactive version of this",
  notRecorded: "couldn't be recorded on this attempt just now, so it isn't shown; try again",
  banner: "Practice with help ◌ — you asked for a figure",
  explore: "▸ a figure to explore",
  open: "open",
  disabled: "figures on practice are switched off, so it isn't shown"
} as const;

const FIGURE_POLL_MS = 400;

// UX-3 (audit seasoned-1 #74-81): the panel unmounts when it closes, and a
// figure still building was lost with it. Its lines, its take-step token and
// whether the check converted are kept per attempt here, outside the panel,
// so the panel opened again on the same attempt shows the figure (or that it
// is still building). Kept in memory for this run of the app only.
interface PanelFigureHostState {
  lines: PanelFigureLine[];
  converted: boolean;
  token: { key: string; token: string } | null;
  /** The figure open in the thread (a figure that landed while closed is open on return). */
  expandedKey: string | null;
}

const NO_FIGURES: PanelFigureHostState = { lines: [], converted: false, token: null, expandedKey: null };
const panelFigureHosts = new Map<string, PanelFigureHostState>();
const panelFigureListeners = new Set<() => void>();

function updateHost(hostKey: string, change: (state: PanelFigureHostState) => PanelFigureHostState): void {
  if (!hostKey) return;
  panelFigureHosts.set(hostKey, change(panelFigureHosts.get(hostKey) ?? NO_FIGURES));
  for (const listener of panelFigureListeners) listener();
}

/** The take-step token kept for a host, read when a request is made: two requests in one
 *  render must see the same token, or the second would take the step again. */
function keptTokenOf(hostKey: string): { key: string; token: string } | null {
  return panelFigureHosts.get(hostKey)?.token ?? null;
}

function subscribeHosts(listener: () => void): () => void {
  panelFigureListeners.add(listener);
  return () => { panelFigureListeners.delete(listener); };
}

/** Forget every kept figure line (tests). */
export function clearPanelFigures(): void {
  panelFigureHosts.clear();
  for (const listener of panelFigureListeners) listener();
}

/** Whether the panel offers *show me ▸* on this host (the sidecar's switch). */
export function panelFiguresOn(target: AskTarget | null): boolean {
  if (!target || !algoConfig().ask?.figures) return false;
  if (target.context === "feedback") return Boolean(target.attemptId);
  return target.context === "practice" && Boolean(target.practiceItemId);
}

/** The host's references (each verified on the server, §7.1). */
export function figureHostRef(target: AskTarget): FigureHostRef | null {
  if (target.context === "feedback") return target.attemptId ? { attemptId: target.attemptId } : null;
  if (!target.practiceItemId) return null;
  if (target.workbenchSessionId) return { itemId: target.practiceItemId, workbenchSessionId: target.workbenchSessionId };
  if (!target.submissionId || !target.sessionId) return null;
  return { itemId: target.practiceItemId, submissionId: target.submissionId, sessionId: target.sessionId };
}

/** The dim line under the box (§6.4), said before sending. */
export function figureCostLine(target: AskTarget, cold: boolean, converted: boolean): string {
  if (target.context === "feedback") return PANEL_FIGURE_COPY.free;
  return cold && !converted ? PANEL_FIGURE_COPY.cold : PANEL_FIGURE_COPY.counts;
}

export interface PanelFigureLine {
  key: string;
  goal: string;
  state: "pending" | "landed" | "failed";
  figure: FigureViewDto | null;
  help: FigureHelpDto | null;
  message: string | null;
}

/** What a figure did to the attempt, for the host (its help record and cold banner). */
export interface PanelFigureEvent {
  /** A new hint-equivalent was counted (the figure was new to this attempt). */
  counted: boolean;
  /** The take step converted a check on your own. */
  converted: boolean;
  banner?: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function settle(start: () => Promise<LibraryJobDto<FigureBuildResultDto>>): Promise<FigureBuildResultDto | null> {
  let job = await start();
  while (job.state === "pending") {
    await sleep(FIGURE_POLL_MS);
    job = await api.readerFigureJob({ jobId: job.jobId });
  }
  return job.state === "done" ? job.result ?? null : null;
}

/** The panel's figures: the requests of this panel, their lines, and the
 *  controller the figure frame draws with (predictions, "not right?"). */
export function usePanelFigures(target: AskTarget | null, { cold, onEvent, chooser = false }: {
  cold: boolean;
  onEvent?: (event: PanelFigureEvent) => void;
  /** The hint chooser's explore_figure line (§11.4): it opens its figure
   *  whether or not the Ask panel is on (the server checks the switch). */
  chooser?: boolean;
}) {
  const enabled = chooser ? Boolean(target?.practiceItemId) : panelFiguresOn(target);
  // UX-3: this host's lines live outside the panel (the chooser's apart from Ask's).
  const hostRef = target ? figureHostRef(target) : null;
  const hostKey = enabled && hostRef ? `${chooser ? "hint" : "ask"}|${JSON.stringify(hostRef)}` : "";
  const hostState = useSyncExternalStore(subscribeHosts, () => panelFigureHosts.get(hostKey) ?? NO_FIGURES);
  const { lines, converted, expandedKey } = hostState;
  const setLines = useCallback((change: (list: PanelFigureLine[]) => PanelFigureLine[], host: string = hostKey) =>
    updateHost(host, (state) => ({ ...state, lines: change(state.lines) })), [hostKey]);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const attemptKey = target ? `${target.submissionId ?? ""}|${target.workbenchSessionId ?? ""}` : "";

  const land = useCallback((key: string, result: FigureBuildResultDto | null, host: string) => {
    // Ruling R1: the server sends an attempt host's figure without its fuller (Manim) version.
    const figure = result?.figure ?? null;
    const help = result?.help ?? null;
    const shown = figure !== null && figure.shown;
    updateHost(host, (state) => ({ ...state, lines: state.lines.map((line) => line.key !== key ? line : {
      ...line, figure, help,
      state: figure ? "landed" : "failed",
      message: help?.status === "not_recorded" ? PANEL_FIGURE_COPY.notRecorded
        : help?.status === "disabled" ? PANEL_FIGURE_COPY.disabled
        : figure ? null : PANEL_FIGURE_COPY.failed
    }) }));
    if (figure && shown) updateHost(host, (state) => ({ ...state, expandedKey: figurePlacementKey(figure) }));
    if (help?.status === "counted" && help.new) onEventRef.current?.({ counted: true, converted: false });
  }, []);

  const send = useCallback(async (goal: string) => {
    const words = goal.trim();
    if (!enabled || !target || !words) return;
    const hostRef = figureHostRef(target);
    if (!hostRef) return;
    // The line is written to the host it was asked on, even if the panel closes meanwhile.
    const host = hostKey;
    const key = `fig:${Date.now()}:${words}`;
    setLines((list) => [...list, { key, goal: words, state: "pending", figure: null, help: null, message: null }], host);
    try {
      let takeStepToken: string | null = null;
      if (cold && target.context === "practice") {
        // §11.3: the take step converts the attempt first; its token goes with the request.
        const keptToken = keptTokenOf(host);
        if (keptToken?.key === attemptKey) {
          takeStepToken = keptToken.token;
        } else {
          const step = await api.figureTakeStep({
            itemId: target.practiceItemId as string, submissionId: target.submissionId ?? null,
            sessionId: target.sessionId ?? null, workbenchSessionId: target.workbenchSessionId ?? null
          });
          if (step.needed && step.token) {
            const kept = { key: attemptKey, token: step.token };
            updateHost(host, (state) => ({ ...state, token: kept, converted: true }));
            takeStepToken = step.token;
            onEventRef.current?.({ counted: true, converted: true, banner: step.banner ?? PANEL_FIGURE_COPY.banner });
          }
        }
      }
      const result = await settle(() => api.figureRequest({ goalText: words, origin: "ask", hostRef, takeStepToken }));
      land(key, result, host);
    } catch (error) {
      setLines((list) => list.map((line) => line.key !== key ? line : { ...line, state: "failed", message: errorMessage(error) }), host);
    }
  }, [enabled, target, cold, attemptKey, land, hostKey, setLines]);

  /** The chooser's explore_figure line opens its figure here (§11.4). */
  const open = useCallback(async (figureId: string, label: string) => {
    if (!enabled || !target) return;
    const hostRef = figureHostRef(target);
    if (!hostRef) return;
    const host = hostKey;
    const key = `open:${figureId}`;
    setLines((list) => list.some((line) => line.key === key) ? list
      : [...list, { key, goal: label, state: "pending", figure: null, help: null, message: null }], host);
    try {
      const keptToken = keptTokenOf(host);
      const opened = await api.figureOpen({ figureId, hostRef, takeStepToken: keptToken?.key === attemptKey ? keptToken.token : null });
      land(key, { figure: opened.figure, reused: true, help: opened.help }, host);
    } catch (error) {
      setLines((list) => list.map((line) => line.key !== key ? line : { ...line, state: "failed", message: errorMessage(error) }), host);
    }
  }, [enabled, target, attemptKey, land, hostKey, setLines]);

  const contract: FiguresContract = useMemo(() => ({ predictions: true, region: false, revisions: true, showMe: true }), []);
  const ctl: FiguresCtl = useMemo(() => {
    const patch = (found: { figureId: string; predictionIndex: number }) => setLines((list) => list.map((line) => {
      if (!line.figure || line.figure.figureId !== found.figureId) return line;
      return { ...line, figure: { ...line.figure, predictions: line.figure.predictions.map((prediction) =>
        prediction.index === found.predictionIndex ? { ...prediction, answered: found as never } : prediction) } };
    }));
    return {
      enabled,
      contract,
      figures: lines.flatMap((line) => line.figure ? [line.figure] : []),
      pending: [],
      expandedKey,
      setExpanded: (figure) => updateHost(hostKey, (state) => ({ ...state, expandedKey: figure ? figurePlacementKey(figure) : null })),
      request: async () => "skipped",
      revise: (figure, note) => {
        const key = lines.find((line) => line.figure?.figureId === figure.figureId)?.key;
        if (!key) return;
        const host = hostKey;
        setLines((list) => list.map((line) => line.key === key ? { ...line, state: "pending" } : line), host);
        // Codex review F4: the version is asked on the host it is open on now (a Reader figure
        // opened from the chooser's line too), so it is recorded and reveal-checked on this attempt.
        const hostRef = target ? figureHostRef(target) : null;
        const keptToken = keptTokenOf(host);
        const takeStepToken = keptToken?.key === attemptKey ? keptToken.token : null;
        void settle(() => api.readerFigureRevise({ figureId: figure.figureId, note, hostRef, takeStepToken }))
          .then((result) => land(key, result, host))
          .catch((error) => setLines((list) => list.map((line) => line.key === key ? { ...line, state: "failed", message: errorMessage(error) } : line), host));
      },
      predict: async (figure, index, answer) => {
        const found = await api.readerFigurePredict({ figureId: figure.figureId, predictionIndex: index, answer });
        patch(found);
        return found;
      },
      explain: async (_figure, predictionId, text) => {
        if (!text.trim()) return null;
        const found = await api.readerFigureExplain({ predictionId, text });
        patch(found);
        return found;
      },
      under: () => ({ figures: [], pending: [], richPending: [], followed: [] }),
      // RW5d P4a: no figure is followed into an attempt host (the Reader's section follow only).
      followed: [],
      follow: async () => false,
      richPending: [],
      cancelRich: () => undefined,
      retryRich: () => undefined,
      manimOptIn: null,
      optInSpanId: null,
      answerManimOptIn: () => undefined
    };
  }, [enabled, contract, lines, expandedKey, land, target, attemptKey, hostKey, setLines]);

  const dismiss = (key: string) => setLines((list) => list.filter((line) => line.key !== key));
  return { enabled, lines, send, open, ctl, converted, dismiss };
}

export type PanelFigures = ReturnType<typeof usePanelFigures>;

const link = { border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 } as const;

/** One figure line in the panel's thread, and its frame at panel width. */
export function PanelFigureThreadLine({ line, figures }: { line: PanelFigureLine; figures: PanelFigures }) {
  const [wide, setWide] = useState(false);
  const counted = line.help?.countsAsHint === true;
  return (
    <div data-testid="ask-figure-line" data-state={line.state} style={{ marginBottom: 12, fontSize: 12 }}>
      <div style={{ color: COLOR.text, display: "flex", gap: 6, alignItems: "baseline" }}>
        <span style={{ color: COLOR.amber, fontWeight: 700 }}>›</span>
        <span>show me {line.goal}</span>
      </div>
      {line.state === "pending" ? <div style={{ color: COLOR.textDim, marginTop: 4 }}>{PANEL_FIGURE_COPY.pending}</div> : null}
      {line.state === "failed" ? (
        <div style={{ color: COLOR.textDim, marginTop: 4 }}>{line.message ?? PANEL_FIGURE_COPY.failed}</div>
      ) : null}
      {line.state === "landed" && line.figure ? (
        <>
          <div style={{ color: COLOR.textDim, marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 11 }}>
            <span>{PANEL_FIGURE_COPY.landed} · {showMeSourceLine(line.figure)} · {counted ? PANEL_FIGURE_COPY.countsLine : PANEL_FIGURE_COPY.freeLine}</span>
            <button type="button" style={link} aria-pressed={wide} onClick={() => setWide((value) => !value)}>
              {wide ? PANEL_FIGURE_COPY.narrow : PANEL_FIGURE_COPY.widen}
            </button>
          </div>
          <div data-testid="ask-figure-frame" data-wide={wide ? "1" : "0"}
            style={{ width: wide ? "min(92vw, 760px)" : "100%", maxWidth: wide ? "none" : "100%", overflowX: "auto" }}>
            <FigureInline figure={line.figure} ctl={figures.ctl} />
          </div>
        </>
      ) : null}
    </div>
  );
}
